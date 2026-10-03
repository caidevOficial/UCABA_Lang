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
Definición de tokens y categorías léxicas para el lenguaje de pseudocódigo.
"""

from enum import Enum, auto
from typing import Any, Optional


class TokenType(Enum):
    # Literales
    ENTERO_LIT = auto()
    REAL_LIT = auto()
    CADENA_LIT = auto()
    CARACTER_LIT = auto()
    BOOLEANO_LIT = auto()

    # Identificadores
    IDENTIFICADOR = auto()

    # Palabras clave de Tipos
    TIPO_ENTERO = auto()
    TIPO_FLOTANTE = auto()
    TIPO_REAL = auto()
    TIPO_CADENA = auto()
    TIPO_CARACTER = auto()
    TIPO_BOOLEANO = auto()
    TIPO_ARCHIVO = auto()
    TIPO_VOID = auto()

    # Estructuras de Control y Bloques
    KW_INICIO = auto()
    KW_FUNCION = auto()
    KW_PROCEDIMIENTO = auto()
    KW_FIN = auto()
    KW_RETORNAR = auto()
    KW_RETORNO = KW_RETORNAR
    KW_SI = auto()
    KW_SINO = auto()
    KW_MIENTRAS = auto()
    KW_HACER = auto()
    KW_PARA = auto()
    KW_IMPRIMIR = auto()

    # Funciones incorporadas matemáticas
    KW_MOD = auto()
    KW_ESPAR = auto()
    KW_ESIMPAR = auto()

    # Operadores Aritméticos
    SUMA = auto()          # +
    RESTA = auto()         # -
    MULT = auto()          # *
    DIV = auto()           # /
    MOD = auto()           # %
    INC = auto()           # ++
    DEC = auto()           # --

    # Operadores Relacionales
    IGUAL_QUE = auto()     # ==
    DISTINTO = auto()      # !=
    MENOR = auto()         # <
    MAYOR = auto()         # >
    MENOR_IGUAL = auto()   # <=
    MAYOR_IGUAL = auto()   # >=

    # Operadores Lógicos
    OP_Y = auto()          # Y, &&
    OP_O = auto()          # O, ||
    OP_NO = auto()         # NO, !

    # Asignaciones
    ASIGNAR = auto()       # =
    ASIG_SUMA = auto()     # +=
    ASIG_RESTA = auto()    # -=

    # Delimitadores
    PARENTESIS_IZQ = auto()  # (
    PARENTESIS_DER = auto()  # )
    CORCHETE_IZQ = auto()    # [
    CORCHETE_DER = auto()    # ]
    COMA = auto()            # ,
    PUNTO_Y_COMA = auto()    # ;
    DOS_PUNTOS = auto()      # :
    PUNTO = auto()           # .

    EOF = auto()


KEYWORDS = {
    # Tipos
    "ENTERO": TokenType.TIPO_ENTERO,
    "FLOTANTE": TokenType.TIPO_FLOTANTE,
    "REAL": TokenType.TIPO_REAL,
    "CADENA": TokenType.TIPO_CADENA,
    "CARACTER": TokenType.TIPO_CARACTER,
    "BOOLEANO": TokenType.TIPO_BOOLEANO,
    "ARCHIVO": TokenType.TIPO_ARCHIVO,
    "VOID": TokenType.TIPO_VOID,

    # Control y Bloques
    "INICIO": TokenType.KW_INICIO,
    "FUNCION": TokenType.KW_FUNCION,
    "PROCEDIMIENTO": TokenType.KW_PROCEDIMIENTO,
    "FIN": TokenType.KW_FIN,
    "RETORNAR": TokenType.KW_RETORNAR,
    "RETORNO": TokenType.KW_RETORNAR,
    "SI": TokenType.KW_SI,
    "SINO": TokenType.KW_SINO,
    "MIENTRAS": TokenType.KW_MIENTRAS,
    "HACER": TokenType.KW_HACER,
    "PARA": TokenType.KW_PARA,
    "IMPRIMIR": TokenType.KW_IMPRIMIR,

    # Funciones especiales
    "MOD": TokenType.KW_MOD,
    "ESPAR": TokenType.KW_ESPAR,
    "ESIMPAR": TokenType.KW_ESIMPAR,

    # Operadores lógicos en español
    "Y": TokenType.OP_Y,
    "O": TokenType.OP_O,
    "NO": TokenType.OP_NO,

    # Booleanos
    "VERDADERO": TokenType.BOOLEANO_LIT,
    "FALSO": TokenType.BOOLEANO_LIT,
    "TRUE": TokenType.BOOLEANO_LIT,
    "FALSE": TokenType.BOOLEANO_LIT,
}


class Token:
    def __init__(self, type_: TokenType, value: Any, line: int, column: int, length: int = 1):
        self.type = type_
        self.value = value
        self.line = line
        self.column = column
        self.length = length

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, L{self.line}:C{self.column})"
