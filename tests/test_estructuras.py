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
Pruebas integrales de todas las estructuras definidas en estructuras.txt
"""

import unittest
from pseudocode import run_code


class TestEstructuras(unittest.TestCase):
    def test_ciclo_para(self):
        code = """
        INICIO
            ENTERO suma = 0
            PARA(ENTERO vueltas = 0; vueltas < 5; vueltas++)
                suma = suma + vueltas
            FIN PARA
            IMPRIMIR("SUMA: " + suma)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("SUMA: 10", out)

    def test_ciclo_mientras(self):
        code = """
        INICIO
            ENTERO n = 3
            MIENTRAS (n > 0)
                n--
            FIN MIENTRAS
            IMPRIMIR("FINAL: " + n)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("FINAL: 0", out)

    def test_ciclo_hacer_mientras(self):
        code = """
        INICIO
            ENTERO cuenta = 0
            HACER
                cuenta++
            MIENTRAS (cuenta < 3)
            FIN HACER
            IMPRIMIR("CUENTA: " + cuenta)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("CUENTA: 3", out)

    def test_condicional_si_sino_si(self):
        code = """
        INICIO
            ENTERO nota = 7
            SI (nota >= 9)
                IMPRIMIR("EXCELENTE")
            SINO SI (nota >= 7)
                IMPRIMIR("MUY BIEN")
            SINO
                IMPRIMIR("REGULAR")
            FIN SI
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("MUY BIEN", out)

    def test_vectores_y_matrices(self):
        code = """
        INICIO
            REAL vector[3] = [1.5, 2.5, 3.5]
            IMPRIMIR("V0: " + vector[0])
            IMPRIMIR("LARGO V: " + vector.largo)

            ENTERO matriz[2][3] = [[10, 20, 30], [40, 50, 60]]
            IMPRIMIR("M1_2: " + matriz[1][2])
            IMPRIMIR("FILAS: " + matriz.largo)
            IMPRIMIR("COLS: " + matriz[0].largo)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("V0: 1.5", out)
        self.assertIn("LARGO V: 3", out)
        self.assertIn("M1_2: 60", out)
        self.assertIn("FILAS: 2", out)
        self.assertIn("COLS: 3", out)

    def test_procedimiento_y_funcion(self):
        code = """
        FUNCION duplicar(x: ENTERO): ENTERO
            RETORNO x * 2
        FIN FUNCION

        PROCEDIMIENTO saludar(nombre: CADENA)
            IMPRIMIR("HOLA " + nombre)
        FIN PROCEDIMIENTO

        INICIO
            ENTERO res = duplicar(21)
            IMPRIMIR("DOBLE: " + res)
            saludar("ALUMNO")
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("DOBLE: 42", out)
        self.assertIn("HOLA ALUMNO", out)

    def test_funciones_matematicas_incorporadas(self):
        code = """
        INICIO
            BOOLEANO par4 = ESPAR(4)
            BOOLEANO impar5 = ESIMPAR(5)
            ENTERO resto = MOD(17, 5)

            IMPRIMIR("PAR: " + par4)
            IMPRIMIR("IMPAR: " + impar5)
            IMPRIMIR("RESTO: " + resto)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("PAR: VERDADERO", out)
        self.assertIn("IMPAR: VERDADERO", out)
        self.assertIn("RESTO: 2", out)

    def test_concatenacion_cadenas_y_vectores(self):
        code = """
        INICIO
            ENTERO mi_numero = 1
            REAL mi_real = 2.5
            BOOLEANO mi_booleano = VERDADERO
            CARACTER mi_caracter = 'a'
            CADENA mi_cadena = "hola"

            IMPRIMIR("El valor es: " + mi_numero)
            IMPRIMIR("El valor es: " + mi_real)
            IMPRIMIR("El valor es: " + mi_booleano)
            IMPRIMIR("El valor es: " + mi_caracter)
            IMPRIMIR("El valor es: " + mi_cadena)

            ENTERO vec1[2] = [1, 2]
            ENTERO vec2[2] = [3, 4]
            ENTERO cat[] = vec1 + vec2
            IMPRIMIR("VEC CONCAT LARGO: " + cat.largo)
            IMPRIMIR("VEC CONCAT [2]: " + cat[2])
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("El valor es: 1", out)
        self.assertIn("El valor es: 2.5", out)
        self.assertIn("El valor es: VERDADERO", out)
        self.assertIn("El valor es: a", out)
        self.assertIn("El valor es: hola", out)
        self.assertIn("VEC CONCAT LARGO: 4", out)
    def test_propiedad_largo_vectores(self):
        code = """
        ENTERO mi_vector[] = [5,2,7]
        ENTERO cantidad = mi_vector.largo //RETORNA 3
        IMPRIMIR("CANTIDAD: " + cantidad)

        CADENA nombres[] = ["Ana", "Pedro", "Lucia", "Marcos"]
        IMPRIMIR("NOMBRES: " + nombres.largo)

        REAL vacio[] = []
        IMPRIMIR("VACIO: " + vacio.largo)
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("CANTIDAD: 3", out)
        self.assertIn("NOMBRES: 4", out)
    def test_funciones_dentro_de_inicio_fin(self):
        code = """
        INICIO
            FUNCION sumar(a: ENTERO, b: ENTERO): ENTERO
                RETORNO a + b
            FIN FUNCION

            ENTERO res = sumar(15, 27)
            IMPRIMIR("RESULTADO: " + res)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("RESULTADO: 42", out)

    def test_funcion_sin_tipo_de_retorno_y_variable_en_cuerpo(self):
        code = """
        INICIO
            FUNCION mostrar_algo(x: ENTERO)
                REAL total_mes = 100.5
                IMPRIMIR("TOTAL: " + total_mes)
            FIN FUNCION

            mostrar_algo(1)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("TOTAL: 100.5", out)

    def test_asignacion_fila_matriz(self):
        code = """
        INICIO
            ENTERO m[2][2]
            ENTERO fila[2] = [10, 20]
            m[0] = fila
            IMPRIMIR("M0_0: " + m[0][0])
            IMPRIMIR("M0_1: " + m[0][1])
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("M0_0: 10", out)
        self.assertIn("M0_1: 20", out)

    def test_leer_linea_tipos_automaticos(self):
        import tempfile
        import os
        with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as f:
            f.write("12345\n")
            f.write("98.75\n")
            f.write("VERDADERO\n")
            f.write("FALSO\n")
            f.write("HOLA MUNDO\n")
            tmp_path = f.name.replace("\\", "/")

        code = f"""
        INICIO
            ARCHIVO f = ABRIR_ARCHIVO("{tmp_path}", "lectura")
            ENTERO n = f.LEER_LINEA()
            REAL r = f.LEER_LINEA()
            BOOLEANO b1 = f.LEER_LINEA()
            BOOLEANO b2 = f.LEER_LINEA()
            CADENA s = f.LEER_LINEA()
            f.CERRAR_ARCHIVO()

            IMPRIMIR("N: " + (n + 5))
            IMPRIMIR("R: " + (r + 1.25))
            IMPRIMIR("B1: " + b1)
            IMPRIMIR("B2: " + b2)
            IMPRIMIR("S: " + s)
        FIN
        """
        try:
            out = []
            run_code(code, output_collector=out)
            self.assertIn("N: 12350", out)
            self.assertIn("R: 100.0", out)
            self.assertIn("B1: VERDADERO", out)
            self.assertIn("B2: FALSO", out)
            self.assertIn("S: HOLA MUNDO", out)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_deteccion_typo_funcion_en_inicio(self):
        from pseudocode.errors import ParseError
        code = """
        INICIO
            FUNCIO duplicar(x: ENTERO): ENTERO
                RETORNAR x * 2
            FIN FUNCION
            IMPRIMIR(duplicar(10))
        FIN
        """
        with self.assertRaises(ParseError) as ctx:
            run_code(code, lenient=False)
        self.assertIn("Palabra clave no reconocida: 'FUNCIO'", str(ctx.exception))
        self.assertIn("¿Quisiste decir 'FUNCION'?", str(ctx.exception))
        self.assertEqual(ctx.exception.length, 6)

    def test_correccion_lenient_funcion_en_inicio(self):
        code = """
        INICIO
            FUNCIO duplicar(x: ENTERO): ENTERO
                RETORNAR x * 2
            FIN FUNCION
            IMPRIMIR("DUPLICADO: " + duplicar(10))
        FIN
        """
        out = []
        run_code(code, output_collector=out, lenient=True)
        self.assertIn("DUPLICADO: 20", out)

    def test_deteccion_typo_retornar(self):
        from pseudocode.errors import ParseError
        code = """
        FUNCION f(): ENTERO
            RETORNA 42
        FIN FUNCION
        """
        with self.assertRaises(ParseError) as ctx:
            run_code(code, lenient=False)
        self.assertIn("Palabra clave no reconocida: 'RETORNA'", str(ctx.exception))
        self.assertIn("¿Quisiste decir 'RETORNAR'?", str(ctx.exception))


    def test_estructura_definir_declarar_y_asignar(self):
        # Caso exacto de la imagen del usuario
        code = """
        Estructura Libro: // Definir
            CADENA nombre
            ENTERO hojas
            CADENA sinopsis
            CADENA autor
            CADENA editorial
            ENTERO edicion
        Fin Estructura

        Libro libro1 // Declarar

        libro1.nombre = "Nombre del Libro" //Asignar un valor
        libro1.hojas = 350
        libro1.autor = "Jorge Luis Borges"
        libro1.editorial = "Sur"
        libro1.edicion = 1

        IMPRIMIR("NOMBRE: " + libro1.nombre)
        IMPRIMIR("HOJAS: " + libro1.hojas)
        IMPRIMIR("AUTOR: " + libro1.autor)
        IMPRIMIR("EDITORIAL: " + libro1.editorial)
        IMPRIMIR("EDICION: " + libro1.edicion)
        IMPRIMIR("OBJETO: " + libro1)
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("NOMBRE: Nombre del Libro", out)
        self.assertIn("HOJAS: 350", out)
        self.assertIn("AUTOR: Jorge Luis Borges", out)
        self.assertIn("EDITORIAL: Sur", out)
        self.assertIn("EDICION: 1", out)
        self.assertTrue(any("Libro{" in line for line in out))

    def test_estructuras_multiples_e_independientes(self):
        code = """
        Estructura Persona:
            CADENA nombre
            ENTERO edad
        Fin Estructura

        Persona p1
        Persona p2

        p1.nombre = "Alice"
        p1.edad = 25

        p2.nombre = "Bob"
        p2.edad = 30

        IMPRIMIR("P1: " + p1.nombre + " (" + p1.edad + ")")
        IMPRIMIR("P2: " + p2.nombre + " (" + p2.edad + ")")
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("P1: Alice (25)", out)
        self.assertIn("P2: Bob (30)", out)

    def test_vector_de_estructuras(self):
        code = """
        Estructura Producto:
            CADENA codigo
            REAL precio
        Fin Estructura

        Producto inventario[2]
        inventario[0].codigo = "P01"
        inventario[0].precio = 99.5
        inventario[1].codigo = "P02"
        inventario[1].precio = 150.0

        IMPRIMIR("PROD0: " + inventario[0].codigo + " $" + inventario[0].precio)
        IMPRIMIR("PROD1: " + inventario[1].codigo + " $" + inventario[1].precio)
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("PROD0: P01 $99.5", out)
        self.assertIn("PROD1: P02 $150.0", out)

    def test_estructura_en_funciones_y_procedimientos(self):
        code = """
        Estructura Alumno:
            CADENA nombre
            ENTERO nota
        Fin Estructura

        FUNCION esta_aprobado(a: Alumno): BOOLEANO
            RETORNAR a.nota >= 6
        FIN FUNCION

        INICIO
            Alumno alumno1
            alumno1.nombre = "Carlos"
            alumno1.nota = 8
            BOOLEANO aprobo = esta_aprobado(alumno1)
            IMPRIMIR("APROBADO: " + aprobo)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("APROBADO: VERDADERO", out)

    def test_error_campo_inexistente_estructura(self):
        from pseudocode.errors import TypeError as PseudoTypeError
        code = """
        Estructura Libro:
            CADENA nombre
            ENTERO hojas
        Fin Estructura

        Libro l
        l.nombr = "Invalido"
        """
        with self.assertRaises(PseudoTypeError) as ctx:
            run_code(code, lenient=False)
        self.assertIn("no tiene el campo 'nombr'", str(ctx.exception))
        self.assertIn("¿Quisiste decir 'nombre'?", str(ctx.exception))

    def test_estructura_recursiva_nodo(self):
        code = """
        Estructura nodo:
            CADENA nombre
            nodo proximo_nodo
        Fin Estructura

        INICIO
            nodo n1
            nodo n2
            n1.nombre = "Primero"
            n2.nombre = "Segundo"
            n1.proximo_nodo = n2

            IMPRIMIR("N1: " + n1.nombre)
            IMPRIMIR("PROXIMO: " + n1.proximo_nodo.nombre)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("N1: Primero", out)
        self.assertIn("PROXIMO: Segundo", out)

    def test_tipo_nulo_y_recorrido_lista(self):
        code = """
        ESTRUCTURA Nodo:
            CADENA nombre
            Nodo proximo_nodo
        Fin Estructura

        INICIO
            Nodo n1
            Nodo n2
            n1.nombre = "Primero"
            n2.nombre = "Segundo"
            n1.proximo_nodo = n2

            Nodo actual
            actual = n1

            MIENTRAS actual != NULO
                IMPRIMIR("VISITADO: " + actual.nombre)
                actual = actual.proximo_nodo
            FIN MIENTRAS

            IMPRIMIR("FINAL: " + actual)
            SI(actual == null)
                IMPRIMIR("ES NULL: VERDADERO")
            FIN SI
            SI(actual == None)
                IMPRIMIR("ES NONE: VERDADERO")
            FIN SI
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("VISITADO: Primero", out)
        self.assertIn("VISITADO: Segundo", out)
        self.assertIn("FINAL: NULO", out)
        self.assertIn("ES NULL: VERDADERO", out)
        self.assertIn("ES NONE: VERDADERO", out)

    def test_estructura_persona_atributos(self):
        code = """
        ESTRUCTURA persona
            CADENA nombre
            ENTERO edad
        FIN ESTRUCTURA

        INICIO
            Persona pepe
            pepe.nombre = "Pepe"
            pepe.edad = 25
            IMPRIMIR("PERSONA: " + pepe.nombre + " " + pepe.edad)
        FIN
        """
        out = []
        run_code(code, output_collector=out)
        self.assertIn("PERSONA: Pepe 25", out)


if __name__ == "__main__":
    unittest.main()


