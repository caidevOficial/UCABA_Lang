use ucaba_core::run_code;

#[test]
fn test_basic_arithmetic_and_print() {
    let code = r#"
    INICIO
        ENTERO a = 10
        ENTERO b = 20
        IMPRIMIR(a + b)
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["30"]);
}

#[test]
fn test_floor_division_and_modulo() {
    let code = r#"
    INICIO
        ENTERO div = 10 // 3
        ENTERO resto = 10 % 3
        IMPRIMIR("DIV:", div)
        IMPRIMIR("MOD:", resto)
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["DIV: 3", "MOD: 1"]);
}

#[test]
fn test_string_concatenation() {
    let code = r#"
    INICIO
        CADENA saludo = "Hola "
        CADENA mundo = "Mundo"
        IMPRIMIR(saludo + mundo)
        IMPRIMIR("Resultado: " + 42)
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["Hola Mundo", "Resultado: 42"]);
}

#[test]
fn test_if_else() {
    let code = r#"
    INICIO
        ENTERO edad = 18
        SI (edad >= 18)
            IMPRIMIR("Mayor")
        SINO
            IMPRIMIR("Menor")
        FIN SI
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["Mayor"]);
}

#[test]
fn test_for_loop() {
    let code = r#"
    INICIO
        ENTERO suma = 0
        PARA (ENTERO i = 1; i <= 5; i++)
            suma += i
        FIN PARA
        IMPRIMIR("TOTAL:", suma)
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["TOTAL: 15"]);
}

#[test]
fn test_while_loop() {
    let code = r#"
    INICIO
        ENTERO x = 3
        MIENTRAS (x > 0)
            IMPRIMIR(x)
            x--
        FIN MIENTRAS
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["3", "2", "1"]);
}

#[test]
fn test_function_and_recursion() {
    let code = r#"
    INICIO
        FUNCION fib(n: ENTERO): ENTERO
            SI (n < 2)
                RETORNAR n
            SINO
                RETORNAR fib(n - 1) + fib(n - 2)
            FIN SI
        FIN FUNCION

        IMPRIMIR("FIB10:", fib(10))
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["FIB10: 55"]);
}

#[test]
fn test_vectors_and_largo() {
    let code = r#"
    INICIO
        ENTERO v[] = [10, 20, 30]
        IMPRIMIR("LARGO:", v.largo)
        IMPRIMIR("PRIMERO:", v[0])
        v[1] = 99
        IMPRIMIR("MODIFICADO:", v[1])
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["LARGO: 3", "PRIMERO: 10", "MODIFICADO: 99"]);
}

#[test]
fn test_structures_basic() {
    let code = r#"
    Estructura Libro:
        CADENA nombre
        ENTERO hojas
        CADENA autor
    Fin Estructura

    Libro libro1
    libro1.nombre = "Ficciones"
    libro1.hojas = 220
    libro1.autor = "Jorge Luis Borges"

    IMPRIMIR("LIBRO:", libro1.nombre, libro1.hojas, libro1.autor)
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["LIBRO: Ficciones 220 Jorge Luis Borges"]);
}

#[test]
fn test_structures_vector() {
    let code = r#"
    Estructura Producto:
        CADENA codigo
        REAL precio
    Fin Estructura

    Producto inventario[2]
    inventario[0].codigo = "P01"
    inventario[0].precio = 99.5
    inventario[1].codigo = "P02"
    inventario[1].precio = 150.0

    IMPRIMIR("P0:", inventario[0].codigo, inventario[0].precio)
    IMPRIMIR("P1:", inventario[1].codigo, inventario[1].precio)
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["P0: P01 99.5", "P1: P02 150.0"]);
}

#[test]
fn test_structures_linked_list() {
    let code = r#"
    INICIO
        ESTRUCTURA Nodo:
            CADENA nombre
            Nodo proximo_nodo
        Fin ESTRUCTURA

        Nodo n1
        Nodo n2
        n1.nombre = "Nodo 1"
        n2.nombre = "Nodo 2"
        n1.proximo_nodo = n2

        Nodo aux = n1
        MIENTRAS aux != NULO
            IMPRIMIR("VISITANDO:", aux.nombre)
            aux = aux.proximo_nodo
        FIN MIENTRAS
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["VISITANDO: Nodo 1", "VISITANDO: Nodo 2"]);
}

