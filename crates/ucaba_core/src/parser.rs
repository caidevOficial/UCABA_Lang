use crate::ast::*;
use crate::error::UcabaError;
use crate::token::{Token, TokenType};

pub struct Parser {
    tokens: Vec<Token>,
    pos: usize,
    _lenient: bool,
}

impl Parser {
    pub fn new(tokens: Vec<Token>, lenient: bool) -> Self {
        Self {
            tokens,
            pos: 0,
            _lenient: lenient,
        }
    }

    fn current(&self) -> &Token {
        if self.pos >= self.tokens.len() {
            self.tokens.last().unwrap()
        } else {
            &self.tokens[self.pos]
        }
    }

    fn previous(&self) -> &Token {
        if self.pos > 0 {
            &self.tokens[self.pos - 1]
        } else {
            &self.tokens[0]
        }
    }

    fn peek(&self, offset: usize) -> &Token {
        let idx = self.pos + offset;
        if idx >= self.tokens.len() {
            self.tokens.last().unwrap()
        } else {
            &self.tokens[idx]
        }
    }

    fn is_at_end(&self) -> bool {
        matches!(self.current().token_type, TokenType::Eof)
    }

    fn advance(&mut self) -> Token {
        let tok = self.current().clone();
        if !self.is_at_end() {
            self.pos += 1;
        }
        tok
    }

    fn check(&self, tok_type: &TokenType) -> bool {
        if self.is_at_end() {
            false
        } else {
            &self.current().token_type == tok_type
        }
    }

    fn match_token(&mut self, tok_type: &TokenType) -> bool {
        if self.check(tok_type) {
            self.advance();
            true
        } else {
            false
        }
    }

    fn consume(&mut self, tok_type: &TokenType, msg: &str) -> Result<Token, UcabaError> {
        if self.check(tok_type) {
            Ok(self.advance())
        } else {
            let tok = self.current();
            Err(UcabaError::Parse {
                message: format!("{} (se encontró '{:?}')", msg, tok.token_type),
                line: tok.line,
                column: tok.column,
            })
        }
    }

    fn consume_ident(&mut self, msg: &str) -> Result<String, UcabaError> {
        if let TokenType::Identificador(name) = &self.current().token_type {
            let n = name.clone();
            self.advance();
            Ok(n)
        } else {
            let tok = self.current();
            Err(UcabaError::Parse {
                message: format!("{} (se encontró '{:?}')", msg, tok.token_type),
                line: tok.line,
                column: tok.column,
            })
        }
    }

    pub fn parse(&mut self) -> Result<Program, UcabaError> {
        let mut statements = Vec::new();

        while !self.is_at_end() {
            if self.match_token(&TokenType::KwInicio) {
                while !self.is_at_end() && !self.check(&TokenType::KwFin) {
                    statements.push(self.parse_statement()?);
                }
                self.consume(&TokenType::KwFin, "Se esperaba 'FIN' para cerrar el bloque 'INICIO'")?;
                continue;
            }

            statements.push(self.parse_statement()?);
        }

        Ok(Program { statements })
    }

