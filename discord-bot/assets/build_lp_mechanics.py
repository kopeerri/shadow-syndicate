#!/usr/bin/env python3
"""LP mechanics — GPT-5.4 generated Pillow code, cleaned."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 675
BG = (8, 10, 20)
TEAL = "#2DD4BF"
GRAY = "#9CA3AF"
CARD_FILL = (18, 22, 38)
PURPLE = "#C084FC"
GOLD = "#FFB000"
WHITE = "#F8FAFC"

OUT = r"C:/Users/nostr/Desktop/Night Raiders/discord-bot/assets/shade_lp_mechanics.png"

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

title_font = load_font(44)
subtitle_font = load_font(22)
heading_font = load_font(24)
body_font = load_font(18)
badge_font = load_font(24)
bottom_main_font = load_font(22)
bottom_sub_font = load_font(18)

img = Image.new("RGBA", (W, H), (*BG, 255))
draw = ImageDraw.Draw(img)

def centered_text_position(draw, text, font, center_x, top_y):
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    x = center_x - text_w / 2 - bbox[0]
    y = top_y - bbox[1]
    return x, y

def centered_text_in_box(draw, text, font, box):
    x1, y1, x2, y2 = box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    box_w = x2 - x1
    box_h = y2 - y1
    x = x1 + (box_w - text_w) / 2 - bbox[0]
    y = y1 + (box_h - text_h) / 2 - bbox[1]
    return x, y

def draw_wrapped(draw, text, font, fill, x, y, max_width, line_spacing=6):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = word if not current else current + " " + word
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    current_y = y
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_h = bbox[3] - bbox[1]
        draw.text((x - bbox[0], current_y - bbox[1]), line, font=font, fill=fill)
        current_y += line_h + line_spacing
    return current_y

# Title
title = "BECOME THE HOUSE"
subtitle = "How liquidity providing works on Shadow Syndicate"
tx, ty = centered_text_position(draw, title, title_font, W / 2, 34)
draw.text((tx, ty), title, font=title_font, fill=TEAL)
title_bbox = draw.textbbox((tx, ty), title, font=title_font)
sx, sy = centered_text_position(draw, subtitle, subtitle_font, W / 2, title_bbox[3] + 10)
draw.text((sx, sy), subtitle, font=subtitle_font, fill=GRAY)

# Cards
card_w, card_h = 320, 240
gap = 40
total_w = card_w * 3 + gap * 2
start_x = (W - total_w) / 2
cards_y = 155

cards_data = [
    (TEAL, "1", "DEPOSIT", "Send $SHADE to the casino bankroll pool. Receive lpSHADE tokens \u2014 your receipt and profit tracker."),
    (PURPLE, "2", "EARN", "Every player bet flows through the pool. House edge drives net inflow. 50% of monthly profits go to liquidity providers."),
    (GOLD, "3", "WITHDRAW", "After 7 days, redeem lpSHADE anytime. Get your deposit + accrued profits back. Distributions every month."),
]

for i, (border_color, num, heading, body) in enumerate(cards_data):
    x1 = start_x + i * (card_w + gap)
    y1 = cards_y
    x2 = x1 + card_w
    y2 = y1 + card_h

    draw.rounded_rectangle([x1, y1, x2, y2], radius=16, fill=CARD_FILL, outline=border_color, width=2)

    # Badge
    badge_size = 44
    bx1 = x1 + 24
    by1 = y1 + 24
    bx2 = bx1 + badge_size
    by2 = by1 + badge_size
    draw.rounded_rectangle([bx1, by1, bx2, by2], radius=10, fill=border_color)
    # Number centered — small visual correction for digit width
    nx, ny = centered_text_in_box(draw, num, badge_font, [bx1, by1, bx2, by2])
    # Single digits often look right-heavy — nudge left by 1px
    draw.text((nx - 1, ny), num, font=badge_font, fill=BG)

    # Heading vertically aligned to badge center — slight downward nudge
    heading_bbox = draw.textbbox((0, 0), heading, font=heading_font)
    heading_h = heading_bbox[3] - heading_bbox[1]
    badge_center_y = (by1 + by2) / 2
    hx = bx2 + 16 - heading_bbox[0]
    hy = badge_center_y - heading_h / 2 - heading_bbox[1] + 2  # +2 visual correction
    draw.text((hx, hy), heading, font=heading_font, fill=WHITE)

    # Body — same x as heading
    body_top = by2 + 22
    draw_wrapped(draw, body, body_font, GRAY, hx, body_top, max_width=(x2 - 24) - hx)

# Bottom bar — semi-transparent teal overlay
bar_x1 = start_x
bar_x2 = start_x + total_w
bar_y1 = 545
bar_y2 = 635
draw.rounded_rectangle([bar_x1, bar_y1, bar_x2, bar_y2], radius=18,
                      fill=(45, 212, 191, 30), outline=(45, 212, 191, 100), width=1)

bottom = "You are not betting against players. You ARE the casino. The house edge compounds in your favor."
sub = "Verified on-chain \u00b7 Midnight Network ZK proofs \u00b7 7-day cooldown \u00b7 Monthly profit distributions"

main_bbox = draw.textbbox((0, 0), bottom, font=bottom_main_font)
sub_bbox = draw.textbbox((0, 0), sub, font=bottom_sub_font)
main_h = main_bbox[3] - main_bbox[1]
sub_h = sub_bbox[3] - sub_bbox[1]
total_h = main_h + 8 + sub_h

bar_cx = (bar_x1 + bar_x2) / 2
bar_cy = (bar_y1 + bar_y2) / 2
block_top = bar_cy - total_h / 2

mx, my = centered_text_position(draw, bottom, bottom_main_font, bar_cx, block_top)
draw.text((mx, my), bottom, font=bottom_main_font, fill=TEAL)
main_drawn = draw.textbbox((mx, my), bottom, font=bottom_main_font)
sx2, sy2 = centered_text_position(draw, sub, bottom_sub_font, bar_cx, main_drawn[3] + 8)
draw.text((sx2, sy2), sub, font=bottom_sub_font, fill=GRAY)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
img.save(OUT, "PNG")
print(f"OK -> {OUT} ({os.path.getsize(OUT)//1024}KB)")
