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
Analizador sintáctico (Parser) descendente recursivo con precedencia de operadores.
Diseñado para admitir variaciones canónicas y tolerantes de pseudocódigo en español.
"""

from typing import List, Optional, Tuple, Any
from pseudocode.tokens import Token, TokenType
from pseudocode.errors import ParseError
from pseudocode.types_system import (
    DataType, VectorType, MatrixType,
    TYPE_ENTERO, TYPE_FLOTANTE, TYPE_REAL, TYPE_CADENA,
    TYPE_CARACTER, TYPE_BOOLEANO, TYPE_ARCHIVO, TYPE_VOID,
    parse_type_name
)
from pseudocode.ast_nodes import (
    ASTNode, Expression, Statement,
    Literal, ArrayLiteral, Variable, BinaryOp, UnaryOp,
    IndexAccess, MemberAccess, FunctionCall,
    VarDeclaration, Assignment, IncrementStatement,
    IfStatement, WhileStatement, DoWhileStatement, ForStatement,
    ReturnStatement, PrintStatement, ExpressionStatement,
    Parameter, FunctionDef, Program
)

# Mapa de tipos según token
TOKEN_TO_TYPE = {
    TokenType.TIPO_ENTERO: TYPE_ENTERO,
    TokenType.TIPO_FLOTANTE: TYPE_FLOTANTE,
    TokenType.TIPO_REAL: TYPE_REAL,
    TokenType.TIPO_CADENA: TYPE_CADENA,
    TokenType.TIPO_CARACTER: TYPE_CARACTER,
    TokenType.TIPO_BOOLEANO: TYPE_BOOLEANO,
    TokenType.TIPO_ARCHIVO: TYPE_ARCHIVO,
    TokenType.TIPO_VOID: TYPE_VOID,
}


import difflib


class Parser:
    def __init__(self, tokens: List[Token], source: str = "", filename: str = "<código>", lenient: bool = False):
        self.tokens = tokens
        self.source = source
        self.filename = filename
        self.lenient = lenient
        self.warnings: List[str] = []
        self.pos = 0

    def check_keyword_typo(self, tok: Token, candidates: List[str]) -> Optional[str]:
        """Detecta si un identificador es un error de tipeo de una palabra clave esperada."""
        if not tok or tok.type != TokenType.IDENTIFICADOR:
            return None
        val = str(tok.value).upper()

        direct_map = {
            "FUNCIO": "FUNCION",
            "FUNCIOM": "FUNCION",
            "FUNCTION": "FUNCION",
            "FUNCT": "FUNCION",
            "FUNC": "FUNCION",
            "DEF": "FUNCION",
            "FN": "FUNCION",
            "PROC": "PROCEDIMIENTO",
            "PROCEDURE": "PROCEDIMIENTO",
            "PROCEDIMIENT": "PROCEDIMIENTO",
            "MIENTRA": "MIENTRAS",
            "WHILE": "MIENTRAS",
            "RETORNA": "RETORNAR",
            "RETURN": "RETORNAR",
            "IMPRIME": "IMPRIMIR",
            "PRINT": "IMPRIMIR",
            "ESCRIBIR": "IMPRIMIR",
            "ALGORITM": "ALGORITMO",
            "ALGORITHM": "ALGORITMO",
            "INICI": "INICIO",
            "START": "INICIO",
            "BEGIN": "INICIO",
            "ENTER": "ENTERO",
            "INT": "ENTERO",
            "INTEGER": "ENTERO",
            "ENTRO": "ENTERO",
            "FLOAT": "FLOTANTE",
            "DOUBLE": "REAL",
            "REA": "REAL",
            "CADEN": "CADENA",
            "STRING": "CADENA",
            "STR": "CADENA",
            "BOOL": "BOOLEANO",
            "BOOLEAN": "BOOLEANO",
            "FILE": "ARCHIVO",
            "ARCHIV": "ARCHIVO",
            "CHAR": "CARACTER",
            "CARACTE": "CARACTER",
            "FOR": "PARA",
            "PAR": "PARA",
            "IF": "SI",
            "ELSE": "SINO",
            "DO": "HACER",
            "HACE": "HACER",
            "HACR": "HACER",
        }
        if val in direct_map and direct_map[val] in candidates:
            return direct_map[val]

        matches = difflib.get_close_matches(val, candidates, n=1, cutoff=0.7)
        if matches:
            return matches[0]
        return None

    def current_token(self) -> Token:
        if self.pos >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[self.pos]

    def previous_token(self) -> Token:
        if self.pos > 0:
            return self.tokens[self.pos - 1]
        return self.tokens[0]

    def peek_token(self, offset: int = 1) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        return self.tokens[idx]

    def advance(self) -> Token:
        tok = self.current_token()
        if self.pos < len(self.tokens) - 1:
            self.pos += 1
        return tok

    def match(self, *expected_types: TokenType) -> bool:
        if self.current_token().type in expected_types:
            self.advance()
            return True
        return False

    def expect(self, expected_type: TokenType, error_msg: Optional[str] = None) -> Token:
        tok = self.current_token()
        if tok.type != expected_type:
            msg = error_msg or f"Se esperaba {expected_type.name}, se encontró {tok.type.name} ('{tok.value}')"
            raise ParseError(msg, line=tok.line, column=tok.column, source=self.source)
        return self.advance()

    def parse_program_item(self, functions: List[FunctionDef], statements: List[Statement]) -> None:
        tok = self.current_token()

        # Funciones y Procedimientos válidos
        if tok.type in (TokenType.KW_FUNCION, TokenType.KW_PROCEDIMIENTO):
            functions.append(self.parse_function_or_procedure())
            return

        # Detección temprana de intento de declaración de función/procedimiento con error de tipeo
        # Patrón: <IDENTIFICADOR> <IDENTIFICADOR> ( ...  (ej: FUNCIO trasponer_matriz(...) )
        if tok.type == TokenType.IDENTIFICADOR:
            next_tok = self.peek_token(1)
            next_next_tok = self.peek_token(2)
            if next_tok.type == TokenType.IDENTIFICADOR and next_next_tok.type == TokenType.PARENTESIS_IZQ:
                suggestion = self.check_keyword_typo(tok, ["FUNCION", "PROCEDIMIENTO"])
                if suggestion:
                    if self.lenient:
                        self.warnings.append(
                            f"Línea {tok.line}: Se corrigió automáticamente '{tok.value}' por '{suggestion}'"
                        )
                        tok.type = TokenType.KW_FUNCION if suggestion == "FUNCION" else TokenType.KW_PROCEDIMIENTO
                        functions.append(self.parse_function_or_procedure())
                        return
                    else:
                        raise ParseError(
                            f"Palabra clave no reconocida: '{tok.value}'. ¿Quisiste decir '{suggestion}'?",
                            line=tok.line, column=tok.column, length=tok.length, source=self.source
                        )
                else:
                    raise ParseError(
                        f"Declaración no válida: se esperaba 'FUNCION' o 'PROCEDIMIENTO' antes de '{next_tok.value}', pero se encontró '{tok.value}'.",
                        line=tok.line, column=tok.column, length=tok.length, source=self.source
                    )

            # Detección de error de tipeo en palabras clave globales
            global_suggestion = self.check_keyword_typo(tok, ["FUNCION", "PROCEDIMIENTO", "ALGORITMO", "INICIO", "ENTERO", "REAL", "CADENA", "BOOLEANO"])
            if global_suggestion:
                raise ParseError(
                    f"Palabra clave no reconocida: '{tok.value}'. ¿Quisiste decir '{global_suggestion}'?",
                    line=tok.line, column=tok.column, length=tok.length, source=self.source
                )

        # Sentencia normal
        statements.append(self.parse_statement())

    def parse(self) -> Program:
        functions: List[FunctionDef] = []
        statements: List[Statement] = []

        while self.current_token().type != TokenType.EOF:
            tok = self.current_token()

            # Bloque INICIO ... FIN
            if tok.type == TokenType.KW_INICIO:
                self.advance()
                while self.current_token().type not in (TokenType.KW_FIN, TokenType.EOF):
                    self.parse_program_item(functions, statements)
                self.expect(TokenType.KW_FIN, "Se esperaba 'FIN' para cerrar el bloque 'INICIO'")
                continue

            self.parse_program_item(functions, statements)

        return Program(functions, statements, line=1, column=1)

    # ==========================================
    # FUNCIONES Y PROCEDIMIENTOS
    # ==========================================

    def parse_function_or_procedure(self) -> FunctionDef:
        start_tok = self.advance()
        is_proc = (start_tok.type == TokenType.KW_PROCEDIMIENTO)

        name_tok = self.expect(TokenType.IDENTIFICADOR, "Se esperaba el nombre de la función o procedimiento")
        name = name_tok.value

        self.expect(TokenType.PARENTESIS_IZQ, "Se esperaba '(' después del nombre")
        params = self.parse_parameters()
        close_paren = self.expect(TokenType.PARENTESIS_DER, "Se esperaba ')' después de los parámetros")

        return_type: DataType = TYPE_VOID
        if not is_proc:
            if self.match(TokenType.DOS_PUNTOS):
                colon_tok = self.previous_token()
                # El tipo de retorno DEBE estar en la misma línea que los dos puntos
                if self.is_type_token(self.current_token()) and self.current_token().line == colon_tok.line:
                    return_type = self.parse_type_specifier()
            elif self.is_type_token(self.current_token()) and self.current_token().line == close_paren.line:
                return_type = self.parse_type_specifier()

        # Parsear cuerpo de la función hasta FIN FUNCION / FIN PROCEDIMIENTO
        body: List[Statement] = []
        end_kw = TokenType.KW_PROCEDIMIENTO if is_proc else TokenType.KW_FUNCION

        while self.current_token().type != TokenType.EOF:
            if self.current_token().type == TokenType.KW_FIN:
                if self.peek_token().type == end_kw:
                    self.advance()  # consume FIN
                    self.advance()  # consume FUNCION / PROCEDIMIENTO
                    break
                elif self.peek_token().type == TokenType.KW_FUNCION and is_proc:
                    # Tolerancia si cierra un procedimiento con FIN FUNCION
                    self.advance()
                    self.advance()
                    break
            body.append(self.parse_statement())

        return FunctionDef(name, params, return_type, body, is_proc, start_tok.line, start_tok.column)

    def parse_parameters(self) -> List[Parameter]:
        params: List[Parameter] = []
        if self.current_token().type == TokenType.PARENTESIS_DER:
            return params

        while True:
            name_tok = self.expect(TokenType.IDENTIFICADOR, "Se esperaba nombre del parámetro")
            p_name = name_tok.value
            is_vector = False
            is_matrix = False

            # Sintaxis estilo: matriz[]: ENTERO o matriz[][]: ENTERO
            while self.match(TokenType.CORCHETE_IZQ):
                self.expect(TokenType.CORCHETE_DER, "Se esperaba ']' en la especificación del parámetro")
                if is_vector:
                    is_matrix = True
                else:
                    is_vector = True

            self.expect(TokenType.DOS_PUNTOS, "Se esperaba ':' para indicar el tipo del parámetro")
            base_type = self.parse_type_specifier()

            if is_matrix:
                param_type = MatrixType(base_type if not isinstance(base_type, (VectorType, MatrixType)) else base_type.element_type)
            elif is_vector:
                param_type = VectorType(base_type if not isinstance(base_type, (VectorType, MatrixType)) else base_type.element_type)
            else:
                param_type = base_type

            params.append(Parameter(p_name, param_type, name_tok.line, name_tok.column))

            if not self.match(TokenType.COMA):
                break

        return params

    def is_type_token(self, tok: Token) -> bool:
        return tok.type in TOKEN_TO_TYPE

    def parse_type_specifier(self) -> DataType:
        tok = self.current_token()
        if tok.type not in TOKEN_TO_TYPE:
            raise ParseError(f"Tipo de dato no válido: '{tok.value}'", line=tok.line, column=tok.column, source=self.source)
        self.advance()
        dtype = TOKEN_TO_TYPE[tok.type]

        # Verificar si tiene corchetes (ej. REAL[] o ENTERO[][])
        while self.match(TokenType.CORCHETE_IZQ):
            self.expect(TokenType.CORCHETE_DER, "Se esperaba ']' en el tipo compuesto")
            if isinstance(dtype, VectorType):
                dtype = MatrixType(dtype.element_type)
            else:
                dtype = VectorType(dtype)
        return dtype

    # ==========================================
    # SENTENCIAS (STATEMENTS)
    # ==========================================

    def parse_statement(self) -> Statement:
        tok = self.current_token()

        # Detección temprana de funciones/procedimientos dentro de bloques anidados
        if tok.type in (TokenType.KW_FUNCION, TokenType.KW_PROCEDIMIENTO):
            raise ParseError(
                f"Declaración inesperada: '{tok.value}' no se puede declarar dentro de una sentencia o bloque anidado.",
                line=tok.line, column=tok.column, length=tok.length, source=self.source
            )

        # Chequeo preventivo de errores de tipeo al inicio de sentencias
        if tok.type == TokenType.IDENTIFICADOR:
            next_tok = self.peek_token(1)
            next_next_tok = self.peek_token(2)

            # Intento de declarar función/procedimiento: <id1> <id2>(
            if next_tok.type == TokenType.IDENTIFICADOR and next_next_tok.type == TokenType.PARENTESIS_IZQ:
                suggestion = self.check_keyword_typo(tok, ["FUNCION", "PROCEDIMIENTO"])
                if suggestion:
                    raise ParseError(
                        f"Palabra clave no reconocida: '{tok.value}'. ¿Quisiste decir '{suggestion}'?",
                        line=tok.line, column=tok.column, length=tok.length, source=self.source
                    )
                else:
                    raise ParseError(
                        f"Declaración no válida: se esperaba 'FUNCION' o 'PROCEDIMIENTO' antes de '{next_tok.value}', pero se encontró '{tok.value}'.",
                        line=tok.line, column=tok.column, length=tok.length, source=self.source
                    )

            # Tipos de datos mal escritos al declarar variable: ej: ENTER x = 10, INT x = 10, CADEN nombre = "test"
            if next_tok.type == TokenType.IDENTIFICADOR and next_next_tok.type in (TokenType.ASIGNAR, TokenType.CORCHETE_IZQ, TokenType.PUNTO_Y_COMA):
                type_suggestion = self.check_keyword_typo(tok, ["ENTERO", "REAL", "FLOTANTE", "CADENA", "BOOLEANO", "CARACTER", "ARCHIVO"])
                if type_suggestion:
                    raise ParseError(
                        f"Tipo de dato no reconocido: '{tok.value}'. ¿Quisiste decir '{type_suggestion}'?",
                        line=tok.line, column=tok.column, length=tok.length, source=self.source
                    )

            # Palabras clave de control mal escritas (no aplica si es asignación o incremento de variable)
            if next_tok.type not in (TokenType.ASIGNAR, TokenType.ASIG_SUMA, TokenType.ASIG_RESTA, TokenType.INC, TokenType.DEC):
                ctrl_suggestion = self.check_keyword_typo(tok, ["RETORNAR", "IMPRIMIR", "MIENTRAS", "HACER", "PARA", "SI"])
                if ctrl_suggestion:
                    raise ParseError(
                        f"Palabra clave no reconocida: '{tok.value}'. ¿Quisiste decir '{ctrl_suggestion}'?",
                        line=tok.line, column=tok.column, length=tok.length, source=self.source
                    )

        # 1. Declaración de variables: TIPO ...
        if self.is_type_token(tok):
            return self.parse_var_declaration()

        # 2. Retorno (RETORNAR / RETORNO)
        if tok.type in (TokenType.KW_RETORNAR, TokenType.KW_RETORNO):
            self.advance()
            val = None
            if not self.is_statement_terminator(self.current_token()):
                val = self.parse_expression()
            self.match(TokenType.PUNTO_Y_COMA)
            return ReturnStatement(val, tok.line, tok.column)

        # 3. Imprimir
        if tok.type == TokenType.KW_IMPRIMIR:
            self.advance()
            has_paren = self.match(TokenType.PARENTESIS_IZQ)
            expr = self.parse_expression()
            if has_paren:
                self.expect(TokenType.PARENTESIS_DER, "Se esperaba ')' después de la expresión en IMPRIMIR")
            self.match(TokenType.PUNTO_Y_COMA)
            return PrintStatement(expr, tok.line, tok.column)

        # 4. Condicional SI
        if tok.type == TokenType.KW_SI:
            return self.parse_if_statement()

        # 5. Bucle MIENTRAS
        if tok.type == TokenType.KW_MIENTRAS:
            return self.parse_while_statement()

        # 6. Bucle HACER ... MIENTRAS ... FIN HACER
        if tok.type == TokenType.KW_HACER:
            return self.parse_do_while_statement()

        # 7. Bucle PARA
        if tok.type == TokenType.KW_PARA:
            return self.parse_for_statement()

        # 8. Asignación, incremento/decremento o llamada a expresión
        expr = self.parse_expression()

        # Postfix ++ / --
        if self.match(TokenType.INC):
            self.match(TokenType.PUNTO_Y_COMA)
            return IncrementStatement(expr, is_increment=True, line=tok.line, column=tok.column)
        if self.match(TokenType.DEC):
            self.match(TokenType.PUNTO_Y_COMA)
            return IncrementStatement(expr, is_increment=False, line=tok.line, column=tok.column)

        # Operadores de asignación: =, +=, -=
        if self.match(TokenType.ASIGNAR):
            val = self.parse_expression()
            self.match(TokenType.PUNTO_Y_COMA)
            return Assignment(expr, "=", val, tok.line, tok.column)
        if self.match(TokenType.ASIG_SUMA):
            val = self.parse_expression()
            self.match(TokenType.PUNTO_Y_COMA)
            return Assignment(expr, "+=", val, tok.line, tok.column)
        if self.match(TokenType.ASIG_RESTA):
            val = self.parse_expression()
            self.match(TokenType.PUNTO_Y_COMA)
            return Assignment(expr, "-=", val, tok.line, tok.column)

        self.match(TokenType.PUNTO_Y_COMA)
        return ExpressionStatement(expr, tok.line, tok.column)

    def is_statement_terminator(self, tok: Token) -> bool:
        return tok.type in (TokenType.PUNTO_Y_COMA, TokenType.KW_FIN, TokenType.KW_SINO, TokenType.EOF)

    # ------------------------------------------
    # DECLARACIONES
    # ------------------------------------------

    def parse_var_declaration(self) -> VarDeclaration:
        type_tok = self.current_token()
        base_type = self.parse_type_specifier()

        name_tok = self.expect(TokenType.IDENTIFICADOR, "Se esperaba el identificador de la variable")
        var_name = name_tok.value

        size_exprs: List[Expression] = []
        is_array = False
        bracket_count = 0

        # Comprobar si se declara con corchetes en el nombre: arr[10], mat[12][30], vec[], mat[][]
        while self.match(TokenType.CORCHETE_IZQ):
            is_array = True
            bracket_count += 1
            if self.current_token().type != TokenType.CORCHETE_DER:
                size_exprs.append(self.parse_expression())
            self.expect(TokenType.CORCHETE_DER, "Se esperaba ']' en el tamaño del vector/matriz")

        final_type = base_type
        if is_array and not isinstance(base_type, (VectorType, MatrixType)):
            if bracket_count >= 2:
                final_type = MatrixType(base_type)
            else:
                final_type = VectorType(base_type)

        initializer: Optional[Expression] = None
        if self.match(TokenType.ASIGNAR):
            initializer = self.parse_expression()

        self.match(TokenType.PUNTO_Y_COMA)
        return VarDeclaration(var_name, final_type, size_exprs, initializer, type_tok.line, type_tok.column)

    # ------------------------------------------
    # ESTRUCTURAS DE CONTROL
    # ------------------------------------------

    def parse_if_statement(self) -> IfStatement:
        si_tok = self.expect(TokenType.KW_SI)
        condition = self.parse_condition_expression()

        then_branch: List[Statement] = []
        elif_branches: List[Tuple[Expression, List[Statement]]] = []
        else_branch: Optional[List[Statement]] = None

        while self.current_token().type not in (TokenType.KW_FIN, TokenType.KW_SINO, TokenType.EOF):
            if len(then_branch) > 0 and self.current_token().column <= si_tok.column:
                break
            then_branch.append(self.parse_statement())

        # SINO o SINO SI
        while self.current_token().type == TokenType.KW_SINO:
            self.advance()  # consume SINO
            if self.match(TokenType.KW_SI):
                elif_cond = self.parse_condition_expression()
                elif_body: List[Statement] = []
                while self.current_token().type not in (TokenType.KW_FIN, TokenType.KW_SINO, TokenType.EOF):
                    if len(elif_body) > 0 and self.current_token().column <= si_tok.column:
                        break
                    elif_body.append(self.parse_statement())
                elif_branches.append((elif_cond, elif_body))
            else:
                else_body: List[Statement] = []
                while self.current_token().type not in (TokenType.KW_FIN, TokenType.EOF):
                    if len(else_body) > 0 and self.current_token().column <= si_tok.column:
                        break
                    else_body.append(self.parse_statement())
                else_branch = else_body
                break

        # Consumir FIN SI si está presente de forma explícita
        if self.current_token().type == TokenType.KW_FIN and self.peek_token().type == TokenType.KW_SI:
            self.advance()  # consume FIN
            self.advance()  # consume SI

        return IfStatement(condition, then_branch, elif_branches, else_branch, si_tok.line, si_tok.column)

    def parse_while_statement(self) -> WhileStatement:
        while_tok = self.expect(TokenType.KW_MIENTRAS)
        condition = self.parse_condition_expression()

        body: List[Statement] = []
        while self.current_token().type != TokenType.EOF:
            if self.current_token().type == TokenType.KW_FIN and self.peek_token().type == TokenType.KW_MIENTRAS:
                self.advance()  # consume FIN
                self.advance()  # consume MIENTRAS
                break
            body.append(self.parse_statement())

        return WhileStatement(condition, body, while_tok.line, while_tok.column)

    def parse_do_while_statement(self) -> DoWhileStatement:
        hacer_tok = self.expect(TokenType.KW_HACER)

        body: List[Statement] = []
        while self.current_token().type != TokenType.EOF:
            if self.current_token().type == TokenType.KW_MIENTRAS:
                break
            body.append(self.parse_statement())

        self.expect(TokenType.KW_MIENTRAS, "Se esperaba 'MIENTRAS' en ciclo HACER...MIENTRAS")
        condition = self.parse_condition_expression()

        self.expect(TokenType.KW_FIN, "Se esperaba 'FIN HACER'")
        self.expect(TokenType.KW_HACER, "Se esperaba 'HACER' después de 'FIN'")

        return DoWhileStatement(body, condition, hacer_tok.line, hacer_tok.column)

    def parse_for_statement(self) -> ForStatement:
        for_tok = self.expect(TokenType.KW_PARA)
        self.expect(TokenType.PARENTESIS_IZQ, "Se esperaba '(' después de PARA")

        # Inicialización: ej. ENTERO col = 0 o col = 0
        init_stmt: Optional[Statement] = None
        if self.current_token().type != TokenType.PUNTO_Y_COMA and self.current_token().type != TokenType.DOS_PUNTOS:
            if self.is_type_token(self.current_token()):
                init_stmt = self.parse_var_declaration()
            else:
                expr = self.parse_expression()
                if self.match(TokenType.ASIGNAR):
                    val = self.parse_expression()
                    init_stmt = Assignment(expr, "=", val, expr.line, expr.column)
                else:
                    init_stmt = ExpressionStatement(expr, expr.line, expr.column)

        # Separador tolerante: ';' o ':'
        if not (self.match(TokenType.PUNTO_Y_COMA) or self.match(TokenType.DOS_PUNTOS)):
            # Ya pudo ser consumido en parse_var_declaration si venía con ';'
            pass

        # Condición: ej. col < columnas
        cond_expr: Optional[Expression] = None
        if self.current_token().type not in (TokenType.PUNTO_Y_COMA, TokenType.DOS_PUNTOS, TokenType.PARENTESIS_DER):
            cond_expr = self.parse_expression()

        # Segundo separador tolerante: ';' o ':'
        self.match(TokenType.PUNTO_Y_COMA) or self.match(TokenType.DOS_PUNTOS)

        # Paso: ej. col++ o col = col + 1
        step_stmt: Optional[Statement] = None
        if self.current_token().type != TokenType.PARENTESIS_DER:
            expr = self.parse_expression()
            if self.match(TokenType.INC):
                step_stmt = IncrementStatement(expr, is_increment=True, line=expr.line, column=expr.column)
            elif self.match(TokenType.DEC):
                step_stmt = IncrementStatement(expr, is_increment=False, line=expr.line, column=expr.column)
            elif self.match(TokenType.ASIGNAR):
                val = self.parse_expression()
                step_stmt = Assignment(expr, "=", val, expr.line, expr.column)
            else:
                step_stmt = ExpressionStatement(expr, expr.line, expr.column)

        self.expect(TokenType.PARENTESIS_DER, "Se esperaba ')' al final del encabezado PARA")

        # Cuerpo
        body: List[Statement] = []
        while self.current_token().type != TokenType.EOF:
            if self.current_token().type == TokenType.KW_FIN and self.peek_token().type == TokenType.KW_PARA:
                self.advance()  # consume FIN
                self.advance()  # consume PARA
                break
            body.append(self.parse_statement())

        return ForStatement(init_stmt, cond_expr, step_stmt, body, for_tok.line, for_tok.column)

    def parse_block_until(self, *end_tokens: TokenType) -> List[Statement]:
        stmts: List[Statement] = []
        while self.current_token().type not in end_tokens and self.current_token().type != TokenType.EOF:
            stmts.append(self.parse_statement())
        return stmts

    # ==========================================
    # EXPRESIONES Y TOLERANCIA SINTÁCTICA
    # ==========================================

    def parse_condition_expression(self) -> Expression:
        """
        Parsea una condición, soportando:
        - SI (condicion)
        - SI condicion
        - SI (cond1) O SI (cond2) > expr
        - SI (cond1) || SI (cond2)
        """
        return self.parse_expression()

    def parse_expression(self) -> Expression:
        return self.parse_logical_or()

    def parse_logical_or(self) -> Expression:
        left = self.parse_logical_and()

        while self.match(TokenType.OP_O):
            tok = self.tokens[self.pos - 1]
            # Tolerancia de pseudocódigo: SI(...) || SI(...) o expr O SI(...)
            if self.match(TokenType.KW_SI):
                pass
            right = self.parse_logical_and()
            left = BinaryOp(left, "O", right, tok.line, tok.column)

        return left

    def parse_logical_and(self) -> Expression:
        left = self.parse_relational()

        while self.match(TokenType.OP_Y):
            tok = self.tokens[self.pos - 1]
            if self.match(TokenType.KW_SI):
                pass
            right = self.parse_relational()
            left = BinaryOp(left, "Y", right, tok.line, tok.column)

        return left

    def parse_relational(self) -> Expression:
        left = self.parse_additive()

        rel_ops = {
            TokenType.IGUAL_QUE: "==",
            TokenType.DISTINTO: "!=",
            TokenType.MENOR: "<",
            TokenType.MENOR_IGUAL: "<=",
            TokenType.MAYOR: ">",
            TokenType.MAYOR_IGUAL: ">=",
        }

        while self.current_token().type in rel_ops:
            op_tok = self.advance()
            right = self.parse_additive()
            left = BinaryOp(left, rel_ops[op_tok.type], right, op_tok.line, op_tok.column)

        return left

    def parse_additive(self) -> Expression:
        left = self.parse_multiplicative()

        while self.current_token().type in (TokenType.SUMA, TokenType.RESTA):
            op_tok = self.advance()
            right = self.parse_multiplicative()
            left = BinaryOp(left, op_tok.value, right, op_tok.line, op_tok.column)

        return left

    def parse_multiplicative(self) -> Expression:
        left = self.parse_unary()

        while self.current_token().type in (TokenType.MULT, TokenType.DIV, TokenType.MOD):
            op_tok = self.advance()
            right = self.parse_unary()
            left = BinaryOp(left, op_tok.value, right, op_tok.line, op_tok.column)

        return left

    def parse_unary(self) -> Expression:
        tok = self.current_token()

        if tok.type in (TokenType.OP_NO, TokenType.RESTA, TokenType.SUMA):
            op_tok = self.advance()
            operand = self.parse_unary()
            op_symbol = "NO" if op_tok.type == TokenType.OP_NO else op_tok.value
            return UnaryOp(op_symbol, operand, op_tok.line, op_tok.column)

        return self.parse_postfix()

    def parse_postfix(self) -> Expression:
        expr = self.parse_primary()

        while True:
            # Indexación múltiple: matriz[i][j] o vector[i]
            if self.match(TokenType.CORCHETE_IZQ):
                indices: List[Expression] = []
                idx_expr = self.parse_expression()
                self.expect(TokenType.CORCHETE_DER, "Se esperaba ']' después del índice")
                indices.append(idx_expr)
                expr = IndexAccess(expr, indices, expr.line, expr.column)
                continue

            # Acceso a miembros y métodos: file.findearchivo, file.CERRAR_ARCHIVO(), vector.largo
            if self.match(TokenType.PUNTO):
                member_tok = self.expect(TokenType.IDENTIFICADOR, "Se esperaba nombre del campo o método después de '.'")
                member_name = member_tok.value

                # Si es llamada a método: file.LEER_LINEA()
                if self.match(TokenType.PARENTESIS_IZQ):
                    args = self.parse_arguments()
                    self.expect(TokenType.PARENTESIS_DER, "Se esperaba ')' al finalizar la llamada")
                    callee = MemberAccess(expr, member_name, member_tok.line, member_tok.column)
                    expr = FunctionCall(callee, args, member_tok.line, member_tok.column)
                else:
                    expr = MemberAccess(expr, member_name, member_tok.line, member_tok.column)
                continue

            # Llamada a función con sintaxis callee(...)
            if self.match(TokenType.PARENTESIS_IZQ):
                args = self.parse_arguments()
                self.expect(TokenType.PARENTESIS_DER, "Se esperaba ')' al finalizar la llamada")
                expr = FunctionCall(expr, args, expr.line, expr.column)
                continue

            break

        return expr

    def parse_arguments(self) -> List[Expression]:
        args: List[Expression] = []
        if self.current_token().type == TokenType.PARENTESIS_DER:
            return args

        while True:
            args.append(self.parse_expression())
            if not self.match(TokenType.COMA):
                break

        return args

    def parse_primary(self) -> Expression:
        tok = self.current_token()

        # Literales numéricos
        if tok.type == TokenType.ENTERO_LIT:
            self.advance()
            return Literal(tok.value, TYPE_ENTERO, tok.line, tok.column)

        if tok.type == TokenType.REAL_LIT:
            self.advance()
            return Literal(tok.value, TYPE_REAL, tok.line, tok.column)

        # Cadenas y Caracteres
        if tok.type == TokenType.CADENA_LIT:
            self.advance()
            return Literal(tok.value, TYPE_CADENA, tok.line, tok.column)

        if tok.type == TokenType.CARACTER_LIT:
            self.advance()
            return Literal(tok.value, TYPE_CARACTER, tok.line, tok.column)

        # Booleanos
        if tok.type == TokenType.BOOLEANO_LIT:
            self.advance()
            return Literal(tok.value, TYPE_BOOLEANO, tok.line, tok.column)

        # Literales de Arreglos/Vectores: [1, 2, 3] o [[1, 2], [3, 4]]
        if self.match(TokenType.CORCHETE_IZQ):
            elements: List[Expression] = []
            if self.current_token().type != TokenType.CORCHETE_DER:
                while True:
                    elements.append(self.parse_expression())
                    if not self.match(TokenType.COMA):
                        break
            self.expect(TokenType.CORCHETE_DER, "Se esperaba ']' al cerrar la lista de elementos")
            return ArrayLiteral(elements, tok.line, tok.column)

        # Funciones matemáticas de estructuras.txt: ESPAR, ESIMPAR, MOD
        if tok.type in (TokenType.KW_ESPAR, TokenType.KW_ESIMPAR, TokenType.KW_MOD):
            fn_tok = self.advance()
            self.expect(TokenType.PARENTESIS_IZQ, f"Se esperaba '(' después de {fn_tok.value}")
            args = self.parse_arguments()
            self.expect(TokenType.PARENTESIS_DER, f"Se esperaba ')' después de los argumentos de {fn_tok.value}")
            callee = Variable(fn_tok.value.upper(), fn_tok.line, fn_tok.column)
            return FunctionCall(callee, args, fn_tok.line, fn_tok.column)

        # Identificadores (variables o llamadas globales como ABRIR_ARCHIVO)
        if tok.type == TokenType.IDENTIFICADOR:
            self.advance()
            # Tolerancia: SI(NO var) O SI(var) > ...
            return Variable(tok.value, tok.line, tok.column)

        # Tolerancia: SI seguido de paréntesis dentro de expresión
        if tok.type == TokenType.KW_SI:
            self.advance()
            if self.match(TokenType.PARENTESIS_IZQ):
                inner = self.parse_expression()
                self.expect(TokenType.PARENTESIS_DER, "Se esperaba ')' después de SI")
                return inner

        # Paréntesis agrupadores: ( expr )
        if self.match(TokenType.PARENTESIS_IZQ):
            inner = self.parse_expression()
            self.expect(TokenType.PARENTESIS_DER, "Se esperaba ')' de cierre")
            return inner

        if tok.type == TokenType.CORCHETE_DER:
            raise ParseError(
                "Expresión esperada dentro de los corchetes '[]'. Los corchetes vacíos '[]' solo son válidos al definir parámetros (ej: 'vector[]: ENTERO').",
                line=tok.line, column=tok.column, length=1, source=self.source
            )

        raise ParseError(
            f"Expresión inesperada: token '{tok.value}' ({tok.type.name})",
            line=tok.line, column=tok.column, length=tok.length, source=self.source
        )
