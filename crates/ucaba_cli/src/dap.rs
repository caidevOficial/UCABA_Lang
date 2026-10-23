//! Servidor DAP (Debug Adapter Protocol) de UCABA: `ucaba dap`.
//!
//! Habla JSON con encabezado `Content-Length` por stdin/stdout, de modo que VS Code
//! (y cualquier IDE compatible con DAP) pueda poner breakpoints, avanzar paso a paso e
//! inspeccionar variables de un programa `.ucaba`.
//!
//! Arquitectura (el intérprete usa `Rc`, por lo que no cruza hilos):
//! - Hilo principal: lee requests y responde. Nunca toca valores del intérprete.
//! - Hilo del intérprete: ejecuta el programa; el hook [`DapDebugger`] se bloquea en cada
//!   parada, publica un [`Snapshot`] ya convertido a texto y emite el evento `stopped`.
//! - La salida estándar (stdout) es EXCLUSIVAMENTE el canal del protocolo: IMPRIMIR se
//!   redirige a eventos `output` mediante `Interpreter::set_print_sink`.

use serde_json::{json, Value as Json};
use std::collections::{HashMap, HashSet};
use std::io::{self, BufRead, Write};
use std::path::Path;
use std::sync::atomic::{AtomicBool, AtomicI64, Ordering};
use std::sync::mpsc::{self, Receiver, Sender};
use std::sync::{Arc, Mutex};
use ucaba_core::ast::DataType;
use ucaba_core::{
    DebugAction, DebugFrame, Debugger, Interpreter, Lexer, Parser, UcabaError, Value as UValue,
    DEBUG_ABORT_MESSAGE,
};

const THREAD_ID: i64 = 1;
const MAX_ITEMS: usize = 200;
const MAX_DEPTH: usize = 6;
const MAX_VALUE_LEN: usize = 200;

// ---------------------------------------------------------------------------
// Canal de salida del protocolo
// ---------------------------------------------------------------------------

struct Channel {
    seq: AtomicI64,
    out: Mutex<io::Stdout>,
}

impl Channel {
    fn new() -> Self {
        Self {
            seq: AtomicI64::new(0),
            out: Mutex::new(io::stdout()),
        }
    }

    fn send(&self, mut msg: Json) {
        msg["seq"] = json!(self.seq.fetch_add(1, Ordering::SeqCst) + 1);
        let body = msg.to_string();
        if let Ok(mut out) = self.out.lock() {
            let _ = write!(out, "Content-Length: {}\r\n\r\n{}", body.len(), body);
            let _ = out.flush();
        }
    }

    fn event(&self, name: &str, body: Json) {
        self.send(json!({ "type": "event", "event": name, "body": body }));
    }

    fn output(&self, category: &str, text: &str) {
        self.event("output", json!({ "category": category, "output": text }));
    }

    fn respond(&self, req: &Json, body: Json) {
        self.send(json!({
            "type": "response",
            "request_seq": req["seq"],
            "success": true,
            "command": req["command"],
            "body": body,
        }));
    }

    fn respond_err(&self, req: &Json, message: &str) {
        self.send(json!({
            "type": "response",
            "request_seq": req["seq"],
            "success": false,
            "command": req["command"],
            "message": message,
        }));
    }
}

// ---------------------------------------------------------------------------
// Snapshot de una parada (todo en texto: seguro de compartir entre hilos)
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
struct VarSnap {
    name: String,
    value: String,
    ty: String,
    reference: i64,
}

#[derive(Debug, Clone)]
struct FrameSnap {
    name: String,
    line: usize,
    scope_ref: i64,
}

#[derive(Debug, Clone, Default)]
struct Snapshot {
    frames: Vec<FrameSnap>,
    /// `variablesReference = índice + 1`.
    refs: Vec<Vec<VarSnap>>,
}

fn infer_type(val: &UValue) -> String {
    match val {
        UValue::Entero(_) => "ENTERO".into(),
        UValue::Real(_) => "REAL".into(),
        UValue::Flotante(_) => "FLOTANTE".into(),
        UValue::Cadena(_) => "CADENA".into(),
        UValue::Caracter(_) => "CARACTER".into(),
        UValue::Booleano(_) => "BOOLEANO".into(),
        UValue::Vector(items) => match items.first() {
            Some(first) => format!("{}[]", infer_type(first)),
            None => "VECTOR".into(),
        },
        UValue::Struct(rc) => rc.borrow().struct_name.clone(),
        UValue::Archivo(_) => "ARCHIVO".into(),
        UValue::Nulo => "NULO".into(),
    }
}

