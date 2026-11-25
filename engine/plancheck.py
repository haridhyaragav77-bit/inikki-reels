"""Plan check (AGENT.md 5.10 "the standard", skill plan-reel). A plan that fails is not made.

    python -m engine.plancheck plans/2026-11-14/*.json

Says in plain words what is wrong. Errors stop the reel; notes do not.
Plans in the approved looks (Stage, Bulletin, Poster Wall, Verdict, Flash; templates/README.md) get check_look;
plans in the older looks (Cinematic, Diorama) get the earlier checks below it."""
import json
import re
import sys

import yaml

from .settings import ENGINE, ROOT, load_yaml, niche_dir

TAMIL = re.compile(r"[஀-௿]")
LATIN = re.compile(r"[A-Za-z]")
TEMPLATES = ("card", "cinematic", "diorama")
VISUALS = ("clip", "image", "meme", "split", "stack", "none", "mascot")


def form(template):
    with open(ROOT / "templates" / template / "plan_form.json", encoding="utf-8") as f:
        return json.load(f)


def _words(t):
    return len(re.sub(r"[*{}]", "", str(t or "")).split())


# ---------------------------------------------------------------- the approved looks (AGENT.md 6.6)
LOOK_KINDS = {
    "stage": {"title", "pins", "technique", "loop", "cards", "moral", "standoff", "timeline", "meter", "versus", "web",
              "detail", "chain", "quote", "source", "board", "climb", "track", "layers", "scene", "end"},
    "bulletin": {"title", "number", "bars", "ladder", "end"},
    "poster-wall": {"title", "film", "recap"},
    "verdict": {"title", "stamp", "scale", "critics", "who", "stars", "end"},
    "flash": {"title", "date", "team", "fact", "end"},
}
LAST_KIND = {"poster-wall": "recap"}          # every other look ends on "end"
SPEAKS = {"stage"}                            # looks that carry a voice: TURN SOUND ON + Tamil and Tanglish subtitles
TRANSITIONS = {"whip", "push", "zoom", "flash", "glitch", "wipe", "cut"}
SOUNDS = {"whoosh", "impact", "stamp", "tick", "pop", "glitch", "riser"}
DATED_ID = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$")
# the scene builder (AGENT.md 5.8, templates/stage/template.js `scene`): what a plan may name. The selftest keeps the icon list
# equal to the template's drawings.
SCENE_ICONS = {"camera", "film", "clapper", "mic", "spotlight", "screen", "person", "runner", "crowd", "car", "racecar", "bike", "train",
               "coach", "plane", "boat", "bridge", "building", "house", "tree", "mountain", "sun", "moon", "star", "cloud", "rain", "fire",
               "bomb", "blast", "gun", "knife", "phone", "clock", "hourglass", "heart", "eye", "crown", "key", "lock", "door", "book",
               "letter", "note", "trophy", "flag", "skull", "mask", "throne", "ball", "ticket", "question", "exclaim", "check", "cross",
               "arrow", "target", "pin", "dot"}
SCENE_ACTS = {"fall", "shake", "blast", "light", "spin", "grow", "fade", "pulse", "swap"}
SCENE_GROUNDS = {"floor", "road", "rail", "water", "city", "sky", "map", "grid", "none"}
SCENE_ENTER = {"pop", "drop", "slide", "rise", "fade"}
SCENE_COLORS = {"accent", "second", "white", "red"}
SCENE_LINKS = {"line", "string", "beam", "arrow"}


def mirror():
    """The Control Room's settings as the last brief copied them (data/control/overrides.yaml). The plan check reads them so a
    series changed on the page is checked as it now is, both here and in the Brain's session (which has no Drive)."""
    p = ROOT / "data" / "control" / "overrides.yaml"
    try:
        return (yaml.safe_load(p.read_text(encoding="utf-8")) or {}) if p.exists() else {}
    except Exception:
        return {}


def series_of(plan):
    """A series card as it stands: its file (or, for a series just added on the page, its Control Room card) with the
    Control Room's changes on top (AGENT.md 6.1)."""
    sid = str(plan.get("series") or "")
    p = niche_dir() / "series" / sid / "series.yaml"
    o = mirror()
    base = (load_yaml(p.relative_to(ROOT)) or {}) if sid and p.exists() else dict((o.get("new_series") or {}).get(sid) or {})
    extra = {k: v for k, v in ((o.get("series") or {}).get(sid) or {}).items() if k not in ("notes", "paused")}
    if extra:
        from .control import deep_merge
        base = deep_merge(base, extra)
    return base


def _label_words(t):
    return len([w for w in str(t or "").split() if re.search(r"\w", w)])


def _music_keys():
    with open(ROOT / "engine" / "music_index.json", encoding="utf-8") as f:
        keys = set(json.load(f)["tracks"])
    return keys | _trending_keys()


def _trending_keys():
    """This month's trending songs from the laptop run (data/music/trending.json, AGENT.md 5.4)."""
    try:
        return {t["key"] for t in json.loads((ROOT / "data" / "music" / "trending.json").read_text(encoding="utf-8")).get("tracks", [])}
    except (OSError, ValueError, KeyError):
        return set()


def _recommended_before(reel_id, also=None):
    """Films other reels have already recommended (knowledge/recommended_log.csv)."""
    import csv
    p = niche_dir() / "knowledge" / "recommended_log.csv"
    if not p.exists():
        return set()
    with open(p, encoding="utf-8") as f:
        return {r["film"].strip().lower() for r in csv.DictReader(f) if r.get("reel_id") not in (reel_id, also)}


def _walk(v, key):
    """Every value stored under `key` anywhere inside v."""
    if isinstance(v, dict):
        for k, x in v.items():
            if k == key:
                yield x
            yield from _walk(x, key)
    elif isinstance(v, list):
        for x in v:
            yield from _walk(x, key)


def recent_plans(template, rid, n=3):
    """The last `n` plans in the same look before this one (by their dated id), for the no-repeat rule (AGENT.md 5.8)."""
    out = []
    for p in (ROOT / "plans").glob("*/*.json"):
        if p.parent.name in ("reference", "samples") or p.name == "respect.json":      # samples are never posted
            continue
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        i = d.get("id") or d.get("reel_id") or ""
        if d.get("template") == template and DATED_ID.match(i) and i != rid and i[:10] <= rid[:10]:
            out.append(d)
    out.sort(key=lambda d: (d.get("id") or d.get("reel_id")), reverse=True)
    return out[:n]


def shape(plan):
    """A reel's build: its screens between the title and the end, in order."""
    return [s.get("kind") for s in (plan.get("screens") or [])[1:-1]]


def check_unique(plan, series, tpl, rid, E, W):
    """Every breakdown has its own design (AGENT.md 5.8): a design kit and a build the last reels did not use.
    Counts from the date in the series card (`unique_design.since`), so older plans are not held by a newer rule."""
    u = series.get("unique_design") or {}
    if not u or not DATED_ID.match(rid) or rid[:10] < str(u.get("since", "")):
        return
    if not ((mirror().get("settings") or {}).get("unique_designs") or {}).get("enabled", True):
        return                                          # switched off in the Control Room (Setup)
    kits, last = list(u.get("kits") or []), recent_plans(tpl, rid, int(u.get("window", 3)))
    d = plan.get("design")
    used = [x.get("design") for x in last if x.get("design")]
    free = [k for k in kits if k not in used]
    if not d or d not in kits:
        E.append(f"Name this reel's design kit in \"design\". Not used lately: {', '.join(free or kits)}.")
    elif d in used:
        E.append(f"The design kit '{d}' was used in the last {len(last)} breakdowns. Pick another: {', '.join(free)}.")
    mine = shape(plan)
    for x in last[:int(u.get("shape_window", 2))]:
        if shape(x) == mine:
            E.append(f"This reel is built from the same screens in the same order as {x.get('id')} ({' → '.join(mine)}). "
                     f"Change the build: other graphics that fit this film's idea ({', '.join(sorted(LOOK_KINDS[tpl] - {'title', 'end'}))}).")
            break
    if last and not (set(mine) - set(shape(last[0]))):
        W.append(f"Every graphic in this reel was also in the last one ({last[0].get('id')}). One fresh graphic keeps the page from looking the same.")


