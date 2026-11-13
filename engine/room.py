"""The Control Room page (AGENT.md 13.1, 16.2): one plain-words file, Drive status/control_room.md, rebuilt at the end of every job.
The Advisor reads only this file to draw the Today, Tomorrow and Dashboard cards, so it never has to piece together raw status files.

    python -m engine.room            rebuild it now (also runs inside engine.status at the end of every workflow)
    python -m engine.room --print    show it here instead of saving it"""
import argparse
import datetime as dt
import json

import yaml

from . import status
from .settings import AGENT, ROOT

WORDS = {"planned": "Planned, not made yet", "rendering": "Being made", "ready": "Ready", "rehearsed": "Rehearsed (not posted)",
         "posted": "Posted", "held": "Held", "failed": "Failed", "skipped": "Skipped"}
MARK = {"posted": "✅", "ready": "⏳", "planned": "📝", "rendering": "🎬", "rehearsed": "🎭", "held": "⛔", "failed": "⚠️", "skipped": "⏭️"}


def _read(drive, folder, name, default=None):
    try:
        return drive.read_json(folder, name) or default
    except Exception:
        return default


def series_names():
    niche = AGENT.get("active", {}).get("niche", "")
    out = {}
    for p in (ROOT / "niches" / niche / "series").glob("*/series.yaml"):
        try:
            out[p.parent.name] = str((yaml.safe_load(p.read_text(encoding="utf-8")) or {}).get("name") or p.parent.name).split(" (")[0]
        except Exception:
            out[p.parent.name] = p.parent.name
    return out


def hhmm(iso):
    try:
        return dt.datetime.fromisoformat(iso).strftime("%H:%M")
    except Exception:
        return ""


def nice_day(d):
    return f"{d.strftime('%a')} {d.day} {d.strftime('%b')}"


def title(r):
    return (r.get("hook") or r.get("reel_id", "")).replace("|", "/")


def views_by_reel(checks):
    return {v.get("reel_id"): v.get("views") for v in (checks or {}).get("reels", {}).values() if v.get("reel_id")}


def reel_row(r, names, views, now):
    st = r.get("state", "planned")
    t = r.get("slot") or hhmm(r.get("post_at") or "")
    note = WORDS.get(st, st)
    if st == "posted":
        note = f"Posted {hhmm(r.get('posted_at') or '')}"
        if views.get(r["reel_id"]) is not None:
            note += f" · {views[r['reel_id']]:,} views so far"
        if r.get("permalink"):
            note += f" · [open]({r['permalink']})"
    elif st == "ready" and r.get("post_at"):
        due = dt.datetime.fromisoformat(r["post_at"])
        note = f"Ready, posts at {due.strftime('%H:%M')}" if due > now else "Ready, posting now"
    elif r.get("reason"):
        note += f": {str(r['reason'])[:110]}"
    return f"| {t or '—'} | {title(r)} | {names.get(r.get('series'), r.get('series') or '—')} | {MARK.get(st, '')} {note} |"


def day_table(reels, names, views, now):
    rows = ["| Time | Reel | Series | Status |", "| --- | --- | --- | --- |"]
    rows += [reel_row(r, names, views, now) for r in reels]
    return rows


def lineup_draft(date):
    """The Refresh run's draft of tomorrow (plans/<date>/lineup.json): [{slot, series, topic}]."""
    p = ROOT / "plans" / date / "lineup.json"
    try:
        return (json.loads(p.read_text(encoding="utf-8")) or {}).get("reels", []) if p.exists() else []
    except ValueError:
        return []


def open_alerts(alerts, posted_ids, now, limit=5):
    """Open alerts from the last 2 days, without the ones a later success already answered (a reel that failed, then posted)."""
    cut = (now - dt.timedelta(days=2)).strftime("%Y-%m-%d")
    out, seen = [], set()
    for a in (alerts or {}).get("alerts", []):
        if not a.get("open") or a.get("at", "")[:10] < cut:
            continue
        happened = a.get("what_happened", "")
        if any(happened.startswith(f"{rid}:") for rid in posted_ids):
            continue
        if a.get("title") in seen:
            continue
        seen.add(a.get("title"))
        out.append(a)
    return out[:limit]


