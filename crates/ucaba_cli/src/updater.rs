//! Verificación de nuevas versiones de UCABA contra GitHub Releases.
//! Port del módulo `pseudocode/updater.py`: comparte formato de caché (`version_cache.json`).

use serde_json::{json, Value};
use std::path::PathBuf;
use std::thread::JoinHandle;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

pub const GITHUB_REPO: &str = "caidevOficial/UCABA_Lang";
const CACHE_TTL_SECS: f64 = 3600.0;

#[derive(Clone, Debug)]
pub struct ReleaseInfo {
    pub latest_version: String,
    pub html_url: String,
    pub installer_url: String,
}

#[derive(Debug)]
pub enum VersionStatus {
    UpdateAvailable(ReleaseInfo),
    UpToDate,
    NetworkError,
}

/// Parsea 'v2.0.1' / '2.0.1' / '2.0.1-beta' a una tupla comparable.
pub fn parse_version(v: &str) -> Vec<u64> {
    v.trim()
        .trim_start_matches(['v', 'V'])
        .split('.')
        .map(|piece| {
            let digits: String = piece.chars().take_while(|c| c.is_ascii_digit()).collect();
            digits.parse().unwrap_or(0)
        })
        .collect()
}

fn is_newer(latest: &str, current: &str) -> bool {
    let (mut a, mut b) = (parse_version(latest), parse_version(current));
    let n = a.len().max(b.len());
    a.resize(n, 0);
    b.resize(n, 0);
    a > b
}

fn cache_path() -> Option<PathBuf> {
    let dir = match std::env::var_os("LOCALAPPDATA") {
        Some(p) => PathBuf::from(p).join("UCABA"),
        None => PathBuf::from(std::env::var_os("USERPROFILE").or_else(|| std::env::var_os("HOME"))?)
            .join(".ucaba"),
    };
    std::fs::create_dir_all(&dir).ok()?;
    Some(dir.join("version_cache.json"))
}

fn now_secs() -> f64 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map(|d| d.as_secs_f64())
        .unwrap_or(0.0)
}

fn info_from_value(v: &Value) -> Option<ReleaseInfo> {
    let latest = v.get("latest_version")?.as_str()?.to_string();
    if latest.is_empty() {
        return None;
    }
    let s = |k: &str| v.get(k).and_then(Value::as_str).unwrap_or("").to_string();
    Some(ReleaseInfo {
        latest_version: latest,
        html_url: {
            let u = s("html_url");
            if u.is_empty() {
                format!("https://github.com/{GITHUB_REPO}/releases/latest")
            } else {
                u
            }
        },
        installer_url: s("installer_url"),
    })
}

fn read_cache() -> Option<ReleaseInfo> {
    let text = std::fs::read_to_string(cache_path()?).ok()?;
    let v: Value = serde_json::from_str(&text).ok()?;
    let last = v.get("last_checked")?.as_f64()?;
    if now_secs() - last < CACHE_TTL_SECS {
        info_from_value(&v)
    } else {
        None
    }
}

fn write_cache(info: &ReleaseInfo) {
    if let Some(path) = cache_path() {
        let v = json!({
            "latest_version": info.latest_version,
            "tag_name": format!("v{}", info.latest_version),
            "html_url": info.html_url,
            "installer_url": info.installer_url,
            "last_checked": now_secs(),
        });
        let _ = std::fs::write(path, serde_json::to_string_pretty(&v).unwrap_or_default());
    }
}

pub fn fetch_latest_release(timeout: Duration) -> Option<ReleaseInfo> {
    let url = format!("https://api.github.com/repos/{GITHUB_REPO}/releases/latest");
    let body = ureq::get(&url)
        .set("User-Agent", "UCABA-Lang-Updater")
        .set("Accept", "application/vnd.github.v3+json")
        .timeout(timeout)
        .call()
        .ok()?
        .into_string()
        .ok()?;
    let payload: Value = serde_json::from_str(&body).ok()?;
    let tag = payload.get("tag_name")?.as_str()?;
    let installer_url = payload
        .get("assets")
        .and_then(Value::as_array)
        .and_then(|assets| {
            assets.iter().find(|a| {
                a.get("name")
                    .and_then(Value::as_str)
                    .is_some_and(|n| n.eq_ignore_ascii_case("instalador_ucaba.exe"))
            })
        })
        .and_then(|a| a.get("browser_download_url")?.as_str())
        .unwrap_or("")
        .to_string();
    let info = ReleaseInfo {
        latest_version: tag.trim_start_matches(['v', 'V']).to_string(),
        html_url: payload
            .get("html_url")
            .and_then(Value::as_str)
            .map(String::from)
            .unwrap_or_else(|| format!("https://github.com/{GITHUB_REPO}/releases/latest")),
        installer_url,
    };
    write_cache(&info);
    Some(info)
}

pub fn check_version_status(current: &str, force_online: bool, timeout: Duration) -> VersionStatus {
    let info = if force_online {
        fetch_latest_release(timeout)
    } else {
        match read_cache() {
            // Caché fresca con versión superior: usarla sin red.
            Some(c) if is_newer(&c.latest_version, current) => Some(c),
            cached => fetch_latest_release(timeout).or(cached),
        }
    };
    match info {
        None => VersionStatus::NetworkError,
        Some(i) if is_newer(&i.latest_version, current) => VersionStatus::UpdateAvailable(i),
        Some(_) => VersionStatus::UpToDate,
    }
}

