# GNU General Public License v3.0 or later (GPL-3.0-or-later)
#
# Copyright (c) 2026 [Facu Falcone](a.facundo.falcone@gmail.com) All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Instalador Gráfico Todo-en-Uno para el Lenguaje UCABA y la Extensión de VS Code.
Permite instalar el binario 'ucaba.exe' en el sistema, añadirlo al PATH,
asociar la extensión .ucaba e instalar el plugin en Visual Studio Code.
"""

import os
import sys
import shutil
import subprocess
import threading
import time
import winreg
import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText


def setup_console():
    """Si fue invocado desde una terminal, se acopla a la consola existente para mostrar salida."""
    try:
        if ctypes.windll.kernel32.AttachConsole(0xFFFFFFFF):
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    except Exception:
        pass


def enable_high_dpi():
    """Habilita escalado nítido para monitores de alta densidad (High-DPI) en Windows."""
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


def safe_print(msg: str):
    """Imprime en consola si está disponible de forma segura."""
    try:
        if sys.stdout:
            print(msg)
            sys.stdout.flush()
    except Exception:
        pass


def broadcast_environment_change():
    """Notifica a Windows y a las aplicaciones abiertas que el PATH del sistema cambió."""
    try:
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        result = wintypes.DWORD()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST,
            WM_SETTINGCHANGE,
            0,
            "Environment",
            SMTO_ABORTIFHUNG,
            3000,
            ctypes.byref(result)
        )
    except Exception:
        pass


def get_resource_path(relative_path: str) -> str:
    """Resuelve la ruta de un recurso tanto en modo desarrollo como empaquetado en PyInstaller."""
    # 1. Si está empaquetado en PyInstaller (_MEIPASS)
    if hasattr(sys, "_MEIPASS"):
        candidates_meipass = [
            os.path.join(sys._MEIPASS, relative_path),
            os.path.join(sys._MEIPASS, "payload", relative_path),
            os.path.join(sys._MEIPASS, "payload", os.path.basename(relative_path))
        ]
        for c in candidates_meipass:
            if os.path.exists(c):
                return c

    # 2. Si se ejecuta directamente desde el código fuente
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, relative_path),
        os.path.join(base_dir, "payload", relative_path),
        os.path.join(base_dir, "payload", os.path.basename(relative_path)),
        os.path.join(base_dir, "dist", relative_path),
        os.path.join(base_dir, "extension-vscode", relative_path)
    ]
    for c in candidates:
        if os.path.exists(c):
            return c

    return os.path.join(base_dir, relative_path)


def add_to_user_path(directory: str) -> bool:
    """Añade un directorio a la variable de entorno PATH del usuario en el Registro de Windows."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
            try:
                current_path, reg_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                current_path, reg_type = "", winreg.REG_EXPAND_SZ

            parts = [p.strip() for p in current_path.split(";") if p.strip()]
            norm_target = os.path.normpath(directory).lower()

            if not any(os.path.normpath(p).lower() == norm_target for p in parts):
                parts.append(directory)
                new_path = ";".join(parts)
                winreg.SetValueEx(key, "Path", 0, reg_type, new_path)
                broadcast_environment_change()
                return True
            return False
    except Exception as e:
        print(f"Error modificando PATH: {e}")
        return False