fn truncate(mut s: String) -> String {
    if s.chars().count() > MAX_VALUE_LEN {
        s = s.chars().take(MAX_VALUE_LEN).collect::<String>() + "…";
    }
    s
}

fn display_value(val: &UValue) -> String {
    truncate(match val {
        UValue::Cadena(s) => format!("\"{s}\""),
        UValue::Caracter(c) => format!("'{c}'"),
        other => other.to_canonical_string(),
    })
}

/// Construye la variable y, si es un contenedor, sus hijos (acotado en profundidad/tamaño).
fn make_var(
    name: &str,
    val: &UValue,
    declared: Option<&DataType>,
    depth: usize,
    path: &mut Vec<usize>,
    refs: &mut Vec<Vec<VarSnap>>,
) -> VarSnap {
    let ty = match declared {
        Some(dt) if *dt != DataType::Void => dt.to_string(),
        _ => infer_type(val),
    };
    let mut value = display_value(val);
    let mut reference = 0;

    match val {
        UValue::Vector(items) if depth < MAX_DEPTH && !items.is_empty() => {
            let mut children = Vec::new();
            for (i, item) in items.iter().take(MAX_ITEMS).enumerate() {
                children.push(make_var(&format!("[{i}]"), item, None, depth + 1, path, refs));
            }
            refs.push(children);
            reference = refs.len() as i64;
        }
        UValue::Struct(rc) => {
            let ptr = std::rc::Rc::as_ptr(rc) as usize;
            if path.contains(&ptr) {
                value = format!("<{} (referencia circular)>", rc.borrow().struct_name);
            } else if depth < MAX_DEPTH {
                path.push(ptr);
                let (order, fields) = {
                    let s = rc.borrow();
                    let mut keys: Vec<String> = if s.field_order.is_empty() {
                        s.fields.keys().cloned().collect()
                    } else {
                        s.field_order.clone()
                    };
                    if s.field_order.is_empty() {
                        keys.sort();
                    }
                    (keys, s.fields.clone())
                };
                let mut children = Vec::new();
                for key in order {
                    if let Some(field_val) = fields.get(&key) {
                        children.push(make_var(&key, field_val, None, depth + 1, path, refs));
                    }
                }
                path.pop();
                refs.push(children);
                reference = refs.len() as i64;
            }
        }
        _ => {}
    }

    VarSnap {
        name: name.to_string(),
        value,
        ty,
        reference,
    }
}

fn build_snapshot(frames: &[DebugFrame]) -> Snapshot {
    let mut refs: Vec<Vec<VarSnap>> = Vec::new();
    let mut out = Vec::with_capacity(frames.len());
    for f in frames {
        let mut vars = Vec::new();
        let mut path = Vec::new();
        for (name, dt, val) in &f.variables {
            vars.push(make_var(name, val, Some(dt), 0, &mut path, &mut refs));
        }
        refs.push(vars);
        out.push(FrameSnap {
            name: f.name.clone(),
            line: f.line,
            scope_ref: refs.len() as i64,
        });
    }
    Snapshot { frames: out, refs }
}

fn var_to_json(v: &VarSnap) -> Json {
    json!({
        "name": v.name,
        "value": v.value,
        "type": v.ty,
        "variablesReference": v.reference,
    })
}

