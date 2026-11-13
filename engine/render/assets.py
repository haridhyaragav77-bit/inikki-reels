#!/usr/bin/env python3
"""Make sure every still a plan uses is on disk, so any cloud machine can render any plan. No AI.

A still named <youtube_id>_<frame>.jpg is fetched from YouTube's official frames (cover + 3 frames from inside
the video). Other stills say where they come from in the plan:
  "fetch": {"youtube": "<id>", "frame": "maxresdefault"}   or   "fetch": {"url": "https://..."}
  "prep":  {"crop_px": [x0, y0, x1, y1], "scale": 2, "resize": [w, h], "sharpen": true}
Usage: python3 engine/render/assets.py plan.json
"""
import sys, os, re, json, subprocess, tempfile
from PIL import Image, ImageFilter
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UA = "iNiKKiReels/1.0 (reel engine)"


def get(url, out):
    subprocess.run(["curl", "-s", "-f", "-L", "-m", "60", "-A", UA, "-o", out, url], check=True)


def main(plan_path):
    plan = json.load(open(plan_path, encoding="utf-8"))
    made = []
    for key, a in plan.get("assets", {}).items():
        dst = os.path.join(ROOT, a["src"])
        if os.path.exists(dst):
            continue
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        f = a.get("fetch")
        if not f:
            m = re.match(r"(.+?)_(maxresdefault|maxres[123]|sddefault|hqdefault)\.jpg$", os.path.basename(dst))
            if not m:
                raise SystemExit(f"asset '{key}' is missing and has no 'fetch' rule: {a['src']}")
            f = {"youtube": m.group(1), "frame": m.group(2)}
        tmp = tempfile.mktemp(suffix=".jpg")
        get(f"https://i.ytimg.com/vi/{f['youtube']}/{f.get('frame', 'maxresdefault')}.jpg" if "youtube" in f else f["url"], tmp)
        im = Image.open(tmp).convert("RGB")
        p = a.get("prep", {})
        if "crop_px" in p:
            im = im.crop(tuple(p["crop_px"]))
        if "scale" in p:
            im = im.resize((int(im.width * p["scale"]), int(im.height * p["scale"])), Image.LANCZOS)
        if "resize" in p:
            im = im.resize(tuple(p["resize"]), Image.LANCZOS)
        if p.get("sharpen"):
            im = im.filter(ImageFilter.UnsharpMask(radius=2, percent=85, threshold=2))
        im.save(dst, quality=93); os.remove(tmp); made.append(key)
    print(json.dumps({"ok": True, "fetched": made}))


if __name__ == "__main__":
    main(sys.argv[1])