def films_lately(date, days, series_id="movie-updates", skip_id=""):
    """Films the series covered in the last `days` days (and today), from the plans on disk: {film key: [reel ids]}."""
    import datetime as _dt
    out = {}
    try:
        d0 = _dt.date.fromisoformat(date)
    except ValueError:
        return out
    for k in range(days + 1):
        folder = ROOT / "plans" / (d0 - _dt.timedelta(days=k)).isoformat()
        for f in sorted(folder.glob("*.json")) if folder.exists() else []:
            try:
                p = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            rid = str(p.get("id") or p.get("reel_id") or f.stem)
            if p.get("series") != series_id or rid == skip_id:
                continue
            key = film_key((p.get("lead") or {}).get("film")) or rid.split("update-", 1)[-1]
            out.setdefault(key, []).append(rid)
    return out


def film_key(name):
    return re.sub(r"[^a-z0-9]+", "-", str(name or "").lower()).strip("-")


def check_variety(plan, series):
    """Movie updates (Harish, 19 Nov): the same film at most once in `variety.film_days` days, unless real new news."""
    v = series.get("variety")
    rid = str(plan.get("id") or plan.get("reel_id") or "")
    if not v or rid[:10] < "2026-11-20":
        return []
    lead = plan.get("lead") or {}
    film = film_key(lead.get("film"))
    if not film:
        return ["Name the film in lead.film, so the page does not repeat one film (variety rule)."]
    seen = films_lately(rid[:10], int(v.get("film_days", 3)), plan.get("series"), rid)
    hits = [r for k, rs in seen.items() for r in rs if k == film or k.startswith(film + "-")]
    if hits and not str(lead.get("new_event") or "").strip():
        return [f"{lead.get('film')} was already covered lately ({', '.join(hits[:3])}). Pick another film, or write the real new news in lead.new_event."]
    return []


def source_of(text):
    """Which studied source a plan names in lead.inspired_by: a name from the niche competitors list, 'own', or None."""
    t = str(text or "").lower()
    if not t.strip():
        return None
    if "own idea" in t or t.strip() == "own":
        return "own"
    from .settings import niche
    for c in sorted((niche().get("competitors") or []), key=lambda c: -len(str(c.get("name", "")))):
        n = str(c.get("name", "")).lower().split(" (")[0]
        if n and n in t:
            return n
    return "other"


def check_rotation(plan, series):
    """Breakdowns rotate their sources (Harish, 19 Nov): not the same source as another breakdown of today or yesterday."""
    days = series.get("source_rotation")
    rid = str(plan.get("id") or plan.get("reel_id") or "")
    if days is None or rid[:10] < "2026-11-20" or plan.get("booked"):
        return []
    src = source_of((plan.get("lead") or {}).get("inspired_by"))
    if not src:
        return ["Name the source in lead.inspired_by: a name from the niche competitors list (or 'own idea'), so sources rotate (AGENT.md 10.3)."]
    if src in ("own", "other"):
        return []
    import datetime as _dt
    d0 = _dt.date.fromisoformat(rid[:10])
    for k in range(int(days) + 1):
        folder = ROOT / "plans" / (d0 - _dt.timedelta(days=k)).isoformat()
        for f in sorted(folder.glob("*.json")) if folder.exists() else []:
            try:
                p = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                continue
            if p.get("series") == plan.get("series") and str(p.get("id") or f.stem) != rid and source_of((p.get("lead") or {}).get("inspired_by")) == src:
                return [f"{p.get('id') or f.stem} already draws on {src}; pick another source for this breakdown (rotation, AGENT.md 10.3)."]
    return []


def check_spine(plan, series, screens):
    """The spine (AGENT.md 5.7): hook, lead, body, loop, body, loop, body, cta. Each screen names its beat; a beat may take
    more than one screen in a row. Only for series that have a spine, and only for plans made from 20 Nov on."""
    sp = series.get("spine")
    rid = str(plan.get("id") or plan.get("reel_id") or "")
    if not sp or rid[:10] < "2026-11-20":
        return []
    E, beats = [], [s.get("beat") for s in screens]
    if any(b is None for b in beats):
        return [f"Every screen names its beat ({', '.join(dict.fromkeys(sp))}); screens without one: "
                f"{', '.join(str(n) for n, b in enumerate(beats, 1) if b is None)} (AGENT.md 5.7)."]
    run = [b for k, b in enumerate(beats) if k == 0 or b != beats[k - 1]]
    if run != sp:
        E.append(f"The beats run {' > '.join(run)}; the spine is {' > '.join(sp)} (AGENT.md 5.7).")
    if beats[0] != "hook" or screens[0].get("kind") != "title":
        E.append("The hook is the title screen.")
    hw = len(str(screens[0].get("voice") or "").split())
    if hw > 12:
        E.append(f"The hook line has {hw} words; 6 to 10 land in 3 seconds.")
    for n, s in enumerate(screens, 1):
        w = len(str(s.get("voice") or "").split())
        if s.get("beat") == "loop" and w > 9:
            E.append(f"Screen {n} (open loop) has {w} words; a loop is a 1-3 s tease (9 words at most).")
        if w > 22:
            E.append(f"Screen {n} has {w} words; 8 to 18 a screen keeps the pace (split it).")
    return E


def check_new_graphics(plan, screens):
    """detail, chain, quote, source and the PART n/of badge: what each needs to draw (templates/README.md)."""
    E = []
    pt = plan.get("part")
    if pt is not None and not (isinstance(pt, list) and len(pt) == 2 and all(isinstance(x, int) for x in pt) and 1 <= pt[0] <= pt[1] <= 3):
        E.append("'part' is a film week's place, [n, of] with of at most 3, e.g. [1, 3] (AGENT.md 5.7).")
    from collections import Counter
    for k, c in Counter(s.get("kind") for s in screens).items():
        if plan.get("template") == "stage" and k not in ("title", "end") and c > 2:
            E.append(f"The '{k}' graphic is used {c} times; at most twice (once, plus one callback). Pick or build an illustration for this idea (AGENT.md 5.8).")
    for n, s in enumerate(screens, 1):
        k = s.get("kind")
        if k == "detail":
            sp = s.get("spot") or {}
            if not s.get("image"):
                E.append(f"Screen {n} (detail): needs the still with the detail in 'image'.")
            if not all(isinstance(sp.get(a), (int, float)) and 0 <= sp[a] <= 1 for a in ("x", "y")):
                E.append(f"Screen {n} (detail): 'spot' is where the detail is in the frame, {{x, y}} from 0 to 1.")
            c = s.get("count")
            if c is not None and not (isinstance(c, list) and len(c) == 2 and 1 <= c[0] <= c[1] <= 5):
                E.append(f"Screen {n} (detail): 'count' is [n, of], e.g. [1, 3].")
            if s.get("label") and _label_words(s["label"]) > 3:
                E.append(f"Screen {n} (detail): the label '{s['label']}' has more than 3 words (AGENT.md 5.8).")
        elif k == "chain":
            st = s.get("steps") or []
            if not 3 <= len(st) <= 5 or not all(isinstance(x, dict) and x.get("label") for x in st):
                E.append(f"Screen {n} (chain): 3 to 5 'steps', each {{label, cue}}; the last one is the payoff.")
            for x in st:
                if isinstance(x, dict) and _label_words(x.get("label")) > 3:
                    E.append(f"Screen {n} (chain): the step '{x.get('label')}' has more than 3 words (AGENT.md 5.8).")
        elif k == "quote":
            if not s.get("name") or not s.get("source"):
                E.append(f"Screen {n} (quote): needs 'name' (who said it) and 'source' (where: interview and year), AGENT.md 5.7.")
            if s.get("phrase") and _label_words(s["phrase"]) > 6:
                E.append(f"Screen {n} (quote): the key phrase has more than 6 words; the rest belongs in the voice.")
        elif k == "source":
            L, R = s.get("left") or {}, s.get("right") or {}
            if not (L.get("title") and R.get("title") and 2 <= len(L.get("beats") or []) <= 4 and 2 <= len(R.get("beats") or []) <= 4):
                E.append(f"Screen {n} (source): 'left' and 'right' each need a 'title' and 2 to 4 'beats' of {{label, cue}}.")
            nb = max(len(L.get("beats") or []), len(R.get("beats") or []))
            for x in s.get("links") or []:
                if not (isinstance(x, dict) and isinstance(x.get("from"), int) and isinstance(x.get("to"), int)
                        and x["from"] < len(L.get("beats") or []) and x["to"] < len(R.get("beats") or [])):
                    E.append(f"Screen {n} (source): each link is {{from: left beat number, to: right beat number, cue}}, counted from 0 (beats: {nb}).")
                    break
        elif k == "scene":
            E += check_scene(s, n)
    return E


