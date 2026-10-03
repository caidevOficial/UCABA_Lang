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

    def skip_whitespace_and_comments(self):
        while self.pos < self.length:
            ch = self.current_char()

            # Espacios en blanco
            if ch in (' ', '\t', '\r', '\n'):
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
                while self.pos < self.length and self.current_char() != '\n':
                    self.advance()
                continue

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
            return Token(tok_type, val, start_line, start_col, len(word))

        return Token(TokenType.IDENTIFICADOR, word, start_line, start_col, len(word))

    def tokenize(self) -> List[Token]:
        tokens: List[Token] = []
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
