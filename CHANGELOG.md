# Registro de Cambios (Changelog) - UCABA

Todos los cambios notables en el lenguaje de programación y compilador **UCABA** serán documentados en este archivo.
El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [2.0.0] - 2026-10-17

### 🚀 Nuevo Motor Nativo en Rust (Workspace Cargo)
- **Migración Arquitectónica Completa:** Creación de un workspace en Rust compuesto por:
  - `crates/ucaba_core`: Motor central que contiene el lexer (`lexer.rs`), AST tipado (`ast.rs`), parser recursivo descendente (`parser.rs`), comprobación estricta de tipos (`eval.rs`), e intérprete de ejecución directa sin runtime externo.
  - `crates/ucaba_cli`: CLI nativo multiplataforma (`ucaba`) con subcomandos `run`, `repl`, `check`, `lsp-check` y flags de tiempo `--time` y `--time-full`.
  - `crates/ucaba_installer`: Asistente GUI autónomo para Windows desarrollado con `eframe`/`egui`, tema Dark Magenta institucional y soporte High-DPI.
- **Rendimiento Revolucionario:**
  - Tiempo de arranque en frío (*Cold Start*): **<1 ms** (~250x más rápido).
  - Ejecución de algoritmos: QuickSort ordenando arreglos en **1 ms** frente a **3.240 ms** en Python (~300x más rápido).
  - Huella de memoria mínima: **< 5 MB RAM** (90% menor consumo).
  - Binario autónomo: **0.83 MB** sin DLLs ni runtime externo (90% más liviano que los 7.8 MB previos).

### 💻 Consola Interactiva REPL (`ucaba repl`)
- **Evaluación Didáctica en Tiempo Real:** Subcomando `ucaba repl` (y ejecución por defecto al invocar `ucaba` sin argumentos) con evaluación de expresiones instantánea (`=> <valor>`).
- **Buffer Multilínea Inteligente:** Función `is_input_complete` con stack de bloques léxicos para admitir sentencias multilínea (`FUNCION`, `SI-SINO`, bucles) y prompt alternado (`ucaba> ` / `...    `).
- **Metacomandos:** `:ayuda`, `:variables` (tabla ASCII estilizada con anchos dinámicos), `:limpiar`, `:cancel` y `:salir`.

### 🧩 Extensión Oficial de Visual Studio Code y Antigravity IDE (v2.0.0)
- **Diagnósticos Sub-milisegundo:** Consumo directo del comando `ucaba lsp-check --json --stdin`, eliminando toda dependencia de Python para el linter en tiempo real.
- **Comando REPL Integrado:** Nuevo comando `UCABA: Iniciar consola interactiva REPL` (`ucaba.startRepl`) accesible desde paleta de comandos y botones de navegación.
- **Detección Automática de Binarios:** Detección de binarios en workspace local (`target/release/ucaba`), `%LOCALAPPDATA%` en Windows y `/usr/local/bin` en Linux/macOS.
- **Resaltado de Sintaxis Completo:** Gramática TextMate actualizada para reconocer tipos personalizados de `ESTRUCTURA` (`entity.name.type.struct.ucaba`), operadores `++` y `--`, palabras reservadas y literales.
- **Inspección y Hover Sin Fallos:** Reparación del parser de contexto léxico en `isInCommentOrString` admitiendo comentarios estilo `#`, habilitando la inspección hover de variables y funciones en cualquier contexto de código.
- **Tema de Iconos Integrado:** Nuevo tema de iconos oficial (`ucaba-icon-theme.json`) aportado vía `iconThemes` y activación por workspace (`workspaceContains:**/*.ucaba`), dotando a los módulos `.ucaba` de su icono magenta en el árbol de archivos.
- **Nuevo Paquete VSIX y Despliegue Robusto:** Publicación de `ucaba-language-support-2.0.0.vsix` embebido en el instalador; actualización de `install_extension.py` para depurar `.obsolete` y registrar formalmente la extensión en `extensions.json` en VS Code, Cursor y Antigravity IDE.

