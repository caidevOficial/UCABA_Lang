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
Módulo de diagnóstico y análisis en tiempo real para Language Server / VS Code / Antigravity.
Analiza código fuente desde stdin o argumentos y devuelve diagnósticos en formato JSON.
"""

import sys
import json
from typing import List, Dict, Any
from pseudocode.lexer import Lexer
from pseudocode.parser import Parser
from pseudocode.type_checker import TypeChecker
from pseudocode.errors import LexerError, ParseError, TypeError as PseudoTypeError, PseudocodeError


def check_source_for_diagnostics(source: str, filename: str = "<código>", lenient: bool = True) -> List[Dict[str, Any]]:
    diagnostics: List[Dict[str, Any]] = []

    # 1. Análisis Léxico
    tokens = []
    try:
        lexer = Lexer(source, filename)
        tokens = lexer.tokenize()
    except LexerError as e:
        diagnostics.append({
            "line": max(0, e.line - 1),
            "character": max(0, e.column - 1),
            "length": getattr(e, "length", 1),
            "message": e.message,
            "severity": "error",
            "source": "ucaba-lexer"
        })
        return diagnostics

    # 2. Análisis Sintáctico (Parser)
    program = None
    try:
        parser = Parser(tokens, source, filename)
        program = parser.parse()
    except ParseError as e:
        diagnostics.append({
            "line": max(0, e.line - 1),
            "character": max(0, e.column - 1),
            "length": getattr(e, "length", 1),
            "message": e.message,
            "severity": "error",
            "source": "ucaba-parser"
        })
        return diagnostics

    # 3. Análisis Semántico y Chequeo Estático de Tipos
    if program:
        type_checker = TypeChecker(source, filename, lenient=lenient)
        try:
            type_checker.check(program)
        except PseudoTypeError as e:
            diagnostics.append({
                "line": max(0, e.line - 1),
                "character": max(0, e.column - 1),
                "length": getattr(e, "length", 1),
                "message": e.message,
                "severity": "error",
                "source": "ucaba-typechecker"
            })
        except Exception as e:
            diagnostics.append({
                "line": 0,
                "character": 0,
                "length": 1,
                "message": str(e),
                "severity": "error",
                "source": "ucaba-checker"
            })

        # Incluir advertencias si las hubo
        import re
        for warn in type_checker.warnings:
            w_line = 0
            m = re.search(r'l[ií]nea\s+(\d+)', warn, re.IGNORECASE)
            if m:
                w_line = max(0, int(m.group(1)) - 1)
            diagnostics.append({
                "line": w_line,
                "character": 0,
                "length": 1,
                "message": warn,
                "severity": "warning",
                "source": "ucaba-warning"
            })

    return diagnostics


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stdin, "reconfigure"):
        sys.stdin.reconfigure(encoding="utf-8")

    lenient = "--lenient" in sys.argv or "-l" in sys.argv
    # Si no se especifica --strict, por defecto en editor podemos usar lenient=True
    if "--strict" in sys.argv:
        lenient = False
    else:
        lenient = True

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if args:
        filename = args[0]
        try:
            with open(filename, "r", encoding="utf-8") as f:
                source = f.read()
        except Exception as e:
            json.dump({"diagnostics": [{"line": 0, "character": 0, "length": 1, "message": f"Error leyendo {filename}: {e}", "severity": "error", "source": "ucaba"}]}, sys.stdout)
            return
    else:
        filename = "<editor>"
        source = sys.stdin.read()

    diags = check_source_for_diagnostics(source, filename=filename, lenient=lenient)
    json.dump({"diagnostics": diags}, sys.stdout, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    main()