/// Resuelve expresiones simples: `x`, `persona.nombre`, `v[2]`, `m[1][0]`, `nodo.proximo.valor`.
fn resolve_expression(snap: &Snapshot, frame_idx: usize, expr: &str) -> Result<VarSnap, String> {
    let frame = snap
        .frames
        .get(frame_idx)
        .ok_or_else(|| "Marco de pila inválido.".to_string())?;
    let expr = expr.trim();
    let first_end = expr.find(['.', '[']).unwrap_or(expr.len());
    let root = &expr[..first_end];
    if root.is_empty() {
        return Err("Expresión vacía.".into());
    }
    let scope = &snap.refs[(frame.scope_ref - 1) as usize];
    let mut current = scope
        .iter()
        .find(|v| v.name == root)
        .or_else(|| scope.iter().find(|v| v.name.eq_ignore_ascii_case(root)))
        .cloned()
        .ok_or_else(|| format!("Variable no definida: '{root}'"))?;

    let mut rest = &expr[first_end..];
    while !rest.is_empty() {
        let child_name: String;
        if let Some(r) = rest.strip_prefix('.') {
            let end = r.find(['.', '[']).unwrap_or(r.len());
            child_name = r[..end].to_string();
            rest = &r[end..];
        } else if let Some(r) = rest.strip_prefix('[') {
            let end = r.find(']').ok_or("Falta ']' en la expresión.")?;
            let idx = r[..end].trim();
            if idx.parse::<usize>().is_err() {
                return Err("Solo se admiten índices numéricos literales.".into());
            }
            child_name = format!("[{idx}]");
            rest = &r[end + 1..];
        } else {
            return Err("Solo se admiten nombres de variables, campos (.) e índices ([n]).".into());
        }
        if current.reference == 0 {
            return Err(format!("'{}' no tiene miembros.", current.name));
        }
        let children = &snap.refs[(current.reference - 1) as usize];
        current = children
            .iter()
            .find(|v| v.name == child_name || v.name.eq_ignore_ascii_case(&child_name))
            .cloned()
            .ok_or_else(|| format!("'{child_name}' no existe en '{}'.", current.name))?;
    }
    Ok(current)
}

// ---------------------------------------------------------------------------
// Estado compartido y depurador
// ---------------------------------------------------------------------------

#[derive(Clone, Copy, Debug)]
enum Resume {
    Continue,
    Next,
    StepIn,
    StepOut,
    Abort,
}

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum StepMode {
    Run,
    In,
    Over,
    Out,
}

struct Session {
    chan: Arc<Channel>,
    /// Líneas con breakpoint por archivo (clave normalizada).
    breakpoints: Mutex<HashMap<String, HashSet<usize>>>,
    snapshot: Mutex<Option<Snapshot>>,
    /// Ruta del programa lanzado (para el `source` de los marcos de pila).
    program: Mutex<Option<String>>,
    pause: AtomicBool,
    abort: AtomicBool,
}

fn norm_path(p: &str) -> String {
    p.replace('\\', "/").to_lowercase()
}

struct DapDebugger {
    session: Arc<Session>,
    rx: Receiver<Resume>,
    program_key: String,
    mode: StepMode,
    step_depth: usize,
    stop_on_entry: bool,
    /// (línea, profundidad) de la sentencia anterior: evita detenerse dos veces en la misma línea.
    last: Option<(usize, usize)>,
}

impl DapDebugger {
    fn is_breakpoint(&self, line: usize) -> bool {
        self.session
            .breakpoints
            .lock()
            .map(|m| m.get(&self.program_key).is_some_and(|s| s.contains(&line)))
            .unwrap_or(false)
    }
}

impl Debugger for DapDebugger {
    fn on_statement(&mut self, line: usize, interp: &Interpreter) -> DebugAction {
        if self.session.abort.load(Ordering::SeqCst) {
            return DebugAction::Abort;
        }
        let depth = interp.debug_depth();
        let same_as_last = self.last == Some((line, depth));
        self.last = Some((line, depth));

        let reason: Option<&str> = if self.stop_on_entry {
            self.stop_on_entry = false;
            Some("entry")
        } else if self.session.pause.swap(false, Ordering::SeqCst) {
            Some("pause")
        } else if same_as_last {
            None
        } else if self.is_breakpoint(line) {
            Some("breakpoint")
        } else {
            match self.mode {
                StepMode::In => Some("step"),
                StepMode::Over if depth <= self.step_depth => Some("step"),
                StepMode::Out if depth < self.step_depth => Some("step"),
                _ => None,
            }
        };
        let Some(reason) = reason else {
            return DebugAction::Continue;
        };

        let snap = build_snapshot(&interp.debug_snapshot());
        if let Ok(mut slot) = self.session.snapshot.lock() {
            *slot = Some(snap);
        }
        self.session.chan.event(
            "stopped",
            json!({ "reason": reason, "threadId": THREAD_ID, "allThreadsStopped": true }),
        );

        let cmd = self.rx.recv();
        if let Ok(mut slot) = self.session.snapshot.lock() {
            *slot = None;
        }
        match cmd {
            Ok(Resume::Continue) => self.mode = StepMode::Run,
            Ok(Resume::Next) => {
                self.mode = StepMode::Over;
                self.step_depth = depth;
            }
            Ok(Resume::StepIn) => self.mode = StepMode::In,
            Ok(Resume::StepOut) => {
                self.mode = StepMode::Out;
                self.step_depth = depth;
            }
            Ok(Resume::Abort) | Err(_) => return DebugAction::Abort,
        }
        DebugAction::Continue
    }
}