def check_scene(s, n):
    """The scene builder (AGENT.md 5.8): props that exist, inside the box, acting on words the voice says."""
    E, voice = [], str(s.get("voice") or "")
    inbox = lambda v: isinstance(v, (int, float)) and -0.05 <= v <= 1.05
    props = s.get("props") or []
    if not 1 <= len(props) <= 8:
        E.append(f"Screen {n} (scene): 1 to 8 'props', each {{icon, x, y}} (templates/README.md).")
    if s.get("ground") is not None and s["ground"] not in SCENE_GROUNDS:
        E.append(f"Screen {n} (scene): ground '{s['ground']}' does not exist. Use one of: {', '.join(sorted(SCENE_GROUNDS))}.")
    ids = set()
    for k, p in enumerate(props, 1):
        if not isinstance(p, dict):
            E.append(f"Screen {n} (scene): prop {k} is not a {{icon, x, y}} object.")
            continue
        if p.get("id"):
            ids.add(p["id"])
        if p.get("icon") not in SCENE_ICONS:
            E.append(f"Screen {n} (scene): prop {k} icon '{p.get('icon')}' is not drawn yet. Use one of: {', '.join(sorted(SCENE_ICONS))}.")
        if not (inbox(p.get("x", .5)) and inbox(p.get("y", .5))):
            E.append(f"Screen {n} (scene): prop {k} 'x' and 'y' are places in the box, from 0 to 1.")
        if p.get("size") is not None and not (isinstance(p["size"], (int, float)) and 0.3 <= p["size"] <= 2.5):
            E.append(f"Screen {n} (scene): prop {k} 'size' runs from 0.3 to 2.5 (1 is a 160 px icon).")
        if p.get("count") is not None and not (isinstance(p["count"], int) and 1 <= p["count"] <= 8):
            E.append(f"Screen {n} (scene): prop {k} 'count' is 1 to 8 copies in a row.")
        if p.get("enter") is not None and p["enter"] not in SCENE_ENTER:
            E.append(f"Screen {n} (scene): prop {k} enters by {', '.join(sorted(SCENE_ENTER))}.")
        if p.get("color") is not None and p["color"] not in SCENE_COLORS:
            E.append(f"Screen {n} (scene): prop {k} colour is one of {', '.join(sorted(SCENE_COLORS))} (the reel's design kit sets the shades).")
        if p.get("label") and _label_words(p["label"]) > 3:
            E.append(f"Screen {n} (scene): the label '{p['label']}' has more than 3 words (AGENT.md 5.8).")
        if "path" in p:
            pa = p["path"]
            if not (isinstance(pa, list) and 2 <= len(pa) <= 8 and all(isinstance(q, list) and len(q) == 2 and inbox(q[0]) and inbox(q[1]) for q in pa)):
                E.append(f"Screen {n} (scene): prop {k} 'path' is 2 to 8 points [x, y] in the box, from 0 to 1.")
        for a in p.get("acts") or []:
            if not isinstance(a, dict) or a.get("do") not in SCENE_ACTS:
                E.append(f"Screen {n} (scene): prop {k} acts by {', '.join(sorted(SCENE_ACTS))}, each {{do, cue}}.")
            elif a["do"] == "swap" and a.get("icon") not in SCENE_ICONS:
                E.append(f"Screen {n} (scene): prop {k} 'swap' needs the new 'icon', one that is drawn.")
        for key in ("move_cue", "label_cue"):
            c = p.get(key)
            if isinstance(c, dict) and c.get("word") and c["word"] not in voice:
                E.append(f"Screen {n} (scene): prop {k} waits for the word '{c['word']}', which the voice line does not say.")
    for l in s.get("links") or []:
        if not isinstance(l, dict) or l.get("from") not in ids or l.get("to") not in ids:
            E.append(f"Screen {n} (scene): a link joins two props by their 'id' ({', '.join(sorted(ids)) or 'no ids yet'}).")
        elif l.get("style") is not None and l["style"] not in SCENE_LINKS:
            E.append(f"Screen {n} (scene): a link's style is one of {', '.join(sorted(SCENE_LINKS))}.")
        elif l.get("label") and _label_words(l["label"]) > 3:
            E.append(f"Screen {n} (scene): the link label '{l['label']}' has more than 3 words.")
    fo = s.get("focus")
    if fo is not None and not (isinstance(fo, dict) and (fo.get("on") in ids or (isinstance(fo.get("on"), list) and len(fo["on"]) == 2))
                               and 1 <= float(fo.get("to", 1.3)) <= 1.8):
        E.append(f"Screen {n} (scene): 'focus' is {{on: a prop id or [x, y], to: 1.1 to 1.8, cue}}.")
    c = s.get("counter")
    if c is not None:
        if not (isinstance(c, dict) and isinstance(c.get("to"), (int, float))):
            E.append(f"Screen {n} (scene): 'counter' is {{from, to, unit, cue}} with numbers.")
        elif "₹" in str(c.get("unit", "")) and not re.search(r"(?i)\b(cr|crore|lakh|l)\b", str(c.get("unit", ""))):
            E.append(f"Screen {n} (scene): the ₹ sign is only for money in crore or lakh (AGENT.md 5.7).")
    sc = s.get("slam_cue")
    if isinstance(sc, dict) and sc.get("word") and sc["word"] not in voice:
        E.append(f"Screen {n} (scene): the slam waits for the word '{sc['word']}', which the voice line does not say.")
    return E


