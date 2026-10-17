use crate::ast::*;
use crate::error::UcabaError;
use crate::value::Value;
use std::collections::HashMap;

#[derive(Debug, Clone)]
pub struct FunctionData {
    pub params: Vec<(String, DataType)>,
    pub body: Vec<Statement>,
    pub return_type: DataType,
}

#[derive(Debug, Clone)]
pub struct Scope {
    variables: HashMap<String, Value>,
    types: HashMap<String, DataType>,
}

impl Scope {
    pub fn new() -> Self {
        Self {
            variables: HashMap::new(),
            types: HashMap::new(),
        }
    }
}

impl Default for Scope {
    fn default() -> Self {
        Self::new()
    }
}

pub fn check_type_compatibility(var_type: &DataType, val: &mut Value) -> Result<(), UcabaError> {
    match (var_type, &mut *val) {
        (DataType::Entero, Value::Entero(_)) => Ok(()),
        (DataType::Entero, Value::Real(r)) => {
            *val = Value::Entero(*r as i64);
            Ok(())
        }
        (DataType::Entero, Value::Flotante(f)) => {
            *val = Value::Entero(*f as i64);
            Ok(())
        }
        (DataType::Real, Value::Real(_)) => Ok(()),
        (DataType::Real, Value::Entero(n)) => {
            *val = Value::Real(*n as f64);
            Ok(())
        }
        (DataType::Real, Value::Flotante(f)) => {
            *val = Value::Real(*f as f64);
            Ok(())
        }
        (DataType::Flotante, Value::Flotante(_)) => Ok(()),
        (DataType::Flotante, Value::Entero(n)) => {
            *val = Value::Flotante(*n as f32);
            Ok(())
        }
        (DataType::Flotante, Value::Real(r)) => {
            *val = Value::Flotante(*r as f32);
            Ok(())
        }
        (DataType::Cadena, Value::Cadena(_)) => Ok(()),
        (DataType::Caracter, Value::Caracter(_)) => Ok(()),
        (DataType::Caracter, Value::Cadena(s)) if s.chars().count() == 1 => {
            *val = Value::Caracter(s.chars().next().unwrap());
            Ok(())
        }
        (DataType::Booleano, Value::Booleano(_)) => Ok(()),
        (DataType::Archivo, Value::Archivo(_)) | (DataType::Archivo, Value::Nulo) => Ok(()),
        (DataType::Vector(inner), Value::Vector(vec)) => {
            for elem in vec.iter_mut() {
                check_type_compatibility(inner, elem)?;
            }
            Ok(())
        }
        (DataType::Vector(_), Value::Nulo) => Ok(()),
        (DataType::Vector(inner), other) => {
            let mut elem = other.clone();
            check_type_compatibility(inner, &mut elem)?;
            *val = Value::Vector(vec![elem]);
            Ok(())
        }
        (DataType::Matriz(_), Value::Vector(_)) | (DataType::Matriz(_), Value::Nulo) => Ok(()),
        (DataType::Estructura(name), Value::Struct(s)) => {
            if s.borrow().struct_name.eq_ignore_ascii_case(name) {
                Ok(())
            } else {
                Err(UcabaError::Runtime {
                    message: format!(
                        "Tipo incompatible: se esperaba estructura '{}', pero se obtuvo '{}'",
                        name, s.borrow().struct_name
                    ),
                    line: 0,
                    column: 0,
                })
            }
        }
        (DataType::Estructura(_), Value::Nulo) => Ok(()),
        (DataType::Nulo, Value::Nulo) => Ok(()),
        (DataType::Void, _) => Ok(()),
        _ => Err(UcabaError::Runtime {
            message: format!(
                "Incompatibilidad de tipos: no se puede asignar valor a variable de tipo '{}'",
                var_type
            ),
            line: 0,
            column: 0,
        }),
    }
}

#[derive(Debug, Clone)]
pub struct StructDefData {
    pub name: String,
    pub fields: Vec<(String, DataType)>,
}

pub struct Interpreter {
    scopes: Vec<Scope>,
    functions: HashMap<String, FunctionData>,
    struct_defs: HashMap<String, StructDefData>,
    pub output: Vec<String>,
}

#[derive(Debug)]
enum ControlFlow {
    None,
    Return(Value),
}

impl Interpreter {
    pub fn new() -> Self {
        Self {
            scopes: vec![Scope::new()],
            functions: HashMap::new(),
            struct_defs: HashMap::new(),
            output: Vec::new(),
        }
    }

    fn push_scope(&mut self) {
        self.scopes.push(Scope::new());
    }

    fn pop_scope(&mut self) {
        if self.scopes.len() > 1 {
            self.scopes.pop();
        }
    }

    fn set_variable(&mut self, name: &str, mut val: Value) -> Result<(), UcabaError> {
        // Buscar de adentro hacia afuera si ya existe
        for scope in self.scopes.iter_mut().rev() {
            if scope.variables.contains_key(name) {
                if let Some(expected_type) = scope.types.get(name) {
                    check_type_compatibility(expected_type, &mut val)?;
                }
                scope.variables.insert(name.to_string(), val);
                return Ok(());
            }
        }
        // Si no existe, declarar en el scope actual
        self.scopes.last_mut().unwrap().variables.insert(name.to_string(), val);
        Ok(())
    }

    fn declare_variable(&mut self, name: &str, data_type: DataType, mut val: Value) -> Result<(), UcabaError> {
        check_type_compatibility(&data_type, &mut val)?;
        let scope = self.scopes.last_mut().unwrap();
        scope.variables.insert(name.to_string(), val);
        scope.types.insert(name.to_string(), data_type);
        Ok(())
    }

    fn get_variable(&self, name: &str) -> Option<Value> {
        for scope in self.scopes.iter().rev() {
            if let Some(val) = scope.variables.get(name) {
                return Some(val.clone());
            }
        }
        None
    }

