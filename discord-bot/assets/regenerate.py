#!/usr/bin/env python3
"""
Shadow Syndicate Asset Regenerator
Run: OR_KEY=sk-or-...f606 python regenerate.py

Regenerates: syndicate crest emoji, $SHADE coin emoji, rules banner, welcome banner
"""
import requests, base64, re, os, sys
from pathlib import Path

OUT = Path(__file__).parent
BASE = "https://openrouter.ai/api/v1/chat/completions"

# Get key from env
key = os.environ.get("OR_KEY", "")
if not key or len(key) < 20:
    print("ERROR: Set OR_KEY environment variable with your full OpenRouter API key")
    print("Usage: OR_KEY=sk-or-... python regenerate.py")
    sys.exit(1)

print(f"Key loaded ({len(key)} chars)")

def gen(prompt):
    r = requests.post(BASE,
        headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        json={"model": "google/gemini-2.5-flash-image", "modalities": ["image", "text"],
              "messages": [{"role": "user", "content": prompt}]}, timeout=120)
    if r.status_code != 200:
        return None, f"HTTP {r.status_code}: {r.text[:120]}"
    d = r.json()
    m = d["choices"][0]["message"]
    if "images" not in m or not m["images"]:
        return None, "No images in response"
    img = m["images"][0]
    if isinstance(img, str) and img.startswith("data:image/"):
        return base64.b64decode(re.split(r'base64,', img, 1)[1]), None
    if isinstance(img, dict) and "image_url" in img:
        url = img["image_url"]["url"]
        if url.startswith("data:"):
            return base64.b64decode(re.split(r'base64,', url, 1)[1]), None
    return None, f"Unknown image format: {type(img)}"

# ================
# ASSET PROMPTS
# ================

assets = [
    # 1. SYNDICATE CREST EMOJI - based on actual logo
    ("emojis/syndicate_crest.png",
     "Minimalist hexagonal crest icon based on the Shadow Syndicate logo. The shape is an elongated hexagon with sharp pointed gothic arch extensions at top and bottom — like a shield/crest. Inside the hexagon: two mirrored interlocking angular blocky S-shapes formed by negative space, creating a geometric intertwined double-S design (not a generic single S). The surface has an iridescent holographic gradient shifting between soft purple, teal, and pale pink with subtle grain/noise texture. Thin metallic gold-tone beveled edges outlining both the hexagon frame and the inner S-shapes. Bold, simple, readable at 128x128 emoji size. Pure black background. No text whatsoever."),

    # 2. $SHADE COIN EMOJI — bold iconic crypto token. Must work at 16x16 like ETH/BTC.
    ("emojis/shade_coin.png",
     "Crypto token icon for $SHADE. Perfect circle. The coin face is split diagonally: upper-left half glows rich purple (#C084FC) with subtle holographic shimmer, lower-right half is near-black deep shadow — the 'shade' concept made literal. At dead center: an EXTREMELY BOLD thick geometric sans-serif letter S in bright white with a teal (#2DD4BF) neon glow, filling 70% of the coin diameter. The S is so large and chunky it nearly touches the edges. Thin teal neon ring around outer circumference. Pure black background. Zero text. Zero small details. Zero thin lines. This is an ICON — not an illustration. Must be instantly recognizable at 16x16 pixels. Think: Ethereum diamond, Bitcoin B, Solana gradient circle. That level of iconic simplicity. Dark, premium, cyberpunk crypto token."),

    # 3. RULES BANNER - proper wide format
    ("banners/rules_banner.png",
     "Wide 16:9 cinematic cyberpunk banner (1920x1080 proportions). Left third of the frame: a large detailed holographic Shadow Syndicate crest emblem — elongated hexagon shield shape with sharp pointed gothic arch extensions at top and bottom, two interlocking angular blocky S-shapes inside creating negative space, iridescent purple-to-teal holographic gradient across the surface with subtle film grain texture, gold-tone metallic beveled edges catching light. The crest emits a soft ethereal glow against the dark void. Right two-thirds: 'THE SYNDICATE CHARTER' displayed in large bold geometric Orbitron-style font, letters glowing bright teal (#2DD4BF) neon with a subtle purple (#C084FC) chromatic aberration offset creating a slight glitch effect. Background: deep infinite dark void with faint perspective grid lines in very dark purple and scattered floating cyan data-stream particles. A thin elegant gold (#FFB000) horizontal line runs across the full width at the very bottom edge. Professional, premium, mysterious cyberpunk aesthetic. No other text or elements."),

    # 4. WELCOME BANNER - cinematic immersive
    ("banners/welcome_banner.png",
     "Wide 16:9 cinematic cyberpunk banner (1920x1080 proportions). Deep infinite dark background with a dramatic sweeping perspective grid floor — dark purple and teal neon grid lines receding to a distant vanishing point on the horizon. Three tall imposing glowing portal arches stand across the mid-ground, evenly spaced — left portal contains a bright neon purple spade card symbol (♠), center portal contains a bright neon purple 3D dice cube (🎲) with visible pips, right portal contains a bright neon purple hexagonal mine grid pattern. Each portal arch is framed with intense glowing purple (#C084FC) neon light that casts soft reflections and light pools on the grid floor below. High above the center portal, floating majestically in the dark atmospheric sky: 'NODE ZERO' in massive bold Orbitron-style geometric font with a stunning iridescent holographic gradient shifting from deep purple through electric teal to soft pink, accented with a subtle glitch chromatic aberration effect. Scattered cyan digital particles and thin vertical data-rain streaks fall gently in the background. The overall atmosphere is epic, immersive, and mysterious — high-end cyberpunk cinematic quality. Dramatic volumetric lighting with god rays emanating from behind the portals."),
]

results = []
for i, (rel_path, prompt) in enumerate(assets):
    name = rel_path.split("/")[-1]
    path = OUT / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"[{i+1}/{len(assets)}] {name}...")
    img_bytes, error = gen(prompt)
    
    if img_bytes:
        path.write_bytes(img_bytes)
        kb = len(img_bytes) // 1024
        print(f"  OK ({kb}KB) -> {rel_path}")
        results.append(f"OK {name}")
    else:
        print(f"  FAIL: {error}")
        results.append(f"FAIL {name}")

print(f"\n=== {sum(1 for r in results if r.startswith('OK'))}/{len(results)} REGENERATED ===")
for r in results:
    print(r)

# Remove old dust_coin if it exists
old = OUT / "emojis" / "dust_coin.png"
if old.exists():
    old.unlink()
    print("Removed old dust_coin.png")
