#!/usr/bin/env python3
"""Regenerate rules banner using coin.png as the crest reference."""
import urllib.request, json, base64, os, re
from pathlib import Path

# Read key
with open(r'C:\Users\nostr\Desktop\claude\.env', 'r') as f:
    for line in f:
        if 'OPENROUTER' in line and '=' in line:
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
            break

# Read coin image and encode as base64
coin_path = Path(r'C:\Users\nostr\Desktop\Night Raiders\build\assets\coin.png')
with open(coin_path, 'rb') as f:
    coin_b64 = base64.b64encode(f.read()).decode()

BASE = "https://openrouter.ai/api/v1/chat/completions"
OUT_DIR = Path(r'C:\Users\nostr\Desktop\Night Raiders\discord-bot\assets\banners')
OUT_DIR.mkdir(parents=True, exist_ok=True)

prompt = """Create a wide 16:9 cinematic cyberpunk banner (1920x1080). 

LEFT SIDE: A large detailed holographic Shadow Syndicate crest emblem. The crest is the SAME design as the reference image I'm providing — a circular coin/medallion with:
- Polished reflective silver/chrome metallic body
- Symmetrical interlocking mirrored S-shapes forming a monogram
- Sharp pointed gothic arch extensions at top and bottom
- Neon glow gradient shifting from magenta/purple on left to teal/cyan on right
- Dark reeded edge around the circular coin
- The text "SHADOW SYNDICATE" and "NODE ZERO" inscribed around the rim

The crest emits a soft ethereal glow against the dark void.

RIGHT SIDE: "THE SYNDICATE CHARTER" displayed in large bold geometric Orbitron-style font, letters glowing bright teal (#2DD4BF) neon with a subtle purple (#C084FC) chromatic aberration offset creating a slight glitch effect.

BACKGROUND: Deep infinite dark void with faint perspective grid lines in very dark purple and scattered floating cyan data-stream particles.

BOTTOM: A thin elegant gold (#FFB000) horizontal line runs across the full width at the very bottom edge.

Professional, premium, mysterious cyberpunk aesthetic. NO watermark text. NO color codes. NO hex values. NO debug text. NO FFB text. Clean final deliverable."""

data = json.dumps({
    "model": "google/gemini-2.5-flash-image",
    "modalities": ["image", "text"],
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{coin_b64}"}
                },
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]
}).encode()

print("Sending banner generation request with coin reference...", flush=True)

req = urllib.request.Request(BASE, data=data,
    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode()
        d = json.loads(body)
        msg = d["choices"][0]["message"]
        imgs = msg.get("images", [])
        if not imgs:
            print(f"FAIL: no images. Content: {str(msg.get('content',''))[:200]}")
            exit(1)
        
        img = imgs[0]
        url = img["image_url"]["url"]
        if "base64," in url:
            img_data = base64.b64decode(re.split(r"base64,", url, 1)[1])
            path = OUT_DIR / "rules_banner.png"
            with open(path, "wb") as f:
                f.write(img_data)
            print(f"OK ({len(img_data)//1024}KB) -> {path}")
        else:
            print(f"Unknown format: {url[:80]}")
except Exception as e:
    print(f"ERROR: {e}")
