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
Manejadores de archivos y funciones incorporadas (Built-ins) para el pseudocódigo.
Incluye ArchivoHandle con soporte para .findearchivo, .LEER_LINEA(), .ESCRIBIR_LINEA() y .CERRAR_ARCHIVO(),
además de ESPAR(), ESIMPAR(), MOD() y ABRIR_ARCHIVO().
"""

import os
from typing import List, Any, Optional
from pseudocode.errors import RuntimeError


class ArchivoHandle:
    def __init__(self, path: str, mode: str):
        self.path = path
        self.mode = mode.lower()
        self.lines: List[str] = []
        self.cursor = 0
        self.is_closed = False
        self.read_during_iteration = False  # Para evitar bucle infinito si omiten LEER_LINEA()

        # Normalizar modos
        if self.mode in ("lectura", "r"):
            self.python_mode = "r"
            if not os.path.exists(path):
                raise RuntimeError(f"El archivo '{path}' no existe para lectura.")
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                # Conservar las líneas sin el salto de línea al final
                self.lines = [line.rstrip("\r\n") for line in f]
        elif self.mode in ("escritura", "w"):
            self.python_mode = "w"
            self.file_writer = open(path, "w", encoding="utf-8")
        elif self.mode in ("anexo", "a"):
            self.python_mode = "a"
            self.file_writer = open(path, "a", encoding="utf-8")
        else:
            raise RuntimeError(f"Modo de archivo no reconocido: '{mode}'. Use 'lectura' o 'escritura'.")

    @property
    def findearchivo(self) -> bool:
        if self.is_closed:
            return True
        if self.python_mode == "r":
            return self.cursor >= len(self.lines)
        return True

    def LEER_LINEA(self) -> Any:
        if self.is_closed:
            raise RuntimeError("Intento de leer de un archivo ya cerrado.")
        if self.python_mode != "r":
            raise RuntimeError("El archivo no está abierto en modo lectura.")

        self.read_during_iteration = True
        if self.cursor >= len(self.lines):
            return ""
        line = self.lines[self.cursor]
        self.cursor += 1
        return parse_auto_value(line)

    def ESCRIBIR_LINEA(self, content: Any):
        if self.is_closed:
            raise RuntimeError("Intento de escribir en un archivo ya cerrado.")
        if self.python_mode not in ("w", "a"):
            raise RuntimeError("El archivo no está abierto en modo escritura.")

        text = stringify_value(content)
        self.file_writer.write(text + "\n")
        self.file_writer.flush()

    def CERRAR_ARCHIVO(self):
        if not self.is_closed:
            if hasattr(self, "file_writer") and self.file_writer:
                self.file_writer.close()
            self.is_closed = True

    def notify_loop_step(self):
        """
        Si un ciclo MIENTRAS NO file.findearchivo se ejecuta sin llamar a LEER_LINEA(),
        avanza el cursor en 1 para evitar bucles infinitos en algoritmos que cuentan líneas.
        """
        if self.python_mode == "r":
            if not self.read_during_iteration:
                if self.cursor < len(self.lines):
                    self.cursor += 1
            self.read_during_iteration = False

    def __repr__(self) -> str:
        return f"<ARCHIVO '{self.path}' modo='{self.mode}' cursor={self.cursor}/{len(self.lines)}>"


def parse_auto_value(text: str) -> Any:
    """
    Parsea automáticamente una línea de texto a su tipo primitivo correspondiente:
    - BOOLEANO: si es 'VERDADERO', 'FALSO', 'TRUE', 'FALSE'
    - ENTERO: si representa un número entero (ej. 3519, -400)
    - REAL / FLOTANTE: si representa un número decimal con punto o notación científica (ej. 35.19, -0.5)
    - CADENA: cualquier otro texto
    """
    if not isinstance(text, str):
        return text

    stripped = text.strip()
    if not stripped:
        return text

    # 1. Booleano
    upper = stripped.upper()
    if upper in ("VERDADERO", "TRUE"):
        return True
    if upper in ("FALSO", "FALSE"):
        return False

    # 2. Entero (ej. 1234, -450, +10)
    if (stripped.isdigit() or 
        (stripped[0] in ('+', '-') and len(stripped) > 1 and stripped[1:].isdigit())):
        try:
            return int(stripped)
        except ValueError:
            pass

    # 3. Flotante / Real (ej. 12.34, -0.5, 1e5)
    if "." in stripped or "e" in stripped.lower():
        try:
            return float(stripped)
        except ValueError:
            pass

    # 4. Cadena (texto por defecto)
    return text


def stringify_value(val: Any) -> str:
    """Convierte un valor de runtime a su representación canónica en pseudocódigo."""
    if isinstance(val, bool):
        return "VERDADERO" if val else "FALSO"
    if val is None:
        return ""
    if isinstance(val, float):
        # Si es un número entero con formato flotante (ej 12.0), mostrar 12.0 o limpio
        if val.is_integer():
            return f"{val:.1f}"
        return str(val)
    if isinstance(val, list):
        return "[" + ", ".join(stringify_value(x) for x in val) + "]"
    return str(val)


# Builtins matemáticos y utilitarios
def builtin_abrir_archivo(path: str, mode: str) -> ArchivoHandle:
    return ArchivoHandle(path, mode)


def builtin_es_par(number: Any) -> bool:
    if not isinstance(number, (int, float)):
        raise RuntimeError(f"ESPAR requiere un número, se obtuvo {type(number).__name__}")
    return int(number) % 2 == 0


def builtin_es_impar(number: Any) -> bool:
    if not isinstance(number, (int, float)):
        raise RuntimeError(f"ESIMPAR requiere un número, se obtuvo {type(number).__name__}")
    return int(number) % 2 != 0


def builtin_mod(a: Any, b: Any) -> int:
    if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
        raise RuntimeError(f"MOD requiere dos operandos numéricos")
    return int(a) % int(b)
