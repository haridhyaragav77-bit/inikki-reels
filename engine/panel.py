"""Panel (AGENT.md 13.3): everything the Control Room shows, in one small file, rewritten after every job.

    status/panel.md    ready-made text for the Control Room chat: one read answers "status", "next", "money", "alerts"
    status/panel.txt   the same facts as data for the Control Room page (JSON packed as base64, because the Drive
                       connector rewrites plain text on the way out)

    python -m engine.panel            build both and save them to Drive
    python -m engine.panel --print    also print the text version

No AI, nothing posted. If a part cannot be read it is left out; the panel is still written (fail soft)."""
import argparse
import base64
import datetime as dt
import json
import sys

import yaml

from .settings import AGENT, ENGINE, ROOT, niche_dir
from . import status
from .control import Control
from .day import Bank, Day, load_json_lines, today

DOW = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
MARK = "INIKKI-PANEL-1"


# ---------------------------------------------------------------- the clock: what runs next
def _field(f, lo, hi):
    if f == "*":
        return None
    out = set()
    for part in f.split(","):
        if part.startswith("*/"):
            out |= set(range(lo, hi + 1, int(part[2:])))
        elif "-" in part:
            a, b = part.split("-")
            out |= set(range(int(a), int(b) + 1))
        else:
            out.add(int(part))
    return out