    fn parse_statement(&mut self) -> Result<Statement, UcabaError> {
        // Palabras clave de control
        if self.match_token(&TokenType::KwSi) {
            return self.parse_if();
        }
        if self.match_token(&TokenType::KwPara) {
            return self.parse_for();
        }
        if self.match_token(&TokenType::KwMientras) {
            return self.parse_while();
        }
        if self.match_token(&TokenType::KwHacer) {
            return self.parse_do_while();
        }
        if self.match_token(&TokenType::KwRetornar) {
            return self.parse_return();
        }
        if self.match_token(&TokenType::KwImprimir) {
            return self.parse_print();
        }
        if self.match_token(&TokenType::KwFuncion) {
            return self.parse_function();
        }
        if self.match_token(&TokenType::KwProcedimiento) {
            return self.parse_procedure();
        }
        if self.match_token(&TokenType::KwEstructura) {
            return self.parse_struct_def();
        }

        // Declaración de variable tipada (ej: ENTERO x, CADENA s, Nodo n)
        if self.is_type_start() {
            return self.parse_var_decl();
        }

        // Asignación, incremento/decremento o expresión
        let expr = self.parse_expression()?;

        if self.match_token(&TokenType::Asignar) {
            let val = self.parse_expression()?;
            self.match_token(&TokenType::PuntoYComa);
            return Ok(Statement::Assign { target: expr, val });
        }

        if self.match_token(&TokenType::AsigSuma) {
            let val = self.parse_expression()?;
            self.match_token(&TokenType::PuntoYComa);
            return Ok(Statement::AssignOp {
                target: expr,
                op: BinaryOp::Suma,
                val,
            });
        }

        if self.match_token(&TokenType::AsigResta) {
            let val = self.parse_expression()?;
            self.match_token(&TokenType::PuntoYComa);
            return Ok(Statement::AssignOp {
                target: expr,
                op: BinaryOp::Resta,
                val,
            });
        }

        if self.match_token(&TokenType::Inc) {
            self.match_token(&TokenType::PuntoYComa);
            return Ok(Statement::Increment {
                target: expr,
                is_inc: true,
            });
        }

        if self.match_token(&TokenType::Dec) {
            self.match_token(&TokenType::PuntoYComa);
            return Ok(Statement::Increment {
                target: expr,
                is_inc: false,
            });
        }

        self.match_token(&TokenType::PuntoYComa);
        Ok(Statement::Expr(expr))
    }

    fn is_type_start(&self) -> bool {
        match &self.current().token_type {
            TokenType::TipoEntero
            | TokenType::TipoFlotante
            | TokenType::TipoReal
            | TokenType::TipoCadena
            | TokenType::TipoCaracter
            | TokenType::TipoBooleano
            | TokenType::TipoArchivo => true,
            TokenType::Identificador(_) => {
                // Podría ser el nombre de una estructura (ej: 'Nodo nuevo_nodo')
                let next = self.peek(1);
                matches!(next.token_type, TokenType::Identificador(_))
            }
            _ => false,
        }
    }

    fn parse_type(&mut self) -> Result<DataType, UcabaError> {
        let base_type = match &self.current().token_type {
            TokenType::TipoEntero => {
                self.advance();
                DataType::Entero
            }
            TokenType::TipoFlotante => {
                self.advance();
                DataType::Flotante
            }
            TokenType::TipoReal => {
                self.advance();
                DataType::Real
            }
            TokenType::TipoCadena => {
                self.advance();
                DataType::Cadena
            }
            TokenType::TipoCaracter => {
                self.advance();
                DataType::Caracter
            }
            TokenType::TipoBooleano => {
                self.advance();
                DataType::Booleano
            }
            TokenType::TipoArchivo => {
                self.advance();
                DataType::Archivo
            }
            TokenType::TipoVoid => {
                self.advance();
                DataType::Void
            }
            TokenType::Identificador(name) => {
                let s_name = name.clone();
                self.advance();
                DataType::Estructura(s_name)
            }
            _ => {
                let tok = self.current();
                return Err(UcabaError::Parse {
                    message: format!("Tipo de dato esperado, se encontró '{:?}'", tok.token_type),
                    line: tok.line,
                    column: tok.column,
                });
            }
        };

        let mut final_type = base_type;
        while self.match_token(&TokenType::CorcheteIzq) {
            self.consume(&TokenType::CorcheteDer, "Se esperaba ']' tras '[' en especificación de tipo vector/matriz")?;
            final_type = match final_type {
                DataType::Vector(inner) => DataType::Matriz(inner),
                other => DataType::Vector(Box::new(other)),
            };
        }

        Ok(final_type)
    }

    fn parse_condition_expression(&mut self) -> Result<Expression, UcabaError> {
        self.parse_expression()
    }

