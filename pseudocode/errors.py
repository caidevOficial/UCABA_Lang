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
Sistema unificado de errores y diagnóstico para el lenguaje de pseudocódigo.
Proporciona ubicación precisa (línea, columna) y visualización del código fuente.
"""

from typing import Optional


class PseudocodeError(Exception):
    def __init__(self, message: str, line: int = 1, column: int = 1, source: Optional[str] = None, length: int = 1):
        super().__init__(message)
        self.message = message
        self.line = line
        self.column = column
        self.source = source
        self.length = max(1, length)

    def format_diagnostic(self, filename: str = "<código>") -> str:
        header = f"{self.__class__.__name__} en {filename}:{self.line}:{self.column}"
        separator = "=" * len(header)
        lines = [header, separator, f"Mensaje: {self.message}"]
        if self.source:
            source_lines = self.source.splitlines()
            if 1 <= self.line <= len(source_lines):
                error_line = source_lines[self.line - 1]
                lines.append("")
                lines.append(f"  {self.line:4d} | {error_line}")
                pointer = " " * (self.column - 1) + "^" * self.length
                lines.append(f"       | {pointer}")
        lines.append(separator)
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.format_diagnostic()


class LexerError(PseudocodeError):
    """Error durante el análisis léxico."""
    pass


class ParseError(PseudocodeError):
    """Error durante el análisis sintáctico."""
    pass


class TypeError(PseudocodeError):
    """Error durante el chequeo estático o dinámico de tipos."""
    pass


class RuntimeError(PseudocodeError):
    """Error durante la ejecución del programa."""
    pass
