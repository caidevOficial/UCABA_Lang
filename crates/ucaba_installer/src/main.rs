// GNU General Public License v3.0 or later (GPL-3.0-or-later)
//
// Copyright (c) 2026 [Facu Falcone](a.facundo.falcone@gmail.com) All rights reserved.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use eframe::egui::{self, Color32, Margin, RichText, Rounding, Stroke};
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::mpsc::{channel, Receiver, Sender};
use std::thread;

#[cfg(windows)]
use std::os::windows::process::CommandExt;

#[cfg(windows)]
const CREATE_NO_WINDOW: u32 = 0x08000000;

fn silent_command<S: AsRef<std::ffi::OsStr>>(program: S) -> Command {
    let mut cmd = Command::new(program);
    #[cfg(windows)]
    cmd.creation_flags(CREATE_NO_WINDOW);
    cmd
}

fn run_powershell_script(script: &str) -> std::io::Result<std::process::Output> {
    silent_command("powershell")
        .arg("-NoProfile")
        .arg("-NonInteractive")
        .arg("-WindowStyle")
        .arg("Hidden")
        .arg("-Command")
        .arg(script)
        .output()
}


// Assets embebidos directamente en el binario del instalador
const UCABA_EXE_BYTES: &[u8] = include_bytes!("../../../target/release/ucaba.exe");
const UCABA_ICON_BYTES: &[u8] = include_bytes!("../../../ucaba_icon.ico");
const UCABA_ICON_PNG_BYTES: &[u8] = include_bytes!("../../../ucaba_icon.png");
#[allow(dead_code)]
const UCABA_LOGO_BYTES: &[u8] = include_bytes!("../../../ucaba_logo_header.png");
const VSCODE_VSIX_BYTES: &[u8] = include_bytes!("../../../extension-vscode/ucaba-language-support-2.1.0.vsix");
const UCABA_VERSION: &str = "2.1.0";

fn current_time_str() -> String {
    let dur = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default();
    let secs = dur.as_secs();
    let sec = secs % 60;
    let min = (secs / 60) % 60;
    let hour = (secs / 3600) % 24;
    format!("{:02}:{:02}:{:02}", hour, min, sec)
}

enum InstallMsg {
    Progress(f32, String),
    Log(String),
    DoneInstall,
    DoneUninstall,
    Error(String),
}

struct InstallerApp {
    status_text: String,
    progress: f32,
    is_busy: bool,
    is_completed: bool,
    is_uninstalled: bool,
    logs: Vec<String>,
    logo_texture: Option<egui::TextureHandle>,

    install_dir: String,
    opt_install_cli: bool,
    opt_add_path: bool,
    opt_install_vscode: bool,
    opt_associate_ext: bool,

    rx: Option<Receiver<InstallMsg>>,
}

impl Default for InstallerApp {
    fn default() -> Self {
        let default_dir = std::env::var("LOCALAPPDATA")
            .map(|p| format!(r"{}\Programs\UCABA\bin", p))
            .unwrap_or_else(|_| r"C:\UCABA\bin".to_string());

        Self {
            status_text: "Listo para instalar.".to_string(),
            progress: 0.0,
            is_busy: false,
            is_completed: false,
            is_uninstalled: false,
            logs: vec![
                format!(
                    "[{}] Asistente de instalación de UCABA v{} iniciado | Autor: <Facu Falcone>",
                    current_time_str(),
                    UCABA_VERSION
                ),
                format!(
                    "[{}] Seleccione los componentes deseados y presione 'Instalar Ahora'.",
                    current_time_str()
                ),
            ],
            logo_texture: None,

            install_dir: default_dir,
            opt_install_cli: true,
            opt_add_path: true,
            opt_install_vscode: true,
            opt_associate_ext: true,

            rx: None,
        }
    }
}

