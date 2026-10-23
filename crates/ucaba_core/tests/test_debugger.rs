use std::cell::RefCell;
use std::rc::Rc;
use ucaba_core::{
    DebugAction, DebugFrame, Debugger, Interpreter, Lexer, Parser, UcabaError, Value,
    DEBUG_ABORT_MESSAGE,
};

const PROGRAMA: &str = "\
FUNCION doble(n: ENTERO): ENTERO
    RETORNAR n * 2
FIN FUNCION
ENTERO x = 5
ENTERO r = doble(x)
IMPRIMIR(r)
";

fn parse(src: &str) -> ucaba_core::ast::Program {
    let tokens = Lexer::new(src).tokenize().expect("lexer");
    Parser::new(tokens, false).parse().expect("parser")
}

/// Registra (línea, profundidad) y captura el snapshot al llegar a `capture_line`.
struct Recorder {
    log: Rc<RefCell<Vec<(usize, usize)>>>,
    capture_line: usize,
    captured: Rc<RefCell<Option<Vec<DebugFrame>>>>,
    abort_at: Option<usize>,
}

impl Debugger for Recorder {
    fn on_statement(&mut self, line: usize, interp: &Interpreter) -> DebugAction {
        self.log.borrow_mut().push((line, interp.debug_depth()));
        if line == self.capture_line {
            *self.captured.borrow_mut() = Some(interp.debug_snapshot());
        }
        if self.abort_at == Some(line) {
            return DebugAction::Abort;
        }
        DebugAction::Continue
    }
}

fn run_with(
    capture_line: usize,
    abort_at: Option<usize>,
) -> (
    Result<(), UcabaError>,
    Vec<(usize, usize)>,
    Option<Vec<DebugFrame>>,
    Vec<String>,
) {
    let program = parse(PROGRAMA);
    let log = Rc::new(RefCell::new(Vec::new()));
    let captured = Rc::new(RefCell::new(None));
    let printed = Rc::new(RefCell::new(Vec::new()));

    let mut interp = Interpreter::new();
    let sink = printed.clone();
    interp.set_print_sink(Box::new(move |t: &str| sink.borrow_mut().push(t.to_string())));
    interp.set_debugger(Box::new(Recorder {
        log: log.clone(),
        capture_line,
        captured: captured.clone(),
        abort_at,
    }));
    let res = interp.run(&program);
    let l = log.borrow().clone();
    let c = captured.borrow().clone();
    let p = printed.borrow().clone();
    (res, l, c, p)
}

#[test]
fn hook_recibe_linea_y_profundidad_de_cada_sentencia() {
    let (res, log, _, _) = run_with(0, None);
    assert!(res.is_ok());
    // Las definiciones (FUNCION) no se ejecutan; la llamada entra al cuerpo en profundidad 1.
    assert_eq!(log, vec![(4, 0), (5, 0), (2, 1), (6, 0)]);
}

#[test]
fn snapshot_dentro_de_funcion_muestra_pila_y_variables() {
    let (_, _, captured, _) = run_with(2, None);
    let frames = captured.expect("snapshot capturado");
    assert_eq!(frames.len(), 2);

    // Marco más interno primero.
    assert_eq!(frames[0].name, "doble");
    assert_eq!(frames[0].line, 2);
    assert_eq!(frames[0].variables.len(), 1);
    assert_eq!(frames[0].variables[0].0, "n");
    assert_eq!(frames[0].variables[0].2, Value::Entero(5));

    // El llamador queda en la línea de la llamada y conserva sus variables.
    assert_eq!(frames[1].name, "<principal>");
    assert_eq!(frames[1].line, 5);
    assert!(frames[1].variables.iter().any(|(n, _, v)| n == "x" && *v == Value::Entero(5)));
}

#[test]
fn abort_detiene_la_ejecucion_con_error_reconocible() {
    let (res, log, _, printed) = run_with(0, Some(5));
    match res {
        Err(UcabaError::Runtime { message, line, .. }) => {
            assert_eq!(message, DEBUG_ABORT_MESSAGE);
            assert_eq!(line, 5);
        }
        other => panic!("se esperaba abort, se obtuvo {:?}", other),
    }
    assert_eq!(log.last(), Some(&(5, 0)));
    assert!(printed.is_empty(), "no debe llegar a IMPRIMIR");
}

#[test]
fn print_sink_redirige_imprimir() {
    let (res, _, _, printed) = run_with(0, None);
    assert!(res.is_ok());
    assert_eq!(printed, vec!["10".to_string()]);
}

#[test]
fn sin_depurador_el_comportamiento_no_cambia() {
    let program = parse(PROGRAMA);
    let mut interp = Interpreter::new();
    interp.run(&program).expect("ejecución normal");
    assert_eq!(interp.output, vec!["10".to_string()]);
    assert_eq!(interp.debug_depth(), 0);
}
