use crate::error::UcabaError;
use crate::token::{Token, TokenType};

pub struct Lexer<'a> {
    _source: &'a str,
    chars: Vec<char>,
    pos: usize,
    line: usize,
    column: usize,
    tokens: Vec<Token>,
}

impl<'a> Lexer<'a> {
    pub fn new(source: &'a str) -> Self {
        Self {
            _source: source,
            chars: source.chars().collect(),
            pos: 0,
            line: 1,
            column: 1,
            tokens: Vec::new(),
        }
    }

    fn current_char(&self) -> Option<char> {
        if self.pos >= self.chars.len() {
            None
        } else {
            Some(self.chars[self.pos])
        }
    }

    fn peek_char(&self, offset: usize) -> Option<char> {
        let target = self.pos + offset;
        if target >= self.chars.len() {
            None
        } else {
            Some(self.chars[target])
        }
    }

    fn advance(&mut self) -> Option<char> {
        if let Some(ch) = self.current_char() {
            self.pos += 1;
            if ch == '\n' {
                self.line += 1;
                self.column = 1;
            } else {
                self.column += 1;
            }
            Some(ch)
        } else {
            None
        }
    }

    fn match_char(&mut self, expected: char) -> bool {
        if self.current_char() == Some(expected) {
            self.advance();
            true
        } else {
            false
        }
    }

    fn is_comment_double_slash(&self) -> bool {
        if self.tokens.is_empty() {
            return true;
        }

        let last_tok = self.tokens.last().unwrap();
        if last_tok.line < self.line {
            return true;
        }

        let is_operand = matches!(
            last_tok.token_type,
            TokenType::Entero(_)
                | TokenType::Real(_)
                | TokenType::Identificador(_)
                | TokenType::ParentesisDer
                | TokenType::CorcheteDer
                | TokenType::Booleano(_)
                | TokenType::Nulo
        );

        if !is_operand {
            return true;
        }

        if matches!(last_tok.token_type, TokenType::Identificador(_)) {
            let line_tokens: Vec<&Token> = self.tokens.iter().filter(|t| t.line == self.line).collect();
            let mut open_brackets: i32 = 0;
            for t in &line_tokens {
                match t.token_type {
                    TokenType::CorcheteIzq | TokenType::ParentesisIzq => open_brackets += 1,
                    TokenType::CorcheteDer | TokenType::ParentesisDer => open_brackets -= 1,
                    _ => {}
                }
            }

            let has_assignment = line_tokens.iter().any(|t| {
                matches!(
                    t.token_type,
                    TokenType::Asignar | TokenType::AsigSuma | TokenType::AsigResta
                )
            });

            if !has_assignment && open_brackets <= 0 {
                if let Some(first_t) = line_tokens.first() {
                    let is_primitive_type = matches!(
                        first_t.token_type,
                        TokenType::TipoEntero
                            | TokenType::TipoFlotante
                            | TokenType::TipoReal
                            | TokenType::TipoCadena
                            | TokenType::TipoCaracter
                            | TokenType::TipoBooleano
                            | TokenType::TipoArchivo
                    );
                    if is_primitive_type
                        || (matches!(first_t.token_type, TokenType::Identificador(_)) && line_tokens.len() >= 2)
                    {
                        return true;
                    }
                }
            }

            if open_brackets > 0 {
                return false;
            }
        }

        // Inspeccionar qué sigue a '//' en la misma línea
        let mut p = self.pos + 2;
        while p < self.chars.len() && (self.chars[p] == ' ' || self.chars[p] == '\t') {
            p += 1;
        }

        // Si la línea termina aquí, no hay operando derecho -> es comentario
        if p >= self.chars.len() || self.chars[p] == '\n' || self.chars[p] == '\r' {
            return true;
        }

        // Si lo siguiente es un separador de comentario como '///', '//---', etc.
        if matches!(self.chars[p], '/' | '-' | '=' | '*' | '#') {
            return true;
        }

        // Analizar el resto de la línea para detectar si es un comentario en lenguaje natural
        let mut line_end = p;
        while line_end < self.chars.len() && self.chars[line_end] != '\n' && self.chars[line_end] != '\r' {
            line_end += 1;
        }

        let after_slash: String = self.chars[p..line_end].iter().collect();
        let words: Vec<&str> = after_slash.split_whitespace().collect();
        if words.is_empty() {
            return true;
        }

        let first_word_upper = words[0].to_uppercase();
        let statement_keywords = [
            "RETORNAR", "RETORNO", "RETORNA", "RETURN",
            "INICIO", "FIN", "FUNCION", "PROCEDIMIENTO",
            "SI", "SINO", "MIENTRAS", "HACER", "PARA",
            "IMPRIMIR", "ESTRUCTURA", "ALGORITMO", "PROGRAMA",
            "ENTERO", "FLOTANTE", "REAL", "CADENA", "CARACTER", "BOOLEANO", "ARCHIVO", "VOID",
            "DECLARAR", "ASIGNAR", "DEFINIR", "COMENTARIO", "TITULO", "PAGINAS"
        ];
        if statement_keywords.contains(&first_word_upper.as_str()) {
            return true;
        }

        if words.len() >= 2 {
            let first_is_word = words[0].chars().next().is_some_and(|c| c.is_alphabetic() || c == '_');
            let second_is_word = words[1].chars().next().is_some_and(|c| c.is_alphabetic() || c == '_');
            let ops = ["+", "-", "*", "/", "%", "==", "!=", "<", ">", "<=", ">=", "&&", "||", "Y", "O", ",", ";", ")", "]", ":"];
            if first_is_word && second_is_word && !ops.contains(&words[1]) {
                return true;
            }
        }

        false
    }

