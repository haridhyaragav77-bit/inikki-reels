"""Relay (AGENT.md 12.5): how the Control Room hands its wishes to the Engine without either side reading much.

The Control Room (the page's buttons, or the chat) only ever CREATES one small file per action in Drive control/inbox/.
Every Engine job starts here: each waiting action is checked, folded into the files the Engine already reads
(control/switch.json, overrides.yaml, commands.jsonl, feedback.jsonl), written to control/log.jsonl in plain words, and its
file goes to Drive's bin. An action is applied once. A bad action is refused and logged; it never stops a job.

One action is one JSON object:
    {"do": "switch", "mode": "run" | "hold_posts" | "sleep"}
    {"do": "set", "settings": {any key of config/agent.yaml}}
    {"do": "series", "id": "<series>", "set": {"paused": true}}
    {"do": "note", "series": "<series>" | "all", "text": "a standing rule in one sentence"}
    {"do": "hold" | "unhold" | "skip" | "post_now" | "retry", "reel_id": "..."}
    {"do": "edit", "reel_id": "...", "hook": "LINE ONE / LINE TWO", "caption": "...", "set": {"screens.0.what": "..."}}
    {"do": "remake", "reel_id": "...", "hook": "..."}        a posted reel made again as a new one; it waits for "post_now"
    {"do": "feedback", "reel_id": "...", "rating": 1-5, "reasons": ["Hook slow"], "text": "..."}
    {"do": "idea", "text": "cover this: ..."}
    {"do": "ack", "alert": "<alert id>" | "all"}
    {"do": "undo", "id": "<id of an earlier action>"}        switch, set, series and note can be undone
"""
import copy
import hashlib
import json

import yaml

from .settings import AGENT, niche_dir
from . import status

INBOX = "control/inbox"
GOOGLE_DOC = "application/vnd.google-apps.document"
MODES = ("run", "hold_posts", "sleep")
REEL_CMDS = ("hold", "unhold", "skip", "post_now", "retry", "edit", "remake")
SERIES_KEYS = ("paused", "slots", "length_s", "voice")          # what Harish may change on a series from the Control Room
CHOICES = {"phase": ("rehearsal", "live"), "approval": ("autopilot", "check_in", "hands_on"), "switch": MODES}
ABSENT = "__absent__"
LOG_KEEP = 200


def _read(drive, f):
    """The text of one inbox file. The Drive connector may have turned it into a Google Doc: export that as plain text."""
    if f.get("mimeType") == GOOGLE_DOC:
        data = drive.svc.files().export(fileId=f["id"], mimeType="text/plain").execute(num_retries=3)
        return (data.decode("utf-8") if isinstance(data, bytes) else str(data)).lstrip("﻿")
    return drive.read_bytes(f["id"]).decode("utf-8").lstrip("﻿")


def parse(text):
    """One action, a list of actions, or one action per line. JSON first; YAML forgives small slips."""
    text = (text or "").strip()
    if not text:
        return []
    for load in (json.loads, yaml.safe_load):
        try:
            v = load(text)
        except Exception:
            continue
        if isinstance(v, dict):
            return [v]
        if isinstance(v, list) and all(isinstance(x, dict) for x in v):
            return v
    out = []
    for line in text.splitlines():
        try:
            v = json.loads(line)
            if isinstance(v, dict):
                out.append(v)
        except ValueError:
            pass
    return out


def _lines(text):
    out = []
    for line in (text or "").splitlines():
        try:
            out.append(json.loads(line))
        except ValueError:
            pass
    return out


def _get(d, path):
    for k in path:
        if not isinstance(d, dict) or k not in d:
            return ABSENT
        d = d[k]
    return copy.deepcopy(d)


def _put(d, path, value):
    for k in path[:-1]:
        d = d.setdefault(k, {})
    if value == ABSENT:
        d.pop(path[-1], None)
    else:
        d[path[-1]] = value


def _leaves(patch, base=()):
    for k, v in patch.items():
        if isinstance(v, dict) and v:
            yield from _leaves(v, base + (k,))
        else:
            yield base + (k,), v


def _same_kind(a, b):
    num = (int, float)
    if isinstance(a, bool) or isinstance(b, bool):
        return isinstance(a, bool) and isinstance(b, bool)
    return (isinstance(a, num) and isinstance(b, num)) or type(a) is type(b)


