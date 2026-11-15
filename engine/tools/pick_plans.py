#!/usr/bin/env python3
"""Which plans the "Make reels" job renders: a pattern given by hand, else the approved reference set.
Only plans in the approved looks (AGENT.md 6.6); the daily "make" job makes everything else. No AI.

    pick_plans.py "<pattern>" [changed-files.txt]

With a list of changed files (the golden test after a push): when every change sits inside single looks' own folders
(templates/<look>/...), only the reference reels of those looks are made again. Any other change (shared drawing code,
engine/render/, this file, the workflow) still makes the whole set. Fewer runner minutes, the same check."""
import glob
import json
import os
import sys

LOOKS = {"stage", "bulletin", "poster-wall", "verdict", "flash"}
pattern = sys.argv[1].strip() if len(sys.argv) > 1 and sys.argv[1].strip() else "plans/reference/*.json"


def only_looks(path):
    """The looks a push touched, or None when the whole set must be made."""
    try:
        with open(path, encoding="utf-8") as fh:
            files = [x.strip() for x in fh if x.strip()]
    except OSError:
        return None
    touched = set()
    for f in files:
        parts = f.split("/")
        if len(parts) >= 3 and parts[0] == "templates" and parts[1] in LOOKS:
            touched.add(parts[1])
        elif parts[0] in ("templates", "engine", ".github"):
            return None
    return touched or None


if len(sys.argv) > 2 and os.environ.get("GITHUB_EVENT_NAME", "push") == "push":
    LOOKS = only_looks(sys.argv[2]) or LOOKS
out = []
for f in sorted(glob.glob(pattern, recursive=True)):
    try:
        with open(f, encoding="utf-8") as fh:
            if json.load(fh).get("template") in LOOKS:
                out.append(f)
    except (OSError, ValueError):
        continue
print("\n".join(out))