    pub fn tokenize(&mut self) -> Result<Vec<Token>, UcabaError> {
        while let Some(ch) = self.current_char() {
            let start_line = self.line;
            let start_col = self.column;

            match ch {
                ' ' | '\t' | '\r' | '\n' => {
                    self.advance();
                }
                '#' => {
                    // Comentario de línea estilo Python
                    while let Some(c) = self.current_char() {
                        if c == '\n' {
                            break;
                        }
                        self.advance();
                    }
                }
                '/' => {
                    if self.peek_char(1) == Some('/') {
                        if self.is_comment_double_slash() {
                            // Es comentario de línea
                            while let Some(c) = self.current_char() {
                                if c == '\n' {
                                    break;
                                }
                                self.advance();
                            }
                        } else {
                            // Es operador de división entera '//'
                            self.advance();
                            self.advance();
                            self.tokens.push(Token::new(TokenType::DivEntera, start_line, start_col, 2));
                        }
                    } else if self.peek_char(1) == Some('*') {
                        // Comentario multilínea /* ... */
                        self.advance();
                        self.advance();
                        let mut closed = false;
                        while let Some(c) = self.current_char() {
                            if c == '*' && self.peek_char(1) == Some('/') {
                                self.advance();
                                self.advance();
                                closed = true;
                                break;
                            }
                            self.advance();
                        }
                        if !closed {
                            return Err(UcabaError::Lexer {
                                message: "Comentario multilínea '/*' sin cerrar".to_string(),
                                line: start_line,
                                column: start_col,
                            });
                        }
                    } else {
                        self.advance();
                        self.tokens.push(Token::new(TokenType::Div, start_line, start_col, 1));
                    }
                }
                '+' => {
                    self.advance();
                    if self.match_char('+') {
                        self.tokens.push(Token::new(TokenType::Inc, start_line, start_col, 2));
                    } else if self.match_char('=') {
                        self.tokens.push(Token::new(TokenType::AsigSuma, start_line, start_col, 2));
                    } else {
                        self.tokens.push(Token::new(TokenType::Suma, start_line, start_col, 1));
                    }
                }
                '-' => {
                    self.advance();
                    if self.match_char('-') {
                        self.tokens.push(Token::new(TokenType::Dec, start_line, start_col, 2));
                    } else if self.match_char('=') {
                        self.tokens.push(Token::new(TokenType::AsigResta, start_line, start_col, 2));
                    } else {
                        self.tokens.push(Token::new(TokenType::Resta, start_line, start_col, 1));
                    }
                }
                '*' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::Mult, start_line, start_col, 1));
                }
                '%' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::Mod, start_line, start_col, 1));
                }
                '=' => {
                    self.advance();
                    if self.match_char('=') {
                        self.tokens.push(Token::new(TokenType::IgualQue, start_line, start_col, 2));
                    } else {
                        self.tokens.push(Token::new(TokenType::Asignar, start_line, start_col, 1));
                    }
                }
                '!' => {
                    self.advance();
                    if self.match_char('=') {
                        self.tokens.push(Token::new(TokenType::Distinto, start_line, start_col, 2));
                    } else {
                        self.tokens.push(Token::new(TokenType::OpNo, start_line, start_col, 1));
                    }
                }
                '<' => {
                    self.advance();
                    if self.match_char('=') {
                        self.tokens.push(Token::new(TokenType::MenorIgual, start_line, start_col, 2));
                    } else {
                        self.tokens.push(Token::new(TokenType::Menor, start_line, start_col, 1));
                    }
                }
                '>' => {
                    self.advance();
                    if self.match_char('=') {
                        self.tokens.push(Token::new(TokenType::MayorIgual, start_line, start_col, 2));
                    } else {
                        self.tokens.push(Token::new(TokenType::Mayor, start_line, start_col, 1));
                    }
                }
                '&' => {
                    self.advance();
                    if self.match_char('&') {
                        self.tokens.push(Token::new(TokenType::OpY, start_line, start_col, 2));
                    } else {
                        return Err(UcabaError::Lexer {
                            message: "Carácter inesperado '&'. Use '&&' o 'Y' para operador lógico".to_string(),
                            line: start_line,
                            column: start_col,
                        });
                    }
                }
                '|' => {
                    self.advance();
                    if self.match_char('|') {
                        self.tokens.push(Token::new(TokenType::OpO, start_line, start_col, 2));
                    } else {
                        return Err(UcabaError::Lexer {
                            message: "Carácter inesperado '|'. Use '||' u 'O' para operador lógico".to_string(),
                            line: start_line,
                            column: start_col,
                        });
                    }
                }
                '(' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::ParentesisIzq, start_line, start_col, 1));
                }
                ')' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::ParentesisDer, start_line, start_col, 1));
                }
                '[' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::CorcheteIzq, start_line, start_col, 1));
                }
                ']' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::CorcheteDer, start_line, start_col, 1));
                }
                ',' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::Coma, start_line, start_col, 1));
                }
                ';' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::PuntoYComa, start_line, start_col, 1));
                }
                ':' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::DosPuntos, start_line, start_col, 1));
                }
                '.' => {
                    self.advance();
                    self.tokens.push(Token::new(TokenType::Punto, start_line, start_col, 1));
                }
                '"' | '\'' => {
                    let quote = ch;
                    self.advance();
                    let mut s = String::new();
                    let mut closed = false;

                    while let Some(c) = self.current_char() {
                        if c == quote {
                            self.advance();
                            closed = true;
                            break;
                        } else if c == '\\' {
                            self.advance();
                            if let Some(esc) = self.current_char() {
                                match esc {
                                    'n' => s.push('\n'),
                                    't' => s.push('\t'),
                                    'r' => s.push('\r'),
                                    '\\' => s.push('\\'),
                                    '\'' => s.push('\''),
                                    '"' => s.push('"'),
                                    _ => s.push(esc),
                                }
                                self.advance();
                            }
                        } else {
                            s.push(c);
                            self.advance();
                        }
                    }

                    if !closed {
                        return Err(UcabaError::Lexer {
                            message: format!("Cadena sin cerrar con comilla {}", quote),
                            line: start_line,
                            column: start_col,
                        });
                    }

                    let len = s.len() + 2;
                    if quote == '\'' && s.chars().count() == 1 {
                        self.tokens.push(Token::new(
                            TokenType::Caracter(s.chars().next().unwrap()),
                            start_line,
                            start_col,
                            len,
                        ));
                    } else {
                        self.tokens.push(Token::new(
                            TokenType::Cadena(s),
                            start_line,
                            start_col,
                            len,
                        ));
                    }
                }
                '0'..='9' => {
                    let mut num_str = String::new();
                    while let Some(c) = self.current_char() {
                        if c.is_ascii_digit() {
                            num_str.push(c);
                            self.advance();
                        } else {
                            break;
                        }
                    }

                    if self.current_char() == Some('.') && self.peek_char(1).is_some_and(|c| c.is_ascii_digit()) {
                        num_str.push('.');
                        self.advance(); // consumir '.'
                        while let Some(c) = self.current_char() {
                            if c.is_ascii_digit() {
                                num_str.push(c);
                                self.advance();
                            } else {
                                break;
                            }
                        }
                        let val: f64 = num_str.parse().map_err(|e| UcabaError::Lexer {
                            message: format!("Literal real no válido: {}", e),
                            line: start_line,
                            column: start_col,
                        })?;
                        let len = num_str.len();
                        self.tokens.push(Token::new(TokenType::Real(val), start_line, start_col, len));
                    } else {
                        let val: i64 = num_str.parse().map_err(|e| UcabaError::Lexer {
                            message: format!("Literal entero no válido: {}", e),
                            line: start_line,
                            column: start_col,
                        })?;
                        let len = num_str.len();
                        self.tokens.push(Token::new(TokenType::Entero(val), start_line, start_col, len));
                    }
                }
                'a'..='z' | 'A'..='Z' | '_' => {
                    let mut ident = String::new();
                    while let Some(c) = self.current_char() {
                        if c.is_alphanumeric() || c == '_' {
                            ident.push(c);
                            self.advance();
                        } else {
                            break;
                        }
                    }

                    let len = ident.len();
                    let upper = ident.to_uppercase();

                    let tok_type = match upper.as_str() {
                        "ENTERO" => TokenType::TipoEntero,
                        "FLOTANTE" => TokenType::TipoFlotante,
                        "REAL" => TokenType::TipoReal,
                        "CADENA" => TokenType::TipoCadena,
                        "CARACTER" => TokenType::TipoCaracter,
                        "BOOLEANO" => TokenType::TipoBooleano,
                        "ARCHIVO" => TokenType::TipoArchivo,
                        "VOID" => TokenType::TipoVoid,
                        "INICIO" => TokenType::KwInicio,
                        "FIN" => TokenType::KwFin,
                        "FUNCION" => TokenType::KwFuncion,
                        "PROCEDIMIENTO" => TokenType::KwProcedimiento,
                        "RETORNAR" | "RETORNO" => TokenType::KwRetornar,
                        "SI" => TokenType::KwSi,
                        "SINO" => TokenType::KwSino,
                        "MIENTRAS" => TokenType::KwMientras,
                        "HACER" => TokenType::KwHacer,
                        "PARA" => TokenType::KwPara,
                        "IMPRIMIR" => TokenType::KwImprimir,
                        "ESTRUCTURA" => TokenType::KwEstructura,
                        "MOD" => TokenType::KwMod,
                        "ESPAR" => TokenType::KwEsPar,
                        "ESIMPAR" => TokenType::KwEsImpar,
                        "Y" => TokenType::OpY,
                        "O" => TokenType::OpO,
                        "NO" => TokenType::OpNo,
                        "VERDADERO" | "TRUE" => TokenType::Booleano(true),
                        "FALSO" | "FALSE" => TokenType::Booleano(false),
                        "NULO" | "NULL" | "NONE" => TokenType::Nulo,
                        _ => TokenType::Identificador(ident),
                    };

                    self.tokens.push(Token::new(tok_type, start_line, start_col, len));
                }
                _ => {
                    let bad_char = ch;
                    self.advance();
                    return Err(UcabaError::Lexer {
                        message: format!("Carácter inesperado: '{}'", bad_char),
                        line: start_line,
                        column: start_col,
                    });
                }
            }
        }

        self.tokens.push(Token::new(TokenType::Eof, self.line, self.column, 0));
        Ok(self.tokens.clone())
    }
}