def cron_times(cron, now, hours=40):
    """When a clock line (UTC, 5 fields) fires in the next `hours`, as aware datetimes."""
    try:
        m, h, dom, mon, dow = cron.split()
        mins, hrs, doms, mons, dows = _field(m, 0, 59), _field(h, 0, 23), _field(dom, 1, 31), _field(mon, 1, 12), _field(dow, 0, 7)
    except ValueError:
        return []
    out, utc = [], now.astimezone(dt.timezone.utc)
    for d in range(0, hours // 24 + 2):
        day = (utc + dt.timedelta(days=d)).date()
        if (doms and day.day not in doms) or (mons and day.month not in mons) or (dows and (day.isoweekday() % 7) not in {x % 7 for x in dows}):
            continue
        for hh in sorted(hrs if hrs is not None else range(24)):
            for mm in sorted(mins if mins is not None else [0]):
                t = dt.datetime(day.year, day.month, day.day, hh, mm, tzinfo=dt.timezone.utc)
                if utc < t <= utc + dt.timedelta(hours=hours):
                    out.append(t.astimezone(status.IST))
    return out


def engine_clock():
    """(job, clock line) for every scheduled Engine job, read from the workflow files themselves."""
    out = []
    for p in sorted((ROOT / ".github" / "workflows").glob("*.yml")):
        try:
            y = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        on = y.get("on", y.get(True)) or {}
        for s in (on.get("schedule") or []) if isinstance(on, dict) else []:
            if s.get("cron"):
                out.append((p.stem, s["cron"]))
    return out


def think_times(spec, now, hours=40):
    """A thinking run's times: "05:37" daily, "sun 22:37" weekly, "1 23:07" on that day of the month (IST)."""
    parts = str(spec).lower().split()
    try:
        hh, mm = (int(x) for x in parts[-1].split(":"))
    except ValueError:
        return []
    out = []
    for d in range(0, hours // 24 + 2):
        day = (now + dt.timedelta(days=d)).date()
        if len(parts) == 2 and ((parts[0] in DOW and DOW[day.weekday()] != parts[0]) or (parts[0].isdigit() and day.day != int(parts[0]))):
            continue
        t = dt.datetime(day.year, day.month, day.day, hh, mm, tzinfo=status.IST)
        if now < t <= now + dt.timedelta(hours=hours):
            out.append(t)
    return out


def schedule(ctl, now, hours=40):
    labels = ENGINE.get("schedule_labels") or {}
    slots = sorted(set(ctl.settings.get("slots", []) + ctl.settings.get("flex_slots", [])))
    out = []
    for job, cron in engine_clock():
        lab = labels.get(job, job)
        lab = lab.get(cron, job) if isinstance(lab, dict) else lab
        for t in cron_times(cron, now, hours):
            what, kind = lab, job
            if job == "post":
                slot = next((s for s in slots if 0 <= (dt.datetime.combine(t.date(), dt.time(*map(int, s.split(":"))), status.IST) - t).total_seconds() <= 1500), None)
                what = f"Post · {slot} slot" if slot else "Post"
            out.append({"at": t.isoformat(timespec="minutes"), "what": what, "kind": kind})
    for name, spec in (ctl.settings.get("thinking_runs") or {}).items():
        for t in think_times(spec, now, hours):
            out.append({"at": t.isoformat(timespec="minutes"), "what": f"Thinking run · {name.capitalize()}", "kind": "think"})
    return sorted(out, key=lambda x: x["at"])


# ---------------------------------------------------------------- the parts
def _safe(fn, default):
    try:
        v = fn()
        return default if v is None else v
    except Exception as e:
        print("panel: a part was left out:", str(e)[:120], file=sys.stderr)
        return default


def reels_today(day, plans_dir):
    from .edits import words
    out = []
    for n, r in enumerate(day.reels(), 1):
        row = {"n": n, "id": r["reel_id"], "series": r.get("series"), "state": r.get("state"), "slot": r.get("slot"),
               "post_at": r.get("post_at"), "reserve": bool(r.get("reserve")), "manual": bool(r.get("manual")), "hook": r.get("hook"),
               "why": r.get("reason"), "seconds": r.get("seconds"), "score": r.get("virality"), "folder": r.get("link"),
               "video": f"https://drive.google.com/file/d/{r['drive_reel']}/view" if r.get("drive_reel") else None,
               "posted": r.get("permalink"), "posted_at": r.get("posted_at"), "caption": (r.get("caption") or "")[:240]}
        p = plans_dir / f"{r['reel_id']}.json"
        if r.get("state") not in ("posted", "rehearsed") and p.exists():
            row["words"] = _safe(lambda: words(json.loads(p.read_text(encoding="utf-8"))), {})
        out.append({k: v for k, v in row.items() if v not in (None, "", False, {})})
    return out


def tomorrow(ctl, date):
    from .brief import lineup_today
    rows, _, _ = lineup_today(ctl, date)
    return [{"time": t, "series": s, "look": tpl, "notes": notes} for t, s, tpl, notes in rows if t != "-"]


def series_cards(ctl, base):
    nd, out = niche_dir(), []
    page = ((base.get("_page") or {}).get("median") or {}).get("views")
    for p in sorted((nd / "series").glob("*/series.yaml")):
        sid = p.parent.name
        card = ctl.series(sid, nd)
        med = ((base.get(sid) or {}).get("median") or {}).get("views")
        out.append({k: v for k, v in {"id": sid, "name": card.get("name", sid), "status": card.get("status"), "paused": ctl.series_paused(sid),
                    "slots": card.get("slots"), "look": card.get("template"), "length_s": card.get("length_s"),
                    "reels_14d": (base.get(sid) or {}).get("reels"), "median_views": med, "page_views": page,
                    "rules": [{"id": n.get("id"), "text": n["text"], "at": n.get("at")} for n in ctl.notes(sid)]}.items() if v not in (None, [], "")})
    return out


def numbers(ctl, drive):
    m = _safe(lambda: drive.read_json("status", "metrics.json"), {}) or {}
    g = ctl.settings.get("goal", {})
    out = {"followers": m.get("followers"), "goal": g.get("followers")}
    try:
        start = dt.date.fromisoformat(str(g.get("start_date")))
        days = (status.now().date() - start).days
        span = int(g.get("by_days", 90))
        out.update(target_today=round(g.get("start_followers", 0) + (g.get("followers", 1000) - g.get("start_followers", 0)) * min(1, days / max(1, span))),
                   days_left=max(0, span - days))
    except Exception:
        pass
    base = m.get("baselines") or {}
    out["page"] = (base.get("_page") or {}).get("median") or {}
    recent = sorted(m.get("reels") or [], key=lambda r: r.get("posted_at", ""), reverse=True)[:8]
    out["recent"] = [{"id": r["reel_id"], "series": r.get("series"), "posted_at": r.get("posted_at", "")[:16], "hook": (r.get("hook") or "")[:60],
                      "views": r.get("views"), "rates": {k: (r.get("rates") or {}).get(k) for k in ("skip_rate", "watch_through", "share_rate", "follow_rate")},
                      "health": r.get("health") or {}, "link": r.get("permalink")} for r in recent]
    c = _safe(lambda: drive.read_json("status", "checks.json"), {}) or {}
    out["early"] = [{"id": v.get("reel_id"), "views": v.get("views"), "age_h": v.get("age_h")} for v in list((c.get("reels") or {}).values())[-6:]]
    out["measured"] = m.get("updated")
    return out, base


def money(ctl, drive):
    out = {}
    try:
        from .budget import Budget
        b = Budget(drive).summary()
        out.update(images_inr=b["spent_inr"], images_cap=b["cap_inr"], images_made=b["images"])
    except Exception:
        pass
    mins = _safe(lambda: drive.read_json("status", "minutes.json"), {}) or {}
    stor = _safe(lambda: drive.read_json("status", "storage.json"), {}) or {}
    out.update(runner_min=mins.get("minutes"), runner_limit=mins.get("limit", ENGINE.get("runner", {}).get("minutes_month")),
               storage_gb=stor.get("gb"), storage_cap=ctl.settings.get("budgets", {}).get("storage_gb"), last_cleanup_deleted=stor.get("deleted"))
    month = status.now().strftime("%Y-%m")
    posted = [p for p in load_json_lines(_safe(lambda: drive.read_text("status", "posted.jsonl"), "") or "") if str(p.get("posted_at", "")).startswith(month)]
    out["posted_month"] = len(posted)
    if posted:
        out["per_reel"] = {"images_inr": round((out.get("images_inr") or 0) / len(posted), 2),
                           "runner_min": round((out.get("runner_min") or 0) / len(posted), 1) if out.get("runner_min") else None}
    u = ROOT / "data" / "notes" / "usage.json"
    if u.exists():
        out["thinking"] = _safe(lambda: json.loads(u.read_text(encoding="utf-8")), None)
    return {k: v for k, v in out.items() if v is not None}


def actions(drive):
    """What Harish asked for lately and what became of it (control/log.jsonl, plus the outcome of word changes)."""
    log = load_json_lines(_safe(lambda: drive.read_text("control", "log.jsonl"), "") or "")[-10:]
    done = (_safe(lambda: drive.read_json("status", "edits.json"), {}) or {}).get("done") or {}
    out = []
    for x in reversed(log):
        row = {"id": x.get("id"), "at": x.get("at"), "what": x.get("summary"), "result": x.get("result"), "why": x.get("why"),
               "can_undo": bool(x.get("undo")) and not x.get("undone"), "undone": bool(x.get("undone"))}
        if x.get("id") in done:
            row["outcome"] = done[x["id"]].get("note")
            row["result"] = "done" if done[x["id"]].get("ok") else "refused"
        out.append({k: v for k, v in row.items() if v not in (None, "", False)})
    return out


def build(drive, ctl=None):
    ctl = ctl or Control(drive)
    now = status.now()
    day, bank = Day(drive), Bank(drive)
    date = today()
    nxt = (now + dt.timedelta(days=1)).strftime("%Y-%m-%d")
    nums, base = _safe(lambda: numbers(ctl, drive), ({}, {}))
    lineup_name = ctl.settings.get("active", {}).get("lineup")
    try:
        from .post import respect_today
        respect = respect_today(drive, date, ctl)
    except Exception:
        respect = None
    reels = _safe(lambda: reels_today(day, ROOT / "plans" / date), [])
    P = {"v": 1, "updated": status.stamp(), "updated_iso": now.isoformat(timespec="seconds"),
         "switch": ctl.mode, "phase": ctl.phase, "approval": ctl.settings.get("approval"), "away": bool(ctl.settings.get("away_mode")),
         "respect": (respect or {}).get("why") if respect else None,
         "active": ctl.settings.get("active"), "volume": ctl.settings.get("volume"), "slots": ctl.settings.get("slots"),
         "today": {"date": date, "reels": reels},
         "tomorrow": {"date": nxt, "slots": _safe(lambda: tomorrow(ctl, nxt), [])},
         "bank": {"ready": len(bank.reels("ready"))},
         "schedule": _safe(lambda: schedule(ctl, now), [])[:24],
         "numbers": nums, "series": _safe(lambda: series_cards(ctl, base), []), "money": _safe(lambda: money(ctl, drive), {}),
         "page_rules": [{"id": n.get("id"), "text": n["text"], "at": n.get("at")} for n in ctl.notes()],
         "alerts": [{k: a.get(k) for k in ("id", "at", "level", "title", "what_happened", "what_was_done", "what_you_do")}
                    for a in (_safe(lambda: drive.read_json("status", "alerts.json"), {}) or {}).get("alerts", []) if a.get("open")][:6],
         "jobs": {k: {"result": v.get("result"), "at": v.get("at")} for k, v in ((_safe(lambda: drive.read_json("status", "jobs.json"), {}) or {}).get("jobs") or {}).items()},
         "digest": (_safe(lambda: drive.read_text("status", "digest.md"), "") or "")[:900],
         "actions": _safe(lambda: actions(drive), []),
         "inbox": _safe(lambda: drive.folder("control/inbox"), None), "lineup": lineup_name}
    return P


# ---------------------------------------------------------------- the text version, for the chat
def _hm(iso):
    return dt.datetime.fromisoformat(iso).strftime("%a %H:%M") if iso else "-"


def _pct(v):
    return "-" if v is None else f"{v * 100:.1f}%"


def text(P):
    n = P.get("numbers") or {}
    m = P.get("money") or {}
    reels = P["today"]["reels"]
    count = lambda s: sum(1 for r in reels if r.get("state") == s)
    L = [f"# iNiKKi panel · updated {P['updated']}",
         f"Switch {str(P['switch']).upper()} · Phase {str(P['phase']).upper()} · Approval {P.get('approval')}"
         + (f" · RESPECT MODE: {P['respect']}" if P.get("respect") else "") + (" · away mode" if P.get("away") else "")]
    if n.get("followers") is not None:
        diff = n["followers"] - n.get("target_today", n["followers"])
        L.append(f"Followers {n['followers']} of {n.get('goal')} · target line today {n.get('target_today')} ({'+' if diff >= 0 else ''}{diff}) · {n.get('days_left')} days left")
    L += ["", f"## TODAY {P['today']['date']} · {count('posted')} posted · {count('ready')} ready · {count('held') + count('failed')} held · {count('skipped')} skipped"]
    for r in reels:
        when = r.get("slot") or ("reserve" if r.get("reserve") else "-")
        link = r.get("posted") or r.get("video") or ""
        L.append(f"{r['n']}. {when} · {str(r.get('state')).upper()}{' (waits for post now)' if r.get('manual') and r.get('state') == 'ready' else ''} · {r['id']} · {r.get('series')} · \"{r.get('hook') or ''}\""
                 + (f" · {link}" if link else "") + (f" · note: {r['why'][:90]}" if r.get("why") else ""))
    if not reels:
        L.append("No reels made yet today.")
    L += ["", "## NEXT RUNS (IST)"] + [f"- {_hm(s['at'])} · {s['what']}" for s in P.get("schedule", [])[:9]]
    if P["tomorrow"]["slots"]:
        L += ["", f"## TOMORROW {P['tomorrow']['date']} (planned at 05:37)", " · ".join(f"{s['time']} {s['series']}" for s in P["tomorrow"]["slots"])]
    L += ["", f"Breakdown bank: {P['bank']['ready']} ready"]
    if n.get("recent"):
        L += ["", "## LAST REELS (views · skip · watch-through · share)"] + [
            f"- {r['id']} · {r.get('views')} views · {_pct(r['rates'].get('skip_rate'))} · {_pct(r['rates'].get('watch_through'))} · {_pct(r['rates'].get('share_rate'))}"
            for r in n["recent"][:6]]
    L += ["", "## MONEY AND LIMITS",
          f"Images ₹{m.get('images_inr', '?')} of ₹{m.get('images_cap', '?')} · runner minutes {m.get('runner_min', '?')} of {m.get('runner_limit', '?')} · storage {m.get('storage_gb', '?')} of {m.get('storage_cap', '?')} GB"]
    if m.get("per_reel"):
        L.append(f"Per posted reel this month ({m.get('posted_month')} reels): ₹{m['per_reel'].get('images_inr')} images · {m['per_reel'].get('runner_min', '?')} runner minutes")
    t = m.get("thinking") or {}
    if t.get("line"):
        L.append(f"Thinking runs: {t['line']}")
    rules = [f"- all series: {x['text']} [{x.get('id')}]" for x in P.get("page_rules") or []] + \
            [f"- {s['id']}: {x['text']} [{x.get('id')}]" for s in P.get("series") or [] for x in s.get("rules") or []]
    if rules:
        L += ["", "## YOUR STANDING RULES"] + rules
    paused = [s["id"] for s in P.get("series") or [] if s.get("paused")]
    L += ["", "## SERIES", " · ".join(f"{s['id']}{' (PAUSED)' if s['id'] in paused else ''}" for s in P.get("series") or [])]
    if P.get("alerts"):
        L += ["", f"## ALERTS ({len(P['alerts'])} open)"] + [f"- {a.get('at')} · {a.get('title')} · you: {a.get('what_you_do') or 'nothing'}" for a in P["alerts"]]
    if P.get("actions"):
        L += ["", "## YOUR LAST ACTIONS"] + [f"- [{a.get('id')}] {a.get('what')} → {a.get('outcome') or a.get('result')}" + (f" ({a['why']})" if a.get("why") else "")
                                             for a in P["actions"][:6]]
    if P.get("digest"):
        L += ["", "## DIGEST", P["digest"].strip()]
    return "\n".join(L) + "\n"


def pack(P):
    raw = base64.b64encode(json.dumps(P, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).decode("ascii")
    return MARK + "\n" + "\n".join(raw[i:i + 76] for i in range(0, len(raw), 76)) + "\n"


def save(drive, ctl=None):
    P = build(drive, ctl)
    status.local_write("panel.json", P)
    drive.write_text("status", "panel.md", text(P), "text/markdown")
    drive.write_text("status", "panel.txt", pack(P), "text/plain")
    return P


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--print", action="store_true")
    a = ap.parse_args()
    from .drive import Drive
    P = save(Drive())
    print(text(P) if a.print else f"panel written: {len(P['today']['reels'])} reels today, {len(P.get('alerts', []))} open alerts")


if __name__ == "__main__":
    main()
