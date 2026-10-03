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
Interfaz de línea de comandos (CLI) para ejecutar y validar programas de pseudocódigo (.ucaba).
"""

import sys
import os
import argparse
import time

# Asegurar que el paquete pseudocode sea importable si se ejecuta cli.py directamente
_base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _base_dir not in sys.path:
    sys.path.insert(0, _base_dir)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from pseudocode import run_file, check_file, resolve_ucaba_path
from pseudocode.lexer import Lexer
from pseudocode.parser import Parser
from pseudocode.errors import PseudocodeError


def main():
    parser = argparse.ArgumentParser(
        prog="ucaba",
        description="UCABA: Lenguaje de programación fuertemente tipado (archivos .ucaba)."
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version="UCABA 1.2.0 - Copyright (C) 2026 Facu Falcone <a.facundo.falcone@gmail.com> (GNU GPLv3)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Comando 'run'
    run_parser = subparsers.add_parser("run", help="Ejecuta un archivo UCABA (.ucaba)")
    run_parser.add_argument("file", help="Ruta al archivo .ucaba")
    run_parser.add_argument("--lenient", "-l", action="store_true", help="Modo permisivo para pseudocódigo informal")
    run_parser.add_argument("--time", action="store_true", help="Muestra el tiempo de ejecución")

    # Comando 'check'
    check_parser = subparsers.add_parser("check", help="Verifica tipos y sintaxis sin ejecutar")
    check_parser.add_argument("file", help="Ruta al archivo .ucaba a verificar")
    check_parser.add_argument("--lenient", "-l", action="store_true", help="Modo permisivo para pseudocódigo informal")

    # Comando 'tokens'
    tokens_parser = subparsers.add_parser("tokens", help="Muestra los tokens léxicos generados")
    tokens_parser.add_argument("file", help="Ruta al archivo .ucaba")

    # Comando 'lsp-check'
    lsp_parser = subparsers.add_parser("lsp-check", help="Verificación diagnóstica en formato JSON para VS Code / IDE")
    lsp_parser.add_argument("file", nargs="?", default=None, help="Ruta al archivo .ucaba (o stdin si se omite)")
    lsp_parser.add_argument("--lenient", "-l", action="store_true", default=True, help="Modo permisivo para pseudocódigo informal")
    lsp_parser.add_argument("--strict", action="store_true", help="Modo estricto")

    # Si se pasa archivo directamente sin comando, por defecto 'run'
    if len(sys.argv) > 1 and sys.argv[1] not in ("run", "check", "tokens", "lsp-check", "-h", "--help", "-v", "--version"):
        args = parser.parse_args(["run"] + sys.argv[1:])
    else:
        args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command == "lsp-check":
            from pseudocode.lsp_check import check_source_for_diagnostics
            import json
            lenient = not getattr(args, "strict", False)
            if getattr(args, "file", None):
                target_path = resolve_ucaba_path(args.file)
                with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                    source = f.read()
                diags = check_source_for_diagnostics(source, target_path, lenient=lenient)
            else:
                source = sys.stdin.read()
                diags = check_source_for_diagnostics(source, "<editor>", lenient=lenient)
            json.dump({"diagnostics": diags}, sys.stdout, indent=2, ensure_ascii=False)
            sys.exit(0)

        target_path = resolve_ucaba_path(args.file)

        if args.command == "tokens":
            with open(target_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            lexer = Lexer(content, target_path)
            tokens = lexer.tokenize()
            for t in tokens:
                print(f"[{t.line:3d}:{t.column:2d}] {t.type.name:<18} -> {t.value!r}")

        elif args.command == "check":
            COLOR_VERDE = "\033[32m"
            COLOR_CYAN = "\033[36m"
            COLOR_AMARILLO = "\033[33m"
            NO_COLOR = "\033[0m"
            print(f"{COLOR_CYAN}[CHECK] Verificando archivo: {target_path} (lenient={getattr(args, 'lenient', False)}) ...{NO_COLOR}")
            warnings = check_file(target_path, lenient=getattr(args, "lenient", False))
            if warnings:
                print(f"\n{COLOR_AMARILLO}[ADVERTENCIAS DETECTADAS ({len(warnings)})]:{NO_COLOR}")
                for w in warnings:
                    print(f"{COLOR_AMARILLO} - {w}{NO_COLOR}")
            print(f"{COLOR_VERDE}\n[OK] Analisis sintactico y chequeo estatico de tipos completado exitosamente.{NO_COLOR}")

        elif args.command == "run":
            COLOR_CYAN = "\033[36m"
            COLOR_AMARILLO = "\033[33m"
            NO_COLOR = "\033[0m"
            print(f"{COLOR_CYAN}[RUN] Ejecutando archivo: {target_path} (lenient={getattr(args, 'lenient', False)}) ...{NO_COLOR}")
            start_t = time.perf_counter()
            run_file(target_path, lenient=getattr(args, "lenient", False))
            elapsed = time.perf_counter() - start_t
            if getattr(args, "time", False):
                print(f"{COLOR_AMARILLO}\n[Tiempo total: {elapsed * 1000:.2f} ms]{NO_COLOR}")

    except PseudocodeError as e:
        COLOR_ROJO = "\033[31m"
        NO_COLOR = "\033[0m"
        print(f"{COLOR_ROJO}\n{e.format_diagnostic(args.file)}\n{NO_COLOR}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        COLOR_ROJO = "\033[31m"
        NO_COLOR = "\033[0m"
        print(f"{COLOR_ROJO}\nError inesperado: {e}\n{NO_COLOR}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