    fn parse_var_decl(&mut self) -> Result<Statement, UcabaError> {
        let base_type = self.parse_type()?;
        let name = self.consume_ident("Se esperaba el nombre de la variable")?;

        // Puede ser array o matriz con dimensión o corchetes: ENTERO v[], ENTERO v[10], ENTERO m[2][2], REAL matriz_t[][]
        let mut size_exprs = Vec::new();
        let mut is_array = false;
        let mut bracket_count = 0;
        while self.match_token(&TokenType::CorcheteIzq) {
            is_array = true;
            bracket_count += 1;
            if !self.check(&TokenType::CorcheteDer) {
                size_exprs.push(self.parse_expression()?);
            }
            self.consume(&TokenType::CorcheteDer, "Se esperaba ']' tras corchetes de array/matriz")?;
        }

        let mut final_type = base_type;
        if is_array && !matches!(final_type, DataType::Vector(_) | DataType::Matriz(_)) {
            if bracket_count >= 2 {
                final_type = DataType::Matriz(Box::new(final_type));
            } else {
                final_type = DataType::Vector(Box::new(final_type));
            }
        }

        let mut init = None;
        if self.match_token(&TokenType::Asignar) {
            init = Some(self.parse_expression()?);
        }

        let _ = self.match_token(&TokenType::PuntoYComa) || self.match_token(&TokenType::DosPuntos);

        Ok(Statement::VarDecl {
            var_type: final_type,
            name,
            size_exprs,
            init,
        })
    }

    fn parse_if(&mut self) -> Result<Statement, UcabaError> {
        let condition = self.parse_condition_expression()?;

        let mut then_branch = Vec::new();
        let mut else_if_branches = Vec::new();
        let mut else_branch = None;

        while !self.is_at_end()
            && !self.check(&TokenType::KwSino)
            && !self.is_fin_block("SI")
        {
            then_branch.push(self.parse_statement()?);
        }

        while self.match_token(&TokenType::KwSino) {
            if self.match_token(&TokenType::KwSi) {
                let e_cond = self.parse_condition_expression()?;
                let mut e_body = Vec::new();
                while !self.is_at_end()
                    && !self.check(&TokenType::KwSino)
                    && !self.is_fin_block("SI")
                {
                    e_body.push(self.parse_statement()?);
                }
                else_if_branches.push((e_cond, e_body));
            } else {
                let mut else_body = Vec::new();
                while !self.is_at_end() && !self.is_fin_block("SI") {
                    else_body.push(self.parse_statement()?);
                }
                else_branch = Some(else_body);
                break;
            }
        }

        self.consume_fin_block("SI")?;

        Ok(Statement::If {
            condition,
            then_branch,
            else_if_branches,
            else_branch,
        })
    }

    fn parse_for(&mut self) -> Result<Statement, UcabaError> {
        self.consume(&TokenType::ParentesisIzq, "Se esperaba '(' tras 'PARA'")?;
        let init = Box::new(self.parse_statement()?);
        let condition = self.parse_expression()?;
        if !self.match_token(&TokenType::PuntoYComa) && !self.match_token(&TokenType::DosPuntos) {
            return Err(UcabaError::Parse {
                message: "Se esperaba ';' o ':' tras condición del bucle 'PARA'".to_string(),
                line: self.current().line,
                column: self.current().column,
            });
        }

        let update_stmt = if self.is_type_start() {
            self.parse_var_decl()?
        } else {
            let expr = self.parse_expression()?;
            if self.match_token(&TokenType::Inc) {
                Statement::Increment { target: expr, is_inc: true }
            } else if self.match_token(&TokenType::Dec) {
                Statement::Increment { target: expr, is_inc: false }
            } else if self.match_token(&TokenType::Asignar) {
                let val = self.parse_expression()?;
                Statement::Assign { target: expr, val }
            } else if self.match_token(&TokenType::AsigSuma) {
                let val = self.parse_expression()?;
                Statement::AssignOp { target: expr, op: BinaryOp::Suma, val }
            } else if self.match_token(&TokenType::AsigResta) {
                let val = self.parse_expression()?;
                Statement::AssignOp { target: expr, op: BinaryOp::Resta, val }
            } else {
                Statement::Expr(expr)
            }
        };

        self.consume(&TokenType::ParentesisDer, "Se esperaba ')' tras actualización del bucle 'PARA'")?;

        let mut body = Vec::new();
        while !self.is_at_end() && !self.is_fin_block("PARA") {
            body.push(self.parse_statement()?);
        }

        self.consume_fin_block("PARA")?;

        Ok(Statement::For {
            init,
            condition,
            update: Box::new(update_stmt),
            body,
        })
    }

