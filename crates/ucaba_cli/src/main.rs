use clap::{Parser as ClapParser, Subcommand, ValueEnum};
use std::path::PathBuf;
use std::process::exit;
use std::time::Instant;
use ucaba_core::{check_file, run_file, VERSION};

mod dap;
mod repl;
mod updater;

#[derive(ClapParser)]
#[command(
    name = "ucaba",
    author = "Facu Falcone <a.facundo.falcone@gmail.com>",
    about = "UCABA: Lenguaje de programación de pseudocódigo en español fuertemente tipado (v2.0 Native Rust Engine)",
    long_about = None,
    disable_version_flag = true
)]
struct Cli {
    #[command(subcommand)]
    command: Option<Commands>,

    /// Muestra la versión del lenguaje UCABA
    #[arg(short = 'v', short_alias = 'V', long = "version")]
    version: bool,

    /// Archivo .ucaba a ejecutar directamente por defecto
    file: Option<PathBuf>,

    /// Modo de medición de tiempo ('ms' o 'full')
    #[arg(long, value_enum, default_missing_value = "ms", num_args = 0..=1)]
    time: Option<TimeMode>,

    /// Muestra el tiempo de ejecución desglosado (Horas, Minutos, Segundos, Milisegundos)
    #[arg(long)]
    time_full: bool,

    /// Modo permisivo para pseudocódigo informal
    #[arg(short, long)]
    lenient: bool,
}

#[derive(Subcommand)]
enum Commands {
    /// Inicia la consola interactiva REPL de UCABA
    Repl,

    /// Ejecuta un archivo UCABA (.ucaba)
    Run {
        /// Ruta al archivo .ucaba
        file: PathBuf,

        /// Modo de medición de tiempo ('ms' o 'full')
        #[arg(long, value_enum, default_missing_value = "ms", num_args = 0..=1)]
        time: Option<TimeMode>,

        /// Muestra el tiempo de ejecución desglosado
        #[arg(long)]
        time_full: bool,

        /// Modo permisivo para pseudocódigo informal
        #[arg(short, long)]
        lenient: bool,
    },

    /// Verifica sintaxis y tipos sin ejecutar
    Check {
        /// Ruta al archivo .ucaba
        file: PathBuf,

        /// Modo permisivo para pseudocódigo informal
        #[arg(short, long)]
        lenient: bool,
    },

    /// Comprueba actualizaciones de UCABA
    Update {
        /// Solo comprueba si existe una versión nueva
        #[arg(short, long)]
        check: bool,
    },

    /// Alias de update
    Upgrade {
        /// Solo comprueba si existe una versión nueva
        #[arg(short, long)]
        check: bool,
    },

    /// Análisis y diagnósticos en tiempo real para Language Server / VS Code (JSON)
    #[command(name = "lsp-check")]
    LspCheck {
        /// Ruta al archivo .ucaba (si se omite o es '-', lee desde stdin)
        file: Option<PathBuf>,

        /// Modo permisivo para pseudocódigo informal
        #[arg(short, long)]
        lenient: bool,

        /// Modo estricto
        #[arg(short, long)]
        strict: bool,

        /// Emite diagnósticos en formato JSON (habilitado por defecto)
        #[arg(long)]
        json: bool,

        /// Lee el código fuente desde la entrada estándar (stdin)
        #[arg(long)]
        stdin: bool,
    },

    /// Servidor de depuración DAP (breakpoints, paso a paso, variables) para VS Code
    Dap,
}

#[derive(Copy, Clone, PartialEq, Eq, PartialOrd, Ord, ValueEnum, Debug)]
enum TimeMode {
    Ms,
    Full,
    Completo,
}

fn print_welcome_banner(force: bool) {
    if !force && std::env::var("UCABA_HIDE_BANNER").ok().as_deref() == Some("1") {
        return;
    }
    let no_color = std::env::var("NO_COLOR").is_ok() || std::env::var("UCABA_NO_COLOR").is_ok();
    if no_color {
        println!("UCABA (v{})", VERSION);
        println!("Hello from the UCABA community. [Dev: Facu Falcone]");
    } else {
        // Color fucsia oficial UCABA #d946ef
        println!("\x1b[95m\x1b[1;38;2;217;70;239mUCABA (v{})\x1b[0m", VERSION);
        println!("\x1b[95m\x1b[1;38;2;217;70;239mHello from the UCABA community. [Dev: Facu Falcone]\x1b[0m");
    }
}

