"""Breakdowns after 22 Nov (Harish; AGENT.md 5.7, 5.8): one clear point, facts line by line, no formula phrases, a hero
visual drawn for the film (the scene builder), stock graphics that cool down, trending songs only on music-only reels.
Run: python -m tests.test_breakdown   (no keys, no Drive)"""
import copy
import json
import sys

from engine import plancheck as PC
from tests.test_control_room import check

REF = "plans/reference/breakdown-scene-viduthalai.json"


def load(p):
    return json.load(open(p, encoding="utf-8"))


def errs(plan):
    return PC.check(plan)[0]


def main():
    PC.mirror = lambda: {}                                         # no Control Room settings in a test
    for p in (REF, "plans/reference/breakdown-f1-real-racing.json"):
        e = errs(load(p))
        check(not e, f"the reference plan passes every check: {p}" + (f" ({e[:2]})" if e else ""))
    check(not PC.selftest(), "the scene icons in the template and the plan check agree")

    base = load(REF)
    base.pop("reference")
    base["id"] = "2026-11-23-breakdown-test"
    base["design"] = "royal"
    base["lead"]["inspired_by"] = "own idea (test)"
    PC.recent_plans = lambda tpl, rid, n=3: [{"id": "2026-11-22-breakdown-older", "design": "forest",
                                              "screens": [{"kind": k} for k in ("title", "meter", "standoff", "quote", "technique", "end")]}][:n]
    e = errs(base)
    check(not e, "a new plan built like the reference passes" + (f" ({e[:2]})" if e else ""))

    def variant(fn):
        p = copy.deepcopy(base)
        fn(p)
        return " | ".join(errs(p))

    check("lead.point" in variant(lambda p: p["lead"].pop("point")), "no one-sentence point: refused")
    check("25 words or fewer" in variant(lambda p: p["lead"].update(point=" ".join(["word"] * 30) + ".")), "a point over 25 words: refused")
    check("more than one sentence" in variant(lambda p: p["lead"].update(point="It is long. It has two parts.")), "two sentences: refused")
    check("'src'" in variant(lambda p: p["screens"][2].pop("src")), "a screen without a source: refused")
    check("'src'" in variant(lambda p: p["screens"][2].update(src=9)), "a source number that is not in lead.sources: refused")
    check("at least 2 sources" in variant(lambda p: p["lead"].update(sources=p["lead"]["sources"][:1]) or [s.update(src=0) for s in p["screens"] if "src" in s]),
          "only one source: refused")
    check("formula phrase" in variant(lambda p: p["screens"][1].update(heading="3 SECRETS")), "a formula phrase ('3 secrets'): refused")
    check("hero visual" in variant(lambda p: p.update(screens=[s for s in p["screens"] if s["kind"] != "scene"])), "no hero visual: refused")
    check("cooling down" in variant(lambda p: p["screens"].insert(2, {"kind": "meter", "voice": p["screens"][2]["voice"], "voice_tg": p["screens"][2]["voice_tg"],
                                                                        "heading": "X", "label": "Y", "levels": [{"label": "A", "value": 50}], "src": 0})),
          "the speedometer right after another breakdown used it: refused")
    check("not drawn yet" in variant(lambda p: p["screens"][1]["props"][0].update(icon="dragon")), "a scene icon that does not exist: refused")
    check("a link joins two props" in variant(lambda p: p["screens"][1]["links"][0].update(to="nobody")), "a scene link to a missing prop: refused")
    check("which the voice line does not say" in variant(lambda p: p["screens"][1]["props"][3].update(move_cue={"word": "இல்லாதசொல்"})),
          "a scene move waiting for a word the voice never says: refused")
    check("₹ sign" in variant(lambda p: p["screens"][1]["counter"].update(unit="₹ DAYS")), "a ₹ on a counter that is not money: refused")

    old = copy.deepcopy(base)
    old["id"] = "2026-11-22-breakdown-test"
    for s in old["screens"]:
        s.pop("src", None)
    old["lead"].pop("point")
    e = " | ".join(errs(old))
    check("lead.point" not in e and "'src'" not in e, "plans before 23 Nov are not held by the new rules")

    PC._trending_keys = lambda: {"song_test"}
    keys = PC._music_keys
    PC._music_keys = lambda: keys() | {"song_test"}
    check("music-only reels" in variant(lambda p: p["music"]["sections"][0].update(track="song_test")), "a trending song on a voiced reel: refused")
    print("\nALL PASSED" if not check.failed else f"\n{check.failed} FAILED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
