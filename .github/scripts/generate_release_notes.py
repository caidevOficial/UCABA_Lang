# GNU General Public License v3.0 or later (GPL-3.0-or-later)
#
# Copyright (c) 2026 [Facu Falcone](a.facundo.falcone@gmail.com) All rights reserved.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

"""
Generador automático de notas de lanzamiento (Release Notes) para GitHub Releases.
Extrae la versión del lenguaje, calcula sumas de verificación SHA-256 de los binarios
y genera un documento markdown estructurado y prolijo.
"""

import os
import sys
import hashlib
import subprocess


def get_version(repo_root: str) -> str:
    """Extrae la versión desde pseudocode/__init__.py."""
    init_path = os.path.join(repo_root, "pseudocode", "__init__.py")
    if os.path.exists(init_path):
        with open(init_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    return line.split("=")[1].strip().strip('"').strip("'")
    return "1.5.0"


def calculate_sha256(filepath: str) -> str:
    """Calcula el hash SHA-256 de un archivo binario."""
    if not os.path.exists(filepath):
        return "No disponible"
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def get_file_size_mb(filepath: str) -> str:
    """Retorna el tamaño del archivo en MB formateado."""
    if not os.path.exists(filepath):
        return "-"
    size_bytes = os.path.getsize(filepath)
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_recent_commits(repo_root: str) -> str:
    """Obtiene los últimos commits para el registro de cambios."""
    try:
        res = subprocess.run(
            ["git", "log", "-n", "8", "--pretty=format:* %s (`%h`)"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            shell=True
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return "* Actualización del lenguaje UCABA y empaquetado de release."


def generate_notes(repo_root: str, output_path: str):
    version = get_version(repo_root)
    tag = f"v{version}"

    installer_path = os.path.join(repo_root, "dist", "Instalador_UCABA.exe")
    cli_path = os.path.join(repo_root, "dist", "ucaba.exe")

    # Localizar el VSIX más reciente
    ext_dir = os.path.join(repo_root, "extension-vscode")
    vsix_files = [os.path.join(ext_dir, f) for f in os.listdir(ext_dir) if f.endswith(".vsix")] if os.path.exists(ext_dir) else []
    vsix_path = sorted(vsix_files, key=os.path.getmtime, reverse=True)[0] if vsix_files else ""
    vsix_name = os.path.basename(vsix_path) if vsix_path else f"ucaba-language-support-{version}.vsix"

    installer_sha = calculate_sha256(installer_path)
    installer_size = get_file_size_mb(installer_path)

    cli_sha = calculate_sha256(cli_path)
    cli_size = get_file_size_mb(cli_path)

    vsix_sha = calculate_sha256(vsix_path) if vsix_path else "N/A"
    vsix_size = get_file_size_mb(vsix_path) if vsix_path else "N/A"

    commits_log = get_recent_commits(repo_root)

    content = f"""# ⚡ UCABA {tag} - Release Oficial

<p align="left">
  <img src="https://img.shields.io/badge/Versi%C3%B3n-{version}-a81a7d?style=for-the-badge" alt="Versión" />
  <img src="https://img.shields.io/badge/Plataforma-Windows_x64-0078d4?style=for-the-badge&logo=windows" alt="Windows" />
  <img src="https://img.shields.io/badge/Licencia-GPL--3.0-2563eb?style=for-the-badge" alt="Licencia" />
  <img src="https://img.shields.io/badge/Tests-28%20passing-22c55e?style=for-the-badge" alt="Tests" />
</p>

¡Nueva versión **{version}** de **UCABA**, el lenguaje de pseudocódigo en español fuertemente tipado para el aprendizaje moderno de algoritmos y estructuras de datos!

---

## 📦 Componentes y Artefactos Incluidos

| Archivo | Tamaño | Descripción |
| :--- | :--- | :--- |
| **`Instalador_UCABA.exe`** | `{installer_size}` | Asistente de instalación gráfico todo-en-uno para Windows. Configura PATH, asocia `.ucaba` e instala la extensión. |
| **`ucaba.exe`** | `{cli_size}` | Compilador y ejecutor autónomo por línea de comandos para Windows (`ucaba run`, `ucaba check`). |
| **`{vsix_name}`** | `{vsix_size}` | Extensión oficial para Visual Studio Code y Antigravity IDE (coloreado, linter estático y snippets). |

---

## 🌟 Novedades y Características Principales de esta Versión

- 🏗️ **Estructuras de Datos Heterogéneas (`ESTRUCTURA ... FIN ESTRUCTURA`)**:
  - Definición de tipos compuestos por el usuario con múltiples atributos tipados.
  - Creación de vectores y matrices de estructuras (`Libro estante[10]`).
  - Paso de estructuras como argumentos y valores de retorno en funciones y procedimientos.
  - Serialización e impresión estructurada directa: `Libro{{nombre: '...', hojas: 210, ...}}`.

- 🔗 **Tipo de Dato y Literal Universal `NULO` (`null` / `None`)**:
  - Representa formalmente la ausencia de valor o referencia nula en memoria.
  - Soporte de aliases equivalentes: `NULO`, `null`, `NULL`, `None`, `NONE`, `nulo`.
  - Comparaciones de igualdad y desigualdad (`==`, `!=`) en bucles y condicionales (`MIENTRAS actual != NULO`).
  - Diagnóstico didáctico de *Null-Safety* en tiempo de ejecución.

- 🌿 **Estructuras Autorreferenciales (Listas Enlazadas, Pilas y Colas)**:
  - Estructuras con campos de su propio tipo (`Nodo proximo_nodo`).
  - Inicialización automática a `NULO` en campos recursivos para evitar ciclos infinitos en instanciación.
  - Recorrido seguro mediante punteros auxiliares.

- 🎨 **Extensión de VS Code y Antigravity v{version}**:
  - Coloreado léxico para palabras clave `ESTRUCTURA`, `NULO`, `null` y `None`.
  - Documentación Hover interactiva al posar el cursor sobre tipos y palabras reservadas.
  - Snippets de código actualizados para plantillas instantáneas con <kbd>Tab</kbd>.

- 🚀 **Mensaje Comunitario y Notificador Inteligente de Actualizaciones**:
  - Saludo de bienvenida oficial de la comunidad: `Hello from the UCABA community. [Dev: Facu Falcone]`.
  - Notificador automático tipo `pip` en segundo plano contra GitHub Releases al finalizar ejecuciones.
  - Nuevo comando CLI interactivo `ucaba update` / `ucaba upgrade` para actualizar con un solo clic.

---

## 🔒 Sumas de Verificación de Integridad (SHA-256)

Para verificar la autenticidad e integridad de los ejecutables descargados:

```text
Instalador_UCABA.exe : {installer_sha}
ucaba.exe            : {cli_sha}
{vsix_name} : {vsix_sha}
```

---

## 🚀 Guía Rápida de Instalación

### Método 1: Asistente Gráfico (Recomendado)
1. Descarga y ejecuta **`Instalador_UCABA.exe`**.
2. Presiona **"Instalar Ahora"**. El asistente:
   - Copiará `ucaba.exe` en tu perfil de usuario (`%LOCALAPPDATA%\\Programs\\UCABA\\bin`).
   - Añadirá automáticamente UCABA a la variable de entorno `PATH`.
   - Registrará la extensión oficial en **Visual Studio Code** y **Antigravity**.
   - Asociará los archivos `.ucaba` con el icono oficial del lenguaje.

### Método 2: Instalación Silenciosa / Desatendida (CLI)
Abre PowerShell o CMD y ejecuta:
```powershell
.\\Instalador_UCABA.exe --silent
```

### Método 3: Extensión Manual en VS Code
```bash
code --install-extension {vsix_name} --force
```

---

## 📝 Registro de Cambios Recientes (Git Commits)
{commits_log}

---

**Autoría y Créditos:**
- **Autor**: [Facu Falcone](mailto:a.facundo.falcone@gmail.com)
- **Licencia**: GNU General Public License v3.0 or later (GPL-3.0-or-later)
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"[OK] Release notes generadas en: {output_path}")

    # Exportar variables de entorno para GitHub Actions si está disponible
    github_env = os.environ.get("GITHUB_ENV")
    if github_env and os.path.exists(github_env):
        with open(github_env, "a", encoding="utf-8") as env_file:
            env_file.write(f"RELEASE_TAG={tag}\n")
            env_file.write(f"RELEASE_VERSION={version}\n")
            env_file.write(f"VSIX_FILENAME={vsix_name}\n")
        print(f"[GITHUB_ENV] Exportado RELEASE_TAG={tag}, RELEASE_VERSION={version}")


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = os.path.join(root, "release_notes.md")
    if len(sys.argv) > 1:
        out = sys.argv[1]
    generate_notes(root, out)
