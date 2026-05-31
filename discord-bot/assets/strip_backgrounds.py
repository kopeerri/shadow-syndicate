#!/usr/bin/env python3
"""Step 2: Strip backgrounds from sticker PNGs using rembg."""
from rembg import remove, new_session
from PIL import Image
import os
from pathlib import Path

d = Path(r'C:\Users\nostr\Desktop\Night Raiders\discord-bot\assets\emojis')
files = sorted([f for f in os.listdir(d) if f.startswith('sticker_') and f.endswith('.png')])

# Use u2net model (better for objects with clear edges)
session = new_session("u2net")

for f in files:
    path = d / f
    print(f'{f}...', end=' ', flush=True)
    
    img = Image.open(path).convert('RGB')
    result = remove(img, session=session, alpha_matting=True,
                    alpha_matting_foreground_threshold=240,
                    alpha_matting_background_threshold=10,
                    alpha_matting_erode_size=10)
    
    # Ensure RGBA
    if result.mode != 'RGBA':
        result = result.convert('RGBA')
    
    result.save(str(path), 'PNG')
    
    # Check
    result_check = Image.open(path)
    if 'A' in result_check.getbands():
        alpha_data = list(result_check.getchannel('A').getdata())
        fully_clear = sum(1 for x in alpha_data if x == 0)
        pct = 100 * fully_clear / len(alpha_data)
        print(f'transparent={pct:.0f}%')
    else:
        print('NO ALPHA')

print('DONE')
