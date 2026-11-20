"""Catch-up check for the thinking runs (AGENT.md 4.2, "Missed runs catch up").

Answers one question with no AI and no keys: which thinking runs are still owed right now?
A run is owed when its time has passed today (or this week / month), main has no sign it ran, the
master switch is not Sleep, and it is not too late to be useful.

    python tools/run_due.py            # every run: one line each, e.g. "plan: due (late start: plan 15:30 18:00 ...)"
    python tools/run_due.py plan       # one run
    python tools/run_due.py --now 2026-11-14T10:05   # for tests (IST)

Proof that a run happened comes from main only: the Sync job commits "brain: <run> <date>" there, and a
Plan run's files land in plans/<date>/. A pushed claude/brain-<run>-<date> branch still waiting for Sync
also counts. Settings: config/agent.yaml (thinking_runs, slots, catch_up)."""
import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
RUNS = ("plan", "refresh", "weekly", "monthly")


def git(*a):
    r = subprocess.run(["git", "-C", str(ROOT), *a], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def settings():
    """Reads config/agent.yaml. Uses PyYAML when installed; otherwise a small reader for the three lines needed
    (the dispatcher's container may not have PyYAML)."""
    text = (ROOT / "config" / "agent.yaml").read_text(encoding="utf-8")
    try:
        import yaml
        s = yaml.safe_load(text) or {}
    except ImportError:
        def flow(key):
            m = re.search(rf"^{key}:\s*(\{{.*?\}}|\[.*?\])", text, re.M)
            if not m:
                return None
            body = m.group(1)
            if body.startswith("["):
                return re.findall(r'"([^"]*)"', body)
            return {k: v.strip().strip('"') for k, v in re.findall(r'(\w+):\s*("[^"]*"|[^,}]+)', body[1:-1])}
        s = {"thinking_runs": flow("thinking_runs"), "slots": flow("slots"), "flex_slots": flow("flex_slots"),
             "catch_up": flow("catch_up")}
    c = s.get("catch_up") or {}
    return {"runs": s.get("thinking_runs") or {}, "slots": s.get("slots") or [], "flex": s.get("flex_slots") or [],
            "make_minutes": int(c.get("make_minutes", 75)), "refresh_until": c.get("refresh_until", "22:45"),
            "weekly_days": int(c.get("weekly_days", 2)), "monthly_days": int(c.get("monthly_days", 2))}


def hm(text):
    h, m = str(text).strip().split()[-1].split(":")
    return dt.time(int(h), int(m))


def at(day, t):
    return dt.datetime.combine(day, t, IST)


def brain_dates(run):
    """Dates main's log says this run finished (Sync commits 'brain: <run> <date>...')."""
    log = git("log", "origin/main", "-300", "--format=%s")
    return {m.group(1) for m in re.finditer(rf"^brain: {run} (\d{{4}}-\d\d-\d\d)", log, re.M)}


def branch_waiting(run, date):
    return bool(git("ls-remote", "--heads", "origin", f"claude/brain-{run}-{date}").strip())


def plans_in(date):
    names = git("ls-tree", "--name-only", "origin/main", f"plans/{date}/").split()
    main = 0
    for n in names:
        if not n.endswith(".json") or n.endswith("respect.json"):
            continue
        try:
            d = json.loads(git("show", f"origin/main:{n}") or "{}")
            if not d.get("reserve") and not d.get("booked"):      # a reel booked ahead (Workshop) is not the Plan run's work
                main += 1
        except ValueError:
            main += 1
    return main


def switch_mode():
    try:
        return json.loads(git("show", "origin/main:data/control/switch.json") or "{}").get("mode", "run")
    except ValueError:
        return "run"


def check(run, now, s):
    today = now.date()
    if run == "plan":
        start = at(today, hm(s["runs"].get("plan", "05:37")))
        if now < start:
            return "not yet", ""
        if plans_in(today.isoformat()) or today.isoformat() in brain_dates("plan") or branch_waiting("plan", today):
            return "done", ""
        ready_by = now + dt.timedelta(minutes=s["make_minutes"])
        left = [t for t in s["slots"] if at(today, hm(t)) >= ready_by]
        flex = [t for t in s["flex"] if at(today, hm(t)) >= ready_by]
        if not left and not flex:
            return "too late", "no post time left today with time to make a reel; tomorrow's Plan run takes the lineup"
        if now <= start + dt.timedelta(minutes=45):
            return "due", ""
        missed = len(s["slots"]) - len(left)
        open_times = sorted(left + flex, key=hm)
        return "due", (f"late start: {missed} of {len(s['slots'])} slot(s) passed; post times still open: {' '.join(open_times)} "
                       f"(flex: {' '.join(flex) or 'none'}); move the missed reels to these times, see runs/plan.md step 4")
    if run == "refresh":
        start = at(today, hm(s["runs"].get("refresh", "16:37")))
        if now < start:
            return "not yet", ""
        if today.isoformat() in brain_dates("refresh") or branch_waiting("refresh", today):
            return "done", ""
        if now > at(today, hm(s["refresh_until"])):
            return "too late", "tonight's posts are made; tomorrow's Plan run picks up"
        return "due", ""
    if run == "weekly":
        spec = str(s["runs"].get("weekly", "sun 22:37"))
        back = (today.weekday() - 6) % 7                      # days since Sunday
        sunday = today - dt.timedelta(days=back)
        start = at(sunday, hm(spec))
        if now < start:
            sunday -= dt.timedelta(days=7)
            start = at(sunday, hm(spec))
        if any(d >= sunday.isoformat() for d in brain_dates("weekly")) or \
                any(branch_waiting("weekly", sunday + dt.timedelta(days=i)) for i in range(s["weekly_days"] + 1)):
            return "done", ""
        if now.date() > sunday + dt.timedelta(days=s["weekly_days"]):
            return "too late", "next Sunday's run covers it"
        return ("due", "") if now >= start else ("not yet", "")
    if run == "monthly":
        spec = str(s["runs"].get("monthly", "1 23:07"))
        first = today.replace(day=int(spec.split()[0]))
        start = at(first, hm(spec))
        if now < start:
            return "not yet", ""
        if any(d.startswith(today.strftime("%Y-%m")) for d in brain_dates("monthly")) or \
                any(branch_waiting("monthly", first + dt.timedelta(days=i)) for i in range(s["monthly_days"] + 1)):
            return "done", ""
        if today > first + dt.timedelta(days=s["monthly_days"]):
            return "too late", "next month's run covers it"
        return "due", ""
    return "unknown", ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run", nargs="?", choices=RUNS)
    ap.add_argument("--now", help="IST time for tests, e.g. 2026-11-14T10:05")
    ap.add_argument("--no-fetch", action="store_true")
    a = ap.parse_args()
    now = dt.datetime.fromisoformat(a.now).replace(tzinfo=IST) if a.now else dt.datetime.now(IST)
    if not a.no_fetch:
        git("fetch", "-q", "origin", "main")
    if switch_mode() == "sleep":
        print("all: skip (the master switch says Sleep)")
        return
    s = settings()
    for run in ([a.run] if a.run else RUNS):
        state, why = check(run, now, s)
        print(f"{run}: {state}" + (f" ({why})" if why else ""))


if __name__ == "__main__":
    sys.exit(main())
