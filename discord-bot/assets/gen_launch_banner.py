#!/usr/bin/env python3
"""Generate $SHADE token launch announcement image for X."""
import urllib.request, json, base64, os, re
from pathlib import Path
from PIL import Image
from rembg import remove, new_session

with open(r'C:\Users\nostr\Desktop\claude\.env', 'r') as f:
    for line in f:
        if 'OPENROUTER' in line and '=' in line:
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
            break

# Read coin logo as reference
coin_path = Path(r'C:\Users\nostr\Desktop\Night Raiders\build\assets\coin.png')
with open(coin_path, 'rb') as f:
    coin_b64 = base64.b64encode(f.read()).decode()

BASE = "https://openrouter.ai/api/v1/chat/completions"
OUT_DIR = Path(r'C:\Users\nostr\Desktop\Night Raiders\discord-bot\assets')
OUT_DIR.mkdir(parents=True, exist_ok=True)

prompt = """Create a dramatic cinematic wide banner (16:9, 1200x675) for a cryptocurrency token launch announcement on snek.fun.

The scene: A massive holographic projection of the Shadow Syndicate coin logo (silver reflective medallion with interlocking S-shapes, neon magenta/cyan glow, reeded edge) floating in a dark cyberpunk void. The coin is slightly tilted, casting dramatic volumetric rays of purple and teal light downward.

Behind the coin: a dark atmospheric background with subtle perspective grid lines receding into infinity, scattered cyan data particles, and faint glitch/scanline effects.

Below the coin, in bold geometric sans-serif font, glowing teal (#2DD4BF) text:

"$SHADE"

Below that, smaller gold (#FFB000) text:

"NOW LIVE ON SNEK.FUN"

Bottom edge: subtle gold line across the width.

The mood is dark, premium, mysterious, and cinematic. No faces, no characters. No watermarks. No URLs in the image. No color codes or debug text. Clean, professional, high-impact announcement banner."""

print("Generating launch banner...", flush=True)

data = json.dumps({
    "model": "google/gemini-2.5-flash-image",
    "modalities": ["image", "text"],
    "messages": [{
        "role": "user",
        "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{coin_b64}"}},
            {"type": "text", "text": prompt}
        ]
    }]
}).encode()

req = urllib.request.Request(BASE, data=data,
    headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"})

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        body = resp.read().decode()
        d = json.loads(body)
        msg = d["choices"][0]["message"]
        imgs = msg.get("images", [])
        if not imgs:
            print(f"FAIL: {str(msg.get('content',''))[:200]}")
            exit(1)
        img_url = imgs[0]["image_url"]["url"]
        img_data = base64.b64decode(re.split(r"base64,", img_url, 1)[1])
        
        path = OUT_DIR / "shade_launch_banner.png"
        with open(path, "wb") as f:
            f.write(img_data)
        print(f"Saved: {path} ({len(img_data)//1024}KB)")

except Exception as e:
    print(f"ERROR: {e}")