impl eframe::App for InstallerApp {
    fn update(&mut self, ctx: &egui::Context, _frame: &mut eframe::Frame) {
        // Cargar textura del logo en el primer cuadro si aún no está en memoria
        if self.logo_texture.is_none() {
            if let Ok(img) = image::load_from_memory(UCABA_ICON_PNG_BYTES) {
                let rgba = img.to_rgba8();
                let size = [rgba.width() as usize, rgba.height() as usize];
                let pixels = rgba.into_raw();
                let color_image = egui::ColorImage::from_rgba_unmultiplied(size, &pixels);
                self.logo_texture = Some(ctx.load_texture("ucaba_logo", color_image, egui::TextureOptions::LINEAR));
            }
        }

        // Configuración de paleta oficial Dark Electric Blue & Jaguar Gamer (UCABA 2.X)
        let mut visuals = egui::Visuals::dark();
        visuals.panel_fill = Color32::from_rgb(8, 12, 20); // #080c14 base noche espacial
        visuals.window_fill = Color32::from_rgb(8, 12, 20);
        visuals.extreme_bg_color = Color32::from_rgb(5, 8, 15); // #05080f
        visuals.faint_bg_color = Color32::from_rgb(15, 23, 42); // #0f172a
        visuals.override_text_color = Some(Color32::from_rgb(224, 242, 254)); // #e0f2fe

        // Widgets inactivos y bordes
        visuals.widgets.inactive.bg_fill = Color32::from_rgb(14, 23, 38); // #0e1726
        visuals.widgets.inactive.bg_stroke = Stroke::new(1.0_f32, Color32::from_rgb(30, 58, 138)); // #1e3a8a
        visuals.widgets.inactive.fg_stroke = Stroke::new(1.0_f32, Color32::from_rgb(224, 242, 254));

        // Hover interactivo
        visuals.widgets.hovered.bg_fill = Color32::from_rgb(0, 102, 255); // #0066ff
        visuals.widgets.hovered.bg_stroke = Stroke::new(1.5_f32, Color32::from_rgb(56, 189, 248)); // #38bdf8
        visuals.widgets.hovered.fg_stroke = Stroke::new(1.5_f32, Color32::WHITE);

        // Click activo
        visuals.widgets.active.bg_fill = Color32::from_rgb(0, 82, 204); // #0052cc
        visuals.widgets.active.bg_stroke = Stroke::new(2.0_f32, Color32::from_rgb(0, 212, 255)); // #00d4ff
        visuals.widgets.active.fg_stroke = Stroke::new(2.0_f32, Color32::WHITE);

        visuals.selection.bg_fill = Color32::from_rgb(0, 102, 255); // #0066ff
        ctx.set_visuals(visuals);

        // Polling de mensajes del hilo de instalación/desinstalación
        let mut msg_received = false;
        if let Some(ref rx) = self.rx {
            while let Ok(msg) = rx.try_recv() {
                msg_received = true;
                match msg {
                    InstallMsg::Progress(val, st) => {
                        self.progress = val;
                        self.status_text = st;
                    }
                    InstallMsg::Log(line) => {
                        self.logs.push(format!("[{}] {}", current_time_str(), line));
                    }
                    InstallMsg::DoneInstall => {
                        self.progress = 1.0;
                        self.is_busy = false;
                        self.is_completed = true;
                        self.status_text = "¡Instalación completada exitosamente!".to_string();
                        self.logs.push(format!("[{}] >>> ¡PROCESO FINALIZADO CON ÉXITO! <<<", current_time_str()));
                        self.logs.push(format!("[{}] Ya puede ejecutar 'ucaba run <archivo.ucaba>' en cualquier consola.", current_time_str()));
                    }
                    InstallMsg::DoneUninstall => {
                        self.progress = 1.0;
                        self.is_busy = false;
                        self.is_uninstalled = true;
                        self.status_text = "¡Desinstalación completada con éxito!".to_string();
                    }
                    InstallMsg::Error(err) => {
                        self.is_busy = false;
                        self.status_text = format!("Error: {}", err);
                        self.logs.push(format!("[{}] [ERROR CRÍTICO]: {}", current_time_str(), err));
                    }
                }
            }
        }
        if msg_received {
            ctx.request_repaint();
        }

        // ====================================================================
        // 1. PANEL SUPERIOR (CABECERA INSTITUCIONAL)
        // ====================================================================
        let header_frame = egui::Frame::none()
            .fill(Color32::from_rgb(15, 23, 42)) // #0f172a
            .stroke(Stroke::new(1.0_f32, Color32::from_rgb(30, 58, 138))) // #1e3a8a
            .inner_margin(Margin { left: 20.0, right: 20.0, top: 14.0, bottom: 14.0 });

        egui::TopBottomPanel::top("header_panel")
            .frame(header_frame)
            .show(ctx, |ui| {
                ui.horizontal(|ui| {
                    // Isotipo institucional oficial
                    if let Some(texture) = &self.logo_texture {
                        ui.add(egui::Image::new(texture).fit_to_exact_size(egui::vec2(52.0, 52.0)));
                        ui.add_space(14.0);
                    }

                    // Bloque de títulos y badges
                    ui.vertical(|ui| {
                        ui.horizontal(|ui| {
                            ui.label(
                                RichText::new("UCABA")
                                    .size(24.0)
                                    .color(Color32::WHITE)
                                    .strong(),
                            );
                            ui.add_space(8.0);

                            // Pill de versión
                            egui::Frame::none()
                                .fill(Color32::from_rgb(30, 58, 138)) // #1e3a8a
                                .stroke(Stroke::new(1.0_f32, Color32::from_rgb(56, 189, 248))) // #38bdf8
                                .rounding(Rounding::same(4.0))
                                .inner_margin(Margin { left: 8.0, right: 8.0, top: 2.0, bottom: 2.0 })
                                .show(ui, |ui| {
                                    ui.label(
                                        RichText::new("v2.1.0")
                                            .size(11.0)
                                            .strong()
                                            .color(Color32::from_rgb(224, 242, 254)),
                                    );
                                });

                            ui.add_space(6.0);

                            // Pill de motor Rust
                            egui::Frame::none()
                                .fill(Color32::from_rgb(15, 43, 92)) // #0f2b5c
                                .stroke(Stroke::new(1.0_f32, Color32::from_rgb(0, 102, 255))) // #0066ff
                                .rounding(Rounding::same(4.0))
                                .inner_margin(Margin { left: 8.0, right: 8.0, top: 2.0, bottom: 2.0 })
                                .show(ui, |ui| {
                                    ui.label(
                                        RichText::new("Rust Engine")
                                            .size(10.0)
                                            .strong()
                                            .color(Color32::from_rgb(186, 230, 253)),
                                    );
                                });
                        });

                        ui.add_space(2.0);
                        ui.label(
                            RichText::new(format!(
                                "Instalador del Lenguaje (v{}) & Extensión para Visual Studio Code",
                                UCABA_VERSION
                            ))
                            .size(11.5)
                            .color(Color32::from_rgb(0, 212, 255)), // #00d4ff
                        );
                    });

                    // Insignia de Autoría a la derecha
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        egui::Frame::none()
                            .fill(Color32::from_rgb(15, 43, 92)) // #0f2b5c
                            .stroke(Stroke::new(1.0_f32, Color32::from_rgb(2, 132, 199))) // #0284c7
                            .rounding(Rounding::same(6.0))
                            .inner_margin(Margin { left: 14.0, right: 14.0, top: 6.0, bottom: 6.0 })
                            .show(ui, |ui| {
                                ui.label(
                                    RichText::new("Autor: <Facu Falcone>")
                                        .size(11.0)
                                        .strong()
                                        .color(Color32::from_rgb(125, 211, 252)), // #7dd3fc
                                );
                            });
                    });
                });
            });

        // ====================================================================
        // 2. PANEL INFERIOR (ESTADO Y BOTONERA DE ACCIÓN)
        // ====================================================================
        let footer_frame = egui::Frame::none()
            .fill(Color32::from_rgb(15, 23, 42)) // #0f172a
            .stroke(Stroke::new(1.0_f32, Color32::from_rgb(30, 58, 138))) // #1e3a8a
            .inner_margin(Margin { left: 20.0, right: 20.0, top: 12.0, bottom: 12.0 });

        egui::TopBottomPanel::bottom("footer_panel")
            .frame(footer_frame)
            .show(ctx, |ui| {
                ui.horizontal(|ui| {
                    // Estado dinámico
                    let (status_icon, status_color) = if self.is_completed || self.is_uninstalled {
                        ("✔ ", Color32::from_rgb(74, 222, 128)) // Verde
                    } else if self.is_busy {
                        ("⏳ ", Color32::from_rgb(56, 189, 248)) // Azul celeste
                    } else if self.status_text.starts_with("Error") {
                        ("✖ ", Color32::from_rgb(248, 113, 113)) // Rojo
                    } else {
                        ("● ", Color32::from_rgb(56, 189, 248)) // Cyan neón
                    };

                    ui.label(
                        RichText::new(format!("{}{}", status_icon, self.status_text))
                            .size(11.5)
                            .color(status_color)
                            .strong(),
                    );

                    // Botonera alineada a la derecha
                    ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                        // Botón Primario: Instalar Ahora
                        let install_btn = egui::Button::new(
                            RichText::new("  Instalar Ahora  ")
                                .size(13.0)
                                .color(Color32::WHITE)
                                .strong(),
                        )
                        .fill(if self.is_busy {
                            Color32::from_rgb(15, 23, 42) // #0f172a
                        } else {
                            Color32::from_rgb(0, 102, 255) // #0066ff
                        });

                        if ui
                            .add_enabled(!self.is_busy, install_btn)
                            .on_hover_text("Inicia la instalación completa de UCABA 2.1.0 y su extensión")
                            .clicked()
                        {
                            self.start_installation();
                        }

                        ui.add_space(8.0);

                        // Botón Secundario: Desinstalar
                        let uninstall_btn = egui::Button::new(
                            RichText::new(" Desinstalar ")
                                .size(11.5)
                                .color(Color32::WHITE),
                        )
                        .fill(Color32::from_rgb(153, 27, 27)); // #991b1b

                        if ui
                            .add_enabled(!self.is_busy, uninstall_btn)
                            .on_hover_text("Remueve el binario ucaba.exe, quita del PATH y retira extensiones")
                            .clicked()
                        {
                            self.start_uninstallation();
                        }

                        ui.add_space(8.0);

                        // Botón Salir / Cerrar
                        let exit_btn = egui::Button::new(
                            RichText::new("  Cerrar  ")
                                .size(11.5)
                                .color(Color32::from_rgb(224, 242, 254)),
                        )
                        .fill(Color32::from_rgb(30, 41, 59)); // #1e293b

                        if ui.add(exit_btn).clicked() {
                            std::process::exit(0);
                        }
                    });
                });
            });

        // ====================================================================
        // 3. PANEL CENTRAL (OPCIONES, PROGRESO Y CONSOLA DE LOGS)
        // ====================================================================
        let central_frame = egui::Frame::none()
            .fill(Color32::from_rgb(8, 12, 20)) // #080c14
            .inner_margin(Margin { left: 20.0, right: 20.0, top: 14.0, bottom: 14.0 });

        egui::CentralPanel::default()
            .frame(central_frame)
            .show(ctx, |ui| {
                // Tarjeta 1: Opciones de Configuración
                let card_frame = egui::Frame::none()
                    .fill(Color32::from_rgb(14, 23, 38)) // #0e1726
                    .stroke(Stroke::new(1.0_f32, Color32::from_rgb(30, 58, 138))) // #1e3a8a
                    .rounding(Rounding::same(8.0))
                    .inner_margin(Margin { left: 16.0, right: 16.0, top: 12.0, bottom: 12.0 });

                card_frame.show(ui, |ui| {
                    ui.label(
                        RichText::new("Componentes y Tareas de Instalación:")
                            .size(13.0)
                            .color(Color32::from_rgb(240, 249, 255))
                            .strong(),
                    );
                    ui.add_space(6.0);

                    ui.add_enabled(
                        !self.is_busy,
                        egui::Checkbox::new(
                            &mut self.opt_install_cli,
                            RichText::new("Instalar ejecutable nativo 'ucaba.exe' en %LOCALAPPDATA%\\Programs\\UCABA\\bin")
                                .size(11.5)
                                .color(Color32::from_rgb(224, 242, 254)),
                        ),
                    );
                    ui.add_space(3.0);

                    ui.add_enabled(
                        !self.is_busy,
                        egui::Checkbox::new(
                            &mut self.opt_add_path,
                            RichText::new("Agregar UCABA a la variable de entorno PATH (usar 'ucaba' desde cualquier terminal)")
                                .size(11.5)
                                .color(Color32::from_rgb(224, 242, 254)),
                        ),
                    );
                    ui.add_space(3.0);

                    ui.add_enabled(
                        !self.is_busy,
                        egui::Checkbox::new(
                            &mut self.opt_install_vscode,
                            RichText::new("Instalar extensión oficial en Visual Studio Code y Antigravity (coloreado, linter y LSP)")
                                .size(11.5)
                                .color(Color32::from_rgb(224, 242, 254)),
                        ),
                    );
                    ui.add_space(3.0);

                    ui.add_enabled(
                        !self.is_busy,
                        egui::Checkbox::new(
                            &mut self.opt_associate_ext,
                            RichText::new("Asociar archivos .ucaba en Windows (icono oficial del lenguaje y comando 'Abrir/Ejecutar')")
                                .size(11.5)
                                .color(Color32::from_rgb(224, 242, 254)),
                        ),
                    );

                    ui.add_space(8.0);
                    ui.separator();
                    ui.add_space(6.0);

                    // Ruta de instalación editable
                    ui.horizontal(|ui| {
                        ui.label(
                            RichText::new("Directorio de Instalación:")
                                .size(11.0)
                                .color(Color32::from_rgb(56, 189, 248)) // #38bdf8
                                .strong(),
                        );
                        ui.add_space(4.0);
                        ui.add_enabled(
                            !self.is_busy,
                            egui::TextEdit::singleline(&mut self.install_dir)
                                .desired_width(f32::INFINITY)
                                .font(egui::TextStyle::Monospace),
                        );
                    });
                });

                ui.add_space(10.0);

                // Barra de Progreso
                let progress_bar = egui::ProgressBar::new(self.progress)
                    .show_percentage()
                    .animate(self.is_busy)
                    .fill(Color32::from_rgb(0, 102, 255)); // #0066ff
                ui.add_sized([ui.available_width(), 16.0], progress_bar);

                ui.add_space(10.0);

                // Fila de Cabecera de la Consola de Logs
                ui.horizontal(|ui| {
                    ui.label(
                        RichText::new("Registro de eventos:")
                            .size(12.0)
                            .color(Color32::from_rgb(56, 189, 248)) // #38bdf8
                            .strong(),
                    );

                    if self.is_completed {
                        ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                            let open_cmd_btn = egui::Button::new(
                                RichText::new(" ▶ Probar 'ucaba --version' en PowerShell ")
                                    .size(11.0)
                                    .color(Color32::WHITE)
                                    .strong(),
                            )
                            .fill(Color32::from_rgb(0, 102, 255)); // Azul eléctrico

                            if ui.add(open_cmd_btn).clicked() {
                                let _ = Command::new("powershell.exe")
                                    .arg("-NoExit")
                                    .arg("-Command")
                                    .arg("ucaba --version; Write-Host ''; Write-Host '¡UCABA 2.1.0 está listo para ser utilizado!' -ForegroundColor Cyan")
                                    .spawn();
                            }
                        });
                    }
                });

                ui.add_space(4.0);

                // Tarjeta 2: Consola de Logs estilo Terminal
                let log_frame = egui::Frame::none()
                    .fill(Color32::from_rgb(5, 8, 15)) // #05080f
                    .stroke(Stroke::new(1.0_f32, Color32::from_rgb(30, 58, 138))) // #1e3a8a
                    .rounding(Rounding::same(6.0))
                    .inner_margin(Margin { left: 10.0, right: 10.0, top: 8.0, bottom: 8.0 });

                log_frame.show(ui, |ui| {
                    egui::ScrollArea::vertical()
                        .max_height(ui.available_height())
                        .stick_to_bottom(true)
                        .auto_shrink([false, false])
                        .show(ui, |ui| {
                            for log in &self.logs {
                                ui.monospace(
                                    RichText::new(log)
                                        .color(Color32::from_rgb(186, 230, 253)) // #bae6fd
                                        .size(11.0),
                                );
                            }
                        });
                });
            });
    }
}

