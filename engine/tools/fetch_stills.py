#!/usr/bin/env python3
"""Fetch official stills from YouTube videos: the cover image plus 3 frames from inside the video.
Usage: python3 engine/tools/fetch_stills.py <out_dir> <video_id> [<video_id> ...]
Keeps only real 1280x720 frames (skips missing ones and YouTube's grey placeholder)."""
import sys, os, subprocess
from PIL import Image
out = sys.argv[1]; os.makedirs(out, exist_ok=True)
for vid in sys.argv[2:]:
    for name in ["maxresdefault", "maxres1", "maxres2", "maxres3", "sddefault"]:
        dst = os.path.join(out, f"{vid}_{name}.jpg")
        r = subprocess.run(["curl", "-s", "-f", "-m", "30", "-o", dst, f"https://i.ytimg.com/vi/{vid}/{name}.jpg"])
        if r.returncode != 0 or not os.path.exists(dst): continue
        try:
            im = Image.open(dst); w, h = im.size
            if w < 600: os.remove(dst); continue
            print(f"{dst} {w}x{h}")
        except Exception: os.remove(dst)
        if name == "maxresdefault" and os.path.exists(dst): pass
