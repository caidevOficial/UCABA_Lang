use crate::error::UcabaError;
use std::cell::RefCell;
use std::collections::{HashMap, HashSet};
use std::fmt;
use std::fs::{File, OpenOptions};
use std::io::{BufRead, BufReader, Write};
use std::path::Path;
use std::rc::Rc;

#[derive(Debug)]
pub struct ArchivoHandle {
    pub path: String,
    pub mode: String,
    pub lines: Vec<String>,
    pub cursor: usize,
    pub is_closed: bool,
    pub read_during_iteration: bool,
    pub writer: Option<File>,
}

impl ArchivoHandle {
    pub fn new(path: &str, mode: &str) -> Result<Self, UcabaError> {
        let norm_mode = mode.to_lowercase();
        let mut lines = Vec::new();
        let mut writer = None;

        if norm_mode == "lectura" || norm_mode == "r" {
            if !Path::new(path).exists() {
                return Err(UcabaError::Runtime {
                    message: format!("El archivo '{}' no existe para lectura.", path),
                    line: 0,
                    column: 0,
                });
            }
            let file = File::open(path).map_err(|e| UcabaError::Runtime {
                message: format!("Error al abrir archivo '{}': {}", path, e),
                line: 0,
                column: 0,
            })?;
            let reader = BufReader::new(file);
            for line_res in reader.lines() {
                let l = line_res.map_err(|e| UcabaError::Runtime {
                    message: format!("Error al leer línea de '{}': {}", path, e),
                    line: 0,
                    column: 0,
                })?;
                lines.push(l.trim_end_matches(&['\r', '\n'][..]).to_string());
            }
        } else if norm_mode == "escritura" || norm_mode == "w" {
            let f = OpenOptions::new()
                .write(true)
                .create(true)
                .truncate(true)
                .open(path)
                .map_err(|e| UcabaError::Runtime {
                    message: format!("Error al abrir archivo '{}' para escritura: {}", path, e),
                    line: 0,
                    column: 0,
                })?;
            writer = Some(f);
        } else if norm_mode == "anexo" || norm_mode == "a" {
            let f = OpenOptions::new()
                .create(true)
                .append(true)
                .open(path)
                .map_err(|e| UcabaError::Runtime {
                    message: format!("Error al abrir archivo '{}' para anexo: {}", path, e),
                    line: 0,
                    column: 0,
                })?;
            writer = Some(f);
        } else {
            return Err(UcabaError::Runtime {
                message: format!(
                    "Modo de archivo no reconocido: '{}'. Use 'lectura' o 'escritura'.",
                    mode
                ),
                line: 0,
                column: 0,
            });
        }

        Ok(Self {
            path: path.to_string(),
            mode: norm_mode,
            lines,
            cursor: 0,
            is_closed: false,
            read_during_iteration: false,
            writer,
        })
    }

    pub fn is_eof(&self) -> bool {
        if self.is_closed {
            return true;
        }
        if self.mode == "lectura" || self.mode == "r" {
            return self.cursor >= self.lines.len();
        }
        true
    }

    pub fn read_line(&mut self) -> Result<Value, UcabaError> {
        if self.is_closed {
            return Err(UcabaError::Runtime {
                message: "Intento de leer de un archivo ya cerrado.".to_string(),
                line: 0,
                column: 0,
            });
        }
        if self.mode != "lectura" && self.mode != "r" {
            return Err(UcabaError::Runtime {
                message: "El archivo no está abierto en modo lectura.".to_string(),
                line: 0,
                column: 0,
            });
        }

        self.read_during_iteration = true;
        if self.cursor >= self.lines.len() {
            return Ok(Value::Cadena(String::new()));
        }
        let line = &self.lines[self.cursor];
        self.cursor += 1;
        Ok(parse_auto_value(line))
    }

    pub fn write_line(&mut self, content: &Value) -> Result<(), UcabaError> {
        if self.is_closed {
            return Err(UcabaError::Runtime {
                message: "Intento de escribir en un archivo ya cerrado.".to_string(),
                line: 0,
                column: 0,
            });
        }
        if let Some(ref mut w) = self.writer {
            writeln!(w, "{}", content.to_canonical_string()).map_err(|e| UcabaError::Runtime {
                message: format!("Error al escribir en archivo: {}", e),
                line: 0,
                column: 0,
            })?;
            w.flush().map_err(|e| UcabaError::Runtime {
                message: format!("Error al descargar buffer de archivo: {}", e),
                line: 0,
                column: 0,
            })?;
            Ok(())
        } else {
            Err(UcabaError::Runtime {
                message: "El archivo no está abierto en modo escritura.".to_string(),
                line: 0,
                column: 0,
            })
        }
    }

    pub fn close(&mut self) {
        if !self.is_closed {
            if let Some(ref mut w) = self.writer {
                let _ = w.flush();
            }
            self.is_closed = true;
        }
    }

    pub fn notify_loop_step(&mut self) {
        if self.mode == "lectura" || self.mode == "r" {
            if !self.read_during_iteration && self.cursor < self.lines.len() {
                self.cursor += 1;
            }
            self.read_during_iteration = false;
        }
    }
}

