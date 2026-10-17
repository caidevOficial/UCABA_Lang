use ucaba_core::run_code;

#[test]
fn test_precision_flotante_vs_real() {
    let code = r#"
    INICIO
        FLOTANTE f = 1.0000001
        REAL r = 1.0000001
        IMPRIMIR("F: " + f)
        IMPRIMIR("R: " + r)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert_ne!(out[0], out[1]);
    assert!(out[0].starts_with("F: 1.000000119"));
    assert_eq!(out[1], "R: 1.0000001");
}

#[test]
fn test_archivos_lectura_y_escritura() {
    let tmp_path = std::env::temp_dir()
        .join("ucaba_test_interpreter_io.txt")
        .to_str()
        .unwrap()
        .replace('\\', "/");

    let write_code = format!(
        r#"
    INICIO
        ARCHIVO f = ABRIR_ARCHIVO("{}", "escritura")
        f.ESCRIBIR_LINEA("PRIMERA")
        f.ESCRIBIR_LINEA("SEGUNDA")
        f.CERRAR_ARCHIVO()
    FIN
    "#,
        tmp_path
    );
    run_code(&write_code, false).unwrap();

    assert!(std::path::Path::new(&tmp_path).exists());

    let read_code = format!(
        r#"
    INICIO
        ARCHIVO f = ABRIR_ARCHIVO("{}", "lectura")
        CADENA l1 = f.LEER_LINEA()
        CADENA l2 = f.LEER_LINEA()
        BOOLEANO es_fin = f.findearchivo
        f.CERRAR_ARCHIVO()

        IMPRIMIR("L1: " + l1)
        IMPRIMIR("L2: " + l2)
        IMPRIMIR("FIN: " + es_fin)
    FIN
    "#,
        tmp_path
    );
    let out = run_code(&read_code, false).unwrap();
    assert_eq!(out, vec!["L1: PRIMERA", "L2: SEGUNDA", "FIN: VERDADERO"]);

    let _ = std::fs::remove_file(&tmp_path);
}

#[test]
fn test_conteo_lineas_archivo_tolerante() {
    let tmp_path = std::env::temp_dir()
        .join("ucaba_test_interpreter_cinco_lineas.txt")
        .to_str()
        .unwrap()
        .replace('\\', "/");

    std::fs::write(&tmp_path, "A\nB\nC\nD\nE\n").unwrap();

    let code = format!(
        r#"
    INICIO
        ENTERO cant = 0
        ARCHIVO f = ABRIR_ARCHIVO("{}", "lectura")
        MIENTRAS NO f.findearchivo
            cant++
        FIN MIENTRAS
        f.CERRAR_ARCHIVO()
        IMPRIMIR("TOTAL: " + cant)
    FIN
    "#,
        tmp_path
    );

    let out = run_code(&code, false).unwrap();
    assert_eq!(out, vec!["TOTAL: 5"]);

    let _ = std::fs::remove_file(&tmp_path);
}

#[test]
fn test_chequeo_estricto_rechaza_incompatibilidad() {
    let code = r#"
    INICIO
        ENTERO n = "texto"
    FIN
    "#;
    assert!(run_code(code, false).is_err());
}

#[test]
fn test_quicksort_pseudocodigo() {
    let code = r#"
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
        FIN SI

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
    "#;

    let out = run_code(code, false).unwrap();
    assert_eq!(out, vec!["O0: 10", "O1: 20", "O2: 30", "O3: 40", "O4: 50"]);
}

#[test]
fn test_repl_core_functionality() {
    use ucaba_core::{is_input_complete, Interpreter, Value};

    // 1. is_input_complete checks
    assert!(is_input_complete("10 + 20"));
    assert!(!is_input_complete("(10 + 20"));
    assert!(!is_input_complete("SI (x > 0)"));
    assert!(is_input_complete("SI (x > 0)\n IMPRIMIR(x)\nFIN SI"));
    assert!(is_input_complete("FUNCION suma(a: ENTERO, b: ENTERO): ENTERO\n RETORNAR a + b\nFIN FUNCION"));
    assert!(is_input_complete("HACER x++ MIENTRAS (x < 10); FIN HACER"));

    // 2. eval_repl_input stateful session
    let mut interp = Interpreter::new();

    // Variable declaration returns None
    let res1 = interp.eval_repl_input("ENTERO base = 15").unwrap();
    assert_eq!(res1, None);

    // Expression evaluation returns Some(Value)
    let res2 = interp.eval_repl_input("base * 3").unwrap();
    assert_eq!(res2, Some(Value::Entero(45)));

    // Variables table inspection
    let vars = interp.get_variables();
    assert_eq!(vars.len(), 1);
    assert_eq!(vars[0].0, "base");
    assert_eq!(vars[0].2, Value::Entero(15));

    // Reset clears state
    interp.reset();
    assert_eq!(interp.get_variables().len(), 0);
}

