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
Intérprete AST (Tree-Walk Interpreter) para el lenguaje de pseudocódigo.
Ejecuta de manera segura y tipada el AST analizado, gestionando entornos de ejecución y llamadas.
"""

from typing import Any, Dict, List, Optional
from pseudocode.types_system import (
    DataType, VectorType, MatrixType,
    TYPE_ENTERO, TYPE_FLOTANTE, TYPE_REAL, TYPE_CADENA,
    TYPE_CARACTER, TYPE_BOOLEANO, TYPE_ARCHIVO, TYPE_VOID,
    validate_runtime_value
)
from pseudocode.ast_nodes import (
    Program, FunctionDef, Statement, Expression,
    VarDeclaration, Assignment, IncrementStatement,
    IfStatement, WhileStatement, DoWhileStatement, ForStatement,
    ReturnStatement, PrintStatement, ExpressionStatement,
    Literal, ArrayLiteral, Variable, BinaryOp, UnaryOp,
    IndexAccess, MemberAccess, FunctionCall
)
from pseudocode.builtins import (
    ArchivoHandle, builtin_abrir_archivo, builtin_es_par, builtin_es_impar, builtin_mod,
    stringify_value
)
from pseudocode.errors import RuntimeError as PseudoRuntimeError


class ReturnSignal(Exception):
    """Señal interna de control de flujo para sentencias RETORNO."""
    def __init__(self, value: Any):
        self.value = value


class Environment:
    def __init__(self, parent: Optional['Environment'] = None, name: str = "global"):
        self.parent = parent
        self.name = name
        self.values: Dict[str, Any] = {}
        self.types: Dict[str, DataType] = {}

    def define(self, name: str, value: Any, data_type: DataType):
        self.values[name] = validate_runtime_value(value, data_type)
        self.types[name] = data_type

    def get(self, name: str, line: int = 1, column: int = 1, source: str = "") -> Any:
        if name in self.values:
            return self.values[name]
        if self.parent:
            return self.parent.get(name, line, column, source)
        raise PseudoRuntimeError(f"Variable no inicializada o no encontrada: '{name}'",
                                 line=line, column=column, source=source)

    def set(self, name: str, value: Any, line: int = 1, column: int = 1, source: str = ""):
        if name in self.values:
            target_type = self.types[name]
            self.values[name] = validate_runtime_value(value, target_type)
            return
        if self.parent:
            self.parent.set(name, value, line, column, source)
            return
        raise PseudoRuntimeError(f"Variable no declarada: '{name}'",
                                 line=line, column=column, source=source)


class Interpreter:
    def __init__(self, source: str = "", filename: str = "<código>", output_collector: Optional[List[str]] = None):
        self.source = source
        self.filename = filename
        self.global_env = Environment(name="global")
        self.current_env = self.global_env
        self.functions: Dict[str, FunctionDef] = {}
        self.output_collector = output_collector  # Para capturar salidas en tests si es provisto

        self._setup_builtins()

    def _setup_builtins(self):
        # Builtin functions
        pass

    def run(self, program: Program):
        # 1. Registrar funciones
        for func in program.functions:
            self.functions[func.name] = func

        # 2. Ejecutar sentencias de nivel global
        for stmt in program.statements:
            self.execute_statement(stmt)

    # ==========================================
    # EJECUCIÓN DE SENTENCIAS
    # ==========================================

    def execute_statement(self, stmt: Statement):
        if isinstance(stmt, VarDeclaration):
            val = None
            # Si tiene expresión de inicialización
            if stmt.initializer:
                val = self.evaluate_expression(stmt.initializer)
                if isinstance(stmt.data_type, VectorType) and not isinstance(val, list):
                    val = [val]
            elif stmt.size_exprs:
                # Creación de vectores o matrices vacíos con tamaño dado
                sizes = [int(self.evaluate_expression(s)) for s in stmt.size_exprs]
                val = self._create_empty_array(stmt.data_type, sizes)
            else:
                # Valor por defecto
                val = self._default_for_type(stmt.data_type)

            self.current_env.define(stmt.name, val, stmt.data_type)

        elif isinstance(stmt, Assignment):
            val = self.evaluate_expression(stmt.value)
            self._assign_target(stmt.target, stmt.op, val)

        elif isinstance(stmt, IncrementStatement):
            delta = 1 if stmt.is_increment else -1
            old_val = self.evaluate_expression(stmt.target)
            new_val = old_val + delta
            self._assign_target(stmt.target, "=", new_val)

        elif isinstance(stmt, IfStatement):
            cond_val = self.evaluate_expression(stmt.condition)
            if self._is_truthy(cond_val):
                for s in stmt.then_branch:
                    self.execute_statement(s)
                return

            # Evaluar ramas SINO SI
            branch_taken = False
            for elif_cond, elif_stmts in stmt.elif_branches:
                if self._is_truthy(self.evaluate_expression(elif_cond)):
                    for s in elif_stmts:
                        self.execute_statement(s)
                    branch_taken = True
                    break

            if not branch_taken and stmt.else_branch:
                for s in stmt.else_branch:
                    self.execute_statement(s)

        elif isinstance(stmt, WhileStatement):
            # Detección y notificación para objetos ARCHIVO dentro de MIENTRAS
            active_file = self._find_archivo_in_expr(stmt.condition)

            while self._is_truthy(self.evaluate_expression(stmt.condition)):
                for s in stmt.body:
                    self.execute_statement(s)
                if active_file:
                    active_file.notify_loop_step()

        elif isinstance(stmt, DoWhileStatement):
            active_file = self._find_archivo_in_expr(stmt.condition)
            while True:
                for s in stmt.body:
                    self.execute_statement(s)
                if active_file:
                    active_file.notify_loop_step()
                if not self._is_truthy(self.evaluate_expression(stmt.condition)):
                    break

        elif isinstance(stmt, ForStatement):
            for_env = Environment(parent=self.current_env, name="for")
            prev_env = self.current_env
            self.current_env = for_env
            try:
                if stmt.init:
                    self.execute_statement(stmt.init)

                while True:
                    if stmt.condition:
                        cond = self.evaluate_expression(stmt.condition)
                        if not self._is_truthy(cond):
                            break
                    for s in stmt.body:
                        self.execute_statement(s)
                    if stmt.step:
                        self.execute_statement(stmt.step)
            finally:
                self.current_env = prev_env

        elif isinstance(stmt, ReturnStatement):
            ret_val = None
            if stmt.value:
                ret_val = self.evaluate_expression(stmt.value)
            raise ReturnSignal(ret_val)

        elif isinstance(stmt, PrintStatement):
            val = self.evaluate_expression(stmt.value)
            text = stringify_value(val)
            if self.output_collector is not None:
                self.output_collector.append(text)
            print(text)

        elif isinstance(stmt, ExpressionStatement):
            self.evaluate_expression(stmt.expr)

    def _assign_target(self, target: Expression, op: str, value: Any):
        if isinstance(target, Variable):
            if op == "=":
                self.current_env.set(target.name, value, target.line, target.column, self.source)
            elif op == "+=":
                cur = self.current_env.get(target.name, target.line, target.column, self.source)
                self.current_env.set(target.name, cur + value, target.line, target.column, self.source)
            elif op == "-=":
                cur = self.current_env.get(target.name, target.line, target.column, self.source)
                self.current_env.set(target.name, cur - value, target.line, target.column, self.source)

        elif isinstance(target, IndexAccess):
            container = self.evaluate_expression(target.target)
            indices = [int(self.evaluate_expression(i)) for i in target.indices]

            # Navegar hasta el penúltimo nivel
            curr = container
            for idx in indices[:-1]:
                if not isinstance(curr, list) or idx < 0 or idx >= len(curr):
                    raise PseudoRuntimeError(f"Índice fuera de rango: {idx}",
                                             line=target.line, column=target.column, source=self.source)
                curr = curr[idx]

            last_idx = indices[-1]
            if not isinstance(curr, list) or last_idx < 0 or last_idx >= len(curr):
                raise PseudoRuntimeError(f"Índice fuera de rango: {last_idx}",
                                         line=target.line, column=target.column, source=self.source)

            # Si el valor viene de LEER_LINEA o cadena y el contenedor espera números
            final_val = value
            if isinstance(value, str) and value.strip():
                try:
                    if "." in value:
                        final_val = float(value.strip())
                    elif value.strip().lstrip('-+').isdigit():
                        final_val = int(value.strip())
                except ValueError:
                    pass

            if last_idx < len(curr) and curr[last_idx] is not None:
                if isinstance(curr[last_idx], float) and isinstance(final_val, (int, float)):
                    final_val = float(final_val)
                elif isinstance(curr[last_idx], int) and isinstance(final_val, float):
                    final_val = int(final_val)
                elif isinstance(curr[last_idx], str) and not isinstance(final_val, str):
                    final_val = str(final_val)

            if op == "=":
                curr[last_idx] = final_val
            elif op == "+=":
                curr[last_idx] += final_val
            elif op == "-=":
                curr[last_idx] -= final_val

    def _create_empty_array(self, data_type: DataType, sizes: List[int]) -> List[Any]:
        if not sizes:
            return []
        if len(sizes) == 1:
            base_t = data_type.element_type if isinstance(data_type, VectorType) else data_type
            return [self._default_for_type(base_t) for _ in range(sizes[0])]
        elif len(sizes) == 2:
            base_t = data_type.element_type if isinstance(data_type, MatrixType) else data_type
            return [
                [self._default_for_type(base_t) for _ in range(sizes[1])]
                for _ in range(sizes[0])
            ]
        return []

    def _default_for_type(self, data_type: DataType) -> Any:
        if data_type == TYPE_ENTERO:
            return 0
        if data_type in (TYPE_FLOTANTE, TYPE_REAL):
            return 0.0
        if data_type == TYPE_CADENA:
            return ""
        if data_type == TYPE_CARACTER:
            return " "
        if data_type == TYPE_BOOLEANO:
            return False
        if isinstance(data_type, (VectorType, MatrixType)):
            return []
        return None

    def _is_truthy(self, val: Any) -> bool:
        if isinstance(val, bool):
            return val
        if val is None:
            return False
        if isinstance(val, (int, float)):
            return val != 0
        if isinstance(val, (str, list)):
            return len(val) > 0
        return True

    def _find_archivo_in_expr(self, expr: Expression) -> Optional[ArchivoHandle]:
        """Busca si la expresión hace referencia a un objeto ArchivoHandle."""
        if isinstance(expr, MemberAccess):
            target_val = self.evaluate_expression(expr.target)
            if isinstance(target_val, ArchivoHandle):
                return target_val
        if isinstance(expr, UnaryOp):
            return self._find_archivo_in_expr(expr.operand)
        if isinstance(expr, BinaryOp):
            return self._find_archivo_in_expr(expr.left) or self._find_archivo_in_expr(expr.right)
        return None

    # ==========================================
    # EVALUACIÓN DE EXPRESIONES
    # ==========================================

    def evaluate_expression(self, expr: Expression) -> Any:
        if isinstance(expr, Literal):
            return expr.value

        if isinstance(expr, ArrayLiteral):
            return [self.evaluate_expression(e) for e in expr.elements]

        if isinstance(expr, Variable):
            return self.current_env.get(expr.name, expr.line, expr.column, self.source)

        if isinstance(expr, BinaryOp):
            left = self.evaluate_expression(expr.left)
            right = self.evaluate_expression(expr.right)

            op = expr.op
            if op == "+":
                # Si alguno es cadena, concatenación de texto
                if isinstance(left, str) or isinstance(right, str):
                    return stringify_value(left) + stringify_value(right)
                # Concatenación de vectores (ej: vec1 + vec2)
                if isinstance(left, list) and isinstance(right, list):
                    return list(left) + list(right)
                if isinstance(left, list):
                    return list(left) + [right]
                if isinstance(right, list):
                    return [left] + list(right)
                return left + right

            if op == "-":
                return left - right
            if op == "*":
                return left * right
            if op == "/":
                if right == 0:
                    raise PseudoRuntimeError("División por cero.", line=expr.line, column=expr.column, source=self.source)
                return left / right
            if op in ("%", "MOD"):
                if right == 0:
                    raise PseudoRuntimeError("Módulo por cero.", line=expr.line, column=expr.column, source=self.source)
                return int(left) % int(right)

            # Comparaciones
            if op == "==":
                return left == right
            if op == "!=":
                return left != right
            if op == "<":
                return left < right
            if op == "<=":
                return left <= right
            if op == ">":
                return left > right
            if op == ">=":
                return left >= right

            # Lógicos
            if op in ("Y", "&&"):
                return self._is_truthy(left) and self._is_truthy(right)
            if op in ("O", "||"):
                return self._is_truthy(left) or self._is_truthy(right)

        if isinstance(expr, UnaryOp):
            val = self.evaluate_expression(expr.operand)
            if expr.op in ("NO", "!"):
                return not self._is_truthy(val)
            if expr.op == "-":
                return -val
            if expr.op == "+":
                return +val

        if isinstance(expr, IndexAccess):
            target = self.evaluate_expression(expr.target)
            curr = target
            for idx_expr in expr.indices:
                idx = int(self.evaluate_expression(idx_expr))
                if not isinstance(curr, (list, str)) or idx < 0 or idx >= len(curr):
                    raise PseudoRuntimeError(
                        f"Índice fuera de límites: {idx} (longitud: {len(curr) if isinstance(curr, (list, str)) else 0})",
                        line=idx_expr.line, column=idx_expr.column, source=self.source
                    )
                curr = curr[idx]
            return curr

        if isinstance(expr, MemberAccess):
            target = self.evaluate_expression(expr.target)
            member = expr.member.lower()

            # Propiedad .largo
            if member == "largo":
                if isinstance(target, (list, str)):
                    return len(target)
                raise PseudoRuntimeError(f"Tipo '{type(target).__name__}' no tiene propiedad '.largo'",
                                         line=expr.line, column=expr.column, source=self.source)

            # Propiedad .findearchivo en ARCHIVO
            if isinstance(target, ArchivoHandle) and member == "findearchivo":
                return target.findearchivo

            raise PseudoRuntimeError(f"Miembro '{expr.member}' no encontrado en el objeto.",
                                     line=expr.line, column=expr.column, source=self.source)

        if isinstance(expr, FunctionCall):
            # 1. Llamada a método: objeto.metodo(...)
            if isinstance(expr.callee, MemberAccess):
                target = self.evaluate_expression(expr.callee.target)
                method_name = expr.callee.member.upper()
                evaluated_args = [self.evaluate_expression(a) for a in expr.args]

                if isinstance(target, ArchivoHandle):
                    if method_name == "LEER_LINEA":
                        return target.LEER_LINEA()
                    elif method_name == "ESCRIBIR_LINEA":
                        return target.ESCRIBIR_LINEA(evaluated_args[0] if evaluated_args else "")
                    elif method_name == "CERRAR_ARCHIVO":
                        return target.CERRAR_ARCHIVO()

                raise PseudoRuntimeError(f"Método '{method_name}' no soportado en objeto de tipo {type(target).__name__}",
                                         line=expr.line, column=expr.column, source=self.source)

            # 2. Llamada a función global o builtin
            if isinstance(expr.callee, Variable):
                fn_name = expr.callee.name.upper()
                evaluated_args = [self.evaluate_expression(a) for a in expr.args]

                # Builtins
                if fn_name == "ABRIR_ARCHIVO":
                    return builtin_abrir_archivo(str(evaluated_args[0]), str(evaluated_args[1]))
                if fn_name == "ESPAR":
                    return builtin_es_par(evaluated_args[0])
                if fn_name == "ESIMPAR":
                    return builtin_es_impar(evaluated_args[0])
                if fn_name == "MOD":
                    return builtin_mod(evaluated_args[0], evaluated_args[1])
                if fn_name == "IMPRIMIR":
                    text = " ".join(stringify_value(x) for x in evaluated_args)
                    if self.output_collector is not None:
                        self.output_collector.append(text)
                    print(text)
                    return None

                # Funciones definidas por el usuario
                user_fn = None
                for fname, fdef in self.functions.items():
                    if fname.upper() == fn_name:
                        user_fn = fdef
                        break

                if user_fn:
                    return self.call_function(user_fn, evaluated_args, expr.line, expr.column)

                raise PseudoRuntimeError(f"Función o procedimiento no encontrado: '{expr.callee.name}'",
                                         line=expr.line, column=expr.column, source=self.source)

        return None

    def call_function(self, func: FunctionDef, args: List[Any], line: int, column: int) -> Any:
        if len(args) != len(func.params):
            raise PseudoRuntimeError(
                f"La función '{func.name}' espera {len(func.params)} argumentos, se recibieron {len(args)}",
                line=line, column=column, source=self.source
            )

        fn_env = Environment(parent=self.global_env, name=func.name)

        # Vincular parámetros
        for param, arg_val in zip(func.params, args):
            fn_env.define(param.name, arg_val, param.data_type)

        prev_env = self.current_env
        self.current_env = fn_env
        try:
            for stmt in func.body:
                self.execute_statement(stmt)
        except ReturnSignal as sig:
            if func.return_type != TYPE_VOID:
                return validate_runtime_value(sig.value, func.return_type)
            return None
        finally:
            self.current_env = prev_env

        return None
