"""26 Nov 2026 (Harish): every reel posted
as a Trial Reel (non-followers first), and a safe cover frame. Run: python -m tests.test_quality   (no keys, no Drive)"""
import sys

from engine import post as P
from tests.test_control_room import check


def main():
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
