use ucaba_core::run_code;

#[test]
fn test_ciclo_para() {
    let code = r#"
    INICIO
        ENTERO suma = 0
        PARA(ENTERO vueltas = 0; vueltas < 5; vueltas++)
            suma = suma + vueltas
        FIN PARA
        IMPRIMIR("SUMA: " + suma)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("SUMA: 10")));
}

#[test]
fn test_ciclo_mientras() {
    let code = r#"
    INICIO
        ENTERO n = 3
        MIENTRAS (n > 0)
            n--
        FIN MIENTRAS
        IMPRIMIR("FINAL: " + n)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("FINAL: 0")));
}

#[test]
fn test_ciclo_hacer_mientras() {
    let code = r#"
    INICIO
        ENTERO cuenta = 0
        HACER
            cuenta++
        MIENTRAS (cuenta < 3)
        FIN HACER
        IMPRIMIR("CUENTA: " + cuenta)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("CUENTA: 3")));
}

#[test]
fn test_condicional_si_sino_si() {
    let code = r#"
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
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("MUY BIEN")));
}

#[test]
fn test_vectores_y_matrices() {
    let code = r#"
    INICIO
        REAL vector[3] = [1.5, 2.5, 3.5]
        IMPRIMIR("V0: " + vector[0])
        IMPRIMIR("LARGO V: " + vector.largo)

        ENTERO matriz[2][3] = [[10, 20, 30], [40, 50, 60]]
        IMPRIMIR("M1_2: " + matriz[1][2])
        IMPRIMIR("FILAS: " + matriz.largo)
        IMPRIMIR("COLS: " + matriz[0].largo)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("V0: 1.5")));
    assert!(out.iter().any(|s| s.contains("LARGO V: 3")));
    assert!(out.iter().any(|s| s.contains("M1_2: 60")));
    assert!(out.iter().any(|s| s.contains("FILAS: 2")));
    assert!(out.iter().any(|s| s.contains("COLS: 3")));
}

#[test]
fn test_procedimiento_y_funcion() {
    let code = r#"
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
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("DOBLE: 42")));
    assert!(out.iter().any(|s| s.contains("HOLA ALUMNO")));
}

#[test]
fn test_funciones_matematicas_incorporadas() {
    let code = r#"
    INICIO
        BOOLEANO par4 = ESPAR(4)
        BOOLEANO impar5 = ESIMPAR(5)
        ENTERO resto = MOD(17, 5)

        IMPRIMIR("PAR: " + par4)
        IMPRIMIR("IMPAR: " + impar5)
        IMPRIMIR("RESTO: " + resto)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("PAR: VERDADERO")));
    assert!(out.iter().any(|s| s.contains("IMPAR: VERDADERO")));
    assert!(out.iter().any(|s| s.contains("RESTO: 2")));
}

#[test]
fn test_concatenacion_cadenas_y_vectores() {
    let code = r#"
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
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("El valor es: 1")));
    assert!(out.iter().any(|s| s.contains("El valor es: 2.5")));
    assert!(out.iter().any(|s| s.contains("El valor es: VERDADERO")));
    assert!(out.iter().any(|s| s.contains("El valor es: a")));
    assert!(out.iter().any(|s| s.contains("El valor es: hola")));
    assert!(out.iter().any(|s| s.contains("VEC CONCAT LARGO: 4")));
    assert!(out.iter().any(|s| s.contains("VEC CONCAT [2]: 3")));
}

#[test]
fn test_propiedad_largo_vectores() {
    let code = r#"
    INICIO
        ENTERO mi_vector[] = [5,2,7]
        ENTERO cantidad = mi_vector.largo
        IMPRIMIR("CANTIDAD: " + cantidad)

        CADENA nombres[] = ["Ana", "Pedro", "Lucia", "Marcos"]
        IMPRIMIR("NOMBRES: " + nombres.largo)

        REAL vacio[] = []
        IMPRIMIR("VACIO: " + vacio.largo)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("CANTIDAD: 3")));
    assert!(out.iter().any(|s| s.contains("NOMBRES: 4")));
    assert!(out.iter().any(|s| s.contains("VACIO: 0")));
}

#[test]
fn test_funciones_dentro_de_inicio_fin() {
    let code = r#"
    INICIO
        FUNCION sumar(a: ENTERO, b: ENTERO): ENTERO
            RETORNO a + b
        FIN FUNCION

        ENTERO res = sumar(15, 27)
        IMPRIMIR("RESULTADO: " + res)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("RESULTADO: 42")));
}

