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

"""
Constructor de paquetes para Linux para el lenguaje UCABA.
Genera de manera automatizada y reproducible:
1. Tarball portable standalone: ucaba-<version>-linux-x64.tar.gz
   (con binario nativo, scripts de install/uninstall, VSIX, icono, desktop entry y mime)
2. Paquete Debian / Ubuntu: ucaba_<version>_amd64.deb
   (con binario en /usr/bin, integración XDG en /usr/share y scripts postinst/postrm)
"""

import os
import sys
import io
import stat
import shutil
import tarfile
import hashlib
import argparse
import subprocess

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))


def get_version() -> str:
    """Obtiene la versión canónica desde pseudocode/__init__.py."""
    init_path = os.path.join(REPO_ROOT, "pseudocode", "__init__.py")
    if os.path.exists(init_path):
        with open(init_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "1.9.0"


def find_latest_vsix() -> str:
    """Localiza el archivo .vsix más reciente en extension-vscode/."""
    ext_dir = os.path.join(REPO_ROOT, "extension-vscode")
    if not os.path.exists(ext_dir):
        return ""
    vsix_files = [os.path.join(ext_dir, f) for f in os.listdir(ext_dir) if f.endswith(".vsix")]
    if not vsix_files:
        return ""
    return sorted(vsix_files, key=os.path.getmtime, reverse=True)[0]


def get_sha256(filepath: str) -> str:
    """Calcula el hash SHA-256 de un archivo."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def generate_desktop_entry() -> str:
    return """[Desktop Entry]
Type=Application
Name=UCABA Pseudocode
GenericName=Pseudocode Compiler & Runner
Comment=Intérprete de Pseudocódigo en Español Fuertemente Tipado (UCABA)
Exec=ucaba %f
Terminal=true
Icon=ucaba
MimeType=application/x-ucaba;text/x-ucaba;
Categories=Development;IDE;
Keywords=ucaba;pseudocode;compiler;interpreter;utn;
"""


def generate_mime_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<mime-info xmlns="http://www.freedesktop.org/standards/shared-mime-info">
    <mime-type type="application/x-ucaba">
        <comment>UCABA Pseudocode Source File</comment>
        <comment xml:lang="es">Archivo fuente de Pseudocódigo UCABA</comment>
        <icon name="ucaba"/>
        <glob pattern="*.ucaba"/>
    </mime-type>
</mime-info>
"""


def generate_install_sh(version: str, vsix_name: str) -> str:
    return f"""#!/bin/bash
# ==============================================================================
# Script de Instalación Oficial de UCABA para Linux (v{version})
# Lenguaje de Pseudocódigo en Español Fuertemente Tipado
# ==============================================================================
set -e

REPO_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
BIN_NAME="ucaba"
VERSION="{version}"

# Estilos y colores
RED='\\033[0;31m'
GREEN='\\033[0;32m'
BLUE='\\033[0;34m'
MAGENTA='\\033[0;35m'
CYAN='\\033[0;36m'
NC='\\033[0m'

echo -e "${{MAGENTA}}=====================================================${{NC}}"
echo -e "${{MAGENTA}}       INSTALADOR DE UCABA v${{VERSION}} PARA LINUX         ${{NC}}"
echo -e "${{MAGENTA}}=====================================================${{NC}}"

if [ "$(id -u)" -eq 0 ]; then
    INSTALL_PREFIX="/usr/local"
    BIN_DIR="$INSTALL_PREFIX/bin"
    SHARE_DIR="$INSTALL_PREFIX/share/ucaba"
    APPS_DIR="/usr/share/applications"
    ICONS_DIR="/usr/share/icons/hicolor/256x256/apps"
    MIME_DIR="/usr/share/mime/packages"
    echo -e "${{CYAN}}[INFO] Modo del Sistema (instalación global)...${{NC}}"
else
    INSTALL_PREFIX="$HOME/.local"
    BIN_DIR="$INSTALL_PREFIX/bin"
    SHARE_DIR="$INSTALL_PREFIX/share/ucaba"
    APPS_DIR="$INSTALL_PREFIX/share/applications"
    ICONS_DIR="$INSTALL_PREFIX/share/icons/hicolor/256x256/apps"
    MIME_DIR="$INSTALL_PREFIX/share/mime/packages"
    echo -e "${{CYAN}}[INFO] Modo de Usuario ($INSTALL_PREFIX)...${{NC}}"
fi

# 1. Crear directorios destino
mkdir -p "$BIN_DIR"
mkdir -p "$SHARE_DIR"
mkdir -p "$APPS_DIR"
mkdir -p "$ICONS_DIR"
mkdir -p "$MIME_DIR"

# 2. Copiar binario ejecutable
if [ -f "$REPO_DIR/$BIN_NAME" ]; then
    cp "$REPO_DIR/$BIN_NAME" "$BIN_DIR/$BIN_NAME"
    chmod +x "$BIN_DIR/$BIN_NAME"
    echo -e "${{GREEN}}[OK] Binario instalado en: $BIN_DIR/$BIN_NAME${{NC}}"
else
    echo -e "${{RED}}[ERROR] No se encontró el binario $BIN_NAME en $REPO_DIR${{NC}}"
    exit 1
fi

# 3. Copiar icono
if [ -f "$REPO_DIR/ucaba_icon.png" ]; then
    cp "$REPO_DIR/ucaba_icon.png" "$ICONS_DIR/ucaba.png"
    echo -e "${{GREEN}}[OK] Icono oficial instalado en: $ICONS_DIR/ucaba.png${{NC}}"
fi

# 4. Registrar tipo MIME (.ucaba)
if [ -f "$REPO_DIR/ucaba.xml" ]; then
    cp "$REPO_DIR/ucaba.xml" "$MIME_DIR/ucaba.xml"
    if which update-mime-database >/dev/null 2>&1; then
        update-mime-database "$(dirname "$MIME_DIR")" 2>/dev/null || true
    fi
    echo -e "${{GREEN}}[OK] Tipo MIME application/x-ucaba registrado (.ucaba).${{NC}}"
fi

# 5. Instalar Desktop Entry
if [ -f "$REPO_DIR/ucaba.desktop" ]; then
    cp "$REPO_DIR/ucaba.desktop" "$APPS_DIR/ucaba.desktop"
    if which update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$APPS_DIR" 2>/dev/null || true
    fi
    echo -e "${{GREEN}}[OK] Acceso de escritorio instalado en: $APPS_DIR/ucaba.desktop${{NC}}"
fi

# 6. Registrar extensión VSIX en editores
VSIX_FILE="$REPO_DIR/{vsix_name}"
if [ -f "$VSIX_FILE" ]; then
    cp "$VSIX_FILE" "$SHARE_DIR/"
    echo -e "${{GREEN}}[OK] Paquete VSIX guardado en: $SHARE_DIR/{vsix_name}${{NC}}"

    if which code >/dev/null 2>&1; then
        echo -e "${{CYAN}}[...] Instalando extensión oficial en Visual Studio Code...${{NC}}"
        code --install-extension "$VSIX_FILE" --force >/dev/null 2>&1 && echo -e "${{GREEN}}[OK] Extensión de VS Code registrada exitosamente.${{NC}}" || true
    fi
    if which cursor >/dev/null 2>&1; then
        echo -e "${{CYAN}}[...] Instalando extensión oficial en Cursor...${{NC}}"
        cursor --install-extension "$VSIX_FILE" --force >/dev/null 2>&1 && echo -e "${{GREEN}}[OK] Extensión de Cursor registrada exitosamente.${{NC}}" || true
    fi
    if which codium >/dev/null 2>&1; then
        echo -e "${{CYAN}}[...] Instalando extensión oficial en VSCodium...${{NC}}"
        codium --install-extension "$VSIX_FILE" --force >/dev/null 2>&1 && echo -e "${{GREEN}}[OK] Extensión de VSCodium registrada exitosamente.${{NC}}" || true
    fi
fi

echo -e "\\n${{GREEN}}=====================================================${{NC}}"
echo -e "${{GREEN}}       ¡UCABA v${{VERSION}} INSTALADO CORRECTAMENTE!        ${{NC}}"
echo -e "${{GREEN}}=====================================================${{NC}}"
echo -e "Prueba el compilador ejecutando:"
echo -e "  ${{CYAN}}ucaba --version${{NC}}"
echo -e "  ${{CYAN}}ucaba --help${{NC}}"

case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *)
    echo -e "\\n${{RED}}[AVISO]${{NC}} Para usar 'ucaba' desde cualquier terminal, añade $BIN_DIR a tu PATH:"
    echo -e "  echo 'export PATH=\"$BIN_DIR:\\$PATH\"' >> ~/.bashrc"
    echo -e "  source ~/.bashrc"
    ;;
esac
"""


def generate_uninstall_sh() -> str:
    return """#!/bin/bash
# ==============================================================================
# Script de Desinstalación de UCABA para Linux
# ==============================================================================
set -e

RED='\\033[0;31m'
GREEN='\\033[0;32m'
MAGENTA='\\033[0;35m'
NC='\\033[0m'

echo -e "${MAGENTA}=====================================================${NC}"
echo -e "${MAGENTA}       DESINSTALADOR DE UCABA PARA GNU/LINUX         ${NC}"
echo -e "${MAGENTA}=====================================================${NC}"

if [ "$(id -u)" -eq 0 ]; then
    INSTALL_PREFIX="/usr/local"
    APPS_DIR="/usr/share/applications"
    ICONS_DIR="/usr/share/icons/hicolor/256x256/apps"
    MIME_DIR="/usr/share/mime/packages"
else
    INSTALL_PREFIX="$HOME/.local"
    APPS_DIR="$INSTALL_PREFIX/share/applications"
    ICONS_DIR="$INSTALL_PREFIX/share/icons/hicolor/256x256/apps"
    MIME_DIR="$INSTALL_PREFIX/share/mime/packages"
fi

BIN_FILE="$INSTALL_PREFIX/bin/ucaba"
SHARE_DIR="$INSTALL_PREFIX/share/ucaba"

# Eliminar binario
if [ -f "$BIN_FILE" ]; then
    rm -f "$BIN_FILE"
    echo -e "${GREEN}[OK] Eliminado binario: $BIN_FILE${NC}"
fi

# Eliminar directorio compartido
if [ -d "$SHARE_DIR" ]; then
    rm -rf "$SHARE_DIR"
    echo -e "${GREEN}[OK] Eliminado: $SHARE_DIR${NC}"
fi

# Eliminar Desktop Entry
if [ -f "$APPS_DIR/ucaba.desktop" ]; then
    rm -f "$APPS_DIR/ucaba.desktop"
    echo -e "${GREEN}[OK] Eliminado: $APPS_DIR/ucaba.desktop${NC}"
    if which update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$APPS_DIR" 2>/dev/null || true
    fi
fi

# Eliminar icono
if [ -f "$ICONS_DIR/ucaba.png" ]; then
    rm -f "$ICONS_DIR/ucaba.png"
    echo -e "${GREEN}[OK] Eliminado: $ICONS_DIR/ucaba.png${NC}"
fi

# Eliminar MIME
if [ -f "$MIME_DIR/ucaba.xml" ]; then
    rm -f "$MIME_DIR/ucaba.xml"
    echo -e "${GREEN}[OK] Eliminado tipo MIME: $MIME_DIR/ucaba.xml${NC}"
    if which update-mime-database >/dev/null 2>&1; then
        update-mime-database "$(dirname "$MIME_DIR")" 2>/dev/null || true
    fi
fi

# Desinstalar extensión de VS Code si se encuentra
if which code >/dev/null 2>&1; then
    code --uninstall-extension ucaba.ucaba-language-support 2>/dev/null || true
fi

echo -e "\\n${GREEN}[OK] UCABA ha sido desinstalado completamente de tu sistema.${NC}"
"""


def generate_readme(version: str) -> str:
    return f"""# UCABA v{version} para GNU/Linux

**UCABA** es un lenguaje de pseudocódigo en español fuertemente tipado diseñado para el aprendizaje moderno de algoritmos y estructuras de datos.

## Instalación Rápida

Para instalar UCABA en tu sistema (en modo usuario `~/.local` o como root con `sudo`):

```bash
chmod +x install.sh
./install.sh
```

Si deseas instalar para todos los usuarios del sistema:
```bash
sudo ./install.sh
```

## Desinstalación

```bash
chmod +x uninstall.sh
./uninstall.sh
```

## Comandos Principales

- Ejecutar un archivo:
  ```bash
  ucaba mi_algoritmo.ucaba
  ```
- Medir tiempo de ejecución:
  ```bash
  ucaba mi_algoritmo.ucaba --time
  ucaba mi_algoritmo.ucaba --time-full
  ```
- Chequear sintaxis y tipos sin ejecutar:
  ```bash
  ucaba check mi_algoritmo.ucaba
  ```

Visita el repositorio oficial en GitHub: https://github.com/caidevOficial/UCABA_Lang
"""


def generate_control(version: str, installed_size_kb: int) -> str:
    return f"""Package: ucaba
Version: {version}
Section: devel
Priority: optional
Architecture: amd64
Installed-Size: {installed_size_kb}
Maintainer: Facu Falcone <a.facundo.falcone@gmail.com>
Homepage: https://github.com/caidevOficial/UCABA_Lang
Description: Intérprete y runtime de pseudocódigo en español fuertemente tipado
 UCABA es un lenguaje de programación de pseudocódigo en español,
 fuertemente tipado con chequeo estático, soporte de estructuras de datos
 (vectores, matrices, estructuras, punteros nulos), funciones recursivas
 de alto rendimiento y extensión oficial para VS Code / Cursor.
"""


def generate_postinst(version: str, vsix_name: str) -> str:
    return f"""#!/bin/sh
set -e

# Actualizar base de datos de tipos MIME
if which update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi

# Actualizar base de datos de entradas de escritorio
if which update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi

# Intentar instalar la extensión de VS Code si existe en el entorno
VSIX_PATH="/usr/share/ucaba/{vsix_name}"
if [ -f "$VSIX_PATH" ]; then
    if which code >/dev/null 2>&1; then
        code --install-extension "$VSIX_PATH" --force >/dev/null 2>&1 || true
    fi
    if which cursor >/dev/null 2>&1; then
        cursor --install-extension "$VSIX_PATH" --force >/dev/null 2>&1 || true
    fi
fi

exit 0
"""


def generate_postrm() -> str:
    return """#!/bin/sh
set -e

if which update-mime-database >/dev/null 2>&1; then
    update-mime-database /usr/share/mime || true
fi

if which update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications || true
fi

exit 0
"""


def build_ar_header(name: str, size: int, mode: int = 0o100644, mtime: int = 0, uid: int = 0, gid: int = 0) -> bytes:
    """Construye un encabezado de 60 bytes en formato ar tradicional para Debian."""
    header = (
        f"{name:<16}"
        f"{mtime:<12}"
        f"{uid:<6}"
        f"{gid:<6}"
        f"{oct(mode)[2:]:<8}"
        f"{size:<10}"
        "`\n"
    )
    return header.encode("ascii")


def create_tar_gz_bytes(entries: list) -> bytes:
    """
    Empaqueta una lista de tuplas (rel_path, data_bytes, mode, is_dir)
    en memoria y retorna el flujo de bytes gzip comprimido con metadatos normalizados.
    """
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for rel_path, data, mode, is_dir in entries:
            ti = tarfile.TarInfo(name=rel_path)
            ti.uname = "root"
            ti.gname = "root"
            ti.uid = 0
            ti.gid = 0
            ti.mtime = 0
            if is_dir:
                ti.type = tarfile.DIRTYPE
                ti.mode = mode or 0o755
                tar.addfile(ti)
            else:
                ti.type = tarfile.REGTYPE
                ti.size = len(data)
                ti.mode = mode or 0o644
                tar.addfile(ti, io.BytesIO(data))
    return buf.getvalue()


def build_tarball(binary_path: str, vsix_path: str, icon_path: str, output_path: str, version: str):
    """Genera el paquete tarball standalone ucaba-<version>-linux-x64.tar.gz."""
    print(f"\n[TARBALL] Creando archivo tarball portable: {output_path}")

    vsix_name = os.path.basename(vsix_path) if vsix_path else f"ucaba-language-support-{version}.vsix"

    with tarfile.open(output_path, "w:gz") as tar:
        prefix = f"ucaba-{version}-linux-x64"

        # Carpeta raíz
        dir_ti = tarfile.TarInfo(name=prefix)
        dir_ti.type = tarfile.DIRTYPE
        dir_ti.mode = 0o755
        tar.addfile(dir_ti)

        # 1. Binario ejecutable
        with open(binary_path, "rb") as f:
            bin_data = f.read()
        bin_ti = tarfile.TarInfo(name=f"{prefix}/ucaba")
        bin_ti.size = len(bin_data)
        bin_ti.mode = 0o755
        tar.addfile(bin_ti, io.BytesIO(bin_data))

        # 2. Scripts
        install_data = generate_install_sh(version, vsix_name).encode("utf-8")
        inst_ti = tarfile.TarInfo(name=f"{prefix}/install.sh")
        inst_ti.size = len(install_data)
        inst_ti.mode = 0o755
        tar.addfile(inst_ti, io.BytesIO(install_data))

        uninstall_data = generate_uninstall_sh().encode("utf-8")
        uninst_ti = tarfile.TarInfo(name=f"{prefix}/uninstall.sh")
        uninst_ti.size = len(uninstall_data)
        uninst_ti.mode = 0o755
        tar.addfile(uninst_ti, io.BytesIO(uninstall_data))

        # 3. Archivos de integración
        desktop_data = generate_desktop_entry().encode("utf-8")
        desk_ti = tarfile.TarInfo(name=f"{prefix}/ucaba.desktop")
        desk_ti.size = len(desktop_data)
        desk_ti.mode = 0o644
        tar.addfile(desk_ti, io.BytesIO(desktop_data))

        mime_data = generate_mime_xml().encode("utf-8")
        mime_ti = tarfile.TarInfo(name=f"{prefix}/ucaba.xml")
        mime_ti.size = len(mime_data)
        mime_ti.mode = 0o644
        tar.addfile(mime_ti, io.BytesIO(mime_data))

        readme_data = generate_readme(version).encode("utf-8")
        readme_ti = tarfile.TarInfo(name=f"{prefix}/README.md")
        readme_ti.size = len(readme_data)
        readme_ti.mode = 0o644
        tar.addfile(readme_ti, io.BytesIO(readme_data))

        # 4. Icono
        if os.path.exists(icon_path):
            with open(icon_path, "rb") as f:
                icon_data = f.read()
            icon_ti = tarfile.TarInfo(name=f"{prefix}/ucaba_icon.png")
            icon_ti.size = len(icon_data)
            icon_ti.mode = 0o644
            tar.addfile(icon_ti, io.BytesIO(icon_data))

        # 5. VSIX
        if os.path.exists(vsix_path):
            with open(vsix_path, "rb") as f:
                vsix_data = f.read()
            vsix_ti = tarfile.TarInfo(name=f"{prefix}/{vsix_name}")
            vsix_ti.size = len(vsix_data)
            vsix_ti.mode = 0o644
            tar.addfile(vsix_ti, io.BytesIO(vsix_data))

        # 6. LICENSE
        lic_path = os.path.join(REPO_ROOT, "LICENSE")
        if os.path.exists(lic_path):
            with open(lic_path, "rb") as f:
                lic_data = f.read()
            lic_ti = tarfile.TarInfo(name=f"{prefix}/LICENSE")
            lic_ti.size = len(lic_data)
            lic_ti.mode = 0o644
            tar.addfile(lic_ti, io.BytesIO(lic_data))

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f" [OK] Tarball generado exitosamente ({size_mb:.2f} MB)")