def check_point(plan, series, screens):
    """One clear point, facts line by line, no formula phrases (Harish, 22 Nov; AGENT.md 5.7). Replaces the spine for plans
    from the date in the series card (`one_point.since`), so older plans are not held by a newer rule."""
    op = series.get("one_point") or {}
    rid = str(plan.get("id") or plan.get("reel_id") or "")
    if not op or rid[:10] < str(op.get("since", "9999")):
        return []
    E, lead = [], plan.get("lead") or {}
    point = str(lead.get("point") or "").strip()
    if not point:
        E.append("Write the reel's one point first, in 'lead.point': one sentence, what the viewer knows after watching (AGENT.md 5.7).")
    else:
        if len(point.split()) > int(op.get("point_words", 25)):
            E.append(f"'lead.point' has {len(point.split())} words; say the point in one sentence of {op.get('point_words', 25)} words or fewer. If it does not fit, the topic is not ready.")
        if len([x for x in re.split(r"[.!?](?:\s|$)", point) if x.strip()]) > 1:
            E.append("'lead.point' is more than one sentence. One point, one sentence.")
    srcs = lead.get("sources") or []
    if len(srcs) < int(op.get("min_sources", 2)):
        E.append(f"A breakdown checks its facts in at least {op.get('min_sources', 2)} sources; 'lead.sources' lists {len(srcs)}.")
    for k, sc in enumerate(screens, 1):
        if sc.get("kind") == "end":
            continue
        v = sc.get("src")
        ok = v == "analysis" or (isinstance(v, int) and 0 <= v < len(srcs)) or \
            (isinstance(v, list) and v and all(isinstance(x, int) and 0 <= x < len(srcs) for x in v))
        if not ok:
            E.append(f"Screen {k}: name where its fact comes from in 'src' (the number of the link in lead.sources, counted from 0, "
                     "or \"analysis\" for our own reasoning that adds no new fact). A claim without a source is cut.")
    text = json.dumps(screens, ensure_ascii=False).lower()
    for ph in series.get("avoid_phrases") or []:
        if str(ph).lower() in text:
            E.append(f"'{ph}' is a formula phrase (series card avoid_phrases). Tell this film's point in its own words (AGENT.md 5.7).")
    hero = series.get("hero_kinds") or []
    if hero and not any(sc.get("kind") in hero for sc in screens):
        E.append(f"Every breakdown has one hero visual drawn for its film: a 'scene' (the scene builder), or {', '.join(h for h in hero if h != 'scene')} "
                 "when one shows the thing itself (AGENT.md 5.8).")
    return E


def critics_cfg():
    try:
        return load_yaml((niche_dir() / "knowledge" / "critics.yaml").relative_to(ROOT)) or {}
    except Exception:
        return {}


def trusted_match(name, cfg):
    """The trusted reviewer a plan's name or outlet stands for (critics.yaml `match`), or None."""
    n = re.sub(r"[^a-z ]+", " ", str(name or "").lower()).strip()
    for c in cfg.get("trusted") or []:
        keys = [str(c.get("name", "")).lower()] + [str(m).lower() for m in c.get("match") or []]
        if any(k and (k == n or re.search(r"\b" + re.escape(k) + r"\b", n)) for k in keys):
            return c.get("name")
    return None


def rating_score(rating, cfg):
    """The combined score out of 5, worked out by code (AGENT.md 10.5): own stars as given, a verbal word by the fixed scale."""
    scale, vals = cfg.get("verbal_scale") or {}, []
    for c in rating.get("critics") or []:
        if isinstance(c.get("stars"), (int, float)) and 0 <= c["stars"] <= 5:
            vals.append(float(c["stars"]))
        elif c.get("verbal") in scale:
            vals.append(float(scale[c["verbal"]]))
    return (round(sum(vals) / len(vals) + 1e-9, 1), len(vals)) if vals else (None, 0)


def verdict_for(score, cfg):
    for v in sorted(cfg.get("verdicts") or [], key=lambda v: -float(v.get("min", 0))):
        if score >= float(v.get("min", 0)):
            return v
    return {}


def check_rating(plan, series, screens):
    """Quick and Trusted Reviews (Harish, 22 Nov; AGENT.md 10.5): the rating block, the score and the answer by code."""
    kind = series.get("rating")
    rid = str(plan.get("id") or plan.get("reel_id") or "")
    if not kind or rid[:10] < "2026-11-23":
        return []
    cfg, E = critics_cfg(), []
    rt = plan.get("rating") or {}
    crit = rt.get("critics") or []
    srcs = (plan.get("lead") or {}).get("sources") or []
    scale = cfg.get("verbal_scale") or {}
    if not crit:
        return ["A review carries a 'rating' block: critics [{name, outlet, stars (0-5) or verbal (" + ", ".join(scale) + "), quote, src}] (AGENT.md 10.5)."]
    names = []
    for k, c in enumerate(crit, 1):
        if not c.get("name") or not c.get("outlet"):
            E.append(f"Rating critic {k}: give the 'name' and the 'outlet'.")
        if not (isinstance(c.get("stars"), (int, float)) and 0 <= c["stars"] <= 5) and c.get("verbal") not in scale:
            E.append(f"Rating critic {k} ({c.get('name')}): give their own 'stars' (0-5) or a 'verbal' word: {', '.join(scale)}.")
        if not (isinstance(c.get("src"), int) and 0 <= c["src"] < len(srcs)):
            E.append(f"Rating critic {k} ({c.get('name')}): 'src' is the number of the link to their review in lead.sources (from 0).")
        if c.get("quote") and _label_words(c["quote"]) > 8:
            E.append(f"Rating critic {k}: the quote has more than 8 words.")
        names.append(trusted_match(c.get("name"), cfg) or trusted_match(c.get("outlet"), cfg))
    if kind == "trusted":
        bad = [c.get("name") for c, n in zip(crit, names) if not n]
        if bad:
            E.append(f"A Trusted Review uses only the trusted reviewers (knowledge/critics.yaml); not on the list: {', '.join(map(str, bad))}.")
        got = len({n for n in names if n})
        if got < int(cfg.get("min_trusted", 3)):
            E.append(f"A Trusted Review needs at least {cfg.get('min_trusted', 3)} trusted reviewers; this one has {got}. Wait until more are in.")
    elif len(crit) < int(cfg.get("min_quick", 2)):
        E.append(f"A Quick Review needs at least {cfg.get('min_quick', 2)} named reviews for its early rating; this one has {len(crit)}.")
    score, n = rating_score(rt, cfg)
    if score is None:
        return E
    v = verdict_for(score, cfg)
    if rt.get("score") != score:
        E.append(f"The combined score works out to {score} (the average of {n} reviews); put \"score\": {score} in 'rating' and on the stars screen.")
    if rt.get("verdict") != v.get("word"):
        E.append(f"A score of {score} means {v.get('word')} ({v.get('line')}); put \"verdict\": \"{v.get('word')}\" in 'rating' and on the stars screen.")
    st = [x for x in screens if x.get("kind") == "stars"]
    if not st:
        E.append("Add the 'stars' screen right after the title: the score out of 5 and the answer (templates/README.md, Verdict).")
    else:
        x = st[0]
        if x.get("score") != score or x.get("verdict") != v.get("word") or x.get("line") != v.get("line"):
            E.append(f"The stars screen shows score {x.get('score')} / {x.get('verdict')} / {x.get('line')}; it must be {score} / {v.get('word')} / {v.get('line')}.")
        if screens.index(x) > 1:
            E.append("The stars screen comes right after the title: the answer first.")
    return E


def cooling(series, rid, tpl="stage"):
    """Stock graphics still cooling down (series card graphics_cooldown, AGENT.md 5.8): {kind: the plan that used it}."""
    cd = series.get("graphics_cooldown") or {}
    if not cd:
        return {}
    last = recent_plans(tpl, rid, max(int(v) for v in cd.values()))
    out = {}
    for kind, n in cd.items():
        for d in last[:int(n)]:
            if kind in [x.get("kind") for x in d.get("screens") or []]:
                out[kind] = d.get("id") or d.get("reel_id")
                break
    return out