    fn get_variable_mut<F>(&mut self, name: &str, f: F) -> Result<(), UcabaError>
    where
        F: FnOnce(&mut Value) -> Result<(), UcabaError>,
    {
        for scope in self.scopes.iter_mut().rev() {
            if let Some(val) = scope.variables.get_mut(name) {
                return f(val);
            }
        }
        Err(UcabaError::Runtime {
            message: format!("Variable no definida: '{}'", name),
            line: 0,
            column: 0,
        })
    }

    fn find_archivo_in_expr(
        &mut self,
        expr: &Expression,
    ) -> Option<std::rc::Rc<std::cell::RefCell<crate::value::ArchivoHandle>>> {
        match expr {
            Expression::MemberAccess { target, .. } => {
                if let Ok(Value::Archivo(a)) = self.eval_expression(target) {
                    Some(a)
                } else {
                    None
                }
            }
            Expression::Unary { expr, .. } => self.find_archivo_in_expr(expr),
            Expression::Binary { left, right, .. } => {
                let l = self.find_archivo_in_expr(left);
                if l.is_some() {
                    l
                } else {
                    self.find_archivo_in_expr(right)
                }
            }
            _ => None,
        }
    }

    fn instantiate_struct(&self, name: &str, parents: &mut std::collections::HashSet<String>) -> Value {
        if let Some(def) = self.struct_defs.get(&name.to_uppercase()) {
            let mut fields = HashMap::new();
            let mut new_parents = parents.clone();
            new_parents.insert(name.to_uppercase());

            for (f_name, f_type) in &def.fields {
                let field_val = match f_type {
                    DataType::Estructura(child_struct) => {
                        if new_parents.contains(&child_struct.to_uppercase()) {
                            Value::Nulo
                        } else {
                            self.instantiate_struct(child_struct, &mut new_parents)
                        }
                    }
                    DataType::Entero => Value::Entero(0),
                    DataType::Real => Value::Real(0.0),
                    DataType::Flotante => Value::Flotante(0.0),
                    DataType::Cadena => Value::Cadena(String::new()),
                    DataType::Caracter => Value::Caracter(' '),
                    DataType::Booleano => Value::Booleano(false),
                    DataType::Vector(_) => Value::Vector(Vec::new()),
                    _ => Value::Nulo,
                };
                fields.insert(f_name.clone(), field_val);
            }

            Value::Struct(std::rc::Rc::new(std::cell::RefCell::new(crate::value::StructInstance {
                struct_name: def.name.clone(),
                fields,
                field_order: def.fields.iter().map(|(n, _)| n.clone()).collect(),
            })))
        } else {
            Value::Nulo
        }
    }

    pub fn run(&mut self, program: &Program) -> Result<(), UcabaError> {
        // 1. Pre-registrar todas las funciones y estructuras declaradas
        for stmt in &program.statements {
            match stmt {
                Statement::FunctionDef {
                    name,
                    params,
                    return_type,
                    body,
                } => {
                    self.functions.insert(
                        name.to_uppercase(),
                        FunctionData {
                            params: params.clone(),
                            body: body.clone(),
                            return_type: return_type.clone(),
                        },
                    );
                }
                Statement::StructDef { name, fields } => {
                    let data = StructDefData {
                        name: name.clone(),
                        fields: fields.clone(),
                    };
                    self.struct_defs.insert(name.clone(), data.clone());
                    self.struct_defs.insert(name.to_uppercase(), data);
                }
                _ => {}
            }
        }

        // 2. Ejecutar sentencias secuencialmente
        for stmt in &program.statements {
            if let ControlFlow::Return(_) = self.execute_statement(stmt)? {
                break;
            }
        }

        Ok(())
    }

