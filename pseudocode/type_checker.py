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
Verificador estático de tipos (Semantic Analyzer / Type Checker) para pseudocódigo.
Valida declaraciones, compatibilidad de tipos, llamadas a funciones y aridades antes de la ejecución.
"""

import difflib
from typing import Dict, List, Optional, Any, Tuple
from pseudocode.types_system import (
    DataType, VectorType, MatrixType,
    TYPE_ENTERO, TYPE_FLOTANTE, TYPE_REAL, TYPE_CADENA,
    TYPE_CARACTER, TYPE_BOOLEANO, TYPE_ARCHIVO, TYPE_VOID, TYPE_ANY
)
from pseudocode.ast_nodes import (
    Program, FunctionDef, Parameter, Statement, Expression,
    VarDeclaration, Assignment, IncrementStatement,
    IfStatement, WhileStatement, DoWhileStatement, ForStatement,
    ReturnStatement, PrintStatement, ExpressionStatement,
    Literal, ArrayLiteral, Variable, BinaryOp, UnaryOp,
    IndexAccess, MemberAccess, FunctionCall
)
from pseudocode.errors import TypeError as PseudoTypeError


class Symbol:
    def __init__(self, name: str, data_type: DataType, line: int = 1, column: int = 1):
        self.name = name
        self.data_type = data_type
        self.line = line
        self.column = column


class Scope:
    def __init__(self, parent: Optional['Scope'] = None, name: str = "global"):
        self.parent = parent
        self.name = name
        self.symbols: Dict[str, Symbol] = {}

    def define(self, name: str, data_type: DataType, line: int = 1, column: int = 1):
        self.symbols[name] = Symbol(name, data_type, line, column)

    def lookup(self, name: str) -> Optional[Symbol]:
        if name in self.symbols:
            return self.symbols[name]
        if self.parent:
            return self.parent.lookup(name)
        return None

    def get_all_symbols(self) -> List[str]:
        names = list(self.symbols.keys())
        if self.parent:
            names.extend(self.parent.get_all_symbols())
        return list(set(names))


class TypeChecker:
    def __init__(self, source: str = "", filename: str = "<código>", lenient: bool = False):
        self.source = source
        self.filename = filename
        self.lenient = lenient
        self.global_scope = Scope(name="global")
        self.current_scope = self.global_scope
        self.functions: Dict[str, FunctionDef] = {}
        self.current_function: Optional[FunctionDef] = None
        self.warnings: List[str] = []

        self._register_builtins()

    def _register_builtins(self):
        # Builtin functions
        self.global_scope.define("ABRIR_ARCHIVO", TYPE_ANY)
        self.global_scope.define("ESPAR", TYPE_BOOLEANO)
        self.global_scope.define("ESIMPAR", TYPE_BOOLEANO)
        self.global_scope.define("MOD", TYPE_ENTERO)
        self.global_scope.define("IMPRIMIR", TYPE_VOID)

    def check(self, program: Program):
        # 1. Registrar firmas de todas las funciones
        for func in program.functions:
            if func.name in self.functions:
                if not self.lenient:
                    raise PseudoTypeError(
                        f"La función o procedimiento '{func.name}' ya ha sido declarada.",
                        line=func.line, column=func.column, source=self.source
                    )
                else:
                    self.warnings.append(f"Advertencia: redefinición de '{func.name}' en línea {func.line}")
            self.functions[func.name] = func
            self.global_scope.define(func.name, func.return_type, func.line, func.column)

        # 2. Verificar cuerpos de funciones
        for func in program.functions:
            self.check_function(func)

        # 3. Verificar sentencias globales
        for stmt in program.statements:
            self.check_statement(stmt)

    def check_function(self, func: FunctionDef):
        self.current_function = func
        fn_scope = Scope(parent=self.global_scope, name=func.name)
        self.current_scope = fn_scope

        # Registrar parámetros
        for p in func.params:
            fn_scope.define(p.name, p.data_type, p.line, p.column)

        # Verificar cuerpo
        for stmt in func.body:
            self.check_statement(stmt)

        self.current_scope = self.global_scope
        self.current_function = None

    def check_statement(self, stmt: Statement):
        if isinstance(stmt, VarDeclaration):
            # Verificar expresiones de tamaño si es array
            for s_expr in stmt.size_exprs:
                s_type = self.check_expression(s_expr)
                if s_type not in (TYPE_ENTERO, TYPE_ANY):
                    raise PseudoTypeError(
                        f"El tamaño del vector o matriz debe ser ENTERO, se obtuvo {s_type}",
                        line=s_expr.line, column=s_expr.column, source=self.source
                    )

            if stmt.initializer:
                val_type = self.check_expression(stmt.initializer)

                # Si se declara 'TIPO var = [...]' o 'TIPO var = funcion_retorna_vector()',
                # se adapta el tipo a TIPO[] o TIPO[][] tal como especifica estructuras.txt
                if not isinstance(stmt.data_type, (VectorType, MatrixType)):
                    if isinstance(val_type, VectorType) and (stmt.data_type == val_type.element_type or stmt.data_type.is_assignable_from(val_type.element_type)):
                        stmt.data_type = VectorType(stmt.data_type)
                    elif isinstance(val_type, MatrixType) and (stmt.data_type == val_type.element_type or stmt.data_type.is_assignable_from(val_type.element_type)):
                        stmt.data_type = MatrixType(stmt.data_type)

                # Si es un vector (ej: pivot[1] = vector[0]) inicializado con un escalar compatible
                if isinstance(stmt.data_type, VectorType) and stmt.data_type.element_type.is_assignable_from(val_type):
                    pass
                elif not stmt.data_type.is_assignable_from(val_type) and val_type != TYPE_ANY:
                    if self.lenient:
                        self.warnings.append(f"Advertencia (L{stmt.line}): Inicialización de {stmt.name} ({stmt.data_type}) con {val_type}")
                    else:
                        raise PseudoTypeError(
                            f"No se puede asignar un valor de tipo {val_type} a la variable '{stmt.name}' de tipo {stmt.data_type}",
                            line=stmt.line, column=stmt.column, source=self.source
                        )

            self.current_scope.define(stmt.name, stmt.data_type, stmt.line, stmt.column)

        elif isinstance(stmt, Assignment):
            target_type = self.check_assignment_target(stmt.target)
            val_type = self.check_expression(stmt.value)

            # En pseudocódigo, asignar texto (ej: file.LEER_LINEA()) a un número implica parseo automático
            is_numeric_target = target_type in (TYPE_ENTERO, TYPE_FLOTANTE, TYPE_REAL)
            if is_numeric_target and val_type == TYPE_CADENA:
                pass
            elif not target_type.is_assignable_from(val_type) and val_type != TYPE_ANY:
                if self.lenient and is_numeric_target and val_type in (TYPE_ENTERO, TYPE_FLOTANTE, TYPE_REAL):
                    self.warnings.append(f"Advertencia (L{stmt.line}): Conversión numérica de {val_type} a {target_type}")
                elif not (isinstance(target_type, (VectorType, MatrixType)) and val_type == TYPE_ANY):
                    if self.lenient:
                        self.warnings.append(f"Advertencia (L{stmt.line}): Asignación de {val_type} a {target_type}")
                    else:
                        raise PseudoTypeError(
                            f"Incompatibilidad de tipos en asignación: no se puede asignar {val_type} a {target_type}",
                            line=stmt.line, column=stmt.column, source=self.source
                        )

        elif isinstance(stmt, IncrementStatement):
            target_type = self.check_assignment_target(stmt.target)
            if target_type not in (TYPE_ENTERO, TYPE_FLOTANTE, TYPE_REAL, TYPE_ANY):
                raise PseudoTypeError(
                    f"Operador ++ / -- solo es aplicable a tipos numéricos, se obtuvo {target_type}",
                    line=stmt.line, column=stmt.column, source=self.source
                )

        elif isinstance(stmt, IfStatement):
            cond_type = self.check_expression(stmt.condition)
            for s in stmt.then_branch:
                self.check_statement(s)
            for elif_cond, elif_stmts in stmt.elif_branches:
                self.check_expression(elif_cond)
                for s in elif_stmts:
                    self.check_statement(s)
            if stmt.else_branch:
                for s in stmt.else_branch:
                    self.check_statement(s)

        elif isinstance(stmt, WhileStatement):
            self.check_expression(stmt.condition)
            for s in stmt.body:
                self.check_statement(s)

        elif isinstance(stmt, DoWhileStatement):
            for s in stmt.body:
                self.check_statement(s)
            self.check_expression(stmt.condition)

        elif isinstance(stmt, ForStatement):
            for_scope = Scope(parent=self.current_scope, name="for")
            self.current_scope = for_scope
            if stmt.init:
                self.check_statement(stmt.init)
            if stmt.condition:
                self.check_expression(stmt.condition)
            if stmt.step:
                self.check_statement(stmt.step)
            for s in stmt.body:
                self.check_statement(s)
            self.current_scope = for_scope.parent

        elif isinstance(stmt, ReturnStatement):
            if self.current_function and self.current_function.is_procedure:
                if stmt.value is not None:
                    raise PseudoTypeError(
                        f"Un PROCEDIMIENTO no puede retornar un valor.",
                        line=stmt.line, column=stmt.column, source=self.source
                    )
            elif self.current_function and self.current_function.return_type != TYPE_VOID:
                if stmt.value is None:
                    raise PseudoTypeError(
                        f"La función '{self.current_function.name}' debe retornar un valor de tipo {self.current_function.return_type}.",
                        line=stmt.line, column=stmt.column, source=self.source
                    )
                val_type = self.check_expression(stmt.value)
                if not self.current_function.return_type.is_assignable_from(val_type) and val_type != TYPE_ANY:
                    msg = f"El tipo retornado {val_type} no coincide con el tipo esperado {self.current_function.return_type}."
                    if self.lenient:
                        self.warnings.append(f"Advertencia (L{stmt.line}): {msg}")
                    else:
                        raise PseudoTypeError(
                            msg,
                            line=stmt.line, column=stmt.column, source=self.source
                        )

        elif isinstance(stmt, PrintStatement):
            self.check_expression(stmt.value)

        elif isinstance(stmt, ExpressionStatement):
            self.check_expression(stmt.expr)

    def check_assignment_target(self, target: Expression) -> DataType:
        if isinstance(target, Variable):
            sym = self.current_scope.lookup(target.name)
            if not sym:
                if self.lenient:
                    self.current_scope.define(target.name, TYPE_ANY, target.line, target.column)
                    self.warnings.append(f"Auto-declarada variable '{target.name}' en línea {target.line}")
                    return TYPE_ANY

                # Sugerencia de nombre si hay error tipográfico
                candidates = self.current_scope.get_all_symbols()
                matches = difflib.get_close_matches(target.name, candidates, n=1, cutoff=0.6)
                sug = f". ¿Quisiste decir '{matches[0]}'?" if matches else ""
                raise PseudoTypeError(
                    f"Variable no declarada '{target.name}'{sug}",
                    line=target.line, column=target.column, source=self.source
                )
            return sym.data_type

        elif isinstance(target, IndexAccess):
            target_type = self.check_assignment_target(target.target)
            for idx_expr in target.indices:
                idx_type = self.check_expression(idx_expr)
                if idx_type not in (TYPE_ENTERO, TYPE_ANY):
                    raise PseudoTypeError(
                        f"El índice debe ser ENTERO, se obtuvo {idx_type}",
                        line=idx_expr.line, column=idx_expr.column, source=self.source
                    )
            if isinstance(target_type, MatrixType):
                if len(target.indices) == 1:
                    return VectorType(target_type.element_type)
                return target_type.element_type
            if isinstance(target_type, VectorType):
                return target_type.element_type
            return TYPE_ANY

        return TYPE_ANY

    def check_expression(self, expr: Expression) -> DataType:
        if isinstance(expr, Literal):
            return expr.data_type

        if isinstance(expr, ArrayLiteral):
            if not expr.elements:
                return VectorType(TYPE_ANY)
            elem_types = [self.check_expression(e) for e in expr.elements]
            first = elem_types[0]
            if isinstance(first, VectorType):
                return MatrixType(first.element_type)
            return VectorType(first)

        if isinstance(expr, Variable):
            sym = self.current_scope.lookup(expr.name)
            if not sym:
                # Si es una función
                if expr.name in self.functions:
                    return self.functions[expr.name].return_type

                if self.lenient:
                    self.current_scope.define(expr.name, TYPE_ANY, expr.line, expr.column)
                    self.warnings.append(f"Auto-declarada variable '{expr.name}' en línea {expr.line}")
                    return TYPE_ANY

                candidates = self.current_scope.get_all_symbols() + list(self.functions.keys())
                matches = difflib.get_close_matches(expr.name, candidates, n=1, cutoff=0.6)
                sug = f". ¿Quisiste decir '{matches[0]}'?" if matches else ""
                raise PseudoTypeError(
                    f"Identificador no declarado: '{expr.name}'{sug}",
                    line=expr.line, column=expr.column, source=self.source
                )
            return sym.data_type

        if isinstance(expr, BinaryOp):
            left_t = self.check_expression(expr.left)
            right_t = self.check_expression(expr.right)

            if expr.op == "+":
                # Concatenación de cadenas
                if left_t == TYPE_CADENA or right_t == TYPE_CADENA:
                    return TYPE_CADENA
                # Concatenación de vectores
                if isinstance(left_t, VectorType) or isinstance(right_t, VectorType):
                    return left_t if isinstance(left_t, VectorType) else right_t
                # Aritmética
                if left_t == TYPE_REAL or right_t == TYPE_REAL:
                    return TYPE_REAL
                if left_t == TYPE_FLOTANTE or right_t == TYPE_FLOTANTE:
                    return TYPE_FLOTANTE
                return TYPE_ENTERO

            if expr.op in ("-", "*", "/", "%"):
                if expr.op == "/" and left_t == TYPE_ENTERO and right_t == TYPE_ENTERO:
                    return TYPE_REAL
                if left_t == TYPE_REAL or right_t == TYPE_REAL:
                    return TYPE_REAL
                if left_t == TYPE_FLOTANTE or right_t == TYPE_FLOTANTE:
                    return TYPE_FLOTANTE
                return TYPE_ENTERO

            if expr.op in ("==", "!=", "<", "<=", ">", ">="):
                return TYPE_BOOLEANO

            if expr.op in ("Y", "O"):
                return TYPE_BOOLEANO

        if isinstance(expr, UnaryOp):
            op_t = self.check_expression(expr.operand)
            if expr.op in ("NO", "!"):
                return TYPE_BOOLEANO
            return op_t

        if isinstance(expr, IndexAccess):
            target_t = self.check_expression(expr.target)
            for idx in expr.indices:
                i_t = self.check_expression(idx)
                if i_t not in (TYPE_ENTERO, TYPE_ANY):
                    raise PseudoTypeError(
                        f"El índice debe ser ENTERO, se obtuvo {i_t}",
                        line=idx.line, column=idx.column, source=self.source
                    )
            if isinstance(target_t, MatrixType):
                if len(expr.indices) == 1:
                    return VectorType(target_t.element_type)
                return target_t.element_type
            if isinstance(target_t, VectorType):
                return target_t.element_type
            if target_t == TYPE_CADENA:
                return TYPE_CARACTER
            return TYPE_ANY

        if isinstance(expr, MemberAccess):
            target_t = self.check_expression(expr.target)
            prop = expr.member.lower()
            if prop == "largo":
                return TYPE_ENTERO
            if prop == "findearchivo":
                return TYPE_BOOLEANO
            return TYPE_ANY

        if isinstance(expr, FunctionCall):
            # Llamada a método: obj.metodo(...)
            if isinstance(expr.callee, MemberAccess):
                m_name = expr.callee.member.upper()
                if m_name == "LEER_LINEA":
                    return TYPE_ANY
                if m_name in ("ESCRIBIR_LINEA", "CERRAR_ARCHIVO"):
                    return TYPE_VOID
                return TYPE_ANY

            if isinstance(expr.callee, Variable):
                fn_name = expr.callee.name
                if fn_name == "ABRIR_ARCHIVO":
                    return TYPE_ARCHIVO
                if fn_name in ("ESPAR", "ESIMPAR"):
                    return TYPE_BOOLEANO
                if fn_name == "MOD":
                    return TYPE_ENTERO

                if fn_name in self.functions:
                    fn_def = self.functions[fn_name]
                    # Verificar aridad
                    if len(expr.args) != len(fn_def.params):
                        msg = f"La función '{fn_name}' espera {len(fn_def.params)} argumentos, se pasaron {len(expr.args)}"
                        if self.lenient:
                            self.warnings.append(f"Advertencia (L{expr.line}): {msg}")
                        else:
                            raise PseudoTypeError(msg, line=expr.line, column=expr.column, source=self.source)

                    # Verificar tipos de argumentos
                    for arg_expr, param in zip(expr.args, fn_def.params):
                        arg_t = self.check_expression(arg_expr)
                        if not param.data_type.is_assignable_from(arg_t) and arg_t != TYPE_ANY:
                            msg = f"En llamada a '{fn_name}', argumento de tipo {arg_t} no es compatible con parámetro '{param.name}' ({param.data_type})"
                            if self.lenient:
                                self.warnings.append(f"Advertencia (L{arg_expr.line}): {msg}")
                            else:
                                raise PseudoTypeError(msg, line=arg_expr.line, column=arg_expr.column, source=self.source)
                    return fn_def.return_type

        return TYPE_ANY
