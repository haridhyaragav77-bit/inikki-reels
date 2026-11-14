"""The Control Room path with a pretend Drive: inbox → relay → control files → panel, and word changes on a plan.
Run: python -m tests.test_control_room   (no keys, nothing posted)"""
import base64
import copy
import json
import shutil
import sys

from engine import edits, panel, relay, status
from engine.control import Control
from engine.day import Day, today
from engine.settings import ROOT


class FakeDrive:
    """Just enough of engine/drive.py: folders are path strings, files live in a dict."""
    def __init__(self):
        self.files, self.n, self.binned = {}, 0, []
        self.svc = None

    def folder(self, path, create=True):
        return path.strip("/")

    def children(self, fid, resolve_shortcuts=True):
        return [dict(f) for f in self.files.values() if f["folder"] == fid]

    def find(self, folder, name):
        return next((f for f in self.files.values() if f["folder"] == folder and f["name"] == name), None)

    def read_bytes(self, file_id):
        return self.files[file_id]["text"].encode("utf-8")

    def read_text(self, folder, name, default=None):
        f = self.find(folder, name)
        return f["text"] if f else default

    def read_json(self, folder, name, default=None):
        t = self.read_text(folder, name)
        return json.loads(t) if t else default

    def write_text(self, folder, name, text, mime="text/plain"):
        f = self.find(folder, name)
        if f:
            f["text"] = text
            return f
        self.n += 1
        f = {"id": f"f{self.n}", "folder": folder, "name": name, "text": text, "mimeType": mime, "createdTime": f"2026-01-01T00:00:{self.n:02d}Z"}
        self.files[f["id"]] = f
        return f

    def write_json(self, folder, name, obj):
        return self.write_text(folder, name, json.dumps(obj, ensure_ascii=False), "application/json")

    def trash(self, file_id):
        self.binned.append(self.files.pop(file_id)["name"])

    def drop(self, name, action):
        """What the Control Room does: create one small file in the inbox."""
        return self.write_text(relay.INBOX, name, json.dumps(action, ensure_ascii=False))


def check(cond, what):
    print(("ok   " if cond else "FAIL ") + what)
    if not cond:
        check.failed += 1
check.failed = 0


