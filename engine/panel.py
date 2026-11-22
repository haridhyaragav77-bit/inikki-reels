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

from .settings import AGENT, ENGINE, ROOT, niche, niche_dir
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
    for s in slots:                                   # Post is started at each slot by the clock tasks (AGENT.md 4.3)
        for t in think_times(s, now, hours):
            out.append({"at": t.isoformat(timespec="minutes"), "what": f"Post · {s} slot", "kind": "post"})
    for c in ENGINE.get("clock") or []:
        for t in think_times(c.get("at", ""), now, hours):
            out.append({"at": t.isoformat(timespec="minutes"), "what": c.get("what", "job"), "kind": c.get("kind", "daily")})
    for job, cron in engine_clock():                  # the rest still hangs on GitHub's own timer, which may run late
        if job == "post":
            continue
        lab = labels.get(job, job)
        lab = lab.get(cron, job) if isinstance(lab, dict) else lab
        for t in cron_times(cron, now, hours):
            out.append({"at": t.isoformat(timespec="minutes"), "what": lab, "kind": job})
    seen, uniq = set(), []
    for x in sorted(out, key=lambda x: x["at"]):
        if (x["at"], x["what"]) not in seen:
            seen.add((x["at"], x["what"]))
            uniq.append(x)
    out = uniq
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


HERO = ("scene", "board", "climb", "track", "layers", "detail")


def plan_bits(plan):
    """For the reel's row: a breakdown's one point and hero visual, and a trending song (AGENT.md 5.4, 5.7, 5.8)."""
    out = {"point": (plan.get("lead") or {}).get("point")}
    kinds = [s.get("kind") for s in plan.get("screens") or []]
    out["hero"] = next((k for k in kinds if k in HERO), None) if plan.get("template") == "stage" else None
    songs = {t["key"]: t.get("title") for t in music_card().get("trending", [])}
    out["song"] = next((songs[s.get("track")] for s in (plan.get("music") or {}).get("sections", []) if s.get("track") in songs), None)
    return {k: v for k, v in out.items() if v}


def music_card():
    """This month's trending songs (data/music/trending.json) and the library's size, for Setup › Trending songs."""
    try:
        tr = json.loads((ROOT / "data" / "music" / "trending.json").read_text(encoding="utf-8")).get("tracks", [])
    except (OSError, ValueError):
        tr = []
    try:
        lib = len(json.loads((ROOT / "engine" / "music_index.json").read_text(encoding="utf-8")).get("tracks", {}))
    except (OSError, ValueError):
        lib = 0
    return {"trending": [{k: t.get(k) for k in ("key", "title", "film", "best", "uses", "added", "fresh")} for t in tr[:15]], "library": lib + len(tr)}


def reels_today(day, plans_dir):
    from .edits import words
    out = []
    for n, r in enumerate(day.reels(), 1):
        row = {"n": n, "id": r["reel_id"], "series": r.get("series"), "state": r.get("state"), "slot": r.get("slot"),
               "post_at": r.get("post_at"), "reserve": bool(r.get("reserve")), "manual": bool(r.get("manual")), "hook": r.get("hook"),
               "why": r.get("reason"), "seconds": r.get("seconds"), "score": r.get("virality"), "folder": r.get("link"),
               "video": f"https://drive.google.com/file/d/{r['drive_reel']}/view" if r.get("drive_reel") else None,
               "posted": r.get("permalink"), "posted_at": r.get("posted_at"), "caption": (r.get("caption") or "")[:240],
               "youtube": r.get("yt_url"), "youtube_note": r.get("yt_reason") if not r.get("yt_url") else None}
        p = plans_dir / f"{r['reel_id']}.json"
        plan = _safe(lambda: json.loads(p.read_text(encoding="utf-8")), {}) if p.exists() else {}
        if r.get("state") not in ("posted", "rehearsed") and plan:
            row["words"] = _safe(lambda: words(plan), {})
        if plan:
            row.update(_safe(lambda: plan_bits(plan), {}))
        out.append({k: v for k, v in row.items() if v not in (None, "", False, {})})
    return out


def tomorrow(ctl, date):
    from .brief import lineup_today
    rows, _, _ = lineup_today(ctl, date)
    return [{"time": t, "series": s, "look": tpl, "notes": notes} for t, s, tpl, notes in rows if t != "-"]


def _flat(card, key):
    v = card
    for k in key.split("."):
        if not isinstance(v, dict) or k not in v:
            return None
        v = v[k]
    return v