#[test]
fn test_builtin_mod_espar_esimpar() {
    let code = r#"
    INICIO
        IMPRIMIR("ESPAR:", ESPAR(4), ESPAR(5))
        IMPRIMIR("ESIMPAR:", ESIMPAR(7), ESIMPAR(8))
        IMPRIMIR("MOD:", MOD(14, 3))
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec![
        "ESPAR: VERDADERO FALSO",
        "ESIMPAR: VERDADERO FALSO",
        "MOD: 2",
    ]);
}

#[test]
fn test_toplevel_functions_and_inicio_block() {
    let code = r#"
    FUNCION duplicar(n: ENTERO): ENTERO
        RETORNAR n * 2
    FIN FUNCION

    INICIO
        IMPRIMIR("DUP:", duplicar(21))
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["DUP: 42"]);
}

#[test]
fn test_archivo_read_write_and_findearchivo() {
    let tmp_path = std::env::temp_dir()
        .join("ucaba_test_archivo.txt")
        .to_str()
        .unwrap()
        .replace('\\', "/");

    let code = format!(
        r#"
    INICIO
        ARCHIVO f_out = ABRIR_ARCHIVO("{}", "escritura")
        f_out.ESCRIBIR_LINEA("12345")
        f_out.ESCRIBIR_LINEA("98.75")
        f_out.ESCRIBIR_LINEA("HOLA MUNDO")
        f_out.CERRAR_ARCHIVO()

        ARCHIVO f_in = ABRIR_ARCHIVO("{}", "lectura")
        ENTERO n = f_in.LEER_LINEA()
        REAL r = f_in.LEER_LINEA()
        CADENA s = f_in.LEER_LINEA()
        BOOLEANO eof = f_in.findearchivo
        f_in.CERRAR_ARCHIVO()

        IMPRIMIR("N:", n + 5)
        IMPRIMIR("R:", r + 1.25)
        IMPRIMIR("S:", s)
        IMPRIMIR("EOF:", eof)
    FIN
    "#,
        tmp_path, tmp_path
    );

    let output = run_code(&code, false).unwrap();
    assert_eq!(output, vec![
        "N: 12350",
        "R: 100.0",
        "S: HOLA MUNDO",
        "EOF: VERDADERO",
    ]);

    let _ = std::fs::remove_file(&tmp_path);
}

#[test]
fn test_archivo_count_lines_in_while() {
    let tmp_path = std::env::temp_dir()
        .join("ucaba_test_count_lines.txt")
        .to_str()
        .unwrap()
        .replace('\\', "/");

    let code = format!(
        r#"
    INICIO
        ARCHIVO f_out = ABRIR_ARCHIVO("{}", "escritura")
        f_out.ESCRIBIR_LINEA("Linea 1")
        f_out.ESCRIBIR_LINEA("Linea 2")
        f_out.ESCRIBIR_LINEA("Linea 3")
        f_out.CERRAR_ARCHIVO()

        ENTERO cant = 0
        ARCHIVO f_in = ABRIR_ARCHIVO("{}", "lectura")
        MIENTRAS NO f_in.findearchivo
            cant++
        FIN MIENTRAS
        f_in.CERRAR_ARCHIVO()

        IMPRIMIR("LINEAS:", cant)
    FIN
    "#,
        tmp_path, tmp_path
    );

    let output = run_code(&code, false).unwrap();
    assert_eq!(output, vec!["LINEAS: 3"]);

    let _ = std::fs::remove_file(&tmp_path);
}

#[test]
fn test_matrix_assignment() {
    let code = r#"
    INICIO
        ENTERO m[2][2]
        m[0][0] = 10
        m[0][1] = 20
        m[1][0] = 30
        m[1][1] = 40
        IMPRIMIR("M0:", m[0][0], m[0][1])
        IMPRIMIR("M1:", m[1][0], m[1][1])
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["M0: 10 20", "M1: 30 40"]);
}

