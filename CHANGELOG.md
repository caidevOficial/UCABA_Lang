# Registro de Cambios (Changelog) - UCABA

Todos los cambios notables en el lenguaje de programación y compilador **UCABA** serán documentados en este archivo.
El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/) y este proyecto se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

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
  - Limpieza de paquetes `.vsix` obsoletos en `extension-vscode/`, conservando únicamente la versión activa `1.9.0`.

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
