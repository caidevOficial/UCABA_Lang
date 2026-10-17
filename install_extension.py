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

import json
import os
import shutil
import subprocess
import sys


def clean_obsolete_file(ext_root: str):
    """Limpia marcas de versiones obsoletas de UCABA en .obsolete."""
    obsolete_path = os.path.join(ext_root, ".obsolete")
    if os.path.exists(obsolete_path):
        try:
            with open(obsolete_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cleaned = {k: v for k, v in data.items() if "ucaba" not in k.lower()}
            with open(obsolete_path, "w", encoding="utf-8") as f:
                json.dump(cleaned, f, indent=2)
            print(f"[CLEANUP] Limpiado registro de obsoletos en: {obsolete_path}")
        except Exception as e:
            print(f"[AVISO] No se pudo procesar .obsolete en {ext_root}: {e}")


def update_extensions_json(ext_root: str, current_folder: str, version: str):
    """Actualiza o registra la extensión UCABA en extensions.json para que el IDE la reconozca."""
    ext_json_path = os.path.join(ext_root, "extensions.json")
    target_folder_path = os.path.join(ext_root, current_folder)
    posix_path = "/" + target_folder_path.replace("\\", "/").lstrip("/")

    entry = {
        "identifier": {
            "id": "ucaba.ucaba-language-support"
        },
        "version": version,
        "location": {
            "$mid": 1,
            "fsPath": target_folder_path,
            "_sep": 1,
            "external": f"file://{posix_path}",
            "path": posix_path,
            "scheme": "file"
        },
        "relativeLocation": current_folder,
        "metadata": {
            "isApplicationScoped": False,
            "isMachineScoped": False,
            "isBuiltin": False,
            "pinned": True,
            "source": "vsix"
        }
    }

    if os.path.exists(ext_json_path):
        try:
            with open(ext_json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                # Filtrar entradas previas de ucaba
                data = [x for x in data if not (isinstance(x, dict) and x.get("identifier", {}).get("id") == "ucaba.ucaba-language-support")]
                data.append(entry)
                with open(ext_json_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"[OK] extensions.json actualizado con éxito en: {ext_root}")
        except Exception as e:
            print(f"[AVISO] No se pudo actualizar {ext_json_path}: {e}")


def install():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    ext_src = os.path.join(repo_root, "extension-vscode")

    # Encontrar el VSIX más reciente generado
    vsix_files = [os.path.join(ext_src, f) for f in os.listdir(ext_src) if f.endswith(".vsix")]
    vsix_path = sorted(vsix_files, key=os.path.getmtime, reverse=True)[0] if vsix_files else None

    try:
        from pseudocode import __version__ as ucaba_version
    except Exception:
        ucaba_version = "2.0.0"

    user_home = os.path.expanduser("~")
    current_folder = f"ucaba.ucaba-language-support-{ucaba_version}"

    ext_roots = [
        os.path.join(user_home, ".vscode", "extensions"),
        os.path.join(user_home, ".vscode-oss", "extensions"),
        os.path.join(user_home, ".vscode-insiders", "extensions"),
        os.path.join(user_home, ".cursor", "extensions"),
        os.path.join(user_home, ".antigravity-ide", "extensions"),
        os.path.join(user_home, ".antigravity", "extensions"),
        os.path.join(user_home, ".var", "app", "com.visualstudio.code", "data", "vscode", "extensions"),
        os.path.join(user_home, ".var", "app", "com.vscodium.codium", "data", "vscode", "extensions")
    ]

    for ext_root in ext_roots:
        if os.path.exists(ext_root) or os.path.exists(os.path.dirname(ext_root)):
            os.makedirs(ext_root, exist_ok=True)
            for item in os.listdir(ext_root):
                if item.startswith("ucaba.ucaba-language-support-") and item != current_folder:
                    old_path = os.path.join(ext_root, item)
                    try:
                        shutil.rmtree(old_path, ignore_errors=True)
                        print(f"[CLEANUP] Eliminada versión obsoleta: {old_path}")
                    except Exception as e:
                        print(f"[AVISO] No se pudo eliminar versión previa {old_path}: {e}")
                elif item == "ucaba-language-support":
                    shutil.rmtree(os.path.join(ext_root, item), ignore_errors=True)

            # Limpiar obsoletos
            clean_obsolete_file(ext_root)

            # Copiar archivos de extensión
            dst = os.path.join(ext_root, current_folder)
            if os.path.exists(dst):
                shutil.rmtree(dst, ignore_errors=True)
            shutil.copytree(ext_src, dst, dirs_exist_ok=True, ignore=shutil.ignore_patterns("*.vsix"))
            print(f"[OK] Archivos de extensión desplegados en: {dst}")

            # Registrar en extensions.json
            update_extensions_json(ext_root, current_folder, ucaba_version)

    # Si existe el archivo VSIX y herramientas CLI, intentar registrar por CLI también
    if vsix_path and os.path.exists(vsix_path):
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        code_cmd = os.path.join(local_app_data, "Programs", "Microsoft VS Code", "bin", "code.cmd") if local_app_data else "code"
        editors = [
            ("code", ["code", "--install-extension", vsix_path, "--force"]),
            ("code.cmd", [code_cmd, "--install-extension", vsix_path, "--force"]),
            ("cursor", ["cursor", "--install-extension", vsix_path, "--force"]),
            ("codium", ["codium", "--install-extension", vsix_path, "--force"]),
            ("antigravity", ["antigravity", "--install-extension", vsix_path, "--force"])
        ]
        for name, cmd in editors:
            exe = cmd[0]
            if os.path.exists(exe) or shutil.which(exe):
                try:
                    print(f"[...] Registrando extensión en {name} mediante CLI...")
                    res = subprocess.run(cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
                    if res.returncode == 0:
                        print(f"[OK] Extensión registrada exitosamente en {name}.")
                    else:
                        print(f"[AVISO] {name} salida: {res.returncode}. {res.stdout.strip()} {res.stderr.strip()}")
                except Exception as e:
                    print(f"[AVISO] No se pudo invocar '{name}': {e}")


if __name__ == "__main__":
    install()