def check_cooldown(plan, series, screens):
    op = series.get("one_point") or {}
    rid = str(plan.get("id") or plan.get("reel_id") or "")
    if not op or rid[:10] < str(op.get("since", "9999")) or not DATED_ID.match(rid):
        return []
    if not ((mirror().get("settings") or {}).get("unique_designs") or {}).get("enabled", True):
        return []
    used, E = cooling(series, rid, plan.get("template") or series.get("template") or "stage"), []
    cd = series.get("graphics_cooldown") or {}
    for kind in dict.fromkeys(sc.get("kind") for sc in screens):
        if kind in used:
            E.append(f"The '{kind}' graphic is cooling down: {used[kind]} used it, and it may come back after {cd[kind]} other breakdown"
                     f"{'s' if int(cd[kind]) != 1 else ''} (AGENT.md 5.8). Show this idea with a scene drawn for this film instead.")
    return E


def check_look(plan, series):
    """A plan in an approved look, against the standard for every reel (AGENT.md 5.10). Returns (errors, notes)."""
    E, W = [], []
    sid = plan.get("series")
    tpl = plan.get("template") or series.get("template")
    rid = plan.get("id") or plan.get("reel_id") or ""
    if not series:
        E.append(f"Series '{sid}' has no settings card in this niche.")
    if not DATED_ID.match(rid):
        E.append("The plan's 'id' must start with its date, e.g. 2026-11-14-breakdown-kaithi.")
    if series.get("template") and series["template"] != tpl:
        E.append(f"Series '{sid}' has its own look, '{series['template']}'; this plan asks for '{tpl}' (AGENT.md 6.6).")
    screens = plan.get("screens") or []
    if not screens:
        return E + ["The plan has no screens."], W
    kinds = [s.get("kind") for s in screens]
    for n, k in enumerate(kinds, 1):
        if k not in LOOK_KINDS[tpl]:
            E.append(f"Screen {n}: '{k}' is not a screen of the {tpl} look. Use one of: {', '.join(sorted(LOOK_KINDS[tpl]))}.")
    if kinds[0] != "title":
        E.append("Screen 1 must be the title screen: the film and what the reel is, big and clear (AGENT.md 5.3).")
    if kinds[-1] != LAST_KIND.get(tpl, "end"):
        E.append(f"The last screen must be '{LAST_KIND.get(tpl, 'end')}': the send prompt with the page name (AGENT.md 5.3).")

    # value first: the worth-it test is answered before the script (AGENT.md 5.7)
    lead, worth = plan.get("lead") or {}, plan.get("worth_it") or {}
    if not lead.get("topic"):
        E.append("The plan has no 'lead.topic'.")
    if len([v for v in worth.values() if str(v).strip()]) < 2:
        E.append("Answer the worth-it test before the script, in 'worth_it' (AGENT.md 5.7).")
    need = int(series.get("proof_required") or 0)
    if sid == "movie-recommendations" and not lead.get("person"):
        need = 0                                            # proof of the list itself is only for "They recommend"
    if need and len(lead.get("sources") or []) < need:
        E.append(f"This series needs {need} trusted sources that agree; 'lead.sources' lists {len(lead.get('sources') or [])}.")

    # screens: how each arrives, sounds, length of each screen, pictures
    assets = plan.get("assets") or {}
    voiced = bool((plan.get("voice") or {}).get("on"))
    for n, s in enumerate(screens, 1):
        if s.get("in") and s["in"] not in TRANSITIONS:
            E.append(f"Screen {n}: transition '{s['in']}' does not exist. Use one of: {', '.join(sorted(TRANSITIONS))}.")
        for fx in s.get("sfx") or []:
            if isinstance(fx, dict) and fx.get("type") not in SOUNDS:
                W.append(f"Screen {n}: sound '{fx.get('type')}' does not exist and is skipped.")
        if not s.get("voice") and not s.get("dur"):
            E.append(f"Screen {n} has no voice line and no 'dur' (seconds), so its length is unknown.")
        if s.get("voice") and not voiced:
            E.append(f"Screen {n} has a voice line, but the reel's voice is off.")
        for key in ("image", "posters"):
            for v in _walk(s, key):
                for name in (v if isinstance(v, list) else [v]):
                    if isinstance(name, str) and name not in assets:
                        E.append(f"Screen {n} uses the picture '{name}', which is not in 'assets'.")
        for v in _walk(s, "text") if s.get("kind") == "pins" else []:
            if _label_words(v) > 3:
                W.append(f"Screen {n}: the label '{v}' has more than 3 words (AGENT.md 5.8).")
        for cue in _walk(s, "cue"):
            if isinstance(cue, dict) and cue.get("word") and cue["word"] not in str(s.get("voice") or ""):
                E.append(f"Screen {n}: a graphic waits for the word '{cue['word']}', which the voice line does not say.")
        for cue in (s.get("cues") or {}).values() if isinstance(s.get("cues"), dict) else []:
            if isinstance(cue, dict) and cue.get("word") and cue["word"] not in str(s.get("voice") or ""):
                E.append(f"Screen {n}: a graphic waits for the word '{cue['word']}', which the voice line does not say.")

    # the breakdown graphics added on 19 Nov (AGENT.md 5.8) and the film-week badge (5.7)
    E += check_new_graphics(plan, screens)
    E += check_spine(plan, series, screens)
    E += check_point(plan, series, screens)
    if not plan.get("reference"):                    # a reference plan is an example, not a reel in the day's sequence
        E += check_cooldown(plan, series, screens)
        E += check_variety(plan, series)
        E += check_rotation(plan, series)

    # voice: sound-on prompt and subtitles come with it (AGENT.md 5.3)
    if voiced:
        if tpl not in SPEAKS:
            E.append(f"The {tpl} look has no subtitles yet, so this reel must be music-only: set voice.on to false (AGENT.md 5.3).")
        if plan.get("subtitles") is False:
            E.append("Voiced reels carry Tamil + Tanglish subtitles: remove 'subtitles: false' (AGENT.md 5.3).")
        for n, s in enumerate(screens, 1):
            ta, tg = str(s.get("voice") or ""), str(s.get("voice_tg") or "")
            if not ta:
                continue
            if not TAMIL.search(ta):
                E.append(f"Screen {n}: the voice line is not in Tamil script.")
            if not tg:
                E.append(f"Screen {n}: the voice line has no Tanglish line ('voice_tg') for the subtitles.")
            elif TAMIL.search(tg):
                E.append(f"Screen {n}: the Tanglish line has Tamil letters in it. Write it in English letters.")
            elif len(ta.split()) != len(tg.split()):
                E.append(f"Screen {n}: the Tanglish line has {len(tg.split())} words and the Tamil line {len(ta.split())}. "
                         "They must match word for word, or the subtitles drift.")

    # music: on frame 1, 1-3 parts that follow the story, from the library (AGENT.md 5.4)
    secs = (plan.get("music") or {}).get("sections") or []
    if not secs:
        E.append("The plan has no music. Music starts on frame 1 and follows the story (AGENT.md 5.4).")
    else:
        f0 = secs[0]
        if ("screen" in f0 and f0["screen"] != 0) or ("screen" not in f0 and float(f0.get("at", 0)) > 0):
            E.append("The music must start on frame 1: the first music part starts on screen 0.")
        if len(secs) > 3:
            W.append(f"{len(secs)} music parts; 1 to 3 that follow the story work best (AGENT.md 5.4).")
        keys, trend = _music_keys(), _trending_keys()
        tcfg = ((ENGINE.get("music") or {}).get("trending") or {})
        if voiced and not tcfg.get("voiced", False) and any(sec.get("track") in trend for sec in secs):
            E.append("Trending songs go on music-only reels (AGENT.md 5.4): if Instagram mutes a matched song, a voiced reel loses its voice "
                     "too. Use the library music for this one.")
        for sec in secs:
            if sec.get("track") not in keys:
                E.append(f"Music track '{sec.get('track')}' is not in engine/music_index.json, so the Engine cannot fetch it.")
            if "screen" in sec and not 0 <= int(sec["screen"]) < len(screens):
                E.append(f"Music track '{sec.get('track')}' starts on screen {sec['screen']}, which does not exist.")

    # length: set by the content, inside the series range (AGENT.md 5.9)
    lo, hi = series.get("length_s") or [10, 75]
    top = series.get("length_max_s", hi)
    pl = plan.get("length_s") or [lo, hi]
    st = series.get("strict_length")
    if isinstance(st, dict) and rid[:10] >= str(st.get("since", "")) and pl[0] < lo:
        E.append(f"The plan aims at {pl[0]}-{pl[1]} s; this series runs {lo}-{hi} s and never shorter (Harish, 25 Nov). Set length_s to start at {lo}.")
    if pl[1] > top:
        E.append(f"The plan allows {pl[1]} s; this series allows {top} s at most.")
    if pl[1] > 45 and not plan.get("length_reason"):
        E.append("Over 45 seconds needs a reason in 'length_reason' (AGENT.md 5.9).")
    if not voiced:
        est = sum(float(s.get("dur") or 0) for s in screens)
        if est and not pl[0] - 1 <= est <= pl[1] + 1:
            W.append(f"The screens add up to about {est:.1f} s; the plan allows {pl[0]} to {pl[1]} s.")
    rate = float((series.get("length_estimate") or {}).get("sec_per_letter") or 0)
    if voiced and rate and isinstance(st, dict) and rid[:10] >= str(st.get("since", "")):
        letters = sum(len(str(s.get("voice") or "").replace(" ", "")) for s in screens)
        est = round(letters * rate)       # measured on posted reels (AGENT.md 5.9)
        if est < lo:
            E.append(f"The reel will run about {est} s (its voice has {letters} letters); this series runs {lo}-{hi} s and never shorter "
                     f"(Harish, 25 Nov). Add about {round((lo - est) / rate) + 20} more letters of voice: one more real detail, the why or "
                     "the payoff (a new screen or fuller lines), never padding.")
        elif est > top + 3:
            W.append(f"The reel will run about {est} s (its voice has {letters} letters); this series allows {top} s at most. Tighten a line or two.")

    # series rules that code can check
    if sid == "film-breakdown":
        if not lead.get("insight"):
            E.append("Value first: the plan has no 'lead.insight' (AGENT.md 5.7).")
        tech = [s for s in screens if s.get("kind") == "technique"]
        optional = rid[:10] >= str((series.get("one_point") or {}).get("since", "9999"))   # 22 Nov: no longer a fixed screen
        if not tech and not optional:
            E.append("Every breakdown pins a named technique (AGENT.md 5.7): add a 'technique' screen with its name and definition.")
        elif tech:
            t = tech[0]
            if not t.get("name"):
                E.append("The technique screen has no 'name' (for example FRAME STORY).")
            if not t.get("definition"):
                E.append("The technique screen has no 'definition'.")
            elif _label_words(t["definition"]) > 6:
                W.append(f"The definition '{t['definition']}' is long; 6 words or fewer read best.")
            if t.get("name") and str(t["name"]).lower() not in str(screens[-1].get("recap", "")).lower():
                E.append(f"The end card must recap the technique, e.g. \"recap\": \"TECHNIQUE: {t['name']}\".")
    if tpl == "stage":
        if not plan.get("reference"):
            check_unique(plan, series, tpl, rid, E, W)
        need = {"timeline": ("heading", "events"), "meter": ("heading", "levels"), "versus": ("left", "right"), "web": ("center", "nodes")}
        for n, s in enumerate(screens, 1):
            for f in need.get(s.get("kind"), ()):
                if not s.get(f):
                    E.append(f"Screen {n} ({s['kind']}): '{f}' is missing (templates/README.md).")
            if s.get("kind") == "web" and not 3 <= len(s.get("nodes") or []) <= 6:
                E.append(f"Screen {n} (web): 3 to 6 people or things around the centre.")
            if s.get("kind") == "timeline" and not 2 <= len(s.get("events") or []) <= 5:
                E.append(f"Screen {n} (timeline): 2 to 5 moments.")
    if tpl == "poster-wall":
        pace = series.get("pace") or {}
        since = str(pace.get("since", "9999"))
        t0 = screens[0]
        if rid[:10] >= since:
            if series.get("timely_titles", True) and not t0.get("kicker"):
                E.append("The title screen needs a 'kicker': 2-4 words that tie the list to today (the day, the hour, the season or a film in "
                         "the news), from the brief's Today lines, e.g. FRIDAY NIGHT WATCHLIST.")
            for n, s in enumerate(screens, 1):
                lim = pace.get("title_s") if s.get("kind") == "title" else pace.get("film_s") if s.get("kind") == "film" else pace.get("recap_s")
                if len([x for x in screens if x.get("kind") == "film"]) == 1 and s.get("kind") == "film":
                    lim = pace.get("single_film_s")
                if lim and float(s.get("dur", 0)) > float(lim):
                    E.append(f"Screen {n} ({s.get('kind')}) runs {s.get('dur')} s; this series moves fast: {lim} s at most.")
                if s.get("kind") == "film":
                    if not s.get("plot"):
                        E.append(f"{s.get('title') or 'Screen ' + str(n)}: no 'plot' (one sentence, no spoilers; it becomes the plot beat after the card).")
                    elif _label_words(s["plot"]) > 16:
                        E.append(f"{s.get('title')}: the plot has {_label_words(s['plot'])} words; 16 or fewer.")
                    for b in s.get("plot_beats") or []:
                        if _label_words(b) > 6:
                            E.append(f"{s.get('title')}: the plot beat '{b}' is long; 6 words or fewer.")
        films = [(n, s) for n, s in enumerate(screens, 1) if s.get("kind") == "film"]
        if len(films) not in (1, 3, 4, 5):
            W.append(f"{len(films)} films; a list is 3 to 5 (or one film you missed).")
        before = _recommended_before(rid, plan.get("remake_of"))     # a new version of a posted reel keeps its films
        for n, s in films:
            name = str(s.get("title") or f"screen {n}")
            r = s.get("rating")
            if not isinstance(r, (int, float)) or not 0 < r <= 5:
                E.append(f"{name}: no Letterboxd rating (a number out of 5).")
            if not s.get("proof"):
                E.append(f"{name}: no award, festival or famous fact ('proof').")
            if not s.get("watch"):
                E.append(f"{name}: no 'watch' (where to watch in India, checked on JustWatch on the day).")
            if not s.get("reason"):
                E.append(f"{name}: no reason to watch.")
            elif _label_words(s["reason"]) > 6:
                E.append(f"{name}: the reason has {_label_words(s['reason'])} words; 6 or fewer.")
            if name.lower() in before:
                E.append(f"{name} was recommended before (recommended_log.csv). Never recommend a film twice.")
    if tpl == "verdict":
        for c in (c for s in screens if s.get("kind") == "critics" for c in s.get("cards") or []):
            if not c.get("critic") or not c.get("outlet"):
                E.append("Every critic quote is named: give the critic and the outlet.")
        E += check_rating(plan, series, screens)

    vir = plan.get("virality") or {}
    if isinstance(vir.get("value"), (int, float)) and vir["value"] < 6:
        E.append("The Value score is under 6, so the reel fails whatever its total (AGENT.md 5.2).")

    # the post itself
    pk = plan.get("package") or {}
    if not pk.get("cover"):
        E.append("No cover title in 'package.cover' (it names the reel in Drive and on the grid).")
    if not pk.get("caption"):
        E.append("No caption in 'package.caption'.")
    tags = pk.get("hashtags") or []
    if not 3 <= len(tags) <= 5:
        W.append(f"The caption has {len(tags)} hashtags (3 to 5 is the rule).")
    if not (pk.get("slot") or plan.get("slot") or plan.get("post_at")):
        W.append("No slot: the reel will be made, but it has no posting time.")
    return E, W


