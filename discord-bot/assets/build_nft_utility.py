#!/usr/bin/env python3
"""Night Raiders NFT utility infographic."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 675
BG = (8, 10, 20)
TEAL = "#2DD4BF"
GOLD = "#FFB000"
PURPLE = "#C084FC"
GRAY = "#9CA3AF"
WHITE = "#F8FAFC"
DARK_CARD = (18, 22, 38)

OUT = r"C:/Users/nostr/Desktop/Night Raiders/discord-bot/assets/nft_utility.png"

FONT_PATHS = [
    r"C:/Windows/Fonts/segoeuib.ttf",
    r"C:/Windows/Fonts/calibrib.ttf",
    r"C:/Windows/Fonts/arialbd.ttf",
]

def load_font(size):
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                pass
    return ImageFont.load_default()

ftitle = load_font(40)
fsub = load_font(20)
fbody = load_font(18)
ftier = load_font(22)
fperk = load_font(16)

img = Image.new("RGBA", (W, H), (*BG, 255))
draw = ImageDraw.Draw(img)

def center(text, font, y, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    x = (W - w) // 2
    draw.text((x - bbox[0], y - bbox[1]), text, font=font, fill=fill)

# Coin logo small
coin = Image.open(r"C:\Users\nostr\Desktop\Night Raiders\build\assets\coin.png").convert("RGBA")
cw = 70
ch = int(coin.height * cw / coin.width)
coin = coin.resize((cw, ch), Image.LANCZOS)
img.paste(coin, ((W - cw) // 2, 20), coin)

center("NIGHT RAIDERS UTILITY", ftitle, 105, TEAL)
center("NFT holders get VIP treatment across the entire Shadow Syndicate casino.", fsub, 158, GRAY)

# 4 tier cards
card_w = 240
card_h = 300
gap = 24
total_w = card_w * 4 + gap * 3
start_x = (W - total_w) // 2
cards_y = 200

tiers = [
    ("COMMON", PURPLE, [
        "5% rakeback on all bets",
        "VIP lounge access",
        "Early game access",
        "Monthly airdrop bonus",
    ]),
    ("RARE", "#3B82F6", [
        "10% rakeback",
        "1.2x staking multiplier",
        "VIP lounge access",
        "Early game access",
    ]),
    ("EPIC", GOLD, [
        "15% rakeback",
        "1.5x staking multiplier",
        "Private high-roller tables",
        "Governance vote weight",
    ]),
    ("LEGENDARY", TEAL, [
        "20% rakeback",
        "2x staking multiplier",
        "0.5% better house edge",
        "Governance + veto power",
    ]),
]

for i, (tier, color, perks) in enumerate(tiers):
    cx = start_x + i * (card_w + gap)
    cy = cards_y
    
    # Card
    draw.rounded_rectangle([cx, cy, cx + card_w, cy + card_h], radius=14,
                          fill=DARK_CARD, outline=color, width=2)
    
    # Tier name
    tbbox = draw.textbbox((0, 0), tier, font=ftier)
    tw = tbbox[2] - tbbox[0]
    draw.text((cx + (card_w - tw) // 2 - tbbox[0], cy + 20 - tbbox[1]), tier, font=ftier, fill=color)
    
    # Accent line
    draw.line([(cx + 30, cy + 58), (cx + card_w - 30, cy + 58)], fill=color, width=1)
    
    # Perks
    py = cy + 72
    for perk in perks:
        draw.text((cx + 24, py), "\u2022 " + perk, font=fperk, fill=GRAY)
        pbbox = draw.textbbox((0, 0), perk, font=fperk)
        py += (pbbox[3] - pbbox[1]) + 16

# Bottom
center("One collection. Infinite utility. The Syndicate rewards loyalty.", fsub, 560, PURPLE)
center("Night Raiders \u00b7 Shadow Syndicate \u00b7 Midnight Network", load_font(16), 595, GRAY)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, "PNG")
print(f"OK -> {OUT} ({os.path.getsize(OUT)//1024}KB)")
