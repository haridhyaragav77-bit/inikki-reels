"""The metronome (AGENT.md 4.3, "The clock"): starts the Engine's timed jobs on time, with no Claude at all.

GitHub's own timer starts this repository's jobs hours late, so for a while a Claude chat ("the clock") sent one line
per tick. That chat re-read its whole conversation at every tick and became the biggest daily cost (23 Nov 2026: about
765,000 tokens a tick). This replaces it: one GitHub job that waits for each tick and starts the right workflow itself.
A run lasts at most about 5 h 50 min (GitHub's limit is 6 h); before it ends it starts the next run and hands over the
time it has covered, so no tick falls in the gap. GitHub's own (late) timer only restarts the chain if it ever breaks.

The ticks are the "clock" list in runs/renew/tasks.json (cron lines in India time): settings, not code.
    python tools/metronome.py --dry --hours 24        list the next day's ticks, start nothing
    python tools/metronome.py                          run (inside the metronome workflow)
"""
import argparse
import datetime as dt
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
RUN_MINUTES = 345            # hand over well before GitHub's 6-hour limit
LOOKBACK_MINUTES = 15        # a run started without a hand-over (GitHub's timer) catches ticks this recent


def field(spec, value, lo, hi):
    if spec == "*":
        return True
    for part in spec.split(","):
        if "/" in part:
            base, step = part.split("/")
            start = lo if base == "*" else int(base)
            if value >= start and (value - start) % int(step) == 0:
                return True
        elif "-" in part:
            a, b = part.split("-")
            if int(a) <= value <= int(b):
                return True
        elif int(part) == value:
            return True
    return False


def matches(cron, t):
    """A 5-field cron line (optionally prefixed with CRON_TZ=...) against a minute in India time."""
    parts = cron.split()
    if parts and parts[0].startswith("CRON_TZ="):
        parts = parts[1:]
    mi, ho, dom, mon, dow = parts
    return (field(mi, t.minute, 0, 59) and field(ho, t.hour, 0, 23) and field(dom, t.day, 1, 31)
            and field(mon, t.month, 1, 12) and field(dow, (t.weekday() + 1) % 7, 0, 6))


def ticks():
    """[(cron, workflow, job or None)] from runs/renew/tasks.json 'clock'."""
    out = []
    for e in json.loads((ROOT / "runs" / "renew" / "tasks.json").read_text(encoding="utf-8")).get("clock", []):
        words = str(e.get("prompt", "")).split()
        if len(words) >= 2 and words[0] == "TICK" and e.get("cron"):
            out.append((e["cron"], words[1], words[2] if len(words) > 2 else None))
    return out


def due(start, end, table):
    """Every tick strictly after start and up to end, in order."""
    t = start.replace(second=0, microsecond=0) + dt.timedelta(minutes=1)
    out = []
    while t <= end:
        out += [(t, wf, job) for cron, wf, job in table if matches(cron, t)]
        t += dt.timedelta(minutes=1)
    return out


def gh(*args):
    r = subprocess.run(["gh", "workflow", "run", *args, "--ref", os.environ.get("GITHUB_REF_NAME", "main")],
                       capture_output=True, text=True, timeout=60)
    return r.returncode == 0, (r.stderr or r.stdout or "").strip()[:160]


def start(wf, job):
    for attempt in range(3):
        ok, msg = gh(f"{wf}.yml", *(["-f", f"job={job}"] if job else []))
        if ok:
            return True, "started"
        time.sleep(20 * (attempt + 1))
    return False, msg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default="", help="ISO time the previous run covered up to (its hand-over)")
    ap.add_argument("--dry", action="store_true", help="list the ticks, start nothing")
    ap.add_argument("--hours", type=float, default=RUN_MINUTES / 60)
    a = ap.parse_args()
    now = dt.datetime.now(IST)
    since = dt.datetime.fromisoformat(a.since).astimezone(IST) if a.since else now - dt.timedelta(minutes=LOOKBACK_MINUTES)
    since = max(since, now - dt.timedelta(hours=2))          # never replay a long gap: a late post would be worse than none
    end = now + dt.timedelta(hours=a.hours)
    plan = due(since, end, ticks())
    print(f"metronome: {now:%a %d %b %H:%M} IST · covering {since:%H:%M} to {end:%a %H:%M} · {len(plan)} tick(s)")
    for t, wf, job in plan:
        print(f"  {t:%a %H:%M}  {wf}{' ' + job if job else ''}")
    if a.dry:
        return 0
    failed = 0
    for t, wf, job in plan:
        wait = (t - dt.datetime.now(IST)).total_seconds()
        if wait > 0:
            time.sleep(wait)
        ok, msg = start(wf, job)
        failed += not ok
        print(f"{dt.datetime.now(IST):%H:%M:%S} {wf}{' ' + job if job else ''}: {msg}", flush=True)
    rest = (end - dt.datetime.now(IST)).total_seconds()
    if rest > 0:
        time.sleep(rest)
    ok, msg = gh("metronome.yml", "-f", f"since={end.isoformat(timespec='minutes')}")
    print(f"hand-over to the next run: {'started' if ok else msg}")
    return 1 if (failed or not ok) else 0


if __name__ == "__main__":
    sys.exit(main())
