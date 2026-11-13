"""Brief job (AGENT.md 4.3, 15.1): the 1-page brief each thinking run starts from (data/brief.md), plus a copy of the
Control Room settings in data/control/ so the Brain needs no Drive access. Weekly and monthly runs also get
data/week_table.md. No AI, nothing posted.

    python -m engine.brief --run plan|refresh|breaking|weekly|monthly [--date YYYY-MM-DD]"""
import argparse
import datetime as dt
import json
import re
import statistics

import yaml

from .settings import AGENT, ROOT, niche_dir
from . import status
from .control import Control
from .day import Bank, Day, load_json_lines, today

OUT = ROOT / "data"


def mirror_control(drive):
    """Drive control/ → data/control/ (the switch, setting changes, feedback, one-off commands)."""
    d = OUT / "control"
    d.mkdir(parents=True, exist_ok=True)
    got = []
    for name in ("switch.json", "overrides.yaml", "feedback.jsonl", "commands.jsonl"):
        try:
            t = drive.read_text("control", name)
        except Exception:
            t = None
        if t is not None:
            (d / name).write_text(t if t.endswith("\n") else t + "\n", encoding="utf-8")
            got.append(name)
    return got


def story_series(lineup, date):
    """The shared story slot. A series with fixed days (Watch This Next: fri, sat, sun) takes those days; the others
    alternate by weekday over the rest, each by its days_per_week."""
    opts = next((s["story_slot"] for s in lineup.get("slots", []) if "story_slot" in s), [])
    if not opts:
        return None
    wd = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"][dt.date.fromisoformat(date).weekday()]
    for o in opts:
        if wd in [str(d).lower()[:3] for d in o.get("days") or []]:
            return o["series"]
    opts = [o for o in opts if not o.get("days")] or opts
    left = {o["series"]: float(o.get("days_per_week", 1)) for o in opts}
    total = sum(left.values())
    credit = {k: 0.0 for k in left}
    pick = None
    for _ in range(dt.date.fromisoformat(date).weekday() + 1):     # Monday first
        for k in credit:
            credit[k] += left[k] / total
        pick = max(credit, key=credit.get)
        credit[pick] -= 1
    return pick


def lineup_today(ctl, date):
    nd = niche_dir()
    name = ctl.settings.get("active", {}).get("lineup", "cinema-core")
    lineup = yaml.safe_load((nd / "lineups" / f"{name}.yaml").read_text(encoding="utf-8")) or {}
    rows = []
    for s in lineup.get("slots", []):
        sid = s.get("series") or story_series(lineup, date)
        if not sid:
            continue
        card = ctl.series(sid, nd)
        if ctl.series_paused(sid):
            rows.append(("-", sid, "paused", ""))
            continue
        n = int(s.get("per_day", 1))
        for t in (card.get("slots") or [])[:n]:
            v = card.get("voice")
            voice = ("voice: " + v.replace("_", " ")) if isinstance(v, str) else ("voice" if v else "no voice")
            rows.append((t, sid, card.get("template", "?"), f"{voice}, {'-'.join(map(str, card.get('length_s', [])))} s"))
    bank_target = next((int(s.get("bank_target", 0)) for s in lineup.get("slots", []) if s.get("bank_target")), 0)
    return sorted(rows), lineup, bank_target


