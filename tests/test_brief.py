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


if __name__ == "__main__":
    brief_runs()
    empty_slot_fill()
    print("all ok" if not check.failed else f"{check.failed} failed")
    sys.exit(1 if check.failed else 0)