def build_deb(binary_path: str, vsix_path: str, icon_path: str, output_path: str, version: str):
    """
    Genera el paquete Debian nativo ucaba_<version>_amd64.deb de manera pura en Python
    o mediante dpkg-deb si está disponible en el entorno del sistema.
    """
    print(f"\n[DEB] Creando paquete Debian / Ubuntu: {output_path}")

    vsix_name = os.path.basename(vsix_path) if vsix_path else f"ucaba-language-support-{version}.vsix"

    # Preparar datos de archivos
    with open(binary_path, "rb") as f:
        bin_data = f.read()

    icon_data = b""
    if os.path.exists(icon_path):
        with open(icon_path, "rb") as f:
            icon_data = f.read()

    vsix_data = b""
    if os.path.exists(vsix_path):
        with open(vsix_path, "rb") as f:
            vsix_data = f.read()

    lic_data = b""
    lic_path = os.path.join(REPO_ROOT, "LICENSE")
    if os.path.exists(lic_path):
        with open(lic_path, "rb") as f:
            lic_data = f.read()

    readme_data = generate_readme(version).encode("utf-8")
    desktop_data = generate_desktop_entry().encode("utf-8")
    mime_data = generate_mime_xml().encode("utf-8")

    # Si dpkg-deb está en el sistema, podemos armar la estructura en un directorio temporal y llamar dpkg-deb
    dpkg_tool = shutil.which("dpkg-deb")
    if dpkg_tool:
        print(f" [INFO] dpkg-deb detectado ({dpkg_tool}), compilando vía herramienta canónica de Debian...")
        temp_deb_dir = os.path.join(os.path.dirname(output_path), "ucaba_deb_tmp")
        if os.path.exists(temp_deb_dir):
            shutil.rmtree(temp_deb_dir, ignore_errors=True)

        os.makedirs(os.path.join(temp_deb_dir, "DEBIAN"), exist_ok=True)
        os.makedirs(os.path.join(temp_deb_dir, "usr", "bin"), exist_ok=True)
        os.makedirs(os.path.join(temp_deb_dir, "usr", "share", "ucaba"), exist_ok=True)
        os.makedirs(os.path.join(temp_deb_dir, "usr", "share", "applications"), exist_ok=True)
        os.makedirs(os.path.join(temp_deb_dir, "usr", "share", "icons", "hicolor", "256x256", "apps"), exist_ok=True)
        os.makedirs(os.path.join(temp_deb_dir, "usr", "share", "mime", "packages"), exist_ok=True)
        os.makedirs(os.path.join(temp_deb_dir, "usr", "share", "doc", "ucaba"), exist_ok=True)

        # Copiar archivos
        with open(os.path.join(temp_deb_dir, "usr", "bin", "ucaba"), "wb") as f:
            f.write(bin_data)
        os.chmod(os.path.join(temp_deb_dir, "usr", "bin", "ucaba"), 0o755)

        if vsix_data:
            with open(os.path.join(temp_deb_dir, "usr", "share", "ucaba", vsix_name), "wb") as f:
                f.write(vsix_data)

        if icon_data:
            with open(os.path.join(temp_deb_dir, "usr", "share", "icons", "hicolor", "256x256", "apps", "ucaba.png"), "wb") as f:
                f.write(icon_data)

        with open(os.path.join(temp_deb_dir, "usr", "share", "applications", "ucaba.desktop"), "wb") as f:
            f.write(desktop_data)

        with open(os.path.join(temp_deb_dir, "usr", "share", "mime", "packages", "ucaba.xml"), "wb") as f:
            f.write(mime_data)

        with open(os.path.join(temp_deb_dir, "usr", "share", "doc", "ucaba", "README.md"), "wb") as f:
            f.write(readme_data)

        if lic_data:
            with open(os.path.join(temp_deb_dir, "usr", "share", "doc", "ucaba", "copyright"), "wb") as f:
                f.write(lic_data)

        installed_kb = max(1, len(bin_data) + len(vsix_data) + len(icon_data)) // 1024

        # Scripts de control
        with open(os.path.join(temp_deb_dir, "DEBIAN", "control"), "w", encoding="utf-8") as f:
            f.write(generate_control(version, installed_kb))

        postinst_file = os.path.join(temp_deb_dir, "DEBIAN", "postinst")
        with open(postinst_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(generate_postinst(version, vsix_name))
        os.chmod(postinst_file, 0o755)

        postrm_file = os.path.join(temp_deb_dir, "DEBIAN", "postrm")
        with open(postrm_file, "w", encoding="utf-8", newline="\n") as f:
            f.write(generate_postrm())
        os.chmod(postrm_file, 0o755)

        res = subprocess.run([dpkg_tool, "--build", temp_deb_dir, output_path], capture_output=True, text=True)
        shutil.rmtree(temp_deb_dir, ignore_errors=True)
        if res.returncode != 0:
            raise RuntimeError(f"Error al ejecutar dpkg-deb: {res.stderr}")

    else:
        # Ensamblador puro en Python del formato estándar Debian 'ar'
        print(" [INFO] Ensamblando formato estándar Debian 'ar' en modo multiplataforma puro...")

        # 1. Construir data.tar.gz
        data_entries = [
            ("./usr", b"", 0o755, True),
            ("./usr/bin", b"", 0o755, True),
            ("./usr/bin/ucaba", bin_data, 0o755, False),
            ("./usr/share", b"", 0o755, True),
            ("./usr/share/ucaba", b"", 0o755, True),
            (f"./usr/share/ucaba/{vsix_name}", vsix_data, 0o644, False) if vsix_data else None,
            ("./usr/share/applications", b"", 0o755, True),
            ("./usr/share/applications/ucaba.desktop", desktop_data, 0o644, False),
            ("./usr/share/icons", b"", 0o755, True),
            ("./usr/share/icons/hicolor", b"", 0o755, True),
            ("./usr/share/icons/hicolor/256x256", b"", 0o755, True),
            ("./usr/share/icons/hicolor/256x256/apps", b"", 0o755, True),
            ("./usr/share/icons/hicolor/256x256/apps/ucaba.png", icon_data, 0o644, False) if icon_data else None,
            ("./usr/share/mime", b"", 0o755, True),
            ("./usr/share/mime/packages", b"", 0o755, True),
            ("./usr/share/mime/packages/ucaba.xml", mime_data, 0o644, False),
            ("./usr/share/doc", b"", 0o755, True),
            ("./usr/share/doc/ucaba", b"", 0o755, True),
            ("./usr/share/doc/ucaba/README.md", readme_data, 0o644, False),
            ("./usr/share/doc/ucaba/copyright", lic_data, 0o644, False) if lic_data else None,
        ]
        data_entries = [e for e in data_entries if e is not None]
        data_tar_gz = create_tar_gz_bytes(data_entries)

        installed_kb = max(1, len(bin_data) + len(vsix_data) + len(icon_data)) // 1024

        # 2. Construir control.tar.gz
        control_str = generate_control(version, installed_kb)
        postinst_str = generate_postinst(version, vsix_name)
        postrm_str = generate_postrm()

        control_entries = [
            ("./control", control_str.encode("utf-8"), 0o644, False),
            ("./postinst", postinst_str.encode("utf-8"), 0o755, False),
            ("./postrm", postrm_str.encode("utf-8"), 0o755, False)
        ]
        control_tar_gz = create_tar_gz_bytes(control_entries)

        # 3. Ensamblar contenedor 'ar' (debian-binary, control.tar.gz, data.tar.gz)
        debian_binary = b"2.0\n"

        with open(output_path, "wb") as deb:
            deb.write(b"!<arch>\n")

            # Entrada 1: debian-binary
            deb.write(build_ar_header("debian-binary", len(debian_binary)))
            deb.write(debian_binary)
            if len(debian_binary) % 2 != 0:
                deb.write(b"\n")

            # Entrada 2: control.tar.gz
            deb.write(build_ar_header("control.tar.gz", len(control_tar_gz)))
            deb.write(control_tar_gz)
            if len(control_tar_gz) % 2 != 0:
                deb.write(b"\n")

            # Entrada 3: data.tar.gz
            deb.write(build_ar_header("data.tar.gz", len(data_tar_gz)))
            deb.write(data_tar_gz)
            if len(data_tar_gz) % 2 != 0:
                deb.write(b"\n")

    size_mb = os.path.getsize(output_path) / (1024 * 1024)
    print(f" [OK] Paquete Debian generado exitosamente ({size_mb:.2f} MB)")


def main():
    parser = argparse.ArgumentParser(description="Empaquetador de UCABA para Linux (.deb y .tar.gz)")
    parser.add_argument("--binary", default=None, help="Ruta al binario compilado ucaba para Linux")
    parser.add_argument("--vsix", default=None, help="Ruta al archivo .vsix de la extensión")
    parser.add_argument("--output-dir", default=os.path.join(REPO_ROOT, "dist"), help="Directorio de salida para los paquetes")
    parser.add_argument("--compile", action="store_true", help="Compilar binario de Linux con PyInstaller antes de empaquetar")
    parser.add_argument("--mock-binary", action="store_true", help="Usar un binario stub para pruebas en entornos cruzados")

    args = parser.parse_args()

    version = get_version()
    os.makedirs(args.output_dir, exist_ok=True)

    print("==================================================")
    print(f"  CREACIÓN DE PAQUETES LINUX PARA UCABA v{version}")
    print("==================================================")

    # 1. Obtener o compilar binario
    binary_path = args.binary
    if args.compile:
        print("\n--- Compilando binario nativo Linux con PyInstaller ---")
        cmd = [
            sys.executable, "-m", "PyInstaller",
            "--name", "ucaba",
            "--onefile",
            "--clean",
            "--paths", ".",
            os.path.join("pseudocode", "cli.py")
        ]
        res = subprocess.run(cmd, cwd=REPO_ROOT)
        if res.returncode != 0:
            raise RuntimeError(f"Error al compilar con PyInstaller: {res.returncode}")
        binary_path = os.path.join(REPO_ROOT, "dist", "ucaba")

    if not binary_path:
        default_candidate = os.path.join(REPO_ROOT, "dist", "ucaba")
        if os.path.exists(default_candidate):
            binary_path = default_candidate
        elif args.mock_binary:
            binary_path = os.path.join(REPO_ROOT, "dist", "ucaba_stub")
            with open(binary_path, "wb") as f:
                f.write(b"#!/bin/sh\necho 'UCABA Stub Test Binary'\n")
            print(f" [MOCK] Creado binario stub para pruebas: {binary_path}")
        else:
            raise FileNotFoundError(
                f"No se encontró el binario 'ucaba' para Linux en {default_candidate}.\n"
                "Usa --compile si estás en Linux o especifica la ruta con --binary <ruta>."
            )

    # 2. Localizar VSIX e icono
    vsix_path = args.vsix or find_latest_vsix()
    icon_path = os.path.join(REPO_ROOT, "ucaba_icon.png")
    if not os.path.exists(icon_path):
        icon_path = os.path.join(REPO_ROOT, "extension-vscode", "icon.png")

    print(f"Versión:  v{version}")
    print(f"Binario:  {binary_path}")
    print(f"VSIX:     {vsix_path}")
    print(f"Icono:    {icon_path}")

    # 3. Construir Tarball
    tarball_name = f"ucaba-{version}-linux-x64.tar.gz"
    tarball_path = os.path.join(args.output_dir, tarball_name)
    build_tarball(binary_path, vsix_path, icon_path, tarball_path, version)

    # 4. Construir Paquete .deb
    deb_name = f"ucaba_{version}_amd64.deb"
    deb_path = os.path.join(args.output_dir, deb_name)
    build_deb(binary_path, vsix_path, icon_path, deb_path, version)

    print("\n==================================================")
    print("  PAQUETES LINUX GENERADOS CON ÉXITO")
    print("==================================================")
    print(f"1. Tarball: {tarball_path} ({get_sha256(tarball_path)})")
    print(f"2. Debian:  {deb_path} ({get_sha256(deb_path)})")


if __name__ == "__main__":
    main()
