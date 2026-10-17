use ucaba_core::run_code;

#[test]
fn test_division_entera_basica() {
    let code = r#"
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
    "#;
    let out = run_code(code, false).unwrap();
    assert_eq!(out, vec!["A: 3", "B: 5", "C: 3", "D: 5"]);
}

#[test]
fn test_division_entera_dentro_de_indices() {
    let code = r#"
    INICIO
        ENTERO columnas = 2
        ENTERO origen[2][2] = [[1, 2], [3, 4]]
        ENTERO destino[2][2]
        PARA (ENTERO p = 0; p < 4; p++)
            destino[p // columnas][p % columnas] = origen[p // columnas][p % columnas] * 10
        FIN PARA
        IMPRIMIR(destino[0][0] + "," + destino[0][1] + "," + destino[1][0] + "," + destino[1][1])
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert_eq!(out, vec!["10,20,30,40"]);
}

#[test]
fn test_division_entera_con_variables_y_precedencia() {
    let code = r#"
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
    "#;
    let out = run_code(code, false).unwrap();
    assert_eq!(out, vec!["RES: 4", "PREC1: 15", "PREC2: 7"]);
}

#[test]
fn test_division_entera_en_funciones_y_retorno() {
    let code = r#"
    FUNCION dividir(dividendo: ENTERO, divisor: ENTERO): ENTERO
        RETORNAR dividendo // divisor
    FIN FUNCION

    INICIO
        ENTERO res = dividir(27, 4)
        IMPRIMIR("DIV: " + res)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert_eq!(out, vec!["DIV: 6"]);
}

#[test]
fn test_division_entera_por_cero_arroja_error() {
    let code = r#"
    INICIO
        ENTERO a = 10 // 0
    FIN
    "#;
    let res = run_code(code, false);
    assert!(res.is_err());
    let err_msg = res.unwrap_err().to_string();
    assert!(err_msg.to_lowercase().contains("cero"));
}

#[test]
fn test_modulo_operador_basico() {
    let code = r#"
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
    "#;
    let out = run_code(code, false).unwrap();
    assert_eq!(out, vec!["M1: 1", "M2: 3", "M3: 0", "M4: 4"]);
}

#[test]
fn test_modulo_con_variables_y_precedencia() {
    let code = r#"
    INICIO
        ENTERO a = 23
        ENTERO b = 5
        ENTERO r = a % b
        ENTERO comb = (a // b) * b + (a % b)
        IMPRIMIR("R: " + r)
        IMPRIMIR("COMB: " + comb)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert_eq!(out, vec!["R: 3", "COMB: 23"]);
}

#[test]
fn test_modulo_por_cero_arroja_error() {
    let code = r#"
    INICIO
        ENTERO a = 10 % 0
    FIN
    "#;
    let res = run_code(code, false);
    assert!(res.is_err());
    let err_msg = res.unwrap_err().to_string();
    assert!(err_msg.to_lowercase().contains("cero") || err_msg.to_lowercase().contains("módulo"));
}

#[test]
fn test_validacion_tipos_division_entera_y_modulo() {
    let code_inv_div = r#"
    INICIO
        CADENA s = "texto"
        ENTERO x = s // 2
    FIN
    "#;
    assert!(run_code(code_inv_div, false).is_err());

    let code_inv_mod = r#"
    INICIO
        CADENA s = "texto"
        ENTERO x = s % 2
    FIN
    "#;
    assert!(run_code(code_inv_mod, false).is_err());
}

#[test]
fn test_convivencia_division_entera_con_comentarios() {
    let code = r#"
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
    "#;
    let out = run_code(code, false).unwrap();
    assert_eq!(out, vec!["X: 3", "Y: 5", "Z: 50"]);
}

#[test]
fn test_comentarios_con_hash_en_lineas_independientes() {
    let code = r#"
    # Comentario de inicio con hash
    INICIO
        # Declaracion de variable
        ENTERO valor = 42 # inline con hash
        IMPRIMIR("VAL: " + valor)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert_eq!(out, vec!["VAL: 42"]);
}