    fn parse_while(&mut self) -> Result<Statement, UcabaError> {
        let condition = self.parse_condition_expression()?;

        let mut body = Vec::new();
        while !self.is_at_end() && !self.is_fin_block("MIENTRAS") {
            body.push(self.parse_statement()?);
        }

        self.consume_fin_block("MIENTRAS")?;

        Ok(Statement::While { condition, body })
    }

    fn parse_do_while(&mut self) -> Result<Statement, UcabaError> {
        let mut body = Vec::new();
        while !self.is_at_end() && !self.check(&TokenType::KwMientras) {
            body.push(self.parse_statement()?);
        }

        self.consume(&TokenType::KwMientras, "Se esperaba 'MIENTRAS' tras bloque 'HACER'")?;
        let condition = self.parse_condition_expression()?;
        let _ = self.match_token(&TokenType::PuntoYComa);
        self.consume_fin_block("HACER")?;

        Ok(Statement::DoWhile { body, condition })
    }

    fn parse_return(&mut self) -> Result<Statement, UcabaError> {
        let val = if self.check(&TokenType::PuntoYComa) || self.check(&TokenType::KwFin) || self.is_at_end() {
            None
        } else {
            Some(self.parse_expression()?)
        };
        self.match_token(&TokenType::PuntoYComa);
        Ok(Statement::Return(val))
    }

    fn parse_print(&mut self) -> Result<Statement, UcabaError> {
        self.consume(&TokenType::ParentesisIzq, "Se esperaba '(' tras 'IMPRIMIR'")?;
        let mut args = Vec::new();
        if !self.check(&TokenType::ParentesisDer) {
            loop {
                args.push(self.parse_expression()?);
                if !self.match_token(&TokenType::Coma) {
                    break;
                }
            }
        }
        self.consume(&TokenType::ParentesisDer, "Se esperaba ')' al final de 'IMPRIMIR'")?;
        self.match_token(&TokenType::PuntoYComa);
        Ok(Statement::Print(args))
    }

    fn parse_parameter_list(&mut self) -> Result<Vec<(String, DataType)>, UcabaError> {
        let mut params = Vec::new();

        if !self.check(&TokenType::ParentesisDer) {
            loop {
                let p_name = self.consume_ident("Se esperaba el nombre del parámetro")?;

                let mut bracket_count = 0;
                while self.match_token(&TokenType::CorcheteIzq) {
                    self.consume(&TokenType::CorcheteDer, "Se esperaba ']' tras '[' en especificación del parámetro")?;
                    bracket_count += 1;
                }

                self.consume(&TokenType::DosPuntos, "Se esperaba ':' tras parámetro")?;
                let mut p_type = self.parse_type()?;

                if bracket_count > 0 {
                    fn get_inner_scalar(dt: DataType) -> DataType {
                        match dt {
                            DataType::Vector(inner) => get_inner_scalar(*inner),
                            DataType::Matriz(inner) => get_inner_scalar(*inner),
                            other => other,
                        }
                    }
                    let inner = get_inner_scalar(p_type);
                    if bracket_count >= 2 {
                        p_type = DataType::Matriz(Box::new(inner));
                    } else {
                        p_type = DataType::Vector(Box::new(inner));
                    }
                }

                params.push((p_name, p_type));

                if !self.match_token(&TokenType::Coma) {
                    break;
                }
            }
        }

        Ok(params)
    }

