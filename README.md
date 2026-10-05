<p align="center">
  <img src="ucaba_logo_header.png" width="120" alt="UCABA Logo" />
</p>

<h1 align="center">⚡ UCABA</h1>

<p align="center">
  <strong>El lenguaje de pseudocódigo en español fuertemente tipado para el aprendizaje moderno de algoritmos, estructuras de datos y desarrollo de software.</strong>
</p>

<p align="center">
  <a href="#-autoría-y-créditos"><img src="https://img.shields.io/badge/Autor-%3CFacu%20Falcone%3E-881337?style=for-the-badge" alt="Autor" /></a>
  <img src="https://img.shields.io/badge/Versi%C3%B3n-1.2.0-a81a7d?style=for-the-badge" alt="Versión" />
  <img src="https://img.shields.io/badge/Extensi%C3%B3n-.ucaba-ba288e?style=for-the-badge" alt="Extensión .ucaba" />
  <img src="https://img.shields.io/badge/VS_Code-Extensi%C3%B3n_Oficial-380d3f?style=for-the-badge&logo=visualstudiocode&logoColor=white" alt="VS Code Extension" />
  <img src="https://img.shields.io/badge/Tests-21%20passing-22c55e?style=for-the-badge" alt="Tests" />
  <img src="https://img.shields.io/badge/Licencia-GPL--3.0-2563eb?style=for-the-badge" alt="Licencia GPL-3.0" />
</p>

---

## 📑 Tabla de Contenidos

