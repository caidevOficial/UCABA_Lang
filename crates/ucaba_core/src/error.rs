use std::fmt;

#[derive(Debug, Clone, PartialEq)]
pub enum UcabaError {
    Lexer {
        message: String,
        line: usize,
        column: usize,
    },
    Parse {
        message: String,
        line: usize,
        column: usize,
    },
    Type {
        message: String,
        line: usize,
        column: usize,
    },
    Runtime {
        message: String,
        line: usize,
        column: usize,
    },
}

impl fmt::Display for UcabaError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            UcabaError::Lexer { message, line, column } => {
                write!(f, "Error léxico en línea {}, columna {}: {}", line, column, message)
            }
            UcabaError::Parse { message, line, column } => {
                write!(f, "Error de sintaxis en línea {}, columna {}: {}", line, column, message)
            }
            UcabaError::Type { message, line, column } => {
                write!(f, "Error de tipos en línea {}, columna {}: {}", line, column, message)
            }
            UcabaError::Runtime { message, line, column } => {
                write!(f, "Error de ejecución en línea {}, columna {}: {}", line, column, message)
            }
        }
    }
}

impl std::error::Error for UcabaError {}
