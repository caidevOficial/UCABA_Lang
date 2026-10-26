use std::fmt;

#[derive(Debug, Clone, PartialEq)]
pub enum DataType {
    Entero,
    Flotante,
    Real,
    Cadena,
    Caracter,
    Booleano,
    Archivo,
    Void,
    Nulo,
    Vector(Box<DataType>),
    Matriz(Box<DataType>),
    Estructura(String),
}

impl fmt::Display for DataType {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            DataType::Entero => write!(f, "ENTERO"),
            DataType::Flotante => write!(f, "FLOTANTE"),
            DataType::Real => write!(f, "REAL"),
            DataType::Cadena => write!(f, "CADENA"),
            DataType::Caracter => write!(f, "CARACTER"),
            DataType::Booleano => write!(f, "BOOLEANO"),
            DataType::Archivo => write!(f, "ARCHIVO"),
            DataType::Void => write!(f, "VOID"),
            DataType::Nulo => write!(f, "NULO"),
            DataType::Vector(inner) => write!(f, "{}[]", inner),
            DataType::Matriz(inner) => write!(f, "{}[][]", inner),
            DataType::Estructura(name) => write!(f, "{}", name),
        }
    }
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum BinaryOp {
    Suma,
    Resta,
    Mult,
    Div,
    DivEntera,
    Mod,
    IgualQue,
    Distinto,
    Menor,
    Mayor,
    MenorIgual,
    MayorIgual,
    Y,
    O,
}

#[derive(Debug, Clone, Copy, PartialEq)]
pub enum UnaryOp {
    No,
    Negativo,
    Positivo,
}

#[derive(Debug, Clone, PartialEq)]
pub enum Expression {
    LiteralInt(i64),
    LiteralReal(f64),
    LiteralCadena(String),
    LiteralCaracter(char),
    LiteralBool(bool),
    LiteralNulo,
    LiteralVector(Vec<Expression>),
    Variable(String),
    Binary {
        left: Box<Expression>,
        op: BinaryOp,
        right: Box<Expression>,
    },
    Unary {
        op: UnaryOp,
        expr: Box<Expression>,
    },
    IndexAccess {
        target: Box<Expression>,
        index: Box<Expression>,
    },
    MemberAccess {
        target: Box<Expression>,
        member: String,
    },
    Call {
        name: String,
        args: Vec<Expression>,
    },
    MethodCall {
        target: Box<Expression>,
        method: String,
        args: Vec<Expression>,
    },
}

#[derive(Debug, Clone, PartialEq)]
pub enum Statement {
    VarDecl {
        var_type: DataType,
        name: String,
        size_exprs: Vec<Expression>,
        init: Option<Expression>,
    },
    Assign {
        target: Expression,
        val: Expression,
    },
    AssignOp {
        target: Expression,
        op: BinaryOp,
        val: Expression,
    },
    Increment {
        target: Expression,
        is_inc: bool,
    },
    If {
        condition: Expression,
        then_branch: Vec<Statement>,
        else_if_branches: Vec<(Expression, Vec<Statement>)>,
        else_branch: Option<Vec<Statement>>,
    },
    While {
        condition: Expression,
        body: Vec<Statement>,
    },
    DoWhile {
        body: Vec<Statement>,
        condition: Expression,
    },
    For {
        init: Box<Statement>,
        condition: Expression,
        update: Box<Statement>,
        body: Vec<Statement>,
    },
    Return(Option<Expression>),
    Print(Vec<Expression>),
    Expr(Expression),
    FunctionDef {
        name: String,
        params: Vec<(String, DataType)>,
        return_type: DataType,
        body: Vec<Statement>,
    },
    StructDef {
        name: String,
        fields: Vec<(String, DataType)>,
    },
    /// Envoltorio que asocia una sentencia con su línea y columna de código fuente (1-based).
    /// Lo usa el depurador (DAP) para breakpoints y avance paso a paso, y el runtime para reportes de error precisos.
    Located {
        line: usize,
        column: usize,
        stmt: Box<Statement>,
    },
}

#[derive(Debug, Clone, PartialEq)]
pub struct Program {
    pub statements: Vec<Statement>,
}
