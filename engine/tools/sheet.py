#!/usr/bin/env python3
"""Contact sheet of preview stills: python3 engine/tools/sheet.py <workdir> <out.jpg> [cols]"""
import sys, glob, os
from PIL import Image, ImageDraw
d, out = sys.argv[1], sys.argv[2]; cols = int(sys.argv[3]) if len(sys.argv) > 3 else 5
fs = sorted(glob.glob(os.path.join(d, "still_*.jpg")), key=lambda f: float(os.path.basename(f)[6:-4].replace("_", ".")))
w, h = 288, 512
rows = (len(fs) + cols - 1) // cols
s = Image.new("RGB", (cols * w, rows * (h + 22)), "black"); dr = ImageDraw.Draw(s)
for k, f in enumerate(fs):
    x, y = (k % cols) * w, (k // cols) * (h + 22)
    s.paste(Image.open(f).resize((w, h)), (x, y)); dr.text((x + 4, y + h + 4), os.path.basename(f)[6:-4].replace("_", ".") + " s", fill="yellow")
s.save(out, quality=82)
