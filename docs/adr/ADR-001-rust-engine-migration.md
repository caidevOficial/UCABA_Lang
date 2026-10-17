# ADR-001: Migración del Motor de UCABA de Python a Rust Nativo (UCABA 2.0)

## Estado
Aceptado (En progreso para v2.0.0-alpha)

## Contexto
El lenguaje UCABA (versión 1.x) fue desarrollado como un intérprete en Python estructurado en:
- `pseudocode/lexer.py`
- `pseudocode/parser.py`
- `pseudocode/type_checker.py`
- `pseudocode/interpreter.py`

Si bien la implementación en Python permitió una rápida iteración didáctica y la validación de la gramática, presenta limitaciones estructurales para programas de mayor escala y rendimiento:
1. **Rendimiento de Ejecución**: En algoritmos de ordenamiento o cómputo matricial (como `sort.ucaba`), el recorrido de AST en CPython introduce un overhead significativo (3.24 segundos para ordenar un arreglo mediano).
2. **Tiempo de Arranque (Cold Start)**: El binario empaquetado con PyInstaller requiere entre 150ms y 300ms solo para inicializar el runtime de CPython antes de evaluar la primera línea.
3. **Consumo de Memoria**: Un proceso simple consume entre 35MB y 50MB de RAM.
4. **Distribución y Dependencias**: El empaquetado de ejecutables multiplataforma requiere encapsular el entorno CPython completo (~20MB por binario).

## Decisión
Reimplementar el motor de ejecución y análisis estático de UCABA en **Rust**, estructurando el repositorio como un **Workspace de Cargo**:

1. **`crates/ucaba_core`**: Librería pura en Rust con:
   - **Lexer**: Tokenización de alta velocidad mediante autómatas deterministas con `logos`.
   - **Parser**: Parser descendente recursivo con recuperación de errores y soporte de modo estricto y modo permisivo (`lenient`).
   - **TypeChecker**: Sistema de tipos estático unificado (`ENTERO`, `FLOTANTE`, `REAL`, `BOOLEANO`, `CADENA`, `CARACTER`, `ARCHIVO`, `TIPO[]`, `TIPO[][]`, `Estructura`, `NULO`).
   - **Evaluator**: Intérprete nativo en Rust con valores fuertemente tipados (`i64`, `f64`, `f32`, `bool`, `String`, etc.) sin boxing innecesario.
2. **`crates/ucaba_cli`**: Binario CLI nativo `ucaba`:
   - Interfaz con `clap` respetando todas las banderas canónicas (`run`, `check`, `--time`, `--time-full`, `--version`, `--help`).
   - Salida formateada de mediciones de tiempo de alta resolución.
   - Saludo institucional fucsia `#d946ef` idéntico a v1.x.

## Consecuencias

### Positivas
- **Aceleración Masiva**: Reducción de tiempos de ejecución entre 50x y 200x.
- **Arranque Instantáneo**: De ~250ms a < 5ms.
- **Binario Nativo Autónomo**: Un único archivo binario estático de ~4-8MB sin dependencias de Python ni librerías dinámicas del sistema.
- **Consumo de Memoria Mínimo**: De ~45MB a < 5MB de RAM.
- **Preparación para WebAssembly**: `ucaba_core` podrá compilarse a `wasm32-unknown-unknown` para integrarse directamente en la extensión de VS Code sin requerir procesos externos.

### Negativas / Mitigaciones
- Necesidad de mantener paridad estricta con la especificación de UCABA 1.x.
  - *Mitigación*: Se utiliza la suite de 52 tests existentes y snapshot testing (`insta`) contra el intérprete Python.
- Curva de implementación en estructuras autorreferenciales.
  - *Mitigación*: Uso de identificadores por índices (`NodeId`) o `Option<Box<StructInstance>>` con inicialización automática a `NULO`.