### 🎨 Iconos y Asociación de Archivos Multiplataforma
- **Windows:** Registro dual de ProgIDs (`UCABAFile` y `UCABA.Program`) con clave `DefaultIcon`, sincronización con `OpenWithProgids` en el registro de Windows y emisión de `SHCNE_ASSOCCHANGED` para refresco instantáneo del explorador.
- **Linux:** Adición de iconos MIME en `icons/hicolor/256x256/mimetypes/` (`application-x-ucaba.png` y `text-x-ucaba.png`) en paquetes `.deb` y script `install.sh`.
- **Publicación Pre-release:** Automatización de GitHub Actions configurada expresamente para publicar la release `v2.0.0` como pre-release (`prerelease: true`).

### 🧪 Suite Exhaustiva de Paridad de Pruebas (72 Tests en Rust)
- **100% de Paridad Certificada:** Porting y ampliación de todos los casos de prueba de Python a suites nativas en Rust (`test_engine.rs`, `test_operators.rs`, `test_estructuras.rs`, `test_interpreter.rs`, `test_cli.rs`, `ucaba_installer::tests`).
- **Verificación Estricta de Tipos:** Validación estática en tiempo de ejecución de asignaciones y retornos, precisión simple de 32 bits para `FLOTANTE` vs doble de 64 bits para `REAL`.
- **Auditoría de Código:** `cargo clippy --workspace -- -D warnings` con **0 advertencias**.

### 🖼️ Asistente de Instalación Gráfico Nativo (`Instalador_UCABA.exe`)
- **GUI Moderna y Autónoma en Rust:** Reemplazo completo de la interfaz basada en Tkinter/PyInstaller por una aplicación nativa escrita en Rust (`eframe`/`egui`).
- **Reducción de Tamaño Masiva:** El ejecutable del instalador pasa de ~18 MB a **5.05 MB** (72% más liviano) incluyendo todos los recursos embebidos en el binario: `ucaba.exe` compilado, `ucaba_icon.ico` y la extensión `ucaba-language-support-2.0.0.vsix`.
- **Migración Fluida y Resiliente desde Python/PyInstaller:** Ruptura de herencia de entorno y handles (`_MEIPASS2`) para evitar avisos de borrado de temporales, manejo resiliente contra bloqueos de archivos en Windows (`os error 32`) con reintentos y reemplazo atómico (*Move-then-Replace*), y purga automática de carpetas temporales residuales `_MEI*` en `%TEMP%`.
- **Instalación Desatendida:** Soporte para flag `--silent` para automatización en entornos de laboratorio o CI/CD.
- **Metadatos e Iconos Nativos Windows PE:** Integración con `winres`, incrustando el icono institucional y metadatos de versión en el recurso PE de Windows.

---

## [1.11.6] - 2026-10-17

> Esta versión es la primera publicada desde la `1.11.0` e **incluye también los cambios de la `1.11.5`** (iconos de archivos `.ucaba`, empaquetado Linux y pruebas de `build_linux_package.py`), detallados más abajo.

### 📖 Documentación del Lenguaje
- **Operadores aritméticos**: nueva tabla de operadores en el `README.md` (`+`, `-`, `*`, `/`, `//`, `%`) con tipo de retorno, ejemplos y la diferencia entre `/` (división real) y `//` (división entera, siempre `ENTERO`).
- **División entera (`//`)**: se elimina la nota obsoleta que indicaba que UCABA no tenía división entera; el ejemplo de *Selection Sort* ahora usa `//` y `%` para recorrer la matriz sin aplanarla.
- **Medición de tiempo (`--time`, `--time ms`, `--time full`, `--time completo`, `--time-full`)**: documentación unificada con tabla de modos, ejemplos y salidas esperadas en el `README.md` y en la especificación del lenguaje.
- **Cobertura de pruebas**: el badge del `README.md` refleja los 52 tests unitarios actuales.
- **Extensión VS Code**: el `README.md` de la extensión documenta el resaltado de `//`, `%` y `#` y el icono de archivos `.ucaba`.

