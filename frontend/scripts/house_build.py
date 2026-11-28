"""Builds the default house pictures for the screen Stroom: assets/house-3.webp and house-2.webp.

Needs rsvg-convert and Pillow. Run from frontend/: python3 scripts/house_build.py
"""

import os
import subprocess
import sys
import tempfile

from PIL import Image

here = os.path.dirname(os.path.abspath(__file__))
for storeys in (3, 2):
    with tempfile.TemporaryDirectory() as tmp:
        svg, png = os.path.join(tmp, "h.svg"), os.path.join(tmp, "h.png")
        subprocess.run([sys.executable, os.path.join(here, "house_gen.py"), svg, str(storeys)], check=True)
        subprocess.run(["rsvg-convert", svg, "-o", png], check=True)
        Image.open(png).convert("RGBA").save(os.path.join(here, "..", "assets", f"house-{storeys}.webp"), "WEBP", quality=88, method=6)
