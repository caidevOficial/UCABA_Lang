import os
import io
import struct
import numpy as np
from PIL import Image
from scipy.ndimage import label

REPO_ROOT = r"e:/Python_d/UCABA_Lang"
SRC_MASCOT = r"C:/Users/Admin/.gemini/antigravity/brain/0b1633a0-3f7b-42f7-a49e-d01ef27ae5f4/ucaba_jaguar_mascot_logo_1793322656746.jpg"

def create_transparent_mascot(src_path):
    print(f"[1/5] Cargando imagen fuente: {src_path}")
    img = Image.open(src_path).convert("RGB")
    arr = np.array(img, dtype=float)
    H, W, _ = arr.shape
    
    # Estimación bilineal de fondo suave a partir de las esquinas
    y, x = np.mgrid[0:H, 0:W]
    u = x / (W - 1)
    v = y / (H - 1)
    c00, c10, c01, c11 = arr[0, 0], arr[0, -1], arr[-1, 0], arr[-1, -1]
    bg_est = (1-u)[:, :, None] * (1-v)[:, :, None] * c00 + \
             u[:, :, None] * (1-v)[:, :, None] * c10 + \
             (1-u)[:, :, None] * v[:, :, None] * c01 + \
             u[:, :, None] * v[:, :, None] * c11

    diff = np.sqrt(np.sum((arr - bg_est)**2, axis=2))
    
    # Identificar fondo exterior conectado a los bordes
    is_bg_candidate = diff < 22
    lbl, num = label(is_bg_candidate)
    border_lbls = set(np.unique(np.concatenate([lbl[0, :], lbl[-1, :], lbl[:, 0], lbl[:, -1]])))
    border_lbls.discard(0)
    is_true_bg = np.isin(lbl, list(border_lbls))
    
    # Transición de alfa suave para evitar bordes dentados
    alpha = np.clip((diff - 16.0) / (28.0 - 16.0), 0.0, 1.0)
    alpha[is_true_bg & (diff < 16)] = 0.0
    alpha[~is_true_bg] = 1.0
    
    # Centrar levemente el isotipo en el lienzo
    is_fg = ~is_true_bg
    fg_y, fg_x = np.where(is_fg)
    center_x = int(np.mean(fg_x))
    center_y = int(np.mean(fg_y))
    shift_x = (W // 2) - center_x
    shift_y = (H // 2) - center_y
    
    rgba = np.dstack([arr, alpha * 255.0]).astype(np.uint8)
    mascot_img = Image.fromarray(rgba, "RGBA")
    
    # Desplazar para centrado perfecto
    if abs(shift_x) > 1 or abs(shift_y) > 1:
        canvas = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        canvas.paste(mascot_img, (shift_x, shift_y), mascot_img)
        mascot_img = canvas
        
    return mascot_img

def build_windows_ico(img_rgba, output_path):
    resolutions = [256, 128, 64, 48, 32, 24, 16]
    data_blobs = []
    
    for size in resolutions:
        resized = img_rgba.resize((size, size), Image.Resampling.LANCZOS)
        if size == 256:
            # Entrada 0: PNG comprimido
            buf = io.BytesIO()
            resized.save(buf, format="PNG")
            blob = buf.getvalue()
        else:
            # Entradas secundarias: DIB 32-bit sin comprimir (Section 4 SKILL.md)
            bi_width = size
            bi_height = 2 * size
            pixel_data_size = size * size * 4
            row_mask_bytes = ((size + 31) // 32) * 4
            and_mask_size = row_mask_bytes * size
            
            header = struct.pack(
                "<IIIHHIIIIII",
                40,             # biSize
                bi_width,       # biWidth
                bi_height,      # biHeight
                1,              # biPlanes
                32,             # biBitCount
                0,              # biCompression
                pixel_data_size,# biSizeImage
                0, 0, 0, 0      # XPels, YPels, ClrUsed, ClrImp
            )
            arr = np.array(resized)
            arr_flipped = np.flipud(arr)
            bgra = arr_flipped[:, :, [2, 1, 0, 3]].tobytes()
            and_mask = b"\x00" * and_mask_size
            blob = header + bgra + and_mask
            
        data_blobs.append(blob)
        
    num_images = len(resolutions)
    icondir = struct.pack("<HHH", 0, 1, num_images)
    current_offset = 6 + 16 * num_images
    direntries = []
    for i, size in enumerate(resolutions):
        blob = data_blobs[i]
        b_w = size if size < 256 else 0
        b_h = size if size < 256 else 0
        direntry = struct.pack("<BBBBHHII", b_w, b_h, 0, 0, 1, 32, len(blob), current_offset)
        direntries.append(direntry)
        current_offset += len(blob)
        
    with open(output_path, "wb") as f:
        f.write(icondir)
        for de in direntries:
            f.write(de)
        for blob in data_blobs:
            f.write(blob)
            
    print(f" [OK] Generado icono multi-resolución: {output_path} ({os.path.getsize(output_path)} bytes)")

def main():
    mascot_img = create_transparent_mascot(SRC_MASCOT)
    
    # 1. ucaba_icon.png (1024x1024 Ultra-HD Master para README, docs y branding)
    path_icon = os.path.join(REPO_ROOT, "ucaba_icon.png")
    mascot_img.save(path_icon, "PNG", optimize=True)
    print(f"[OK] Generado ucaba_icon.png (1024x1024 Ultra-HD, {os.path.getsize(path_icon)} bytes)")
    
    # 2. ucaba_logo_header.png (80x80 nítido para Tkinter installer_gui.py y egui header)
    path_header = os.path.join(REPO_ROOT, "ucaba_logo_header.png")
    header80 = mascot_img.resize((80, 80), Image.Resampling.LANCZOS)
    header80.save(path_header, "PNG", optimize=True)
    print(f"[OK] Generado ucaba_logo_header.png (80x80, {os.path.getsize(path_header)} bytes)")
    
    # 3. extension-vscode/icon.png (256x256 para VS Code marketplace)
    path_vscode_icon = os.path.join(REPO_ROOT, "extension-vscode", "icon.png")
    vscode256 = mascot_img.resize((256, 256), Image.Resampling.LANCZOS)
    vscode256.save(path_vscode_icon, "PNG", optimize=True)
    print(f"[OK] Generado extension-vscode/icon.png (256x256, {os.path.getsize(path_vscode_icon)} bytes)")
    
    # 4. ucaba_icon.ico y ucaba_icon_standard.ico
    path_ico = os.path.join(REPO_ROOT, "ucaba_icon.ico")
    path_ico_std = os.path.join(REPO_ROOT, "ucaba_icon_standard.ico")
    build_windows_ico(mascot_img, path_ico)
    build_windows_ico(mascot_img, path_ico_std)

if __name__ == "__main__":
    main()