### 🐛 Correcciones del Lenguaje y CLI
- **Comprobación explícita de actualizaciones (`ucaba update --check`)**: `check_for_update` utilizaba el archivo de caché local (con TTL de 6 horas) sin consultar la API de GitHub cuando el usuario solicitaba expresamente verificar si había una nueva versión. Se implementó `check_version_status` con `force_online=True`, asegurando que `ucaba update --check` y `ucaba upgrade --check` verifiquen siempre en vivo contra GitHub Releases y reporten errores de conectividad claramente.
- **División entera dentro de índices**: expresiones como `matriz[p // columnas][p % columnas] = valor` (o `v[n // 2]`) ya no se interpretaban como división entera sino como comentario, provocando un `ParseError`. El lexer ya no aplica la heurística de "declaración + comentario" dentro de corchetes o paréntesis sin cerrar. Se añade `test_division_entera_dentro_de_indices` a `tests/test_operators.py`.

### 🎨 Iconos y Empaquetado Oficial
- **Iconos de archivos `.ucaba`**:
  - **Extensión VS Code / Antigravity / Cursor**: se declara el icono de lenguaje (`contributes.languages[].icon`) con `icons/ucaba-file.png`, de modo que los archivos `.ucaba` muestran el logo de UCABA en el explorador y en las pestañas (al estilo de Python o Rust).
  - **Windows**: el instalador notifica al Explorador (`SHChangeNotify`) tras registrar la asociación para refrescar el icono sin reiniciar el sistema.
  - **Linux**: el tipo MIME usa el nombre estándar `application-x-ucaba` y se instala el icono bajo ese nombre; se refresca la caché de iconos (`gtk-update-icon-cache`) en `install.sh`, `uninstall.sh`, `postinst` y `postrm`.
- **Constructor de paquetes Linux (`build_linux_package.py`)**:
  - Generación de ejecutables ZipApp standalone universales, paquetes `.deb` y `.tar.gz` con validación estricta de binarios reales y suite de pruebas en `tests/test_build_linux_package.py`.

### 🚀 Release y CI
- **Notas de release (`generate_release_notes.py`)**: se elimina `shell=True` en las llamadas a `git`, que en Linux (runner `ubuntu-latest`) impedía obtener el registro de commits desde el último tag. Ahora cada release incluye las novedades de esta sección del CHANGELOG y la lista de commits reales.
- **Versionado**: sincronización de la versión `1.11.6` en intérprete, instaladores, metadatos de Windows, paquetes Linux y extensión (`ucaba-language-support-1.11.6.vsix`).

---

## [1.11.5] - 2026-10-17

### 🎨 Iconos de archivos .ucaba
- **Extensión VS Code / Antigravity / Cursor**: se declara el icono de lenguaje (contributes.languages[].icon) con icons/ucaba-file.png, de modo que los archivos .ucaba muestran el logo de UCABA en el explorador y en las pestañas (igual que Python o Ruby).
- **Windows**: el instalador notifica al Explorador (SHChangeNotify) tras registrar la asociación para refrescar el icono sin reiniciar.
- **Linux**: el tipo MIME usa el nombre estándar `application-x-ucaba` y se instala el icono bajo ese nombre; se refresca la caché de iconos (gtk-update-icon-cache) en install.sh, uninstall.sh, postinst y postrm.

---

## [1.11.0] - 2026-10-16

### ➗ Operadores Aritméticos y Gramática
- **Operador de División Entera (`//`)**:
  - Soporte completo del operador infijo `//` en el analizador léxico (`Lexer`), sintáctico (`Parser`), verificador de tipos (`TypeChecker`) e intérprete (`Interpreter`).
  - Retorno garantizado de tipo `ENTERO` con chequeo estático estricto para operandos numéricos y control de división por cero.
  - Desambiguación léxica inteligente: convivencia transparente entre expresiones con división entera `//` y comentarios de línea con `//`.
