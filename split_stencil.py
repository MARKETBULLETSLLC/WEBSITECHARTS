"""
Alpine Industries Logo — Stencil Separator
Splits the logo into 3 elements, each scaled to fill an 8.5x11 sheet at 300 DPI.

Usage:
    python split_stencil.py  <path-to-logo-image>

Output (saved next to the source file):
    stencil_1_trees.pdf / .png
    stencil_2_alpine_industries.pdf / .png
    stencil_3_roman_II.pdf / .png
"""

import sys
import os
from PIL import Image, ImageOps

# ── CONFIG ──────────────────────────────────────────────────────────────────
DPI = 300                       # print resolution
PAGE_W_IN, PAGE_H_IN = 8.5, 11 # inches
MARGIN_IN = 0.25                # white border kept around each element
THRESHOLD = 200                 # pixel value < this is considered "ink"

# Approximate horizontal split points as fractions of image width.
# Adjust if a crop catches the wrong element.
SPLIT_1 = 0.30   # end of trees  / start of text
SPLIT_2 = 0.865  # end of text   / start of II

# ── HELPERS ─────────────────────────────────────────────────────────────────

def load_gray(path):
    img = Image.open(path).convert("L")   # greyscale
    return img

def tight_bbox(gray_crop, threshold=THRESHOLD):
    """Return bounding box of all pixels darker than threshold."""
    mask = gray_crop.point(lambda p: 0 if p < threshold else 255)
    inv  = ImageOps.invert(mask)          # invert so ink = white for getbbox
    bbox = inv.getbbox()
    return bbox                           # (left, top, right, bottom) or None

def crop_to_content(gray_crop, threshold=THRESHOLD, pad_px=20):
    bbox = tight_bbox(gray_crop, threshold)
    if bbox is None:
        return gray_crop
    l, t, r, b = bbox
    l = max(0, l - pad_px)
    t = max(0, t - pad_px)
    r = min(gray_crop.width,  r + pad_px)
    b = min(gray_crop.height, b + pad_px)
    return gray_crop.crop((l, t, r, b))

def scale_to_page(gray_img, dpi=DPI,
                  page_w=PAGE_W_IN, page_h=PAGE_H_IN,
                  margin=MARGIN_IN):
    """
    Scale image to fill the printable area (page minus margins),
    preserving aspect ratio. Returns a white-background page image.
    """
    avail_w = int((page_w - 2 * margin) * dpi)
    avail_h = int((page_h - 2 * margin) * dpi)
    page_px_w = int(page_w * dpi)
    page_px_h = int(page_h * dpi)

    # Choose orientation that best fits the element
    iw, ih = gray_img.size
    aspect = iw / ih

    # Try portrait
    fit_w_p = avail_w
    fit_h_p = int(fit_w_p / aspect)
    if fit_h_p > avail_h:
        fit_h_p = avail_h
        fit_w_p = int(fit_h_p * aspect)
    area_portrait = fit_w_p * fit_h_p

    # Try landscape
    avail_lw = int((page_h - 2 * margin) * dpi)
    avail_lh = int((page_w - 2 * margin) * dpi)
    fit_w_l = avail_lw
    fit_h_l = int(fit_w_l / aspect)
    if fit_h_l > avail_lh:
        fit_h_l = avail_lh
        fit_w_l = int(fit_h_l * aspect)
    area_landscape = fit_w_l * fit_h_l

    if area_landscape > area_portrait:
        # use landscape
        page = Image.new("L", (page_px_h, page_px_w), 255)
        scaled = gray_img.resize((fit_w_l, fit_h_l), Image.LANCZOS)
        off_x = (page_px_h - fit_w_l) // 2
        off_y = (page_px_w - fit_h_l) // 2
    else:
        page = Image.new("L", (page_px_w, page_px_h), 255)
        scaled = gray_img.resize((fit_w_p, fit_h_p), Image.LANCZOS)
        off_x = (page_px_w - fit_w_p) // 2
        off_y = (page_px_h - fit_h_p) // 2

    page.paste(scaled, (off_x, off_y))
    return page

def save(page_img, base_path, name, dpi=DPI):
    png_path = base_path + name + ".png"
    pdf_path = base_path + name + ".pdf"
    page_img.save(png_path, dpi=(dpi, dpi))
    page_img.save(pdf_path, dpi=(dpi, dpi))
    print(f"  Saved: {png_path}")
    print(f"  Saved: {pdf_path}")

# ── MAIN ────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) < 2:
        print("Usage: python split_stencil.py <path-to-logo-image>")
        sys.exit(1)

    src = sys.argv[1]
    base = os.path.splitext(src)[0] + "_stencil_"

    print(f"Loading: {src}")
    gray = load_gray(src)
    W, H = gray.size
    print(f"  Image size: {W} x {H} px")

    x1 = int(W * SPLIT_1)
    x2 = int(W * SPLIT_2)

    # ── Element 1: Trees ──────────────────────────────────────────────────
    print("\n[1] Trees")
    region1 = gray.crop((0, 0, x1, H))
    crop1   = crop_to_content(region1)
    page1   = scale_to_page(crop1)
    save(page1, base, "1_trees")

    # ── Element 2: ALPINE INDUSTRIES text ────────────────────────────────
    print("\n[2] ALPINE INDUSTRIES text")
    region2 = gray.crop((x1, 0, x2, H))
    crop2   = crop_to_content(region2)
    page2   = scale_to_page(crop2)
    save(page2, base, "2_alpine_industries")

    # ── Element 3: Roman II ───────────────────────────────────────────────
    print("\n[3] Roman II")
    region3 = gray.crop((x2, 0, W, H))
    crop3   = crop_to_content(region3)
    page3   = scale_to_page(crop3)
    save(page3, base, "3_roman_II")

    print("\nDone. Open the PDFs and print at 'Actual Size' (no scaling).")

if __name__ == "__main__":
    main()
