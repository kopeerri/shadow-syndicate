#!/usr/bin/env python3
"""Generate stickers with MAGENTA chroma key, strip to transparent PNG."""
import urllib.request, json, base64, os, re
from pathlib import Path
from PIL import Image
import numpy as np

# Read key
with open(r'C:\Users\nostr\Desktop\claude\.env', 'r') as f:
    for line in f:
        if 'OPENROUTER' in line and '=' in line:
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
            break

BASE = "https://openrouter.ai/api/v1/chat/completions"
OUT_DIR = Path(r'C:\Users\nostr\Desktop\Night Raiders\discord-bot\assets\emojis')
OUT_DIR.mkdir(parents=True, exist_ok=True)

STICKERS = [
    ("sticker_shade_coin", "Minimalist sticker icon: hexagonal coin with bold dollar sign, iridescent purple to teal gradient fill, thin gold metallic hex edge. Clean vector style. Subtle glow. The icon is on a SOLID BRIGHT MAGENTA (hex #FF00FF, RGB 255 0 255) background. The background must be uniform, flat, pure magenta with no variation at all — like a green screen but magenta."),
    ("sticker_dice", "Minimalist sticker icon: single D20 dice tilted, purple body with teal numbered faces, gold edge highlights. Icon style, subtle glow. SOLID BRIGHT MAGENTA (#FF00FF) uniform flat background — like a chroma key screen."),
    ("sticker_cards", "Minimalist sticker icon: two fanned playing cards, one purple spade, one teal diamond, gold card edge accents. Clean icon style. SOLID BRIGHT MAGENTA (#FF00FF) uniform flat background."),
    ("sticker_chips", "Minimalist sticker icon: 3 stacked casino chips alternating purple, teal, gold. Edge spots visible. Clean icon. SOLID BRIGHT MAGENTA (#FF00FF) uniform flat background."),
    ("sticker_skull", "Minimalist sticker icon: angular cyberpunk skull side profile, purple and teal accents, one teal glowing eye, gold jawline. Bold clean lines. SOLID BRIGHT MAGENTA (#FF00FF) uniform flat background."),
    ("sticker_ghost", "Minimalist sticker icon: geometric hooded ghost figure, purple robe, teal glowing triangular eyes in dark hood, gold edge trim. SOLID BRIGHT MAGENTA (#FF00FF) uniform flat background."),
    ("sticker_martini", "Minimalist sticker icon: elegant martini glass, purple glass body, teal glowing liquid, gold rim and olive. SOLID BRIGHT MAGENTA (#FF00FF) uniform flat background."),
    ("sticker_crest", "Minimalist sticker icon: elongated hexagon shield crest with sharp gothic arch points, interlocking angular S-shapes in negative space. Iridescent purple to teal gradient. Thin gold metallic edge. Bold iconic style. SOLID BRIGHT MAGENTA (#FF00FF) uniform flat background."),
]

MAGENTA = np.array([255, 0, 255])

def strip_magenta(input_path, output_path, threshold=80):
    """Replace magenta pixels with transparency using distance threshold."""
    img = Image.open(input_path).convert("RGBA")
    arr = np.array(img, dtype=np.float32)
    
    # Color distance from pure magenta
    dist = np.sqrt(np.sum((arr[:,:,:3] - MAGENTA) ** 2, axis=2))
    
    # Linear alpha: 0 at distance 0 (pure magenta), 255 at distance >= threshold
    alpha = np.clip(dist / threshold * 255, 0, 255).astype(np.uint8)
    
    arr[:,:,3] = alpha
    result = Image.fromarray(arr.astype(np.uint8), "RGBA")
    result.save(output_path, "PNG")
    
    # Verify
    result2 = Image.open(output_path)
    alpha_data = list(result2.getchannel("A").getdata())
    fully_clear = sum(1 for a in alpha_data if a == 0)
    pct = 100 * fully_clear / len(alpha_data)
    return pct

for i, (name, prompt) in enumerate(STICKERS):
    print(f"[{i+1}/{len(STICKERS)}] {name}...", flush=True)
    
    data = json.dumps({
        "model": "google/gemini-2.5-flash-image",
        "modalities": ["image", "text"],
        "messages": [{"role": "user", "content": prompt}]
    }).encode()
    
    req = urllib.request.Request(BASE, data=data,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})
    
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            body = resp.read().decode()
            d = json.loads(body)
            msg = d["choices"][0]["message"]
            imgs = msg.get("images", [])
            if not imgs:
                print(f"  FAIL: no images")
                continue
            img = imgs[0]
            url = img["image_url"]["url"]
            if "base64," in url:
                img_data = base64.b64decode(re.split(r"base64,", url, 1)[1])
                
                raw_path = OUT_DIR / f"{name}_raw.png"
                with open(raw_path, "wb") as f:
                    f.write(img_data)
                
                # Check background color
                check = Image.open(raw_path).convert("RGB")
                check_arr = np.array(check)
                corner = check_arr[0:10, 0:10].mean(axis=(0,1))
                print(f"  bg=({corner[0]:.0f},{corner[1]:.0f},{corner[2]:.0f})", end=" ", flush=True)
                
                final_path = OUT_DIR / f"{name}.png"
                pct = strip_magenta(raw_path, final_path)
                
                raw_path.unlink()
                print(f"transparent={pct:.0f}%")
            else:
                print(f"  Unknown format: {url[:60]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nALL DONE")
