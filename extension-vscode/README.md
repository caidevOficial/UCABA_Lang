# UCABA - Soporte Oficial para Visual Studio Code

Extensión oficial para **Visual Studio Code** y **Antigravity IDE** que brinda soporte completo para el lenguaje de programación **UCABA** (archivos `.ucaba`).

## Características

- ⚡ **Diagnósticos Instantáneos (< 1 ms)**: Integración nativa con el motor v2.0 en Rust (`ucaba lsp-check --json --stdin`), detectando errores de sintaxis y tipos estáticos en tiempo real mientras escribes sin retardos.
- 💻 **Consola Interactiva REPL Integrada**: Ejecuta `UCABA: Iniciar consola interactiva REPL` desde la paleta de comandos o desde el botón en la barra superior para probar expresiones, funciones y algoritmos al instante.
- 🎨 **Coloreado de Sintaxis Completo**: Palabras clave (`INICIO`, `FIN`, `FUNCION`, `RETORNAR`, `SI`, `PARA`, `MIENTRAS`), tipos de datos (`ENTERO`, `FLOTANTE`, `REAL`, `CADENA`, etc.), operadores (incluida la división entera `//` y el módulo `%`) y comentarios (`//`, `#`, `/* */`).
- 🖼️ **Icono de archivo `.ucaba`**: Los archivos del lenguaje muestran el logo de UCABA en el explorador y en las pestañas.
- 💡 **Autocompletado Inteligente (IntelliSense)**:
  - Tipos y palabras reservadas.
  - Funciones incorporadas (`MOSTRAR`, `LEER`, `MOD`, `ESPAR`, `ESIMPAR`, `ABRIR_ARCHIVO`, etc.).
  - Propiedad `.largo` para vectores, matrices y cadenas.
- 📖 **Documentación al pasar el cursor (Hover)**: Explicación de tipos, rangos de bits, sintaxis y firmas de funciones integradas.
- ⚡ **Snippets Integrados**: Plantillas rápidas para `algoritmo`, `funcion`, `si`, `sisino`, `para`, `mientras`, `vector`, `matriz`, `leer_archivo`.
- 🔗 **Ir a Definición (Go to Definition - `Ctrl + Clic` / `F12`)**: Al presionar `Ctrl + Clic izquierdo` (o `F12`) sobre una función en cualquier parte del código, salta instantáneamente a su definición (`FUNCION` / `PROCEDIMIENTO`).
- 🔎 **Buscar Referencias (`Shift + F12`)**: Encuentra todas las llamadas y usos de una función en el archivo.
- 📑 **Vista de Esquema (Outline) y Breadcrumbs**: Muestra el mapa de funciones en el panel lateral Esquema y permite saltar con `Ctrl + Shift + O`.
- ▶️ **Ejecución Directa**: Clic derecho en el editor -> "UCABA: Ejecutar archivo actual" o botón en la barra superior del editor.

## Requisitos

- **Motor UCABA v2.0 (Recomendado)**: El ejecutable autónomo `ucaba` (o `ucaba.exe` en Windows). No requiere instalar Python ni dependencias externas.
- **Modo Compatibilidad (Opcional)**: Python 3.8+ con el paquete `pseudocode` si no se dispone del binario nativo.

## Instalación en Visual Studio Code

### Opción 1: Automática desde la terminal (Recomendada)
Ejecuta con el comando de VS Code:
```bash
code --install-extension extension-vscode/ucaba-language-support-2.0.0.vsix --force
```

### Opción 2: Gráfica desde la interfaz de VS Code
1. Abre **Visual Studio Code**.
2. Ve al panel de **Extensiones** (`Ctrl + Shift + X`).
3. Haz clic en el menú de los **tres puntos (`...`)** en la esquina superior derecha del panel de extensiones.
4. Selecciona **"Instalar desde VSIX..."** (*Install from VSIX...*).
5. Navega a `./extension-vscode/` y selecciona el archivo `ucaba-language-support-2.0.0.vsix`.
6. En la paleta de comandos (`Ctrl + Shift + P`), escribe y selecciona **Developer: Reload Window** (o reinicia VS Code).

---

## Configuración

- `ucaba.pythonPath`: Ruta personalizada al intérprete de Python si no está en el PATH del sistema.
- `ucaba.cliPath`: Ruta explícita al ejecutable `ucaba.exe`.

---

## 👤 Autoría y Licencia

- **Autor**: [Facu Falcone](mailto:a.facundo.falcone@gmail.com)
- **Licencia**: GNU General Public License v3.0 or later (GPL-3.0-or-later)
- **Copyright**: © 2026 Facu Falcone. All rights reserved.
