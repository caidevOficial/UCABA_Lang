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
Script de construcción para compilar el Instalador Todo-en-Uno (Instalador_UCABA.exe).
Orquesta:
1. Compilación del binario nativo ucaba.exe
2. Empaquetado del payload (ucaba.exe + VSIX + archivos de extensión)
3. Compilación de installer_gui.py en un único Instalador_UCABA.exe
"""

import os
import sys
import shutil
import subprocess

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))

def run_command(cmd, cwd=REPO_ROOT):
    print(f"\n[BUILD] Ejecutando: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    res = subprocess.run(cmd, cwd=cwd, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"El comando falló con código {res.returncode}")

def build():
    print("==================================================")
    print("  CONSTRUCCIÓN DEL INSTALADOR AUTÓNOMO UCABA      ")
    print("==================================================")

    dist_dir = os.path.join(REPO_ROOT, "dist")
    payload_dir = os.path.join(REPO_ROOT, "payload")
    os.makedirs(payload_dir, exist_ok=True)

    # 1. Compilar ucaba.exe con su icono directamente desde cli.py
    ico_file = os.path.join(REPO_ROOT, "ucaba_icon.ico")
    ucaba_exe = os.path.join(dist_dir, "ucaba.exe")
    print("\n--- Paso 1: Compilando binario nativo ucaba.exe desde cli.py con nuevo icono ---")
    ucaba_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "ucaba",
        "--onefile",
        "--clean",
        "--paths", "."
    ]
    if os.path.exists(ico_file):
        ucaba_cmd.extend(["--icon", "./ucaba_icon.ico"])
    ver_ucaba = os.path.join(REPO_ROOT, "version_info_ucaba.txt")
    if os.path.exists(ver_ucaba):
        ucaba_cmd.extend(["--version-file", "./version_info_ucaba.txt"])
    ucaba_cmd.append(os.path.join("pseudocode", "cli.py"))
    run_command(ucaba_cmd)

    # 2. Copiar componentes a la carpeta payload
    print("\n--- Paso 2: Preparando payload ---")
    shutil.copy2(ucaba_exe, os.path.join(payload_dir, "ucaba.exe"))
    print(" [OK] ucaba.exe copiado a payload/")

    if os.path.exists(ico_file):
        shutil.copy2(ico_file, os.path.join(payload_dir, "ucaba_icon.ico"))
        print(" [OK] ucaba_icon.ico copiado a payload/")

    header_logo = os.path.join(REPO_ROOT, "ucaba_logo_header.png")
    if os.path.exists(header_logo):
        shutil.copy2(header_logo, os.path.join(payload_dir, "ucaba_logo_header.png"))
        print(" [OK] ucaba_logo_header.png copiado a payload/")

    vsix_src = os.path.join(REPO_ROOT, "extension-vscode", "ucaba-language-support-1.2.0.vsix")
    shutil.copy2(vsix_src, os.path.join(payload_dir, "ucaba-language-support-1.2.0.vsix"))
    print(" [OK] VSIX copiado a payload/")

    ext_payload_dir = os.path.join(payload_dir, "extension-vscode")
    if os.path.exists(ext_payload_dir):
        shutil.rmtree(ext_payload_dir, ignore_errors=True)

    # Copiar archivos relevantes de extension-vscode (evitando .vsix antiguos)
    ext_src_dir = os.path.join(REPO_ROOT, "extension-vscode")
    shutil.copytree(
        ext_src_dir,
        ext_payload_dir,
        ignore=shutil.ignore_patterns("*.vsix", ".git*", "node_modules")
    )
    print(" [OK] Directorio de extensión copiado a payload/extension-vscode")

    # 3. Compilar el Instalador_UCABA.exe con icono
    print("\n--- Paso 3: Compilando Instalador_UCABA.exe con PyInstaller e icono ---")
    add_data_payload = "./payload;payload"
    pyinstaller_cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "Instalador_UCABA",
        "--noconsole",
        "--onefile",
        "--clean",
        "--add-data", add_data_payload
    ]
    if os.path.exists(ico_file):
        pyinstaller_cmd.extend(["--icon", "./ucaba_icon.ico"])
        pyinstaller_cmd.extend(["--add-data", "./ucaba_icon.ico;."])
    if os.path.exists(header_logo):
        pyinstaller_cmd.extend(["--add-data", "./ucaba_logo_header.png;."])
    ver_installer = os.path.join(REPO_ROOT, "version_info_installer.txt")
    if os.path.exists(ver_installer):
        pyinstaller_cmd.extend(["--version-file", "./version_info_installer.txt"])

    pyinstaller_cmd.append("installer_gui.py")
    run_command(pyinstaller_cmd)

    final_exe = os.path.join(dist_dir, "Instalador_UCABA.exe")
    if os.path.exists(final_exe):
        size_mb = os.path.getsize(final_exe) / (1024 * 1024)
        print("\n==================================================")
        print(f" [¡ÉXITO!] Instalador generado exitosamente:")
        print(f" Archivo: {final_exe}")
        print(f" Tamaño:  {size_mb:.2f} MB")
        print("==================================================")
    else:
        raise FileNotFoundError(f"No se generó {final_exe}")

if __name__ == "__main__":
    build()
