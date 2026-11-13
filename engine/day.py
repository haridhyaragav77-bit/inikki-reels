"""One day's reels and where each one stands (AGENT.md 13, 16): Drive status/days/<date>.json, copied to status/today.json
for the Control Room. States: planned → rendering → ready → posted (or rehearsed), or held / failed / skipped, with a reason.

Make and Post can run at the same time, so saving re-reads the file and writes back only the reels this run touched."""
import datetime as dt
import json

from . import status

STATES = ("planned", "rendering", "ready", "rehearsed", "posted", "held", "failed", "skipped")


def today():
    return status.now().strftime("%Y-%m-%d")


class Ledger:
    """A small list of records in one Drive JSON file, keyed by reel_id, safe to save from two jobs at once."""
    def __init__(self, drive, folder, name, empty=None):
        self.drive, self.folder, self.name = drive, folder, name
        self.empty = empty or {"reels": []}
        self.data = self._load()
        self.dirty = set()

    def _load(self):
        d = None
        if self.drive:
            try:
                d = self.drive.read_json(self.folder, self.name)
            except Exception:
                d = None
        d = d or json.loads(json.dumps(self.empty))
        d.setdefault("reels", [])
        return d

    def get(self, reel_id):
        return next((r for r in self.data["reels"] if r["reel_id"] == reel_id), None)

    def upsert(self, reel_id, **fields):
        r = self.get(reel_id)
        if not r:
            r = {"reel_id": reel_id}
            self.data["reels"].append(r)
        r.update({k: v for k, v in fields.items() if v is not None or k == "reason"})
        r["updated"] = status.now().isoformat(timespec="seconds")
        self.dirty.add(reel_id)
        return r

    def reels(self, *states):
        return [r for r in self.data["reels"] if not states or r.get("state") in states]

    def _merged(self):
        fresh = self._load()
        mine = {r["reel_id"]: r for r in self.data["reels"] if r["reel_id"] in self.dirty}
        out = [mine.pop(r["reel_id"], r) for r in fresh["reels"]] + list(mine.values())
        fresh["reels"] = sorted(out, key=lambda r: (r.get("post_at") or "9", r["reel_id"]))
        return fresh

    def save(self, local_name=None):
        self.data = self._merged() if self.drive else self.data
        self.data["updated"] = status.stamp()
        status.local_write(local_name or self.name.replace("/", "-"), self.data)
        if self.drive:
            self.drive.write_json(self.folder, self.name, self.data)
        return self.data


class Day(Ledger):
    def __init__(self, drive, date=None):
        self.date = date or today()
        super().__init__(drive, "status/days", f"{self.date}.json", {"date": self.date, "reels": []})

    def save(self):
        d = super().save(f"day-{self.date}.json")
        if self.drive and self.date == today():
            self.drive.write_json("status", "today.json", d)
        return d


class Bank(Ledger):
    """Breakdown reels made ahead of time (AGENT.md 6.2, bank_target). Used when a breakdown slot has nothing ready."""
    def __init__(self, drive):
        super().__init__(drive, "status", "bank.json")


def slot_time(plan, date):
    """When a plan should post, as an aware datetime (IST). From post_at, or from its slot "HH:MM" on that date."""
    tz = status.IST
    if plan.get("post_at"):
        try:
            t = dt.datetime.fromisoformat(plan["post_at"])
            return t if t.tzinfo else t.replace(tzinfo=tz)
        except ValueError:
            pass
    if plan.get("slot"):
        h, m = (int(x) for x in str(plan["slot"]).split(":"))
        d = dt.date.fromisoformat(date)
        return dt.datetime(d.year, d.month, d.day, h, m, tzinfo=tz)
    return None


def load_json_lines(text):
    out = []
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out
