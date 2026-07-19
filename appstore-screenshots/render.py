#!/usr/bin/env python3
"""
Readori App Store Screenshot Renderer
======================================
Renders all 8 App Store screenshots from index.html to 1284×2778 PNG files.

Usage:
  1. Place raw phone screenshots into screenshots/ folder:
       01-library.png          (Library / bookshelf grid)
       02-explore.png          (Explore tab)
       03-reading-settings.png (In-reader settings panel)
       04-reading-experience.png (Reading Experience page)
       05-pro.png              (Pro features page)
       06-import.png           (Import Sources page)
       07-settings.png         (Main Settings page)
       08-personalization.png  (Personalization page)

  2. Run:  python render.py

  3. Output PNGs land in output/ folder, ready to upload.

Requirements:
  pip install playwright
  playwright install chromium
"""

import sys
import os
import asyncio
from pathlib import Path

# ---------- CONFIG ----------
SCRIPT_DIR = Path(__file__).resolve().parent
HTML_PATH  = SCRIPT_DIR / "index.html"
OUTPUT_DIR = SCRIPT_DIR / "output"
FRAME_W    = 1284
FRAME_H    = 2778
NUM_FRAMES = 8

NAMES = [
    "01-library",
    "02-explore",
    "03-reading-settings",
    "04-reading-experience",
    "05-pro",
    "06-import",
    "07-settings",
    "08-personalization",
]

# Also generate 1242x2688 variants (6.5" display)
ALSO_65_INCH = True
ALT_W = 1242
ALT_H = 2688


async def render():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print("ERROR: playwright not installed.")
        print("  pip install playwright")
        print("  playwright install chromium")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    alt_dir = OUTPUT_DIR / "6.5-inch"
    if ALSO_65_INCH:
        alt_dir.mkdir(parents=True, exist_ok=True)

    html_url = HTML_PATH.as_uri()
    print(f"Rendering from: {html_url}")
    print(f"Output to:      {OUTPUT_DIR}")
    print()

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        # Use exact device pixel ratio = 1 so dimensions are pixel-perfect
        context = await browser.new_context(
            viewport={"width": FRAME_W, "height": FRAME_H},
            device_scale_factor=1,
        )
        page = await context.new_page()
        await page.goto(html_url, wait_until="networkidle")
        # Wait for images to load
        await page.wait_for_timeout(2000)

        for i in range(NUM_FRAMES):
            frame_id = f"frame-{i}"
            name = NAMES[i]

            # Scroll the frame into view
            frame = page.locator(f"#{frame_id}")
            await frame.scroll_into_view_if_needed()
            await page.wait_for_timeout(300)

            # Get bounding box
            box = await frame.bounding_box()
            if not box:
                print(f"  SKIP {name}: frame not found")
                continue

            # Clip to exact frame dimensions
            clip = {
                "x": box["x"],
                "y": box["y"],
                "width": FRAME_W,
                "height": FRAME_H,
            }

            out_path = OUTPUT_DIR / f"{name}.png"
            await page.screenshot(path=str(out_path), clip=clip)
            size_kb = out_path.stat().st_size / 1024
            print(f"  ✓ {name}.png  ({size_kb:.0f} KB)")

            # --- Optional 6.5" variant via resize ---
            if ALSO_65_INCH:
                try:
                    from PIL import Image
                    img = Image.open(out_path)
                    img_resized = img.resize((ALT_W, ALT_H), Image.LANCZOS)
                    alt_path = alt_dir / f"{name}.png"
                    img_resized.save(str(alt_path), "PNG")
                    print(f"    → 6.5-inch/{name}.png  ({alt_path.stat().st_size / 1024:.0f} KB)")
                except ImportError:
                    pass  # PIL not available, skip 6.5" variant

        await browser.close()

    print()
    print(f"Done! {NUM_FRAMES} screenshots in {OUTPUT_DIR}")
    if ALSO_65_INCH:
        print(f"6.5\" variants in {alt_dir}")


if __name__ == "__main__":
    asyncio.run(render())
