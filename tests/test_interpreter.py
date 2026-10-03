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
Pruebas exhaustivas para el intérprete y el sistema de tipos.
"""

import os
import tempfile
import unittest
from pseudocode import run_code, check_file
from pseudocode.errors import TypeError as PseudoTypeError, ParseError


class TestPseudocodeInterpreter(unittest.TestCase):
    def test_precision_flotante_vs_real(self):
        # 1.0000001 en 32 bits redondea diferente a 64 bits
        code = """
        INICIO
            FLOTANTE f = 1.0000001
            REAL r = 1.0000001
            IMPRIMIR("F: " + f)
            IMPRIMIR("R: " + r)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        # En float32 (precisión simple), se representa como float de 32-bit (1.0000001192092896)
        # mientras que en float64 (REAL) se mantiene 1.0000001
        self.assertNotEqual(out[0], out[1])
        self.assertTrue(out[0].startswith("F: 1.000000119"))
        self.assertEqual(out[1], "R: 1.0000001")

    def test_archivos_lectura_y_escritura(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            f_path = os.path.join(tmpdir, "datos.txt").replace("\\", "/")
            # Escribir archivo con pseudocódigo
            write_code = f"""
            INICIO
                ARCHIVO f = ABRIR_ARCHIVO("{f_path}", "escritura")
                f.ESCRIBIR_LINEA("PRIMERA")
                f.ESCRIBIR_LINEA("SEGUNDA")
                f.CERRAR_ARCHIVO()
            FIN
            """
            run_code(write_code)

            self.assertTrue(os.path.exists(f_path))

            # Leer archivo con pseudocódigo
            read_code = f"""
            INICIO
                ARCHIVO f = ABRIR_ARCHIVO("{f_path}", "lectura")
                CADENA l1 = f.LEER_LINEA()
                CADENA l2 = f.LEER_LINEA()
                BOOLEANO es_fin = f.findearchivo
                f.CERRAR_ARCHIVO()

                IMPRIMIR("L1: " + l1)
                IMPRIMIR("L2: " + l2)
                IMPRIMIR("FIN: " + es_fin)
            FIN
            """
            out = []
            run_code(read_code, output_collector=out)
            self.assertIn("L1: PRIMERA", out)
            self.assertIn("L2: SEGUNDA", out)
            self.assertIn("FIN: VERDADERO", out)

    def test_conteo_lineas_archivo_tolerante(self):
        # Prueba el caso de algoritmo.txt donde el while no llama a LEER_LINEA explícitamente
        with tempfile.TemporaryDirectory() as tmpdir:
            f_path = os.path.join(tmpdir, "cinco_lineas.txt").replace("\\", "/")
            with open(f_path, "w", encoding="utf-8") as f:
                f.write("A\nB\nC\nD\nE\n")

            code = f"""
            INICIO
                ENTERO cant = 0
                ARCHIVO f = ABRIR_ARCHIVO("{f_path}", "lectura")
                MIENTRAS NO f.findearchivo
                    cant++
                FIN MIENTRAS
                f.CERRAR_ARCHIVO()
                IMPRIMIR("TOTAL: " + cant)
            FIN
            """
            out = []
            run_code(code, output_collector=out)
            self.assertIn("TOTAL: 5", out)

    def test_chequeo_estricto_rechaza_incompatibilidad(self):
        code = """
        INICIO
            ENTERO n = "texto"
        FIN
        """
        with self.assertRaises(PseudoTypeError):
            run_code(code, lenient=False)

    def test_quicksort_pseudocodigo(self):
        code = """
        FUNCION contar(vec[]: ENTERO, piv: ENTERO, mayor: BOOLEANO): ENTERO
            ENTERO c = 0
            PARA(ENTERO i = 0; i < vec.largo; i++)
                SI (mayor Y vec[i] > piv) O (NO mayor Y vec[i] <= piv)
                    c++
                FIN SI
            FIN PARA
            RETORNO c
        FIN FUNCION

        FUNCION quicksort(vec[]: ENTERO): ENTERO[]
            SI(vec.largo < 2)
                RETORNO vec

            ENTERO piv[1] = vec[0]
            ENTERO c_men = contar(vec, piv[0], FALSO) - 1
            ENTERO c_may = contar(vec, piv[0], VERDADERO)

            ENTERO menores[c_men]
            ENTERO mayores[c_may]
            ENTERO i_men = 0
            ENTERO i_may = 0

            PARA(ENTERO i = 1; i < vec.largo; i++)
                SI (vec[i] <= piv[0])
                    menores[i_men] = vec[i]
                    i_men++
                SINO
                    mayores[i_may] = vec[i]
                    i_may++
                FIN SI
            FIN PARA

            RETORNO quicksort(menores) + piv + quicksort(mayores)
        FIN FUNCION

        INICIO
            ENTERO arr[5] = [50, 20, 40, 10, 30]
            ENTERO ordenado[] = quicksort(arr)
            IMPRIMIR("O0: " + ordenado[0])
            IMPRIMIR("O1: " + ordenado[1])
            IMPRIMIR("O2: " + ordenado[2])
            IMPRIMIR("O3: " + ordenado[3])
            IMPRIMIR("O4: " + ordenado[4])
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertEqual(out, ["O0: 10", "O1: 20", "O2: 30", "O3: 40", "O4: 50"])


if __name__ == "__main__":
    unittest.main()
