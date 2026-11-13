"""Plan check (AGENT.md 5.10 "the standard", skill plan-reel). A plan that fails is not made.

    python -m engine.plancheck plans/2026-11-12/*.json

Says in plain words what is wrong. Errors stop the reel; warnings do not."""
import json
import re
import sys

from .settings import ROOT, load_yaml, niche_dir

TAMIL = re.compile(r"[஀-௿]")
LATIN = re.compile(r"[A-Za-z]")
TEMPLATES = ("card", "cinematic", "diorama")
VISUALS = ("clip", "image", "meme", "split", "stack", "none", "mascot")


def form(template):
    with open(ROOT / "templates" / template / "plan_form.json", encoding="utf-8") as f:
        return json.load(f)


def _words(t):
    return len(re.sub(r"[*{}]", "", str(t or "")).split())


def check(plan):
    """Returns (errors, warnings) as lists of plain sentences."""
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
        if template == "card" and voiced:      # measured on the runner: about 2.5 s per spoken screen, about 11.5 Tamil letters a second
            chars = sum(len(str(s.get("voice_line") or "").replace(" ", "")) for s in screens)
            est = round(0.5 * chars / 11.5 + 0.5 * 2.5 * len(screens))
        else:
            est = round(sum(float(s.get("dur") or 0) for s in screens))
        lo, hi = float(lo_hi[0]), float(lo_hi[1])
        L = E if series.get("strict_length") else W
        if est and est < lo * 0.9:
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
