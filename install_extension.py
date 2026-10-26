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


def patch_installed_icon_themes(ext_root: str, svg_path: str):
    """Integra el icono oficial de UCABA en temas de iconos instalados (Bearded Icons, Material Icon Theme, etc.)."""
    if not os.path.exists(ext_root) or not os.path.exists(svg_path):
        return

    try:
        items = os.listdir(ext_root)
    except Exception:
        return

    for item in items:
        folder = os.path.join(ext_root, item)
        if not os.path.isdir(folder):
            continue

        # 1. Bearded Icons
        if "beardedicons" in item.lower():
            icons_json = os.path.join(folder, "icons.json")
            if os.path.exists(icons_json):
                try:
                    dest_svg = os.path.join(folder, "icons", "ucaba-file.svg")
                    os.makedirs(os.path.dirname(dest_svg), exist_ok=True)
                    shutil.copy2(svg_path, dest_svg)
                    with open(icons_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    data["showLanguageModeIcons"] = True
                    if "iconDefinitions" not in data:
                        data["iconDefinitions"] = {}
                    data["iconDefinitions"]["_file_ucaba"] = {"iconPath": "./icons/ucaba-file.svg"}
                    if "fileExtensions" not in data:
                        data["fileExtensions"] = {}
                    data["fileExtensions"]["ucaba"] = "_file_ucaba"
                    if "languageIds" not in data:
                        data["languageIds"] = {}
                    data["languageIds"]["ucaba"] = "_file_ucaba"
                    with open(icons_json, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"[OK] Icono oficial UCABA integrado en Bearded Icons ({item})")
                except Exception as e:
                    print(f"[AVISO] No se pudo integrar en Bearded Icons: {e}")

        # 2. Material Icon Theme
        if "material-icon-theme" in item.lower():
            icons_json = os.path.join(folder, "dist", "material-icons.json")
            if not os.path.exists(icons_json):
                icons_json = os.path.join(folder, "icons.json")
            if os.path.exists(icons_json):
                try:
                    dest_svg = os.path.join(os.path.dirname(icons_json), "icons", "ucaba-file.svg")
                    os.makedirs(os.path.dirname(dest_svg), exist_ok=True)
                    shutil.copy2(svg_path, dest_svg)
                    with open(icons_json, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    data["showLanguageModeIcons"] = True
                    if "iconDefinitions" not in data:
                        data["iconDefinitions"] = {}
                    data["iconDefinitions"]["_file_ucaba"] = {"iconPath": "./icons/ucaba-file.svg"}
                    if "fileExtensions" not in data:
                        data["fileExtensions"] = {}
                    data["fileExtensions"]["ucaba"] = "_file_ucaba"
                    if "languageIds" not in data:
                        data["languageIds"] = {}
                    data["languageIds"]["ucaba"] = "_file_ucaba"
                    with open(icons_json, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2)
                    print(f"[OK] Icono oficial UCABA integrado en Material Icon Theme ({item})")
                except Exception as e:
                    print(f"[AVISO] No se pudo integrar en Material Icon Theme: {e}")


def patch_seti_theme(svg_path: str):
    """Integra el icono oficial de UCABA en el tema Seti por defecto de VS Code y Antigravity IDE."""
    if not os.path.exists(svg_path):
        return

    candidates = []
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if local_app_data:
            candidates.extend([
                os.path.join(local_app_data, "Programs", "Microsoft VS Code", "resources", "app", "extensions", "theme-seti"),
                os.path.join(local_app_data, "Programs", "Antigravity IDE", "resources", "app", "extensions", "theme-seti"),
            ])
    else:
        candidates.extend([
            "/usr/share/code/resources/app/extensions/theme-seti",
            "/usr/share/antigravity/resources/app/extensions/theme-seti",
            "/usr/share/codium/resources/app/extensions/theme-seti",
            "/opt/visual-studio-code/resources/app/extensions/theme-seti",
        ])

    for base in candidates:
        icon_theme = os.path.join(base, "icons", "vs-seti-icon-theme.json")
        if os.path.exists(icon_theme):
            try:
                dest_svg = os.path.join(base, "icons", "ucaba-file.svg")
                shutil.copy2(svg_path, dest_svg)
                with open(icon_theme, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data["showLanguageModeIcons"] = True
                if "iconDefinitions" not in data:
                    data["iconDefinitions"] = {}
                data["iconDefinitions"]["_ucaba"] = {"iconPath": "./ucaba-file.svg"}
                if "fileExtensions" not in data:
                    data["fileExtensions"] = {}
                data["fileExtensions"]["ucaba"] = "_ucaba"
                if "languageIds" not in data:
                    data["languageIds"] = {}
                data["languageIds"]["ucaba"] = "_ucaba"
                with open(icon_theme, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                print(f"[OK] Icono oficial UCABA integrado en Seti: {base}")
            except Exception as e:
                print(f"[AVISO] No se pudo actualizar Seti en {base}: {e}")


def fix_windows_file_icons():
    """Asegura que el Registro de Windows asocie los archivos .ucaba con ucaba_icon.ico."""
    if sys.platform != "win32":
        return
    try:
        import winreg
        import ctypes
        user_profile = os.environ.get("USERPROFILE", "")
        icon_path = os.path.join(user_profile, "AppData", "Local", "Programs", "UCABA", "bin", "ucaba_icon.ico")
        if not os.path.exists(icon_path):
            repo_ico = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ucaba_icon.ico")
            if os.path.exists(repo_ico):
                icon_path = repo_ico
        if os.path.exists(icon_path):
            val = f'"{icon_path}"'
            classes = [r"Software\Classes\.ucaba", r"Software\Classes\UCABAFile", r"Software\Classes\UCABA.Program"]
            for cls in classes:
                with winreg.CreateKey(winreg.HKEY_CURRENT_USER, rf"{cls}\DefaultIcon") as k:
                    winreg.SetValueEx(k, "", 0, winreg.REG_SZ, val)
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0, None, None)
            print("[OK] Asociaciones de icono de Windows Explorer (.ucaba) actualizadas exitosamente.")
    except Exception as e:
        print(f"[AVISO] No se pudo actualizar iconos en Registro de Windows: {e}")


def install():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    ext_src = os.path.join(repo_root, "extension-vscode")
    svg_icon = os.path.join(ext_src, "icons", "ucaba-file.svg")

    # Encontrar el VSIX más reciente generado
    vsix_files = [os.path.join(ext_src, f) for f in os.listdir(ext_src) if f.endswith(".vsix")]
    vsix_path = sorted(vsix_files, key=os.path.getmtime, reverse=True)[0] if vsix_files else None

    try:
        from pseudocode import __version__ as ucaba_version
    except Exception:
        ucaba_version = "2.0.3"

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

            # Parchear temas de iconos instalados (Bearded Icons, Material)
            patch_installed_icon_themes(ext_root, svg_icon)

    # Parchear tema Seti integrado del sistema
    patch_seti_theme(svg_icon)

    # Corregir iconos en Windows Registry para Windows Explorer
    fix_windows_file_icons()

    # Si existe el archivo VSIX y herramientas CLI, registrar formalmente por CLI en editores
    if vsix_path and os.path.exists(vsix_path):
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        code_cmd = os.path.join(local_app_data, "Programs", "Microsoft VS Code", "bin", "code.cmd") if local_app_data else "code"
        antigravity_cmd = os.path.join(local_app_data, "Programs", "Antigravity IDE", "bin", "antigravity-ide.cmd") if local_app_data else "antigravity-ide"
        cursor_cmd = os.path.join(local_app_data, "Programs", "cursor", "resources", "app", "bin", "cursor.cmd") if local_app_data else "cursor"
        codium_cmd = os.path.join(local_app_data, "Programs", "VSCodium", "bin", "codium.cmd") if local_app_data else "codium"

        editors = [
            ("code", ["code", "--install-extension", vsix_path, "--force"]),
            ("code.cmd", [code_cmd, "--install-extension", vsix_path, "--force"]),
            ("antigravity-ide", ["antigravity-ide", "--install-extension", vsix_path, "--force"]),
            ("antigravity-ide.cmd", [antigravity_cmd, "--install-extension", vsix_path, "--force"]),
            ("antigravity", ["antigravity", "--install-extension", vsix_path, "--force"]),
            ("cursor", ["cursor", "--install-extension", vsix_path, "--force"]),
            ("cursor.cmd", [cursor_cmd, "--install-extension", vsix_path, "--force"]),
            ("codium", ["codium", "--install-extension", vsix_path, "--force"]),
            ("codium.cmd", [codium_cmd, "--install-extension", vsix_path, "--force"]),
        ]
        registered_targets = set()
        for name, cmd in editors:
            exe = cmd[0]
            if os.path.exists(exe) or shutil.which(exe):
                target_key = "vscode" if "code" in name else ("antigravity" if "antigravity" in name else name)
                if target_key in registered_targets:
                    continue
                try:
                    print(f"[...] Registrando extensión en {name} mediante CLI...")
                    res = subprocess.run(cmd, capture_output=True, text=True, shell=(os.name == 'nt'))
                    if res.returncode == 0:
                        print(f"[OK] Extensión registrada exitosamente en {name}.")
                        registered_targets.add(target_key)
                    else:
                        print(f"[AVISO] {name} salida: {res.returncode}. {res.stdout.strip()} {res.stderr.strip()}")
                except Exception as e:
                    print(f"[AVISO] No se pudo invocar '{name}': {e}")


if __name__ == "__main__":
    install()