impl InstallerApp {
    fn start_installation(&mut self) {
        self.is_busy = true;
        self.is_completed = false;
        self.is_uninstalled = false;
        self.progress = 0.05;
        self.status_text = "Iniciando instalación...".to_string();
        self.logs.push(format!("[{}] Iniciando tareas de instalación seleccionadas...", current_time_str()));

        let (tx, rx) = channel();
        self.rx = Some(rx);

        let cfg = InstallConfig {
            target_dir: self.install_dir.clone(),
            install_cli: self.opt_install_cli,
            add_path: self.opt_add_path,
            install_vscode: self.opt_install_vscode,
            associate_ext: self.opt_associate_ext,
        };

        thread::spawn(move || {
            if let Err(e) = run_installation_pipeline(tx.clone(), cfg) {
                let _ = tx.send(InstallMsg::Error(e));
            }
        });
    }

    fn start_uninstallation(&mut self) {
        self.is_busy = true;
        self.is_completed = false;
        self.is_uninstalled = false;
        self.progress = 0.05;
        self.status_text = "Iniciando desinstalación...".to_string();
        self.logs.push(format!("[{}] Iniciando tareas de desinstalación...", current_time_str()));

        let (tx, rx) = channel();
        self.rx = Some(rx);

        let target_dir = self.install_dir.clone();

        thread::spawn(move || {
            run_uninstallation_pipeline(tx, target_dir);
        });
    }
}

struct InstallConfig {
    target_dir: String,
    install_cli: bool,
    add_path: bool,
    install_vscode: bool,
    associate_ext: bool,
}

