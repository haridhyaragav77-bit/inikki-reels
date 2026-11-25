"""The brief builds for every run, with a fake Drive and no keys (24 Nov 2026: the refresh brief crashed twice on
23 Nov because a new trailer was in the library). Also checks that an empty slot is filled at post time.
Run: python -m tests.test_brief"""
import datetime as dt
import json
import shutil
import sys
import tempfile
from pathlib import Path

from tests.test_control_room import FakeDrive, check
from engine import brief, post, status
from engine.control import Control
from engine.day import Bank, Day
from engine.settings import ROOT


def brief_runs():
    tmp = Path(tempfile.mkdtemp())
    shutil.copytree(ROOT / "data", tmp / "data")
    brief.OUT = tmp / "data"                           # nothing in the repository's data/ is touched
    date = status.now().date().isoformat()
    d = FakeDrive()
    d.write_json("clip-library", "index.json", {"trailers": [{"film": "Test Film", "kind": "trailer", "sheet": "t.jpg",
                                                              "fetched": date, "shots": []}], "stills": []})
    for run in ("plan", "refresh", "breaking", "weekly", "monthly"):
        try:
            brief.build(d, run, date)
            text = (tmp / "data" / "brief.md").read_text(encoding="utf-8")
            check(text.startswith(f"# Brief · {run} run · {date}"), f"brief for the {run} run builds")
        except Exception as e:
            check(False, f"brief for the {run} run builds ({type(e).__name__}: {e})")
    shutil.rmtree(tmp, ignore_errors=True)


def empty_slot_fill():
    d = FakeDrive()
    ctl = Control(d)
    now = status.now().replace(hour=11, minute=2, second=0, microsecond=0)
    day, bank = Day(d, now.date().isoformat()), Bank(d)
    day.upsert("upd-0830", series="movie-updates", slot="08:30", post_at=now.replace(hour=8, minute=30).isoformat(), state="posted")
    bank.upsert("bank-kaithi", series="film-breakdown", state="ready", drive_reel="folder1")
    r = post.fill_empty_slot(day, bank, now, ctl, times=["08:30", "11:00", "12:30"])
    check(r and r["reel_id"] == "bank-kaithi" and r["slot"] == "11:00", "an empty 11:00 slot is filled from the bank")
    check(post.fill_empty_slot(day, bank, now, ctl, times=["08:30", "11:00", "12:30"]) is None, "a filled slot is not filled twice")
    later = now.replace(hour=12, minute=31)
    day.upsert("res-1", series="movie-updates", reserve=True, state="ready", drive_reel="folder2")
    r = post.fill_empty_slot(day, bank, later, ctl, times=["08:30", "11:00", "12:30"])
    check(r and r["reel_id"] == "res-1" and not r.get("reserve"), "a ready reserve fills an empty slot before the bank")
    check(post.fill_empty_slot(day, bank, now.replace(hour=15), ctl, times=["11:00"]) is None, "a slot over an hour old is left alone")
    # the Control Room's preview names the same reel the post job will use (24 Nov, Harish)
    d2 = FakeDrive()
    day2, bank2 = Day(d2, now.date().isoformat()), Bank(d2)
    day2.upsert("upd-0830", series="movie-updates", slot="08:30", state="posted")
    bank2.upsert("bank-a", series="film-breakdown", state="ready", drive_reel="fa", hook="A")
    bank2.upsert("bank-b", series="film-breakdown", state="ready", drive_reel="fb", hook="B")
    early = now.replace(hour=9, minute=0)
    pv = post.fill_preview(day2, bank2, ctl, early, times=["08:30", "11:00", "12:30", "18:00"])
    check([(x["time"], x["id"]) for x in pv] == [("11:00", "bank-a"), ("12:30", "bank-b"), ("18:00", None)],
          "the preview lists each empty slot with its own bank reel, and says when nothing is left")
    at11 = post.fill_empty_slot(day2, bank2, now.replace(hour=11, minute=1), ctl, times=["08:30", "11:00", "12:30", "18:00"])
    check(at11 and at11["reel_id"] == pv[0]["id"], "at 11:00 the post job uses the reel the preview showed")
    from engine import panel
    P = {"updated": "x", "switch": "run", "phase": "live", "approval": "autopilot", "today": {"date": "d", "reels": []},
         "tomorrow": {"slots": []}, "bank": {"ready": 1, "reels": [{"id": "bank-b", "series": "film-breakdown", "hook": "B"}]},
         "fills": pv[1:], "schedule": []}
    t = panel.text(P)
    check("SLOTS WITH NO PLAN" in t and "bank-b" in t and "nothing to fill it" in t, "the panel text shows the empty slots and the bank reels")


def fresh_first():
    """Harish, 25 Nov: reels made today post before reserves and the bank; a reserve of another series comes last."""
    d = FakeDrive()
    ctl = Control(d)
    now = status.now().replace(hour=20, minute=1, second=0, microsecond=0)
    at = lambda h, m=0: now.replace(hour=h, minute=m).isoformat()
    day, bank = Day(d, now.date().isoformat()), Bank(d)
    day.upsert("bd-2000", series="film-breakdown", slot="20:00", post_at=at(20), state="failed")
    day.upsert("res-upd", series="movie-updates", reserve=True, state="ready", drive_reel="r1")
    bank.upsert("bank-old", series="film-breakdown", state="ready", drive_reel="b1")
    r = post.choose(day, bank, now, ctl)
    check(r and r["reel_id"] == "bank-old", "a failed breakdown's slot goes to a breakdown (bank), not an update reserve")
    d = FakeDrive()
    day, bank = Day(d, now.date().isoformat()), Bank(d)
    day.upsert("bd-2000", series="film-breakdown", slot="20:00", post_at=at(20), state="held")
    day.upsert("bd-1230", series="film-breakdown", slot="12:30", post_at=at(12, 30), state="ready", drive_reel="f1")
    day.upsert("res-bd", series="film-breakdown", reserve=True, state="ready", drive_reel="r2")
    bank.upsert("bank-old", series="film-breakdown", state="ready", drive_reel="b1")
    r = post.choose(day, bank, now, ctl)
    check(r and r["reel_id"] == "bd-1230", "a reel made today that missed its time beats the reserve and the bank")
    check(day.get("bd-2000")["state"] == "skipped", "the held reel's slot is taken, and it is marked skipped")
    day.upsert("res-bd2", series="film-breakdown", reserve=True, state="ready", drive_reel="r3")
    kind, x = post.pick_filler(day, bank, "21:30", series="film-breakdown", now=now)
    check(kind == "reserve" and x["series"] == "film-breakdown", "with no missed fresh reel, a reserve of the same series comes next")
    d = FakeDrive()
    day, bank = Day(d, now.date().isoformat()), Bank(d)
    bank.upsert("bank-short", series="film-breakdown", state="ready", drive_reel="b1", seconds=43.0)
    bank.upsert("bank-long", series="film-breakdown", state="ready", drive_reel="b2", seconds=47.0)
    kind, x = post.pick_filler(day, bank, "20:00", series="film-breakdown", now=now)
    check(x and x["reel_id"] == "bank-long", "a saved breakdown under the 45 s floor is never used")


if __name__ == "__main__":
    brief_runs()
    empty_slot_fill()
    fresh_first()
    print("all ok" if not check.failed else f"{check.failed} failed")
    sys.exit(1 if check.failed else 0)