class State:
    """The control files as they stand, changed in memory, saved once at the end."""
    def __init__(self, drive):
        self.drive = drive
        self.switch = self._json("switch.json") or {"mode": AGENT.get("switch", "run")}
        try:
            self.overrides = yaml.safe_load(drive.read_text("control", "overrides.yaml") or "") or {}
        except Exception:
            self.overrides = {}
        self.commands = drive.read_text("control", "commands.jsonl") or ""
        self.feedback = drive.read_text("control", "feedback.jsonl") or ""
        self.log = _lines(drive.read_text("control", "log.jsonl") or "")
        self.dirty = set()
        self.alerts_closed = []

    def _json(self, name):
        try:
            return self.drive.read_json("control", name)
        except Exception:
            return None

    def save(self):
        d = self.drive
        if "switch" in self.dirty:
            d.write_json("control", "switch.json", self.switch)
        if "overrides" in self.dirty:
            d.write_text("control", "overrides.yaml", yaml.safe_dump(self.overrides, allow_unicode=True, sort_keys=False), "text/plain")
        if "commands" in self.dirty:
            d.write_text("control", "commands.jsonl", self.commands, "text/plain")
        if "feedback" in self.dirty:
            d.write_text("control", "feedback.jsonl", self.feedback, "text/plain")
        d.write_text("control", "log.jsonl", "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in self.log[-LOG_KEEP:]), "text/plain")
        if self.alerts_closed:
            try:
                cur = d.read_json("status", "alerts.json") or {"alerts": []}
                for a in cur.get("alerts", []):
                    if "all" in self.alerts_closed or a.get("id") in self.alerts_closed:
                        a["open"] = False
                status.write(d, "alerts.json", cur)
            except Exception:
                pass


def _patch(st, root, patch):
    """Set the leaves of `patch` under overrides[root...]; returns what was there before, for Undo."""
    before = {}
    for path, value in _leaves(patch):
        full = tuple(root) + path
        before[".".join(full)] = _get(st.overrides, full)
        _put(st.overrides, full, value)
    st.dirty.add("overrides")
    return before


def apply_one(st, a, aid, at):
    """Returns (summary in plain words, undo data or None). Raises ValueError with the reason when refused."""
    do = str(a.get("do") or a.get("cmd") or "").strip().lower()
    if do == "switch":
        mode = str(a.get("mode", "")).lower()
        if mode not in MODES:
            raise ValueError(f"the switch can be run, hold_posts or sleep, not '{mode}'")
        before = st.switch.get("mode")
        st.switch = {"mode": mode, "set_by": a.get("by", "harish"), "at": at}
        st.dirty.add("switch")
        return f"Master switch: {before} → {mode}", {"switch": before}
    if do == "set":
        s = a.get("settings")
        if not isinstance(s, dict) or not s:
            raise ValueError("no settings given")
        for k, v in s.items():
            if k not in AGENT:
                raise ValueError(f"'{k}' is not a setting (config/agent.yaml)")
            if k in CHOICES and v not in CHOICES[k]:
                raise ValueError(f"'{k}' can be: {', '.join(CHOICES[k])}")
            if not _same_kind(v, AGENT[k]):
                raise ValueError(f"'{k}' must look like its default ({json.dumps(AGENT[k], ensure_ascii=False)[:60]})")
        before = _patch(st, ("settings",), s)
        return ("Settings: " + ", ".join(f"{'.'.join(k)} = {json.dumps(v, ensure_ascii=False)}" for k, v in _leaves(s)))[:220], {"overrides": before}
    if do == "series":
        sid, s = str(a.get("id") or a.get("series") or ""), a.get("set")
        if not (niche_dir() / "series" / sid / "series.yaml").exists():
            raise ValueError(f"there is no series '{sid}'")
        if not isinstance(s, dict) or not s or any(k not in SERIES_KEYS for k in s):
            raise ValueError("a series change can set: " + ", ".join(SERIES_KEYS))
        before = _patch(st, ("series", sid), s)
        return f"Series {sid}: " + ", ".join(f"{k} = {json.dumps(v)}" for k, v in s.items()), {"overrides": before}
    if do == "note":
        text, sid = str(a.get("text") or "").strip(), str(a.get("series") or "all")
        if not text:
            raise ValueError("the note is empty")
        if sid != "all" and not (niche_dir() / "series" / sid / "series.yaml").exists():
            raise ValueError(f"there is no series '{sid}'")
        home = st.overrides.setdefault("series", {}).setdefault(sid, {}) if sid != "all" else st.overrides
        home.setdefault("notes", []).append({"id": aid, "at": at[:10], "text": text[:300]})
        st.dirty.add("overrides")
        return f"Standing rule for {'every series' if sid == 'all' else sid}: {text[:120]}", {"note": aid}
    if do in REEL_CMDS:
        rid = str(a.get("reel_id") or "").strip()
        if not rid:
            raise ValueError("no reel named")
        c = {"cmd": do, "reel_id": rid, "at": at, "id": aid}
        for k in ("hook", "caption", "set", "first_comment", "hashtags"):
            if a.get(k) not in (None, "", [], {}):
                c[k] = a[k]
        if do in ("edit", "remake") and len(c) == 4 and do == "edit":
            raise ValueError("an edit needs a new hook, caption or 'set'")
        st.commands += json.dumps(c, ensure_ascii=False) + "\n"
        st.dirty.add("commands")
        words = {"hold": "Hold", "unhold": "Release", "skip": "Skip", "post_now": "Post now", "retry": "Make again",
                 "edit": "Change before posting", "remake": "Make a new version of"}[do]
        return f"{words}: {rid}" + (f" · new hook: {c['hook']}" if c.get("hook") else ""), None
    if do == "feedback":
        f = {k: a[k] for k in ("reel_id", "series", "rating", "reasons", "text") if a.get(k) not in (None, "", [])}
        if not f:
            raise ValueError("the feedback is empty")
        f.update(at=at, id=aid)
        st.feedback += json.dumps(f, ensure_ascii=False) + "\n"
        st.dirty.add("feedback")
        return f"Feedback on {f.get('reel_id') or f.get('series') or 'the page'}: " + (", ".join(f.get("reasons") or []) or str(f.get("text", ""))[:80] or f"rated {f.get('rating')}"), None
    if do == "idea":
        text = str(a.get("text") or "").strip()
        if not text:
            raise ValueError("the idea is empty")
        st.commands += json.dumps({"cmd": "idea", "text": text[:400], "at": at, "id": aid}, ensure_ascii=False) + "\n"
        st.dirty.add("commands")
        return f"Idea for the next plan: {text[:120]}", None
    if do == "ack":
        st.alerts_closed.append(str(a.get("alert") or "all"))
        return "Alert(s) marked as read", None
    if do == "undo":
        target = next((x for x in reversed(st.log) if x.get("id") == str(a.get("id")) and x.get("result") == "applied"), None)
        u = (target or {}).get("undo")
        if not u:
            raise ValueError("that action cannot be undone (only the switch, settings, series changes and rules can)")
        if "switch" in u:
            st.switch = {"mode": u["switch"] or "run", "set_by": "harish (undo)", "at": at}
            st.dirty.add("switch")
        for dotted, value in (u.get("overrides") or {}).items():
            _put(st.overrides, tuple(dotted.split(".")), value)
            st.dirty.add("overrides")
        if u.get("note"):
            for home in [st.overrides] + list((st.overrides.get("series") or {}).values()):
                if isinstance(home, dict) and home.get("notes"):
                    home["notes"] = [n for n in home["notes"] if n.get("id") != u["note"]]
            st.dirty.add("overrides")
        target["undone"] = at
        return f"Undone: {target.get('summary', '')[:140]}", None
    raise ValueError(f"'{do}' is not an action the Engine knows")


def run(drive):
    """Apply everything waiting in control/inbox. Returns the number applied. Never raises."""
    try:
        fid = drive.folder(INBOX)
        files = [f for f in drive.children(fid, resolve_shortcuts=False) if f.get("mimeType") != "application/vnd.google-apps.folder"]
    except Exception as e:
        print("relay: inbox not readable:", str(e)[:160])
        return 0
    if not files:
        return 0
    files.sort(key=lambda f: (f.get("createdTime") or f.get("modifiedTime") or "", f.get("name", "")))
    try:
        st = State(drive)
    except Exception as e:
        print("relay: control files not readable:", str(e)[:160])
        return 0
    seen = {x.get("file") for x in st.log}
    done = 0
    for f in files:
        if f["id"] in seen:                                    # applied earlier, its file just could not be binned
            _bin(drive, f)
            continue
        try:
            actions = parse(_read(drive, f))
        except Exception as e:
            actions, err = [], str(e)[:120]
        else:
            err = None if actions else "not a readable action"
        if err:
            st.log.append({"id": hashlib.md5(f["id"].encode()).hexdigest()[:6], "file": f["id"], "at": status.stamp(), "do": "?",
                           "summary": f"{f.get('name', '')}: {err}", "result": "refused", "why": err})
        for n, a in enumerate(actions):
            aid = hashlib.md5(f"{f['id']}:{n}".encode()).hexdigest()[:6]
            at = status.stamp()
            entry = {"id": aid, "file": f["id"], "at": at, "do": str(a.get("do") or a.get("cmd") or "?")}
            try:
                entry["summary"], undo = apply_one(st, a, aid, at)
                entry["result"] = "applied"
                if undo:
                    entry["undo"] = undo
                done += 1
            except ValueError as e:
                entry.update(summary=json.dumps(a, ensure_ascii=False)[:140], result="refused", why=str(e)[:200])
            except Exception as e:                             # fail soft: one bad action, never the job
                entry.update(summary=json.dumps(a, ensure_ascii=False)[:140], result="refused", why=f"could not be applied ({str(e)[:120]})")
            st.log.append(entry)
            print(f"relay: {entry['result']}: {entry.get('summary', '')}" + (f" ({entry['why']})" if entry.get("why") else ""))
    try:
        st.save()
    except Exception as e:
        print("relay: could not save the control files; the actions stay in the inbox:", str(e)[:160])
        return 0
    for f in files:
        _bin(drive, f)
    return done


def _bin(drive, f):
    try:
        drive.trash(f["id"])
    except Exception as e:
        print("relay: could not bin", f.get("name"), str(e)[:100])