fn format_elapsed_time(elapsed_secs: f64, is_full: bool) -> String {
    if !is_full {
        let ms = elapsed_secs * 1000.0;
        format!("[Tiempo total: {:.2} ms]", ms)
    } else {
        let total_ms_f = elapsed_secs * 1000.0;
        let mut total_ms = total_ms_f.round() as u64;

        let hours = total_ms / 3_600_000;
        total_ms %= 3_600_000;

        let minutes = total_ms / 60_000;
        total_ms %= 60_000;

        let seconds = total_ms / 1_000;
        let millis = total_ms % 1_000;

        let h_str = if hours == 1 { "1 Hora" } else { &format!("{} Horas", hours) };
        let m_str = if minutes == 1 { "1 Minuto" } else { &format!("{} Minutos", minutes) };
        let s_str = if seconds == 1 { "1 Segundo" } else { &format!("{} Segundos", seconds) };
        let ms_str = if millis == 1 { "1 Milisegundo" } else { &format!("{} Milisegundos", millis) };

        format!("[Tiempo total: {}, {}, {}, {}]", h_str, m_str, s_str, ms_str)
    }
}

fn main() {
    #[cfg(windows)]
    let _ = colored::control::set_virtual_terminal(true);

    let cli = Cli::parse();

    if cli.version {
        print_welcome_banner(true);
        return;
    }

    // LSP y DAP usan stdout como canal de protocolo: no deben imprimir banner ni avisos.
    let is_lsp = matches!(cli.command, Some(Commands::LspCheck { .. }) | Some(Commands::Dap));
    if !is_lsp {
        print_welcome_banner(false);
    }

    // Aviso de nueva versión en segundo plano (no aplica a update/upgrade ni LSP).
    let skip_notice = is_lsp
        || matches!(
            cli.command,
            Some(Commands::Update { .. }) | Some(Commands::Upgrade { .. })
        );
    let bg_check = if skip_notice {
        None
    } else {
        Some(updater::BackgroundCheck::start(VERSION))
    };
    let is_repl = matches!(cli.command, Some(Commands::Repl))
        || (cli.command.is_none() && cli.file.is_none());
    let bg_check = if is_repl {
        // En el REPL el aviso debe verse al iniciar, no al salir.
        if let Some(b) = bg_check {
            b.finish(std::time::Duration::from_millis(1500));
        }
        None
    } else {
        bg_check
    };

    match cli.command {
        Some(Commands::Dap) => {
            exit(dap::run_dap());
        }
        Some(Commands::Repl) => {
            repl::run_repl();
        }
        Some(Commands::Run {
            file,
            time,
            time_full,
            lenient,
        }) => {
            execute_run(file, time, time_full, lenient);
        }
        Some(Commands::Check { file, lenient }) => {
            println!("[CHECK] Verificando archivo: {} (lenient={}) ...", file.display(), lenient);
            match check_file(&file, lenient) {
                Ok(_) => {
                    println!("\x1b[32m[OK] Sin errores de sintaxis ni tipos detectados.\x1b[0m");
                }
                Err(err) => {
                    eprintln!("\x1b[31m{}\x1b[0m", err);
                    exit(1);
                }
            }
        }
        Some(Commands::LspCheck { file, lenient, strict, json: _, stdin }) => {
            let is_lenient = if strict { false } else { lenient || true };
            let source = if stdin || file.as_ref().is_none_or(|p| p.to_string_lossy() == "-") {
                use std::io::Read;
                let mut buffer = String::new();
                let _ = std::io::stdin().read_to_string(&mut buffer);
                buffer
            } else {
                let p = file.as_ref().unwrap();
                match std::fs::read_to_string(p) {
                    Ok(s) => s,
                    Err(e) => {
                        let report = ucaba_core::DiagnosticsReport {
                            diagnostics: vec![ucaba_core::Diagnostic {
                                line: 0,
                                character: 0,
                                length: 1,
                                message: format!("Error leyendo archivo '{}': {}", p.display(), e),
                                severity: "error".to_string(),
                                source: "ucaba-io".to_string(),
                            }],
                        };
                        println!("{}", report.to_json());
                        return;
                    }
                }
            };

            let report = ucaba_core::check_diagnostics(&source, is_lenient);
            println!("{}", report.to_json());
        }
        Some(Commands::Update { check }) | Some(Commands::Upgrade { check }) => {
            let code = if check {
                updater::run_check(VERSION)
            } else {
                updater::run_update(VERSION)
            };
            if code != 0 {
                exit(code);
            }
        }
        None => {
            if let Some(file) = cli.file {
                execute_run(file, cli.time, cli.time_full, cli.lenient);
            } else {
                repl::run_repl();
            }
        }
    }

    if let Some(b) = bg_check {
        b.finish(std::time::Duration::from_millis(500));
    }
}

fn execute_run(file: PathBuf, time: Option<TimeMode>, time_full: bool, lenient: bool) {
    println!("[RUN] Ejecutando archivo: {} (lenient={}) ...", file.display(), lenient);

    let start = Instant::now();
    let res = run_file(&file, lenient);
    let elapsed = start.elapsed().as_secs_f64();

    match res {
        Ok(_) => {
            let is_full = time_full
                || matches!(time, Some(TimeMode::Full) | Some(TimeMode::Completo));
            let show_time = time.is_some() || time_full;

            if show_time {
                println!("\n{}", format_elapsed_time(elapsed, is_full));
            }
        }
        Err(err) => {
            eprintln!("\x1b[31m{}\x1b[0m", err);
            exit(1);
        }
    }
}
