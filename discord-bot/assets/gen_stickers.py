#!/usr/bin/env python3
"""Generate transparent-background sticker PNGs for Shadow Syndicate."""
import urllib.request, json, base64, os, re

# Read key from .env
with open(r'C:\Users\nostr\Desktop\claude\.env', 'r') as f:
    for line in f:
        if 'OPENROUTER' in line and '=' in line:
            parts = line.split('=', 1)
            key = parts[1].strip().strip('"').strip("'")
            break

BASE = "https://openrouter.ai/api/v1/chat/completions"
OUT_DIR = os.path.dirname(os.path.abspath(__file__)) + "/emojis"
os.makedirs(OUT_DIR, exist_ok=True)

STICKERS = [
    ("sticker_shade_coin", "Minimalist sticker icon: hexagonal coin with bold dollar sign, iridescent purple to teal gradient fill, thin gold metallic hex edge. TRANSPARENT PNG background with alpha channel. No filled background behind the icon. Just the floating icon. Clean vector style. Subtle neon glow for dark mode visibility."),
    ("sticker_dice", "Minimalist sticker icon: single D20 dice tilted, purple body with teal numbered faces, gold edge highlights. TRANSPARENT PNG background. Icon style, subtle glow."),
    ("sticker_cards", "Minimalist sticker icon: two fanned playing cards, one purple spade, one teal diamond, gold card edge accents. TRANSPARENT PNG background. Clean icon style."),
    ("sticker_chips", "Minimalist sticker icon: 3 stacked casino chips alternating purple, teal, gold from top to bottom. Edge spots visible. TRANSPARENT PNG background. Clean icon."),
    ("sticker_skull", "Minimalist sticker icon: angular cyberpunk skull side profile, purple and teal accents, one teal glowing eye, gold jawline trim. TRANSPARENT PNG background. Bold clean lines."),
    ("sticker_ghost", "Minimalist sticker icon: geometric hooded ghost figure, purple robe, teal glowing triangular eyes in dark hood, gold edge trim. TRANSPARENT PNG background."),
    ("sticker_martini", "Minimalist sticker icon: elegant martini glass, purple glass body, teal glowing liquid inside, gold rim and olive on toothpick. TRANSPARENT PNG background."),
    ("sticker_crest", "Minimalist sticker icon: elongated hexagon shield crest with sharp gothic arch points at top and bottom. Inside: two interlocking angular blocky S-shapes in negative space. Iridescent purple to teal gradient surface. Thin gold metallic edge. TRANSPARENT PNG background. Bold iconic style."),
]

for i, (name, prompt) in enumerate(STICKERS):
    full_prompt = f"TRANSPARENT PNG BACKGROUND: alpha channel, no filled background behind the icon. {prompt}"
    
    print(f"[{i+1}/{len(STICKERS)}] {name}...", flush=True)
    
    data = json.dumps({
        "model": "google/gemini-2.5-flash-image",
        "modalities": ["image", "text"],
        "messages": [{"role": "user", "content": full_prompt}]
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
                path = os.path.join(OUT_DIR, f"{name}.png")
                with open(path, "wb") as f:
                    f.write(img_data)
                print(f"  OK ({len(img_data)//1024}KB) -> {path}")
            else:
                print(f"  Unknown format: {url[:60]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nALL DONE")
