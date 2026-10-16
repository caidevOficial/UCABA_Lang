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

__version__ = "1.9.0"
__author__ = "Facu Falcone <a.facundo.falcone@gmail.com>"

import sys
import os

# Incrementar límite de recursión para permitir algoritmos recursivos profundos sin desbordamiento
try:
    sys.setrecursionlimit(max(sys.getrecursionlimit(), 50000))
except Exception:
    pass

_BANNER_PRINTED = False


def _enable_windows_ansi():
    """Habilita el procesamiento de secuencias ANSI en la consola de Windows si es necesario."""
    if sys.platform == "win32":
        try:
            import ctypes
            kernel32 = ctypes.windll.kernel32
            hStdOut = kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if kernel32.GetConsoleMode(hStdOut, ctypes.byref(mode)):
                kernel32.SetConsoleMode(hStdOut, mode.value | 0x0004)
        except Exception:
            pass


def print_welcome_banner(force: bool = False):
    """Muestra el mensaje institucional de la comunidad UCABA con el color fucsia oficial."""
    global _BANNER_PRINTED
    if _BANNER_PRINTED and not force:
        return

    # Evitar imprimir en modo lsp-check (VS Code espera JSON puro) o si se silencia explícitamente
    if os.environ.get("UCABA_HIDE_BANNER") == "1" or os.environ.get("UCABA_HIDE_SUPPORT_PROMPT") == "1":
        return
    all_args = list(sys.argv) + list(getattr(sys, "orig_argv", []))
    if any("lsp-check" in str(arg).lower() or "lsp_check" in str(arg).lower() for arg in all_args):
        return

    _BANNER_PRINTED = True
    _enable_windows_ansi()

    # Color fucsia oficial de UCABA (#d946ef / #c02694)
    if os.environ.get("NO_COLOR") or os.environ.get("UCABA_NO_COLOR"):
        color_fucsia = ""
        color_reset = ""
    else:
        color_fucsia = "\033[95m\033[1;38;2;217;70;239m"
        color_reset = "\033[0m"

    print(f"{color_fucsia}UCABA (v{__version__})")
    print(f"Hello from the UCABA community. [Dev: Facu Falcone]{color_reset}")


def saludo():
    """Función auxiliar para mostrar el saludo institucional de la comunidad UCABA."""
    print_welcome_banner(force=True)


from pseudocode.lexer import Lexer
from pseudocode.parser import Parser
from pseudocode.type_checker import TypeChecker
from pseudocode.interpreter import Interpreter
from pseudocode.errors import PseudocodeError
from pseudocode.updater import register_update_notice_on_exit

# Ejecutar el saludo una única vez al cargar el paquete UCABA
print_welcome_banner()

# Iniciar comprobación en segundo plano y registrar aviso de versión al salir (estilo pip)
register_update_notice_on_exit(__version__)


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
