#!/usr/bin/env python3
"""Generate $SHADE tokenomics breakdown — cleaner prompt."""
import urllib.request, json, base64, os, re
from pathlib import Path

with open(r'C:\Users\nostr\Desktop\claude\.env', 'r') as f:
    for line in f:
        if 'OPENROUTER' in line and '=' in line:
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
            break

coin_path = Path(r'C:\Users\nostr\Desktop\Night Raiders\build\assets\coin.png')
with open(coin_path, 'rb') as f:
    coin_b64 = base64.b64encode(f.read()).decode()

BASE = "https://openrouter.ai/api/v1/chat/completions"
OUT_DIR = Path(r'C:\Users\nostr\Desktop\Night Raiders\discord-bot\assets')

prompt = """Dark cyberpunk infographic banner (16:9, 1200x675). 

LEFT: The shadow syndicate silver coin logo floating with holographic neon glow.

RIGHT: "TOKENOMICS" in large teal (#2DD4BF) geometric font at top. Below it, four simple clean text blocks stacked vertically, each in white sans-serif with a small colored square bullet to the left:

Green square + "80% Public Float"  
Gold square + "10% LP Reserve"
Purple square + "5% Casino Liquidity"  
Gray square + "5% Treasury (12-month vest)"

Bottom: small white text "1,000,000,000 total supply · No team allocation"

Dark void background with faint grid. Clean. No other text. No color codes. No watermarks."""

print("Generating...", flush=True)

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
        img_url = imgs[0]["image_url"]["url"]
        img_data = base64.b64decode(re.split(r"base64,", img_url, 1)[1])
        path = OUT_DIR / "shade_tokenomics.png"
        with open(path, "wb") as f:
            f.write(img_data)
        print(f"Saved: {path} ({len(img_data)//1024}KB)")
except Exception as e:
    print(f"ERROR: {e}")