    fn execute_statement(&mut self, stmt: &Statement) -> Result<ControlFlow, UcabaError> {
        match stmt {
            Statement::VarDecl {
                var_type,
                name,
                size_exprs,
                init,
            } => {
                let initial_val = if let Some(init_expr) = init {
                    self.eval_expression(init_expr)?
                } else if !size_exprs.is_empty() {
                    let mut sizes = Vec::new();
                    for s_expr in size_exprs {
                        let size_val = self.eval_expression(s_expr)?;
                        let s = match size_val {
                            Value::Entero(n) => n.max(0) as usize,
                            Value::Real(r) => r.max(0.0) as usize,
                            Value::Flotante(f) => f.max(0.0) as usize,
                            _ => {
                                return Err(UcabaError::Runtime {
                                    message: "El tamaño debe ser un número entero".to_string(),
                                    line: 0,
                                    column: 0,
                                });
                            }
                        };
                        sizes.push(s);
                    }

                    fn get_default_elem(dt: &DataType, ctx: &mut Interpreter) -> Value {
                        match dt {
                            DataType::Entero => Value::Entero(0),
                            DataType::Real => Value::Real(0.0),
                            DataType::Flotante => Value::Flotante(0.0),
                            DataType::Cadena => Value::Cadena(String::new()),
                            DataType::Caracter => Value::Caracter(' '),
                            DataType::Booleano => Value::Booleano(false),
                            DataType::Estructura(s_name) => {
                                ctx.instantiate_struct(s_name, &mut std::collections::HashSet::new())
                            }
                            DataType::Vector(inner) | DataType::Matriz(inner) => get_default_elem(inner, ctx),
                            _ => Value::Nulo,
                        }
                    }

                    if sizes.len() == 1 {
                        let size = sizes[0];
                        let mut elements = Vec::with_capacity(size);
                        for _ in 0..size {
                            elements.push(get_default_elem(var_type, self));
                        }
                        Value::Vector(elements)
                    } else if sizes.len() == 2 {
                        let rows = sizes[0];
                        let cols = sizes[1];
                        let mut matrix = Vec::with_capacity(rows);
                        for _ in 0..rows {
                            let mut row = Vec::with_capacity(cols);
                            for _ in 0..cols {
                                row.push(get_default_elem(var_type, self));
                            }
                            matrix.push(Value::Vector(row));
                        }
                        Value::Vector(matrix)
                    } else {
                        Value::Vector(Vec::new())
                    }
                } else {
                    match var_type {
                        DataType::Entero => Value::Entero(0),
                        DataType::Real => Value::Real(0.0),
                        DataType::Flotante => Value::Flotante(0.0),
                        DataType::Cadena => Value::Cadena(String::new()),
                        DataType::Caracter => Value::Caracter(' '),
                        DataType::Booleano => Value::Booleano(false),
                        DataType::Vector(_) | DataType::Matriz(_) => Value::Vector(Vec::new()),
                        DataType::Estructura(s_name) => {
                            self.instantiate_struct(s_name, &mut std::collections::HashSet::new())
                        }
                        _ => Value::Nulo,
                    }
                };

                self.declare_variable(name, var_type.clone(), initial_val)?;
                Ok(ControlFlow::None)
            }
            Statement::Assign { target, val } => {
                let evaluated = self.eval_expression(val)?;
                self.assign_to_target(target, evaluated)?;
                Ok(ControlFlow::None)
            }
            Statement::AssignOp { target, op, val } => {
                let right = self.eval_expression(val)?;
                let current = self.eval_expression(target)?;
                let res = self.eval_binary_op(&current, *op, &right)?;
                self.assign_to_target(target, res)?;
                Ok(ControlFlow::None)
            }
            Statement::Increment { target, is_inc } => {
                let current = self.eval_expression(target)?;
                let one = Value::Entero(1);
                let op = if *is_inc { BinaryOp::Suma } else { BinaryOp::Resta };
                let res = self.eval_binary_op(&current, op, &one)?;
                self.assign_to_target(target, res)?;
                Ok(ControlFlow::None)
            }
            Statement::If {
                condition,
                then_branch,
                else_if_branches,
                else_branch,
            } => {
                let cond_val = self.eval_expression(condition)?;
                if cond_val.is_truthy() {
                    for s in then_branch {
                        if let flow @ ControlFlow::Return(_) = self.execute_statement(s)? {
                            return Ok(flow);
                        }
                    }
                    return Ok(ControlFlow::None);
                }

                for (e_cond_expr, e_body) in else_if_branches {
                    let e_cond = self.eval_expression(e_cond_expr)?;
                    if e_cond.is_truthy() {
                        for s in e_body {
                            if let flow @ ControlFlow::Return(_) = self.execute_statement(s)? {
                                return Ok(flow);
                            }
                        }
                        return Ok(ControlFlow::None);
                    }
                }

                if let Some(else_stmts) = else_branch {
                    for s in else_stmts {
                        if let flow @ ControlFlow::Return(_) = self.execute_statement(s)? {
                            return Ok(flow);
                        }
                    }
                }

                Ok(ControlFlow::None)
            }
            Statement::While { condition, body } => {
                let active_file = self.find_archivo_in_expr(condition);
                while self.eval_expression(condition)?.is_truthy() {
                    for s in body {
                        if let flow @ ControlFlow::Return(_) = self.execute_statement(s)? {
                            return Ok(flow);
                        }
                    }
                    if let Some(ref file) = active_file {
                        file.borrow_mut().notify_loop_step();
                    }
                }
                Ok(ControlFlow::None)
            }
            Statement::DoWhile { body, condition } => {
                let active_file = self.find_archivo_in_expr(condition);
                loop {
                    for s in body {
                        if let flow @ ControlFlow::Return(_) = self.execute_statement(s)? {
                            return Ok(flow);
                        }
                    }
                    if let Some(ref file) = active_file {
                        file.borrow_mut().notify_loop_step();
                    }
                    if !self.eval_expression(condition)?.is_truthy() {
                        break;
                    }
                }
                Ok(ControlFlow::None)
            }
            Statement::For {
                init,
                condition,
                update,
                body,
            } => {
                self.push_scope();
                self.execute_statement(init)?;

                while self.eval_expression(condition)?.is_truthy() {
                    for s in body {
                        if let flow @ ControlFlow::Return(_) = self.execute_statement(s)? {
                            self.pop_scope();
                            return Ok(flow);
                        }
                    }
                    self.execute_statement(update)?;
                }

                self.pop_scope();
                Ok(ControlFlow::None)
            }
            Statement::Return(opt_expr) => {
                let val = if let Some(expr) = opt_expr {
                    self.eval_expression(expr)?
                } else {
                    Value::Nulo
                };
                Ok(ControlFlow::Return(val))
            }
            Statement::Print(args) => {
                let pieces: Result<Vec<String>, UcabaError> = args
                    .iter()
                    .map(|arg| self.eval_expression(arg).map(|v| v.to_canonical_string()))
                    .collect();
                let text = pieces?.join(" ");
                println!("{}", text);
                self.output.push(text);
                Ok(ControlFlow::None)
            }
            Statement::Expr(expr) => {
                self.eval_expression(expr)?;
                Ok(ControlFlow::None)
            }
            Statement::FunctionDef { .. } | Statement::StructDef { .. } => {
                // Ya pre-registradas
                Ok(ControlFlow::None)
            }
        }
    }