def remove_from_user_path(directory: str) -> bool:
    """Elimina un directorio de la variable PATH del usuario."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_READ | winreg.KEY_SET_VALUE) as key:
            try:
                current_path, reg_type = winreg.QueryValueEx(key, "Path")
            except FileNotFoundError:
                return False

            parts = [p.strip() for p in current_path.split(";") if p.strip()]
            norm_target = os.path.normpath(directory).lower()
            filtered = [p for p in parts if os.path.normpath(p).lower() != norm_target]

            if len(filtered) != len(parts):
                new_path = ";".join(filtered)
                winreg.SetValueEx(key, "Path", 0, reg_type, new_path)
                broadcast_environment_change()
                return True
            return False
    except Exception as e:
        print(f"Error quitando de PATH: {e}")
        return False


def associate_file_extension(ucaba_exe: str, icon_path: str = None):
    """Asocia la extensión .ucaba con ucaba.exe en el Registro de Windows del usuario."""
    try:
        base = winreg.HKEY_CURRENT_USER
        with winreg.CreateKey(base, r"Software\Classes\.ucaba") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "UCABA.Program")

        with winreg.CreateKey(base, r"Software\Classes\UCABA.Program") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, "Código Fuente UCABA")

        icon_val = f'"{icon_path}",0' if icon_path and os.path.exists(icon_path) else f'"{ucaba_exe}",0'
        with winreg.CreateKey(base, r"Software\Classes\UCABA.Program\DefaultIcon") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, icon_val)

        with winreg.CreateKey(base, r"Software\Classes\UCABA.Program\shell\open\command") as key:
            winreg.SetValueEx(key, "", 0, winreg.REG_SZ, f'cmd.exe /k ""{ucaba_exe}" run "%1""')
        return True
    except Exception as e:
        print(f"Error asociando archivos: {e}")
        return False


def remove_file_association():
    """Elimina las asociaciones de archivos .ucaba."""
    keys_to_delete = [
        r"Software\Classes\UCABA.Program\shell\open\command",
        r"Software\Classes\UCABA.Program\shell\open",
        r"Software\Classes\UCABA.Program\shell",
        r"Software\Classes\UCABA.Program\DefaultIcon",
        r"Software\Classes\UCABA.Program",
        r"Software\Classes\.ucaba"
    ]
    for sub in keys_to_delete:
        try:
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, sub)
        except OSError:
            pass


def find_code_cli():
    """Localiza el comando de CLI de Visual Studio Code ('code' o 'code.cmd')."""
    which_code = shutil.which("code.cmd") or shutil.which("code")
    if which_code:
        return which_code

    candidates = [
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd"),
        os.path.expandvars(r"%PROGRAMFILES%\Microsoft VS Code\bin\code.cmd"),
        os.path.expandvars(r"%PROGRAMFILES(X86)%\Microsoft VS Code\bin\code.cmd"),
    ]
    for c in candidates:
        if os.path.exists(c):
            return c
    return None


class InstallerApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Instalador UCABA & Extensión VS Code")

        # Dimensiones optimizadas para visualización completa y High-DPI en Windows
        window_width = 880
        window_height = 640
        self.root.minsize(840, 600)
        self.root.configure(bg="#150817")

        # Centrar la ventana dinámicamente en la pantalla del usuario
        try:
            self.root.update_idletasks()
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            pos_x = max(0, (screen_w - window_width) // 2)
            pos_y = max(0, (screen_h - window_height) // 2)
            self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        except Exception:
            self.root.geometry(f"{window_width}x{window_height}")

        # Cargar icono de la aplicación
        ico_file = get_resource_path("ucaba_icon.ico")
        if os.path.exists(ico_file):
            try:
                self.root.iconbitmap(ico_file)
            except Exception:
                pass

        # Variables de estado
        self.opt_install_cli = tk.BooleanVar(value=True)
        self.opt_add_path = tk.BooleanVar(value=True)
        self.opt_install_vscode = tk.BooleanVar(value=True)
        self.opt_associate_ext = tk.BooleanVar(value=True)

        self._build_ui()

    def _build_ui(self):
        # 1. Cabecera visual con logo institucional e información (TOP)
        header_frame = tk.Frame(self.root, bg="#240a26", padx=20, pady=16)
        header_frame.pack(side=tk.TOP, fill=tk.X)

        self.logo_img = None
        logo_path = get_resource_path("ucaba_logo_header.png")
        if not os.path.exists(logo_path):
            logo_path = get_resource_path("ucaba_icon.png")

        if os.path.exists(logo_path):
            try:
                self.logo_img = tk.PhotoImage(file=logo_path)
                logo_lbl = tk.Label(header_frame, image=self.logo_img, bg="#240a26")
                logo_lbl.pack(side=tk.LEFT, padx=(0, 16))
            except Exception:
                pass

        # Badge de autor estilizado en la esquina superior derecha
        author_badge = tk.Frame(
            header_frame,
            bg="#380d3f",
            padx=14,
            pady=6,
            highlightbackground="#a81a7d",
            highlightthickness=1
        )
        author_badge.pack(side=tk.RIGHT, padx=(10, 0), anchor="center")

        author_lbl = tk.Label(
            author_badge,
            text="Autor: <Facu Falcone>",
            font=("Segoe UI", 9, "bold"),
            fg="#fce7f3",
            bg="#380d3f"
        )
        author_lbl.pack()

        text_frame = tk.Frame(header_frame, bg="#240a26")
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        title_lbl = tk.Label(
            text_frame,
            text="UCABA",
            font=("Segoe UI", 20, "bold"),
            fg="#ffffff",
            bg="#240a26",
            anchor="w",
            justify=tk.LEFT
        )
        title_lbl.pack(anchor="w", fill=tk.X)

        subtitle_lbl = tk.Label(
            text_frame,
            text="Instalador del Lenguaje & Extensión para Visual Studio Code",
            font=("Segoe UI", 10),
            fg="#f472b6",
            bg="#240a26",
            anchor="w",
            justify=tk.LEFT
        )
        subtitle_lbl.pack(anchor="w", fill=tk.X, pady=(2, 0))

        # 2. Pie de página con botones (BOTTOM)
        # REGLA CRÍTICA: Se empaqueta en BOTTOM ANTES del cuerpo para garantizar que nunca sea ocultado o recortado
        footer_frame = tk.Frame(self.root, bg="#240a26", padx=20, pady=12)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_lbl = tk.Label(
            footer_frame,
            text="Listo para instalar.",
            font=("Segoe UI", 9),
            fg="#f472b6",
            bg="#240a26"
        )
        self.status_lbl.pack(side=tk.LEFT)

        self.btn_exit = tk.Button(
            footer_frame,
            text="Cerrar",
            command=self.root.quit,
            font=("Segoe UI", 9),
            bg="#3b153e",
            fg="#fce7f3",
            activebackground="#4d1d52",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=14,
            pady=5,
            cursor="hand2"
        )
        self.btn_exit.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_uninstall = tk.Button(
            footer_frame,
            text="Desinstalar",
            command=self.start_uninstall,
            font=("Segoe UI", 9),
            bg="#881337",
            fg="#ffffff",
            activebackground="#9f1239",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=14,
            pady=5,
            cursor="hand2"
        )
        self.btn_uninstall.pack(side=tk.RIGHT, padx=(8, 0))

        self.btn_install = tk.Button(
            footer_frame,
            text="Instalar Ahora",
            command=self.start_install,
            font=("Segoe UI", 10, "bold"),
            bg="#a81a7d",
            fg="#ffffff",
            activebackground="#c02694",
            activeforeground="#ffffff",
            relief=tk.FLAT,
            padx=20,
            pady=5,
            cursor="hand2"
        )
        self.btn_install.pack(side=tk.RIGHT)

        # Efectos hover interactivos en botones
        self.btn_install.bind("<Enter>", lambda e: self.btn_install.config(bg="#c02694") if str(self.btn_install["state"]) != str(tk.DISABLED) else None)
        self.btn_install.bind("<Leave>", lambda e: self.btn_install.config(bg="#a81a7d") if str(self.btn_install["state"]) != str(tk.DISABLED) else None)

        self.btn_uninstall.bind("<Enter>", lambda e: self.btn_uninstall.config(bg="#9f1239") if str(self.btn_uninstall["state"]) != str(tk.DISABLED) else None)
        self.btn_uninstall.bind("<Leave>", lambda e: self.btn_uninstall.config(bg="#881337") if str(self.btn_uninstall["state"]) != str(tk.DISABLED) else None)

        self.btn_exit.bind("<Enter>", lambda e: self.btn_exit.config(bg="#4d1d52"))
        self.btn_exit.bind("<Leave>", lambda e: self.btn_exit.config(bg="#3b153e"))

        # 3. Contenido principal (CENTER)
        # Se expande en todo el espacio disponible restante entre la cabecera y el pie de página
        body_frame = tk.Frame(self.root, bg="#150817", padx=20, pady=12)
        body_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Opciones de instalación
        opts_label = tk.Label(
            body_frame,
            text="Componentes y Tareas de Instalación:",
            font=("Segoe UI", 11, "bold"),
            fg="#fae8ff",
            bg="#150817"
        )
        opts_label.pack(anchor="w", pady=(0, 8))

        chk_style = {
            "bg": "#150817",
            "fg": "#fce7f3",
            "activebackground": "#150817",
            "activeforeground": "#f472b6",
            "selectcolor": "#2e0c32",
            "font": ("Segoe UI", 9)
        }

        self.chk1 = tk.Checkbutton(
            body_frame,
            text="Instalar ejecutable nativo 'ucaba.exe' en %LOCALAPPDATA%\\Programs\\UCABA\\bin",
            variable=self.opt_install_cli,
            **chk_style
        )
        self.chk1.pack(anchor="w", pady=2)

        self.chk2 = tk.Checkbutton(
            body_frame,
            text="Agregar UCABA a la variable de entorno PATH (usar 'ucaba' desde cualquier terminal)",
            variable=self.opt_add_path,
            **chk_style
        )
        self.chk2.pack(anchor="w", pady=2)

        self.chk3 = tk.Checkbutton(
            body_frame,
            text="Instalar extensión de UCABA en Visual Studio Code (v1.2.0 - coloreado, linter y ejecución)",
            variable=self.opt_install_vscode,
            **chk_style
        )
        self.chk3.pack(anchor="w", pady=2)

        self.chk4 = tk.Checkbutton(
            body_frame,
            text="Asociar archivos .ucaba en Windows (icono oficial de UCABA y comando 'Abrir/Ejecutar')",
            variable=self.opt_associate_ext,
            **chk_style
        )
        self.chk4.pack(anchor="w", pady=2)

        # Barra de progreso
        style = ttk.Style()
        style.theme_use('default')
        style.configure("UCABA.Horizontal.TProgressbar", troughcolor="#240a26", background="#a81a7d")

        self.progress = ttk.Progressbar(body_frame, orient="horizontal", mode="determinate", style="UCABA.Horizontal.TProgressbar")
        self.progress.pack(fill=tk.X, pady=(14, 8))

        # Consola de registro / Logs
        log_label = tk.Label(
            body_frame,
            text="Registro de eventos:",
            font=("Segoe UI", 9, "bold"),
            fg="#f472b6",
            bg="#150817"
        )
        log_label.pack(anchor="w", pady=(0, 4))

        self.log_text = ScrolledText(
            body_frame,
            height=8,
            bg="#0d040e",
            fg="#f5d0fe",
            insertbackground="#f472b6",
            font=("Consolas", 9),
            relief=tk.FLAT,
            padx=8,
            pady=8
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)

        self.log("Asistente de instalación de UCABA iniciado | Autor: <Facu Falcone>")
        self.log("Seleccione las opciones deseadas y presione 'Instalar Ahora'.")

    def log(self, message: str):
        """Escribe un mensaje en el área de logs de forma segura para hilos."""
        def _append():
            self.log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
            self.log_text.see(tk.END)
        self.root.after(0, _append)

    def set_status(self, text: str, fg: str = "#38bdf8"):
        def _update():
            self.status_lbl.config(text=text, fg=fg)
        self.root.after(0, _update)

    def set_progress(self, value: int):
        def _update():
            self.progress["value"] = value
        self.root.after(0, _update)

    def set_controls_enabled(self, enabled: bool):
        state = tk.NORMAL if enabled else tk.DISABLED
        def _update():
            self.btn_install.config(state=state)
            self.btn_uninstall.config(state=state)
            self.chk1.config(state=state)
            self.chk2.config(state=state)
            self.chk3.config(state=state)
            self.chk4.config(state=state)
        self.root.after(0, _update)

    def start_install(self):
        self.set_controls_enabled(False)
        self.set_progress(0)
        self.set_status("Iniciando instalación...")
        threading.Thread(target=self._run_installation, daemon=True).start()

    def start_uninstall(self):
        confirm = messagebox.askyesno(
            "Confirmar desinstalación",
            "¿Desea desinstalar UCABA, remover el comando del PATH y retirar la extensión de VS Code?"
        )
        if not confirm:
            return
        self.set_controls_enabled(False)
        self.set_progress(0)
        self.set_status("Desinstalando...")
        threading.Thread(target=self._run_uninstallation, daemon=True).start()

    def _run_installation(self):
        try:
            self.set_progress(10)
            install_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\UCABA\bin")
            ucaba_target_exe = os.path.join(install_dir, "ucaba.exe")

            # 1. Instalar CLI
            if self.opt_install_cli.get():
                self.log(f"[1/4] Instalando ejecutable nativo en: {install_dir}")
                src_exe = get_resource_path("ucaba.exe")
                if not os.path.exists(src_exe):
                    # Intentar en subcarpetas dist / payload
                    src_exe = get_resource_path(os.path.join("dist", "ucaba.exe"))

                if not os.path.exists(src_exe):
                    raise FileNotFoundError(f"No se encontró el archivo 'ucaba.exe' en el paquete ({src_exe}).")

                os.makedirs(install_dir, exist_ok=True)
                shutil.copy2(src_exe, ucaba_target_exe)
                self.log(" - ucaba.exe copiado exitosamente.")
            self.set_progress(35)

            # 2. Agregar a PATH
            if self.opt_add_path.get():
                self.log("[2/4] Configurando variable de entorno PATH del usuario...")
                added = add_to_user_path(install_dir)
                if added:
                    self.log(" - Directorio agregado al PATH con éxito. (Notificación de sistema enviada).")
                else:
                    self.log(" - El directorio ya se encontraba registrado en el PATH.")
            self.set_progress(55)

            # 3. Asociar extensión de archivo .ucaba
            if self.opt_associate_ext.get():
                self.log("[3/4] Registrando extensión de archivo .ucaba en Windows con icono personalizado...")
                src_ico = get_resource_path("ucaba_icon.ico")
                target_ico = os.path.join(install_dir, "ucaba_icon.ico")
                if os.path.exists(src_ico):
                    try:
                        shutil.copy2(src_ico, target_ico)
                    except Exception:
                        pass

                if os.path.exists(ucaba_target_exe):
                    associate_file_extension(ucaba_target_exe, target_ico if os.path.exists(target_ico) else None)
                    self.log(" - Asociación completada con icono asignado a los archivos .ucaba.")
                else:
                    self.log(" - Aviso: ucaba.exe no encontrado para asociar archivos.")
            self.set_progress(75)

            # 4. Instalar extensión de VS Code
            if self.opt_install_vscode.get():
                self.log("[4/4] Instalando extensión en Visual Studio Code...")

                # VSIX
                vsix_candidate = get_resource_path("ucaba-language-support-1.2.0.vsix")
                if not os.path.exists(vsix_candidate):
                    vsix_candidate = get_resource_path(os.path.join("extension-vscode", "ucaba-language-support-1.2.0.vsix"))

                code_cli = find_code_cli()
                if code_cli and os.path.exists(vsix_candidate):
                    self.log(f" - Detectado ejecutable de VS Code CLI: {code_cli}")
                    try:
                        res = subprocess.run(
                            [code_cli, "--install-extension", vsix_candidate, "--force"],
                            capture_output=True,
                            text=True,
                            shell=True
                        )
                        if res.returncode == 0:
                            self.log(" - Extensión registrada mediante 'code --install-extension' correctamente.")
                        else:
                            self.log(f" - Aviso en VS Code CLI: {res.stdout.strip()} {res.stderr.strip()}")
                    except Exception as e:
                        self.log(f" - Aviso ejecutando code CLI: {e}")
                else:
                    self.log(" - VS Code CLI no encontrado en PATH; aplicando despliegue directo a disco...")

                # Copia directa en carpetas de extensiones
                ext_src = get_resource_path("extension-vscode")
                if not os.path.exists(ext_src):
                    ext_src = get_resource_path(os.path.join("payload", "extension-vscode"))

                user_home = os.path.expanduser("~")
                targets = [
                    os.path.join(user_home, ".vscode", "extensions", "ucaba.ucaba-language-support-1.2.0"),
                    os.path.join(user_home, ".antigravity-ide", "extensions", "ucaba-language-support")
                ]
                cursor_ext = os.path.join(user_home, ".cursor", "extensions")
                if os.path.exists(cursor_ext):
                    targets.append(os.path.join(cursor_ext, "ucaba.ucaba-language-support-1.2.0"))

                if os.path.exists(ext_src):
                    for t in targets:
                        parent = os.path.dirname(t)
                        if not os.path.exists(parent):
                            os.makedirs(parent, exist_ok=True)
                        if os.path.exists(t):
                            shutil.rmtree(t, ignore_errors=True)
                        shutil.copytree(ext_src, t, dirs_exist_ok=True)
                        self.log(f" - Extensión desplegada en: {t}")
                else:
                    self.log(" - Aviso: No se localizó la carpeta de la extensión para copia directa.")

            self.set_progress(100)
            self.set_status("¡Instalación completada exitosamente!", fg="#4ade80")
            self.log("\n>>> ¡PROCESO FINALIZADO CON ÉXITO! <<<")
            self.log("Puede abrir una nueva terminal y escribir: ucaba run <archivo.ucaba>")
            self.log("O abrir cualquier archivo .ucaba en VS Code para editarlo y ejecutarlo.")

            self.root.after(200, lambda: messagebox.showinfo(
                "Instalación Completada",
                "¡UCABA Pseudocódigo y la extensión para VS Code han sido instalados correctamente!\n\n"
                "Para comenzar:\n"
                "• Escribe 'ucaba --help' en una nueva consola\n"
                "• O abre tus archivos .ucaba en Visual Studio Code"
            ))

        except Exception as e:
            self.set_status(f"Error: {e}", fg="#f87171")
            self.log(f"\n[ERROR CRÍTICO]: {e}")
            self.root.after(200, lambda: messagebox.showerror("Error en la instalación", str(e)))

        finally:
            self.set_controls_enabled(True)

    def _run_uninstallation(self):
        try:
            self.set_progress(20)
            self.log("[1/3] Removiendo archivos del lenguaje...")
            install_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\UCABA\bin")
            if os.path.exists(install_dir):
                shutil.rmtree(os.path.dirname(install_dir), ignore_errors=True)
                self.log(f" - Carpeta eliminada: {install_dir}")

            self.set_progress(45)
            self.log("[2/3] Quitando UCABA de la variable de entorno PATH...")
            removed = remove_from_user_path(install_dir)
            if removed:
                self.log(" - Variable PATH restaurada.")

            self.log(" - Removiendo asociaciones de archivos .ucaba...")
            remove_file_association()

            self.set_progress(70)
            self.log("[3/3] Removiendo extensión de VS Code...")
            user_home = os.path.expanduser("~")
            ext_paths = [
                os.path.join(user_home, ".vscode", "extensions", "ucaba.ucaba-language-support-1.2.0"),
                os.path.join(user_home, ".vscode", "extensions", "ucaba.ucaba-language-support-1.1.0"),
                os.path.join(user_home, ".vscode", "extensions", "ucaba.ucaba-language-support-1.0.0"),
                os.path.join(user_home, ".vscode", "extensions", "ucaba-language-support"),
                os.path.join(user_home, ".antigravity-ide", "extensions", "ucaba-language-support")
            ]
            for ep in ext_paths:
                if os.path.exists(ep):
                    shutil.rmtree(ep, ignore_errors=True)
                    self.log(f" - Eliminada extensión: {ep}")

            code_cli = find_code_cli()
            if code_cli:
                try:
                    subprocess.run([code_cli, "--uninstall-extension", "ucaba.ucaba-language-support"], capture_output=True, text=True, shell=True)
                except Exception:
                    pass

            self.set_progress(100)
            self.set_status("Desinstalación completada.", fg="#94a3b8")
            self.log("\n>>> DESINSTALACIÓN COMPLETADA <<<")
            self.root.after(200, lambda: messagebox.showinfo(
                "Desinstalación",
                "UCABA y la extensión de VS Code han sido desinstalados de su equipo."
            ))

        except Exception as e:
            self.set_status(f"Error: {e}", fg="#f87171")
            self.log(f"[ERROR]: {e}")
        finally:
            self.set_controls_enabled(True)


def run_cli_install():
    """Ejecuta la instalación completa en modo consola desatendido (silencioso)."""
    safe_print("==================================================")
    safe_print("  INSTALACIÓN DESATENDIDA DE UCABA & VS CODE     ")
    safe_print("==================================================")
    install_dir = os.path.expandvars(r"%LOCALAPPDATA%\Programs\UCABA\bin")
    ucaba_target_exe = os.path.join(install_dir, "ucaba.exe")

    # 1. Copiar CLI
    safe_print(f"[1/4] Instalando ejecutable en: {install_dir}")
    src_exe = get_resource_path("ucaba.exe")
    if not os.path.exists(src_exe):
        src_exe = get_resource_path(os.path.join("payload", "ucaba.exe"))
    if not os.path.exists(src_exe):
        src_exe = get_resource_path(os.path.join("dist", "ucaba.exe"))

    if not os.path.exists(src_exe):
        safe_print(f"[ERROR] No se encontró el binario ucaba.exe ({src_exe})")
        sys.exit(1)

    os.makedirs(install_dir, exist_ok=True)
    shutil.copy2(src_exe, ucaba_target_exe)
    safe_print(" [OK] ucaba.exe instalado con éxito.")

    # 2. Agregar a PATH
    safe_print("[2/4] Registrando en variable PATH del usuario...")
    added = add_to_user_path(install_dir)
    if added:
        safe_print(" [OK] PATH actualizado y notificado a Windows.")
    else:
        safe_print(" [OK] PATH ya estaba configurado.")

    # 3. Asociar archivos
    safe_print("[3/4] Asociando archivos .ucaba en Windows con icono...")
    src_ico = get_resource_path("ucaba_icon.ico")
    target_ico = os.path.join(install_dir, "ucaba_icon.ico")
    if os.path.exists(src_ico):
        try:
            shutil.copy2(src_ico, target_ico)
        except Exception:
            pass
    associate_file_extension(ucaba_target_exe, target_ico if os.path.exists(target_ico) else None)
    safe_print(" [OK] Asociación de archivos .ucaba registrada con icono.")

    # 4. Extensión VS Code
    safe_print("[4/4] Instalando extensión en Visual Studio Code...")
    vsix_candidate = get_resource_path("ucaba-language-support-1.2.0.vsix")
    if not os.path.exists(vsix_candidate):
        vsix_candidate = get_resource_path(os.path.join("payload", "ucaba-language-support-1.2.0.vsix"))

    code_cli = find_code_cli()
    if code_cli and os.path.exists(vsix_candidate):
        safe_print(f" [INFO] Ejecutando: {code_cli} --install-extension ...")
        try:
            res = subprocess.run([code_cli, "--install-extension", vsix_candidate, "--force"], capture_output=True, text=True, shell=True)
            safe_print(" [OK] Registrado en VS Code CLI.")
        except Exception as e:
            safe_print(f" [AVISO] {e}")

    ext_src = get_resource_path("extension-vscode")
    if not os.path.exists(ext_src):
        ext_src = get_resource_path(os.path.join("payload", "extension-vscode"))

    user_home = os.path.expanduser("~")
    targets = [
        os.path.join(user_home, ".vscode", "extensions", "ucaba.ucaba-language-support-1.2.0"),
        os.path.join(user_home, ".antigravity-ide", "extensions", "ucaba-language-support")
    ]
    if os.path.exists(ext_src):
        for t in targets:
            parent = os.path.dirname(t)
            if not os.path.exists(parent):
                os.makedirs(parent, exist_ok=True)
            if os.path.exists(t):
                shutil.rmtree(t, ignore_errors=True)
            shutil.copytree(ext_src, t, dirs_exist_ok=True)
            safe_print(f" [OK] Extensión desplegada en: {t}")

    safe_print("\n==================================================")
    safe_print(" [¡ÉXITO!] Instalación completada correctamente.")
    safe_print("==================================================")


def main():
    setup_console()
    if "--silent" in sys.argv or "--install" in sys.argv or "-s" in sys.argv:
        run_cli_install()
        return

    enable_high_dpi()
    root = tk.Tk()
    app = InstallerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
