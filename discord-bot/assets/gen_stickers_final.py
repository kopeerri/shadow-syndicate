#!/usr/bin/env python3
"""Step 1: Generate sticker icons (keep backgrounds, we'll strip later)."""
import urllib.request, json, base64, os, re
from pathlib import Path

with open(r'C:\Users\nostr\Desktop\claude\.env', 'r') as f:
    for line in f:
        if 'OPENROUTER' in line and '=' in line:
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
            break

BASE = "https://openrouter.ai/api/v1/chat/completions"
OUT_DIR = Path(r'C:\Users\nostr\Desktop\Night Raiders\discord-bot\assets\emojis')
OUT_DIR.mkdir(parents=True, exist_ok=True)

STICKERS = [
    ("sticker_shade_coin", "Minimalist flat vector sticker icon on solid dark background. Hexagonal coin with bold white dollar sign. Purple (#8B5CF6) to teal (#14B8A6) gradient. Thin gold rim. Clean icon, bold, simple."),
    ("sticker_dice", "Minimalist flat vector sticker icon on solid dark background. Single white D20 dice tilted, purple and teal numbered faces, gold edges. Icon style."),
    ("sticker_cards", "Minimalist flat vector sticker icon on solid dark background. Two fanned playing cards: purple spade card overlapping teal diamond card. Gold trim. Clean."),
    ("sticker_chips", "Minimalist flat vector sticker icon on solid dark background. Three stacked poker chips: purple, teal, gold. Clean simple icon."),
    ("sticker_skull", "Minimalist flat vector sticker icon on solid dark background. Angular cyberpunk skull side profile. Purple and teal accents, one teal glowing eye, gold jawline."),
    ("sticker_ghost", "Minimalist flat vector sticker icon on solid dark background. Geometric hooded ghost, purple robe, teal glowing eyes, gold trim."),
    ("sticker_martini", "Minimalist flat vector sticker icon on solid dark background. Martini glass, purple glass with teal liquid, gold rim and olive."),
    ("sticker_crest", "Minimalist flat vector sticker icon on solid dark background. Elongated hexagon shield crest with gothic arch points. Interlocking S-shapes in negative space. Purple-teal gradient, gold edge."),
]

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
                path = OUT_DIR / f"{name}.png"
                with open(path, "wb") as f:
                    f.write(img_data)
                print(f"  OK ({len(img_data)//1024}KB)")
            else:
                print(f"  Unknown format: {url[:60]}")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\nALL DONE — run strip_backgrounds.py next")
