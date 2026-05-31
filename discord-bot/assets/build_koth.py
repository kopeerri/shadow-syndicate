#!/usr/bin/env python3
"""King of the Hill victory graphic."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 675
BG = (8, 10, 20)
TEAL = "#2DD4BF"
GOLD = "#FFB000"
PURPLE = "#C084FC"
GRAY = "#9CA3AF"
WHITE = "#F8FAFC"

OUT = r"C:/Users/nostr/Desktop/Night Raiders/discord-bot/assets/shade_koth.png"

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

img = Image.new("RGBA", (W, H), (*BG, 255))
draw = ImageDraw.Draw(img)

# Coin centered
coin = Image.open(r"C:\Users\nostr\Desktop\Night Raiders\build\assets\coin.png").convert("RGBA")
cw = 260
ch = int(coin.height * cw / coin.width)
coin = coin.resize((cw, ch), Image.LANCZOS)
img.paste(coin, ((W - cw) // 2, 55), coin)

# Crown / KOTH text
ftitle = load_font(64)
fsub = load_font(28)
fsmall = load_font(20)
fbig = load_font(72)

def center(draw, text, font, y, fill):
    w = draw.textbbox((0, 0), text, font=font)[2] - draw.textbbox((0, 0), text, font=font)[0]
    x = (W - w) // 2
    draw.text((x, y), text, font=font, fill=fill)

# Gold crown emoji feel
center(draw, "KING OF THE HILL", ftitle, 340, GOLD)

# Token line
center(draw, "$SHADE is #1 on snek.fun", fsub, 415, TEAL)

# Stats row
stats_y = 490
stats = [
    ("#1", "RANKING"),
    ("ATH", "PRICE"),
    ("SURGING", "VOLUME"),
]
stat_w = 200
total_w = stat_w * 3 + 60 * 2
sx = (W - total_w) // 2

for i, (val, label) in enumerate(stats):
    x = sx + i * (stat_w + 60)
    # Value
    vw = draw.textbbox((0, 0), val, font=ftitle)[2] - draw.textbbox((0, 0), val, font=ftitle)[0]
    draw.text((x + (stat_w - vw) // 2, stats_y), val, font=ftitle, fill=GOLD)
    # Label
    lw = draw.textbbox((0, 0), label, font=fsub)[2] - draw.textbbox((0, 0), label, font=fsub)[0]
    draw.text((x + (stat_w - lw) // 2, stats_y + 80), label, font=fsub, fill=GRAY)

# Bottom
center(draw, "The Syndicate rises. The rest can watch.", fsmall, 625, PURPLE)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, "PNG")
print(f"OK -> {OUT} ({os.path.getsize(OUT)//1024}KB)")