def build(drive, now=None):
    from .control import Control
    now = now or status.now()
    ctl = Control(drive)
    names = series_names()
    today_s, tom = now.strftime("%Y-%m-%d"), now.date() + dt.timedelta(days=1)
    tom_s = tom.strftime("%Y-%m-%d")
    day = _read(drive, "status/days", f"{today_s}.json", {"reels": []})
    tday = _read(drive, "status/days", f"{tom_s}.json", {"reels": []})
    bank = _read(drive, "status", "bank.json", {"reels": []})
    views = views_by_reel(_read(drive, "status", "checks.json", {}))
    alerts = _read(drive, "status", "alerts.json", {"alerts": []})
    jobs = (_read(drive, "status", "jobs.json", {}) or {}).get("jobs", {})
    budget = _read(drive, "status", "budget.json", {}) or {}
    mins = _read(drive, "status", "minutes.json", {}) or {}
    stor = _read(drive, "status", "storage.json", {}) or {}

    reels = day.get("reels", [])
    main = [r for r in reels if not r.get("reserve")]
    spares = [r for r in reels if r.get("reserve") and r.get("state") == "ready"]
    count = lambda *s: sum(1 for r in main if r.get("state") in s)
    posted_ids = [r["reel_id"] for r in reels if r.get("state") == "posted"]
    upcoming = sorted((r for r in main if r.get("state") in ("ready", "planned", "rendering") and r.get("post_at")
                       and dt.datetime.fromisoformat(r["post_at"]) > now), key=lambda r: r["post_at"])

    f_path = ROOT / "data" / "metrics" / "followers.jsonl"
    g = ctl.settings.get("goal", {})
    followers = None
    if f_path.exists():
        lines = [x for x in f_path.read_text(encoding="utf-8").splitlines() if x.strip()]
        try:
            followers = json.loads(lines[-1]).get("followers") if lines else None
        except ValueError:
            pass
    try:
        days_in = (now.date() - dt.date.fromisoformat(str(g.get("start_date")))).days
        target = round(g.get("start_followers", 0) + (g.get("followers", 1000) - g.get("start_followers", 0)) * min(1, days_in / g.get("by_days", 90)))
    except Exception:
        target = None

    mode = {"run": "Run", "hold_posts": "Hold posts", "sleep": "Sleep"}.get(ctl.mode, ctl.mode)
    L = [f"# iNiKKi Control Room · {nice_day(now)}", f"Updated {status.stamp()}. If this is more than 2 hours old, say so.", "",
         "## Page",
         f"- Phase: **{'Live' if ctl.phase == 'live' else 'Rehearsal (nothing posts)'}** · Master switch: **{mode}**",
         f"- Followers: **{followers if followers is not None else '—'}** · target line today: {target if target is not None else '—'}"
         + (f" · {'ahead' if followers >= target else 'behind'} by {abs(followers - target)}" if followers is not None and target is not None else ""),
         "",
         f"## Today · {count('posted')} of {len(main)} posted · {len(upcoming)} still to post · {count('held', 'failed', 'skipped')} held or skipped"]
    if upcoming:
        L.append(f"Next: **{upcoming[0].get('slot') or hhmm(upcoming[0]['post_at'])} · {title(upcoming[0])}**")
    L += [""] + (day_table(main, names, views, now) if main else ["No reels planned today yet (plans are made at 05:37)."])
    L += ["", f"Spare reels ready: {', '.join(title(r) for r in spares) if spares else 'none'}", ""]

    L.append(f"## Tomorrow · {nice_day(tom)}")
    if tday.get("reels"):
        L += ["Made or being made:", ""] + day_table([r for r in tday["reels"] if not r.get("reserve")], names, views, now)
    elif lineup_draft(tom_s):
        L += ["Draft lineup (from this evening's Refresh run). The 05:37 Plan run firms it up and may swap topics for fresh news.", "",
              "| Time | Topic | Series |", "| --- | --- | --- |"]
        L += [f"| {x.get('slot', '—')} | {str(x.get('topic', '—')).replace('|', '/')} | {names.get(x.get('series'), x.get('series') or '—')} |"
              for x in lineup_draft(tom_s)]
    else:
        L.append(f"Not drafted yet. The Refresh run (16:37) drafts it; the Plan run makes it final at 05:37. "
                 f"Slots: {', '.join(ctl.settings.get('slots', []))}.")
    ready_bank = [r for r in bank.get("reels", []) if r.get("state") == "ready"]
    L += ["", f"Breakdowns ready in the bank (used when a slot has nothing ready): {len(ready_bank)}"
          + (f" · {', '.join(title(r) for r in ready_bank[:4])}" if ready_bank else ""), ""]

    L.append("## Needs you")
    al = open_alerts(alerts, posted_ids, now)
    L += [f"- **{a['title']}** ({a['at'][11:16]}): {a.get('what_was_done', '')} You: {a.get('what_you_do', 'nothing')}" for a in al] or ["Nothing."]
    L.append("")

    L += ["## Money and limits",
          f"- AI images: ₹{round(float(budget.get('inr', 0)))} of ₹{AGENT.get('budgets', {}).get('images_inr_month', 500)} this month",
          f"- Runner minutes: {mins.get('minutes', '—')} of {mins.get('limit', 2000)} this month",
          f"- Drive storage: {stor.get('gb', '—')} GB of {ctl.settings.get('budgets', {}).get('storage_gb', 8)} GB", ""]

    bad = [(k, v) for k, v in jobs.items() if v.get("result") not in ("success", "skipped", "cancelled") and v.get("at", "")[:10] >= (now - dt.timedelta(days=1)).strftime("%Y-%m-%d")]
    L.append("## Jobs")
    L.append("All jobs finished fine in the last day." if not bad else
             "Did not finish in the last day: " + ", ".join(f"{k} ({v.get('at', '')[11:16]})" for k, v in bad))
    return "\n".join(L) + "\n"


def save(drive):
    text = build(drive)
    p = status.local_write("control_room.json", {"text": text})
    p.with_name("control_room.md").write_text(text, encoding="utf-8")
    drive.write_text("status", "control_room.md", text, "text/markdown")
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()
    from .drive import Drive
    drive = Drive()
    print(build(drive) if a.print else save(drive))


if __name__ == "__main__":
    main()
