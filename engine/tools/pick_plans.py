#!/usr/bin/env python3
"""Which plans the "Make reels" job renders: a pattern given by hand, else the approved reference set.
Only plans in the approved looks (AGENT.md 6.6); the daily "make" job makes everything else. No AI."""
import glob
import json
import sys

LOOKS = {"stage", "bulletin", "poster-wall", "verdict", "flash"}
pattern = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() else "plans/reference/*.json"
out = []
for f in sorted(glob.glob(pattern, recursive=True)):
    try:
        with open(f, encoding="utf-8") as fh:
            if json.load(fh).get("template") in LOOKS:
                out.append(f)
    except (OSError, ValueError):
        continue
print("\n".join(out))
