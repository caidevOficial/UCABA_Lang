//! Prueba de integración del servidor DAP: maneja `ucaba dap` como lo haría VS Code.

use serde_json::{json, Value};
use std::io::{BufRead, BufReader, Read, Write};
use std::process::{Child, ChildStdin, Command, Stdio};
use std::sync::mpsc::{self, Receiver};
use std::thread;
use std::time::Duration;

const PROGRAMA: &str = "\
FUNCION doble(n: ENTERO): ENTERO
    RETORNAR n * 2
FIN FUNCION
ENTERO x = 5
ENTERO r = doble(x)
IMPRIMIR(r)
";

struct DapClient {
    child: Child,
    stdin: ChildStdin,
    rx: Receiver<Value>,
    seq: i64,
    log: Vec<Value>,
}

impl DapClient {
    fn start() -> Self {
        let mut child = Command::new(env!("CARGO_BIN_EXE_ucaba"))
            .arg("dap")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn()
            .expect("no se pudo lanzar `ucaba dap`");
        let stdin = child.stdin.take().unwrap();
        let mut reader = BufReader::new(child.stdout.take().unwrap());
        let (tx, rx) = mpsc::channel();
        thread::spawn(move || loop {
            let mut len = 0usize;
            loop {
                let mut line = String::new();
                match reader.read_line(&mut line) {
                    Ok(0) | Err(_) => return,
                    Ok(_) => {}
                }
                let t = line.trim_end();
                if t.is_empty() {
                    break;
                }
                if let Some(v) = t.strip_prefix("Content-Length:") {
                    len = v.trim().parse().unwrap();
                }
            }
            let mut buf = vec![0u8; len];
            if reader.read_exact(&mut buf).is_err() {
                return;
            }
            let msg: Value = serde_json::from_slice(&buf).expect("JSON inválido del servidor DAP");
            if tx.send(msg).is_err() {
                return;
            }
        });
        Self { child, stdin, rx, seq: 0, log: Vec::new() }
    }

    fn send(&mut self, command: &str, arguments: Value) -> i64 {
        self.seq += 1;
        let body = json!({
            "seq": self.seq, "type": "request", "command": command, "arguments": arguments
        })
        .to_string();
        write!(self.stdin, "Content-Length: {}\r\n\r\n{}", body.len(), body).unwrap();
        self.stdin.flush().unwrap();
        self.seq
    }

    fn wait_for(&mut self, what: &str, pred: impl Fn(&Value) -> bool) -> Value {
        loop {
            let msg = self
                .rx
                .recv_timeout(Duration::from_secs(10))
                .unwrap_or_else(|_| panic!("timeout esperando {what}; log: {:#?}", self.log));
            self.log.push(msg.clone());
            if pred(&msg) {
                return msg;
            }
        }
    }

    fn request(&mut self, command: &str, arguments: Value) -> Value {
        let seq = self.send(command, arguments);
        let resp = self.wait_for(command, |m| m["type"] == "response" && m["request_seq"] == seq);
        assert_eq!(resp["success"], true, "{command} falló: {resp}");
        resp["body"].clone()
    }

    fn wait_event(&mut self, name: &str) -> Value {
        let name = name.to_string();
        self.wait_for(&name.clone(), move |m| m["type"] == "event" && m["event"] == name)["body"].clone()
    }

    fn top_frame(&mut self) -> Value {
        let st = self.request("stackTrace", json!({ "threadId": 1 }));
        st["stackFrames"][0].clone()
    }
}

impl Drop for DapClient {
    fn drop(&mut self) {
        let _ = self.child.kill();
        let _ = self.child.wait();
    }
}