- [🌟 ¿Qué es UCABA?](#-qué-es-ucaba)
- [✨ Características Principales](#-características-principales)
- [🚀 Instalación y Ecosistema](#-instalación-y-ecosistema)
  - [Instalador Gráfico Autónomo](#-instalador-gráfico-autónomo)
  - [Uso como Módulo de Python](#-uso-como-módulo-de-python)
- [💻 Interfaz de Línea de Comandos (`ucaba`)](#-interfaz-de-línea-de-comandos-ucaba)
- [🎨 Extensión Oficial para Visual Studio Code](#-extensión-oficial-para-visual-studio-code)
- [💎 Sistema de Tipos (Fuertemente Tipado)](#-sistema-de-tipos-fuertemente-tipado)
  - [Tabla de Tipos Primitivos](#tabla-de-tipos-primitivos)
  - [Vectores y Matrices](#vectores-y-matrices)
  - [Reglas de Conversión y Concatenación](#reglas-de-conversión-y-concatenación)
- [📜 Sintaxis y Gramática Canónica](#-sintaxis-y-gramática-canónica)
  - [1. Estructura General del Programa](#1-estructura-general-del-programa)
  - [2. Funciones y Procedimientos](#2-funciones-y-procedimientos)
  - [3. Estructuras de Control](#3-estructuras-de-control)
  - [4. Manejo de Archivos (`ARCHIVO`)](#4-manejo-de-archivos-archivo)
  - [5. Funciones Incorporadas (Built-ins)](#5-funciones-incorporadas-built-ins)
- [💡 Ejemplo Completo de Algoritmo](#-ejemplo-completo-de-algoritmo)
- [🔢 Ordenar una Matriz (Selection Sort)](#-ordenar-una-matriz-selection-sort)
- [🧪 Pruebas Automatizadas](#-pruebas-automatizadas)
- [👤 Autoría y Créditos](#-autoría-y-créditos)

---

## 🌟 ¿Qué es UCABA?

**UCABA** es un lenguaje de programación de pseudocódigo en español, diseñado para combinar la intuición pedagógica del pseudocódigo clásico con el rigor técnico y la seguridad de un **sistema de tipos estático y moderno**.

Permite escribir algoritmos estructurados con palabras clave naturales en español (`INICIO`, `FUNCION`, `MIENTRAS`, `PARA`, `SI`), mientras que un analizador sintáctico descendente recursivo y un verificador de tipos estático aseguran la consistencia de datos antes y durante la ejecución.

> [!NOTE]
> Todos los archivos fuente de UCABA utilizan la extensión oficial obligatoria **`.ucaba`** (por ejemplo: `algoritmo.ucaba`, `nomina.ucaba`).

---

## ✨ Características Principales

- 🛡️ **Fuertemente Tipado:** Validación estática de variables, firmas de funciones, aridad y tipos de retorno.
- 📐 **Precisión Numérica Determinística:** Distinción clara entre `FLOTANTE` (IEEE 754 de 32 bits) y `REAL` (IEEE 754 de 64 bits de doble precisión).
- 🧩 **Arreglos Dinámicos y Matrices:** Vectores (`TIPO[]`) y matrices bidimensionales (`TIPO[][]`) con introspección mediante la propiedad `.largo` y concatenación con el operador `+`.
- 📁 **Manejo Nativo de Archivos:** Tipo `ARCHIVO` integrado con lectura secuencial (`.LEER_LINEA()`), escritura (`.ESCRIBIR_LINEA()`) y detección de fin de archivo (`.findearchivo`).
- ⚡ **CLI Nativo y Autónomo:** Binario `ucaba.exe` listo para ejecutarse en Windows sin requerir instalación previa de Python.
- 🎨 **Herramientas de Desarrollo:** Extensión oficial para VS Code con resaltado sintáctico, autocompletado, diagnósticos visuales y ejecución con un clic.
- 🖼️ **Instalador Todo-en-Uno:** Asistente gráfico moderno con tema Dark Magenta, soporte High-DPI y registro en Windows.

---

## 🚀 Instalación y Ecosistema

### 📦 Instalador Gráfico Autónomo

La forma más sencilla de configurar todo el ecosistema de UCABA en Windows es mediante el instalador todo-en-uno:

1. Ejecuta **`dist/Instalador_UCABA.exe`**.
2. El asistente te permitirá de forma automatizada:
   - ✅ Instalar el comando nativo `ucaba.exe` en tu sistema.
   - ✅ Añadir `ucaba` a la variable de entorno `PATH` del usuario.
   - ✅ Instalar la extensión oficial de **Visual Studio Code** (`ucaba-language-support-1.2.0.vsix`).
   - ✅ Asociar los archivos `.ucaba` en Windows con el icono oficial y opciones de ejecución directa.

> [!TIP]
> El instalador también soporta instalación silenciosa y desatendida mediante el flag:
> ```powershell
> .\Instalador_UCABA.exe --silent
> ```

### 🐍 Uso como Módulo de Python

Si prefieres ejecutar o embeber el intérprete en entornos de desarrollo Python:

```bash
# Ejecutar un archivo
python -m pseudocode run mi_programa.ucaba

# Chequeo estático de tipos sin ejecutar
python -m pseudocode check mi_programa.ucaba
```

---

## 💻 Interfaz de Línea de Comandos (`ucaba`)

El comando `ucaba` ofrece una suite completa de utilidades para desarrolladores y estudiantes:

```
usage: ucaba [-h] {run,check,tokens,lsp-check} ...
```

### 1. `ucaba run` — Ejecutar archivo
Ejecuta el código fuente `.ucaba` directamente:
```bash
ucaba run mi_algoritmo.ucaba
```
*Opciones útiles:*
- `--time`: Muestra el tiempo de análisis y de ejecución en milisegundos.
- `--no-check`: Omite el chequeo estático previo y ejecuta directamente.

### 2. `ucaba check` — Verificación estática
Analiza la sintaxis y valida todos los tipos de variables y funciones sin correr el programa:
```bash
ucaba check mi_algoritmo.ucaba
```

### 3. `ucaba tokens` — Inspección léxica
Muestra el flujo de tokens identificados por el lexer (ideal para debugging o enseñanza de compiladores):
```bash
ucaba tokens mi_algoritmo.ucaba
```

---

## 🎨 Extensión Oficial para Visual Studio Code

El repositorio incluye la extensión oficial empaquetada en `extension-vscode/`:

<p align="center">
  <img src="payload/ucaba_logo_header.png" width="64" alt="VS Code Extension" />
</p>

### Funcionalidades:
- 🌈 **Color de Sintaxis Avanzado:** Gramática TextMate completa para palabras clave, tipos de datos, cadenas, números y comentarios (`//` y `"""`).
- 🔍 **Diagnósticos en Tiempo Real (Linter):** Muestra advertencias y errores de tipos directamente en el editor con subrayados rojos y panel de problemas.
- ▶️ **Botón "Ejecutar UCABA":** Botón de reproducción integrado en la barra de herramientas del editor para ejecutar el archivo actual con un clic.
- ⚡ **Snippets Rápidos:** Escribe `func`, `proc`, `para`, `mientras`, `si` o `archivo` y presiona <kbd>Tab</kbd> para generar plantillas de código instantáneas.

---

## 💎 Sistema de Tipos (Fuertemente Tipado)

UCABA implementa un sistema de tipos riguroso que previene errores lógicos comunes en tiempo de compilación/análisis estático.

### Tabla de Tipos Primitivos

| Tipo | Equivalente | Descripción | Ejemplo de Declaración |
| :--- | :--- | :--- | :--- |
| `ENTERO` | `int64` | Números enteros con signo | `ENTERO edad = 25` |
| `FLOTANTE` | `float32` | Punto flotante de 32 bits (IEEE 754) | `FLOTANTE tasa = 0.05` |
| `REAL` | `float64` | Punto flotante de doble precisión (64 bits) | `REAL sueldo = 1250450.75` |
| `CADENA` | `string` | Texto entre comillas dobles o simples | `CADENA nombre = "Facundo"` |
| `CARACTER` | `char` | Carácter individual | `CARACTER letra = 'A'` |
| `BOOLEANO` | `boolean` | Valor de verdad: `VERDADERO` o `FALSO` | `BOOLEANO activo = VERDADERO` |
| `ARCHIVO` | `Handle` | Descriptor para lectura/escritura de archivos | `ARCHIVO f = ABRIR_ARCHIVO("datos.txt", "lectura")` |
| `VOID` | `void` | Utilizado en procedimientos sin retorno | `PROCEDIMIENTO saludar() ...` |

> [!IMPORTANT]
> **Diferencia entre `FLOTANTE` y `REAL`:**
> `FLOTANTE` trunca deliberadamente la mantisa a 32 bits conforme a la especificación estándar IEEE 754, mientras que `REAL` preserva 64 bits de precisión total para cálculos científicos o financieros.

### Vectores y Matrices

Los arreglos son tipados y cuentan con propiedades de introspección:

```text
// Vectores unidimensionales
ENTERO edades[] = [18, 21, 30, 42]
REAL promedios[5] = [8.5, 9.0, 7.2, 10.0, 6.8]

// Matrices bidimensionales (filas x columnas)
REAL matriz[12][30]
ENTERO identidad[2][2] = [[1, 0], [0, 1]]

// Propiedad .largo
IMPRIMIR(edades.largo)       // 4 (cantidad de elementos)
IMPRIMIR(matriz.largo)       // 12 (cantidad de filas)
IMPRIMIR(matriz[0].largo)    // 30 (cantidad de columnas)
```

### Reglas de Conversión y Concatenación

1. **Concatenación de Cadenas Polimórfica:**
   Al usar el operador `+` con al menos un operando de tipo `CADENA`, el otro operando es convertido a texto automáticamente:
   ```text
   IMPRIMIR("El sueldo total es: $" + sueldo)
   IMPRIMIR("Estado activo: " + activo)  // Muestra: Estado activo: VERDADERO
   ```
2. **Concatenación de Arreglos:**
   Dos vectores del mismo tipo pueden unirse con el operador `+`:
   ```text
   ENTERO grupo_a[] = [1, 2]
   ENTERO grupo_b[] = [3, 4]
   ENTERO grupo_total[] = grupo_a + grupo_b // [1, 2, 3, 4]
   ```
3. **Promoción Numérica:**
   `ENTERO` se promueve automáticamente a `REAL` o `FLOTANTE` en operaciones matemáticas mixtas.

---

## 📜 Sintaxis y Gramática Canónica

### 1. Estructura General del Programa

Los programas pueden envolverse en un bloque `INICIO ... FIN` o declarar funciones y lógica directamente en el archivo:

```text
INICIO
    // Código principal
    IMPRIMIR("¡Hola, mundo desde UCABA!")
FIN
```

*Comentarios soportados:*
```text
// Este es un comentario de una sola línea

"""
Este es un bloque de comentarios
multilínea o documentación de algoritmo.
"""
```

---

### 2. Funciones y Procedimientos

- **Función (con valor de retorno tipado):**
  ```text
  FUNCION calcular_promedio(nota1: REAL, nota2: REAL): REAL
      REAL promedio = (nota1 + nota2) / 2
      RETORNAR promedio
  FIN FUNCION
  ```

- **Procedimiento (sin valor de retorno):**
  ```text
  PROCEDIMIENTO mostrar_bienvenida(usuario: CADENA)
      IMPRIMIR("==============================")
      IMPRIMIR(" Bienvenido al sistema, " + usuario)
      IMPRIMIR("==============================")
  FIN PROCEDIMIENTO
  ```

---

### 3. Estructuras de Control

#### Condicional `SI` / `SINO SI` / `SINO`
```text
SI (edad >= 18 Y tiene_licencia == VERDADERO)
    IMPRIMIR("Habilitado para conducir.")
SINO SI (edad >= 16)
    IMPRIMIR("Permiso especial requerido.")
SINO
    IMPRIMIR("No habilitado.")
FIN SI
```

#### Bucle `PARA`
```text
PARA (ENTERO i = 0; i < 5; i++)
    IMPRIMIR("Iteración número: " + i)
FIN PARA
```

#### Bucle `MIENTRAS`
```text
ENTERO contador = 10
MIENTRAS (contador > 0)
    IMPRIMIR("Cuenta regresiva: " + contador)
    contador--
FIN MIENTRAS
```

#### Bucle `HACER ... MIENTRAS`
```text
ENTERO intentos = 0
HACER
    intentos++
    IMPRIMIR("Intento actual: " + intentos)
MIENTRAS (intentos < 3)
FIN HACER
```

---

### 4. Manejo de Archivos (`ARCHIVO`)

UCABA ofrece manejo estructurado de flujos de texto:

```text
// Apertura en modo "lectura", "escritura" o "anexo"
ARCHIVO nomina = ABRIR_ARCHIVO("nomina.txt", "lectura")

MIENTRAS NO nomina.findearchivo
    CADENA linea = nomina.LEER_LINEA()
    IMPRIMIR("Registro leído: " + linea)
FIN MIENTRAS

nomina.CERRAR_ARCHIVO()
```

Para escribir archivos:
```text
ARCHIVO salida = ABRIR_ARCHIVO("resultados.txt", "escritura")
salida.ESCRIBIR_LINEA("INFORME FINAL")
salida.ESCRIBIR_LINEA("Total procesado: $540000.00")
salida.CERRAR_ARCHIVO()
```

---

### 5. Funciones Incorporadas (Built-ins)

| Función | Parámetros | Tipo Retorno | Descripción |
| :--- | :--- | :--- | :--- |
| `IMPRIMIR(...)` | Uno o varios valores | `VOID` | Muestra valores en la salida estándar. |
| `ABRIR_ARCHIVO(ruta, modo)` | `CADENA`, `CADENA` | `ARCHIVO` | Abre un archivo en `"lectura"`, `"escritura"` o `"anexo"`. |
| `ESPAR(numero)` | `ENTERO` o `REAL` | `BOOLEANO` | Retorna `VERDADERO` si el número es par. |
| `ESIMPAR(numero)` | `ENTERO` o `REAL` | `BOOLEANO` | Retorna `VERDADERO` si el número es impar. |
| `MOD(dividendo, divisor)` | Numéricos | `ENTERO` | Retorna el resto de la división entera. |

---

## 💡 Ejemplo Completo de Algoritmo

A continuación, un ejemplo completo de algoritmo que procesa nóminas y calcula porcentajes:

```text
// Archivo: calcular_sueldos.ucaba

FUNCION sumar_sueldos(montos[]: REAL): REAL
    REAL acumulado = 0
    PARA (ENTERO i = 0; i < montos.largo; i++)
        acumulado += montos[i]
    FIN PARA
    RETORNAR acumulado
FIN FUNCION

FUNCION calcular_porcentaje(porcion: REAL, total: REAL): REAL
    SI (total == 0)
        RETORNAR 0.0
    FIN SI
    RETORNAR (porcion * 100.0) / total
FIN FUNCION

PROCEDIMIENTO imprimir_informe(empleados[]: CADENA, sueldos[]: REAL)
    REAL total_pagado = sumar_sueldos(sueldos)
    
    IMPRIMIR("========================================")
    IMPRIMIR("   LIQUIDACIÓN MENSUAL DE SUELDOS       ")
    IMPRIMIR("========================================")
    IMPRIMIR("Total erogado: $" + total_pagado)
    IMPRIMIR("")

    PARA (ENTERO i = 0; i < empleados.largo; i++)
        REAL tasa = calcular_porcentaje(sueldos[i], total_pagado)
        IMPRIMIR("• " + empleados[i] + " -> $" + sueldos[i] + " (" + tasa + "%)")
    FIN PARA
FIN PROCEDIMIENTO

INICIO
    CADENA equipo[3] = ["Lucía Mendez", "Martín Palermo", "Julieta Rossi"]
    REAL salarios[3] = [580000.0, 720000.0, 640000.0]

    imprimir_informe(equipo, salarios)
FIN
```

---

## 🔢 Ordenar una Matriz (Selection Sort)

La función `ordenar_matriz` recibe una matriz de `ENTERO` por parámetro, la ordena de menor a mayor con el algoritmo **Selection Sort** y **retorna la matriz ordenada**. La matriz original no se modifica.

```text
FUNCION ordenar_matriz(matriz[][]: ENTERO): ENTERO[][]
    ENTERO filas = matriz.largo
    ENTERO columnas = matriz[0].largo
    ENTERO total = filas * columnas

    // 1. Aplanar la matriz en un vector (recorrido por filas)
    ENTERO elementos[total]
    ENTERO posicion = 0
    PARA (ENTERO f = 0; f < filas; f++)
        PARA (ENTERO c = 0; c < columnas; c++)
            elementos[posicion] = matriz[f][c]
            posicion++
        FIN PARA
    FIN PARA

    // 2. Selection Sort sobre el vector
    PARA (ENTERO i = 0; i < total - 1; i++)
        ENTERO indice_minimo = i
        PARA (ENTERO j = i + 1; j < total; j++)
            SI (elementos[j] < elementos[indice_minimo])
                indice_minimo = j
            FIN SI
        FIN PARA

        SI (indice_minimo != i)
            ENTERO auxiliar = elementos[i]
            elementos[i] = elementos[indice_minimo]
            elementos[indice_minimo] = auxiliar
        FIN SI
    FIN PARA

    // 3. Reconstruir la matriz ordenada (la original no se modifica)
    ENTERO resultado[filas][columnas]
    posicion = 0
    PARA (ENTERO f = 0; f < filas; f++)
        PARA (ENTERO c = 0; c < columnas; c++)
            resultado[f][c] = elementos[posicion]
            posicion++
        FIN PARA
    FIN PARA

    RETORNAR resultado
FIN FUNCION

INICIO
    ENTERO datos[3][3] = [[9, 4, 7], [1, 8, 2], [6, 3, 5]]
    ENTERO ordenada[][] = ordenar_matriz(datos)

    PARA (ENTERO f = 0; f < ordenada.largo; f++)
        IMPRIMIR(ordenada[f])
    FIN PARA
FIN
```

**Salida:**
```text
[1, 2, 3]
[4, 5, 6]
[7, 8, 9]
```

| Elemento | Detalle |
| :--- | :--- |
| **Parámetro** | `matriz[][]: ENTERO` — matriz de enteros de cualquier tamaño (`filas x columnas`). |
| **Retorno** | `ENTERO[][]` — nueva matriz con las mismas dimensiones y todos sus elementos en orden ascendente por filas. |
| **Algoritmo** | Selection Sort: en cada pasada se busca el mínimo del tramo sin ordenar y se intercambia con la posición actual. |
| **Complejidad** | `O(n²)` con `n = filas * columnas`. |

> [!NOTE]
> Como UCABA no tiene división entera (`/` siempre devuelve `REAL`), la matriz se aplana a un vector para poder ordenarla con índices enteros y luego se reconstruye. Para ordenar de mayor a menor, cambia la comparación a `elementos[j] > elementos[indice_minimo]`.

---

## 🧪 Pruebas Automatizadas

La suite de pruebas unitarias evalúa exhaustivamente el lexer, parser, verificador de tipos y runtime:

```bash
# Ejecutar toda la batería de tests unitarios
python -m unittest discover tests
```

**Cobertura de pruebas:**
- ✅ Tipado estático y compatibilidad numérica float32/float64.
- ✅ Bucle `PARA`, `MIENTRAS`, `HACER ... MIENTRAS`.
- ✅ Recursión, algoritmos de ordenamiento (Quicksort) y matrices.
- ✅ Manejo de archivos y bucles de lectura sin fin de archivo.
- ✅ Todas las estructuras canónicas definidas en `estructuras.txt`.

---

## 👤 Autoría y Créditos

<div align="center">

| Concepto | Detalle |
| :--- | :--- |
| **Lenguaje** | **UCABA** (Pseudocódigo Fuertemente Tipado) |
| **Autor** | **[Facu Falcone](mailto:a.facundo.falcone@gmail.com)** |
| **Repositorio** | `Python_d/UCABA_Lang` |
| **Licencia** | [GNU General Public License v3.0 (GPL-3.0-or-later)](./LICENSE) |
| **Copyright** | © 2026 Facu Falcone. All rights reserved. |

</div>

---

## 📜 Licencia

Este proyecto está licenciado bajo los términos de la **GNU General Public License v3.0 (GPL-3.0-or-later)**.
Garantiza la libertad de uso, estudio, modificación y redistribución del software, protegiendo los derechos de autoría y asegurando que cualquier obra derivada permanezca libre y de código abierto (copyleft fuerte).

Para más detalles, consulte el archivo [LICENSE](./LICENSE).

<p align="center">
  Diseñado con dedicación para impulsar la enseñanza y la práctica rigurosa de la algoritmia. 🚀
</p>

