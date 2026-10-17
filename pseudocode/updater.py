# GNU General Public License v3.0 or later (GPL-3.0-or-later)
#
# Copyright (c) 2026 [Facu Falcone](a.facundo.falcone@gmail.com) All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Módulo de verificación y actualización automática de UCABA contra GitHub Releases.
Verifica en segundo plano si existe una versión más reciente (estilo pip) y
permite actualizar automáticamente ejecutando: ucaba update.
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
import http.client
import socket
import ssl
import email.message
import threading
import atexit
import subprocess
import tempfile
from typing import Optional, Tuple, Dict, Any

GITHUB_REPO = "caidevOficial/UCABA_Lang"
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
CACHE_TTL_SECONDS = 3600  # 1 hora de caché para verificaciones en segundo plano

_NEW_RELEASE_INFO: Optional[Dict[str, Any]] = None
_CHECK_STARTED = False
_BACKGROUND_THREAD: Optional[threading.Thread] = None


def parse_version(v_str: str) -> Tuple[int, ...]:
    """Parsea una cadena de versión semántica (ej: 'v1.5.0' o '1.5.2') a tupla de enteros."""
    clean = str(v_str).strip().lstrip("vV")
    parts = []
    for piece in clean.split("."):
        digits = "".join(ch for ch in piece if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def get_cache_file_path() -> str:
    """Devuelve la ruta al archivo de caché local de versiones."""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        cache_dir = os.path.join(local_app_data, "UCABA")
    else:
        cache_dir = os.path.join(os.path.expanduser("~"), ".ucaba")
    os.makedirs(cache_dir, exist_ok=True)
    return os.path.join(cache_dir, "version_cache.json")


def read_cached_version() -> Optional[Dict[str, Any]]:
    """Lee la última comprobación de versión guardada en caché si no ha expirado."""
    try:
        cache_file = get_cache_file_path()
        if os.path.exists(cache_file):
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            last_checked = data.get("last_checked", 0)
            if time.time() - last_checked < CACHE_TTL_SECONDS:
                return data
    except Exception:
        pass
    return None


def write_cached_version(data: Dict[str, Any]):
    """Guarda en caché local los metadatos de la última versión comprobada."""
    try:
        cache_file = get_cache_file_path()
        data["last_checked"] = time.time()
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def fetch_latest_release_online(timeout: float = 5.0) -> Optional[Dict[str, Any]]:
    """Consulta la API pública de GitHub para obtener la última versión lanzada."""
    try:
        req = urllib.request.Request(
            API_URL,
            headers={
                "User-Agent": "UCABA-Lang-Updater",
                "Accept": "application/vnd.github.v3+json"
            }
        )
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                payload = json.loads(response.read().decode("utf-8"))
                tag_name = payload.get("tag_name", "")
                latest_ver = tag_name.lstrip("vV")

                installer_url = ""
                cli_url = ""
                vsix_url = ""
                for asset in payload.get("assets", []):
                    name = asset.get("name", "")
                    dl_url = asset.get("browser_download_url", "")
                    if name.lower() == "instalador_ucaba.exe":
                        installer_url = dl_url
                    elif name.lower() == "ucaba.exe":
                        cli_url = dl_url
                    elif name.lower().endswith(".vsix"):
                        vsix_url = dl_url

                info = {
                    "tag_name": tag_name,
                    "latest_version": latest_ver,
                    "html_url": payload.get("html_url", f"https://github.com/{GITHUB_REPO}/releases/latest"),
                    "installer_url": installer_url,
                    "cli_url": cli_url,
                    "vsix_url": vsix_url,
                    "body": payload.get("body", "")
                }
                write_cached_version(info)
                return info
    except Exception:
        pass
    return None


def check_version_status(
    current_version: str,
    force_online: bool = False,
    timeout: float = 5.0
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Verifica el estado de versión contra GitHub Releases.
    Retorna una tupla (estado, info):
      - ("UPDATE_AVAILABLE", info): hay una versión superior disponible en GitHub.
      - ("UP_TO_DATE", info): la versión actual coincide o supera la última versión publicada.
      - ("NETWORK_ERROR", None): no se pudo conectar con GitHub ni obtener información válida.
    """
    info = None
    if force_online:
        info = fetch_latest_release_online(timeout=timeout)
    else:
        cached = read_cached_version()
        if cached and "latest_version" in cached:
            # Si en caché ya hay una versión superior a la actual, usarla
            if parse_version(cached["latest_version"]) > parse_version(current_version):
                info = cached
            else:
                info = fetch_latest_release_online(timeout=timeout) or cached
        else:
            info = fetch_latest_release_online(timeout=timeout)

    if not info or "latest_version" not in info:
        return "NETWORK_ERROR", None

    curr_tuple = parse_version(current_version)
    latest_tuple = parse_version(info["latest_version"])

    if latest_tuple > curr_tuple:
        return "UPDATE_AVAILABLE", info
    return "UP_TO_DATE", info


def check_for_update(
    current_version: str,
    allow_network: bool = True,
    force_online: bool = False
) -> Optional[Dict[str, Any]]:
    """Verifica si existe una versión más reciente que la actual."""
    status, info = check_version_status(
        current_version,
        force_online=force_online,
        timeout=5.0 if force_online else 2.0
    )
    if status == "UPDATE_AVAILABLE":
        return info
    return None


def print_update_notice(info: Dict[str, Any], current_version: str):
    """Muestra en terminal la notificación de actualización estilo pip."""
    latest_ver = info.get("latest_version", "desconocida")
    html_url = info.get("html_url", f"https://github.com/{GITHUB_REPO}/releases/latest")

    print("\n\033[33m[AVISO] Hay una nueva versión de UCABA disponible: "
          f"\033[1m{current_version}\033[0m\033[33m -> \033[1;32m{latest_ver}\033[0m")
    print(f"\033[33mPara actualizar automáticamente, ejecuta: \033[1;37mucaba update\033[0m")
    print(f"\033[90mO visita: {html_url}\033[0m\n", file=sys.stderr)


def _background_check_worker(current_version: str):
    global _NEW_RELEASE_INFO
    try:
        update = check_for_update(current_version, allow_network=True)
        if update:
            _NEW_RELEASE_INFO = update
    except Exception:
        pass


def start_background_check(current_version: str):
    """Inicia la comprobación de versión en un hilo en segundo plano no bloqueante."""
    global _CHECK_STARTED, _BACKGROUND_THREAD
    if _CHECK_STARTED:
        return

    # Silenciar en entornos automáticos, tests, CI o LSP
    if (
        os.environ.get("UCABA_NO_UPDATE_CHECK") == "1"
        or os.environ.get("UCABA_HIDE_BANNER") == "1"
        or os.environ.get("CI") == "true"
        or "GITHUB_ACTIONS" in os.environ
        or "unittest" in sys.modules
        or "pytest" in sys.modules
    ):
        return

    all_args = [str(arg).lower() for arg in list(sys.argv) + list(getattr(sys, "orig_argv", []))]
    fast_cmds = ("--version", "-v", "--help", "-h", "tokens", "lsp-check", "update", "upgrade")
    if any(arg in fast_cmds for arg in all_args):
        return

    _CHECK_STARTED = True

    # 1. Si ya tenemos en caché local reciente (< 1 hora):
    cached = read_cached_version()
    if cached and "latest_version" in cached:
        if parse_version(cached["latest_version"]) > parse_version(current_version):
            global _NEW_RELEASE_INFO
            _NEW_RELEASE_INFO = cached
        # Si la caché está fresca (haya actualización o ya estemos al día), no consultar en red
        return

    # 2. De lo contrario, consultar en segundo plano sin ralentizar la ejecución del programa
    t = threading.Thread(target=_background_check_worker, args=(current_version,), daemon=True)
    _BACKGROUND_THREAD = t
    t.start()


def _atexit_notice_hook(current_version: str):
    """Muestra la notificación al finalizar la ejecución del programa si se detectó nueva versión."""
    global _BACKGROUND_THREAD
    # No mostrar aviso duplicado si el comando ejecutado fue update/upgrade
    all_args = [str(arg).lower() for arg in list(sys.argv) + list(getattr(sys, "orig_argv", []))]
    if any(arg in ("update", "upgrade") for arg in all_args):
        return

    if _BACKGROUND_THREAD and _BACKGROUND_THREAD.is_alive():
        _BACKGROUND_THREAD.join(timeout=0.15)

    if _NEW_RELEASE_INFO:
        print_update_notice(_NEW_RELEASE_INFO, current_version)


def register_update_notice_on_exit(current_version: str):
    """Registra el hook de atexit para mostrar el aviso al terminar el comando."""
    start_background_check(current_version)
    atexit.register(_atexit_notice_hook, current_version)


def run_interactive_update(current_version: str, force: bool = False, silent: bool = False):
    """Descarga e instala la última versión de UCABA desde GitHub Releases."""
    print("==================================================")
    print("   ACTUALIZADOR OFICIAL DEL LENGUAJE UCABA       ")
    print("==================================================")
    print(f"Versión actual instalada: v{current_version}")
    print("Comprobando últimas versiones en GitHub Releases...")

    info = fetch_latest_release_online(timeout=5.0)
    if not info:
        print("[ERROR] No se pudo conectar con GitHub Releases. Verifica tu conexión a internet.")
        return 1

    latest_ver = info["latest_version"]
    curr_t = parse_version(current_version)
    late_t = parse_version(latest_ver)

    if late_t <= curr_t and not force:
        print(f"\n[OK] ¡Ya tienes la versión más reciente de UCABA instalada (v{current_version})!")
        return 0

    print(f"\n[ACTUALIZACIÓN DISPONIBLE]: v{current_version} -> v{latest_ver}")
    installer_url = info.get("installer_url")
    if not installer_url:
        print(f"[ERROR] No se encontró el archivo 'Instalador_UCABA.exe' en el release v{latest_ver}.")
        print(f"Por favor, descarga la actualización manualmente desde:\n{info['html_url']}")
        return 1

    # Descargar el instalador en un directorio temporal
    temp_dir = tempfile.mkdtemp(prefix="ucaba_update_")
    installer_path = os.path.join(temp_dir, "Instalador_UCABA.exe")

    print(f"\nDescargando instalador oficial de UCABA v{latest_ver}...")
    print(f"Fuente: {installer_url}")

    try:
        def _reporthook(block_num, block_size, total_size):
            if total_size > 0:
                downloaded = block_num * block_size
                percent = min(100.0, (downloaded / total_size) * 100.0)
                mb_down = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                sys.stdout.write(f"\rProgreso: [{percent:5.1f}%] {mb_down:5.1f}MB / {mb_total:5.1f}MB")
                sys.stdout.flush()

        urllib.request.urlretrieve(installer_url, installer_path, reporthook=_reporthook)
        print("\n\n[OK] Instalador descargado exitosamente.")
    except Exception as e:
        print(f"\n[ERROR] Falló la descarga del instalador: {e}")
        return 1

    print("\nIniciando asistente de instalación...")
    try:
        cmd = [installer_path]
        if silent:
            cmd.append("--silent")
        subprocess.Popen(cmd)
        print("[ÉXITO] El asistente de instalación se ha iniciado en su equipo.")
        print("Siga las instrucciones en pantalla para completar la actualización.")
    except Exception as e:
        print(f"[ERROR] No se pudo ejecutar el instalador: {e}")
        print(f"Puedes ejecutarlo manualmente desde: {installer_path}")
        return 1

    return 0
