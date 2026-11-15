"""The day plan: how many reels each series makes a day, at which times, and whether the extras run (AGENT.md 12.3).
Harish sets it in the Control Room → Setup → Reels per day. One Save is one action, {"do": "day_plan", ...}, and one Undo.

Roles come from the active lineup file (niches/<niche>/lineups/<lineup>.yaml):
    regular  a lineup slot with its own series (per_day reels at the series' times)
    story    the shared story slot (one reel on the series' days)
    extra    flex series (trailer-breakdown, movie-review, ...) and the extra ones (breaking-news): "up to N", only when triggered
The counts live in control/overrides.yaml as series.<id>.per_day (and .slots); the total goes to settings.volume.base."""
import yaml

from .settings import niche_dir

MAX_PER_SERIES = 4
OFF_REGULAR = "Turned off in the Control Room (0 a day)."
OFF_EXTRAS = "Extras are off in the Control Room."


def lineup(settings):
    name = (settings.get("active") or {}).get("lineup", "cinema-core")
    p = niche_dir() / "lineups" / f"{name}.yaml"
    return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}


def roles(settings):
    """{series id: (role, lineup entry)} in lineup order."""
    out, L = {}, lineup(settings)
    for s in L.get("slots", []):
        if s.get("series"):
            out[s["series"]] = ("regular", s)
        for o in s.get("story_slot") or []:
            out[o["series"]] = ("story", o)
    for s in (L.get("flex") or []) + (L.get("extra") or []):
        out.setdefault(s["series"], ("extra", s))
    return out


def chosen(overrides, sid):
    """Harish's per_day for a series, or None when he never set one."""
    v = ((overrides.get("series") or {}).get(sid) or {}).get("per_day")
    return None if v is None else int(v)


def extras_on(settings):
    v = settings.get("extras")
    return bool(v.get("enabled", True)) if isinstance(v, dict) else True


def off(ctl, sid):
    """Why this series makes nothing today because of the day plan, in plain words (or None)."""
    role = roles(ctl.settings).get(sid, (None, None))[0]
    if role == "extra" and not extras_on(ctl.settings):
        return OFF_EXTRAS
    if chosen(ctl.overrides, sid) == 0:
        return OFF_REGULAR if role != "extra" else "Turned off in the Control Room."
    return None


def default_count(role, entry, card):
    if role == "regular":
        return int(entry.get("per_day", 1))
    if role == "story":
        return 1
    return int(entry.get("max") or card.get("per_day_max") or card.get("per_day") or 1)


def card(ctl):
    """What the Setup page shows and edits."""
    nd, rows, times = niche_dir(), [], set(ctl.settings.get("slots", []) + ctl.settings.get("flex_slots", []))
    for sid, (role, entry) in roles(ctl.settings).items():
        try:
            c = ctl.series(sid, nd)
        except Exception:
            continue
        if c.get("status") == "retired":
            continue
        n = chosen(ctl.overrides, sid)
        if sid == "breaking-news":
            n = int((ctl.settings.get("budgets") or {}).get("breaking_per_day", 2)) if (ctl.settings.get("breaking") or {}).get("enabled", True) else 0
        slots = list(c.get("slots") or [])
        rows.append({"id": sid, "name": c.get("name", sid), "role": role, "per_day": default_count(role, entry, c) if n is None else n,
                     "slots": slots, "days": entry.get("days") or c.get("days") or [], "paused": ctl.series_paused(sid),
                     "when": entry.get("trigger"), "max": 1 if role == "story" else (3 if role == "extra" else MAX_PER_SERIES)})
    vol = ctl.settings.get("volume") or {}
    return {"rows": rows, "times": sorted(times), "extras": extras_on(ctl.settings), "base": vol.get("base"),
            "min": 3, "max": int(vol.get("max", 8))}


def check(settings, overrides, want, series_card):
    """Checks one day plan. want = {series: {"per_day": n, "slots": [...]}}. Returns (series patch, settings patch, words, regular total).
    Raises ValueError in plain words."""
    R = roles(settings)
    timers = sorted(set(settings.get("slots", []) + settings.get("flex_slots", [])))
    patch, settings_patch, said = {}, {}, []
    for sid, w in (want or {}).items():
        if sid not in R:
            raise ValueError(f"'{sid}' is not in today's lineup")
        if not isinstance(w, dict):
            raise ValueError(f"{sid}: give per_day and slots")
        role, entry = R[sid]
        c = series_card(sid)
        top = 1 if role == "story" else (3 if role == "extra" else MAX_PER_SERIES)
        try:
            n = int(w.get("per_day"))
        except (TypeError, ValueError):
            raise ValueError(f"{c.get('name', sid)}: the number of reels must be 0 to {top}")
        if not 0 <= n <= top:
            raise ValueError(f"{c.get('name', sid)}: the number of reels must be 0 to {top}")
        slots = w.get("slots")
        if slots is not None:
            if role == "extra":
                raise ValueError(f"{c.get('name', sid)}: an extra posts when its news lands; its times are not set here")
            slots = [_time(x) for x in slots]
            bad = [x for x in slots if x not in timers]
            if bad:
                raise ValueError(f"{bad[0]} has no posting timer; pick one of {', '.join(timers)}")
            if len(set(slots)) < len(slots):
                raise ValueError(f"{c.get('name', sid)}: two reels at the same time")
        have = slots if slots is not None else list(c.get("slots") or [])
        if role != "extra" and n > len(have):
            raise ValueError(f"{c.get('name', sid)}: {n} a day needs {n} post times")
        if sid == "breaking-news":
            settings_patch.setdefault("budgets", {})["breaking_per_day"] = n
            settings_patch["breaking"] = {"enabled": n > 0}
        else:
            patch[sid] = {"per_day": n}
        if slots is not None:
            patch.setdefault(sid, {})["slots"] = slots
        said.append(f"{c.get('name', sid).split(' (')[0]} {'off' if n == 0 else (('up to ' if role == 'extra' else '') + str(n))}")
    # the whole day after the change: no two regular reels at one time, and the total inside the volume limits
    used, total, story_on = {}, 0, False
    for sid, (role, entry) in R.items():
        if role == "extra":
            continue
        c = series_card(sid)
        if c.get("status") in ("retired", "paused", "draft") or ((overrides.get("series") or {}).get(sid) or {}).get("paused"):
            continue
        p = patch.get(sid, {})
        n = p.get("per_day", chosen(overrides, sid))
        n = default_count(role, entry, c) if n is None else n
        if role == "story":
            story_on = story_on or n > 0
            continue
        total += n
        for t in (p.get("slots") or c.get("slots") or [])[:n]:
            if t in used and used[t] != sid:
                raise ValueError(f"{c.get('name', sid).split(' (')[0]} and {used[t]} both post at {t}; pick another time")
            used[t] = c.get("name", sid).split(" (")[0]
    total += 1 if story_on else 0
    vol = dict(settings.get("volume") or {})
    lo, hi = 3, int(vol.get("max", 8))
    if not lo <= total <= hi:
        raise ValueError(f"that makes {total} regular reels a day; it can be {lo} to {hi}")
    settings_patch["volume"] = {"base": total}
    return patch, settings_patch, said, total


def _time(x):
    hh, _, mm = str(x).strip().partition(":")
    if not (hh.isdigit() and mm.isdigit() and len(mm) == 2 and 0 <= int(hh) < 24 and 0 <= int(mm) < 60):
        raise ValueError(f"'{x}' is not a time; write it like 15:30")
    return f"{int(hh):02d}:{mm}"
