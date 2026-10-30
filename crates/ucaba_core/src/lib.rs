pub mod ast;
pub mod error;
pub mod eval;
pub mod lexer;
pub mod parser;
pub mod token;
pub mod value;

pub use error::UcabaError;
pub use eval::{
    check_type_compatibility, is_input_complete, DebugAction, DebugFrame, Debugger, Interpreter,
    DEBUG_ABORT_MESSAGE,
};
pub use lexer::Lexer;
pub use parser::Parser;
pub use value::Value;

use std::fs;
use std::path::Path;

pub const VERSION: &str = "2.1.0";

pub fn run_code(source: &str, lenient: bool) -> Result<Vec<String>, UcabaError> {
    let mut lexer = Lexer::new(source);
    let tokens = lexer.tokenize()?;

    let mut parser = Parser::new(tokens, lenient);
    let program = parser.parse()?;

    let mut interpreter = Interpreter::new();
    interpreter.run(&program)?;

    Ok(interpreter.output)
}

pub fn run_file<P: AsRef<Path>>(path: P, lenient: bool) -> Result<Vec<String>, UcabaError> {
    let path_ref = path.as_ref();
    if !path_ref.to_string_lossy().ends_with(".ucaba") {
        return Err(UcabaError::Runtime {
            message: format!(
                "Extensión no válida: '{}'. El lenguaje UCABA solo admite archivos con extensión '.ucaba'.",
                path_ref.display()
            ),
            line: 0,
            column: 0,
        });
    }

    let source = fs::read_to_string(path_ref).map_err(|e| UcabaError::Runtime {
        message: format!("No se pudo leer el archivo '{}': {}", path_ref.display(), e),
        line: 0,
        column: 0,
    })?;

    run_code(&source, lenient)
}

pub fn check_code(source: &str, lenient: bool) -> Result<(), UcabaError> {
    let mut lexer = Lexer::new(source);
    let tokens = lexer.tokenize()?;

    let mut parser = Parser::new(tokens, lenient);
    let _program = parser.parse()?;

    Ok(())
}

pub fn check_file<P: AsRef<Path>>(path: P, lenient: bool) -> Result<(), UcabaError> {
    let path_ref = path.as_ref();
    let source = fs::read_to_string(path_ref).map_err(|e| UcabaError::Runtime {
        message: format!("No se pudo leer el archivo '{}': {}", path_ref.display(), e),
        line: 0,
        column: 0,
    })?;

    check_code(&source, lenient)
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Diagnostic {
    pub line: usize,
    pub character: usize,
    pub length: usize,
    pub message: String,
    pub severity: String,
    pub source: String,
}

#[derive(Debug, Clone, PartialEq, Eq)]
pub struct DiagnosticsReport {
    pub diagnostics: Vec<Diagnostic>,
}

fn escape_json_str(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    out.push('"');
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\x08' => out.push_str("\\b"),
            '\x0C' => out.push_str("\\f"),
            c if c < ' ' => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out.push('"');
    out
}

impl DiagnosticsReport {
    pub fn to_json(&self) -> String {
        let mut out = String::from("{\"diagnostics\":[");
        for (i, d) in self.diagnostics.iter().enumerate() {
            if i > 0 {
                out.push(',');
            }
            out.push_str(&format!(
                r#"{{"line":{},"character":{},"length":{},"message":{},"severity":{},"source":{}}}"#,
                d.line,
                d.character,
                d.length,
                escape_json_str(&d.message),
                escape_json_str(&d.severity),
                escape_json_str(&d.source)
            ));
        }
        out.push_str("]}");
        out
    }
}

pub fn check_diagnostics(source: &str, lenient: bool) -> DiagnosticsReport {
    let mut lexer = Lexer::new(source);
    let tokens = match lexer.tokenize() {
        Ok(t) => t,
        Err(e) => {
            let (line, col, msg) = match e {
                UcabaError::Lexer { line, column, message } => (line, column, message),
                _ => (1, 1, e.to_string()),
            };
            return DiagnosticsReport {
                diagnostics: vec![Diagnostic {
                    line: line.saturating_sub(1),
                    character: col.saturating_sub(1),
                    length: 1,
                    message: msg,
                    severity: "error".to_string(),
                    source: "ucaba-lexer".to_string(),
                }],
            };
        }
    };

    let mut parser = Parser::new(tokens, lenient);
    if let Err(e) = parser.parse() {
        let (line, col, msg) = match e {
            UcabaError::Parse { line, column, message } => (line, column, message),
            _ => (1, 1, e.to_string()),
        };
        return DiagnosticsReport {
            diagnostics: vec![Diagnostic {
                line: line.saturating_sub(1),
                character: col.saturating_sub(1),
                length: 1,
                message: msg,
                severity: "error".to_string(),
                source: "ucaba-parser".to_string(),
            }],
        };
    }

    DiagnosticsReport {
        diagnostics: Vec::new(),
    }
}

