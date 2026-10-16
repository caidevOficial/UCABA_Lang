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

from pseudocode import __version__, run_file, check_file, resolve_ucaba_path
from pseudocode.lexer import Lexer
from pseudocode.parser import Parser
from pseudocode.errors import PseudocodeError


def format_elapsed_time(elapsed_s: float, mode: str = "ms") -> str:
    """
    Formatea el tiempo de ejecución en milisegundos ('ms') o desglose completo ('full'/'completo').

    Ejemplos:
      - ms: '[Tiempo total: 37.61 ms]'
      - full: '[Tiempo total: 1 Hora, 15 Minutos, 30 Segundos, 45 Milisegundos]'
    """
    if mode == "ms":
        return f"[Tiempo total: {elapsed_s * 1000:.2f} ms]"

    total_ms = int(round(elapsed_s * 1000))
    hours = total_ms // 3600000
    remainder = total_ms % 3600000
    minutes = remainder // 60000
    remainder = remainder % 60000
    seconds = remainder // 1000
    milliseconds = remainder % 1000

    h_unit = "Hora" if hours == 1 else "Horas"
    m_unit = "Minuto" if minutes == 1 else "Minutos"
    s_unit = "Segundo" if seconds == 1 else "Segundos"
    ms_unit = "Milisegundo" if milliseconds == 1 else "Milisegundos"

    return f"[Tiempo total: {hours} {h_unit}, {minutes} {m_unit}, {seconds} {s_unit}, {milliseconds} {ms_unit}]"


def _normalize_cli_args(args_list: list) -> list:
    """
    Normaliza argumentos CLI para que opciones como '--time full' o '--time' se interpreten
    sin interferir con el argumento posicional obligatorio 'file'.
    """
    new_args = []
    i = 0
    valid_modes = {"ms", "full", "completo"}
    while i < len(args_list):
        arg = args_list[i]
        if arg == "--time":
            if i + 1 < len(args_list) and str(args_list[i + 1]).lower() in valid_modes:
                new_args.append(f"--time={str(args_list[i + 1]).lower()}")
                i += 2
                continue
            else:
                new_args.append("--time=ms")
                i += 1
                continue
        new_args.append(arg)
        i += 1
    return new_args


def main(cli_args=None):
    parser = argparse.ArgumentParser(
        prog="ucaba",
        description="UCABA: Lenguaje de programación fuertemente tipado (archivos .ucaba)."
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"UCABA {__version__} - Copyright (C) 2026 Facu Falcone <a.facundo.falcone@gmail.com> (GNU GPLv3)"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    # Comando 'run'
    run_parser = subparsers.add_parser("run", help="Ejecuta un archivo UCABA (.ucaba)")
    run_parser.add_argument("file", help="Ruta al archivo .ucaba")
    run_parser.add_argument("--lenient", "-l", action="store_true", help="Modo permisivo para pseudocódigo informal")
    run_parser.add_argument(
        "--time",
        nargs="?",
        const="ms",
        default=None,
        choices=["ms", "full", "completo"],
        help="Muestra el tiempo de ejecución. Modos: 'ms' (milisegundos, predeterminado), 'full' o 'completo' (horas, minutos, segundos y milisegundos)"
    )
    run_parser.add_argument(
        "--time-full",
        action="store_true",
        help="Muestra el tiempo de ejecución desglosado (ej: [Tiempo total: 1 Hora, 15 Minutos, 30 Segundos, 45 Milisegundos])"
    )

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

    # Comando 'update'
    update_parser = subparsers.add_parser("update", help="Comprueba y actualiza UCABA a la versión más reciente desde GitHub")
    update_parser.add_argument("--force", "-f", action="store_true", help="Fuerza la reinstalación aunque ya esté actualizado")
    update_parser.add_argument("--silent", "-s", action="store_true", help="Instalación en segundo plano desatendida")
    update_parser.add_argument("--check", "-c", action="store_true", help="Solo comprueba si existe una versión nueva sin instalar")

    subparsers.add_parser("upgrade", parents=[update_parser], add_help=False, help="Alias de 'update'")

    # Si se pasa archivo directamente sin comando, por defecto 'run'
    raw_argv = sys.argv[1:] if cli_args is None else list(cli_args)
    raw_argv = _normalize_cli_args(raw_argv)

    known_commands = ("run", "check", "tokens", "lsp-check", "update", "upgrade", "-h", "--help", "-v", "--version")
    if len(raw_argv) > 0 and raw_argv[0] not in known_commands:
        args = parser.parse_args(["run"] + raw_argv)
    else:
        args = parser.parse_args(raw_argv)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    try:
        if args.command in ("update", "upgrade"):
            from pseudocode.updater import run_interactive_update, check_for_update
            if getattr(args, "check", False):
                print(f"Comprobando versiones en GitHub ({__version__})...")
                upd = check_for_update(__version__, allow_network=True)
                if upd:
                    print(f"\n[AVISO] Hay una nueva versión de UCABA disponible: {__version__} -> {upd['latest_version']}")
                    print(f"Para actualizar ejecuta: ucaba update")
                else:
                    print(f"\n[OK] UCABA ya está en la versión más reciente (v{__version__}).")
                sys.exit(0)
            ret_code = run_interactive_update(__version__, force=getattr(args, "force", False), silent=getattr(args, "silent", False))
            sys.exit(ret_code)

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
            time_mode = None
            if getattr(args, "time_full", False):
                time_mode = "full"
            elif getattr(args, "time", None):
                val = str(getattr(args, "time")).lower()
                time_mode = "full" if val in ("full", "completo") else "ms"

            if time_mode:
                print(f"{COLOR_AMARILLO}\n{format_elapsed_time(elapsed, mode=time_mode)}{NO_COLOR}")

    except PseudocodeError as e:
        COLOR_ROJO = "\033[31m"
        NO_COLOR = "\033[0m"
        print(f"{COLOR_ROJO}\n{e.format_diagnostic(args.file)}\n{NO_COLOR}", file=sys.stderr)
        sys.exit(1)
    except RecursionError:
        COLOR_ROJO = "\033[31m"
        NO_COLOR = "\033[0m"
        print(
            f"{COLOR_ROJO}\n[ERROR DE EJECUCIÓN] Se excedió la profundidad máxima de llamadas recursivas.\n"
            f"Verifica la condición de corte (caso base) o la selección del pivote en funciones recursivas.\n{NO_COLOR}",
            file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        COLOR_ROJO = "\033[31m"
        NO_COLOR = "\033[0m"
        print(f"{COLOR_ROJO}\nError inesperado: {e}\n{NO_COLOR}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