def trailers(drive):
    """The trailers in the clip library, each with its shot grid, copied as text to data/trailers.json (shot times),
    so the planning run picks exact moments. Returns one short line per trailer for the brief."""
    try:
        idx = drive.read_json("clip-library", "index.json") or {"trailers": []}
    except Exception:
        idx = {"trailers": []}
    keep = [{k: t.get(k) for k in ("film", "kind", "file", "sheet", "duration", "shots")} for t in idx.get("trailers", [])]
    stills = [{"film": x["film"], "sheet": x["sheet"], "stills": [{k: it.get(k) for k in ("n", "kind", "date", "caption")} for it in x.get("stills", [])]}
              for x in idx.get("stills", [])]
    (OUT / "trailers.json").write_text(json.dumps({"trailers": keep, "stills": stills}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return [f"{t['film']} ({t['kind']}, {len(t.get('shots') or [])} shots, grid: clip-library/sheets/{t['sheet']})" for t in keep]


def table(rows, head):
    if not rows:
        return []
    return ["| " + " | ".join(head) + " |", "| " + " | ".join("---" for _ in head) + " |"] + ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]


def safe_json(drive, folder, name, default):
    try:
        return drive.read_json(folder, name) or default
    except Exception:
        return default


def pct(v):
    return "-" if v is None else f"{v * 100:.1f}%"


def changes(n=10):
    """The change log, newest first: one-line entries (`#n · ...`) and Harish's feedback rounds (## #n · ...)."""
    p = ROOT / "rules" / "changes.md"
    lines = [re.sub(r"^(##\s*|`)", "", l.strip()).strip("`") for l in p.read_text(encoding="utf-8").splitlines()
             if re.match(r"^(`|##\s*)#\d+", l.strip())] if p.exists() else []
    return [l[:170] for l in lines[:n]]


def metrics_rows(days):
    rows = []
    for mp in sorted((ROOT / "data" / "metrics").glob("20*.jsonl"))[-3:]:
        rows += load_json_lines(mp.read_text(encoding="utf-8"))
    cut = (status.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    return [r for r in rows if r.get("posted_at", "")[:10] >= cut]


# The number each series is judged on (its success_metric), as a rate the Measure job computes.
PRIORITY = {"sends_per_reach": "share_rate", "saves_and_sends": "share_rate", "saves_per_reach": "save_rate", "reach": "views"}
PLAIN = {"share_rate": "share rate", "save_rate": "save rate", "views": "views", "skip_rate": "skip rate"}


def change_entries():
    """Dated entries of rules/changes.md: (number, date, series or None for all, set by Harish?, text)."""
    p = ROOT / "rules" / "changes.md"
    out = []
    for l in (p.read_text(encoding="utf-8").splitlines() if p.exists() else []):
        m = re.match(r"^(?:`|##\s*)#(\d+)\s*·\s*(\d{1,2} \w{3} \d{4})\s*·\s*(.*)", l.strip())
        if not m:
            continue
        try:
            d = dt.datetime.strptime(m.group(2), "%d %b %Y").date()
        except ValueError:
            continue
        rest = m.group(3).strip("`")
        sm = re.match(r"\w+\s*\(([a-z0-9-]+)\)", rest)                 # "series (movie-recommendations) · ..."
        out.append((int(m.group(1)), d, sm.group(1) if sm else None, "Harish" in rest, rest[:90]))
    return out


def change_effects(rows):
    """Did each recent change help? Its series' priority number for 14 days before against 14 days after.
    A drop of auto_revert_drop (20%) or more on 5+ reels each side means: apply its Undo (AGENT.md 9.3).
    Harish's own rules are never undone by numbers; he is shown both (AGENT.md 8.4)."""
    drop = float(AGENT.get("learning", {}).get("auto_revert_drop", 0.2))
    nd, now = niche_dir(), dt.date.fromisoformat(today())
    out = []
    for n, d, sid, harish, text in change_entries():
        if (now - d).days > 42:
            continue
        card = {}
        if sid and (nd / "series" / sid / "series.yaml").exists():
            card = yaml.safe_load((nd / "series" / sid / "series.yaml").read_text(encoding="utf-8")) or {}
        k = PRIORITY.get(str(card.get("success_metric")), "share_rate")
        def vals(lo, hi):
            got = [r for r in rows if (sid is None or r.get("series") == sid) and lo <= r.get("posted_at", "")[:10] < hi]
            v = [r.get("views") if k == "views" else (r.get("rates") or {}).get(k) for r in got]
            return [x for x in v if x is not None]
        b = vals(str(d - dt.timedelta(days=14)), str(d))
        a = vals(str(d), str(d + dt.timedelta(days=15)))
        who = sid or "all series"
        if len(a) < 5 or len(b) < 5:
            out.append(f"- #{n} ({who}): too early to judge ({len(b)} reels before, {len(a)} after; 5 each needed)")
            continue
        bm, am = statistics.median(b), statistics.median(a)
        ch = (am - bm) / bm if bm else 0.0
        fmt = (lambda v: str(int(v))) if k == "views" else pct
        verdict = "keep"
        if ch <= -drop:
            verdict = "kept: Harish's own rule, show him these numbers" if harish else "REVERT: apply its Undo and log it"
        out.append(f"- #{n} ({who}): {PLAIN.get(k, k)} {fmt(bm)} → {fmt(am)} ({ch:+.0%}) · {verdict}")
    return out


def week_table():
    """data/week_table.md for the Weekly run: each series this week against its 14-day median (AGENT.md 2.3),
    then whether recent changes helped (auto-revert, AGENT.md 9.3)."""
    from .measure import RATES, LOWER_BETTER, colour
    week, base = metrics_rows(7), metrics_rows(21)
    lines = [f"# Week table · {today()} (computed by the Engine; rates per reach)", ""]
    learn = AGENT.get("learning", {})
    need_reels, need_days = int(learn.get("min_reels", 10)), int(learn.get("min_days", 14))
    first = min((r.get("posted_at", "")[:10] for r in metrics_rows(90)), default=None)
    days_known = (dt.date.fromisoformat(today()) - dt.date.fromisoformat(first)).days if first else 0
    if len(base) < need_reels or days_known < need_days:
        lines.append(f"Small numbers rule: {len(base)} reels measured over {days_known} days (need {need_reels} reels and "
                     f"{need_days} days). No rule changes this week.")
    for s in sorted({r.get("series") for r in week} | {"_page"}):
        w = [r for r in week if s == "_page" or r.get("series") == s]
        b = [r for r in base if s == "_page" or r.get("series") == s]
        if not w:
            continue
        rows, weakest = [], None
        for k in RATES:
            wv = [r["rates"][k] for r in w if r.get("rates", {}).get(k) is not None]
            bv = [r["rates"][k] for r in b if r.get("rates", {}).get(k) is not None]
            if not wv:
                continue
            wm, bm = statistics.median(wv), (statistics.median(bv) if bv else None)
            c = colour(wm, bm, k in LOWER_BETTER)
            weakest = weakest or (k if c in ("red", "amber") else None)
            rows.append((k, pct(wm), pct(bm), c))
        views = [r.get("views") or 0 for r in w]
        lines += ["", f"## {'Whole page' if s == '_page' else s} · {len(w)} reels · median views {int(statistics.median(views)) if views else 0}",
                  f"Weakest priority metric: {weakest or 'none below median'}"] + table(rows, ["metric", "this week", "14-day median", "health"])
    lines += ["", "## Did the recent changes help? (14 days before vs after, each series' own number)"] + \
        (change_effects(metrics_rows(90)) or ["- no changes in the last 6 weeks"])
    lines += ["", "## Changes in force (newest first)"] + [f"- {c}" for c in changes(8)]
    (OUT / "week_table.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build(drive, run, date):
    ctl = Control(drive)
    got = mirror_control(drive)
    day, bank = Day(drive, date), Bank(drive)
    slots, lineup, bank_target = lineup_today(ctl, date)
    plans_dir = ROOT / "plans" / date
    plans = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(plans_dir.glob("*.json")) if p.name != "respect.json"] if plans_dir.exists() else []
    main_plans = [p for p in plans if not p.get("reserve")]
    reserves = len(plans) - len(main_plans)
    from .post import respect_today
    respect = respect_today(drive, date, ctl)
    radar = safe_json(drive, "status", "radar.json", {"stories": []})
    metrics = safe_json(drive, "status", "metrics.json", {"reels": []})
    checks = safe_json(drive, "status", "checks.json", {"reels": {}})
    alerts = [a for a in safe_json(drive, "status", "alerts.json", {"alerts": []}).get("alerts", []) if a.get("open")][:5]
    minutes = safe_json(drive, "status", "minutes.json", {})
    storage = safe_json(drive, "status", "storage.json", {})
    try:
        from .budget import Budget
        b = Budget(drive).summary()
        money = f"Images ₹{b['spent_inr']:.0f} of ₹{b['cap_inr']:.0f} this month"
    except Exception:
        money = "Images: budget file not readable"
    base = int(ctl.settings.get("volume", {}).get("base", 6))
    feedback = [f for f in load_json_lines((OUT / "control" / "feedback.jsonl").read_text(encoding="utf-8"))
                if str(f.get("at", ""))[:10] >= (dt.date.fromisoformat(date) - dt.timedelta(days=2)).isoformat()] if (OUT / "control" / "feedback.jsonl").exists() else []
    breaking_today = sum(1 for r in day.reels() if r.get("series") == "breaking-news")
    nothing = None
    todo = []
    if ctl.mode == "sleep":
        nothing = "Nothing to do: the master switch says Sleep."
    elif run == "plan":
        if len(main_plans) >= base:
            nothing = f"Nothing to do: today's {len(main_plans)} plans are already in."
        else:
            todo.append(f"Plan {base - len(main_plans)} reel(s) for {date} at the slots below, plus {max(0, 2 - reserves)} reserve(s) "
                        f"(\"reserve\": true). Save each to plans/{date}/<reel_id>.json and check it with: python -m engine.plancheck <file>.")
    elif run == "refresh":
        todo.append("Breaking check: the top stories are below. Refresh tonight's updates only if better-proven news exists.")
        need = max(0, bank_target - len(bank.reels("ready")))
        todo.append(f"Breakdown bank: {len(bank.reels('ready'))} of {bank_target} ready." + (" Add 1 breakdown plan to plans/bank/." if need else " Full."))
        todo.append(f"Feedback: {len(feedback)} new item(s) in data/control/feedback.jsonl." if feedback else "Feedback: nothing new.")
        todo.append("Write the daily digest (6 lines at most, AGENT.md 16.4) to data/out/digest.md.")
    elif run == "breaking":
        cap = int(ctl.settings.get("budgets", {}).get("breaking_per_day", 2))
        if breaking_today >= cap:
            nothing = f"Nothing to do: already {breaking_today} breaking reels today (max {cap})."
        else:
            todo.append(f"Verify the lead in the trigger text with 2 trusted sources (niches/{AGENT['active']['niche']}/knowledge/sources.yaml). "
                        f"If confirmed: one plan in plans/{date}/ with series breaking-news and post_at = now. Breaking reels today: {breaking_today} of {cap}.")
    elif run == "weekly":
        week_table()
        lab = dt.date.fromisoformat(date).isocalendar()[1] % 2 == 0
        todo.append("Use skill weekly-learn on data/week_table.md." + (" Lab week: skill series-pitch (up to 3)." if lab else " Not a Lab week."))
        todo.append("Write the weekly report (AGENT.md 16.5) to data/out/weekly_report.md.")
    elif run == "monthly":
        week_table()
        g = ctl.settings.get("goal", {})
        start = dt.date.fromisoformat(str(g.get("start_date", date)))
        days = (dt.date.fromisoformat(date) - start).days
        line = g.get("start_followers", 0) + (g.get("followers", 1000) - g.get("start_followers", 0)) * min(1, days / max(1, g.get("by_days", 90)))
        fl = load_json_lines((ROOT / "data" / "metrics" / "followers.jsonl").read_text(encoding="utf-8")) if (ROOT / "data" / "metrics" / "followers.jsonl").exists() else []
        now_f = fl[-1]["followers"] if fl else None
        todo.append(f"Pace: {now_f if now_f is not None else '?'} followers on day {days}; the target line says {int(line)}.")
        todo.append("Write the monthly review to data/out/monthly_review.md.")
    L = [f"# Brief · {run} run · {date} (written {status.stamp()})", "",
         f"Switch: **{ctl.mode}** · Phase: **{ctl.phase}**" + (" (nothing posts; plan exactly as if live)" if ctl.phase != "live" else "")
         + f" · Respect mode: **{'ON: ' + respect.get('why', '') if respect else 'off'}** · Approval: {ctl.settings.get('approval')}",
         f"Control Room settings copied to data/control/: {', '.join(got) or 'none yet'}", ""]
    L += ["## To do", nothing] if nothing else ["## To do"] + [f"{i}. {t}" for i, t in enumerate(todo, 1)]
    rules = [f"- every series: {n['text']} ({n.get('at', '')})" for n in ctl.notes()]
    for p in sorted((niche_dir() / "series").glob("*/series.yaml")):
        rules += [f"- {p.parent.name}: {n['text']} ({n.get('at', '')})" for n in ctl.notes(p.parent.name)]
    if rules:
        L += ["", "## Harish's standing rules (set in the Control Room; follow them in every plan, AGENT.md 8.4)"] + rules
    ideas = [c for c in load_json_lines((OUT / "control" / "commands.jsonl").read_text(encoding="utf-8")) if c.get("cmd") == "idea"
             and str(c.get("at", ""))[:10] >= (dt.date.fromisoformat(date) - dt.timedelta(days=2)).isoformat()] if (OUT / "control" / "commands.jsonl").exists() else []
    if ideas and run in ("plan", "refresh"):
        L += ["", "## Ideas from Harish (leads, not orders: use one if it passes the worth-it test, AGENT.md 5.7)"] + [f"- {c['text'][:200]}" for c in ideas[-5:]]
    if run in ("plan", "refresh"):
        L += ["", f"## Today's slots ({date})"] + table(slots, ["time", "series", "template", "notes"])
        vids = trailers(drive)
        try:
            want = (drive.read_json("status", "trailers_wanted.json") or {}).get("films", [])
        except Exception:
            want = []
        L += ["", "## Pictures for the approved looks (AGENT.md 5.11, skill plan-reel)"]
        L += ["Breakdowns, updates, Watch This Next, reviews and breaking use official YouTube frames and posters, which the Engine "
              "fetches itself: an asset {\"src\": \"engine/.cache/stills/<film>/<YouTube id>_maxres2.jpg\"} (maxresdefault, maxres1, "
              "maxres2 or maxres3), or a poster with \"fetch\": {\"url\": ...}. Any film works; no film waits for the library. "
              "The YouTube ids of the trailers below are in their grid names, e.g. Kaithi [g79CvhHaj5I]."]
        L += ["", "## Trailers in the clip library (older looks: Guess the Movie, Artwork; and trailer ids for the frames above)"]
        L += [f"- {v}" for v in vids[:40]] or ["- None yet."]
        L += ["For an older look, open a film's grid (Google Drive) and pick the shot whose picture shows each line; shot times are "
              "in data/trailers.json. Check its timeline sheet (same folder, '... - timeline.jpg', a frame every 1.5 s): the tiles "
              "from your start second for as long as the line lasts (2-4 s) must all show what the line says. "
              "Older-look visual: {type: clip, film: <film>, start: <second>, len: 2.5, label: <2-word tag>}."]
        try:
            from .trailers import index as clip_index
            sts = clip_index(drive).get("stills", [])
        except Exception:
            sts = []
        if sts:
            L += ["", "## Official stills in the library (older looks; approved looks use the official frames above)"]
            L += [f"- {x['film']}: {len(x['stills'])} stills, grid: clip-library/sheets/{x['sheet']}" for x in sts[-20:]]
            L += ["Older-look visual: {type: image, still: {film: <film>, n: <number on the grid>}, ai: false, label: <2-word tag>}. "
                  "Pick the still that shows what the line says; skip stills that are mostly text."]
        try:
            from . import trailers as T
            asks = T.request_doc(drive)                       # Drive requests/trailers_to_get.md, Harish's ready command
            cal = (drive.read_json("status", "trailer_calendar.json") or {}).get("expected", [])
            idx = T.index(drive)
        except Exception:
            asks, cal, idx = [], [], {"trailers": []}
        if asks:
            L += ["", "## Trailers to get (Harish runs the laptop helper; the command is in Drive requests/trailers_to_get.md)",
                  f"Waiting: {', '.join(asks[:12])}. Plans for these wait until they arrive.",
                  "Researcher: for each, find the official YouTube trailer (studio or music label channel) and add a line "
                  "'Film = link' to data/notes/trailer_links.md, so the command has the exact video."]
            if run == "refresh":
                L += [f"Digest 'Needs you' line: {len(asks)} trailer(s) to get, command in Drive requests/trailers_to_get.md."]
        if cal:
            L += ["", "## Trailers expected (announced dates)"] + [f"- {x['film']}: {x['when']} ({x['headline'][:80]})" for x in cal[-8:]]
        new = [t for t in idx.get("trailers", []) if t.get("kind") in ("trailer", "teaser", "glimpse")
               and str(t.get("fetched", ""))[:10] >= (dt.date.fromisoformat(date) - dt.timedelta(days=3)).isoformat()]
        if new:
            L += ["", "## New trailers in the library (last 3 days)"] + [f"- {t['film']} ({t['kind']}, grid: clip-library/sheets/{t['sheet']})" for t in new[:6]]
            L += ["Flex slot: plan one trailer-breakdown (AGENT.md 5.13) for the newest of these that is a new release."]
        try:
            from .trailers import index as clip_index, have
            idx = clip_index(drive)
            ready = [(r["reel_id"], f) for r in day.reels() if r.get("state") == "held" for f in (r.get("waiting_for") or []) if have(f, idx)]
        except Exception:
            ready = []
        if ready:
            L += ["", "## Re-pick moments (the trailer has arrived)"] + [
                f"- {rid}: {f}'s grid is in the library now. Pick the shot for each line, write the start seconds into plans/{date}/{rid}.json, commit."
                for rid, f in ready]
        L += [f"Flex slots {', '.join(ctl.settings.get('flex_slots', []))}: trailer-breakdown when a new trailer lands, movie-review on release days, "
              "artwork-quote after a dull stretch."]
    if day.reels():
        L += ["", "## Today's reels"] + table([(r.get("slot") or "-", r["reel_id"], r.get("series", ""), r.get("state", ""), (r.get("reason") or "")[:60])
                                               for r in day.reels()], ["slot", "reel", "series", "state", "note"])
    elif plans:
        L += ["", f"Plans already in plans/{date}/: {', '.join(p.get('reel_id', '?') for p in plans)}"]
    y = (dt.date.fromisoformat(date) - dt.timedelta(days=1)).isoformat()
    yrows = [r for r in metrics.get("reels", []) if r.get("posted_at", "")[:10] == y]
    L += ["", "## Yesterday's numbers (per reach; colour against the series median)"]
    if yrows:
        L += table([(r["reel_id"], r.get("series"), r.get("views"), *[f"{pct(r['rates'].get(k))} {r['health'].get(k, '')}" for k in
                     ("skip_rate", "watch_through", "share_rate", "follow_rate")]) for r in yrows], ["reel", "series", "views", "skip", "watch", "share", "follow"])
    else:
        L.append("Nothing posted yesterday." if ctl.phase == "live" else "Rehearsal: nothing posted yet, so no numbers.")
    if run == "refresh" and checks.get("reels"):
        L += ["", "## Early numbers (2 hours after posting)"] + [f"- {v['reel_id']}: {v.get('views')} views, share {pct(v['rates'].get('share_rate'))}, skip {pct(v['rates'].get('skip_rate'))}"
                                                                  for v in list(checks["reels"].values())[-6:]]
    top = sorted(radar.get("stories", []), key=lambda s: -s.get("rank", 0))[:5]
    L += ["", "## Trends from the news watch (top 5, no AI; verify before use)"]
    L += [f"- [{s.get('rank')}] {s['title'][:110]} · {len(s.get('publishers', {}))} publishers ({s.get('trusted', 0)} trusted)" for s in top] or ["- No feed stories yet."]
    L += ["", "## Changes in force (newest first)"] + ([f"- {c}" for c in changes(5)] or ["- none"])
    if feedback:
        L += ["", "## New feedback from Harish"] + [f"- {f.get('reel_id') or f.get('series') or 'page'}: " + " · ".join(x for x in (f"rated {f['rating']}/5" if f.get("rating") else "", ", ".join(f.get("reasons") or []),
                                                    str(f.get("text", f.get("note", "")))[:140]) if x) for f in feedback[-5:]]
    if alerts:
        L += ["", "## Open alerts"] + [f"- {a['at']}: {a['title']}" for a in alerts]
    L += ["", "## Money and limits", f"- {money}",
          f"- Runner minutes: {minutes.get('minutes', '?')} of {minutes.get('limit', 2000)} this month",
          f"- Storage: {storage.get('gb', '?')} GB of {ctl.settings.get('budgets', {}).get('storage_gb', 8)} GB",
          "", "Plan forms: templates/<template>/plan_form.json · motion library: rules/motion.md · check: python -m engine.plancheck <file>"]
    (OUT / "brief.md").write_text("\n".join(l for l in L if l is not None) + "\n", encoding="utf-8")
    status.write(drive, "brief.json", {"run": run, "date": date, "nothing_to_do": bool(nothing)})
    print("\n".join(L[:12]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", default="plan", choices=["plan", "refresh", "breaking", "weekly", "monthly"])
    ap.add_argument("--date", default=None)
    a = ap.parse_args()
    from .drive import Drive
    build(Drive(), a.run, a.date or today())


if __name__ == "__main__":
    main()