def check(plan):
    """Returns (errors, warnings) as lists of plain sentences."""
    series = series_of(plan)
    if (plan.get("template") or series.get("template")) in LOOK_KINDS:
        return check_look(plan, series)
    E, W = [], []
    for k in ("reel_id", "series", "screens"):
        if not plan.get(k):
            E.append(f"The plan has no '{k}'.")
    if E:
        return E, W
    sdir = niche_dir() / "series" / str(plan["series"]) / "series.yaml"
    series = load_yaml(sdir.relative_to(ROOT)) if sdir.exists() else {}
    if not series:
        W.append(f"Series '{plan['series']}' has no settings card in this niche.")
    template = plan.get("template") or series.get("template") or "card"
    if template not in TEMPLATES:
        return [f"Template '{template}' does not exist. Use one of: {', '.join(TEMPLATES)}."], W
    F = form(template)
    screens = plan["screens"]
    images = plan.get("images") or []
    cap = plan.get("image_cap", series.get("image_cap_per_reel"))
    voiced = plan.get("voice", {}).get("on", True) if isinstance(plan.get("voice"), dict) else bool(series.get("voice"))

    def both(n, latin, tamil, what, need=True):
        """The two-subtitle rule: an English-letter line and a Tamil-script line."""
        if need and not latin:
            E.append(f"Screen {n}: the {what} has no Tanglish (English-letter) line.")
        if need and not tamil:
            E.append(f"Screen {n}: the {what} has no Tamil-script line.")
        if latin and TAMIL.search(latin):
            E.append(f"Screen {n}: the Tanglish {what} has Tamil letters in it. Write it in English letters.")
        if tamil and not TAMIL.search(tamil):
            E.append(f"Screen {n}: the Tamil {what} is not in Tamil script.")

    hooks = set(re.findall(r"^    (\w+)\(host", (ROOT / "templates" / "common" / "hooks.js").read_text(encoding="utf-8"), re.M))
    hook = plan.get("hook") or series.get("hook")
    if not hook:
        E.append("No visual hook for the first second. Give the plan a hook (rules/motion.md), or set one on the series card.")
    elif hook not in hooks:
        E.append(f"'{hook}' is not a visual hook. Use one of: {', '.join(sorted(hooks))}.")
    if "name_reveal" in (series.get("story_shape") or []) and not any((s.get("motion") or {}).get("type") == "reveal" for s in screens if isinstance(s.get("motion"), dict)):
        E.append("This story never says who it is. Add a reveal beat near the end (motion 'reveal': \"None other than …\").")

    if template == "card":
        names = set(F["motions"])
        for i, s in enumerate(screens):
            n = i + 1
            if not s.get("headline"):
                E.append(f"Screen {n}: no headline.")
            elif _words(s["headline"]) > 7:
                W.append(f"Screen {n}: the headline has {_words(s['headline'])} words (7 or fewer reads faster).")
            if s.get("headline") and not s.get("tamil"):
                E.append(f"Screen {n}: no Tamil line under the headline.")
            if s.get("tamil") and not TAMIL.search(s["tamil"]):
                E.append(f"Screen {n}: the Tamil line is not in Tamil script.")
            spoken = s.get("voice_line")
            if voiced and not spoken:
                E.append(f"Screen {n}: this series has voice, but the screen has no spoken line.")
            if spoken or s.get("caption"):
                both(n, s.get("caption"), s.get("caption_tamil") or spoken, "subtitle")
                if s.get("caption") and _words(s["caption"]) > 8:
                    W.append(f"Screen {n}: the Tanglish subtitle has {_words(s['caption'])} words (about 6 fits one row).")
            m = s.get("motion")
            ms = [m] if isinstance(m, (dict, str)) else (m or [])
            ms = [{"type": x} if isinstance(x, str) else x for x in ms]
            if not ms:
                E.append(f"Screen {n}: no motion graphic. Pick the one from rules/motion.md that shows what the line says.")
            for x in ms:
                if x.get("type") not in names:
                    E.append(f"Screen {n}: '{x.get('type')}' is not in the motion library (rules/motion.md).")
                else:
                    for need in F["motions"][x["type"]].get("needs", []):
                        if x.get(need) in (None, "", []):
                            E.append(f"Screen {n}: the '{x['type']}' graphic needs '{need}'.")
            if len(ms) > 2 or (len(ms) == 2 and "callout" not in [x.get("type") for x in ms]):
                E.append(f"Screen {n}: one motion graphic per screen (a callout may be added to one other).")
            v = s.get("visual")
            if v is None:
                E.append(f"Screen {n}: no picture. Give a clip, image or meme, or \"same\" to keep the one before.")
            elif v == "same" and i == 0:
                E.append("Screen 1: \"same\" has no picture before it.")
            elif isinstance(v, dict) and v.get("type") not in VISUALS:
                E.append(f"Screen {n}: picture type '{v.get('type')}' is not known.")
            if isinstance(v, dict) and v.get("type") == "meme" and series.get("meme_use") == "never":
                E.append(f"Screen {n}: this series does not use memes.")
            if isinstance(v, dict) and v.get("type") == "meme" and series.get("meme_use") == "ending_only" and i < len(screens) - 2:
                E.append(f"Screen {n}: memes are for the ending only in this series.")
        if not any(isinstance(s.get("motion"), dict) and s["motion"].get("type") == "cta" or s.get("cta") for s in screens[-2:]):
            W.append("The last screen has no send prompt (motion 'cta').")
        if voiced and screens and _words(screens[0].get("voice_line")) > 5:
            W.append("Screen 1: the first spoken line is long. The hook should land in about 1.5 seconds.")
        # only pictures that may be made by AI count against the cap; free-only pictures ("ai": false) do not (AGENT.md 5.11)
        n_img = sum(1 for s in screens if isinstance(s.get("visual"), dict) and s["visual"].get("type") == "image" and s["visual"].get("ai") is not False)

    elif template == "cinematic":
        names = set(F["motions"])
        for i, s in enumerate(screens):
            n = i + 1
            if "image" not in s and not s.get("visual"):
                E.append(f"Beat {n}: no picture number.")
            elif "image" in s and not (0 <= int(s["image"]) < len(images)):
                E.append(f"Beat {n}: picture {s['image']} is not in the list of images.")
            both(n, " ".join(x for x in (s.get("line"), s.get("headline")) if x), s.get("tamil"), "text")
            if s.get("headline") and _words(s["headline"]) > 5:
                W.append(f"Beat {n}: the gold headline has {_words(s['headline'])} words (5 or fewer hits harder).")
            m = s.get("motion") or "slam"
            m = {"type": m} if isinstance(m, str) else m
            if m.get("type") not in names:
                E.append(f"Beat {n}: '{m.get('type')}' is not a cinematic motion (rules/motion.md).")
            elif m["type"] == "count" and "{n}" not in str(s.get("headline")):
                E.append(f"Beat {n}: a counting number needs {{n}} in the headline where the number goes.")
            elif m["type"] == "stamp" and not (m.get("stamp") or m.get("text")):
                E.append(f"Beat {n}: the stamp needs its word.")
        per = {}
        for s in screens:
            per[s.get("image")] = per.get(s.get("image"), 0) + 1
        if any(v > 3 for v in per.values()):
            W.append("One picture carries more than 3 text beats. 2 is the house rule.")
        n_img = len(images)

    else:  # diorama
        kinds = [s.get("kind") for s in screens]
        want = F["kinds_in_order"]
        if kinds != want:
            E.append(f"The screens must be, in order: {', '.join(want)}. This plan has: {', '.join(str(k) for k in kinds)}.")
        for i, s in enumerate(screens):
            n = i + 1
            if "image" in s and not (0 <= int(s["image"]) < len(images)):
                E.append(f"Screen {n}: picture {s['image']} is not in the list of images.")
            both(n, s.get("caption"), s.get("caption_tamil"), "caption")
            if s.get("kind") == "clue":
                both(n, s.get("headline"), s.get("tamil"), "clue")
            if s.get("kind") == "reveal" and not (s.get("title") and s.get("year")):
                E.append(f"Screen {n}: the reveal needs the film title and the year.")
            if s.get("kind") == "countdown" and float(s.get("dur", 0)) < 3.5:
                E.append(f"Screen {n}: the countdown needs at least 3.5 seconds (ready, 3, 2, 1).")
        n_img = len(images)

    lo_hi = series.get("length_s") or []
    if len(lo_hi) == 2 and screens:
        rate = float((series.get("length_estimate") or {}).get("sec_per_letter") or 0)
        letters = sum(len(str(s.get("voice") or s.get("voice_line") or "").replace(" ", "")) for s in screens)
        if voiced and rate and letters:          # measured on posted reels (series file `length_estimate`, AGENT.md 5.9)
            est = round(letters * rate)
        elif template == "card" and voiced:      # measured on the runner: about 2.5 s per spoken screen, about 11.5 Tamil letters a second
            chars = sum(len(str(s.get("voice_line") or "").replace(" ", "")) for s in screens)
            est = round(0.5 * chars / 11.5 + 0.5 * 2.5 * len(screens))
        else:
            est = round(sum(float(s.get("dur") or 0) for s in screens))
        lo, hi = float(lo_hi[0]), float(lo_hi[1])
        strict = series.get("strict_length")
        rid = str(plan.get("id") or plan.get("reel_id") or "")
        if isinstance(strict, dict):             # strict from a day on (older plans and the golden set stay as they were)
            strict = rid[:10] >= str(strict.get("since", ""))
        L = E if strict else W
        if strict and rate and est and est < lo:     # Harish, 25 Nov: breakdowns never shorter than the series' minimum
            need = round((lo - est) / rate) + 20
            L.append(f"The reel will run about {est} s (its voice has {letters} letters); this series runs {lo:g}-{hi:g} s and never shorter. "
                     f"Add about {need} more letters of voice: one more real detail, the why or the payoff (a new screen or fuller lines), never padding.")
        elif est and est < lo * 0.9:
            L.append(f"The reel will run about {est} s; this series runs {lo:g}-{hi:g} s. Add about {max(1, round((lo - est) / 2.5))} "
                     "more spoken screens (each is about 2.5 s), or say more in each line.")
        elif est > hi * 1.15:
            L.append(f"The reel will run about {est} s; this series runs {lo:g}-{hi:g} s. Cut a screen or two.")
    if series.get("min_screens") and len(screens) < int(series["min_screens"]):
        E.append(f"This series needs at least {series['min_screens']} screens (the Kaithi model has 18); this plan has {len(screens)}.")
    if series.get("visuals") in ("clips", "official") and template == "card":
        official = series.get("visuals") == "official"       # updates: the film's clips, or its official stills
        def kinds(v):
            if not isinstance(v, dict):
                return []
            if v.get("type") in ("stack", "split"):
                return kinds(v.get("top") or v.get("left")) + kinds(v.get("bottom") or v.get("right"))
            return ["still" if v.get("type") == "image" and v.get("still") and v.get("ai") is False else v.get("type")]
        ok = ("clip", "meme", "still") if official else ("clip", "meme")
        bad = [i + 1 for i, s in enumerate(screens) if any(k not in ok for k in kinds(s.get("visual")))]
        if bad:
            E.append(f"Screens {', '.join(map(str, bad))}: this series uses only the film's " + ("trailer clips or official stills" if official else "trailer clips")
                     + " (AGENT.md 5.11), no other photos or AI pictures" + ("; a still is {type: image, still: {film, n}, ai: false}." if official else "."))
        moments = {(str(v.get("film", "")).lower(), v.get("start")) for s in screens for v in [s.get("visual")] if isinstance(v, dict) and v.get("type") == "clip"}
        moments |= {(str(v["still"].get("film", "")).lower(), f"still {v['still'].get('n')}") for s in screens for v in [s.get("visual")]
                    if isinstance(v, dict) and v.get("type") == "image" and isinstance(v.get("still"), dict)}
        if len(moments) < 3:
            E.append(f"Only {len(moments)} different " + ("film pictures" if official else "trailer moments")
                     + "; show at least 3" + ("." if official else ", one for each point (AGENT.md 5.10)."))
    if cap is not None and n_img > int(cap):
        E.append(f"The plan asks for {n_img} AI images; this series allows {cap} per reel.")
    for im in images:
        if not (im.get("prompt") or im.get("subject")):
            E.append("An image has no description.")
    cap_ = plan.get("caption") or {}
    tags = cap_.get("hashtags") or []
    if cap_ and not (3 <= len(tags) <= 5):
        W.append(f"The post caption has {len(tags)} hashtags (3 to 5 is the rule).")
    return E, W