#[cfg(windows)]
fn ensure_clean_environment_and_break_away() {
    // Si fuimos invocados desde una versión anterior en Python empaquetada con PyInstaller,
    // heredamos variables (_MEIPASS2) y handles abiertos al directorio temporal _MEIxxxxxx
    // y al propio ucaba.exe. Para liberar inmediatamente el proceso padre de Python y sus bloqueos,
    // nos re-lanzamos de forma limpia con bInheritHandles = FALSE y salimos de inmediato.
    if std::env::var("UCABA_RESPAWNED_CLEAN").is_err()
        && (std::env::var("_MEIPASS2").is_ok() || std::env::var("_MEIPASS").is_ok())
    {
        if let Ok(current_exe) = std::env::current_exe() {
            let mut cmd = Command::new(current_exe);
            cmd.args(std::env::args().skip(1));
            cmd.env_remove("_MEIPASS2");
            cmd.env_remove("_MEIPASS");
            cmd.env("UCABA_RESPAWNED_CLEAN", "1");

            if cmd.spawn().is_ok() {
                std::process::exit(0);
            }
        }
    }
}

fn cleanup_pyinstaller_temp_dirs(tx: Option<&Sender<InstallMsg>>) {
    let temp = std::env::temp_dir();
    if let Ok(entries) = fs::read_dir(&temp) {
        let mut cleaned_count = 0;
        for entry in entries.flatten() {
            if let Ok(ft) = entry.file_type() {
                if ft.is_dir() {
                    let name = entry.file_name().to_string_lossy().to_string();
                    if name.starts_with("_MEI") {
                        let path = entry.path();
                        let is_pyinstaller_orphan = path.join("pseudocode").exists()
                            || path.join("ucaba_icon.ico").exists()
                            || path.join("ucaba.exe").exists()
                            || path.join("base_library.zip").exists()
                            || path.join("VCRUNTIME140.dll").exists()
                            || path.join("python310.dll").exists()
                            || path.join("python311.dll").exists()
                            || path.join("python312.dll").exists()
                            || path.join("python313.dll").exists();
                        if is_pyinstaller_orphan {
                            if fs::remove_dir_all(&path).is_ok() {
                                cleaned_count += 1;
                            }
                        }
                    }
                }
            }
        }
        if cleaned_count > 0 {
            if let Some(sender) = tx {
                let _ = sender.send(InstallMsg::Log(format!(
                    "[OK] Limpieza: eliminadas {} carpetas temporales residuales de PyInstaller (_MEI*) en %TEMP%",
                    cleaned_count
                )));
            }
        }
    }
}

fn terminate_running_ucaba_processes() {
    #[cfg(windows)]
    {
        let _ = silent_command("taskkill")
            .arg("/F")
            .arg("/IM")
            .arg("ucaba.exe")
            .arg("/T")
            .output();
    }
}

fn cleanup_old_executables(exe_path: &Path) {
    if let Some(parent) = exe_path.parent() {
        if let Ok(entries) = fs::read_dir(parent) {
            for entry in entries.flatten() {
                let name = entry.file_name().to_string_lossy().to_lowercase();
                if (name.starts_with("ucaba.old_") || name.starts_with("ucaba_old_") || name.ends_with(".bak"))
                    && name.ends_with(".exe")
                {
                    let _ = fs::remove_file(entry.path());
                }
            }
        }
    }
}

fn safe_write_executable(
    exe_path: &Path,
    bytes: &[u8],
    tx: &Sender<InstallMsg>,
) -> Result<(), String> {
    cleanup_old_executables(exe_path);

    // 1. Intento directo
    match fs::write(exe_path, bytes) {
        Ok(_) => return Ok(()),
        Err(err) => {
            let _ = tx.send(InstallMsg::Log(format!(
                "[AVISO] Archivo ucaba.exe bloqueado ({}). Liberando procesos y reintentando...",
                err
            )));
            terminate_running_ucaba_processes();
            std::thread::sleep(std::time::Duration::from_millis(200));
        }
    }

    // 2. Reintentos de escritura directa con backoff
    for attempt in 1..=3 {
        if fs::write(exe_path, bytes).is_ok() {
            let _ = tx.send(InstallMsg::Log(format!(
                "[OK] ucaba.exe liberado y actualizado correctamente (intento {})",
                attempt
            )));
            return Ok(());
        }
        std::thread::sleep(std::time::Duration::from_millis(150 * attempt));
    }

    // 3. Reemplazo atómico (Atomic Rename)
    // En Windows NTFS un archivo ejecutable en ejecución no permite GENERIC_WRITE,
    // pero el sistema de archivos sí permite moverlo/renombrarlo en el mismo volumen.
    let timestamp = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .unwrap_or_default()
        .as_millis();
    let old_backup = exe_path.with_file_name(format!("ucaba.old_{}.exe", timestamp));

    let _ = tx.send(InstallMsg::Log(
        "[INFO] Aplicando técnica de reemplazo atómico para ucaba.exe...".to_string(),
    ));

    if let Err(rename_err) = fs::rename(exe_path, &old_backup) {
        // Segundo intento forzando cierre de procesos
        terminate_running_ucaba_processes();
        std::thread::sleep(std::time::Duration::from_millis(250));
        fs::rename(exe_path, &old_backup).map_err(|e| {
            format!(
                "Error escribiendo ucaba.exe: El archivo está bloqueado por otro proceso ({}) y no pudo renombrarse ({}). Cierre editores o terminales con UCABA e intente nuevamente.",
                rename_err, e
            )
        })?;
    }

    // Al renombrarse el archivo anterior, la ruta original queda libre para escribir el nuevo binario
    fs::write(exe_path, bytes).map_err(|e| {
        let _ = fs::rename(&old_backup, exe_path);
        format!("Error escribiendo ucaba.exe tras reemplazo atómico: {}", e)
    })?;

    // Intentar eliminar el archivo de respaldo si el proceso anterior ya cerró su handle
    if let Err(_) = fs::remove_file(&old_backup) {
        #[cfg(windows)]
        unsafe {
            use windows_sys::Win32::Storage::FileSystem::{MoveFileExW, MOVEFILE_DELAY_UNTIL_REBOOT};
            let wide_old: Vec<u16> = old_backup.to_string_lossy().encode_utf16().chain(std::iter::once(0)).collect();
            MoveFileExW(wide_old.as_ptr(), std::ptr::null(), MOVEFILE_DELAY_UNTIL_REBOOT);
        }
    }

    Ok(())
}