// ---------------------------------------------------------------------------
// Ejecución del programa (hilo del intérprete)
// ---------------------------------------------------------------------------

struct Launch {
    program: String,
    stop_on_entry: bool,
    lenient: bool,
    no_debug: bool,
    cwd: Option<String>,
}

fn run_program(session: Arc<Session>, launch: Launch, rx: Receiver<Resume>) {
    let chan = session.chan.clone();
    let finish = |code: i32| {
        chan.event("exited", json!({ "exitCode": code }));
        chan.event("terminated", json!({}));
    };

    if let Some(cwd) = &launch.cwd {
        let _ = std::env::set_current_dir(cwd);
    }

    let source = match std::fs::read_to_string(&launch.program) {
        Ok(s) => s,
        Err(e) => {
            chan.output(
                "stderr",
                &format!("No se pudo leer '{}': {}\n", launch.program, e),
            );
            return finish(1);
        }
    };

    let program = match Lexer::new(&source)
        .tokenize()
        .and_then(|tokens| Parser::new(tokens, launch.lenient).parse())
    {
        Ok(p) => p,
        Err(e) => {
            chan.output("stderr", &format!("{e}\n"));
            return finish(1);
        }
    };

    let mut interp = Interpreter::new();
    let sink_chan = chan.clone();
    interp.set_print_sink(Box::new(move |text: &str| {
        sink_chan.output("stdout", &format!("{text}\n"));
    }));
    if !launch.no_debug {
        interp.set_debugger(Box::new(DapDebugger {
            session: session.clone(),
            rx,
            program_key: norm_path(&launch.program),
            mode: StepMode::Run,
            step_depth: 0,
            stop_on_entry: launch.stop_on_entry,
            last: None,
        }));
    }

    match interp.run(&program) {
        Ok(()) => finish(0),
        Err(UcabaError::Runtime { message, .. }) if message == DEBUG_ABORT_MESSAGE => finish(0),
        Err(e) => {
            chan.output("stderr", &format!("{e}\n"));
            finish(1)
        }
    }
}

// ---------------------------------------------------------------------------
// Bucle de requests (hilo principal)
// ---------------------------------------------------------------------------

fn read_message(reader: &mut impl BufRead) -> Option<Json> {
    let mut content_len: Option<usize> = None;
    loop {
        let mut line = String::new();
        if reader.read_line(&mut line).ok()? == 0 {
            return None;
        }
        let trimmed = line.trim_end();
        if trimmed.is_empty() {
            break;
        }
        if let Some(v) = trimmed
            .to_ascii_lowercase()
            .strip_prefix("content-length:")
        {
            content_len = v.trim().parse().ok();
        }
    }
    let mut buf = vec![0u8; content_len?];
    reader.read_exact(&mut buf).ok()?;
    serde_json::from_slice(&buf).ok()
}

