"""Reviews and the release calendar (Harish, 22 Nov; AGENT.md 10.5): the score and the answer by code, trusted reviewers
only, date changes kept by code, reviews due and missed. Run: python -m tests.test_reviews   (no keys, no Drive)"""
import copy
import json
import sys
import tempfile
from pathlib import Path

from engine import plancheck as PC
from engine import releases as R
from tests.test_control_room import check


def main():
    PC.mirror = lambda: {}
    for k in ("quick", "trusted"):
        e = PC.check(json.load(open(f"plans/reference/review-{k}.json", encoding="utf-8")))[0]
        check(not e, f"the {k} reference passes" + (f" ({e[:2]})" if e else ""))
    base = json.load(open("plans/reference/review-trusted.json", encoding="utf-8"))

    def errs(fn):
        p = copy.deepcopy(base)
        fn(p)
        return " | ".join(PC.check(p)[0])

    check("works out to 3.7" in errs(lambda p: p["rating"].update(score=4.5)), "a made-up score is refused with the right number")
    check("means GO" in errs(lambda p: p["rating"].update(verdict="SKIP")), "the answer must follow the score")
    check("stars screen shows" in errs(lambda p: p["screens"][1].update(score=4.0)), "the stars screen must show the worked-out score")
    check("not on the list" in errs(lambda p: p["rating"]["critics"].append({"name": "Random Blogger", "outlet": "Blog", "stars": 5, "quote": "wow", "src": 0})),
          "a reviewer not on the trusted list is refused")
    check("at least 3 trusted" in errs(lambda p: p["rating"].update(critics=p["rating"]["critics"][:2])), "fewer than 3 trusted reviewers: wait")
    check("verbal" in errs(lambda p: p["rating"]["critics"][0].update(stars=None, verbal="amazing")), "a verbal word outside the scale is refused")
    check("'src'" in errs(lambda p: p["rating"]["critics"][0].pop("src")), "a review without its source link is refused")
    cfg = PC.critics_cfg()
    check(PC.verdict_for(3.5, cfg)["word"] == "GO" and PC.verdict_for(3.4, cfg)["word"] == "WAIT" and PC.verdict_for(2.4, cfg)["word"] == "SKIP",
          "3.5+ GO, 2.5-3.4 WAIT, below SKIP")
    check(PC.trusted_match("Bharadwaj Rangan", cfg) == "Baradwaj Rangan" and PC.trusted_match("TOI", cfg) == "The Times of India",
          "other spellings of a trusted reviewer are recognised")

    # the calendar: date changes recorded by code, reviews due and missed
    tmp = Path(tempfile.mkdtemp())
    R.SEEN = tmp / "seen.json"
    cal = [{"film": "Film A", "date": "2026-12-04"}, {"film": "Film B", "date": "2026-11-27"}]
    R.save(R.track(cal, "2026-11-22"))
    seen = R.track([{"film": "Film A", "date": "2026-12-11"}, cal[1]], "2026-11-24")
    h = seen["films"]["filma"]["history"]
    check(h and h[-1] == {"from": "2026-12-04", "to": "2026-12-11", "on": "2026-11-24"}, "a moved date is recorded with the day it changed")
    plans = [("movie-review", "2026-11-27", "2026-11-27-review-film-b", ["filmb"])]
    st = {r["film"]: r for r in R.status_of(cal, "2026-11-29", plans)}
    check(st["Film B"]["quick"] and st["Film B"]["trusted_state"] == "due", "day 2: Quick done, Trusted due")
    st = {r["film"]: r for r in R.status_of(cal, "2026-12-02", plans)}
    check(st["Film B"]["trusted_state"] == "missed", "after day 4: Trusted missed (an alert is raised)")
    st = {r["film"]: r for r in R.status_of([{"film": "Film C", "date": "2026-11-29"}], "2026-11-29", [])}
    check(st["Film C"]["quick_state"] == "due today", "release day: Quick due today")
    hs = R.hints([{"film": "Film A", "date": "2026-12-04"}], [{"title": "Film A release postponed to January"}, {"title": "Film A trailer out"}], "2026-11-24")
    check(len(hs) == 1 and "postponed" in hs[0], "a headline about a moved date is flagged; a trailer headline is not")
    print("\nALL PASSED" if not check.failed else f"\n{check.failed} FAILED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
