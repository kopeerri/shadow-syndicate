#!/usr/bin/env python3
"""Generate stickers with green screen, then strip to transparent PNG."""
import urllib.request, json, base64, os, re
from pathlib import Path

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
    ("sticker_shade_coin", "Minimalist sticker icon: hexagonal coin with bold dollar sign, iridescent purple to teal gradient fill, thin gold metallic hex edge. Clean vector style. Subtle neon glow. SOLID BRIGHT GREEN (#00FF00) background."),
    ("sticker_dice", "Minimalist sticker icon: single D20 dice tilted, purple body with teal numbered faces, gold edge highlights. Icon style, subtle glow. SOLID BRIGHT GREEN (#00FF00) background."),
    ("sticker_cards", "Minimalist sticker icon: two fanned playing cards, one purple spade, one teal diamond, gold card edge accents. Clean icon style. SOLID BRIGHT GREEN (#00FF00) background."),
    ("sticker_chips", "Minimalist sticker icon: 3 stacked casino chips alternating purple, teal, gold. Edge spots visible. Clean icon. SOLID BRIGHT GREEN (#00FF00) background."),
    ("sticker_skull", "Minimalist sticker icon: angular cyberpunk skull side profile, purple and teal accents, one teal glowing eye, gold jawline. Bold clean lines. SOLID BRIGHT GREEN (#00FF00) background."),
    ("sticker_ghost", "Minimalist sticker icon: geometric hooded ghost figure, purple robe, teal glowing triangular eyes in dark hood, gold edge trim. SOLID BRIGHT GREEN (#00FF00) background."),
    ("sticker_martini", "Minimalist sticker icon: elegant martini glass, purple glass body, teal glowing liquid, gold rim and olive. SOLID BRIGHT GREEN (#00FF00) background."),
    ("sticker_crest", "Minimalist sticker icon: elongated hexagon shield crest with sharp gothic arch points, interlocking angular S-shapes in negative space. Iridescent purple to teal gradient. Thin gold metallic edge. Bold iconic style. SOLID BRIGHT GREEN (#00FF00) background."),
]

GREEN = (0, 255, 0)
TOLERANCE = 80  # how close to pure green counts as background

def strip_green(input_path, output_path):
    """Replace solid green pixels with transparency."""
    from PIL import Image
    import numpy as np
    
    img = Image.open(input_path).convert("RGBA")
    arr = np.array(img)
    
    # Find pixels that are close to pure green
    r, g, b, a = arr[:,:,0], arr[:,:,1], arr[:,:,2], arr[:,:,3]
    
    # A pixel is "green" if green channel dominates heavily
    green_mask = (g > 200) & (r < g * 0.5) & (b < g * 0.5)
    
    # Set alpha to 0 for green pixels
    a[green_mask] = 0
    
    # Also apply a soft edge: pixels near green get partial transparency
    # But keep it simple for now
    
    result = Image.fromarray(arr, "RGBA")
    result.save(output_path, "PNG")
    
    # Verify
    result2 = Image.open(output_path)
    if 'A' in result2.getbands():
        alpha_data = list(result2.getchannel('A').getdata())
        transparent = sum(1 for a in alpha_data if a == 0)
        pct = 100 * transparent / len(alpha_data)
        return pct
    return 0

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
                
                # Save raw version
                raw_path = OUT_DIR / f"{name}_raw.png"
                with open(raw_path, "wb") as f:
                    f.write(img_data)
                
                # Strip green screen
                final_path = OUT_DIR / f"{name}.png"
                pct = strip_green(raw_path, final_path)
                
                # Clean up raw
                raw_path.unlink()
                
                print(f"  OK ({len(img_data)//1024}KB) transparent={pct:.0f}% -> {final_path}")
            else:
                print(f"  Unknown format: {url[:60]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nALL DONE")