fn run_installation_pipeline(tx: Sender<InstallMsg>, cfg: InstallConfig) -> Result<(), String> {
    let target_path = PathBuf::from(&cfg.target_dir);
    let exe_path = target_path.join("ucaba.exe");
    let icon_path = target_path.join("ucaba_icon.ico");

    // Limpieza de residuos y carpetas temporales de PyInstaller (_MEI*) de versiones anteriores de Python
    cleanup_pyinstaller_temp_dirs(Some(&tx));
    if let Ok(local_app) = std::env::var("LOCALAPPDATA") {
        let cache_file = PathBuf::from(local_app).join("UCABA").join("version_cache.json");
        if cache_file.exists() {
            let _ = fs::remove_file(&cache_file);
        }
    }

    // 1. Crear directorio destino
    tx.send(InstallMsg::Progress(0.15, "Preparando directorio de instalación...".to_string())).map_err(|e| e.to_string())?;
    fs::create_dir_all(&target_path)
        .map_err(|e| format!("No se pudo crear '{}': {}", cfg.target_dir, e))?;
    tx.send(InstallMsg::Log(format!("[OK] Directorio listo: {}", cfg.target_dir))).map_err(|e| e.to_string())?;

    // 2. Extraer ucaba.exe
    if cfg.install_cli {
        tx.send(InstallMsg::Progress(0.35, "Extrayendo motor nativo ucaba.exe...".to_string())).map_err(|e| e.to_string())?;
        safe_write_executable(&exe_path, UCABA_EXE_BYTES, &tx)?;
        tx.send(InstallMsg::Log(format!("[OK] ucaba.exe copiado exitosamente ({} bytes)", UCABA_EXE_BYTES.len()))).map_err(|e| e.to_string())?;
    }

    // 3. Extraer icono institucional
    if let Err(e) = fs::write(&icon_path, UCABA_ICON_BYTES) {
        tx.send(InstallMsg::Log(format!("[AVISO] Icono no extraído: {}", e))).map_err(|e| e.to_string())?;
    } else {
        tx.send(InstallMsg::Log("[OK] ucaba_icon.ico extraído correctamente".to_string())).map_err(|e| e.to_string())?;
    }

    // 4. Agregar a variable PATH del usuario
    if cfg.add_path {
        tx.send(InstallMsg::Progress(0.55, "Configurando variable PATH del usuario...".to_string())).map_err(|e| e.to_string())?;
        match add_to_user_path(&cfg.target_dir) {
            Ok(_) => {
                broadcast_env_change();
                tx.send(InstallMsg::Log("[OK] PATH actualizado y notificación de sistema enviada".to_string())).map_err(|e| e.to_string())?;
            }
            Err(e) => {
                tx.send(InstallMsg::Log(format!("[AVISO] PATH: {}", e))).map_err(|e| e.to_string())?;
            }
        }
    }

    // 5. Asociar extensión .ucaba
    if cfg.associate_ext && exe_path.exists() {
        tx.send(InstallMsg::Progress(0.70, "Registrando asociación de archivos .ucaba...".to_string())).map_err(|e| e.to_string())?;
        if let Err(e) = register_file_association(&exe_path, &icon_path) {
            tx.send(InstallMsg::Log(format!("[AVISO] Asociación .ucaba: {}", e))).map_err(|e| e.to_string())?;
        } else {
            tx.send(InstallMsg::Log("[OK] Asociación de archivos .ucaba registrada en Windows con icono oficial".to_string())).map_err(|e| e.to_string())?;
        }
    }

    // 6. Instalar extensión en VS Code
    if cfg.install_vscode {
        tx.send(InstallMsg::Progress(0.88, "Instalando extensión en Visual Studio Code...".to_string())).map_err(|e| e.to_string())?;
        let temp_vsix = std::env::temp_dir().join("ucaba_ext_temp.vsix");
        if fs::write(&temp_vsix, VSCODE_VSIX_BYTES).is_ok() {
            let vs_res = install_vsix_extension(&temp_vsix);
            let _ = fs::remove_file(&temp_vsix);
            match vs_res {
                Ok(_) => {
                    tx.send(InstallMsg::Log("[OK] Extensión de Visual Studio Code instalada con éxito".to_string())).map_err(|e| e.to_string())?;
                }
                Err(w) => {
                    tx.send(InstallMsg::Log(format!("[AVISO] Extensión VS Code: {}", w))).map_err(|e| e.to_string())?;
                }
            }
        }
    }

    // 8. Registro en Agregar/Quitar programas de Windows
    register_uninstaller(&target_path, &icon_path);

    tx.send(InstallMsg::Progress(1.0, "Instalación completada".to_string())).map_err(|e| e.to_string())?;
    tx.send(InstallMsg::DoneInstall).map_err(|e| e.to_string())?;
    Ok(())
}

fn run_uninstallation_pipeline(tx: Sender<InstallMsg>, target_dir: String) {
    let _ = tx.send(InstallMsg::Progress(0.20, "Removiendo archivos del lenguaje...".to_string()));
    let _ = tx.send(InstallMsg::Log("[1/4] Removiendo archivos del lenguaje UCABA...".to_string()));

    terminate_running_ucaba_processes();
    std::thread::sleep(std::time::Duration::from_millis(150));

    let target_path = PathBuf::from(&target_dir);
    if target_path.exists() {
        let root_to_delete = if target_path.ends_with("bin") {
            target_path.parent().unwrap_or(&target_path)
        } else {
            &target_path
        };
        cleanup_old_executables(&target_path.join("ucaba.exe"));
        if let Err(e) = fs::remove_dir_all(root_to_delete) {
            let _ = tx.send(InstallMsg::Log(format!("[AVISO] No se pudo borrar todo el directorio: {}", e)));
        } else {
            let _ = tx.send(InstallMsg::Log(format!("[OK] Directorio eliminado: {}", root_to_delete.display())));
        }
    }

    let _ = tx.send(InstallMsg::Progress(0.45, "Restaurando variable de entorno PATH...".to_string()));
    let _ = tx.send(InstallMsg::Log("[2/4] Quitando UCABA de la variable de entorno PATH...".to_string()));
    let _ = remove_from_user_path(&target_dir);
    let _ = tx.send(InstallMsg::Log("[OK] Variable PATH restaurada exitosamente.".to_string()));

    let _ = tx.send(InstallMsg::Progress(0.70, "Removiendo asociaciones de archivos...".to_string()));
    let _ = tx.send(InstallMsg::Log("[3/4] Removiendo asociaciones de archivos .ucaba en Windows...".to_string()));
    remove_file_association();
    remove_uninstaller();
    let _ = tx.send(InstallMsg::Log("[OK] Asociaciones y registro de desinstalación eliminados.".to_string()));

    let _ = tx.send(InstallMsg::Progress(0.85, "Removiendo extensión de editores...".to_string()));
    let _ = tx.send(InstallMsg::Log("[4/4] Removiendo extensión de VS Code / Cursor / Antigravity...".to_string()));
    let _ = silent_command("code")
        .arg("--uninstall-extension")
        .arg("ucaba.ucaba-language-support")
        .output();

    if let Ok(user_home) = std::env::var("USERPROFILE") {
        let home = PathBuf::from(user_home);
        let targets = [
            home.join(r".vscode\extensions\ucaba.ucaba-language-support-1.11.6"),
            home.join(r".vscode\extensions\ucaba-language-support"),
            home.join(r".antigravity-ide\extensions\ucaba-language-support"),
            home.join(r"Desktop\UCABA.lnk"),
            home.join(r"AppData\Roaming\Microsoft\Windows\Start Menu\Programs\UCABA.lnk"),
        ];
        for t in targets {
            if t.exists() {
                if t.is_dir() {
                    let _ = fs::remove_dir_all(&t);
                } else {
                    let _ = fs::remove_file(&t);
                }
                let _ = tx.send(InstallMsg::Log(format!("[OK] Eliminado residuo: {}", t.display())));
            }
        }
    }

    let _ = tx.send(InstallMsg::Progress(1.0, "Desinstalación completada con éxito".to_string()));
    let _ = tx.send(InstallMsg::Log(">>> ¡DESINSTALACIÓN FINALIZADA CON ÉXITO! <<<".to_string()));
    let _ = tx.send(InstallMsg::DoneUninstall);
}