- **Operador de Módulo (`%`)**:
  - Soporte infijo oficial del símbolo `%` para calcular el residuo/resto de una división entera (equivalente a la función incorporada `MOD(a, b)`).
  - Validación de tipos estricta y protección contra módulo por cero en tiempo de ejecución.
- **Soporte de Comentarios de Línea con Numeral (`#`)**:
  - Se añade `#` como delimitador de comentarios de línea unificado, compatible con la convención de Python y entornos scripting.
- **Suite de Pruebas Unitarias**:
  - Creación de `tests/test_operators.py` cubriendo precedencia, llamadas a funciones, arrays, excepciones por cero y coexistencia sintáctica con comentarios (43 tests unitarios superados).
- **Extensión VS Code**:
  - Actualización de la sintaxis TextMate (`ucaba.tmLanguage.json`) para resaltar `//`, `%` y `#`.

---

## [1.10.0] - 2026-10-16

### 🐧 Soporte Oficial y Empaquetado para GNU/Linux
- **Paquete Nativo Debian / Ubuntu (`.deb`)**:
  - Generación de `ucaba_<version>_amd64.deb` con instalación de binario en `/usr/bin/ucaba`, registro de tipo MIME `application/x-ucaba` para archivos `.ucaba`, iconos en tema de sistema (`hicolor/256x256`) y acceso directo de escritorio (`ucaba.desktop`).
  - Scripts de control `postinst` y `postrm` con actualización automática de bases de datos de escritorio y MIME, junto con registro automático de la extensión si VS Code o Cursor están presentes.
- **Tarball Standalone Universal (`.tar.gz`)**:
  - Generación de `ucaba-<version>-linux-x64.tar.gz` compatible con cualquier distribución Linux (Arch, Fedora, Debian, etc.), incluyendo binario ELF nativo, scripts `install.sh` y `uninstall.sh` con detección automática de permisos (root vs usuario en `~/.local/bin`), paquete VSIX y licencia.
- **Constructor Autónomo Multiplataforma (`build_linux_package.py`)**:
  - Herramienta Python capaz de generar tanto `.deb` (usando `dpkg-deb` o un ensamblador puro del formato 'ar') como `.tar.gz` de forma reproducible.
- **Integración Continua Multiplataforma (GitHub Actions)**:
  - Workflow de release actualizado para compilar en paralelo en Windows (`windows-latest`) y Linux (`ubuntu-latest`), publicando instaladores y binarios para ambas plataformas en cada release oficial.
- **Gestión Dinámica de Extensiones y Limpieza de VSIX**:
  - Refactorización de `install_extension.py` para purgar dinámicamente versiones anteriores obsoletas mediante coincidencia de patrones.
  - Limpieza de paquetes `.vsix` obsoletos en `extension-vscode/`, conservando únicamente la versión activa `1.10.0`.
- **Extensión VS Code v1.10.0**:
  - Empaquetado y actualización de `ucaba-language-support-1.10.0.vsix`.

---

## [1.9.0] - 2026-10-16

### 🚀 Rendimiento y Optimización de Algoritmos
- **Optimización de Quicksort ($O(N \log N)$)**:
  - Implementación con selección de **pivote central** (`medio = vector.largo / 2`), evitando la degradación al peor caso cuadrático $O(N^2)$ en vectores ordenados o invertidos.
  - Partición balanceada de 3 vías (menores, iguales y mayores) que preserva elementos repetidos y elimina pasadas redundantes sobre el vector.
  - Capaz de ordenar **100.000 elementos** en ~37 segundos en el intérprete sin desbordamiento.
