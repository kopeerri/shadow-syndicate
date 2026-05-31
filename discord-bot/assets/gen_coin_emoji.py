#!/usr/bin/env python3
"""Generate coin emoji from coin.png reference, strip background."""
import urllib.request, json, base64, os, re
from pathlib import Path
from rembg import remove, new_session
from PIL import Image

# Read key
with open(r'C:\Users\nostr\Desktop\claude\.env', 'r') as f:
    for line in f:
        if 'OPENROUTER' in line and '=' in line:
            key = line.split('=', 1)[1].strip().strip('"').strip("'")
            break

# Read reference coin image
coin_path = Path(r'C:\Users\nostr\Desktop\Night Raiders\build\assets\coin.png')
with open(coin_path, 'rb') as f:
    coin_b64 = base64.b64encode(f.read()).decode()

BASE = "https://openrouter.ai/api/v1/chat/completions"
OUT_DIR = Path(r'C:\Users\nostr\Desktop\Night Raiders\discord-bot\assets\emojis')
OUT_DIR.mkdir(parents=True, exist_ok=True)

prompt = """Create a clean flat sticker-style emoji icon based on the reference coin image. 

Keep the SAME design faithfully:
- Circular silver reflective medallion/coin with reeded edge
- Symmetrical interlocking mirrored S-shapes at center forming a monogram
- Sharp pointed gothic arch extensions at top and bottom
- Neon glow gradient: magenta/purple on left, teal/cyan on right
- Dark milled edge around the circular coin
- "SHADOW SYNDICATE" and "NODE ZERO" inscribed around the rim

Make it a bold, clean, readable emoji/sticker icon — not a realistic coin render. Flat vector style. 
Solid dark background for now (will be removed later). No text outside the coin. No watermark."""

print("Generating coin emoji from reference...", flush=True)

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
        if "base64," not in img_url:
            print(f"FAIL: unknown format")
            exit(1)
        
        img_data = base64.b64decode(re.split(r"base64,", img_url, 1)[1])
        
        # Save raw
        raw_path = OUT_DIR / "coin_emoji_raw.png"
        with open(raw_path, "wb") as f:
            f.write(img_data)
        print(f"Raw saved ({len(img_data)//1024}KB)")
        
        # Strip background
        print("Stripping background with rembg...", flush=True)
        img = Image.open(raw_path).convert("RGB")
        session = new_session("u2net")
        result = remove(img, session=session, alpha_matting=True,
                        alpha_matting_foreground_threshold=240,
                        alpha_matting_background_threshold=10,
                        alpha_matting_erode_size=10)
        
        final_path = OUT_DIR / "coin_emoji.png"
        result.save(str(final_path), "PNG")
        raw_path.unlink()
        
        # Verify
        check = Image.open(final_path)
        if 'A' in check.getbands():
            alpha = list(check.getchannel('A').getdata())
            transparent = sum(1 for a in alpha if a == 0)
            pct = 100 * transparent / len(alpha)
            print(f"Done: {final_path} ({os.path.getsize(final_path)//1024}KB, {pct:.0f}% transparent)")
        
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