def selftest():
    """The library named in three places must agree: the template code, the plan form, the rulebook."""
    js = (ROOT / "templates" / "card" / "motion.js").read_text(encoding="utf-8")
    in_code = set(re.findall(r"^    (\w+): \{", js, re.M))
    in_form = set(form("card")["motions"])
    rules = (ROOT / "rules" / "motion.md").read_text(encoding="utf-8")
    in_rules = set(re.findall(r"^\| `(\w+)`", rules, re.M))
    out = []
    st = (ROOT / "templates" / "stage" / "template.js").read_text(encoding="utf-8")
    i = st.find("const ICONS = {")
    drawn = set(re.findall(r"^      (\w+): g =>", st[i:st.find("const painter", i)], re.M)) if i >= 0 else set()
    if drawn != SCENE_ICONS:
        out.append(f"Scene icons differ between the Stage template and the plan check: {sorted(drawn ^ SCENE_ICONS)}")
    if in_code != in_form:
        out.append(f"Card motions differ between the template and the plan form: {sorted(in_code ^ in_form)}")
    if not in_form <= in_rules:
        out.append(f"Card motions missing from rules/motion.md: {sorted(in_form - in_rules)}")
    return out


def main():
    paths = [a for a in sys.argv[1:] if not a.startswith("--")]
    bad = 0
    if "--selftest" in sys.argv:
        problems = selftest()
        print("library check:", "OK" if not problems else "; ".join(problems))
        bad += len(problems)
    for p in paths:
        with open(p, encoding="utf-8") as f:
            plan = json.load(f)
        E, W = check(plan)
        print(f"{p}: {'OK' if not E else 'NOT OK'}" + (f" ({len(W)} note{'s' if len(W) != 1 else ''})" if W else ""))
        for e in E:
            print("  fix:", e)
        for w in W:
            print("  note:", w)
        bad += len(E)
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