    fn assign_to_target(&mut self, target: &Expression, val: Value) -> Result<(), UcabaError> {
        match target {
            Expression::Variable(name) => {
                self.set_variable(name, val)?;
                Ok(())
            }
            Expression::IndexAccess { target: inner, index } => {
                let idx_val = self.eval_expression(index)?;
                let idx = match idx_val {
                    Value::Entero(n) => n as usize,
                    Value::Real(r) => r as usize,
                    Value::Flotante(f) => f as usize,
                    _ => {
                        return Err(UcabaError::Runtime {
                            message: "El índice de acceso debe ser un número entero".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                };

                if let Expression::Variable(var_name) = inner.as_ref() {
                    return self.get_variable_mut(var_name, |container| match container {
                        Value::Vector(vec) => {
                            if idx >= vec.len() {
                                return Err(UcabaError::Runtime {
                                    message: format!(
                                        "Índice fuera de rango: {} (tamaño: {})",
                                        idx,
                                        vec.len()
                                    ),
                                    line: 0,
                                    column: 0,
                                });
                            }
                            let promoted_val = match (&vec[idx], &val) {
                                (Value::Real(_), Value::Entero(n)) => Value::Real(*n as f64),
                                (Value::Flotante(_), Value::Entero(n)) => Value::Flotante(*n as f32),
                                (Value::Entero(_), Value::Real(r)) => Value::Entero(*r as i64),
                                _ => val,
                            };
                            vec[idx] = promoted_val;
                            Ok(())
                        }
                        _ => Err(UcabaError::Runtime {
                            message: format!("La variable '{}' no es un vector indexable", var_name),
                            line: 0,
                            column: 0,
                        }),
                    });
                }

                if let Expression::IndexAccess {
                    target: root,
                    index: row_index,
                } = inner.as_ref()
                {
                    if let Expression::Variable(var_name) = root.as_ref() {
                        let row_idx_val = self.eval_expression(row_index)?;
                        let row_idx = match row_idx_val {
                            Value::Entero(n) => n as usize,
                            Value::Real(r) => r as usize,
                            Value::Flotante(f) => f as usize,
                            _ => {
                                return Err(UcabaError::Runtime {
                                    message: "El índice de fila debe ser un número entero".to_string(),
                                    line: 0,
                                    column: 0,
                                });
                            }
                        };

                        return self.get_variable_mut(var_name, |container| match container {
                            Value::Vector(matrix) => {
                                if row_idx >= matrix.len() {
                                    return Err(UcabaError::Runtime {
                                        message: format!(
                                            "Índice de fila fuera de rango: {} (tamaño: {})",
                                            row_idx,
                                            matrix.len()
                                        ),
                                        line: 0,
                                        column: 0,
                                    });
                                }
                                match &mut matrix[row_idx] {
                                    Value::Vector(row) => {
                                        if idx >= row.len() {
                                            return Err(UcabaError::Runtime {
                                                message: format!(
                                                    "Índice de columna fuera de rango: {} (tamaño: {})",
                                                    idx,
                                                    row.len()
                                                ),
                                                line: 0,
                                                column: 0,
                                            });
                                        }
                                        let promoted_val = match (&row[idx], &val) {
                                            (Value::Real(_), Value::Entero(n)) => Value::Real(*n as f64),
                                            (Value::Flotante(_), Value::Entero(n)) => Value::Flotante(*n as f32),
                                            (Value::Entero(_), Value::Real(r)) => Value::Entero(*r as i64),
                                            _ => val,
                                        };
                                        row[idx] = promoted_val;
                                        Ok(())
                                    }
                                    _ => Err(UcabaError::Runtime {
                                        message: format!("La fila {} de '{}' no es un vector indexable", row_idx, var_name),
                                        line: 0,
                                        column: 0,
                                    }),
                                }
                            }
                            _ => Err(UcabaError::Runtime {
                                message: format!("La variable '{}' no es una matriz", var_name),
                                line: 0,
                                column: 0,
                            }),
                        });
                    }
                }

                Err(UcabaError::Runtime {
                    message: "Asignación compleja por índice aún no soportada".to_string(),
                    line: 0,
                    column: 0,
                })
            }
            Expression::MemberAccess { target, member } => {
                let container = self.eval_expression(target)?;
                match container {
                    Value::Struct(inst) => {
                        let mut borrowed = inst.borrow_mut();
                        let mut found_key = None;
                        for k in borrowed.fields.keys() {
                            if k.eq_ignore_ascii_case(member) {
                                found_key = Some(k.clone());
                                break;
                            }
                        }
                        if let Some(key) = found_key {
                            borrowed.fields.insert(key, val);
                            Ok(())
                        } else {
                            let mut suggestion = String::new();
                            let s_name = borrowed.struct_name.clone();
                            let fields: Vec<String> = borrowed.fields.keys().cloned().collect();
                            for f in &fields {
                                if f.to_lowercase().starts_with(&member.to_lowercase())
                                    || member.to_lowercase().starts_with(&f.to_lowercase())
                                {
                                    suggestion = format!(". ¿Quisiste decir '{}'?", f);
                                    break;
                                }
                            }
                            Err(UcabaError::Runtime {
                                message: format!(
                                    "La estructura '{}' no tiene el campo '{}'{}",
                                    s_name, member, suggestion
                                ),
                                line: 0,
                                column: 0,
                            })
                        }
                    }
                    Value::Nulo => Err(UcabaError::Runtime {
                        message: format!("Intento de asignar el campo '{}' en una referencia nula (NULO)", member),
                        line: 0,
                        column: 0,
                    }),
                    _ => Err(UcabaError::Runtime {
                        message: format!("No se puede asignar el miembro '{}' sobre un tipo no estructura", member),
                        line: 0,
                        column: 0,
                    }),
                }
            }
            _ => Err(UcabaError::Runtime {
                message: "Destino de asignación no válido".to_string(),
                line: 0,
                column: 0,
            }),
        }
    }

    pub fn eval_expression(&mut self, expr: &Expression) -> Result<Value, UcabaError> {
        match expr {
            Expression::LiteralInt(n) => Ok(Value::Entero(*n)),
            Expression::LiteralReal(r) => Ok(Value::Real(*r)),
            Expression::LiteralCadena(s) => Ok(Value::Cadena(s.clone())),
            Expression::LiteralCaracter(c) => Ok(Value::Caracter(*c)),
            Expression::LiteralBool(b) => Ok(Value::Booleano(*b)),
            Expression::LiteralNulo => Ok(Value::Nulo),
            Expression::LiteralVector(elements) => {
                let values: Result<Vec<Value>, UcabaError> = elements
                    .iter()
                    .map(|elem| self.eval_expression(elem))
                    .collect();
                Ok(Value::Vector(values?))
            }
            Expression::Variable(name) => {
                if let Some(val) = self.get_variable(name) {
                    Ok(val)
                } else {
                    Err(UcabaError::Runtime {
                        message: format!("Variable no definida: '{}'", name),
                        line: 0,
                        column: 0,
                    })
                }
            }
            Expression::Binary { left, op, right } => {
                let left_val = self.eval_expression(left)?;
                let right_val = self.eval_expression(right)?;
                self.eval_binary_op(&left_val, *op, &right_val)
            }
            Expression::Unary { op, expr } => {
                let val = self.eval_expression(expr)?;
                match op {
                    UnaryOp::No => Ok(Value::Booleano(!val.is_truthy())),
                    UnaryOp::Negativo => match val {
                        Value::Entero(n) => Ok(Value::Entero(-n)),
                        Value::Real(r) => Ok(Value::Real(-r)),
                        Value::Flotante(f) => Ok(Value::Flotante(-f)),
                        _ => Err(UcabaError::Runtime {
                            message: "Operador unario '-' no aplicable a tipo no numérico".to_string(),
                            line: 0,
                            column: 0,
                        }),
                    },
                    UnaryOp::Positivo => match val {
                        Value::Entero(n) => Ok(Value::Entero(n)),
                        Value::Real(r) => Ok(Value::Real(r)),
                        Value::Flotante(f) => Ok(Value::Flotante(f)),
                        _ => Err(UcabaError::Runtime {
                            message: "Operador unario '+' no aplicable a tipo no numérico".to_string(),
                            line: 0,
                            column: 0,
                        }),
                    },
                }
            }
            Expression::IndexAccess { target, index } => {
                let target_val = self.eval_expression(target)?;
                let index_val = self.eval_expression(index)?;
                let idx = match index_val {
                    Value::Entero(n) => n as usize,
                    Value::Real(r) => r as usize,
                    Value::Flotante(f) => f as usize,
                    _ => {
                        return Err(UcabaError::Runtime {
                            message: "El índice de vector debe ser un número entero".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                };

                match target_val {
                    Value::Vector(vec) => {
                        if idx >= vec.len() {
                            return Err(UcabaError::Runtime {
                                message: format!(
                                    "Índice fuera de límites: {} (tamaño: {})",
                                    idx,
                                    vec.len()
                                ),
                                line: 0,
                                column: 0,
                            });
                        }
                        Ok(vec[idx].clone())
                    }
                    _ => Err(UcabaError::Runtime {
                        message: "Acceso por índice sobre un elemento no indexable".to_string(),
                        line: 0,
                        column: 0,
                    }),
                }
            }
            Expression::MemberAccess { target, member } => {
                let target_val = self.eval_expression(target)?;
                if member == "largo" {
                    match target_val {
                        Value::Vector(v) => Ok(Value::Entero(v.len() as i64)),
                        Value::Cadena(s) => Ok(Value::Entero(s.chars().count() as i64)),
                        _ => Err(UcabaError::Runtime {
                            message: "Propiedad '.largo' solo disponible en vectores o cadenas".to_string(),
                            line: 0,
                            column: 0,
                        }),
                    }
                } else if member == "findearchivo" {
                    if let Value::Archivo(file) = target_val {
                        Ok(Value::Booleano(file.borrow().is_eof()))
                    } else {
                        Err(UcabaError::Runtime {
                            message: "Propiedad '.findearchivo' solo disponible en tipo ARCHIVO".to_string(),
                            line: 0,
                            column: 0,
                        })
                    }
                } else {
                    match target_val {
                        Value::Struct(inst) => {
                            let borrowed = inst.borrow();
                            let mut found_val = None;
                            for (k, v) in &borrowed.fields {
                                if k.eq_ignore_ascii_case(member) {
                                    found_val = Some(v.clone());
                                    break;
                                }
                            }
                            if let Some(val) = found_val {
                                Ok(val)
                            } else {
                                let mut suggestion = String::new();
                                for k in borrowed.fields.keys() {
                                    if k.to_lowercase().starts_with(&member.to_lowercase())
                                        || member.to_lowercase().starts_with(&k.to_lowercase())
                                    {
                                        suggestion = format!(". ¿Quisiste decir '{}'?", k);
                                        break;
                                    }
                                }
                                Err(UcabaError::Runtime {
                                    message: format!(
                                        "La estructura '{}' no tiene el campo '{}'{}",
                                        borrowed.struct_name, member, suggestion
                                    ),
                                    line: 0,
                                    column: 0,
                                })
                            }
                        }
                        Value::Nulo => Err(UcabaError::Runtime {
                            message: format!("Intento de acceder al campo '{}' en una referencia nula (NULO)", member),
                            line: 0,
                            column: 0,
                        }),
                        _ => Err(UcabaError::Runtime {
                            message: format!("Acceso a miembro '.{}' sobre tipo no estructura", member),
                            line: 0,
                            column: 0,
                        }),
                    }
                }
            }
            Expression::MethodCall { target, method, args } => {
                let target_val = self.eval_expression(target)?;
                let method_upper = method.to_uppercase();

                match target_val {
                    Value::Archivo(file) => {
                        if method_upper == "LEER_LINEA" {
                            file.borrow_mut().read_line()
                        } else if method_upper == "ESCRIBIR_LINEA" {
                            let content = if !args.is_empty() {
                                self.eval_expression(&args[0])?
                            } else {
                                Value::Cadena(String::new())
                            };
                            file.borrow_mut().write_line(&content)?;
                            Ok(Value::Nulo)
                        } else if method_upper == "CERRAR_ARCHIVO" {
                            file.borrow_mut().close();
                            Ok(Value::Nulo)
                        } else {
                            Err(UcabaError::Runtime {
                                message: format!("Método '{}' no existe en tipo ARCHIVO", method),
                                line: 0,
                                column: 0,
                            })
                        }
                    }
                    _ => Err(UcabaError::Runtime {
                        message: format!("Llamada a método '{}' sobre tipo no compatible", method),
                        line: 0,
                        column: 0,
                    }),
                }
            }
            Expression::Call { name, args } => {
                let upper = name.to_uppercase();

                // Built-in ABRIR_ARCHIVO
                if upper == "ABRIR_ARCHIVO" {
                    if args.len() != 2 {
                        return Err(UcabaError::Runtime {
                            message: "ABRIR_ARCHIVO requiere exactamente 2 argumentos (ruta, modo)".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                    let path_val = self.eval_expression(&args[0])?;
                    let mode_val = self.eval_expression(&args[1])?;
                    let path = match path_val {
                        Value::Cadena(s) => s,
                        _ => path_val.to_canonical_string(),
                    };
                    let mode = match mode_val {
                        Value::Cadena(s) => s,
                        _ => mode_val.to_canonical_string(),
                    };
                    let handle = crate::value::ArchivoHandle::new(&path, &mode)?;
                    return Ok(Value::Archivo(std::rc::Rc::new(std::cell::RefCell::new(handle))));
                }

                // Built-in ESPAR / ESIMPAR
                if upper == "ESPAR" {
                    if args.len() != 1 {
                        return Err(UcabaError::Runtime {
                            message: "ESPAR requiere exactamente 1 argumento".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                    let val = self.eval_expression(&args[0])?;
                    let n = match val {
                        Value::Entero(n) => n,
                        _ => {
                            return Err(UcabaError::Runtime {
                                message: "ESPAR requiere un número entero".to_string(),
                                line: 0,
                                column: 0,
                            });
                        }
                    };
                    return Ok(Value::Booleano(n % 2 == 0));
                }

                if upper == "ESIMPAR" {
                    if args.len() != 1 {
                        return Err(UcabaError::Runtime {
                            message: "ESIMPAR requiere exactamente 1 argumento".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                    let val = self.eval_expression(&args[0])?;
                    let n = match val {
                        Value::Entero(n) => n,
                        _ => {
                            return Err(UcabaError::Runtime {
                                message: "ESIMPAR requiere un número entero".to_string(),
                                line: 0,
                                column: 0,
                            });
                        }
                    };
                    return Ok(Value::Booleano(n % 2 != 0));
                }

                if upper == "MOD" {
                    if args.len() != 2 {
                        return Err(UcabaError::Runtime {
                            message: "MOD requiere exactamente 2 argumentos".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                    let a_val = self.eval_expression(&args[0])?;
                    let b_val = self.eval_expression(&args[1])?;
                    let (a, b) = match (a_val, b_val) {
                        (Value::Entero(a), Value::Entero(b)) => (a, b),
                        _ => {
                            return Err(UcabaError::Runtime {
                                message: "MOD requiere argumentos enteros".to_string(),
                                line: 0,
                                column: 0,
                            });
                        }
                    };
                    if b == 0 {
                        return Err(UcabaError::Runtime {
                            message: "Módulo por cero.".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                    return Ok(Value::Entero(a.rem_euclid(b)));
                }

                // Función de usuario
                let func_data = if let Some(fd) = self.functions.get(&upper) {
                    fd.clone()
                } else {
                    return Err(UcabaError::Runtime {
                        message: format!("Función no definida: '{}'", name),
                        line: 0,
                        column: 0,
                    });
                };

                if args.len() != func_data.params.len() {
                    return Err(UcabaError::Runtime {
                        message: format!(
                            "La función '{}' esperaba {} argumentos pero recibió {}",
                            name,
                            func_data.params.len(),
                            args.len()
                        ),
                        line: 0,
                        column: 0,
                    });
                }

                let mut evaluated_args = Vec::new();
                for arg in args {
                    evaluated_args.push(self.eval_expression(arg)?);
                }

                // Crear un nuevo frame de ejecución aislado para la función
                self.push_scope();
                for (i, (p_name, p_type)) in func_data.params.iter().enumerate() {
                    self.declare_variable(p_name, p_type.clone(), evaluated_args[i].clone())?;
                }

                let mut ret_val = Value::Nulo;
                for stmt in &func_data.body {
                    if let ControlFlow::Return(v) = self.execute_statement(stmt)? {
                        ret_val = v;
                        break;
                    }
                }

                self.pop_scope();
                Ok(ret_val)
            }
        }
    }

    fn eval_binary_op(&mut self, left: &Value, op: BinaryOp, right: &Value) -> Result<Value, UcabaError> {
        match op {
            BinaryOp::Suma => {
                // Cadena + Cualquier cosa
                if let Value::Cadena(s) = left {
                    return Ok(Value::Cadena(format!("{}{}", s, right.to_canonical_string())));
                }
                if let Value::Cadena(s) = right {
                    return Ok(Value::Cadena(format!("{}{}", left.to_canonical_string(), s)));
                }

                // Vector + Vector (Concatenación)
                if let (Value::Vector(v1), Value::Vector(v2)) = (left, right) {
                    let mut combined = v1.clone();
                    combined.extend(v2.clone());
                    return Ok(Value::Vector(combined));
                }

                // Operaciones numéricas
                match (left, right) {
                    (Value::Entero(a), Value::Entero(b)) => Ok(Value::Entero(a + b)),
                    (Value::Real(a), Value::Real(b)) => Ok(Value::Real(a + b)),
                    (Value::Entero(a), Value::Real(b)) => Ok(Value::Real(*a as f64 + b)),
                    (Value::Real(a), Value::Entero(b)) => Ok(Value::Real(a + *b as f64)),
                    (Value::Flotante(a), Value::Flotante(b)) => Ok(Value::Flotante(a + b)),
                    _ => Err(UcabaError::Runtime {
                        message: format!("Operador '+' no compatible con tipos '{:?}' y '{:?}'", left, right),
                        line: 0,
                        column: 0,
                    }),
                }
            }
            BinaryOp::Resta => match (left, right) {
                (Value::Entero(a), Value::Entero(b)) => Ok(Value::Entero(a - b)),
                (Value::Real(a), Value::Real(b)) => Ok(Value::Real(a - b)),
                (Value::Entero(a), Value::Real(b)) => Ok(Value::Real(*a as f64 - b)),
                (Value::Real(a), Value::Entero(b)) => Ok(Value::Real(a - *b as f64)),
                (Value::Flotante(a), Value::Flotante(b)) => Ok(Value::Flotante(a - b)),
                _ => Err(UcabaError::Runtime {
                    message: "Operador '-' solo compatible con números".to_string(),
                    line: 0,
                    column: 0,
                }),
            },
            BinaryOp::Mult => match (left, right) {
                (Value::Entero(a), Value::Entero(b)) => Ok(Value::Entero(a * b)),
                (Value::Real(a), Value::Real(b)) => Ok(Value::Real(a * b)),
                (Value::Entero(a), Value::Real(b)) => Ok(Value::Real(*a as f64 * b)),
                (Value::Real(a), Value::Entero(b)) => Ok(Value::Real(a * *b as f64)),
                (Value::Flotante(a), Value::Flotante(b)) => Ok(Value::Flotante(a * b)),
                _ => Err(UcabaError::Runtime {
                    message: "Operador '*' solo compatible con números".to_string(),
                    line: 0,
                    column: 0,
                }),
            },
            BinaryOp::Div => {
                // División real '/': siempre retorna REAL
                let (a, b) = match (left, right) {
                    (Value::Entero(a), Value::Entero(b)) => (*a as f64, *b as f64),
                    (Value::Real(a), Value::Real(b)) => (*a, *b),
                    (Value::Entero(a), Value::Real(b)) => (*a as f64, *b),
                    (Value::Real(a), Value::Entero(b)) => (*a, *b as f64),
                    _ => {
                        return Err(UcabaError::Runtime {
                            message: "Operador '/' solo compatible con números".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                };
                if b == 0.0 {
                    return Err(UcabaError::Runtime {
                        message: "División por cero.".to_string(),
                        line: 0,
                        column: 0,
                    });
                }
                Ok(Value::Real(a / b))
            }
            BinaryOp::DivEntera => {
                // División entera '//': siempre retorna ENTERO
                let (a, b) = match (left, right) {
                    (Value::Entero(a), Value::Entero(b)) => (*a, *b),
                    (Value::Real(a), Value::Real(b)) => (a.floor() as i64, b.floor() as i64),
                    (Value::Entero(a), Value::Real(b)) => (*a, b.floor() as i64),
                    (Value::Real(a), Value::Entero(b)) => (a.floor() as i64, *b),
                    _ => {
                        return Err(UcabaError::Runtime {
                            message: "Operador '//' requiere operandos numéricos".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                };
                if b == 0 {
                    return Err(UcabaError::Runtime {
                        message: "División por cero.".to_string(),
                        line: 0,
                        column: 0,
                    });
                }
                Ok(Value::Entero(a.div_euclid(b)))
            }
            BinaryOp::Mod => {
                // Módulo '%': siempre retorna ENTERO
                let (a, b) = match (left, right) {
                    (Value::Entero(a), Value::Entero(b)) => (*a, *b),
                    _ => {
                        return Err(UcabaError::Runtime {
                            message: "Operador '%' requiere operandos enteros".to_string(),
                            line: 0,
                            column: 0,
                        });
                    }
                };
                if b == 0 {
                    return Err(UcabaError::Runtime {
                        message: "Módulo por cero.".to_string(),
                        line: 0,
                        column: 0,
                    });
                }
                Ok(Value::Entero(a.rem_euclid(b)))
            }
            BinaryOp::IgualQue => Ok(Value::Booleano(left == right)),
            BinaryOp::Distinto => Ok(Value::Booleano(left != right)),
            BinaryOp::Menor => match (left, right) {
                (Value::Entero(a), Value::Entero(b)) => Ok(Value::Booleano(a < b)),
                (Value::Real(a), Value::Real(b)) => Ok(Value::Booleano(a < b)),
                (Value::Entero(a), Value::Real(b)) => Ok(Value::Booleano((*a as f64) < *b)),
                (Value::Real(a), Value::Entero(b)) => Ok(Value::Booleano(*a < (*b as f64))),
                _ => Err(UcabaError::Runtime {
                    message: "Operador '<' requiere números".to_string(),
                    line: 0,
                    column: 0,
                }),
            },
            BinaryOp::Mayor => match (left, right) {
                (Value::Entero(a), Value::Entero(b)) => Ok(Value::Booleano(a > b)),
                (Value::Real(a), Value::Real(b)) => Ok(Value::Booleano(a > b)),
                (Value::Entero(a), Value::Real(b)) => Ok(Value::Booleano((*a as f64) > *b)),
                (Value::Real(a), Value::Entero(b)) => Ok(Value::Booleano(*a > (*b as f64))),
                _ => Err(UcabaError::Runtime {
                    message: "Operador '>' requiere números".to_string(),
                    line: 0,
                    column: 0,
                }),
            },
            BinaryOp::MenorIgual => match (left, right) {
                (Value::Entero(a), Value::Entero(b)) => Ok(Value::Booleano(a <= b)),
                (Value::Real(a), Value::Real(b)) => Ok(Value::Booleano(a <= b)),
                (Value::Entero(a), Value::Real(b)) => Ok(Value::Booleano((*a as f64) <= *b)),
                (Value::Real(a), Value::Entero(b)) => Ok(Value::Booleano(*a <= (*b as f64))),
                _ => Err(UcabaError::Runtime {
                    message: "Operador '<=' requiere números".to_string(),
                    line: 0,
                    column: 0,
                }),
            },
            BinaryOp::MayorIgual => match (left, right) {
                (Value::Entero(a), Value::Entero(b)) => Ok(Value::Booleano(a >= b)),
                (Value::Real(a), Value::Real(b)) => Ok(Value::Booleano(a >= b)),
                (Value::Entero(a), Value::Real(b)) => Ok(Value::Booleano((*a as f64) >= *b)),
                (Value::Real(a), Value::Entero(b)) => Ok(Value::Booleano(*a >= (*b as f64))),
                _ => Err(UcabaError::Runtime {
                    message: "Operador '>=' requiere números".to_string(),
                    line: 0,
                    column: 0,
                }),
            },
            BinaryOp::Y => Ok(Value::Booleano(left.is_truthy() && right.is_truthy())),
            BinaryOp::O => Ok(Value::Booleano(left.is_truthy() || right.is_truthy())),
        }
    }

    pub fn eval_repl_input(&mut self, input: &str) -> Result<Option<Value>, UcabaError> {
        let mut lexer = crate::lexer::Lexer::new(input);
        let tokens = lexer.tokenize()?;

        if tokens.is_empty()
            || (tokens.len() == 1 && matches!(tokens[0].token_type, crate::token::TokenType::Eof))
        {
            return Ok(None);
        }

        let mut parser = crate::parser::Parser::new(tokens, true);
        let program = parser.parse()?;

        if program.statements.is_empty() {
            return Ok(None);
        }

        // Si es una única expresión evaluable (ej: `10 + 20` o `x`), retornar el valor
        if program.statements.len() == 1 {
            if let Statement::Expr(expr) = &program.statements[0] {
                let val = self.eval_expression(expr)?;
                return Ok(Some(val));
            }
        }

        self.run(&program)?;
        Ok(None)
    }

    pub fn get_variables(&self) -> Vec<(String, DataType, Value)> {
        let mut vars = Vec::new();
        for scope in &self.scopes {
            let mut keys: Vec<String> = scope.variables.keys().cloned().collect();
            keys.sort();
            for k in keys {
                let val = scope.variables.get(&k).unwrap().clone();
                let dt = scope.types.get(&k).cloned().unwrap_or(DataType::Void);
                vars.push((k, dt, val));
            }
        }
        vars
    }

    pub fn reset(&mut self) {
        self.scopes = vec![Scope::new()];
        self.functions.clear();
        self.struct_defs.clear();
        self.output.clear();
    }
}

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
enum BlockKind {
    Inicio,
    Funcion,
    Procedimiento,
    Estructura,
    Si,
    Mientras,
    Hacer,
    Para,
}

pub fn is_input_complete(input: &str) -> bool {
    let mut lexer = crate::lexer::Lexer::new(input);
    let tokens = match lexer.tokenize() {
        Ok(t) => t,
        Err(_) => return true,
    };

    let mut stack: Vec<BlockKind> = Vec::new();
    let mut parens: i32 = 0;
    let mut brackets: i32 = 0;
    let mut after_fin = false;
    let mut after_sino = false;

    for tok in tokens {
        match tok.token_type {
            crate::token::TokenType::ParentesisIzq => {
                parens += 1;
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::ParentesisDer => {
                if parens > 0 {
                    parens -= 1;
                }
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::CorcheteIzq => {
                brackets += 1;
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::CorcheteDer => {
                if brackets > 0 {
                    brackets -= 1;
                }
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::KwInicio => {
                stack.push(BlockKind::Inicio);
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::KwFuncion => {
                if !after_fin {
                    stack.push(BlockKind::Funcion);
                }
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::KwProcedimiento => {
                if !after_fin {
                    stack.push(BlockKind::Procedimiento);
                }
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::KwEstructura => {
                if !after_fin {
                    stack.push(BlockKind::Estructura);
                }
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::KwSi => {
                if !after_fin && !after_sino {
                    stack.push(BlockKind::Si);
                }
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::KwSino => {
                after_sino = true;
                after_fin = false;
            }
            crate::token::TokenType::KwMientras => {
                if !after_fin && stack.last() != Some(&BlockKind::Hacer) {
                    stack.push(BlockKind::Mientras);
                }
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::KwHacer => {
                if !after_fin {
                    stack.push(BlockKind::Hacer);
                }
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::KwPara => {
                if !after_fin {
                    stack.push(BlockKind::Para);
                }
                after_fin = false;
                after_sino = false;
            }
            crate::token::TokenType::KwFin => {
                let _ = stack.pop();
                after_fin = true;
                after_sino = false;
            }
            crate::token::TokenType::Eof => {}
            _ => {
                after_fin = false;
                after_sino = false;
            }
        }
    }

    stack.is_empty() && parens == 0 && brackets == 0
}

impl Default for Interpreter {
    fn default() -> Self {
        Self::new()
    }
}
