"""Release calendar and reviews (Harish, 22 Nov; AGENT.md 10.5). Code only, no AI, no keys.

The thinking runs keep niches/<niche>/knowledge/releases.yaml up to date (every Tamil release in the next 8 weeks). This
module keeps what they cannot be trusted to remember:
  history    every date change, recorded by code: data/releases_seen.json (old date, new date, the day it changed)
  hints      news headlines that mention a calendar film with "postponed", "new release date"... (from the news watch)
  reviews    for every film released in the last week: is its Quick Review planned (release day), its Trusted Review
             (1-4 days later)? What is due today, what was missed (an alert, once).

    python -m engine.releases --show [--date YYYY-MM-DD]     the calendar, the changes and the reviews due (no Drive)
"""
import argparse
import datetime as dt
import json
import re

import yaml

from .settings import ROOT, niche_dir
from . import status

SEEN = ROOT / "data" / "releases_seen.json"
QUICK, TRUSTED = "movie-review", "trusted-review"
MOVE_WORDS = re.compile(r"(?i)\b(postpone\w*|prepone\w*|delay\w*|pushed|new release date|release date|advanced|deferred|rescheduled|"
                        r"to release on|releasing on|now releas\w*|ott release|streaming from|premieres? on)\b")


def norm(s):
    return re.sub(r"[^a-z0-9]+", "", str(s or "").lower())


def calendar():
    try:
        rel = (yaml.safe_load((niche_dir() / "knowledge" / "releases.yaml").read_text(encoding="utf-8")) or {}).get("releases") or []
    except Exception:
        rel = []
    out = []
    for r in rel:
        try:
            out.append({**r, "date": dt.date.fromisoformat(str(r.get("date"))).isoformat()})
        except (ValueError, TypeError):
            continue                                    # a release with no clear date yet is not in the calendar
    return sorted(out, key=lambda r: (r["date"], str(r.get("film"))))


def critics():
    try:
        return yaml.safe_load((niche_dir() / "knowledge" / "critics.yaml").read_text(encoding="utf-8")) or {}
    except Exception:
        return {}


def track(cal, today):
    """Record new films and date changes since the last look (by code). Returns the state with each film's history."""
    try:
        seen = json.loads(SEEN.read_text(encoding="utf-8"))
    except Exception:
        seen = {"films": {}, "alerted": {}}
    films = seen.setdefault("films", {})
    for r in cal:
        k = norm(r.get("film"))
        cur = films.get(k)
        if not cur:
            films[k] = {"film": r.get("film"), "date": r["date"], "first_seen": today, "history": []}
        elif cur.get("date") != r["date"]:
            cur.setdefault("history", []).append({"from": cur.get("date"), "to": r["date"], "on": today})
            cur["date"] = r["date"]
    cut = (dt.date.fromisoformat(today) - dt.timedelta(days=60)).isoformat()
    seen["films"] = {k: v for k, v in films.items() if v.get("date", "9999") >= cut}
    seen["alerted"] = {k: v for k, v in (seen.get("alerted") or {}).items() if v >= cut}
    return seen


