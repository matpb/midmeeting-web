#!/usr/bin/env python3
"""Crop, assert, and diff-check the OG card renders. Called by build.sh."""
import sys
from PIL import Image

def crop_and_check(src_path, dst_path, target_size=400_000):
    im = Image.open(src_path).convert("RGB")
    w, h = im.size
    if w < 1200 or h < 630:
        raise SystemExit(f"{src_path}: render too small {w}x{h}")
    cropped = im.crop((0, 0, 1200, 630))
    assert cropped.size == (1200, 630), f"bad crop size {cropped.size}"

    # Domain text sits around x 900-1150, y 550-595; must not be flat bg.
    band = cropped.crop((900, 550, 1150, 595))
    colors = band.getcolors(maxcolors=100000)
    distinct = len(colors) if colors else 0
    bg = cropped.getpixel((5, 5))
    non_bg = sum(c for c, col in (colors or []) if _dist(col, bg) > 12)
    if distinct < 3 or non_bg < 50:
        raise SystemExit(
            f"{src_path}: bottom-band check failed (distinct={distinct}, "
            f"non_bg_px={non_bg}) -- crop likely cut off the domain row"
        )

    cropped.save(dst_path, format="PNG", optimize=True)
    size = _shrink_if_needed(dst_path, target_size)
    print(f"OK {dst_path}: 1200x630, {size} bytes, bottom-band distinct={distinct} non_bg={non_bg}")
    return size

def _dist(a, b):
    return sum(abs(x - y) for x, y in zip(a, b))

def _shrink_if_needed(path, target_size):
    import os
    size = os.path.getsize(path)
    if size <= target_size:
        return size
    im = Image.open(path).convert("RGB")
    for colors in (256, 192, 128):
        q = im.quantize(colors=colors, method=Image.MEDIANCUT)
        q.save(path, format="PNG", optimize=True)
        size = os.path.getsize(path)
        if size <= target_size:
            return size
    return size

def diff_substantial(path_a, path_b, min_diff_fraction=0.02):
    a = Image.open(path_a).convert("RGB")
    b = Image.open(path_b).convert("RGB")
    if a.size != b.size:
        return True
    wa, ha = a.size
    pa = a.load()
    pb = b.load()
    diff_px = 0
    step = 3
    sampled = 0
    for y in range(0, ha, step):
        for x in range(0, wa, step):
            sampled += 1
            if _dist(pa[x, y], pb[x, y]) > 24:
                diff_px += 1
    frac = diff_px / sampled if sampled else 0
    return frac, frac >= min_diff_fraction

if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "crop":
        crop_and_check(sys.argv[2], sys.argv[3])
    elif cmd == "diff":
        frac, ok = diff_substantial(sys.argv[2], sys.argv[3])
        print(f"diff_fraction={frac:.4f} substantial={ok}")
        if not ok:
            raise SystemExit(f"font render did not differ enough from fallback: {frac:.4f}")
    elif cmd == "assertsize":
        im = Image.open(sys.argv[2])
        assert im.size == (1200, 630), f"{sys.argv[2]} is {im.size}"
        print(f"{sys.argv[2]}: {im.size[0]}x{im.size[1]}")
    else:
        raise SystemExit(f"unknown command {cmd}")
