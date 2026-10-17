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
Script de construcción para compilar el Instalador Todo-en-Uno (Instalador_UCABA.exe) y ucaba.exe.
Por defecto utiliza el motor y toolchain de Rust (2.0.0-alpha.1) de alto rendimiento:
1. Compila crates/ucaba_cli -> target/release/ucaba.exe (con icono PE integrado via winres).
2. Compila crates/ucaba_installer -> target/release/Instalador_UCABA.exe (asistente GUI eframe/egui autónomo).
3. Copia ambos binarios a dist/ y calcula sus hashes SHA-256 y tamaños.
Permite el flag '--legacy' para compilar la versión histórica basada en PyInstaller si fuera necesario.
"""

import os
import sys
import shutil
import hashlib
import argparse
import subprocess

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_sha256(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def run_command(cmd, cwd=REPO_ROOT):
    cmd_str = ' '.join(cmd) if isinstance(cmd, list) else cmd
    print(f"\n[BUILD] Ejecutando: {cmd_str}")
    res = subprocess.run(cmd, cwd=cwd, shell=True)
    if res.returncode != 0:
        raise RuntimeError(f"El comando falló con código {res.returncode}")


def build_rust():
    print("==================================================")
    print("  CONSTRUCCIÓN DEL ECOSISTEMA NATIVO UCABA (RUST) ")
    print("==================================================")

    dist_dir = os.path.join(REPO_ROOT, "dist")
    os.makedirs(dist_dir, exist_ok=True)

    # 1. Compilar CLI nativo
    print("\n--- Paso 1: Compilando binario nativo ucaba.exe (crates/ucaba_cli) ---")
    run_command("cargo build --release -p ucaba_cli")

    src_cli = os.path.join(REPO_ROOT, "target", "release", "ucaba.exe")
    dst_cli = os.path.join(dist_dir, "ucaba.exe")
    if not os.path.exists(src_cli):
        raise FileNotFoundError(f"No se generó {src_cli}")
    shutil.copy2(src_cli, dst_cli)
    cli_mb = os.path.getsize(dst_cli) / (1024 * 1024)
    print(f" [OK] ucaba.exe copiado a dist/ ({cli_mb:.2f} MB, SHA256: {get_sha256(dst_cli)})")

    # 2. Compilar Instalador GUI nativo
    print("\n--- Paso 2: Compilando Instalador_UCABA.exe (crates/ucaba_installer) ---")
    run_command("cargo build --release -p ucaba_installer")

    src_inst = os.path.join(REPO_ROOT, "target", "release", "Instalador_UCABA.exe")
    dst_inst = os.path.join(dist_dir, "Instalador_UCABA.exe")
    if not os.path.exists(src_inst):
        raise FileNotFoundError(f"No se generó {src_inst}")
    shutil.copy2(src_inst, dst_inst)
    inst_mb = os.path.getsize(dst_inst) / (1024 * 1024)
    print(f" [OK] Instalador_UCABA.exe copiado a dist/ ({inst_mb:.2f} MB, SHA256: {get_sha256(dst_inst)})")

    print("\n==================================================")
    print(" [¡ÉXITO!] Artefactos de UCABA generados exitosamente:")
    print(f" 1. CLI:        {dst_cli} ({cli_mb:.2f} MB)")
    print(f" 2. Instalador: {dst_inst} ({inst_mb:.2f} MB)")
    print("==================================================")


def build_legacy():
    print("==================================================")
    print("  CONSTRUCCIÓN LEGACY (PYTHON / PYINSTALLER)      ")
    print("==================================================")

    dist_dir = os.path.join(REPO_ROOT, "dist")
    payload_dir = os.path.join(REPO_ROOT, "payload")
    os.makedirs(payload_dir, exist_ok=True)

    ico_file = os.path.join(REPO_ROOT, "ucaba_icon.ico")
    ucaba_exe = os.path.join(dist_dir, "ucaba.exe")
    print("\n--- Paso 1: Compilando binario ucaba.exe desde pseudocode/cli.py ---")
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

    print("\n--- Paso 2: Preparando payload ---")
    shutil.copy2(ucaba_exe, os.path.join(payload_dir, "ucaba.exe"))

    if os.path.exists(ico_file):
        shutil.copy2(ico_file, os.path.join(payload_dir, "ucaba_icon.ico"))

    header_logo = os.path.join(REPO_ROOT, "ucaba_logo_header.png")
    if os.path.exists(header_logo):
        shutil.copy2(header_logo, os.path.join(payload_dir, "ucaba_logo_header.png"))

    for existing_vsix in [os.path.join(payload_dir, f) for f in os.listdir(payload_dir) if f.endswith(".vsix")]:
        try:
            os.remove(existing_vsix)
        except OSError:
            pass

    vsix_files = [os.path.join(REPO_ROOT, "extension-vscode", f) for f in os.listdir(os.path.join(REPO_ROOT, "extension-vscode")) if f.endswith(".vsix")]
    if vsix_files:
        vsix_src = sorted(vsix_files, key=os.path.getmtime, reverse=True)[0]
        vsix_dst = os.path.join(payload_dir, os.path.basename(vsix_src))
        shutil.copy2(vsix_src, vsix_dst)

    ext_payload_dir = os.path.join(payload_dir, "extension-vscode")
    if os.path.exists(ext_payload_dir):
        shutil.rmtree(ext_payload_dir, ignore_errors=True)

    ext_src_dir = os.path.join(REPO_ROOT, "extension-vscode")
    shutil.copytree(
        ext_src_dir,
        ext_payload_dir,
        ignore=shutil.ignore_patterns("*.vsix", ".git*", "node_modules")
    )

    print("\n--- Paso 3: Compilando Instalador_UCABA.exe con PyInstaller ---")
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
        print(f" [¡ÉXITO!] Instalador legacy generado exitosamente:")
        print(f" Archivo: {final_exe}")
        print(f" Tamaño:  {size_mb:.2f} MB")
        print("==================================================")
    else:
        raise FileNotFoundError(f"No se generó {final_exe}")


def main():
    parser = argparse.ArgumentParser(description="Constructor de artefactos de UCABA")
    parser.add_argument("--legacy", action="store_true", help="Compilar versión histórica usando PyInstaller")
    args = parser.parse_args()

    if args.legacy:
        build_legacy()
    else:
        build_rust()


if __name__ == "__main__":
    main()