/// Punto de entrada de `ucaba dap`. No retorna hasta que el cliente se desconecta.
pub fn run_dap() -> i32 {
    let chan = Arc::new(Channel::new());
    let session = Arc::new(Session {
        chan: chan.clone(),
        breakpoints: Mutex::new(HashMap::new()),
        snapshot: Mutex::new(None),
        program: Mutex::new(None),
        pause: AtomicBool::new(false),
        abort: AtomicBool::new(false),
    });

    let stdin = io::stdin();
    let mut reader = stdin.lock();
    let mut launch: Option<Launch> = None;
    let mut resume_tx: Option<Sender<Resume>> = None;
    let mut started = false;

    while let Some(req) = read_message(&mut reader) {
        if req["type"] != "request" {
            continue;
        }
        let command = req["command"].as_str().unwrap_or("").to_string();
        let args = &req["arguments"];

        match command.as_str() {
            "initialize" => {
                chan.respond(
                    &req,
                    json!({
                        "supportsConfigurationDoneRequest": true,
                        "supportsEvaluateForHovers": true,
                        "supportsTerminateRequest": true,
                    }),
                );
                chan.event("initialized", json!({}));
            }
            "launch" => match args["program"].as_str() {
                Some(program) => {
                    if let Ok(mut p) = session.program.lock() {
                        *p = Some(program.to_string());
                    }
                    launch = Some(Launch {
                        program: program.to_string(),
                        stop_on_entry: args["stopOnEntry"].as_bool().unwrap_or(false),
                        lenient: args["lenient"].as_bool().unwrap_or(false),
                        no_debug: args["noDebug"].as_bool().unwrap_or(false),
                        cwd: args["cwd"].as_str().map(String::from),
                    });
                    chan.respond(&req, json!({}));
                }
                None => chan.respond_err(&req, "Falta el campo 'program' en la configuración de launch."),
            },
            "setBreakpoints" => {
                let path = args["source"]["path"].as_str().map(norm_path);
                let mut lines: Vec<usize> = args["breakpoints"]
                    .as_array()
                    .map(|a| a.iter().filter_map(|b| b["line"].as_u64()).map(|l| l as usize).collect())
                    .unwrap_or_default();
                if lines.is_empty() {
                    if let Some(legacy) = args["lines"].as_array() {
                        lines = legacy.iter().filter_map(|l| l.as_u64()).map(|l| l as usize).collect();
                    }
                }
                if let Some(path) = path {
                    if let Ok(mut map) = session.breakpoints.lock() {
                        map.insert(path, lines.iter().copied().collect());
                    }
                }
                let verified: Vec<Json> = lines
                    .iter()
                    .map(|l| json!({ "verified": true, "line": l }))
                    .collect();
                chan.respond(&req, json!({ "breakpoints": verified }));
            }
            "setExceptionBreakpoints" => chan.respond(&req, json!({})),
            "configurationDone" => {
                chan.respond(&req, json!({}));
                if let (false, Some(l)) = (started, launch.take()) {
                    started = true;
                    let (tx, rx) = mpsc::channel();
                    resume_tx = Some(tx);
                    let sess = session.clone();
                    let spawned = std::thread::Builder::new()
                        .name("ucaba-interpreter".into())
                        .stack_size(64 * 1024 * 1024)
                        .spawn(move || run_program(sess, l, rx));
                    if let Err(e) = spawned {
                        chan.output("stderr", &format!("No se pudo iniciar el intérprete: {e}\n"));
                        chan.event("terminated", json!({}));
                    }
                }
            }
            "threads" => chan.respond(
                &req,
                json!({ "threads": [{ "id": THREAD_ID, "name": "UCABA" }] }),
            ),
            "stackTrace" => {
                let snap = session.snapshot.lock().ok().and_then(|s| s.clone());
                let program = session.program.lock().ok().and_then(|p| p.clone());
                let frames: Vec<Json> = snap
                    .map(|s| {
                        s.frames
                            .iter()
                            .enumerate()
                            .map(|(i, f)| {
                                let mut frame = json!({
                                    "id": i,
                                    "name": f.name,
                                    "line": f.line,
                                    "column": 1,
                                });
                                if let Some(p) = &program {
                                    frame["source"] = json!({
                                        "name": Path::new(p).file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default(),
                                        "path": p,
                                    });
                                }
                                frame
                            })
                            .collect()
                    })
                    .unwrap_or_default();
                let total = frames.len();
                chan.respond(&req, json!({ "stackFrames": frames, "totalFrames": total }));
            }
            "scopes" => {
                let frame_id = args["frameId"].as_u64().unwrap_or(0) as usize;
                let scopes: Vec<Json> = session
                    .snapshot
                    .lock()
                    .ok()
                    .and_then(|s| s.clone())
                    .and_then(|s| s.frames.get(frame_id).cloned())
                    .map(|f| {
                        vec![json!({
                            "name": "Variables",
                            "variablesReference": f.scope_ref,
                            "expensive": false,
                        })]
                    })
                    .unwrap_or_default();
                chan.respond(&req, json!({ "scopes": scopes }));
            }
            "variables" => {
                let reference = args["variablesReference"].as_i64().unwrap_or(0);
                let vars: Vec<Json> = session
                    .snapshot
                    .lock()
                    .ok()
                    .and_then(|s| s.clone())
                    .and_then(|s| {
                        if reference >= 1 {
                            s.refs.get((reference - 1) as usize).cloned()
                        } else {
                            None
                        }
                    })
                    .map(|v| v.iter().map(var_to_json).collect())
                    .unwrap_or_default();
                chan.respond(&req, json!({ "variables": vars }));
            }
            "evaluate" => {
                let expr = args["expression"].as_str().unwrap_or("");
                let frame_id = args["frameId"].as_u64().unwrap_or(0) as usize;
                let snap = session.snapshot.lock().ok().and_then(|s| s.clone());
                match snap {
                    Some(s) => match resolve_expression(&s, frame_id, expr) {
                        Ok(v) => chan.respond(
                            &req,
                            json!({
                                "result": v.value,
                                "type": v.ty,
                                "variablesReference": v.reference,
                            }),
                        ),
                        Err(msg) => chan.respond_err(&req, &msg),
                    },
                    None => chan.respond_err(&req, "El programa no está detenido."),
                }
            }
            "continue" | "next" | "stepIn" | "stepOut" => {
                let resume = match command.as_str() {
                    "continue" => Resume::Continue,
                    "next" => Resume::Next,
                    "stepIn" => Resume::StepIn,
                    _ => Resume::StepOut,
                };
                // Primero la respuesta: así el evento `stopped` siguiente llega después.
                if command == "continue" {
                    chan.respond(&req, json!({ "allThreadsContinued": true }));
                } else {
                    chan.respond(&req, json!({}));
                }
                if let Some(tx) = &resume_tx {
                    let _ = tx.send(resume);
                }
            }
            "pause" => {
                session.pause.store(true, Ordering::SeqCst);
                chan.respond(&req, json!({}));
            }
            "terminate" => {
                session.abort.store(true, Ordering::SeqCst);
                chan.respond(&req, json!({}));
                if let Some(tx) = &resume_tx {
                    let _ = tx.send(Resume::Abort);
                }
            }
            "disconnect" => {
                session.abort.store(true, Ordering::SeqCst);
                chan.respond(&req, json!({}));
                if let Some(tx) = &resume_tx {
                    let _ = tx.send(Resume::Abort);
                }
                break;
            }
            other => chan.respond_err(&req, &format!("Comando DAP no soportado: '{other}'")),
        }
    }

    session.abort.store(true, Ordering::SeqCst);
    if let Some(tx) = &resume_tx {
        let _ = tx.send(Resume::Abort);
    }
    0
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::io::Cursor;

    #[test]
    fn lee_mensaje_con_content_length() {
        let body = r#"{"seq":1,"type":"request","command":"initialize"}"#;
        let raw = format!("Content-Length: {}\r\n\r\n{}", body.len(), body);
        let mut cur = Cursor::new(raw.into_bytes());
        let msg = read_message(&mut cur).expect("mensaje");
        assert_eq!(msg["command"], "initialize");
    }

    #[test]
    fn resuelve_campos_e_indices() {
        let snap = Snapshot {
            frames: vec![FrameSnap { name: "<principal>".into(), line: 1, scope_ref: 3 }],
            refs: vec![
                vec![VarSnap { name: "[0]".into(), value: "10".into(), ty: "ENTERO".into(), reference: 0 }],
                vec![VarSnap { name: "datos".into(), value: "[10]".into(), ty: "ENTERO[]".into(), reference: 1 }],
                vec![VarSnap { name: "p".into(), value: "P{}".into(), ty: "P".into(), reference: 2 }],
            ],
        };
        // scope_ref=3 -> refs[2] = [p]; p -> refs[1] = [datos]; datos -> refs[0] = ["[0]"].
        let v = resolve_expression(&snap, 0, "p.datos[0]").expect("resuelve");
        assert_eq!(v.value, "10");
        assert!(resolve_expression(&snap, 0, "q").is_err());
    }
}