fn add_to_user_path(target_dir: &str) -> Result<(), String> {
    use std::ptr::null_mut;
    use windows_sys::Win32::System::Registry::{
        RegCloseKey, RegOpenKeyExW, RegQueryValueExW, RegSetValueExW, HKEY, HKEY_CURRENT_USER, KEY_READ, KEY_WRITE, REG_EXPAND_SZ,
    };

    let subkey: Vec<u16> = "Environment\0".encode_utf16().collect();
    let val_name: Vec<u16> = "PATH\0".encode_utf16().collect();

    let mut hkey: HKEY = null_mut();
    let res = unsafe { RegOpenKeyExW(HKEY_CURRENT_USER, subkey.as_ptr(), 0, KEY_READ | KEY_WRITE, &mut hkey) };
    if res != 0 {
        return Err(format!("Error abriendo clave de registro Environment: código {}", res));
    }

    let mut buf = vec![0u16; 8192];
    let mut buf_size = (buf.len() * 2) as u32;
    let mut val_type = 0;

    let q_res = unsafe {
        RegQueryValueExW(
            hkey,
            val_name.as_ptr(),
            null_mut(),
            &mut val_type,
            buf.as_mut_ptr() as *mut u8,
            &mut buf_size,
        )
    };

    let current_path = if q_res == 0 {
        let len = (buf_size as usize / 2).saturating_sub(1);
        String::from_utf16_lossy(&buf[..len])
    } else {
        String::new()
    };

    if !current_path.split(';').any(|p| p.trim().eq_ignore_ascii_case(target_dir)) {
        let new_path = if current_path.is_empty() {
            target_dir.to_string()
        } else {
            format!("{};{}", current_path, target_dir)
        };

        let wide_new: Vec<u16> = new_path.encode_utf16().chain(std::iter::once(0)).collect();
        let target_type = if val_type == 0 { REG_EXPAND_SZ } else { val_type };

        unsafe {
            RegSetValueExW(
                hkey,
                val_name.as_ptr(),
                0,
                target_type,
                wide_new.as_ptr() as *const u8,
                (wide_new.len() * 2) as u32,
            );
        }
    }

    unsafe { RegCloseKey(hkey) };
    Ok(())
}

fn remove_from_user_path(target_dir: &str) -> Result<(), String> {
    use std::ptr::null_mut;
    use windows_sys::Win32::System::Registry::{
        RegCloseKey, RegOpenKeyExW, RegQueryValueExW, RegSetValueExW, HKEY, HKEY_CURRENT_USER, KEY_READ, KEY_WRITE, REG_EXPAND_SZ,
    };

    let subkey: Vec<u16> = "Environment\0".encode_utf16().collect();
    let val_name: Vec<u16> = "PATH\0".encode_utf16().collect();

    let mut hkey: HKEY = null_mut();
    let res = unsafe { RegOpenKeyExW(HKEY_CURRENT_USER, subkey.as_ptr(), 0, KEY_READ | KEY_WRITE, &mut hkey) };
    if res != 0 {
        return Err(format!("Error abriendo clave Environment: código {}", res));
    }

    let mut buf = vec![0u16; 8192];
    let mut buf_size = (buf.len() * 2) as u32;
    let mut val_type = 0;

    let q_res = unsafe {
        RegQueryValueExW(
            hkey,
            val_name.as_ptr(),
            null_mut(),
            &mut val_type,
            buf.as_mut_ptr() as *mut u8,
            &mut buf_size,
        )
    };

    if q_res == 0 {
        let len = (buf_size as usize / 2).saturating_sub(1);
        let current_path = String::from_utf16_lossy(&buf[..len]);
        let filtered: Vec<&str> = current_path
            .split(';')
            .filter(|p| !p.trim().is_empty() && !p.trim().eq_ignore_ascii_case(target_dir))
            .collect();

        let new_path = filtered.join(";");
        let wide_new: Vec<u16> = new_path.encode_utf16().chain(std::iter::once(0)).collect();
        let target_type = if val_type == 0 { REG_EXPAND_SZ } else { val_type };

        unsafe {
            RegSetValueExW(
                hkey,
                val_name.as_ptr(),
                0,
                target_type,
                wide_new.as_ptr() as *const u8,
                (wide_new.len() * 2) as u32,
            );
        }
    }

    unsafe { RegCloseKey(hkey) };
    broadcast_env_change();
    Ok(())
}

fn broadcast_env_change() {
    use windows_sys::Win32::UI::WindowsAndMessaging::{
        SendMessageTimeoutW, HWND_BROADCAST, SMTO_ABORTIFHUNG, WM_SETTINGCHANGE,
    };

    let env_str: Vec<u16> = "Environment\0".encode_utf16().collect();
    let mut res = 0;
    unsafe {
        SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            env_str.as_ptr() as isize,
            SMTO_ABORTIFHUNG,
            2000,
            &mut res,
        );
    }
}

fn refresh_shell_icons() {
    use windows_sys::Win32::UI::Shell::{SHChangeNotify, SHCNE_ASSOCCHANGED, SHCNF_IDLIST};
    unsafe {
        SHChangeNotify(SHCNE_ASSOCCHANGED as i32, SHCNF_IDLIST, std::ptr::null(), std::ptr::null());
    }
}

fn register_file_association(exe_path: &Path, icon_path: &Path) -> Result<(), String> {
    let ps_script = format!(
        r#"
        $extPath = "HKCU:\Software\Classes\.ucaba"
        New-Item -Path $extPath -Force | Out-Null
        Set-ItemProperty -Path $extPath -Name "(Default)" -Value "UCABAFile"
        Set-ItemProperty -Path $extPath -Name "Content Type" -Value "text/x-ucaba"
        Set-ItemProperty -Path $extPath -Name "PerceivedType" -Value "text"

        $iconPath = "{}"
        $exePath = "{}"

        if (Test-Path $iconPath) {{
            $extIconReg = "$extPath\DefaultIcon"
            New-Item -Path $extIconReg -Force | Out-Null
            Set-ItemProperty -Path $extIconReg -Name "(Default)" -Value "`"$iconPath`""
        }}

        foreach ($prog in @("UCABAFile", "UCABA.Program")) {{
            $progPath = "HKCU:\Software\Classes\$prog"
            New-Item -Path $progPath -Force | Out-Null
            Set-ItemProperty -Path $progPath -Name "(Default)" -Value "Código Fuente UCABA"
            if (Test-Path $iconPath) {{
                $iconReg = "$progPath\DefaultIcon"
                New-Item -Path $iconReg -Force | Out-Null
                Set-ItemProperty -Path $iconReg -Name "(Default)" -Value "`"$iconPath`""
            }} elseif (Test-Path $exePath) {{
                $iconReg = "$progPath\DefaultIcon"
                New-Item -Path $iconReg -Force | Out-Null
                Set-ItemProperty -Path $iconReg -Name "(Default)" -Value "`"$exePath`",0"
            }}
            $cmdReg = "$progPath\shell\open\command"
            New-Item -Path $cmdReg -Force | Out-Null
            Set-ItemProperty -Path $cmdReg -Name "(Default)" -Value "cmd.exe /k `"`"$exePath`" run `"`"%1`"`""
        }}

        $feProgids = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Explorer\FileExts\.ucaba\OpenWithProgids"
        New-Item -Path $feProgids -Force | Out-Null
        Set-ItemProperty -Path $feProgids -Name "UCABAFile" -Value ([byte[]]@()) -Type None
        Set-ItemProperty -Path $feProgids -Name "UCABA.Program" -Value ([byte[]]@()) -Type None
        "#,
        icon_path.to_string_lossy(),
        exe_path.to_string_lossy()
    );

    let _ = run_powershell_script(&ps_script);

    refresh_shell_icons();
    Ok(())
}