pub fn parse_auto_value(text: &str) -> Value {
    let stripped = text.trim();
    if stripped.is_empty() {
        return Value::Cadena(text.to_string());
    }

    let upper = stripped.to_uppercase();
    if upper == "VERDADERO" || upper == "TRUE" {
        return Value::Booleano(true);
    }
    if upper == "FALSO" || upper == "FALSE" {
        return Value::Booleano(false);
    }
    if upper == "NULO" || upper == "NULL" || upper == "NONE" {
        return Value::Nulo;
    }

    if let Ok(n) = stripped.parse::<i64>() {
        return Value::Entero(n);
    }

    if stripped.contains('.') || stripped.contains('e') || stripped.contains('E') {
        if let Ok(r) = stripped.parse::<f64>() {
            return Value::Real(r);
        }
    }

    Value::Cadena(text.to_string())
}

#[derive(Debug, Clone)]
pub struct StructInstance {
    pub struct_name: String,
    pub fields: HashMap<String, Value>,
    pub field_order: Vec<String>,
}

#[derive(Debug, Clone)]
pub enum Value {
    Entero(i64),
    Real(f64),
    Flotante(f32),
    Cadena(String),
    Caracter(char),
    Booleano(bool),
    Vector(Vec<Value>),
    Struct(Rc<RefCell<StructInstance>>),
    Archivo(Rc<RefCell<ArchivoHandle>>),
    Nulo,
}

impl PartialEq for Value {
    fn eq(&self, other: &Self) -> bool {
        match (self, other) {
            (Value::Entero(a), Value::Entero(b)) => a == b,
            (Value::Real(a), Value::Real(b)) => a == b,
            (Value::Flotante(a), Value::Flotante(b)) => a == b,
            (Value::Cadena(a), Value::Cadena(b)) => a == b,
            (Value::Caracter(a), Value::Caracter(b)) => a == b,
            (Value::Booleano(a), Value::Booleano(b)) => a == b,
            (Value::Vector(a), Value::Vector(b)) => a == b,
            (Value::Struct(a), Value::Struct(b)) => Rc::ptr_eq(a, b),
            (Value::Archivo(a), Value::Archivo(b)) => Rc::ptr_eq(a, b),
            (Value::Nulo, Value::Nulo) => true,
            // Comparaciones numéricas mixtas
            (Value::Entero(a), Value::Real(b)) => (*a as f64) == *b,
            (Value::Real(a), Value::Entero(b)) => *a == (*b as f64),
            (Value::Entero(a), Value::Flotante(b)) => (*a as f32) == *b,
            (Value::Flotante(a), Value::Entero(b)) => *a == (*b as f32),
            (Value::Real(a), Value::Flotante(b)) => *a == (*b as f64),
            (Value::Flotante(a), Value::Real(b)) => (*a as f64) == *b,
            _ => false,
        }
    }
}

impl Value {
    pub fn is_truthy(&self) -> bool {
        match self {
            Value::Booleano(b) => *b,
            Value::Entero(n) => *n != 0,
            Value::Real(r) => *r != 0.0,
            Value::Flotante(f) => *f != 0.0,
            Value::Cadena(s) => !s.is_empty(),
            Value::Vector(v) => !v.is_empty(),
            Value::Nulo => false,
            _ => true,
        }
    }

    pub fn to_canonical_string(&self) -> String {
        let mut seen = HashSet::new();
        self.to_string_impl(&mut seen)
    }

    fn to_string_impl(&self, seen: &mut HashSet<usize>) -> String {
        match self {
            Value::Booleano(true) => "VERDADERO".to_string(),
            Value::Booleano(false) => "FALSO".to_string(),
            Value::Nulo => "NULO".to_string(),
            Value::Entero(n) => n.to_string(),
            Value::Real(r) => {
                if r.fract() == 0.0 {
                    format!("{:.1}", r)
                } else {
                    r.to_string()
                }
            }
            Value::Flotante(f) => {
                if f.fract() == 0.0 {
                    format!("{:.1}", f)
                } else {
                    let d = *f as f64;
                    d.to_string()
                }
            }
            Value::Cadena(s) => s.clone(),
            Value::Caracter(c) => c.to_string(),
            Value::Vector(v) => {
                let items: Vec<String> = v.iter().map(|item| item.to_string_impl(seen)).collect();
                format!("[{}]", items.join(", "))
            }
            Value::Struct(rc) => {
                let ptr = Rc::as_ptr(rc) as usize;
                let s = rc.borrow();
                if seen.contains(&ptr) {
                    return format!("<{} ...>", s.struct_name);
                }
                seen.insert(ptr);

                let keys: Vec<String> = if !s.field_order.is_empty() {
                    s.field_order.clone()
                } else {
                    let mut k: Vec<String> = s.fields.keys().cloned().collect();
                    k.sort();
                    k
                };

                let items: Vec<String> = keys
                    .iter()
                    .filter_map(|k| {
                        s.fields.get(k).map(|v| {
                            let val_str = match v {
                                Value::Cadena(str_val) => format!("'{}'", str_val),
                                _ => v.to_string_impl(seen),
                            };
                            format!("{}: {}", k, val_str)
                        })
                    })
                    .collect();

                format!("{}{{{}}}", s.struct_name, items.join(", "))
            }
            Value::Archivo(rc) => {
                let h = rc.borrow();
                format!("<ARCHIVO '{}' modo='{}'>", h.path, h.mode)
            }
        }
    }
}

impl fmt::Display for Value {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}", self.to_canonical_string())
    }
}
