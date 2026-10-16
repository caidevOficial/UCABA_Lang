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

import os
import sys
import shutil
import subprocess

def install():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    ext_src = os.path.join(repo_root, "extension-vscode")
    
    # Encontrar el VSIX más reciente generado
    vsix_files = [os.path.join(ext_src, f) for f in os.listdir(ext_src) if f.endswith(".vsix")]
    vsix_path = sorted(vsix_files, key=os.path.getmtime, reverse=True)[0] if vsix_files else None

    try:
        from pseudocode import __version__ as ucaba_version
    except Exception:
        ucaba_version = "1.10.0"

    user_home = os.path.expanduser("~")
    current_folder = f"ucaba.ucaba-language-support-{ucaba_version}"
    
    # Limpiar dinámicamente versiones previas obsoletas para evitar colisiones
    ext_roots = [
        os.path.join(user_home, ".vscode", "extensions"),
        os.path.join(user_home, ".cursor", "extensions"),
        os.path.join(user_home, ".antigravity-ide", "extensions")
    ]
    for ext_root in ext_roots:
        if os.path.exists(ext_root):
            for item in os.listdir(ext_root):
                if item.startswith("ucaba.ucaba-language-support-") and item != current_folder:
                    old_path = os.path.join(ext_root, item)
                    try:
                        shutil.rmtree(old_path, ignore_errors=True)
                        print(f"[CLEANUP] Eliminada versión obsoleta: {old_path}")
                    except Exception as e:
                        print(f"[AVISO] No se pudo eliminar versión previa {old_path}: {e}")

    destinations = [
        os.path.join(user_home, ".vscode", "extensions", current_folder),
        os.path.join(user_home, ".vscode", "extensions", "ucaba-language-support"),
        os.path.join(user_home, ".antigravity-ide", "extensions", "ucaba-language-support")
    ]
    cursor_ext = os.path.join(user_home, ".cursor", "extensions")
    if os.path.exists(cursor_ext):
        destinations.append(os.path.join(cursor_ext, current_folder))

    for dst in destinations:
        parent = os.path.dirname(dst)
        if not os.path.exists(parent):
            os.makedirs(parent, exist_ok=True)
        if os.path.exists(dst):
            shutil.rmtree(dst, ignore_errors=True)
        shutil.copytree(ext_src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.vsix"))
        print(f"[OK] Archivos copiados a: {dst}")

    # Si existe el archivo VSIX y el comando 'code', instalar directamente
    if os.path.exists(vsix_path):
        try:
            print(f"[...] Registrando extensión en VS Code mediante 'code --install-extension'...")
            res = subprocess.run(["code", "--install-extension", vsix_path, "--force"], capture_output=True, text=True, shell=True)
            if res.returncode == 0:
                print(f"[OK] Extensión registrada exitosamente en VS Code.")
            else:
                print(f"[AVISO] Código de salida: {res.returncode}. {res.stdout} {res.stderr}")
        except Exception as e:
            print(f"[AVISO] No se pudo invocar 'code': {e}")

if __name__ == "__main__":
    install()

