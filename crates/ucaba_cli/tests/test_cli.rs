use std::process::Command;

#[test]
fn test_cli_version() {
    for flag in ["--version", "-v", "-V"] {
        let output = Command::new(env!("CARGO_BIN_EXE_ucaba"))
            .arg(flag)
            .output()
            .unwrap_or_else(|_| panic!("Failed to execute ucaba {}", flag));

        assert!(output.status.success());
        let stdout = String::from_utf8_lossy(&output.stdout);
        assert!(stdout.contains("UCABA (v2.0.3)"), "Flag {} failed banner version check", flag);
        assert!(stdout.contains("Hello from the UCABA community. [Dev: Facu Falcone]"), "Flag {} failed dev check", flag);
    }
}

#[test]
fn test_cli_help() {
    let output = Command::new(env!("CARGO_BIN_EXE_ucaba"))
        .arg("--help")
        .output()
        .expect("Failed to execute ucaba --help");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("UCABA: Lenguaje de programación"));
    assert!(stdout.contains("run"));
    assert!(stdout.contains("check"));
    assert!(stdout.contains("lsp-check"));
}

#[test]
fn test_cli_check_valid() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap().parent().unwrap();
    let file = root.join("ejemplo.ucaba");
    let output = Command::new(env!("CARGO_BIN_EXE_ucaba"))
        .args(["check", file.to_str().unwrap()])
        .output()
        .expect("Failed to execute ucaba check");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("[OK] Sin errores"));
}

#[test]
fn test_cli_run_with_time() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap().parent().unwrap();
    let file = root.join("ejemplo.ucaba");
    let output = Command::new(env!("CARGO_BIN_EXE_ucaba"))
        .args(["run", file.to_str().unwrap(), "--time"])
        .output()
        .expect("Failed to execute ucaba run");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("[Tiempo total:"));
    assert!(stdout.contains("ms]"));
}

#[test]
fn test_cli_run_with_time_full() {
    let root = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).parent().unwrap().parent().unwrap();
    let file = root.join("sort.ucaba");
    let output = Command::new(env!("CARGO_BIN_EXE_ucaba"))
        .args(["run", file.to_str().unwrap(), "--time-full"])
        .output()
        .expect("Failed to execute ucaba run --time-full");

    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("[Tiempo total:"));
    assert!(stdout.contains("Horas") || stdout.contains("Hora"));
    assert!(stdout.contains("Milisegundos") || stdout.contains("Milisegundo"));
}

#[test]
fn test_cli_update_check() {
    let output = Command::new(env!("CARGO_BIN_EXE_ucaba"))
        .args(["update", "--check"])
        .output()
        .expect("Failed to execute ucaba update --check");

    let stdout = String::from_utf8_lossy(&output.stdout);
    let stderr = String::from_utf8_lossy(&output.stderr);

    if output.status.success() {
        assert!(
            stdout.contains("UCABA") || stdout.contains("Comprobando versiones"),
            "Salida inesperada en update --check: {}",
            stdout
        );
    } else {
        assert!(
            stderr.contains("No se pudo consultar GitHub Releases")
                || stdout.contains("Comprobando versiones"),
            "update --check falló sin mensaje controlado: stdout='{}', stderr='{}'",
            stdout,
            stderr
        );
    }
}

#[test]
fn test_cli_repl_expression_evaluation() {
    use std::io::Write;

    let mut child = Command::new(env!("CARGO_BIN_EXE_ucaba"))
        .arg("repl")
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .expect("Failed to spawn ucaba repl");

    {
        let stdin = child.stdin.as_mut().expect("Failed to open stdin");
        stdin.write_all(b"10 + 25\n:salir\n").expect("Failed to write to stdin");
    }

    let output = child.wait_with_output().expect("Failed to wait on child");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("=> 35"));
    assert!(stdout.contains("Hasta luego"));
}

#[test]
fn test_cli_repl_variables_and_multiline() {
    use std::io::Write;

    let input = b"ENTERO n = 7\nFUNCION triple(x: ENTERO): ENTERO\n    RETORNAR x * 3\nFIN FUNCION\ntriple(n)\n:vars\n:salir\n";

    let mut child = Command::new(env!("CARGO_BIN_EXE_ucaba"))
        .arg("repl")
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .expect("Failed to spawn ucaba repl");

    {
        let stdin = child.stdin.as_mut().expect("Failed to open stdin");
        stdin.write_all(input).expect("Failed to write to stdin");
    }

    let output = child.wait_with_output().expect("Failed to wait on child");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("=> 21"));
    assert!(stdout.contains("NOMBRE"));
    assert!(stdout.contains("TIPO"));
    assert!(stdout.contains("VALOR"));
    assert!(stdout.contains("n"));
    assert!(stdout.contains("ENTERO"));
    assert!(stdout.contains("7"));
}

#[test]
fn test_cli_repl_help_and_clear() {
    use std::io::Write;

    let mut child = Command::new(env!("CARGO_BIN_EXE_ucaba"))
        .arg("repl")
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .expect("Failed to spawn ucaba repl");

    {
        let stdin = child.stdin.as_mut().expect("Failed to open stdin");
        stdin.write_all(b":ayuda\n:limpiar\n:salir\n").expect("Failed to write to stdin");
    }

    let output = child.wait_with_output().expect("Failed to wait on child");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("Comandos del REPL"));
    assert!(stdout.contains("Entorno y variables reiniciados"));
}

#[test]
fn test_cli_default_launches_repl_on_empty_args() {
    use std::io::Write;

    let mut child = Command::new(env!("CARGO_BIN_EXE_ucaba"))
        .stdin(std::process::Stdio::piped())
        .stdout(std::process::Stdio::piped())
        .spawn()
        .expect("Failed to spawn ucaba without args");

    {
        let stdin = child.stdin.as_mut().expect("Failed to open stdin");
        stdin.write_all(b"6 * 7\n:salir\n").expect("Failed to write to stdin");
    }

    let output = child.wait_with_output().expect("Failed to wait on child");
    assert!(output.status.success());
    let stdout = String::from_utf8_lossy(&output.stdout);
    assert!(stdout.contains("=> 42"));
}