def framework_card(ctl):
    """The series framework for the page: the 7 blocks with their fields, and the global switches with today's values."""
    from . import relay
    fw = relay.framework()
    f = lambda x: {k: v for k, v in {"key": x["key"], "label": x.get("label"), "type": x.get("type", "text"), "help": x.get("help"), "ask": x.get("ask"),
                                    "required": x.get("required"), "options": relay.options(x) if x.get("type") == "choice" else None}.items() if v not in (None, False, [])}
    voices = (ENGINE["voice"].get("elevenlabs") or {}).get("voices") or {}
    return {"blocks": [{"id": b["id"], "name": b["name"], "about": b.get("about"), "fields": [f(x) for x in b["fields"]]} for b in fw.get("blocks", [])],
            "switches": [{**f(x), "value": _flat(ctl.settings, x["key"])} for x in fw.get("switches", [])],
            "voice_labels": {k: v.get("label", k) for k, v in voices.items()}}


def series_cards(ctl, base, drive=None):
    from . import relay
    nd, out = niche_dir(), []
    keys = list(relay.field_specs())
    page = ((base.get("_page") or {}).get("median") or {}).get("views")
    tests = {}
    try:
        for t in ((drive.read_json("status", "tests.json") or {}).get("done") or {}).values():
            tests[t.get("series")] = {k: t.get(k) for k in ("at", "ok", "link", "note")}
    except Exception:
        pass
    new = ctl.new_series()
    for sid in ctl.series_ids(nd):
        card = ctl.series(sid, nd)
        med = ((base.get(sid) or {}).get("median") or {}).get("views")
        vals = {k: _flat(card, k) for k in keys}
        out.append({k: v for k, v in {"id": sid, "name": card.get("name", sid), "status": card.get("status"), "paused": ctl.series_paused(sid),
                    "slots": card.get("slots"), "look": card.get("template"), "length_s": card.get("length_s"),
                    "reels_14d": (base.get(sid) or {}).get("reels"), "median_views": med, "page_views": page,
                    "values": {k: v for k, v in vals.items() if v not in (None, [], "")}, "changed": sorted(ctl.series_changes(sid)),
                    "new": sid in new, "has_reference": bool((card.get("reference") or {}).get("plan")), "test": tests.get(sid),
                    "rules": [{"id": n.get("id"), "text": n["text"], "at": n.get("at")} for n in ctl.notes(sid)]}.items() if v not in (None, [], "", False)})
    return out


def usage(ctl, drive, money_card):
    """Everything that is counted and capped, in one card: GitHub runner minutes, voice credits, pictures, Claude."""
    R = ENGINE.get("runner", {})
    mins = _safe(lambda: drive.read_json("status", "minutes.json"), {}) or {}
    limit = mins.get("limit", R.get("minutes_month"))
    stage = "saver" if ctl.on("saver", False) and mins.get("stage", "normal") == "normal" else mins.get("stage", "normal")
    runner = {"minutes": mins.get("minutes"), "limit": limit, "forecast": mins.get("forecast"), "per_day": mins.get("pace_per_day") or mins.get("per_day"),
              "stage": stage, "runs_out": mins.get("runs_out"), "month": mins.get("month"),
              "pct": round(100 * mins["minutes"] / limit) if mins.get("minutes") is not None and limit else None,
              "forecast_pct": round(100 * mins["forecast"] / limit) if mins.get("forecast") and limit else None,
              "ladder": [f"Heading past {limit}: reserve and bank reels wait", f"At {int(float(R.get('tight_share', .85)) * 100)}%: the same, and no extra news checks",
                         f"At {int(float(R.get('last_share', .95)) * 100)}%: only {R.get('last_reels_day', 3)} new reels a day, so posting never stops",
                         "At 100%: GitHub stops every job until the 1st. Nothing moves to Claude: the Brain cannot make or post reels."] if not mins.get("free") else ["No monthly limit: the repository is public, so nothing is slowed down or skipped to save minutes."], "free": bool(mins.get("free"))}
    v = _safe(lambda: drive.read_json("status", "voice.json"), {}) or {}
    sub, reels = v.get("subscription") or {}, dict(v.get("reels") or {})
    from .voice import NO_KEY
    real = [r for r in v.get("recent") or [] if r.get("why") != NO_KEY]        # the automatic look check runs without the key: not a reel
    if v.get("recent"):
        reels = {p: len({r.get("reel_id") for r in real if r.get("voice") == p}) for p in ("elevenlabs", "microsoft")}
    el = reels.get("elevenlabs", 0)
    per_reel = round(v.get("credits_by_engine", 0) / el) if el else None
    now = status.now()
    voice = {"main": (ctl.settings.get("voice") or {}).get("provider"), "now": v.get("provider_now"), "used": sub.get("used"), "limit": sub.get("limit"),
             "left": sub.get("left"), "resets": sub.get("resets"), "tier": sub.get("tier"), "read": sub.get("read"),
             "reels_elevenlabs": el, "reels_microsoft": reels.get("microsoft", 0), "per_reel": per_reel,
             "covers_reels": int(sub["left"] / per_reel) if per_reel and sub.get("left") is not None else None,
             "reused_lines": v.get("lines_reused"), "last_backup": next((r for r in real if r.get("voice") == "microsoft" and r.get("why")), None)}
    try:
        if per_reel and sub.get("resets") and sub.get("left") is not None:
            days_left = max(1, (dt.date.fromisoformat(sub["resets"]) - now.date()).days)
            day_n = max(1, now.day)
            voice["need_to_reset"] = round(el / day_n * days_left * per_reel)          # at this month's pace
            voice["enough"] = voice["need_to_reset"] <= sub["left"]
    except Exception:
        pass
    runs = ctl.settings.get("thinking_runs") or {}
    claude = {"runs": [{"name": k, "at": str(t)} for k, t in runs.items()], "measured": (money_card.get("thinking") or {}).get("measured"),
              "line": (money_card.get("thinking") or {}).get("line"),
              "quiet": [f"{str(t)} ({k})" for k, t in runs.items() if k in ("plan", "refresh")],
              "note": "Claude has no way to set tokens aside for the agent. What protects the runs: each one starts in a clean chat, "
                      "and a run that was blocked is started again by the catch-up check (5 times a day)."}
    return {"runner": {k: x for k, x in runner.items() if x is not None}, "voice": {k: x for k, x in voice.items() if x is not None}, "claude": claude}