- **Ampliación de Límite de Recursión (`sys.setrecursionlimit(50000)`)**:
  - Pila de llamadas recursivas ampliada a 50.000 frames en el motor del intérprete para admitir algoritmos de árboles, grafos y particiones recursivas profundas sin colapsar el límite por defecto de Python.
- **Validación Acelerada de Vectores (*Fast-Path*)**:
  - En `pseudocode/types_system.py`, se implementó validación rápida para vectores numéricos y homogéneos evitando clonaciones profundas innecesarias en llamadas y retornos de funciones recursivas.
- **Diagnóstico Educativo de `RecursionError`**:
  - Captura limpia y mensaje formativo en la CLI ante recursiones infinitas o casos base inalcanzables.

### 📖 Documentación y CLI
- **Documentación Completa de `--time`**:
  - Inclusión en `--help` y `README.md` de las opciones `--time ms` (tiempo de ejecución en milisegundos) y `--time full` / `--time-full` (desglose legible en horas, minutos, segundos y milisegundos).
- **Extensión VS Code v1.9.0**:
  - Empaquetado y actualización de `ucaba-language-support-1.9.0.vsix`.
- **Automatización de Release Notes**:
  - Integración dinámica de novedades por versión en `release_notes.md` y notas de release en GitHub generadas desde `CHANGELOG.md`.

---

## [1.8.0] - 2026-10-16

### ⏱️ Interfaz de Línea de Comandos (CLI)
- **Medición de Tiempo Detallada (`--time full` / `--time-full`)**:
  - Desglose con precisión en horas, minutos, segundos y milisegundos con concordancia singular/plural (ej: `[Tiempo total: 1 Hora, 15 Minutos, 30 Segundos, 45 Milisegundos]`).
- **Compatibilidad Dual de `--time`**:
  - `--time` o `--time ms` mantiene la salida tradicional en milisegundos (`[Tiempo total: 211.22 ms]`).
- **Normalización de Argumentos CLI**:
  - Soporte para ubicar `--time [modo]` en cualquier posición de la línea de comandos sin interferir con el argumento posicional obligatorio `file`.
- **Suite de Pruebas CLI**:
  - Pruebas unitarias en `tests/test_cli_time.py` para validar normalización de argumentos y formateo gramatical de tiempo.

---

## [1.7.0] - 2026-10-16

### 💡 IDE y Experiencia de Desarrollo
- **Autocompletado e IntelliSense por Punto (`.`) en VS Code / Antigravity**:
  - Al escribir un punto (`.`) sobre variables de estructura, despliega la lista de atributos con sus tipos y documentación.
  - Soporte de autocompletado para el tipo `ARCHIVO`: métodos `LEER_LINEA()`, `ESCRIBIR_LINEA()`, `CERRAR_ARCHIVO()` y propiedad `findearchivo`.
  - Soporte recursivo para estructuras encadenadas y listas de estructuras.

---

## [1.6.1] - 2026-10-16

### 🎨 Identidad Visual
- **Banner Comunitario Institucional**:
  - Estilizado en color fucsia corporativo oficial de UCABA (#d946ef).

---

## [1.6.0] - 2026-10-16

### ✨ Nuevas Características
- **Estructuras de Datos Heterogéneas (`ESTRUCTURA ... FIN ESTRUCTURA`)**:
  - Definición de tipos compuestos por el usuario con múltiples atributos tipados.
  - Creación de vectores y matrices de estructuras (`Libro estante[10]`).
  - Serialización directa `Libro{nombre: '...', hojas: 350}`.
- **Tipo de Dato y Literal Universal `NULO` (`null` / `None`)**:
  - Manejo de referencias nulas y comparaciones seguras de punteros.
- **Estructuras Autorreferenciales**:
  - Creación de nodos para listas enlazadas, pilas y colas.
- **Actualizador Automático (`ucaba update`)**:
  - Notificación en segundo plano (estilo `pip`) y actualización automatizada contra GitHub Releases.
