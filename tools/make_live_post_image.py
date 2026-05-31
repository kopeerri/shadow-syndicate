from PIL import Image, ImageDraw, ImageFont, ImageFilter
import math, random
from pathlib import Path

OUT = Path(r"C:/Users/nostr/Desktop/Night Raiders/build/assets/shadow-syndicate-live.png")
W = H = 1200
random.seed(7)

# Palette
BG = (5, 7, 14)
PANEL = (10, 14, 28)
TEAL = (45, 212, 191)
CYAN = (0, 240, 255)
PURPLE = (192, 132, 252)
MAGENTA = (255, 45, 210)
GOLD = (255, 176, 0)
WHITE = (236, 244, 255)
MUTED = (115, 130, 150)

img = Image.new("RGBA", (W, H), BG + (255,))

# Helpers
def font(size, bold=True):
    paths = [
        "C:/Windows/Fonts/segoeuib.ttf" if bold else "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/calibrib.ttf" if bold else "C:/Windows/Fonts/calibri.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()

def center_text(draw, box, text, fnt, fill, spacing=0):
    x1, y1, x2, y2 = box
    bbox = draw.multiline_textbbox((0, 0), text, font=fnt, spacing=spacing, align="center")
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.multiline_text((x1 + (x2 - x1 - tw) / 2, y1 + (y2 - y1 - th) / 2 - bbox[1]), text, font=fnt, fill=fill, align="center", spacing=spacing)

def glow_line(layer, pts, fill, width=3, glow=18):
    g = Image.new("RGBA", (W, H), (0,0,0,0))
    gd = ImageDraw.Draw(g)
    for w in [width+18, width+10, width+4]:
        gd.line(pts, fill=fill[:3] + (35,), width=w, joint="curve")
    gd.line(pts, fill=fill[:3] + (210,), width=width, joint="curve")
    layer.alpha_composite(g.filter(ImageFilter.GaussianBlur(glow/5)))
    layer.alpha_composite(g)

# background gradient
pix = img.load()
for y in range(H):
    for x in range(W):
        dx = (x - W*0.5) / W
        dy = (y - H*0.48) / H
        radial = max(0, 1 - math.sqrt(dx*dx + dy*dy)*1.8)
        r = int(BG[0] + radial*22 + max(0, 1-y/H)*4)
        g = int(BG[1] + radial*18)
        b = int(BG[2] + radial*48)
        pix[x,y] = (r,g,b,255)

d = ImageDraw.Draw(img)

# star/noise points
for _ in range(520):
    x = random.randrange(W); y = random.randrange(H)
    a = random.randrange(18, 85)
    col = random.choice([TEAL, PURPLE, MUTED])
    d.point((x,y), fill=col+(a,))

# perspective grid floor
for i in range(-12, 13):
    x0 = W//2 + i*38
    glow_line(img, [(x0, 705), (W//2 + i*105, H+40)], TEAL, width=1, glow=9)
for j in range(9):
    y = 720 + int((j/8)**1.8 * 430)
    glow_line(img, [(110, y), (1090, y)], PURPLE if j%2 else TEAL, width=1, glow=8)

# vault glow behind door
for radius, alpha in [(520,18),(390,28),(270,55),(165,90)]:
    layer = Image.new("RGBA", (W,H), (0,0,0,0))
    ld = ImageDraw.Draw(layer)
    ld.ellipse((W//2-radius, 490-radius, W//2+radius, 490+radius), fill=TEAL+(alpha,))
    img.alpha_composite(layer.filter(ImageFilter.GaussianBlur(42)))

# vault door / portal
cx, cy, r = 600, 505, 255
# outer ring
for rad, col, width in [(292, PURPLE, 8), (268, TEAL, 5), (236, GOLD, 2)]:
    d.ellipse((cx-rad, cy-rad, cx+rad, cy+rad), outline=col+(190,), width=width)
# door halves cracked open
left_poly = [(cx-230, cy-245), (cx-32, cy-180), (cx-32, cy+210), (cx-230, cy+250)]
right_poly = [(cx+230, cy-245), (cx+32, cy-180), (cx+32, cy+210), (cx+230, cy+250)]
d.polygon(left_poly, fill=(11, 15, 28, 245), outline=PURPLE+(180,))
d.polygon(right_poly, fill=(11, 15, 28, 245), outline=TEAL+(180,))
# central live light crack
for wdt, alpha in [(70,30),(42,70),(20,130),(7,245)]:
    d.rounded_rectangle((cx-wdt//2, cy-210, cx+wdt//2, cy+230), radius=wdt//2, fill=TEAL+(alpha,))
# door detail
d.arc((cx-145, cy-145, cx+145, cy+145), start=205, end=335, fill=MUTED+(130,), width=3)
d.arc((cx-178, cy-178, cx+178, cy+178), start=25, end=155, fill=MUTED+(100,), width=2)
for ang in range(0,360,30):
    a=math.radians(ang)
    x1=cx+math.cos(a)*240; y1=cy+math.sin(a)*240
    x2=cx+math.cos(a)*262; y2=cy+math.sin(a)*262
    d.line((x1,y1,x2,y2), fill=GOLD+(180,), width=3)

# coin emblem
coin_r=76
coin=(cx, cy+7)
for rr, col, a in [(106, TEAL, 45),(88, PURPLE,65),(coin_r,GOLD,230)]:
    lay=Image.new("RGBA",(W,H),(0,0,0,0)); ld=ImageDraw.Draw(lay)
    ld.ellipse((coin[0]-rr, coin[1]-rr, coin[0]+rr, coin[1]+rr), fill=col+(a,))
    img.alpha_composite(lay.filter(ImageFilter.GaussianBlur(12 if rr>coin_r else 0)))
d.ellipse((coin[0]-coin_r, coin[1]-coin_r, coin[0]+coin_r, coin[1]+coin_r), fill=(20,22,34,255), outline=GOLD+(240,), width=5)
d.ellipse((coin[0]-coin_r+14, coin[1]-coin_r+14, coin[0]+coin_r-14, coin[1]+coin_r-14), outline=TEAL+(180,), width=2)
# stylized S/S mark
d.arc((coin[0]-36, coin[1]-47, coin[0]+36, coin[1]+7), 190, 535, fill=WHITE+(230,), width=10)
d.arc((coin[0]-36, coin[1]-7, coin[0]+36, coin[1]+47), 10, 355, fill=WHITE+(230,), width=10)
d.line((coin[0]-30, coin[1]-32, coin[0]+30, coin[1]+32), fill=PURPLE+(230,), width=6)

# hologram icons
icon_y=806
# card
card_box=(275, icon_y-45, 365, icon_y+80)
d.rounded_rectangle(card_box, radius=10, outline=TEAL+(220,), width=3, fill=(8,13,25,190))
d.text((298,icon_y-20), "A", font=font(40), fill=WHITE+(235,))
d.text((316,icon_y+20), "♠", font=font(36), fill=PURPLE+(230,))
# dice
x0=555; y0=icon_y-35
d.rounded_rectangle((x0,y0,x0+90,y0+90), radius=14, outline=GOLD+(220,), width=3, fill=(8,13,25,190))
for px,py in [(x0+24,y0+24),(x0+66,y0+24),(x0+45,y0+45),(x0+24,y0+66),(x0+66,y0+66)]:
    d.ellipse((px-5,py-5,px+5,py+5), fill=GOLD+(230,))
# mine grid
mx=835; my=icon_y-37
for gy in range(3):
    for gx in range(3):
        d.rounded_rectangle((mx+gx*32,my+gy*32,mx+gx*32+24,my+gy*32+24), radius=4, outline=PURPLE+(170,), width=2, fill=(8,13,25,160))
d.ellipse((mx+36,my+36,mx+52,my+52), fill=MAGENTA+(220,))

# typography panel
panel = Image.new("RGBA", (W,H), (0,0,0,0))
pd = ImageDraw.Draw(panel)
pd.rounded_rectangle((110, 84, 1090, 224), radius=26, fill=(5,8,18,205), outline=TEAL+(110,), width=2)
img.alpha_composite(panel)
d = ImageDraw.Draw(img)
center_text(d, (120, 74, 1080, 150), "NODE ZERO IS LIVE", font(58), WHITE+(255,))
center_text(d, (120, 144, 1080, 214), "$SHADE CASINO · MANUAL DEPOSITS · PROVABLY FAIR GAMES", font(24), TEAL+(235,))

# bottom lockup
pd = ImageDraw.Draw(img)
pd.rounded_rectangle((165, 1026, 1035, 1102), radius=19, fill=(5,8,18,218), outline=PURPLE+(120,), width=2)
center_text(pd, (180, 1017, 1020, 1072), "shadow-syndicate-iota.vercel.app", font(32), WHITE+(245,))
center_text(pd, (180, 1060, 1020, 1103), "send $SHADE manually · verify on-chain · play from casino balance", font(22), MUTED+(245,))

# subtle vignette
vig = Image.new("L", (W,H), 0)
vd = ImageDraw.Draw(vig)
vd.rectangle((0,0,W,H), fill=0)
for i in range(280):
    alpha = int((i/280)**2 * 210)
    vd.rectangle((i,i,W-i,H-i), outline=alpha)
# invert-ish: create dark edge mask by radial manually
edge = Image.new("RGBA", (W,H), (0,0,0,0))
ep=edge.load()
for y in range(H):
    for x in range(W):
        dx=abs(x-W/2)/(W/2); dy=abs(y-H/2)/(H/2)
        v=max(0, (max(dx,dy)-0.52)/0.48)
        ep[x,y]=(0,0,0,int(v*v*150))
img.alpha_composite(edge)

OUT.parent.mkdir(parents=True, exist_ok=True)
img.convert("RGB").save(OUT, quality=95)
print(OUT)
