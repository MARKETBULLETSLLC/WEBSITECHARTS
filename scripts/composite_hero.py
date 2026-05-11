from PIL import Image
import numpy as np

TRUCK = r"C:\Users\hofer\OneDrive\MBLLC.COM CLOUD\Site Development\images\20230320_watertruck.png"
LOGO  = r"C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\MarketBullets_Logo.png"
OUT   = r"C:\Users\hofer\OneDrive\Documents\GitHub\WEBSITECHARTS\hero_banner.jpg"

DOOR_CX   = 0.145   # door center as fraction of image width  (~left 14.5%)
DOOR_CY   = 0.525   # door center as fraction of image height (~52% down)
LOGO_FRAC = 0.28    # logo diameter = 28% of image height
OPACITY   = 0.68    # weathered/faded painted-on look

# Truck-door olive green — matches faded body paint, readable against door panel
PAINT_RGB = (88, 118, 48)   # hex #587630

truck = Image.open(TRUCK).convert("RGBA")
logo  = Image.open(LOGO).convert("RGBA")

W, H = truck.size
logo_px = int(H * LOGO_FRAC)
logo = logo.resize((logo_px, logo_px), Image.LANCZOS)

# Extract luminosity of logo as mask (white logo art = opaque, black bg = transparent)
gray = np.array(logo.convert("L"), dtype=np.float32) / 255.0

# Build colored layer in truck green
colored = np.zeros((logo_px, logo_px, 4), dtype=np.float32)
colored[..., 0] = PAINT_RGB[0] / 255.0
colored[..., 1] = PAINT_RGB[1] / 255.0
colored[..., 2] = PAINT_RGB[2] / 255.0
colored[..., 3] = gray * OPACITY          # alpha = logo brightness × opacity

painted = Image.fromarray((colored * 255).astype(np.uint8), "RGBA")

# Paste onto truck door
px = int(W * DOOR_CX) - logo_px // 2
py = int(H * DOOR_CY) - logo_px // 2
truck.paste(painted, (px, py), painted)

truck.convert("RGB").save(OUT, "JPEG", quality=92, optimize=True)
print(f"Saved -> {OUT}  ({W}x{H} source, logo {logo_px}px at ({px},{py}))")
