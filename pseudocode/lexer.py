# GNU General Public License v3.0 or later (GPL-3.0-or-later)
#
# Copyright (c) 2026 [Facu Falcone](a.facundo.falcone@gmail.com) All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Analizador léxico (Lexer) para el lenguaje de pseudocódigo.
Maneja comentarios multilínea (estilo Python triple comillas), comentarios simples (//),
cadenas, números y palabras clave con seguimiento preciso de líneas y columnas.
"""

from typing import List, Optional
from pseudocode.tokens import Token, TokenType, KEYWORDS
from pseudocode.errors import LexerError


class Lexer:
    def __init__(self, source: str, filename: str = "<código>"):
        self.source = source
        self.filename = filename
        self.pos = 0
        self.line = 1
        self.column = 1
        self.length = len(source)
        self.tokens: List[Token] = []

    def current_char(self) -> Optional[str]:
        if self.pos >= self.length:
            return None
        return self.source[self.pos]

    def peek_char(self, offset: int = 1) -> Optional[str]:
        target = self.pos + offset
        if target >= self.length:
            return None
        return self.source[target]

    def advance(self) -> Optional[str]:
        ch = self.current_char()
        if ch is not None:
            self.pos += 1
            if ch == '\n':
                self.line += 1
                self.column = 1
            else:
                self.column += 1
        return ch

    def match(self, expected: str) -> bool:
        if self.current_char() == expected:
            self.advance()
            return True
        return False

    def is_comment_double_slash(self) -> bool:
        """Determina si un par de barras '//' corresponde a un comentario o al operador de división entera '//'."""
        if not self.tokens:
            return True

        last_tok = self.tokens[-1]
        # Si el último token ocurrió en una línea previa, en la línea actual '//' inicia un comentario
        if last_tok.line < self.line:
            return True

        # Un operador binario sólo puede ubicarse inmediatamente tras un operando o delimitador de cierre
        allowed_prev = {
            TokenType.ENTERO_LIT,
            TokenType.REAL_LIT,
            TokenType.IDENTIFICADOR,
            TokenType.PARENTESIS_DER,
            TokenType.CORCHETE_DER,
            TokenType.BOOLEANO_LIT,
            TokenType.NULO_LIT,
        }
        if last_tok.type not in allowed_prev:
            return True

        # Si el token previo es un identificador pero la línea es una declaración pura sin inicializador
        # (ej: 'Libro libro1 // Declarar' o 'ENTERO a // Comentario')
        if last_tok.type == TokenType.IDENTIFICADOR:
            line_tokens = [t for t in self.tokens if t.line == self.line]
            # Dentro de un índice o paréntesis sin cerrar (ej: 'm[i // n]'), el identificador es un operando
            open_brackets = sum(
                1 if t.type in (TokenType.CORCHETE_IZQ, TokenType.PARENTESIS_IZQ)
                else -1 if t.type in (TokenType.CORCHETE_DER, TokenType.PARENTESIS_DER)
                else 0
                for t in line_tokens
            )
            has_assignment = any(t.type == TokenType.ASIGNAR for t in line_tokens)
            if not has_assignment and open_brackets <= 0:
                type_keywords = {
                    TokenType.TIPO_ENTERO, TokenType.TIPO_FLOTANTE, TokenType.TIPO_REAL,
                    TokenType.TIPO_CADENA, TokenType.TIPO_CARACTER, TokenType.TIPO_BOOLEANO,
                    TokenType.TIPO_ARCHIVO, TokenType.TIPO_VOID, TokenType.TIPO_NULO
                }
                first_t = line_tokens[0] if line_tokens else None
                if first_t and (first_t.type in type_keywords or (first_t.type == TokenType.IDENTIFICADOR and len(line_tokens) >= 2)):
                    return True

        # Inspeccionar qué sigue a '//' en la misma línea
        p = self.pos + 2
        while p < self.length and self.source[p] in (' ', '\t'):
            p += 1

        # Si la línea termina aquí, no hay operando derecho -> es comentario
        if p >= self.length or self.source[p] in ('\n', '\r'):
            return True

        # Si lo siguiente es un separador de comentario como '///', '//---', etc.
        if self.source[p] in ('/', '-', '=', '*', '#'):
            return True

        # Analizar el resto de la línea para detectar si es un comentario en lenguaje natural
        line_end = p
        while line_end < self.length and self.source[line_end] not in ('\n', '\r'):
            line_end += 1
        after_slash = self.source[p:line_end].strip()

        # Extraer tokens preliminares de after_slash
        import re
        tokens_after = re.findall(r'[a-zA-Z_][a-zA-Z0-9_]*|\d+(?:\.\d+)?|[^\s\w]', after_slash)
        if not tokens_after:
            return True

        first_token = tokens_after[0]
        first_token_upper = first_token.upper()

        # Si la primera palabra tras '//' es una palabra clave de sentencia o tipo (ej: RETORNA, FIN, SI, ENTERO):
        statement_keywords = {
            "RETORNAR", "RETORNO", "RETORNA", "RETURN",
            "INICIO", "FIN", "FUNCION", "PROCEDIMIENTO",
            "SI", "SINO", "MIENTRAS", "HACER", "PARA",
            "IMPRIMIR", "ESTRUCTURA", "ALGORITMO", "PROGRAMA",
            "ENTERO", "FLOTANTE", "REAL", "CADENA", "CARACTER", "BOOLEANO", "ARCHIVO", "VOID"
        }
        if first_token_upper in statement_keywords:
            return True

        # En una expresión aritmética válida, dos operandos consecutivos (ej: ID ID, o ID NUM)
        # sin operador entre ellos son imposibles (ej: 'RETORNA 3', 'Asignar un valor', 'comentario explicativo')
        if len(tokens_after) >= 2:
            t1, t2 = tokens_after[0], tokens_after[1]
            op_symbols = {'+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||', 'Y', 'O', ',', ';', ')', ']', ':'}
            t1_is_word = bool(re.match(r'^[a-zA-Z_]', t1))
            t2_is_word_or_num = bool(re.match(r'^[a-zA-Z0-9_]', t2))
            if t1_is_word and t2_is_word_or_num and t2 not in op_symbols:
                return True

        # Es el operador de división entera '//'
        return False

    def skip_whitespace_and_comments(self):
        while self.pos < self.length:
            ch = self.current_char()

            # Espacios en blanco
            if ch in (' ', '\t', '\r', '\n'):
                self.advance()
                continue

            # Comentario de línea con #
            if ch == '#':
                while self.pos < self.length and self.current_char() != '\n':
                    self.advance()
                continue

            # Comentario multilínea """ ... """ o ''' ... '''
            if (ch == '"' and self.peek_char(1) == '"' and self.peek_char(2) == '"') or \
               (ch == "'" and self.peek_char(1) == "'" and self.peek_char(2) == "'"):
                quote_type = ch * 3
                start_line = self.line
                start_col = self.column
                self.advance()
                self.advance()
                self.advance()
                while self.pos < self.length:
                    if self.source.startswith(quote_type, self.pos):
                        self.advance()
                        self.advance()
                        self.advance()
                        break
                    self.advance()
                else:
                    raise LexerError(
                        f"Comentario multilínea sin cerrar iniciado en línea {start_line}",
                        line=start_line, column=start_col, source=self.source
                    )
                continue

            # Comentario de bloque /* ... */
            if ch == '/' and self.peek_char(1) == '*':
                start_line = self.line
                start_col = self.column
                self.advance()
                self.advance()
                while self.pos < self.length:
                    if self.current_char() == '*' and self.peek_char(1) == '/':
                        self.advance()
                        self.advance()
                        break
                    self.advance()
                else:
                    raise LexerError(
                        f"Comentario de bloque sin cerrar iniciado en línea {start_line}",
                        line=start_line, column=start_col, source=self.source
                    )
                continue

            # Comentario de línea //
            if ch == '/' and self.peek_char(1) == '/':
                if self.is_comment_double_slash():
                    while self.pos < self.length and self.current_char() != '\n':
                        self.advance()
                    continue
                else:
                    # Es el operador de división entera '//', salimos para tokenizarlo
                    break

            # Si no es espacio ni comentario, salimos
            break

    def read_string(self, quote: str) -> Token:
        start_line = self.line
        start_col = self.column
        self.advance()  # Salta la comilla inicial
        val = []
        while self.pos < self.length:
            ch = self.current_char()
            if ch == quote:
                self.advance()
                raw_str = "".join(val)
                # Si comilla simple y longitud 1, puede ser CARACTER o CADENA
                if quote == "'" and len(raw_str) == 1:
                    return Token(TokenType.CARACTER_LIT, raw_str, start_line, start_col)
                return Token(TokenType.CADENA_LIT, raw_str, start_line, start_col)
            elif ch == '\\':
                self.advance()
                esc = self.advance()
                if esc == 'n':
                    val.append('\n')
                elif esc == 't':
                    val.append('\t')
                elif esc == 'r':
                    val.append('\r')
                elif esc == '\\':
                    val.append('\\')
                elif esc == quote:
                    val.append(quote)
                else:
                    val.append(esc if esc else '')
            elif ch == '\n':
                raise LexerError("Cadena literal sin cerrar antes del salto de línea",
                                 line=start_line, column=start_col, source=self.source)
            else:
                val.append(ch)
                self.advance()

        raise LexerError("Cadena literal no terminada al final del archivo",
                         line=start_line, column=start_col, source=self.source)

    def read_number(self) -> Token:
        start_line = self.line
        start_col = self.column
        num_str = []
        is_real = False

        while self.current_char() and self.current_char().isdigit():
            num_str.append(self.advance())

        if self.current_char() == '.' and self.peek_char(1) and self.peek_char(1).isdigit():
            is_real = True
            num_str.append(self.advance())  # Consumir el punto
            while self.current_char() and self.current_char().isdigit():
                num_str.append(self.advance())

        literal_text = "".join(num_str)
        if is_real:
            return Token(TokenType.REAL_LIT, float(literal_text), start_line, start_col, len(literal_text))
        else:
            return Token(TokenType.ENTERO_LIT, int(literal_text), start_line, start_col, len(literal_text))

    def read_identifier_or_keyword(self) -> Token:
        start_line = self.line
        start_col = self.column
        chars = []

        while self.current_char() and (self.current_char().isalnum() or self.current_char() == '_'):
            chars.append(self.advance())

        word = "".join(chars)
        upper_word = word.upper()

        if upper_word in KEYWORDS:
            tok_type = KEYWORDS[upper_word]
            val = word
            if tok_type == TokenType.BOOLEANO_LIT:
                val = True if upper_word in ("VERDADERO", "TRUE") else False
            elif tok_type == TokenType.NULO_LIT:
                val = None
            return Token(tok_type, val, start_line, start_col, len(word))

        return Token(TokenType.IDENTIFICADOR, word, start_line, start_col, len(word))

    def tokenize(self) -> List[Token]:
        self.tokens = []
        tokens = self.tokens
        while self.pos < self.length:
            self.skip_whitespace_and_comments()
            if self.pos >= self.length:
                break

            start_line = self.line
            start_col = self.column
            ch = self.current_char()

            # Literales de cadena
            if ch in ('"', "'"):
                tokens.append(self.read_string(ch))
                continue

            # Números
            if ch.isdigit():
                tokens.append(self.read_number())
                continue

            # Identificadores y palabras clave
            if ch.isalpha() or ch == '_':
                tokens.append(self.read_identifier_or_keyword())
                continue

            # Operadores y signos de puntuación
            if ch == '+':
                self.advance()
                if self.match('+'):
                    tokens.append(Token(TokenType.INC, "++", start_line, start_col, 2))
                elif self.match('='):
                    tokens.append(Token(TokenType.ASIG_SUMA, "+=", start_line, start_col, 2))
                else:
                    tokens.append(Token(TokenType.SUMA, "+", start_line, start_col, 1))
            elif ch == '-':
                self.advance()
                if self.match('-'):
                    tokens.append(Token(TokenType.DEC, "--", start_line, start_col, 2))
                elif self.match('='):
                    tokens.append(Token(TokenType.ASIG_RESTA, "-=", start_line, start_col, 2))
                else:
                    tokens.append(Token(TokenType.RESTA, "-", start_line, start_col, 1))
            elif ch == '*':
                self.advance()
                tokens.append(Token(TokenType.MULT, "*", start_line, start_col, 1))
            elif ch == '/':
                self.advance()
                if self.match('/'):
                    tokens.append(Token(TokenType.DIV_ENTERA, "//", start_line, start_col, 2))
                else:
                    tokens.append(Token(TokenType.DIV, "/", start_line, start_col, 1))
            elif ch == '%':
                self.advance()
                tokens.append(Token(TokenType.MOD, "%", start_line, start_col, 1))
            elif ch == '=':
                self.advance()
                if self.match('='):
                    tokens.append(Token(TokenType.IGUAL_QUE, "==", start_line, start_col, 2))
                else:
                    tokens.append(Token(TokenType.ASIGNAR, "=", start_line, start_col, 1))
            elif ch == '!':
                self.advance()
                if self.match('='):
                    tokens.append(Token(TokenType.DISTINTO, "!=", start_line, start_col, 2))
                else:
                    tokens.append(Token(TokenType.OP_NO, "!", start_line, start_col, 1))
            elif ch == '<':
                self.advance()
                if self.match('='):
                    tokens.append(Token(TokenType.MENOR_IGUAL, "<=", start_line, start_col, 2))
                else:
                    tokens.append(Token(TokenType.MENOR, "<", start_line, start_col, 1))
            elif ch == '>':
                self.advance()
                if self.match('='):
                    tokens.append(Token(TokenType.MAYOR_IGUAL, ">=", start_line, start_col, 2))
                else:
                    tokens.append(Token(TokenType.MAYOR, ">", start_line, start_col, 1))
            elif ch == '&':
                self.advance()
                if self.match('&'):
                    tokens.append(Token(TokenType.OP_Y, "&&", start_line, start_col, 2))
                else:
                    raise LexerError(f"Carácter inesperado '&', ¿quisiste decir '&&'?",
                                     line=start_line, column=start_col, source=self.source)
            elif ch == '|':
                self.advance()
                if self.match('|'):
                    tokens.append(Token(TokenType.OP_O, "||", start_line, start_col, 2))
                else:
                    raise LexerError(f"Carácter inesperado '|', ¿quisiste decir '||'?",
                                     line=start_line, column=start_col, source=self.source)
            elif ch == '(':
                self.advance()
                tokens.append(Token(TokenType.PARENTESIS_IZQ, "(", start_line, start_col, 1))
            elif ch == ')':
                self.advance()
                tokens.append(Token(TokenType.PARENTESIS_DER, ")", start_line, start_col, 1))
            elif ch == '[':
                self.advance()
                tokens.append(Token(TokenType.CORCHETE_IZQ, "[", start_line, start_col, 1))
            elif ch == ']':
                self.advance()
                tokens.append(Token(TokenType.CORCHETE_DER, "]", start_line, start_col, 1))
            elif ch == ',':
                self.advance()
                tokens.append(Token(TokenType.COMA, ",", start_line, start_col, 1))
            elif ch == ';':
                self.advance()
                tokens.append(Token(TokenType.PUNTO_Y_COMA, ";", start_line, start_col, 1))
            elif ch == ':':
                self.advance()
                tokens.append(Token(TokenType.DOS_PUNTOS, ":", start_line, start_col, 1))
            elif ch == '.':
                self.advance()
                tokens.append(Token(TokenType.PUNTO, ".", start_line, start_col, 1))
            else:
                self.advance()
                raise LexerError(f"Carácter desconocido o no soportado: {ch!r}",
                                 line=start_line, column=start_col, source=self.source)

        tokens.append(Token(TokenType.EOF, "", self.line, self.column, 0))
        return tokens