    fn parse_function(&mut self) -> Result<Statement, UcabaError> {
        let name = self.consume_ident("Se esperaba el nombre de la función")?;

        self.consume(&TokenType::ParentesisIzq, "Se esperaba '(' tras nombre de función")?;
        let params = self.parse_parameter_list()?;
        self.consume(&TokenType::ParentesisDer, "Se esperaba ')' tras lista de parámetros")?;
        let close_paren_line = self.previous().line;

        let mut return_type = DataType::Void;
        if self.match_token(&TokenType::DosPuntos) {
            let colon_line = self.previous().line;
            if self.is_type_start() && self.current().line == colon_line {
                return_type = self.parse_type()?;
            }
        } else if self.is_type_start() && self.current().line == close_paren_line {
            return_type = self.parse_type()?;
        }

        let mut body = Vec::new();
        while !self.is_at_end() && !self.is_fin_block("FUNCION") {
            body.push(self.parse_statement()?);
        }

        self.consume_fin_block("FUNCION")?;

        Ok(Statement::FunctionDef {
            name,
            params,
            return_type,
            body,
        })
    }

    fn parse_procedure(&mut self) -> Result<Statement, UcabaError> {
        let name = self.consume_ident("Se esperaba el nombre del procedimiento")?;

        self.consume(&TokenType::ParentesisIzq, "Se esperaba '(' tras nombre del procedimiento")?;
        let params = self.parse_parameter_list()?;
        self.consume(&TokenType::ParentesisDer, "Se esperaba ')' tras parámetros del procedimiento")?;
        self.match_token(&TokenType::DosPuntos);

        let mut body = Vec::new();
        while !self.is_at_end() && !self.is_fin_block("PROCEDIMIENTO") {
            body.push(self.parse_statement()?);
        }

        self.consume_fin_block("PROCEDIMIENTO")?;

        Ok(Statement::FunctionDef {
            name,
            params,
            return_type: DataType::Void,
            body,
        })
    }

    fn parse_struct_def(&mut self) -> Result<Statement, UcabaError> {
        let name = self.consume_ident("Se esperaba el nombre de la estructura")?;

        let _ = self.match_token(&TokenType::DosPuntos);

        let mut fields = Vec::new();
        while !self.is_at_end() && !self.is_fin_block("ESTRUCTURA") {
            let f_type = self.parse_type()?;
            let f_name = self.consume_ident("Se esperaba el nombre del campo de la estructura")?;
            self.match_token(&TokenType::PuntoYComa);
            fields.push((f_name, f_type));
        }

        self.consume_fin_block("ESTRUCTURA")?;

        Ok(Statement::StructDef { name, fields })
    }

    fn is_fin_block(&self, _block_name: &str) -> bool {
        self.check(&TokenType::KwFin)
    }

    fn consume_fin_block(&mut self, block_name: &str) -> Result<(), UcabaError> {
        self.consume(&TokenType::KwFin, &format!("Se esperaba 'FIN {}'", block_name))?;
        // Opcionalmente se admite la palabra clave del bloque tras FIN (ej: 'FIN SI', 'FIN PARA')
        match block_name {
            "SI" => { self.match_token(&TokenType::KwSi); }
            "PARA" => { self.match_token(&TokenType::KwPara); }
            "MIENTRAS" => { self.match_token(&TokenType::KwMientras); }
            "HACER" => { self.match_token(&TokenType::KwHacer); }
            "FUNCION" => { self.match_token(&TokenType::KwFuncion); }
            "PROCEDIMIENTO" => { self.match_token(&TokenType::KwProcedimiento); }
            "ESTRUCTURA" => { self.match_token(&TokenType::KwEstructura); }
            _ => {}
        }
        Ok(())
    }

