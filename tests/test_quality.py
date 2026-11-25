"""26 Nov 2026 (Harish): a motion floor in the plan check that holds whatever model writes the plan, every reel posted
as a Trial Reel (non-followers first), and a safe cover frame. Run: python -m tests.test_quality   (no keys, no Drive)"""
import json
import sys

from engine import plancheck as PC
from engine import post as P
from tests.test_control_room import check


def floor(path, day="2026-11-26"):
    p = json.load(open(path, encoding="utf-8"))
    p["id"] = day + p["id"][10:]
    return PC.check_motion_floor(p, PC.series_of(p), p["screens"])


def main():
    PC.mirror = lambda: {}
    check(not floor("plans/2026-11-21/2026-11-21-update-suriya-643cr-year.json"), "the 21 Nov Suriya ₹643 Cr update passes the motion floor")
    e = floor("plans/2026-11-25/2026-11-25-update-suriya-failures-to-770cr.json")
    check(any("animated graphic" in x for x in e), "an update of three text cards is refused (no count-up, no bars)")
    check(any("money figure" in x for x in e), "a money figure typed on a title card is refused")
    check(not floor("plans/2026-11-23/2026-11-23-breakdown-dune-two-infrared.json"), "the 23 Nov Dune breakdown passes")
    check(any("sound hits" in x for x in floor("plans/2026-11-25/2026-11-25-breakdown-kaithi-one-night.json")), "a breakdown with one hit a screen is refused")
    check(not floor("plans/2026-11-25/2026-11-25-update-suriya-failures-to-770cr.json", "2026-11-25"), "plans before 26 Nov are not judged")

    P._post_cfg = lambda: {"trial_reels": {"on": True, "series": "all", "graduation": "SS_PERFORMANCE"}, "cover_fallback_s": 2.6}
    check(P.trial_of({"series": "movie-updates"}) == "SS_PERFORMANCE", "every reel goes to non-followers first")
    check(P.trial_of({"series": "movie-updates", "trial": False}) is None, "a plan can still say trial: false")
    P._post_cfg = lambda: {"trial_reels": {"on": False}}
    check(P.trial_of({"series": "movie-updates"}) is None, "trial reels switch off with on: false")
    check(P.thumb_ms({"cover_t": 2.58}) == 2580, "the cover time from the render is used")
    check(P.thumb_ms({"cover_t": 0}) == 2600 and P.thumb_ms({}) == 2600, "no cover time: late in the title screen, never 1 s")

    class IG:
        calls = []
        def create_reel(self, local, cap, thumb_offset_ms=None, trial=None):
            IG.calls.append(trial)
            if trial:
                raise RuntimeError("trial_params not allowed")
            return "c1"
    P._post_cfg = lambda: {"trial_reels": {"on": True}}
    cid, tr = P.create(IG(), "x.mp4", {"reel_id": "r", "series": "s"})
    check(cid == "c1" and tr is None and IG.calls == ["SS_PERFORMANCE", None], "if Instagram refuses a Trial Reel, it posts as a normal reel")
    return 1 if check.failed else 0


if __name__ == "__main__":
    sys.exit(main())
