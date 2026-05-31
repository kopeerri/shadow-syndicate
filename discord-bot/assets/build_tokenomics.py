#!/usr/bin/env python3
"""Build tokenomics infographic programmatically — no AI text errors."""
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

W, H = 1200, 675
OUT = Path(r'C:\Users\nostr\Desktop\Night Raiders\discord-bot\assets\shade_tokenomics.png')

# Dark background with subtle grid
img = Image.new('RGBA', (W, H), (5, 5, 15, 255))
draw = ImageDraw.Draw(img)

# Subtle grid
for x in range(0, W, 40):
    draw.line([(x, 0), (x, H)], fill=(20, 20, 40, 80), width=1)
for y in range(0, H, 40):
    draw.line([(0, y), (W, y)], fill=(20, 20, 40, 80), width=1)

# Load and place coin logo
coin = Image.open(r'C:\Users\nostr\Desktop\Night Raiders\build\assets\coin.png').convert('RGBA')
coin_w = 320
coin_h = int(coin.height * coin_w / coin.width)
coin = coin.resize((coin_w, coin_h), Image.LANCZOS)
img.paste(coin, (50, (H - coin_h) // 2), coin)

# Try loading a geometric font
font_paths = [
    "C:/Windows/Fonts/impact.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
]
font_title = None
font_body = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            font_title = ImageFont.truetype(fp, 52)
            font_body = ImageFont.truetype(fp, 28)
            font_small = ImageFont.truetype(fp, 18)
            break
        except:
            continue

if font_title is None:
    font_title = ImageFont.load_default()
    font_body = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Right panel start
rx = 420

# Title
draw.text((rx, 90), "$SHADE TOKENOMICS", fill=(45, 212, 191), font=font_title)

# Allocation bars
bar_x = rx
bar_w = 500
bar_h = 36
gap = 22
start_y = 190

allocations = [
    ("90% Public Float", (45, 212, 191)),       # teal
    ("5% Casino Liquidity", (192, 132, 252)),    # purple
    ("5% Treasury (12-month vest)", (148, 163, 184)),  # gray
]

for i, (label, color) in enumerate(allocations):
    y = start_y + i * (bar_h + gap)
    pct = int(label.split('%')[0])
    bar_fill_w = int(bar_w * pct / 90)  # scale to 90% max
    
    # Bar background
    draw.rectangle([bar_x, y, bar_x + bar_w, y + bar_h], fill=(30, 30, 50), outline=None)
    # Filled bar
    draw.rectangle([bar_x, y, bar_x + bar_fill_w, y + bar_h], fill=color)
    # Label
    draw.text((bar_x + bar_w + 16, y + 4), label, fill=(220, 220, 240), font=font_body)

# Bottom text
draw.text((rx, start_y + 4 * (bar_h + gap) + 30), 
          "1,000,000,000 total supply  ·  No team allocation  ·  No VC unlocks",
          fill=(140, 160, 180), font=font_small)

# Gold accent line at bottom
draw.line([(rx, H - 50), (W - 40, H - 50)], fill=(255, 176, 0, 180), width=2)

img.save(OUT, 'PNG')
print(f"Saved: {OUT} ({os.path.getsize(OUT)//1024}KB)")