#[test]
fn test_for_separator_colon() {
    let code = r#"
    INICIO
        ENTERO s = 0
        PARA (ENTERO i = 0; i < 4: i++)
            s += i
        FIN PARA
        IMPRIMIR("S:", s)
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["S: 6"]);
}

#[test]
fn test_if_tolerant_condition() {
    let code = r#"
    INICIO
        ENTERO modo = 2
        ENTERO val = 0
        SI (modo == 1) O SI (modo == 2)
            val = 99
        FIN SI
        IMPRIMIR("VAL:", val)
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["VAL: 99"]);
}

#[test]
fn test_matrix_function_parameters_and_trailing_colon() {
    let code = r#"
    FUNCION trasponer(matriz[][]: ENTERO): ENTERO[][]
        ENTERO cols = matriz[0].largo
        ENTERO filas = matriz.largo
        ENTERO res[cols][filas]
        PARA (ENTERO c = 0; c < cols; c++)
            PARA (ENTERO f = 0; f < filas; f++)
                res[c][f] = matriz[f][c]
            FIN PARA
        FIN PARA
        RETORNAR res
    FIN FUNCION

    FUNCION procesar(m[][]: ENTERO):
        ENTERO t[2][2]
        t = trasponer(m)
        IMPRIMIR("T0_1:", t[0][1])
        IMPRIMIR("T1_0:", t[1][0])
    FIN FUNCION

    INICIO
        ENTERO origen[2][2]
        origen[0][0] = 1
        origen[0][1] = 2
        origen[1][0] = 3
        origen[1][1] = 4
        procesar(origen)
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["T0_1: 3", "T1_0: 2"]);
}

#[test]
fn test_null_and_none_equivalence() {
    let code = r#"
    ESTRUCTURA Nodo:
        CADENA nombre
        Nodo siguiente
    FIN ESTRUCTURA

    INICIO
        Nodo n
        n.nombre = "Primero"
        SI (n.siguiente == NULO)
            IMPRIMIR("ES NULO")
        FIN SI
        SI (n.siguiente == null)
            IMPRIMIR("ES NULL")
        FIN SI
        SI (n.siguiente == None)
            IMPRIMIR("ES NONE")
        FIN SI
    FIN
    "#;
    let output = run_code(code, false).unwrap();
    assert_eq!(output, vec!["ES NULO", "ES NULL", "ES NONE"]);
}

#[test]
fn test_lsp_check_valid_and_invalid() {
    use ucaba_core::check_diagnostics;

    let valid_code = "INICIO ENTERO x = 10; IMPRIMIR(x); FIN";
    let report_valid = check_diagnostics(valid_code, false);
    assert!(report_valid.diagnostics.is_empty());
    assert_eq!(report_valid.to_json(), r#"{"diagnostics":[]}"#);

    let invalid_code = "INICIO\nENTERO x = ;\nFIN";
    let report_invalid = check_diagnostics(invalid_code, false);
    assert_eq!(report_invalid.diagnostics.len(), 1);
    assert_eq!(report_invalid.diagnostics[0].line, 1);
    assert_eq!(report_invalid.diagnostics[0].severity, "error");
    assert_eq!(report_invalid.diagnostics[0].source, "ucaba-parser");
    let json = report_invalid.to_json();
    assert!(json.contains(r#""severity":"error""#));
    assert!(json.contains(r#""source":"ucaba-parser""#));
}

#[test]
fn test_runtime_error_line_and_column() {
    use ucaba_core::UcabaError;

    let code = "INICIO\nENTERO v[2]\nIMPRIMIR(v[5])\nFIN";
    let res = run_code(code, false);
    assert!(res.is_err());
    match res.unwrap_err() {
        UcabaError::Runtime { line, column, message } => {
            assert_eq!(line, 3);
            assert_eq!(column, 1);
            assert!(message.contains("Índice fuera de límites"));
        }
        other => panic!("Se esperaba UcabaError::Runtime, pero fue: {:?}", other),
    }
}