    // Precedencia de expresiones
    pub fn parse_expression(&mut self) -> Result<Expression, UcabaError> {
        self.parse_logical_or()
    }

    fn parse_logical_or(&mut self) -> Result<Expression, UcabaError> {
        let mut left = self.parse_logical_and()?;
        while self.match_token(&TokenType::OpO) {
            self.match_token(&TokenType::KwSi);
            let right = self.parse_logical_and()?;
            left = Expression::Binary {
                left: Box::new(left),
                op: BinaryOp::O,
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_logical_and(&mut self) -> Result<Expression, UcabaError> {
        let mut left = self.parse_equality()?;
        while self.match_token(&TokenType::OpY) {
            self.match_token(&TokenType::KwSi);
            let right = self.parse_equality()?;
            left = Expression::Binary {
                left: Box::new(left),
                op: BinaryOp::Y,
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_equality(&mut self) -> Result<Expression, UcabaError> {
        let mut left = self.parse_comparison()?;
        loop {
            let op = if self.match_token(&TokenType::IgualQue) {
                BinaryOp::IgualQue
            } else if self.match_token(&TokenType::Distinto) {
                BinaryOp::Distinto
            } else {
                break;
            };
            let right = self.parse_comparison()?;
            left = Expression::Binary {
                left: Box::new(left),
                op,
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_comparison(&mut self) -> Result<Expression, UcabaError> {
        let mut left = self.parse_additive()?;
        loop {
            let op = if self.match_token(&TokenType::Menor) {
                BinaryOp::Menor
            } else if self.match_token(&TokenType::MenorIgual) {
                BinaryOp::MenorIgual
            } else if self.match_token(&TokenType::Mayor) {
                BinaryOp::Mayor
            } else if self.match_token(&TokenType::MayorIgual) {
                BinaryOp::MayorIgual
            } else {
                break;
            };
            let right = self.parse_additive()?;
            left = Expression::Binary {
                left: Box::new(left),
                op,
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_additive(&mut self) -> Result<Expression, UcabaError> {
        let mut left = self.parse_multiplicative()?;
        loop {
            let op = if self.match_token(&TokenType::Suma) {
                BinaryOp::Suma
            } else if self.match_token(&TokenType::Resta) {
                BinaryOp::Resta
            } else {
                break;
            };
            let right = self.parse_multiplicative()?;
            left = Expression::Binary {
                left: Box::new(left),
                op,
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_multiplicative(&mut self) -> Result<Expression, UcabaError> {
        let mut left = self.parse_unary()?;
        loop {
            let op = if self.match_token(&TokenType::Mult) {
                BinaryOp::Mult
            } else if self.match_token(&TokenType::Div) {
                BinaryOp::Div
            } else if self.match_token(&TokenType::DivEntera) {
                BinaryOp::DivEntera
            } else if self.match_token(&TokenType::Mod) || self.match_token(&TokenType::KwMod) {
                BinaryOp::Mod
            } else {
                break;
            };
            let right = self.parse_unary()?;
            left = Expression::Binary {
                left: Box::new(left),
                op,
                right: Box::new(right),
            };
        }
        Ok(left)
    }

    fn parse_unary(&mut self) -> Result<Expression, UcabaError> {
        if self.match_token(&TokenType::OpNo) {
            let expr = self.parse_unary()?;
            return Ok(Expression::Unary {
                op: UnaryOp::No,
                expr: Box::new(expr),
            });
        }
        if self.match_token(&TokenType::Resta) {
            let expr = self.parse_unary()?;
            return Ok(Expression::Unary {
                op: UnaryOp::Negativo,
                expr: Box::new(expr),
            });
        }
        if self.match_token(&TokenType::Suma) {
            let expr = self.parse_unary()?;
            return Ok(Expression::Unary {
                op: UnaryOp::Positivo,
                expr: Box::new(expr),
            });
        }

        self.parse_postfix()
    }

    fn parse_postfix(&mut self) -> Result<Expression, UcabaError> {
        let mut expr = self.parse_primary()?;

        loop {
            if self.match_token(&TokenType::ParentesisIzq) {
                // Llamada a función: expr(arg1, arg2)
                let mut args = Vec::new();
                if !self.check(&TokenType::ParentesisDer) {
                    loop {
                        args.push(self.parse_expression()?);
                        if !self.match_token(&TokenType::Coma) {
                            break;
                        }
                    }
                }
                self.consume(&TokenType::ParentesisDer, "Se esperaba ')' al final de llamada a función")?;

                expr = match expr {
                    Expression::Variable(n) => Expression::Call { name: n, args },
                    Expression::MemberAccess { target, member } => Expression::MethodCall {
                        target,
                        method: member,
                        args,
                    },
                    _ => {
                        return Err(UcabaError::Parse {
                            message: "Llamada a expresión que no es un identificador de función ni método".to_string(),
                            line: self.current().line,
                            column: self.current().column,
                        });
                    }
                };
            } else if self.match_token(&TokenType::CorcheteIzq) {
                // Acceso por índice: expr[index]
                let index = self.parse_expression()?;
                self.consume(&TokenType::CorcheteDer, "Se esperaba ']' tras índice")?;
                expr = Expression::IndexAccess {
                    target: Box::new(expr),
                    index: Box::new(index),
                };
            } else if self.match_token(&TokenType::Punto) {
                // Acceso a miembro: expr.largo o expr.campo
                let member = self.consume_ident("Se esperaba el nombre del miembro tras '.'")?;
                expr = Expression::MemberAccess {
                    target: Box::new(expr),
                    member,
                };
            } else {
                break;
            }
        }

        Ok(expr)
    }

    fn parse_primary(&mut self) -> Result<Expression, UcabaError> {
        let tok = self.current().clone();

        match tok.token_type {
            TokenType::Entero(n) => {
                self.advance();
                Ok(Expression::LiteralInt(n))
            }
            TokenType::Real(r) => {
                self.advance();
                Ok(Expression::LiteralReal(r))
            }
            TokenType::Cadena(s) => {
                self.advance();
                Ok(Expression::LiteralCadena(s))
            }
            TokenType::Caracter(c) => {
                self.advance();
                Ok(Expression::LiteralCaracter(c))
            }
            TokenType::Booleano(b) => {
                self.advance();
                Ok(Expression::LiteralBool(b))
            }
            TokenType::Nulo => {
                self.advance();
                Ok(Expression::LiteralNulo)
            }
            TokenType::Identificador(name) => {
                self.advance();
                Ok(Expression::Variable(name))
            }
            TokenType::KwEsPar => {
                self.advance();
                Ok(Expression::Variable("ESPAR".to_string()))
            }
            TokenType::KwEsImpar => {
                self.advance();
                Ok(Expression::Variable("ESIMPAR".to_string()))
            }
            TokenType::KwMod => {
                self.advance();
                Ok(Expression::Variable("MOD".to_string()))
            }
            TokenType::ParentesisIzq => {
                self.advance();
                let expr = self.parse_expression()?;
                self.consume(&TokenType::ParentesisDer, "Se esperaba ')' tras expresión entre paréntesis")?;
                Ok(expr)
            }
            TokenType::CorcheteIzq => {
                // Literal de vector: [elem1, elem2, ...]
                self.advance();
                let mut elements = Vec::new();
                if !self.check(&TokenType::CorcheteDer) {
                    loop {
                        elements.push(self.parse_expression()?);
                        if !self.match_token(&TokenType::Coma) {
                            break;
                        }
                    }
                }
                self.consume(&TokenType::CorcheteDer, "Se esperaba ']' al cerrar literal de vector")?;
                Ok(Expression::LiteralVector(elements))
            }
            _ => Err(UcabaError::Parse {
                message: format!("Expresión esperada, se encontró '{:?}'", tok.token_type),
                line: tok.line,
                column: tok.column,
            }),
        }
    }
}
