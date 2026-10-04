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

    user_home = os.path.expanduser("~")
    destinations = [
        os.path.join(user_home, ".vscode", "extensions", "ucaba.ucaba-language-support-1.2.0"),
        os.path.join(user_home, ".vscode", "extensions", "ucaba.ucaba-language-support-1.1.0"),
        os.path.join(user_home, ".vscode", "extensions", "ucaba.ucaba-language-support-1.0.0"),
        os.path.join(user_home, ".vscode", "extensions", "ucaba-language-support"),
        os.path.join(user_home, ".antigravity-ide", "extensions", "ucaba-language-support")
    ]

    # Detectar dinámicamente cualquier carpeta ucaba existente en extensiones
    for base_dir in [os.path.join(user_home, ".vscode", "extensions"), os.path.join(user_home, ".antigravity-ide", "extensions")]:
        if os.path.exists(base_dir):
            for item in os.listdir(base_dir):
                if "ucaba" in item.lower():
                    cand = os.path.join(base_dir, item)
                    if cand not in destinations:
                        destinations.append(cand)

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