def save(seen):
    SEEN.parent.mkdir(parents=True, exist_ok=True)
    SEEN.write_text(json.dumps(seen, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def review_plans():
    """{normalised film: {"movie-review": [(date, id)], "trusted-review": [...]}} from the plan files."""
    out = {}
    for p in (ROOT / "plans").glob("20??-??-??/*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        sid = d.get("series")
        if sid not in (QUICK, TRUSTED):
            continue
        names = [(d.get("lead") or {}).get("film"), ((d.get("screens") or [{}])[0]).get("film"), (d.get("lead") or {}).get("topic")]
        out.setdefault("_all", []).append((sid, p.parent.name, d.get("id"), [norm(n) for n in names if n]))
    return out.get("_all", [])


def reviews_for(film, plans):
    k = norm(film)
    got = {QUICK: [], TRUSTED: []}
    for sid, date, rid, names in plans:
        if any(k and (k == n or k in n) for n in names):
            got[sid].append((date, rid))
    return got


def window():
    w = critics().get("window_days") or [1, 4]
    return int(w[0]), int(w[1])


def status_of(cal, today, plans=None):
    """Each film released in the last 7 days (and today): what is planned and what is due or missed."""
    plans = review_plans() if plans is None else plans
    t0, (w0, w1) = dt.date.fromisoformat(today), window()
    out = []
    for r in cal:
        age = (t0 - dt.date.fromisoformat(r["date"])).days
        if not 0 <= age <= 7 or str(r.get("status", "confirmed")) not in ("confirmed", "released"):
            continue
        got = reviews_for(r["film"], plans)
        q, tr = got[QUICK], got[TRUSTED]
        row = {"film": r["film"], "date": r["date"], "age": age, "where": r.get("where", "theatres"),
               "quick": q[0][1] if q else None, "trusted": tr[0][1] if tr else None}
        if not q:
            row["quick_state"] = "due today" if age == 0 else "missed"
        if not tr:
            row["trusted_state"] = "waiting for release" if age < w0 else ("due" if age <= w1 else "missed")
        out.append(row)
    return out


def hints(cal, stories, today):
    """Headlines about a calendar film that sound like a date change, for the thinking run to check."""
    t0 = dt.date.fromisoformat(today)
    soon = {norm(r["film"]): r for r in cal if -1 <= (dt.date.fromisoformat(r["date"]) - t0).days <= 60}
    out = []
    for s in stories or []:
        title = str(s.get("title") or "")
        if not MOVE_WORDS.search(title):
            continue
        nt = norm(title)
        for k, r in soon.items():
            if len(k) >= 4 and k in nt:
                out.append(f"{r['film']} (calendar: {r['date']}): \"{title[:120]}\"")
                break
    return list(dict.fromkeys(out))[:6]


def brief_lines(date, run, stories=None, drive=None):
    """The brief's release section: the calendar at a glance, date changes, news to check, reviews due and missed."""
    cal = calendar()
    seen = track(cal, date)
    save(seen)
    d0 = dt.date.fromisoformat(date)
    nxt = [r for r in cal if 0 <= (dt.date.fromisoformat(r["date"]) - d0).days <= 21]
    L = ["", "## Releases and reviews (knowledge/releases.yaml: every Tamil release in the next 8 weeks; AGENT.md 10.5)"]
    L.append(f"Calendar: {len(nxt)} film(s) in the next 21 days: " + (", ".join(f"{r['film']} {r['date'][5:]}" + ("" if r.get("status", "confirmed") == "confirmed" else " (tentative)")
                                                                        for r in nxt[:12]) or "none listed") + ".")
    moved = [(v["film"], h) for v in seen["films"].values() for h in v.get("history", []) if h.get("on", "") >= (d0 - dt.timedelta(days=7)).isoformat()]
    if moved:
        L.append("Date changes this week (recorded by code): " + "; ".join(f"{f}: {h['from']} → {h['to']}" for f, h in moved[:8]) + ".")
    hs = hints(cal, stories, date)
    if hs:
        L.append("News that may move a date (check in 2 sources; if it moved, change the date in releases.yaml, the history is kept by code):")
        L += [f"- {h}" for h in hs]
    today_f = [r["film"] for r in cal if r["date"] == date]
    tomorrow_f = [r["film"] for r in cal if r["date"] == (d0 + dt.timedelta(days=1)).isoformat()]
    if today_f:
        L.append(f"Releasing TODAY: {', '.join(today_f)}. Its 'out now' update takes the first morning slot (08:30, else the next open one). "
                 "A release on its day is never breaking news.")
    if tomorrow_f:
        L.append(f"Releasing TOMORROW: {', '.join(tomorrow_f)}. One 'releases tomorrow' news reel today (breaking-news Flash look: title, date, team, fact) "
                 "in an evening slot, unless the Plan run already made one.")
    st = status_of(cal, date)
    cr = critics()
    names = ", ".join(c["name"] for c in cr.get("trusted") or [])
    due = []
    for r in st:
        if r.get("quick_state") == "due today":
            due.append(f"- QUICK REVIEW (movie-review) for {r['film']}: "
                       + ("Refresh run writes it for 17:00 from the first reviews (at least "
                          f"{cr.get('min_quick', 2)} named critics or outlets). " if run == "refresh" else "Plan run: keep 17:00 free; the Refresh run writes it. ")
                       + "A 'rating' block, the 'stars' screen and the answer GO / WAIT / SKIP (templates/README.md, Verdict).")
        if r.get("trusted_state") == "due":
            due.append(f"- TRUSTED REVIEW (trusted-review) for {r['film']} (out {r['age']} day(s) ago, window ends on day {window()[1]})")
    if due:
        L += ["REVIEWS DUE (they stay on even when extras are off):"] + due
        if any("TRUSTED" in x for x in due):
            L.append(f"Trusted Review: only when at least {cr.get('min_trusted', 3)} of these have reviewed the film: {names}. Slots 17:00, then 18:00; "
                     "at most 2 a day (the oldest release first, the rest the next day). Too few in: wait, and say so in the digest.")
    missed = [f"{r['film']} ({'Quick' if r.get('quick_state') == 'missed' else ''}{' and ' if r.get('quick_state') == 'missed' and r.get('trusted_state') == 'missed' else ''}"
              f"{'Trusted' if r.get('trusted_state') == 'missed' else ''})" for r in st if "missed" in (r.get("quick_state"), r.get("trusted_state"))]
    if missed:
        L.append("Missed reviews: " + ", ".join(missed) + ". A Trusted Review can still go out today if the reviews are in; say so in the digest.")
    if drive is not None:
        alert_missed(drive, st, seen, date)
        save(seen)
    if not (today_f or tomorrow_f or due):
        L.append("No release today or tomorrow and no review due. Keep the calendar complete: add any confirmed date you find (2 sources).")
    return L


def alert_missed(drive, st, seen, today):
    """One Control Room alert per missed review (AGENT.md 10.5)."""
    al = seen.setdefault("alerted", {})
    for r in st:
        for kind, key in (("Quick Review", "quick_state"), ("Trusted Review", "trusted_state")):
            if r.get(key) != "missed":
                continue
            aid = f"{norm(r['film'])}:{kind}"
            if aid in al:
                continue
            al[aid] = today
            try:
                status.alert(drive, f"{kind} missed: {r['film']}", f"{r['film']} came out on {r['date']} and its {kind} was not planned in time.",
                             "The next thinking run is told to make it if the reviews are in.", "nothing, unless you want it skipped", level="warn")
            except Exception as e:
                print("missed-review alert not saved:", str(e)[:120])


def card(today):
    """For the Control Room: the calendar (next 21 days, date changes marked) and the review status of recent releases."""
    cal = calendar()
    try:
        seen = json.loads(SEEN.read_text(encoding="utf-8"))
    except Exception:
        seen = {"films": {}}
    d0 = dt.date.fromisoformat(today)
    up = []
    for r in cal:
        days = (dt.date.fromisoformat(r["date"]) - d0).days
        if 0 < days <= 21:
            h = (seen["films"].get(norm(r["film"])) or {}).get("history") or []
            up.append({"film": r["film"], "date": r["date"], "in_days": days, "where": r.get("where", "theatres"),
                       "tentative": r.get("status", "confirmed") != "confirmed", "moved_from": h[-1]["from"] if h else None})
    return {"upcoming": up[:20], "recent": status_of(cal, today),
            "critics": [{"name": c.get("name"), "outlet": c.get("outlet")} for c in critics().get("trusted") or []]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    ap.add_argument("--date", default=None)
    a = ap.parse_args()
    date = a.date or status.now().date().isoformat()
    print("\n".join(brief_lines(date, "plan")))
    print(json.dumps(card(date), ensure_ascii=False, indent=1)[:1500])


if __name__ == "__main__":
    main()
