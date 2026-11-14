"""Calendar awareness (AGENT.md 10.5). No AI: what day it is, what part of the week, which season, which festival or
birthday, and which words fit each slot's hour. Printed at the top of every brief and shown in the Control Room, so hooks
and titles fit today ("FRIDAY NIGHT: 4 FILMS", "RAINY NIGHT PICKS") instead of being timeless.
Everything comes from niches/<niche>/knowledge/calendar.yaml (settings, not code)."""
import datetime as dt

import yaml

from .settings import niche_dir

DOW = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


def load():
    p = niche_dir() / "knowledge" / "calendar.yaml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def _in_season(day, s):
    a, b, d = str(s.get("from")), str(s.get("to")), day.strftime("%m-%d")
    return a <= d <= b if a <= b else (d >= a or d <= b)


def part_of_day(hhmm, cal=None):
    for p in (cal or load()).get("day_parts") or []:
        if str(hhmm) <= str(p.get("until", "23:59")):
            return p
    return {}


def today(date, slots=(), cal=None):
    """Everything the calendar knows about one date: {day, mood, events, seasons, coming, angles, slots}."""
    cal = cal or load()
    day = dt.date.fromisoformat(str(date)[:10])
    wd = (cal.get("weekdays") or {}).get(DOW[day.weekday()]) or {}

    def on(d):
        return ([e for e in cal.get("dates") or [] if str(e.get("date")) == d.strftime("%m-%d")]
                + [e for e in cal.get("moving") or [] if str(e.get("date")) == d.isoformat()])
    events = on(day)
    seasons = [s for s in cal.get("seasons") or [] if _in_season(day, s)]
    coming = []
    for n in range(1, int(cal.get("look_ahead_days", 7)) + 1):
        d = day + dt.timedelta(days=n)
        coming += [{"name": e["name"], "on": d.isoformat(), "day": d.strftime("%a %d %b")} for e in on(d)]
    angles = []
    for src in events + seasons + [wd]:                    # the rarest reason first: a festival beats a season beats a weekday
        angles += [a.replace("{YEAR}", str(day.year)) for a in src.get("angles") or []]
    return {"date": day.isoformat(), "day": day.strftime("%A %d %b %Y"), "mood": wd.get("mood"),
            "events": [e["name"] for e in events], "seasons": [s["name"] for s in seasons], "coming": coming,
            "angles": list(dict.fromkeys(angles))[:8],
            "slots": [{"time": s, "part": part_of_day(s, cal).get("name"), "words": part_of_day(s, cal).get("words") or []} for s in slots]}


def lines(date, slots=()):
    """The same, as a few plain lines for the brief."""
    t = today(date, slots)
    if not t.get("mood") and not t["events"] and not t["seasons"]:
        return []
    out = [" · ".join(x for x in [t["day"], t.get("mood"), *t["events"], *[f"season: {s}" for s in t["seasons"]]] if x)]
    if t["coming"]:
        out.append("Coming up: " + " · ".join(f"{c['name']} ({c['day']})" for c in t["coming"][:6]))
    if t["slots"]:
        out.append("Words that fit each slot's hour: " + " · ".join(f"{s['time']} {s['part']}: {' / '.join(s['words'])}" for s in t["slots"] if s["words"]))
    if t["angles"]:
        out.append("Title angles for today (fill {N} and {FILM}; a film in today's news makes the strongest tie-in): " + " | ".join(t["angles"]))
    return out
