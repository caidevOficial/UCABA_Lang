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
Pruebas unitarias para los operadores de división entera '//' y módulo '%'
y su correcta convivencia con comentarios simples ('//' y '#').
"""

import unittest
from pseudocode import run_code
from pseudocode.errors import TypeError as PseudoTypeError, RuntimeError as PseudoRuntimeError


class TestOperators(unittest.TestCase):
    def test_division_entera_basica(self):
        code = """
        INICIO
            ENTERO a = 10 // 3
            ENTERO b = 20 // 4
            ENTERO c = 7 // 2
            ENTERO d = 100 // 10 // 2
            IMPRIMIR("A: " + a)
            IMPRIMIR("B: " + b)
            IMPRIMIR("C: " + c)
            IMPRIMIR("D: " + d)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertEqual(out, ["A: 3", "B: 5", "C: 3", "D: 5"])

    def test_division_entera_dentro_de_indices(self):
        code = """
        INICIO
            ENTERO columnas = 2
            ENTERO origen[2][2] = [[1, 2], [3, 4]]
            ENTERO destino[2][2]
            PARA (ENTERO p = 0; p < 4; p++)
                destino[p // columnas][p % columnas] = origen[p // columnas][p % columnas] * 10
            FIN PARA
            IMPRIMIR(destino[0][0] + "," + destino[0][1] + "," + destino[1][0] + "," + destino[1][1])
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertEqual(out, ["10,20,30,40"])


    def test_division_entera_con_variables_y_precedencia(self):
        code = """
        INICIO
            ENTERO x = 14
            ENTERO val_b = 3
            ENTERO res = x // val_b
            ENTERO prec1 = 10 + 20 // 4
            ENTERO prec2 = (10 + 20) // 4
            IMPRIMIR("RES: " + res)
            IMPRIMIR("PREC1: " + prec1)
            IMPRIMIR("PREC2: " + prec2)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertEqual(out, ["RES: 4", "PREC1: 15", "PREC2: 7"])

    def test_division_entera_en_funciones_y_retorno(self):
        code = """
        FUNCION dividir(dividendo: ENTERO, divisor: ENTERO): ENTERO
            RETORNAR dividendo // divisor
        FIN FUNCION

        INICIO
            ENTERO res = dividir(27, 4)
            IMPRIMIR("DIV: " + res)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertEqual(out, ["DIV: 6"])

    def test_division_entera_por_cero_arroja_error(self):
        code = """
        INICIO
            ENTERO a = 10 // 0
        FIN
        """
        with self.assertRaises(PseudoRuntimeError) as ctx:
            run_code(code)
        self.assertIn("División por cero", str(ctx.exception))

    def test_modulo_operador_basico(self):
        code = """
        INICIO
            ENTERO m1 = 10 % 3
            ENTERO m2 = 15 % 4
            ENTERO m3 = 20 % 5
            ENTERO m4 = 25 % 7
            IMPRIMIR("M1: " + m1)
            IMPRIMIR("M2: " + m2)
            IMPRIMIR("M3: " + m3)
            IMPRIMIR("M4: " + m4)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertEqual(out, ["M1: 1", "M2: 3", "M3: 0", "M4: 4"])

    def test_modulo_con_variables_y_precedencia(self):
        code = """
        INICIO
            ENTERO a = 23
            ENTERO b = 5
            ENTERO r = a % b
            ENTERO comb = (a // b) * b + (a % b)
            IMPRIMIR("R: " + r)
            IMPRIMIR("COMB: " + comb)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertEqual(out, ["R: 3", "COMB: 23"])

    def test_modulo_por_cero_arroja_error(self):
        code = """
        INICIO
            ENTERO a = 10 % 0
        FIN
        """
        with self.assertRaises(PseudoRuntimeError) as ctx:
            run_code(code)
        self.assertIn("Módulo por cero", str(ctx.exception))

    def test_validacion_tipos_division_entera_y_modulo(self):
        code_inv_div = """
        INICIO
            CADENA s = "texto"
            ENTERO x = s // 2
        FIN
        """
        with self.assertRaises(PseudoTypeError):
            run_code(code_inv_div, lenient=False)

        code_inv_mod = """
        INICIO
            CADENA s = "texto"
            ENTERO x = s % 2
        FIN
        """
        with self.assertRaises(PseudoTypeError):
            run_code(code_inv_mod, lenient=False)

    def test_convivencia_division_entera_con_comentarios(self):
        code = """
        // Comentario en la primera linea
        INICIO
            // Comentario indentado
            ENTERO x = 10 // 3
            ENTERO val_y = 20 // 4 // Comentario explicativo
            ENTERO z = 100 // 2 # Comentario con hash
            IMPRIMIR("X: " + x)
            IMPRIMIR("Y: " + val_y)
            IMPRIMIR("Z: " + z)
        FIN // Fin del programa
        """
        out = []
        run_code(code, output_collector=out)
        self.assertEqual(out, ["X: 3", "Y: 5", "Z: 50"])

    def test_comentarios_con_hash_en_lineas_independientes(self):
        code = """
        # Comentario de inicio con hash
        INICIO
            # Declaracion de variable
            ENTERO valor = 42 # inline con hash
            IMPRIMIR("VAL: " + valor)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertEqual(out, ["VAL: 42"])


if __name__ == "__main__":
    unittest.main()
