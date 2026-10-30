"""
Script para generar todos los formatos de iconos necesarios para UCABA:
- extension-vscode/icons/ucaba-file.svg
- extension-vscode/icons/ucaba-file.png
- extension-vscode/icons/file.svg (icono genérico para tema UCABA)
- extension-vscode/icons/folder.svg (carpeta cerrada)
- extension-vscode/icons/folder-open.svg (carpeta abierta)
- extension-vscode/icons/folder-root.svg
- extension-vscode/icons/folder-root-open.svg
- extension-vscode/icons/python.svg
- extension-vscode/icons/rust.svg
- extension-vscode/icons/json.svg
- extension-vscode/icons/markdown.svg
- extension-vscode/icons/text.svg
"""

import os
import base64
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(REPO_ROOT, "extension-vscode", "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

# 1. Cargar icono oficial PNG (512x512)
src_png = os.path.join(REPO_ROOT, "ucaba_icon.png")
with open(src_png, "rb") as f:
    png_bytes = f.read()

b64_img = base64.b64encode(png_bytes).decode("ascii")

# SVG para el archivo UCABA
ucaba_svg_content = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="16" height="16">
  <image href="data:image/png;base64,{b64_img}" width="512" height="512" />
</svg>
'''

with open(os.path.join(ICONS_DIR, "ucaba-file.svg"), "w", encoding="utf-8") as f:
    f.write(ucaba_svg_content)

print("[OK] Generado ucaba-file.svg")

# 2. Generar PNG optimizado para 16x16, 32x32, 64x64, 128x128
im = Image.open(src_png)
im_resized = im.resize((128, 128), Image.Resampling.LANCZOS)
im_resized.save(os.path.join(ICONS_DIR, "ucaba-file.png"), "PNG")
print("[OK] Generado ucaba-file.png (128x128)")

# 3. Iconos SVG limpios y modernos para el tema de iconos oficial UCABA
file_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#94a3b8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
  <polyline points="14 2 14 8 20 8"/>
</svg>'''

folder_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="#0066ff" fill-opacity="0.25" stroke="#38bdf8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/>
</svg>'''

folder_open_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="#0066ff" fill-opacity="0.35" stroke="#38bdf8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M5 19h14a2 2 0 0 0 2-1.7l1.3-7.3a1 1 0 0 0-.9-1.2l-1.4.2H8.5L6.5 6H4a2 2 0 0 0-2 2v11a2 2 0 0 0 2 2h1"/>
</svg>'''

text_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#cbd5e1" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
  <polyline points="14 2 14 8 20 8"/>
  <line x1="16" y1="13" x2="8" y2="13"/>
  <line x1="16" y1="17" x2="8" y2="17"/>
  <line x1="10" y1="9" x2="8" y2="9"/>
</svg>'''

python_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#38bdf8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M12 2a5 5 0 0 0-5 5v2h5v1H5a5 5 0 0 0 0 10h2v-2a3 3 0 0 1 3-3h4a3 3 0 0 1 3 3v2h2a5 5 0 0 0 0-10h-2V7a5 5 0 0 0-5-5z"/>
  <circle cx="9.5" cy="5.5" r=".7" fill="#38bdf8"/>
  <circle cx="14.5" cy="18.5" r=".7" fill="#38bdf8"/>
</svg>'''

rust_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#fb923c" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <circle cx="12" cy="12" r="9"/>
  <path d="M9 8h4.5a2.5 2.5 0 0 1 0 5H9m0-5v8m0-3h4.5l2.5 3"/>
</svg>'''

json_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#facc15" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <path d="M8 3a3 3 0 0 0-3 3v3a2 2 0 0 1-2 2 2 2 0 0 1 2 2v3a3 3 0 0 0 3 3"/>
  <path d="M16 3a3 3 0 0 1 3 3v3a2 2 0 0 0 2 2 2 2 0 0 0-2 2v3a3 3 0 0 1-3 3"/>
</svg>'''

markdown_svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="#60a5fa" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
  <rect x="3" y="4" width="18" height="16" rx="2"/>
  <path d="M7 15V9l2.5 3L12 9v6m4-5v5m-2-2 2 2 2-2"/>
</svg>'''

svg_files = {
    "file.svg": file_svg,
    "folder.svg": folder_svg,
    "folder-open.svg": folder_open_svg,
    "folder-root.svg": folder_svg,
    "folder-root-open.svg": folder_open_svg,
    "text.svg": text_svg,
    "python.svg": python_svg,
    "rust.svg": rust_svg,
    "json.svg": json_svg,
    "markdown.svg": markdown_svg
}

for name, content in svg_files.items():
    with open(os.path.join(ICONS_DIR, name), "w", encoding="utf-8") as f:
        f.write(content)
    print(f"[OK] Generado {name}")

print("\n[ÉXITO] Todos los iconos SVG generados en:", ICONS_DIR)
