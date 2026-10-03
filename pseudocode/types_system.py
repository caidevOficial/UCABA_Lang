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
Sistema de tipos fuertemente tipado para el lenguaje de pseudocódigo.
Define los tipos canónicos (ENTERO, FLOTANTE, REAL, CADENA, CARACTER, BOOLEANO, ARCHIVO, Vector, Matriz),
las reglas de compatibilidad, promoción y representación en tiempo de ejecución.
"""

import struct
from typing import Any, Optional, List, Tuple


class DataType:
    """Clase base para todos los tipos del sistema de tipos."""
    def __init__(self, name: str):
        self.name = name

    def is_assignable_from(self, source: 'DataType') -> bool:
        """Determina si un valor de tipo `source` se puede asignar a una variable de este tipo."""
        if self.name == "ANY" or (isinstance(source, DataType) and source.name == "ANY"):
            return True
        if self == source:
            return True
        # Reglas de compatibilidad y conversión numérica:
        # ENTERO, FLOTANTE y REAL son asignables entre sí en el sistema de números decimales,
        # aplicando truncamiento a float32 para FLOTANTE y float64 para REAL.
        if self in (TYPE_REAL, TYPE_FLOTANTE) and source in (TYPE_ENTERO, TYPE_FLOTANTE, TYPE_REAL):
            return True
        if self == TYPE_ENTERO and source in (TYPE_FLOTANTE, TYPE_REAL):
            return True
        # CARACTER a CADENA
        if self == TYPE_CADENA and source == TYPE_CARACTER:
            return True
        return False

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, DataType):
            return self.name == other.name
        return False

    def __repr__(self) -> str:
        return self.name


class VectorType(DataType):
    def __init__(self, element_type: DataType, size: Optional[int] = None):
        super().__init__(f"{element_type.name}[]")
        self.element_type = element_type
        self.size = size

    def is_assignable_from(self, source: 'DataType') -> bool:
        if isinstance(source, VectorType):
            return self.element_type.is_assignable_from(source.element_type)
        return False

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, VectorType):
            return self.element_type == other.element_type
        return False


class MatrixType(DataType):
    def __init__(self, element_type: DataType, rows: Optional[int] = None, cols: Optional[int] = None):
        super().__init__(f"{element_type.name}[][]")
        self.element_type = element_type
        self.rows = rows
        self.cols = cols

    def is_assignable_from(self, source: 'DataType') -> bool:
        if isinstance(source, MatrixType):
            return self.element_type.is_assignable_from(source.element_type)
        return False

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, MatrixType):
            return self.element_type == other.element_type
        return False


# Tipos primitivos singleton
TYPE_ENTERO = DataType("ENTERO")
TYPE_FLOTANTE = DataType("FLOTANTE")
TYPE_REAL = DataType("REAL")
TYPE_CADENA = DataType("CADENA")
TYPE_CARACTER = DataType("CARACTER")
TYPE_BOOLEANO = DataType("BOOLEANO")
TYPE_ARCHIVO = DataType("ARCHIVO")
TYPE_VOID = DataType("VACIO")
TYPE_ANY = DataType("ANY")


def parse_type_name(name: str) -> DataType:
    """Convierte un nombre textual al objeto DataType correspondiente."""
    upper = name.strip().upper()
    if upper.endswith("[][]"):
        base_name = upper[:-4]
        base_type = parse_type_name(base_name)
        return MatrixType(base_type)
    elif upper.endswith("[]"):
        base_name = upper[:-2]
        base_type = parse_type_name(base_name)
        return VectorType(base_type)

    mapping = {
        "ENTERO": TYPE_ENTERO,
        "FLOTANTE": TYPE_FLOTANTE,
        "REAL": TYPE_REAL,
        "CADENA": TYPE_CADENA,
        "CARACTER": TYPE_CARACTER,
        "BOOLEANO": TYPE_BOOLEANO,
        "ARCHIVO": TYPE_ARCHIVO,
        "VACIO": TYPE_VOID,
        "PROCEDIMIENTO": TYPE_VOID,
    }
    if upper in mapping:
        return mapping[upper]
    raise ValueError(f"Tipo de dato desconocido: '{name}'")


def to_float32(value: float) -> float:
    """Convierte un flotante a precisión simple de 32 bits (IEEE 754)."""
    try:
        return struct.unpack('f', struct.pack('f', float(value)))[0]
    except OverflowError:
        return float('inf') if value > 0 else float('-inf')


def validate_runtime_value(value: Any, expected_type: DataType) -> Any:
    """
    Valida y adapta un valor en tiempo de ejecución para cumplir con el tipo esperado.
    Lanza TypeError si no es compatible.
    """
    if expected_type == TYPE_ANY:
        return value

    if expected_type == TYPE_ENTERO:
        if isinstance(value, bool):
            raise TypeError("No se puede asignar un BOOLEANO a un ENTERO.")
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        if isinstance(value, str) and value.strip().lstrip('-+').isdigit():
            return int(value.strip())
        raise TypeError(f"Se esperaba ENTERO, se obtuvo {type(value).__name__} ({value!r})")

    if expected_type == TYPE_FLOTANTE:
        if isinstance(value, (int, float)):
            return to_float32(float(value))
        if isinstance(value, str):
            try:
                return to_float32(float(value.strip()))
            except ValueError:
                pass
        raise TypeError(f"Se esperaba FLOTANTE (32-bit), se obtuvo {type(value).__name__} ({value!r})")

    if expected_type == TYPE_REAL:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value.strip())
            except ValueError:
                pass
        raise TypeError(f"Se esperaba REAL (64-bit), se obtuvo {type(value).__name__} ({value!r})")

    if expected_type == TYPE_CADENA:
        if isinstance(value, str):
            return value
        return str(value)

    if expected_type == TYPE_CARACTER:
        if isinstance(value, str) and len(value) == 1:
            return value
        raise TypeError(f"Se esperaba CARACTER (longitud 1), se obtuvo {value!r}")

    if expected_type == TYPE_BOOLEANO:
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            u = value.strip().upper()
            if u in ("VERDADERO", "TRUE", "1"):
                return True
            if u in ("FALSO", "FALSE", "0"):
                return False
        raise TypeError(f"Se esperaba BOOLEANO, se obtuvo {type(value).__name__} ({value!r})")

    if isinstance(expected_type, VectorType):
        if not isinstance(value, list):
            raise TypeError(f"Se esperaba un vector ({expected_type}), se obtuvo {type(value).__name__}")
        return [validate_runtime_value(item, expected_type.element_type) for item in value]

    if isinstance(expected_type, MatrixType):
        if not isinstance(value, list):
            raise TypeError(f"Se esperaba una matriz ({expected_type}), se obtuvo {type(value).__name__}")
        return [
            [validate_runtime_value(cell, expected_type.element_type) for cell in row]
            for row in value
        ]

    return value