#[test]
fn dap_breakpoint_stepin_stepout_variables_y_salida() {
    let path = std::env::temp_dir().join(format!("ucaba_dap_test_{}.ucaba", std::process::id()));
    std::fs::write(&path, PROGRAMA).unwrap();
    let program = path.to_string_lossy().to_string();

    let mut dap = DapClient::start();

    let caps = dap.request("initialize", json!({ "adapterID": "ucaba" }));
    assert_eq!(caps["supportsConfigurationDoneRequest"], true);
    dap.wait_event("initialized");

    dap.request("launch", json!({ "program": program }));
    let bps = dap.request(
        "setBreakpoints",
        json!({ "source": { "path": program }, "breakpoints": [{ "line": 5 }] }),
    );
    assert_eq!(bps["breakpoints"][0]["verified"], true);
    dap.request("configurationDone", json!({}));

    // 1) Se detiene en el breakpoint de la línea 5, en el programa principal.
    let stopped = dap.wait_event("stopped");
    assert_eq!(stopped["reason"], "breakpoint");
    let frame = dap.top_frame();
    assert_eq!(frame["line"], 5);
    assert_eq!(frame["name"], "<principal>");

    // 2) Variables del marco: x = 5.
    let scopes = dap.request("scopes", json!({ "frameId": 0 }));
    let vref = scopes["scopes"][0]["variablesReference"].as_i64().unwrap();
    let vars = dap.request("variables", json!({ "variablesReference": vref }));
    let x = vars["variables"]
        .as_array()
        .unwrap()
        .iter()
        .find(|v| v["name"] == "x")
        .expect("variable x");
    assert_eq!(x["value"], "5");
    assert_eq!(x["type"], "ENTERO");

    // 3) stepIn entra a `doble`: pila de 2 marcos y evaluate de `n`.
    dap.request("stepIn", json!({ "threadId": 1 }));
    assert_eq!(dap.wait_event("stopped")["reason"], "step");
    let st = dap.request("stackTrace", json!({ "threadId": 1 }));
    assert_eq!(st["totalFrames"], 2);
    assert_eq!(st["stackFrames"][0]["name"], "doble");
    assert_eq!(st["stackFrames"][0]["line"], 2);
    assert_eq!(st["stackFrames"][1]["line"], 5);
    let ev = dap.request("evaluate", json!({ "expression": "n", "frameId": 0 }));
    assert_eq!(ev["result"], "5");

    // 4) stepOut vuelve al llamador y se detiene en la línea 6.
    dap.request("stepOut", json!({ "threadId": 1 }));
    assert_eq!(dap.wait_event("stopped")["reason"], "step");
    assert_eq!(dap.top_frame()["line"], 6);

    // 5) continue: el programa termina y IMPRIMIR llega como evento `output`, no por stdout crudo.
    dap.request("continue", json!({ "threadId": 1 }));
    dap.wait_event("terminated");
    let printed: String = dap
        .log
        .iter()
        .filter(|m| m["event"] == "output" && m["body"]["category"] == "stdout")
        .map(|m| m["body"]["output"].as_str().unwrap().to_string())
        .collect();
    assert_eq!(printed, "10\n");

    let _ = std::fs::remove_file(&path);
}

#[test]
fn dap_stop_on_entry_y_terminate() {
    let path = std::env::temp_dir().join(format!("ucaba_dap_entry_{}.ucaba", std::process::id()));
    std::fs::write(&path, PROGRAMA).unwrap();
    let program = path.to_string_lossy().to_string();

    let mut dap = DapClient::start();
    dap.request("initialize", json!({}));
    dap.wait_event("initialized");
    dap.request("launch", json!({ "program": program, "stopOnEntry": true }));
    dap.request("configurationDone", json!({}));

    assert_eq!(dap.wait_event("stopped")["reason"], "entry");
    assert_eq!(dap.top_frame()["line"], 4);

    dap.request("terminate", json!({}));
    dap.wait_event("terminated");
    let _ = std::fs::remove_file(&path);
}

#[test]
fn dap_error_de_sintaxis_termina_con_salida_stderr() {
    let path = std::env::temp_dir().join(format!("ucaba_dap_err_{}.ucaba", std::process::id()));
    std::fs::write(&path, "SI (\n").unwrap();
    let program = path.to_string_lossy().to_string();

    let mut dap = DapClient::start();
    dap.request("initialize", json!({}));
    dap.wait_event("initialized");
    dap.request("launch", json!({ "program": program }));
    dap.request("configurationDone", json!({}));
    dap.wait_event("terminated");
    assert!(dap
        .log
        .iter()
        .any(|m| m["event"] == "output" && m["body"]["category"] == "stderr"));
    let _ = std::fs::remove_file(&path);
}
