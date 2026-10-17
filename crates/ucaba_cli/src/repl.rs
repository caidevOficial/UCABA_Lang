use std::io::{self, BufRead, Write};
use ucaba_core::{is_input_complete, Interpreter};

pub fn run_repl() {
    println!("\x1b[38;2;244;114;182mConsola Interactiva REPL. Escribe expresiones o código de pseudocódigo.\x1b[0m");
    println!("Comandos especiales: \x1b[33m:ayuda\x1b[0m, \x1b[33m:variables\x1b[0m, \x1b[33m:limpiar\x1b[0m, \x1b[33m:salir\x1b[0m\n");

    let mut interpreter = Interpreter::new();
    let stdin = io::stdin();
    let mut stdin_lock = stdin.lock();
    let mut buffer = String::new();

    loop {
        if buffer.is_empty() {
            print!("\x1b[1;38;2;217;70;239mucaba>\x1b[0m ");
        } else {
            print!("\x1b[38;2;168;26;125m...   \x1b[0m ");
        }
        let _ = io::stdout().flush();

        let mut line = String::new();
        match stdin_lock.read_line(&mut line) {
            Ok(0) => {
                // Fin de archivo (EOF / Ctrl+D / Ctrl+Z / piped input finalizado)
                println!();
                break;
            }
            Ok(_) => {
                let trimmed = line.trim();

                // Manejo de comandos especiales cuando el buffer está vacío
                if buffer.is_empty() {
                    match trimmed {
                        ":salir" | ":exit" | ":quit" | ":q" => {
                            println!("\x1b[38;2;244;114;182m¡Hasta luego!\x1b[0m");
                            break;
                        }
                        ":ayuda" | ":help" | ":?" => {
                            print_help();
                            continue;
                        }
                        ":variables" | ":vars" => {
                            print_variables(&interpreter);
                            continue;
                        }
                        ":limpiar" | ":clear" => {
                            interpreter.reset();
                            print!("\x1b[2J\x1b[1;1H");
                            let _ = io::stdout().flush();
                            println!("\x1b[32m[OK] Entorno y variables reiniciados.\x1b[0m");
                            continue;
                        }
                        "" => continue,
                        _ => {}
                    }
                } else if trimmed == ":cancel" || trimmed == ":c" {
                    println!("\x1b[33m[Entrada multilínea cancelada]\x1b[0m");
                    buffer.clear();
                    continue;
                }

                buffer.push_str(&line);

                if is_input_complete(&buffer) {
                    match interpreter.eval_repl_input(&buffer) {
                        Ok(Some(val)) => {
                            println!("\x1b[36m=> {}\x1b[0m", val.to_canonical_string());
                        }
                        Ok(None) => {}
                        Err(err) => {
                            eprintln!("\x1b[31m{}\x1b[0m", err);
                        }
                    }
                    buffer.clear();
                }
            }
            Err(e) => {
                eprintln!("\x1b[31mError leyendo entrada: {}\x1b[0m", e);
                break;
            }
        }
    }
}

fn print_variables(interpreter: &Interpreter) {
    let vars = interpreter.get_variables();
    if vars.is_empty() {
        println!("\x1b[33m(No hay variables definidas en el entorno actual)\x1b[0m");
        return;
    }

    let mut name_width = "NOMBRE".len();
    let mut type_width = "TIPO".len();
    let mut val_width = "VALOR".len();

    let formatted_vars: Vec<(String, String, String)> = vars
        .into_iter()
        .map(|(name, dt, val)| {
            let n_str = name;
            let t_str = dt.to_string();
            let v_str = val.to_canonical_string();

            if n_str.len() > name_width {
                name_width = n_str.len();
            }
            if t_str.len() > type_width {
                type_width = t_str.len();
            }
            if v_str.len() > val_width {
                val_width = v_str.len();
            }
            (n_str, t_str, v_str)
        })
        .collect();

    // Dibujo de tabla con bordes estilizados
    let line_top = format!(
        "┌─{}─┬─{}─┬─{}─┐",
        "─".repeat(name_width),
        "─".repeat(type_width),
        "─".repeat(val_width)
    );
    let line_mid = format!(
        "├─{}─┼─{}─┼─{}─┤",
        "─".repeat(name_width),
        "─".repeat(type_width),
        "─".repeat(val_width)
    );
    let line_bot = format!(
        "└─{}─┴─{}─┴─{}─┘",
        "─".repeat(name_width),
        "─".repeat(type_width),
        "─".repeat(val_width)
    );

    println!("\x1b[38;2;168;26;125m{}\x1b[0m", line_top);
    println!(
        "\x1b[38;2;168;26;125m│\x1b[0m \x1b[1m{:<nw$}\x1b[0m \x1b[38;2;168;26;125m│\x1b[0m \x1b[1m{:<tw$}\x1b[0m \x1b[38;2;168;26;125m│\x1b[0m \x1b[1m{:<vw$}\x1b[0m \x1b[38;2;168;26;125m│\x1b[0m",
        "NOMBRE", "TIPO", "VALOR",
        nw = name_width,
        tw = type_width,
        vw = val_width
    );
    println!("\x1b[38;2;168;26;125m{}\x1b[0m", line_mid);

    for (name, dt, val) in formatted_vars {
        println!(
            "\x1b[38;2;168;26;125m│\x1b[0m {:<nw$} \x1b[38;2;168;26;125m│\x1b[0m \x1b[35m{:<tw$}\x1b[0m \x1b[38;2;168;26;125m│\x1b[0m \x1b[36m{:<vw$}\x1b[0m \x1b[38;2;168;26;125m│\x1b[0m",
            name, dt, val,
            nw = name_width,
            tw = type_width,
            vw = val_width
        );
    }
    println!("\x1b[38;2;168;26;125m{}\x1b[0m", line_bot);
}

fn print_help() {
    println!("\x1b[1;38;2;217;70;239mComandos del REPL de UCABA:\x1b[0m");
    println!("  \x1b[33m:ayuda\x1b[0m, \x1b[33m:help\x1b[0m        Muestra esta guía de ayuda y atajos");
    println!("  \x1b[33m:variables\x1b[0m, \x1b[33m:vars\x1b[0m    Muestra la tabla de variables activas en memoria");
    println!("  \x1b[33m:limpiar\x1b[0m, \x1b[33m:clear\x1b[0m     Reinicia el estado del intérprete y borra las variables");
    println!("  \x1b[33m:cancel\x1b[0m, \x1b[33m:c\x1b[0m         Cancela la entrada multilínea en curso");
    println!("  \x1b[33m:salir\x1b[0m, \x1b[33m:exit\x1b[0m, \x1b[33m:q\x1b[0m    Cierra la sesión del REPL\n");
    println!("\x1b[1;38;2;217;70;239mEjemplos rápidos:\x1b[0m");
    println!("  \x1b[32m• Expresiones:\x1b[0m       10 + 20 * 3");
    println!("  \x1b[32m• Cadenas y vectores:\x1b[0m\"Hola \" + \"Mundo\", [1, 2, 3] + [4, 5]");
    println!("  \x1b[32m• Declaraciones:\x1b[0m     ENTERO x = 42");
    println!("  \x1b[32m• Condicionales:\x1b[0m     SI (x > 10) IMPRIMIR(\"Mayor\") SINO IMPRIMIR(\"Menor\") FIN SI");
    println!("  \x1b[32m• Funciones:\x1b[0m         FUNCION doble(n: ENTERO): ENTERO");
    println!("                         RETORNAR n * 2");
    println!("                       FIN FUNCION");
    println!("                       doble(21)");
}
