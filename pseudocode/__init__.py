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
Paquete oficial del Lenguaje de Programación UCABA.
"""

import os
from pseudocode.lexer import Lexer
from pseudocode.parser import Parser
from pseudocode.type_checker import TypeChecker
from pseudocode.interpreter import Interpreter
from pseudocode.errors import PseudocodeError


def resolve_ucaba_path(filepath: str) -> str:
    """Valida y resuelve que el archivo de código fuente tenga la extensión obligatoria .ucaba."""
    if not filepath.endswith(".ucaba"):
        # Si se pasó el nombre sin extensión pero existe con .ucaba, resolverlo
        candidate = filepath + ".ucaba"
        if os.path.exists(candidate):
            return candidate
        raise PseudocodeError(
            f"Extensión no válida: '{filepath}'. El lenguaje UCABA solo admite archivos de código con extensión '.ucaba'."
        )
    return filepath


def run_code(source: str, filename: str = "<código>", output_collector=None, lenient: bool = False):
    """Ejecuta una cadena de pseudocódigo realizando análisis léxico, sintáctico, tipado y evaluación."""
    lexer = Lexer(source, filename)
    tokens = lexer.tokenize()

    parser = Parser(tokens, source, filename, lenient=lenient)
    program = parser.parse()

    type_checker = TypeChecker(source, filename, lenient=lenient)
    type_checker.check(program)

    interpreter = Interpreter(source, filename, output_collector=output_collector)
    interpreter.run(program)
    return interpreter


def run_file(filepath: str, output_collector=None, lenient: bool = False):
    """Ejecuta un archivo de código fuente de pseudocódigo (.ucaba)."""
    valid_path = resolve_ucaba_path(filepath)
    with open(valid_path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()
    return run_code(source, valid_path, output_collector=output_collector, lenient=lenient)


def check_file(filepath: str, lenient: bool = False):
    """Realiza la verificación estática de sintaxis y tipos de un archivo .ucaba sin ejecutarlo."""
    valid_path = resolve_ucaba_path(filepath)
    with open(valid_path, "r", encoding="utf-8", errors="replace") as f:
        source = f.read()

    lexer = Lexer(source, valid_path)
    tokens = lexer.tokenize()

    parser = Parser(tokens, source, valid_path, lenient=lenient)
    program = parser.parse()

    type_checker = TypeChecker(source, valid_path, lenient=lenient)
    type_checker.check(program)
    return parser.warnings + type_checker.warnings