fn remove_file_association() {
    let ps_script = r#"
        Remove-Item -Path "HKCU:\Software\Classes\.ucaba" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -Path "HKCU:\Software\Classes\UCABAFile" -Recurse -Force -ErrorAction SilentlyContinue
        Remove-Item -Path "HKCU:\Software\Classes\UCABA.Program" -Recurse -Force -ErrorAction SilentlyContinue
    "#;
    let _ = run_powershell_script(ps_script);

    refresh_shell_icons();
}

fn install_vsix_extension(vsix_path: &Path) -> Result<(), String> {
    // 1. Intentar registrar vía CLIs de editores conocidos
    let editors = ["code", "cursor", "codium", "antigravity", "antigravity-ide"];
    for editor in editors {
        let _ = silent_command(editor)
            .arg("--install-extension")
            .arg(vsix_path)
            .arg("--force")
            .output();
    }

    if let Ok(local) = std::env::var("LOCALAPPDATA") {
        let local_path = PathBuf::from(&local);
        let editor_cmds = [
            local_path.join(r"Programs\Microsoft VS Code\bin\code.cmd"),
            local_path.join(r"Programs\Antigravity IDE\bin\antigravity-ide.cmd"),
            local_path.join(r"Programs\cursor\resources\app\bin\cursor.cmd"),
            local_path.join(r"Programs\VSCodium\bin\codium.cmd"),
        ];
        for cmd in editor_cmds {
            if cmd.exists() {
                let _ = silent_command(&cmd)
                    .arg("--install-extension")
                    .arg(vsix_path)
                    .arg("--force")
                    .output();
            }
        }
    }

    // 2. Despliegue directo y registro en extensions.json / limpieza de .obsolete
    let ps_deploy = format!(
        r#"
        $vsix = "{}"
        $userHome = [Environment]::GetFolderPath('UserProfile')
        $extRoots = @(
            "$userHome\.vscode\extensions",
            "$userHome\.vscode-oss\extensions",
            "$userHome\.cursor\extensions",
            "$userHome\.antigravity-ide\extensions",
            "$userHome\.antigravity\extensions"
        )
        $currentFolder = "ucaba.ucaba-language-support-{}"
        $tempExtract = Join-Path ([System.IO.Path]::GetTempPath()) "ucaba_vsix_unpacked"
        if (Test-Path $tempExtract) {{ Remove-Item -Path $tempExtract -Recurse -Force -ErrorAction SilentlyContinue }}
        try {{
            Expand-Archive -Path $vsix -DestinationPath $tempExtract -Force
            $srcExt = Join-Path $tempExtract "extension"
            if (Test-Path $srcExt) {{
                foreach ($root in $extRoots) {{
                    if ((Test-Path $root) -or (Test-Path (Split-Path $root -Parent))) {{
                        New-Item -Path $root -ItemType Directory -Force | Out-Null
                        Get-ChildItem -Path $root -Filter "ucaba.ucaba-language-support-*" -ErrorAction SilentlyContinue | Where-Object {{ $_.Name -ne $currentFolder }} | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
                        Remove-Item -Path (Join-Path $root "ucaba-language-support") -Recurse -Force -ErrorAction SilentlyContinue
                        $obs = Join-Path $root ".obsolete"
                        if (Test-Path $obs) {{
                            try {{
                                $obsJson = Get-Content $obs -Raw | ConvertFrom-Json
                                $newObs = @{{}}
                                foreach ($prop in $obsJson.PSObject.Properties) {{
                                    if ($prop.Name -notlike "*ucaba*") {{
                                        $newObs[$prop.Name] = $prop.Value
                                    }}
                                }}
                                $newObs | ConvertTo-Json | Set-Content $obs
                            }} catch {{}}
                        }}
                        $dest = Join-Path $root $currentFolder
                        if (Test-Path $dest) {{ Remove-Item -Path $dest -Recurse -Force -ErrorAction SilentlyContinue }}
                        Copy-Item -Path $srcExt -Destination $dest -Recurse -Force
                        $extJson = Join-Path $root "extensions.json"
                        if (Test-Path $extJson) {{
                            try {{
                                $list = Get-Content $extJson -Raw | ConvertFrom-Json
                                $filtered = @()
                                foreach ($it in $list) {{
                                    if ($it.identifier.id -ne "ucaba.ucaba-language-support") {{
                                        $filtered += $it
                                    }}
                                }}
                                $posixPath = "/" + ($dest.Replace("\", "/").TrimStart("/"))
                                $newEntry = [PSCustomObject]@{{
                                    identifier = [PSCustomObject]@{{ id = "ucaba.ucaba-language-support" }};
                                    version = "{}";
                                    location = [PSCustomObject]@{{
                                        "`$mid" = 1;
                                        fsPath = $dest;
                                        _sep = 1;
                                        external = "file://$posixPath";
                                        path = $posixPath;
                                        scheme = "file"
                                    }};
                                    relativeLocation = $currentFolder;
                                    metadata = [PSCustomObject]@{{
                                        isApplicationScoped = $false;
                                        isMachineScoped = $false;
                                        isBuiltin = $false;
                                        pinned = $true;
                                        source = "vsix"
                                    }}
                                }}
                                $filtered += $newEntry
                                $filtered | ConvertTo-Json -Depth 10 | Set-Content $extJson
                            }} catch {{}}
                        }}
                    }}
                }}

                # Parchear temas de iconos instalados (Bearded Icons, Material, Seti)
                $svgSrc = Join-Path $srcExt "icons\ucaba-file.svg"
                if (Test-Path $svgSrc) {{
                    foreach ($root in $extRoots) {{
                        if (Test-Path $root) {{
                            Get-ChildItem -Path $root -Directory -ErrorAction SilentlyContinue | ForEach-Object {{
                                $f = $_.FullName
                                if ($_.Name -like "*beardedicons*") {{
                                    $tj = Join-Path $f "icons.json"
                                    if (Test-Path $tj) {{
                                        try {{
                                            $dSvg = Join-Path $f "icons\ucaba-file.svg"
                                            New-Item -Path (Split-Path $dSvg -Parent) -ItemType Directory -Force | Out-Null
                                            Copy-Item -Path $svgSrc -Destination $dSvg -Force
                                            $data = Get-Content $tj -Raw | ConvertFrom-Json
                                            $data | Add-Member -MemberType NoteProperty -Name "showLanguageModeIcons" -Value $true -Force
                                            if (-not $data.iconDefinitions._file_ucaba) {{
                                                $data.iconDefinitions | Add-Member -MemberType NoteProperty -Name "_file_ucaba" -Value ([PSCustomObject]@{{ iconPath = "./icons/ucaba-file.svg" }}) -Force
                                            }}
                                            $data.fileExtensions | Add-Member -MemberType NoteProperty -Name "ucaba" -Value "_file_ucaba" -Force
                                            $data.languageIds | Add-Member -MemberType NoteProperty -Name "ucaba" -Value "_file_ucaba" -Force
                                            $data | ConvertTo-Json -Depth 10 | Set-Content $tj
                                        }} catch {{}}
                                    }}
                                }}
                            }}
                        }}
                    }}
                    $localApp = [Environment]::GetEnvironmentVariable("LOCALAPPDATA")
                    if ($localApp) {{
                        @("Microsoft VS Code", "Antigravity IDE") | ForEach-Object {{
                            $setiTheme = Join-Path $localApp "Programs\$_\resources\app\extensions\theme-seti\icons\vs-seti-icon-theme.json"
                            if (Test-Path $setiTheme) {{
                                try {{
                                    $destSetiSvg = Join-Path (Split-Path $setiTheme -Parent) "ucaba-file.svg"
                                    Copy-Item -Path $svgSrc -Destination $destSetiSvg -Force
                                    $sj = Get-Content $setiTheme -Raw | ConvertFrom-Json
                                    $sj | Add-Member -MemberType NoteProperty -Name "showLanguageModeIcons" -Value $true -Force
                                    if (-not $sj.iconDefinitions._ucaba) {{
                                        $sj.iconDefinitions | Add-Member -MemberType NoteProperty -Name "_ucaba" -Value ([PSCustomObject]@{{ iconPath = "./ucaba-file.svg" }}) -Force
                                    }}
                                    $sj.fileExtensions | Add-Member -MemberType NoteProperty -Name "ucaba" -Value "_ucaba" -Force
                                    $sj.languageIds | Add-Member -MemberType NoteProperty -Name "ucaba" -Value "_ucaba" -Force
                                    $sj | ConvertTo-Json -Depth 10 | Set-Content $setiTheme
                                }} catch {{}}
                            }}
                        }}
                    }}
                }}
            }}
        }} catch {{}}
        finally {{
            if (Test-Path $tempExtract) {{ Remove-Item -Path $tempExtract -Recurse -Force -ErrorAction SilentlyContinue }}
        }}
        "#,
        vsix_path.to_string_lossy(),
        UCABA_VERSION,
        UCABA_VERSION
    );

    let _ = run_powershell_script(&ps_deploy);

    Ok(())
}

fn register_uninstaller(target_dir: &Path, icon_path: &Path) {
    let ps_script = format!(
        r#"
        $unPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\UCABA"
        New-Item -Path $unPath -Force | Out-Null
        Set-ItemProperty -Path $unPath -Name "DisplayName" -Value "UCABA Lenguaje de Programación (v{})"
        Set-ItemProperty -Path $unPath -Name "DisplayVersion" -Value "{}"
        Set-ItemProperty -Path $unPath -Name "Publisher" -Value "Facu Falcone"
        Set-ItemProperty -Path $unPath -Name "DisplayIcon" -Value "{}"
        Set-ItemProperty -Path $unPath -Name "InstallLocation" -Value "{}"
        Set-ItemProperty -Path $unPath -Name "UninstallString" -Value 'powershell -NoProfile -WindowStyle Hidden -Command "Remove-Item -Recurse -Force \"{}\""'
        "#,
        UCABA_VERSION,
        UCABA_VERSION,
        icon_path.to_string_lossy(),
        target_dir.to_string_lossy(),
        target_dir.to_string_lossy()
    );

    let _ = run_powershell_script(&ps_script);
}

fn remove_uninstaller() {
    let ps_script = r#"
        Remove-Item -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\UCABA" -Recurse -Force -ErrorAction SilentlyContinue
    "#;
    let _ = run_powershell_script(ps_script);
}

fn main() -> eframe::Result<()> {
    #[cfg(windows)]
    ensure_clean_environment_and_break_away();

    // Si se pasa flag silencioso
    let args: Vec<String> = std::env::args().collect();
    if args.iter().any(|a| a == "--silent" || a == "-s") {
        let (tx, rx) = channel();
        let target_dir = std::env::var("LOCALAPPDATA")
            .map(|p| format!(r"{}\Programs\UCABA\bin", p))
            .unwrap_or_else(|_| r"C:\UCABA\bin".to_string());

        let cfg = InstallConfig {
            target_dir,
            install_cli: true,
            add_path: true,
            install_vscode: true,
            associate_ext: true,
        };

        let res = run_installation_pipeline(tx, cfg);
        while let Ok(msg) = rx.try_recv() {
            match msg {
                InstallMsg::Log(l) => println!("{}", l),
                InstallMsg::Error(e) => eprintln!("Error: {}", e),
                _ => {}
            }
        }
        if res.is_ok() {
            println!("Instalación silenciosa completada.");
            std::process::exit(0);
        } else {
            std::process::exit(1);
        }
    }

    #[cfg(windows)]
    unsafe {
        let app_id: Vec<u16> = "UCABA.Language.Installer\0".encode_utf16().collect();
        let _ = windows_sys::Win32::UI::Shell::SetCurrentProcessExplicitAppUserModelID(app_id.as_ptr());
    }

    let icon_data = image::load_from_memory(UCABA_ICON_PNG_BYTES).ok().map(|img| {
        let rgba = img.to_rgba8();
        let (width, height) = (rgba.width(), rgba.height());
        egui::IconData {
            rgba: rgba.into_raw(),
            width,
            height,
        }
    });

    let mut viewport = egui::ViewportBuilder::default()
        .with_inner_size([880.0, 640.0])
        .with_min_inner_size([840.0, 600.0])
        .with_resizable(true)
        .with_title("Instalador UCABA v2.1 & Extensión para Visual Studio Code");

    if let Some(icon) = icon_data {
        viewport = viewport.with_icon(icon);
    }

    let options = eframe::NativeOptions {
        viewport,
        ..Default::default()
    };

    eframe::run_native(
        "Instalador UCABA v2.1 & Extensión para Visual Studio Code",
        options,
        Box::new(|_cc| Ok(Box::new(InstallerApp::default()))),
    )
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::mpsc::channel;

    #[test]
    fn test_safe_write_executable_clean_write() {
        let temp_dir = std::env::temp_dir().join(format!("ucaba_test_install_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis()));
        fs::create_dir_all(&temp_dir).unwrap();
        let target = temp_dir.join("ucaba.exe");
        let (tx, _rx) = channel();

        let data = b"TEST_UCABA_BINARY_DATA";
        assert!(safe_write_executable(&target, data, &tx).is_ok());
        assert_eq!(fs::read(&target).unwrap(), data);

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_safe_write_executable_overwrites_existing() {
        let temp_dir = std::env::temp_dir().join(format!("ucaba_test_install_ow_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis()));
        fs::create_dir_all(&temp_dir).unwrap();
        let target = temp_dir.join("ucaba.exe");
        fs::write(&target, b"OLD_DATA").unwrap();
        let (tx, _rx) = channel();

        let new_data = b"NEW_DATA_V2";
        assert!(safe_write_executable(&target, new_data, &tx).is_ok());
        assert_eq!(fs::read(&target).unwrap(), new_data);

        let _ = fs::remove_dir_all(&temp_dir);
    }

    #[test]
    fn test_cleanup_old_executables() {
        let temp_dir = std::env::temp_dir().join(format!("ucaba_test_cleanup_{}", std::time::SystemTime::now().duration_since(std::time::UNIX_EPOCH).unwrap().as_millis()));
        fs::create_dir_all(&temp_dir).unwrap();
        let old1 = temp_dir.join("ucaba.old_12345.exe");
        let old2 = temp_dir.join("ucaba_old_67890.exe");
        let keep = temp_dir.join("ucaba.exe");
        fs::write(&old1, b"old").unwrap();
        fs::write(&old2, b"old").unwrap();
        fs::write(&keep, b"keep").unwrap();

        cleanup_old_executables(&keep);

        assert!(!old1.exists());
        assert!(!old2.exists());
        assert!(keep.exists());

        let _ = fs::remove_dir_all(&temp_dir);
    }
}

