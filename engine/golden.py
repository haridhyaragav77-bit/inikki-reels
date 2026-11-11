"""Golden check (CLAUDE.md rules 2 and 3): the same plan must give the same picture, every time.

    python -m engine.golden                      every plan in plans/reference, with stand-in pictures
    python -m engine.golden plans/x.json ...     chosen plans

For each plan it draws three frames in two separate browser sessions and compares them exactly.
Run it after any template change, before the golden reels are re-rendered."""
import glob
import hashlib
import json
import sys

from .brandkit import kit
from .settings import OUT, ROOT
from . import render as R


def check(plan_path):
    with open(plan_path, encoding="utf-8") as f:
        plan = json.load(f)
    res, template = R.resolve(plan, str(OUT / "work" / ("golden-" + plan["reel_id"])), True)
    brand = kit(plan.get("brand"))
    sums = []
    for _ in range(2):
        fr = R.Frames(template)
        try:
            total = float(fr.setup(res, brand)["total"])
            sums.append([hashlib.sha256(fr.frame(total * k, "png")).hexdigest()[:16] for k in (0.11, 0.52, 0.93)])
        finally:
            fr.close()
    return sums[0] == sums[1], template, sums


def main():
    plans = [a for a in sys.argv[1:]] or sorted(glob.glob(str(ROOT / "plans" / "reference" / "*.json")))
    bad = 0
    for p in plans:
        ok, template, sums = check(p)
        print(f"{p} ({template}): {'same picture both times' if ok else 'PICTURES DIFFER ' + json.dumps(sums)}")
        bad += not ok
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