def main():
    d = FakeDrive()
    d.write_json("control", "switch.json", {"mode": "run"})

    # 1. the switch, a setting, a series pause, a standing rule, feedback, an idea, a bad action
    d.drop("1-switch.json", {"do": "switch", "mode": "hold_posts"})
    d.drop("2-set.json", {"do": "set", "settings": {"volume": {"base": 4}}})
    d.drop("3-series.json", {"do": "series", "id": "movie-updates", "set": {"paused": True}})
    d.drop("4-note.json", {"do": "note", "series": "movie-recommendations", "text": "Open with a promise and a number, e.g. 4 FILMS TO WATCH TONIGHT."})
    d.drop("5-feedback.json", {"do": "feedback", "reel_id": "2026-11-13-watch-loved-jailer-2", "rating": 3, "reasons": ["Hook slow"]})
    d.drop("6-idea.json", {"do": "idea", "text": "cover this: 5 one-night thrillers"})
    d.drop("7-bad.json", {"do": "set", "settings": {"volume": "lots"}})
    d.drop("8-bad.json", {"do": "launch_rocket"})
    ctl = Control(d)
    check(ctl.mode == "hold_posts", "switch set to hold_posts")
    check(ctl.settings["volume"] == {"base": 4, "max": 8}, "one setting changed, the rest kept")
    check(ctl.series_paused("movie-updates"), "series paused")
    check(len(ctl.notes("movie-recommendations")) == 1, "standing rule stored for the series")
    check("paused" not in json.dumps(ctl.series("movie-recommendations", ROOT / "niches" / "tamil-cinema")), "rules do not leak into the series card")
    check('"Hook slow"' in d.read_text("control", "feedback.jsonl"), "feedback recorded")
    check('"idea"' in d.read_text("control", "commands.jsonl"), "idea recorded")
    log = [json.loads(l) for l in d.read_text("control", "log.jsonl").splitlines()]
    check([x["result"] for x in log] == ["applied"] * 6 + ["refused"] * 2, "6 applied, 2 refused, all logged")
    check(not d.children(relay.INBOX) and len(d.binned) == 8, "inbox emptied into the bin")
    check(relay.run(d) == 0, "nothing is applied twice")

    # 2. undo
    for name, what in (("9-undo.json", "switch"), ("10-undo.json", "series"), ("11-undo.json", "note"), ("12-undo.json", "set")):
        d.drop(name, {"do": "undo", "id": next(x["id"] for x in log if x["do"] == what)})
    ctl = Control(d)
    check(ctl.mode == "run" and not ctl.series_paused("movie-updates") and not ctl.notes("movie-recommendations")
          and ctl.settings["volume"]["base"] == 6, "undo restores the switch, the series, the rule and the setting")

    # 2b. the series framework: edit any block, add a series, test, sample, retire, global switches (AGENT.md 6.1, 12.3)
    nd = ROOT / "niches" / "tamil-cinema"
    d.drop("20-shape.json", {"do": "series", "id": "movie-recommendations", "set": {"story_shape": ["title_screen", "plot beat", "recap_grid"], "voice_cfg.provider": "microsoft", "length_s": "20, 40"}})
    d.drop("21-add.json", {"do": "series_add", "card": {"name": "Song Stories", "promise": "The story behind one famous song.", "slots": "17:00\n21:00", "length_s": "15, 30",
                                                         "title_screen": "{SONG} · THE STORY", "story_shape": "title\nthe story\nquestion", "template": "bulletin", "music": '{"default":"soft_warm"}', "voice": "false"}})
    d.drop("22-sw.json", {"do": "set", "settings": {"voice.provider": "microsoft"}})
    d.drop("23-sw.json", {"do": "set", "settings": {"saver.enabled": True}})
    d.drop("24-test.json", {"do": "test", "series": "movie-recommendations"})
    d.drop("25-sample.json", {"do": "sample", "series": "film-breakdown", "url": "https://www.instagram.com/reel/x/", "note": "the first frame"})
    d.drop("26-bad.json", {"do": "series", "id": "movie-updates", "set": {"template": "no-such-look"}})
    d.drop("27-bad.json", {"do": "set", "settings": {"voice.provider": "robot"}})
    d.drop("28-bad.json", {"do": "series_add", "card": {"name": "Movie Updates"}})
    ctl = Control(d)
    card = ctl.series("movie-recommendations", nd)
    check(card["story_shape"] == ["title_screen", "plot beat", "recap_grid"] and card["voice_cfg"]["provider"] == "microsoft" and card["length_s"] == [20, 40],
          "a series' structure, voice and length are changed from the Control Room")
    check(ctl.series_changes("movie-recommendations").keys() == {"story_shape", "voice_cfg", "length_s"}, "the brief is told exactly what changed")
    new = ctl.series("song-stories", nd)
    check(new.get("status") == "draft" and new["slots"] == ["17:00", "21:00"] and new["voice"] is False and new["music"] == {"default": "soft_warm"} and "song-stories" in ctl.series_ids(nd),
          "a new series is added as a draft, in the framework's shape")
    check(ctl.settings["voice"]["provider"] == "microsoft" and ctl.settings["voice"]["backup"] == "microsoft" and ctl.on("saver", False), "global switches are set")
    import datetime as _dt
    from engine.brief import draft_day, lineup_today
    dd = next(x for x in (_dt.date.today() + _dt.timedelta(days=k) for k in range(2)) if draft_day(x.isoformat())).isoformat()
    off = (_dt.date.fromisoformat(dd) + _dt.timedelta(days=1)).isoformat()
    rows = [r for r in lineup_today(ctl, dd)[0] if r[1] == "song-stories"]
    check(len(rows) == 1 and rows[0][3].startswith("DRAFT") and not [r for r in lineup_today(ctl, off)[0] if r[1] == "song-stories"],
          "a draft series gets one reel every other day, marked as never posted")
    from engine import voice as V
    check(V.order(None, d)[0] == "microsoft", "the voice follows the switch")
    cmds = d.read_text("control", "commands.jsonl")
    check('"cmd": "test"' in cmds and '"cmd": "sample"' in cmds, "a test reel and a sample reel are queued")
    log = [json.loads(l) for l in d.read_text("control", "log.jsonl").splitlines()]
    check([x["result"] for x in log[-9:]] == ["applied"] * 6 + ["refused"] * 3, "a look that does not exist, a wrong choice and a duplicate series are refused")
    d.drop("29-retire.json", {"do": "series_remove", "id": "song-stories"})
    ctl = Control(d)
    check(ctl.series_paused("song-stories") and ctl.series("song-stories", nd)["status"] == "retired", "a series is retired")
    log = [json.loads(l) for l in d.read_text("control", "log.jsonl").splitlines()]
    for n, what in enumerate(("series_remove", "series_add", "series"), 30):
        d.drop(f"{n}-undo.json", {"do": "undo", "id": next(x["id"] for x in reversed(log) if x["do"] == what and x["result"] == "applied")})
    for n, x in enumerate([x for x in log if x["do"] == "set" and x["result"] == "applied"][-2:], 40):
        d.drop(f"{n}-undo.json", {"do": "undo", "id": x["id"]})
    ctl = Control(d)
    check("song-stories" not in ctl.series_ids(nd) and not ctl.series_changes("movie-recommendations") and ctl.settings["voice"]["provider"] == "elevenlabs" and not ctl.on("saver", False),
          "undo takes back the new series, the series changes and the switches")

    # 3. a Google-Doc style or sloppy file still parses; several actions in one file
    check(len(relay.parse('{do: hold, reel_id: x}')) == 1 and len(relay.parse('{"do":"hold","reel_id":"a"}\n{"do":"skip","reel_id":"b"}')) == 2, "forgiving reader")

    # 4. word changes on a real plan (a copy of the reference plan, in today's folder)
    date = today()
    folder = ROOT / "plans" / date
    made_folder = not folder.exists()
    src = json.loads((ROOT / "plans" / "reference" / "watch-loved-vikram-vedha.json").read_text(encoding="utf-8"))
    rid = f"{date}-zz-test-watch"
    src["id"] = rid
    src["remake_of"] = "2026-11-13-watch-loved-vikram-vedha"      # so the never-twice rule lets the test plan through
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{rid}.json").write_text(json.dumps(src, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        w = edits.words(src)
        check(w.get("screens.0.lines") == "LOVED VIKRAM VEDHA? / WATCH THESE 4", "the panel can show a reel's editable words")
        new = edits.change(src, {"hook": "4 FILMS TO WATCH TONIGHT / IF YOU LOVED VIKRAM VEDHA"})
        check(new["screens"][0]["lines"] == ["4 FILMS TO WATCH TONIGHT", "IF YOU LOVED VIKRAM VEDHA"], "hook changed, as two lines")
        check(src["screens"][0]["lines"][0] == "LOVED VIKRAM VEDHA?", "the original plan is untouched until saved")
        try:
            edits.set_path(copy.deepcopy(src), "screens.0.fx", "9")
            check(False, "structure cannot be changed")
        except ValueError:
            check(True, "structure cannot be changed")
        bul = json.loads((ROOT / "plans" / "reference" / "update-scene-week1.json").read_text(encoding="utf-8"))
        try:
            edits.change(bul, {"hook": "ONE LINE ONLY"})
            check(False, "a title with fixed places keeps its number of lines")
        except ValueError:
            check(True, "a title with fixed places keeps its number of lines")
        check(edits.change(bul, {"hook": "WEEK 2 / BOX OFFICE"})["screens"][0]["lines"][0]["text"] == "WEEK 2", "fixed-place title: words swapped in place")

        day = Day(d)
        day.upsert(rid, series="movie-recommendations", state="ready", hash="old", slot="15:30")
        day.save()
        d.drop("20-edit.json", {"do": "edit", "reel_id": rid, "hook": "4 FILMS TO WATCH TONIGHT / IF YOU LOVED VIKRAM VEDHA"})
        d.drop("21-remake.json", {"do": "remake", "reel_id": rid, "hook": "TONIGHT'S 4 FILMS / FOR VEDHA FANS"})
        edits.main(d)
        saved = json.loads((folder / f"{rid}.json").read_text(encoding="utf-8"))
        check(saved["screens"][0]["lines"][0] == "4 FILMS TO WATCH TONIGHT", "edit saved to the plan")
        check(Day(d).get(rid)["state"] == "planned", "the edited reel waits to be made again (it cannot post half-changed)")
        v2 = folder / f"{rid}-v2.json"
        check(v2.exists() and json.loads(v2.read_text(encoding="utf-8")).get("manual") is True, "remake made a new plan that waits for 'post now'")
        book = d.read_json("status", "edits.json")["done"]
        check(len(book) == 2 and all(x["ok"] for x in book.values()), "both word changes recorded as done")
        edits.main(d)
        check(len(d.read_json("status", "edits.json")["done"]) == 2, "word changes are applied once")

        # 5. the panel
        P = panel.save(d)
        check(P["switch"] == "run" and P["today"]["reels"] and P["today"]["reels"][0].get("words"), "panel has the switch and today's reels with their words")
        check(len(P["schedule"]) >= 8 and any(s["kind"] == "think" for s in P["schedule"]) and any("slot" in s["what"] for s in P["schedule"]),
              "panel lists the next Engine jobs and thinking runs")
        check(len(P["tomorrow"]["slots"]) >= 4, "panel shows tomorrow's slots")
        check(len(P["series"]) >= 8, "panel lists every series")
        fw = P["framework"]
        check(len(fw["blocks"]) == 7 and any(x["key"] == "voice.provider" for x in fw["switches"]) and "stage" in next(f for b in fw["blocks"] for f in b["fields"] if f["key"] == "template")["options"],
              "panel carries the series framework: 7 blocks, the switches, the looks that exist")
        rec = next(x for x in P["series"] if x["id"] == "movie-recommendations")
        check(rec["values"]["story_shape"] and rec["values"]["template"] == "poster-wall" and rec.get("has_reference"), "each series comes with its values, block by block")
        check({"runner", "voice", "claude"} <= set(P["usage"]) and P["insights"].get("headline") and P["calendar"].get("day"), "panel carries usage, insights and today's calendar")
        txt = d.read_text("status", "panel.txt")
        back = json.loads(base64.b64decode("".join(c for c in txt.split("\n", 1)[1] if c.isalnum() or c in "+/=")))
        check(txt.startswith(panel.MARK) and back["updated"] == P["updated"], "page data unpacks to the same panel")
        md = d.read_text("status", "panel.md")
        check("## TODAY" in md and "## NEXT RUNS" in md and len(md) < 6000, f"chat text is one small page ({len(md)} characters)")
    finally:
        for p in folder.glob(f"{rid}*.json"):
            p.unlink()
        if made_folder:
            shutil.rmtree(folder, ignore_errors=True)
        shutil.rmtree(ROOT / "out" / "status", ignore_errors=True)
    print("\nALL PASSED" if not check.failed else f"\n{check.failed} FAILED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
