#!/usr/bin/env python3
"""Clean professional profit split graphic."""
from PIL import Image, ImageDraw, ImageFont
import os
from pathlib import Path

W, H = 1200, 675
OUT = Path(r'C:\Users\nostr\Desktop\Night Raiders\discord-bot\assets\shade_profit_split.png')

# Clean dark background
img = Image.new('RGBA', (W, H), (8, 10, 20, 255))
draw = ImageDraw.Draw(img)

# Fonts
font_paths = ["C:/Windows/Fonts/segoeuib.ttf", "C:/Windows/Fonts/calibrib.ttf", "C:/Windows/Fonts/arialbd.ttf"]
font_title = font_body = font_small = font_big = None
for fp in font_paths:
    if os.path.exists(fp):
        try:
            font_big = ImageFont.truetype(fp, 56)
            font_title = ImageFont.truetype(fp, 44)
            font_body = ImageFont.truetype(fp, 26)
            font_small = ImageFont.truetype(fp, 18)
            break
        except:
            continue
if font_title is None:
    font_big = font_title = font_body = font_small = ImageFont.load_default()

# === COIN — top left, smaller ===
coin = Image.open(r'C:\Users\nostr\Desktop\Night Raiders\build\assets\coin.png').convert('RGBA')
coin_w = 200
coin_h = int(coin.height * coin_w / coin.width)
coin = coin.resize((coin_w, coin_h), Image.LANCZOS)
img.paste(coin, (60, 50), coin)

# === TITLE ===
draw.text((290, 65), "CASINO PROFIT SPLIT", fill=(45, 212, 191), font=font_title)
draw.text((290, 125), "100% of casino profits distributed monthly. On-chain. Trustless.", fill=(150, 160, 180), font=font_small)

# === THREE CARDS ===
card_w = 300
card_h = 220
card_gap = 30
cards_x = 60
cards_y = 310

cards = [
    ("20%", "$SHADE Stakers", "Hold and stake. Earn yield\ndirectly from casino revenue.\nNo LP risk. Pure passive income.", (45, 212, 191)),
    ("50%", "Liquidity Providers", "Deposit into the casino\nbankroll. You are the house.\nEarn the largest profit share.", (255, 176, 0)),
    ("30%", "Treasury", "Funds development, marketing,\nand ecosystem growth.\nDAO-governed after launch.", (148, 163, 184)),
]

for i, (pct, title, desc, color) in enumerate(cards):
    cx = cards_x + i * (card_w + card_gap)
    cy = cards_y
    
    # Card background
    draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=16, fill=(18, 22, 38, 255), outline=(color[0], color[1], color[2], 60), width=1)
    
    # Percentage
    draw.text((cx + 24, cy + 24), pct, fill=color, font=font_big)
    
    # Title
    draw.text((cx + 24, cy + 95), title, fill=(240, 245, 255), font=font_body)
    
    # Description
    draw.text((cx + 24, cy + 135), desc, fill=(140, 150, 170), font=font_small)

# Bottom bar
draw.text((60, 610), "All distributions verified on-chain via Midnight Network ZK proofs. Fully auditable. Fully trustless.", fill=(100, 110, 130), font=font_small)
draw.line([(60, H - 30), (W - 60, H - 30)], fill=(45, 212, 191, 100), width=2)

img.save(OUT, 'PNG')
print(f"Saved: {OUT} ({os.path.getsize(OUT)//1024}KB)")
