"""Runner-minute savings must not change what is posted or when (AGENT.md 15.3, 15 Nov 2026).
Run: python -m tests.test_minutes   (no keys, nothing fetched, nothing posted)"""
import datetime as dt
import subprocess
import sys
import tempfile

from engine import panel, post, status
from engine.control import Control
from engine.day import Bank, Day
from tests.test_control_room import FakeDrive


class RealishDrive(FakeDrive):
    """FakeDrive with the two calls of the real Drive that the panel's read-once wrapper uses, and a count of fetches."""
    def __init__(self):
        super().__init__()
        self.fetches, self.searches = 0, 0

    def _is_mine(self, item):
        return False

    def find_child(self, parent_id, name, mime=None):
        self.searches += 1
        return self.find(parent_id, name)

    def read_bytes(self, file_id):
        self.fetches += 1
        return super().read_bytes(file_id)


def main():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("ok   " if cond else "FAIL ") + name)

    drive = FakeDrive()
    ctl = Control(drive, relay=False)
    slots = post.slots(ctl)
    check("there are slots to test with", len(slots) >= 2)
    base = status.now().replace(hour=12, minute=0, second=0, microsecond=0)
    at = lambda hm, day=0: (base + dt.timedelta(days=day)).replace(hour=int(hm[:2]), minute=int(hm[3:]))

    # --- is the clock alive? (decides whether GitHub's late timer waits for a slot or leaves it to the clock)
    s1, s2 = slots[0], slots[1]
    now = at(s2) - dt.timedelta(minutes=10)                      # 10 minutes before the second slot
    check("newest passed slot is found", post.last_slot_before(ctl, now) == at(s1))
    check("early morning: the newest passed slot is yesterday's last", post.last_slot_before(ctl, at(s1) - dt.timedelta(minutes=30)) == at(slots[-1], -1))
    check("clock ticked at the last slot: alive", post.clock_alive({"post_tick": (at(s1) + dt.timedelta(seconds=40)).isoformat()}, ctl, now))
    check("clock missed the last slot: not alive", not post.clock_alive({"post_tick": (at(s1) - dt.timedelta(hours=2)).isoformat()}, ctl, now))
    check("nothing known about the clock: not alive (full backstop)", not post.clock_alive({}, ctl, now))
    check("unreadable clock note: not alive", not post.clock_alive({"post_tick": "soon"}, ctl, now))

    # --- waiting: only when the clock is missing its times; never post a coming slot early when leaving it to the clock
    slept, real_now, real_sleep = [], status.now, post.time.sleep
    status.now = lambda: now
    post.time.sleep = lambda s: slept.append(s)
    try:
        check("clock alive: no waiting, and the coming reel is left alone", post.wait_for_slot(ctl, alive=True) == 0 and not slept)
        check("clock missing: waits for the slot as before", post.wait_for_slot(ctl, alive=False) == 5 and slept and abs(slept[0] - 600) < 2)
        status.now = lambda: at(s1) + dt.timedelta(minutes=25)
        slept.clear()
        check("no slot close: no waiting either way", post.wait_for_slot(ctl, alive=False) == 5 and post.wait_for_slot(ctl, alive=True) == 5 and not slept)
    finally:
        post.time.sleep = real_sleep

    # --- choose(): the same reel as before; with early_min=0 a reel 4 minutes ahead is not taken
    status.now = real_now
    n = status.now()
    day, bank = Day(drive), Bank(drive)
    day.upsert("soon", state="ready", post_at=(n + dt.timedelta(minutes=4)).isoformat(timespec="seconds"), slot="x")
    check("a reel due in 4 minutes is taken (as before)", (post.choose(day, bank, n, ctl) or {}).get("reel_id") == "soon")
    check("...but not by a run that leaves the slot to the clock", post.choose(day, bank, n, ctl, early_min=0) is None)
    day.upsert("late", state="ready", post_at=(n - dt.timedelta(hours=2, minutes=50)).isoformat(timespec="seconds"), slot="y")
    check("a reel 2 h 50 min late is still posted by a late run", (post.choose(day, bank, n, ctl, early_min=0) or {}).get("reel_id") == "late")
    day.upsert("late", post_at=(n - dt.timedelta(hours=3, minutes=10)).isoformat(timespec="seconds"))
    check("a reel more than 3 hours late is not (unchanged rule)", post.choose(day, bank, n, ctl, early_min=0) is None)

    # --- the news watch is not repeated minutes later, but never skipped at the next slot
    check("no watch on record: watch runs", post.watch_due({}, n))
    check("watch 10 minutes ago: not repeated", not post.watch_due({"watch_at": (n - dt.timedelta(minutes=10)).isoformat()}, n))
    gaps = [(at(b) - at(a)).total_seconds() / 60 for a, b in zip(slots, slots[1:])]
    gap = float((post._post_cfg()).get("watch_gap_minutes", 50))
    check(f"the gap ({gap:.0f} min) is shorter than the shortest gap between slots ({min(gaps):.0f} min): every slot still watches", gap < min(gaps))

    # --- the early upload is used only for the very same reel, and only while Instagram keeps it
    r = {"reel_id": "a", "drive_reel": "F1", "made_at": "2026-11-15T06:00:00+05:30", "caption": "one", "cover_t": 1.2, "trial": None}
    r["ig_prepared"] = {"id": "C1", "at": (n - dt.timedelta(hours=5)).isoformat(), "key": post.prep_key(r)}
    check("same reel, 5 hours old: the early upload is used", post.prep_usable(r, n) == "C1")
    check("words changed: uploaded afresh", post.prep_usable(dict(r, caption="two"), n) is None)
    check("made again (same Drive file): uploaded afresh", post.prep_usable(dict(r, made_at="2026-11-15T09:00:00+05:30"), n) is None)
    check("cover moment changed: uploaded afresh", post.prep_usable(dict(r, cover_t=2.0), n) is None)
    check("older than Instagram keeps it: uploaded afresh", post.prep_usable(dict(r, ig_prepared=dict(r["ig_prepared"], at=(n - dt.timedelta(hours=21)).isoformat())), n) is None)
    check("no early upload: uploaded at the slot as before", post.prep_usable({k: v for k, v in r.items() if k != "ig_prepared"}, n) is None)
    check("a reel with no slot is not uploaded early", post.prepare(drive, day, "nobody") is None)

    # --- the panel reads each Drive file once, finds them with one listing, and shows the same thing
    d2 = RealishDrive()
    d2.write_json("status", "minutes.json", {"minutes": 12, "limit": 2000})
    d2.write_json("status", "alerts.json", {"alerts": []})
    once = panel.Once(d2)
    a, b = once.read_json("status", "minutes.json"), once.read_json("status", "minutes.json")
    check("read once, same answer twice", a == b == {"minutes": 12, "limit": 2000} and d2.fetches == 1)
    once.read_json("status", "alerts.json")
    check("a folder's files are found with one listing, not one search each", d2.searches == 0)
    check("a missing file gives the default", once.read_json("status", "nope.json", {"x": 1}) == {"x": 1} and once.read_text("status", "nope.txt", "d") == "d")
    P1, P2 = panel.build(FakeDrive(), Control(FakeDrive(), relay=False)), panel.build(d2, Control(d2, relay=False))
    check("the panel is built through the read-once Drive and has the same parts", set(P1) == set(P2) and P2["usage"] is not None)

    # --- golden test: only the looks a push touched; anything shared makes the whole set
    def picked(changed):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("\n".join(changed))
        out = subprocess.run([sys.executable, "engine/tools/pick_plans.py", "", f.name], capture_output=True, text=True, env={"GITHUB_EVENT_NAME": "push", "PATH": ""}).stdout
        return [x for x in out.split("\n") if x]
    whole = [x for x in subprocess.run([sys.executable, "engine/tools/pick_plans.py", ""], capture_output=True, text=True).stdout.split("\n") if x]
    one = picked(["templates/bulletin/template.js"])
    check("a change inside one look makes only that look's reference reels", 0 < len(one) < len(whole) and set(one) < set(whole))
    check("a change to shared drawing code makes the whole set", picked(["templates/bulletin/template.js", "templates/_shared/page.html"]) == whole)
    check("a change to the render engine makes the whole set", picked(["engine/render/render.mjs"]) == whole)
    check("no list of changes makes the whole set", whole and picked([]) == whole)

    print("\nALL OK" if ok else "\nSOMETHING FAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