def scouts_card(drive):
    st = _safe(lambda: drive.read_json("status", "scouts.json"), {}) or {}
    out = []
    for name, pg in (st.get("pages") or {}).items():
        leads = sorted(pg.get("lead_min") or [])
        out.append({"page": name, "posts": pg.get("posts"), "film_posts": pg.get("film_posts"), "first": pg.get("first"),
                    "lead_min": leads[len(leads) // 2] if leads else None, "kinds": pg.get("kinds"),
                    "names": sorted((pg.get("mentions") or {}).items(), key=lambda kv: -kv[1])[:6]})
    latest = sorted((x for pg in (st.get("pages") or {}).values() for x in pg.get("latest") or []), key=lambda x: x.get("at") or "", reverse=True)[:3]
    return {"since": st.get("since"), "pages": out, "learned": st.get("learned") or [], "checked": st.get("updated"), "latest": latest} if out else None


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
    out.update(runner_min=mins.get("minutes"), runner_limit="no limit" if mins.get("free") else mins.get("limit", ENGINE.get("runner", {}).get("minutes_month")),
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


class Once:
    """The Drive, read once: the panel is one snapshot, so each file is fetched a single time while it is built, and a
    folder's files are found with one listing instead of one search per file. Reading only; every write, and anything
    not found in the listing, goes to the real Drive. (Runner minutes: this step ends every job, AGENT.md 15.3.)"""

    def __init__(self, drive):
        self._d, self._texts, self._index = drive, {}, {}

    def __getattr__(self, name):
        return getattr(self._d, name)

    def _find(self, fid, name):
        if fid not in self._index:
            by = {}
            for it in self._d.children(fid):
                by.setdefault(it["name"], []).append(it)
            # the same choice as Drive.find_child when two files share a name
            self._index[fid] = {n: sorted(v, key=lambda x: self._d._is_mine(x))[0] for n, v in by.items()}
        return self._index[fid].get(name) or self._d.find_child(fid, name)

    def read_text(self, folder_path, name, default=None):
        key = (folder_path.strip("/"), name)
        if key not in self._texts:
            fid = self._d.folder(folder_path, create=False)
            f = self._find(fid, name) if fid else None
            self._texts[key] = self._d.read_bytes(f["id"]).decode("utf-8") if f else None
        t = self._texts[key]
        return default if t is None else t

    def read_json(self, folder_path, name, default=None):
        t = self.read_text(folder_path, name)
        return json.loads(t) if t else default


def build(drive, ctl=None):
    ctl = ctl or Control(drive)             # the real Drive: this takes in the Control Room's inbox first
    if hasattr(drive, "find_child") and hasattr(drive, "_is_mine"):
        drive = Once(drive)
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
    money_card = _safe(lambda: money(ctl, drive), {})
    radar = _safe(lambda: drive.read_json("status", "radar.json"), {})
    jobs_file = _safe(lambda: drive.read_json("status", "jobs.json"), {})
    P = {"v": 2, "updated": status.stamp(), "updated_iso": now.isoformat(timespec="seconds"),
         "switch": ctl.mode, "phase": ctl.phase, "approval": ctl.settings.get("approval"), "away": bool(ctl.settings.get("away_mode")),
         "respect": (respect or {}).get("why") if respect else None,
         "active": ctl.settings.get("active"), "volume": ctl.settings.get("volume"), "slots": ctl.settings.get("slots"),
         "day_plan": _safe(lambda: __import__("engine.dayplan", fromlist=["card"]).card(ctl), {}),
         "today": {"date": date, "reels": reels},
         "tomorrow": {"date": nxt, "slots": _safe(lambda: tomorrow(ctl, nxt), [])},
         "bank": {"ready": len(bank.reels("ready"))},
         "schedule": _safe(lambda: schedule(ctl, now), [])[:24],
         "numbers": nums, "series": _safe(lambda: series_cards(ctl, base, drive), []), "money": money_card,
         "usage": _safe(lambda: usage(ctl, drive, money_card), {}), "framework": _safe(lambda: framework_card(ctl), {}),
         "insights": _safe(lambda: __import__("engine.insights", fromlist=["build"]).build(drive.read_json("status", "metrics.json") or {}, now), {}),
         "calendar": _safe(lambda: __import__("engine.almanac", fromlist=["today"]).today(date, ctl.settings.get("slots") or []), {}) if ctl.on("calendar") else None,
         "scouts": _safe(lambda: scouts_card(drive), None), "radar": [{"title": x.get("title"), "rank": x.get("rank"), "sources": len(x.get("publishers") or {}), "fired": bool(x.get("fired_at"))}
                                                                      for x in (radar or {}).get("stories", [])[:5]], "radar_checked": (radar or {}).get("updated"),
         "page_rules": [{"id": n.get("id"), "text": n["text"], "at": n.get("at")} for n in ctl.notes()],
         "alerts": [{k: a.get(k) for k in ("id", "at", "level", "title", "what_happened", "what_was_done", "what_you_do")}
                    for a in (_safe(lambda: drive.read_json("status", "alerts.json"), {}) or {}).get("alerts", []) if a.get("open")][:6],
         "jobs": {k: {"result": v.get("result"), "at": v.get("at"), "run": v.get("run")} for k, v in ((jobs_file or {}).get("jobs") or {}).items()},
         "failed_runs": [f for f in (jobs_file or {}).get("failed") or [] if str(f.get("iso", ""))[:10] >= (now - dt.timedelta(days=7)).date().isoformat()][:15],
         "youtube": {"on": bool((ENGINE.get("youtube") or {}).get("enabled", True)), "privacy": (ENGINE.get("youtube") or {}).get("privacy", "private"),
                     "today": sum(1 for r in reels if r.get("youtube"))},
         "study": {**(_safe(lambda: drive.read_json("status", "study.json"), {}) or {}),
                   "sources": [{"name": c.get("name"), "where": c.get("platform"), "priority": c.get("priority"), "mode": c.get("study")}
                               for c in sorted((niche().get("competitors") or []), key=lambda c: c.get("priority", 9)) if isinstance(c, dict)]},
         "fresh_updates": ctl.on("fresh_updates"),
         "music": _safe(music_card, {}),
         "releases": _safe(lambda: __import__("engine.releases", fromlist=["card"]).card(date), {}),
         "digest": (_safe(lambda: drive.read_text("status", "digest.md"), "") or "")[:900],
         "manual": _safe(lambda: __import__("engine.manual", fromlist=["build"]).build(drive, now), {"count": 0, "jobs": []}),
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
    if P.get("inbox"):
        L.append(f"Inbox folder id: {P['inbox']}")
    if n.get("followers") is not None:
        diff = n["followers"] - n.get("target_today", n["followers"])
        L.append(f"Followers {n['followers']} of {n.get('goal')} · target line today {n.get('target_today')} ({'+' if diff >= 0 else ''}{diff}) · {n.get('days_left')} days left")
    L += ["", f"## TODAY {P['today']['date']} · {count('posted')} posted · {count('ready')} ready · {count('held') + count('failed')} held · {count('skipped')} skipped"]
    for r in reels:
        when = r.get("slot") or ("reserve" if r.get("reserve") else "-")
        link = r.get("posted") or r.get("video") or ""
        L.append(f"{r['n']}. {when} · {str(r.get('state')).upper()}{' (waits for post now)' if r.get('manual') and r.get('state') == 'ready' else ''} · {r['id']} · {r.get('series')} · \"{r.get('hook') or ''}\""
                 + (f" · {link}" if link else "") + (f" · YouTube: {r['youtube']}" if r.get("youtube") else "")
                 + (f" · note: {r['why'][:90]}" if r.get("why") else "") + (f" · {r['youtube_note'][:80]}" if r.get("youtube_note") else ""))
    if not reels:
        L.append("No reels made yet today.")
    fr = P.get("failed_runs") or []
    if fr:
        L += ["", f"## FAILED RUNS (7 days): {len(fr)}"] + [f"- {f.get('at')} · {f.get('job')} · {f.get('result')} · {f.get('run')}" for f in fr[:6]]
    yt = P.get("youtube") or {}
    L.append(f"YouTube: {'on' if yt.get('on') else 'off'} ({yt.get('privacy')}) · {yt.get('today', 0)} uploaded today")
    st = P.get("study") or {}
    if st.get("last"):
        L.append(f"Channel study: {st['last']}")
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
    u = P.get("usage") or {}
    r, v = u.get("runner") or {}, u.get("voice") or {}
    if r.get("free"):
        L.append("Runner minutes: no monthly limit (the repository is public). Nothing is slowed down to save minutes.")
    elif r.get("forecast"):
        L.append(f"Runner minutes are heading for {r['forecast']} of {r.get('limit')} by month end ({r.get('stage')})." + (f" At this pace they run out on {r['runs_out']}." if r.get("runs_out") else ""))
    if v.get("limit"):
        n_el, n_ms = v.get("reels_elevenlabs", 0), v.get("reels_microsoft", 0)
        L.append(f"Voice: ElevenLabs {v.get('used')} of {v.get('limit')} credits used, new credits on {v.get('resets')} · this month {n_el} reel{'s' if n_el != 1 else ''} with ElevenLabs, {n_ms} with the Microsoft backup")
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
    mw = P.get("manual") or {}
    if mw.get("jobs"):
        L += ["", f"## MANUAL WORK ({mw['count']} for your laptop · {mw.get('urgent', 0)} urgent)"]
        for j in mw["jobs"]:
            L += [f"- [{str(j['level']).upper()}] {j['title']} · due {j['due_text']} [{j['id']}]",
                  f"  why: {j['why'][:200]}", f"  if skipped: {'; '.join(j['suffers'][:3])}", f"  command: {j['command']}"]
        L.append("Run the command on your laptop, then press Done in Control Room › Manual work (or tell the chat: done <job id>).")
    else:
        L += ["", "## MANUAL WORK", "Nothing needs your laptop right now."]
    rl = P.get("releases") or {}
    if rl.get("recent") or rl.get("upcoming"):
        L += ["", "## RELEASES AND REVIEWS"]
        L += [f"- {r['film']} (out {r['date']}): Quick {'planned' if r.get('quick') else r.get('quick_state', '-')} · Trusted "
              f"{'planned' if r.get('trusted') else r.get('trusted_state', '-')}" for r in rl.get("recent", [])[:6]]
        L += ["- Next: " + ", ".join(f"{u['film']} {u['date'][5:]}" + (f" (moved from {u['moved_from'][5:]})" if u.get("moved_from") else "")
                                     for u in rl.get("upcoming", [])[:8])]
    mu = P.get("music") or {}
    if mu.get("trending"):
        L += ["", f"## TRENDING SONGS ({len(mu['trending'])} on the list; music-only reels, organic only)",
              "- " + " · ".join(f"{t.get('title')} [{t.get('key')}]" for t in mu["trending"][:8])]
    if P.get("alerts"):
        L += ["", f"## ALERTS ({len(P['alerts'])} open)"] + [f"- {a.get('at')} · {a.get('title')} · you: {a.get('what_you_do') or 'nothing'}" for a in P["alerts"]]
    if P.get("actions"):
        L += ["", "## YOUR LAST ACTIONS"] + [f"- [{a.get('id')}] {a.get('what')} → {a.get('outcome') or a.get('result')}" + (f" ({a['why']})" if a.get("why") else "")
                                             for a in P["actions"][:6]]
    ins = P.get("insights") or {}
    if ins.get("headline"):
        L += ["", "## INSIGHTS (worked out by code)", ins["headline"]] + [f"- {d['do']}: {d['why']}" for d in ins.get("do_next", [])[:4]]
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
