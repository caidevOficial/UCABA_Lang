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
Definición del Árbol de Sintaxis Abstracta (AST) para el lenguaje de pseudocódigo.
Cada nodo almacena su posición en el código fuente (línea y columna) para reportar diagnósticos.
"""

from typing import List, Optional, Any, Tuple
from pseudocode.types_system import DataType


class ASTNode:
    def __init__(self, line: int = 1, column: int = 1):
        self.line = line
        self.column = column


# ==========================================
# EXPRESIONES
# ==========================================

class Expression(ASTNode):
    pass


class Literal(Expression):
    def __init__(self, value: Any, data_type: DataType, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.value = value
        self.data_type = data_type

    def __repr__(self) -> str:
        return f"Literal({self.value!r}, {self.data_type})"


class ArrayLiteral(Expression):
    def __init__(self, elements: List[Expression], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.elements = elements

    def __repr__(self) -> str:
        return f"ArrayLiteral({self.elements!r})"


class Variable(Expression):
    def __init__(self, name: str, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.name = name

    def __repr__(self) -> str:
        return f"Variable({self.name})"


class BinaryOp(Expression):
    def __init__(self, left: Expression, op: str, right: Expression, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self) -> str:
        return f"BinaryOp({self.left} {self.op} {self.right})"


class UnaryOp(Expression):
    def __init__(self, op: str, operand: Expression, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.op = op
        self.operand = operand

    def __repr__(self) -> str:
        return f"UnaryOp({self.op} {self.operand})"


class IndexAccess(Expression):
    def __init__(self, target: Expression, indices: List[Expression], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.target = target
        self.indices = indices

    def __repr__(self) -> str:
        return f"IndexAccess({self.target}{self.indices})"


class MemberAccess(Expression):
    def __init__(self, target: Expression, member: str, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.target = target
        self.member = member

    def __repr__(self) -> str:
        return f"MemberAccess({self.target}.{self.member})"


class FunctionCall(Expression):
    def __init__(self, callee: Expression, args: List[Expression], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.callee = callee
        self.args = args

    def __repr__(self) -> str:
        return f"FunctionCall({self.callee}({self.args}))"


# ==========================================
# SENTENCIAS (STATEMENTS)
# ==========================================

class Statement(ASTNode):
    pass


class VarDeclaration(Statement):
    def __init__(self, name: str, data_type: DataType,
                 size_exprs: Optional[List[Expression]] = None,
                 initializer: Optional[Expression] = None,
                 line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.name = name
        self.data_type = data_type
        self.size_exprs = size_exprs or []
        self.initializer = initializer

    def __repr__(self) -> str:
        return f"VarDeclaration({self.data_type} {self.name} sizes={self.size_exprs} = {self.initializer})"


class Assignment(Statement):
    def __init__(self, target: Expression, op: str, value: Expression, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.target = target
        self.op = op
        self.value = value

    def __repr__(self) -> str:
        return f"Assignment({self.target} {self.op} {self.value})"


class IncrementStatement(Statement):
    def __init__(self, target: Expression, is_increment: bool, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.target = target
        self.is_increment = is_increment

    def __repr__(self) -> str:
        op = "++" if self.is_increment else "--"
        return f"IncrementStatement({self.target}{op})"


class IfStatement(Statement):
    def __init__(self, condition: Expression, then_branch: List[Statement],
                 elif_branches: Optional[List[Tuple[Expression, List[Statement]]]] = None,
                 else_branch: Optional[List[Statement]] = None,
                 line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.condition = condition
        self.then_branch = then_branch
        self.elif_branches = elif_branches or []
        self.else_branch = else_branch

    def __repr__(self) -> str:
        return f"IfStatement({self.condition}, then={len(self.then_branch)}, elifs={len(self.elif_branches)}, else={bool(self.else_branch)})"


class WhileStatement(Statement):
    def __init__(self, condition: Expression, body: List[Statement], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.condition = condition
        self.body = body

    def __repr__(self) -> str:
        return f"WhileStatement({self.condition}, body={len(self.body)})"


class DoWhileStatement(Statement):
    def __init__(self, body: List[Statement], condition: Expression, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.body = body
        self.condition = condition

    def __repr__(self) -> str:
        return f"DoWhileStatement(body={len(self.body)}, {self.condition})"


class ForStatement(Statement):
    def __init__(self, init: Optional[Statement], condition: Optional[Expression],
                 step: Optional[Statement], body: List[Statement], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.init = init
        self.condition = condition
        self.step = step
        self.body = body

    def __repr__(self) -> str:
        return f"ForStatement(init={self.init}, cond={self.condition}, step={self.step}, body={len(self.body)})"


class ReturnStatement(Statement):
    def __init__(self, value: Optional[Expression] = None, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.value = value

    def __repr__(self) -> str:
        return f"ReturnStatement({self.value})"


class PrintStatement(Statement):
    def __init__(self, value: Expression, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.value = value

    def __repr__(self) -> str:
        return f"PrintStatement({self.value})"


class ExpressionStatement(Statement):
    def __init__(self, expr: Expression, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.expr = expr

    def __repr__(self) -> str:
        return f"ExpressionStatement({self.expr})"


class Parameter:
    def __init__(self, name: str, data_type: DataType, line: int = 1, column: int = 1):
        self.name = name
        self.data_type = data_type
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        return f"{self.name}: {self.data_type}"


class FunctionDef(ASTNode):
    def __init__(self, name: str, params: List[Parameter], return_type: DataType,
                 body: List[Statement], is_procedure: bool = False, line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.name = name
        self.params = params
        self.return_type = return_type
        self.body = body
        self.is_procedure = is_procedure

    def __repr__(self) -> str:
        kind = "Procedimiento" if self.is_procedure else "Funcion"
        return f"{kind} {self.name}({self.params}): {self.return_type} [{len(self.body)} stmts]"


class Program(ASTNode):
    def __init__(self, functions: List[FunctionDef], statements: List[Statement], line: int = 1, column: int = 1):
        super().__init__(line, column)
        self.functions = functions
        self.statements = statements

    def __repr__(self) -> str:
        return f"Program(funcs={len(self.functions)}, top_stmts={len(self.statements)})"