#[test]
fn test_funcion_sin_tipo_de_retorno_y_variable_en_cuerpo() {
    let code = r#"
    INICIO
        FUNCION mostrar_algo(x: ENTERO)
            REAL total_mes = 100.5
            IMPRIMIR("TOTAL: " + total_mes)
        FIN FUNCION

        mostrar_algo(1)
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("TOTAL: 100.5")));
}

#[test]
fn test_asignacion_fila_matriz() {
    let code = r#"
    INICIO
        ENTERO m[2][2]
        ENTERO fila[2] = [10, 20]
        m[0] = fila
        IMPRIMIR("M0_0: " + m[0][0])
        IMPRIMIR("M0_1: " + m[0][1])
    FIN
    "#;
    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("M0_0: 10")));
    assert!(out.iter().any(|s| s.contains("M0_1: 20")));
}

#[test]
fn test_leer_linea_tipos_automaticos() {
    let tmp_path = std::env::temp_dir()
        .join("ucaba_test_tipos_auto.txt")
        .to_str()
        .unwrap()
        .replace('\\', "/");

    std::fs::write(&tmp_path, "12345\n98.75\nVERDADERO\nFALSO\nHOLA MUNDO\n").unwrap();

    let code = format!(
        r#"
    INICIO
        ARCHIVO f = ABRIR_ARCHIVO("{}", "lectura")
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
    "#,
        tmp_path
    );

    let out = run_code(&code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("N: 12350")));
    assert!(out.iter().any(|s| s.contains("R: 100.0")));
    assert!(out.iter().any(|s| s.contains("B1: VERDADERO")));
    assert!(out.iter().any(|s| s.contains("B2: FALSO")));
    assert!(out.iter().any(|s| s.contains("S: HOLA MUNDO")));

    let _ = std::fs::remove_file(&tmp_path);
}

#[test]
fn test_estructura_definir_declarar_y_asignar() {
    let code = r#"
    Estructura Libro:
        CADENA nombre
        ENTERO hojas
        CADENA sinopsis
        CADENA autor
        CADENA editorial
        ENTERO edicion
    Fin Estructura

    Libro libro1

    libro1.nombre = "Nombre del Libro"
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
    "#;

    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("NOMBRE: Nombre del Libro")));
    assert!(out.iter().any(|s| s.contains("HOJAS: 350")));
    assert!(out.iter().any(|s| s.contains("AUTOR: Jorge Luis Borges")));
    assert!(out.iter().any(|s| s.contains("EDITORIAL: Sur")));
    assert!(out.iter().any(|s| s.contains("EDICION: 1")));
    assert!(out.iter().any(|s| s.contains("Libro{")));
}

#[test]
fn test_estructuras_multiples_e_independientes() {
    let code = r#"
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
    "#;

    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("P1: Alice (25)")));
    assert!(out.iter().any(|s| s.contains("P2: Bob (30)")));
}

#[test]
fn test_vector_de_estructuras() {
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

    IMPRIMIR("PROD0: " + inventario[0].codigo + " $" + inventario[0].precio)
    IMPRIMIR("PROD1: " + inventario[1].codigo + " $" + inventario[1].precio)
    "#;

    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("PROD0: P01 $99.5")));
    assert!(out.iter().any(|s| s.contains("PROD1: P02 $150.0")));
}

#[test]
fn test_estructura_en_funciones_y_procedimientos() {
    let code = r#"
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
    "#;

    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("APROBADO: VERDADERO")));
}

#[test]
fn test_error_campo_inexistente_estructura() {
    let code = r#"
    Estructura Libro:
        CADENA nombre
        ENTERO hojas
    Fin Estructura

    Libro l
    l.nombr = "Invalido"
    "#;

    let res = run_code(code, false);
    assert!(res.is_err());
    let err = res.unwrap_err().to_string();
    assert!(err.contains("no tiene el campo 'nombr'"));
    assert!(err.contains("¿Quisiste decir 'nombre'?"));
}

#[test]
fn test_estructura_recursiva_nodo() {
    let code = r#"
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
    "#;

    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("N1: Primero")));
    assert!(out.iter().any(|s| s.contains("PROXIMO: Segundo")));
}

#[test]
fn test_tipo_nulo_y_recorrido_lista() {
    let code = r#"
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
    "#;

    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("VISITADO: Primero")));
    assert!(out.iter().any(|s| s.contains("VISITADO: Segundo")));
    assert!(out.iter().any(|s| s.contains("FINAL: NULO")));
    assert!(out.iter().any(|s| s.contains("ES NULL: VERDADERO")));
    assert!(out.iter().any(|s| s.contains("ES NONE: VERDADERO")));
}

#[test]
fn test_estructura_persona_atributos() {
    let code = r#"
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
    "#;

    let out = run_code(code, false).unwrap();
    assert!(out.iter().any(|s| s.contains("PERSONA: Pepe 25")));
}