pub fn print_update_notice(info: &ReleaseInfo, current: &str) {
    eprintln!(
        "\n\x1b[33m[AVISO] Hay una nueva versión de UCABA disponible: \x1b[1m{current}\x1b[0m\x1b[33m -> \x1b[1;32m{}\x1b[0m",
        info.latest_version
    );
    eprintln!("\x1b[33mPara actualizar automáticamente, ejecuta: \x1b[1;37mucaba update\x1b[0m");
    eprintln!("\x1b[90mO visita: {}\x1b[0m\n", info.html_url);
}

fn background_check_disabled() -> bool {
    ["UCABA_NO_UPDATE_CHECK", "UCABA_HIDE_BANNER"]
        .iter()
        .any(|k| std::env::var(k).ok().as_deref() == Some("1"))
        || std::env::var("CI").ok().as_deref() == Some("true")
        || std::env::var_os("GITHUB_ACTIONS").is_some()
}

/// Comprobación no bloqueante en segundo plano (estilo pip).
pub struct BackgroundCheck {
    handle: Option<JoinHandle<Option<ReleaseInfo>>>,
    current: String,
}

impl BackgroundCheck {
    pub fn start(current: &str) -> Self {
        let cur = current.to_string();
        let handle = if background_check_disabled() {
            None
        } else {
            let c = cur.clone();
            Some(std::thread::spawn(move || {
                match check_version_status(&c, false, Duration::from_secs(3)) {
                    VersionStatus::UpdateAvailable(i) => Some(i),
                    _ => None,
                }
            }))
        };
        Self { handle, current: cur }
    }

    /// Espera hasta `wait` y, si hay una versión nueva, muestra el aviso.
    pub fn finish(mut self, wait: Duration) {
        let Some(handle) = self.handle.take() else { return };
        let deadline = std::time::Instant::now() + wait;
        while !handle.is_finished() {
            if std::time::Instant::now() >= deadline {
                return;
            }
            std::thread::sleep(Duration::from_millis(20));
        }
        if let Ok(Some(info)) = handle.join() {
            print_update_notice(&info, &self.current);
        }
    }
}

/// `ucaba update --check`: consulta siempre en línea. Devuelve código de salida.
pub fn run_check(current: &str) -> i32 {
    println!("Comprobando versiones en GitHub ({current})...");
    match check_version_status(current, true, Duration::from_secs(5)) {
        VersionStatus::UpdateAvailable(i) => {
            println!(
                "[ACTUALIZACIÓN DISPONIBLE] v{current} -> v{}\nEjecuta 'ucaba update' o visita: {}",
                i.latest_version, i.html_url
            );
            0
        }
        VersionStatus::UpToDate => {
            println!("[OK] UCABA Rust Engine v{current} está al día.");
            0
        }
        VersionStatus::NetworkError => {
            eprintln!("[ERROR] No se pudo consultar GitHub Releases. Verifica tu conexión a internet.");
            1
        }
    }
}

/// `ucaba update`: descarga y lanza el instalador oficial del último release.
pub fn run_update(current: &str) -> i32 {
    println!("Versión actual instalada: v{current}\nComprobando últimas versiones en GitHub Releases...");
    let info = match check_version_status(current, true, Duration::from_secs(5)) {
        VersionStatus::NetworkError => {
            eprintln!("[ERROR] No se pudo conectar con GitHub Releases. Verifica tu conexión a internet.");
            return 1;
        }
        VersionStatus::UpToDate => {
            println!("[OK] ¡Ya tienes la versión más reciente de UCABA (v{current})!");
            return 0;
        }
        VersionStatus::UpdateAvailable(i) => i,
    };
    println!("[ACTUALIZACIÓN DISPONIBLE]: v{current} -> v{}", info.latest_version);
    if info.installer_url.is_empty() {
        eprintln!(
            "[ERROR] El release v{} no incluye 'Instalador_UCABA.exe'. Descárgalo manualmente: {}",
            info.latest_version, info.html_url
        );
        return 1;
    }
    let dir = std::env::temp_dir().join(format!("ucaba_update_{}", std::process::id()));
    let path = dir.join("Instalador_UCABA.exe");
    println!("Descargando instalador desde {} ...", info.installer_url);
    let result = (|| -> Result<(), String> {
        std::fs::create_dir_all(&dir).map_err(|e| e.to_string())?;
        let resp = ureq::get(&info.installer_url)
            .set("User-Agent", "UCABA-Lang-Updater")
            .timeout(Duration::from_secs(300))
            .call()
            .map_err(|e| e.to_string())?;
        let mut file = std::fs::File::create(&path).map_err(|e| e.to_string())?;
        std::io::copy(&mut resp.into_reader(), &mut file).map_err(|e| e.to_string())?;
        Ok(())
    })();
    if let Err(e) = result {
        eprintln!("[ERROR] Falló la descarga del instalador: {e}");
        return 1;
    }
    match std::process::Command::new(&path).spawn() {
        Ok(_) => {
            println!("[ÉXITO] Asistente de instalación iniciado. Sigue las instrucciones en pantalla.");
            0
        }
        Err(e) => {
            eprintln!("[ERROR] No se pudo ejecutar el instalador: {e}\nEjecútalo manualmente: {}", path.display());
            1
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn compara_versiones() {
        assert!(is_newer("2.0.1", "2.0.0"));
        assert!(is_newer("v2.1", "2.0.9"));
        assert!(!is_newer("2.0.0", "2.0.0"));
        assert!(!is_newer("2.0", "2.0.0"));
        assert!(!is_newer("1.9.9", "2.0.0"));
    }
}
