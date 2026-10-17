#[derive(Debug, Clone, PartialEq)]
pub enum TokenType {
    // Literales
    Entero(i64),
    Real(f64),
    Cadena(String),
    Caracter(char),
    Booleano(bool),
    Nulo,

    // Identificador
    Identificador(String),

    // Palabras clave de tipos
    TipoEntero,
    TipoFlotante,
    TipoReal,
    TipoCadena,
    TipoCaracter,
    TipoBooleano,
    TipoArchivo,
    TipoVoid,

    // Control y bloques
    KwInicio,
    KwFin,
    KwFuncion,
    KwProcedimiento,
    KwRetornar,
    KwSi,
    KwSino,
    KwMientras,
    KwHacer,
    KwPara,
    KwImprimir,
    KwEstructura,

    // Funciones incorporadas
    KwMod,
    KwEsPar,
    KwEsImpar,

    // Operadores aritméticos
    Suma,        // +
    Resta,       // -
    Mult,        // *
    Div,         // /
    DivEntera,   // //
    Mod,         // %
    Inc,         // ++
    Dec,         // --

    // Operadores relacionales
    IgualQue,    // ==
    Distinto,    // !=
    Menor,       // <
    Mayor,       // >
    MenorIgual,  // <=
    MayorIgual,  // >=

    // Operadores lógicos
    OpY,         // Y, &&
    OpO,         // O, ||
    OpNo,        // NO, !

    // Asignaciones
    Asignar,     // =
    AsigSuma,    // +=
    AsigResta,   // -=

    // Delimitadores
    ParentesisIzq,  // (
    ParentesisDer,  // )
    CorcheteIzq,    // [
    CorcheteDer,    // ]
    Coma,           // ,
    PuntoYComa,     // ;
    DosPuntos,      // :
    Punto,          // .

    Eof,
}

#[derive(Debug, Clone, PartialEq)]
pub struct Token {
    pub token_type: TokenType,
    pub line: usize,
    pub column: usize,
    pub length: usize,
}

impl Token {
    pub fn new(token_type: TokenType, line: usize, column: usize, length: usize) -> Self {
        Self {
            token_type,
            line,
            column,
            length,
        }
    }
}
