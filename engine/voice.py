"""Voice (AGENT.md 4.4). Main voice: ElevenLabs. Backup, always kept: Microsoft, through Harish's tools/voice_tool.py
(call it, never rewrite it). Which one speaks is a setting (config/agent.yaml `voice`, a series' `voice_cfg`, or a plan).

One take, never two drafts: every line is recorded once and kept by its exact words (Drive work/voice-cache), so a
retry, a word change or a re-made reel never pays for the same line again. A reel speaks with one voice from start to
end: if the main voice fails part-way, the whole reel is recorded with the backup.

Cost guards are code (CLAUDE.md rule 5): the month's ElevenLabs credits are read before each reel; below the reserve,
or without a key, the backup voice is used and the Control Room says so."""
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys

import requests

from .settings import AGENT, ENGINE, ROOT, secret
from . import status

TOOL = str(ROOT / ENGINE["voice"]["tool"])
CACHE_FOLDER = "work/voice-cache"
NO_KEY = "no ElevenLabs key on this job"        # only test runs (the automatic look check) render without the key
PROVIDERS = ("elevenlabs", "microsoft")


# ---------------------------------------------------------------- settings
def cfg():
    return ENGINE["voice"]


def eleven():
    return cfg().get("elevenlabs") or {}


def live(drive=None):
    """The voice settings as Harish last set them (Control Room), over the file defaults."""
    out = dict(AGENT.get("voice") or {})
    if drive:
        try:
            from .control import Control
            out.update(Control(drive, relay=False).settings.get("voice") or {})
        except Exception:
            pass
    return out


def series_voice(drive, sid):
    """A series' own voice choice (its Voice block: provider, ElevenLabs voice, speed), with the Control Room's changes."""
    if not sid:
        return {}
    try:
        from .control import Control
        from .settings import niche_dir
        return dict(Control(drive, relay=False).series(str(sid), niche_dir()).get("voice_cfg") or {})
    except Exception:
        return {}


def key():
    for n in eleven().get("key_names") or ["ELEVENLABS_API_KEY"]:
        if secret(n):
            return secret(n)
    return None


def voice_id(name):
    """A voice by its short name in config/engine.yaml (voice.elevenlabs.voices), or a raw ElevenLabs voice id."""
    voices = eleven().get("voices") or {}
    name = str(name or eleven().get("voice") or "")
    if name in voices:
        return voices[name]["id"]
    return name if len(name) >= 18 and " " not in name and not name.startswith("ta-") else voices[eleven().get("voice")]["id"]


def defaults():
    v = cfg()
    return {"voice": v["voice"], "rate": v["rate"], "pitch": v["pitch"]}


# ---------------------------------------------------------------- Microsoft (the backup), through the tool
def _run(args, timeout=600):
    r = subprocess.run([sys.executable, TOOL] + args, capture_output=True, text=True, timeout=timeout, cwd=str(ROOT))
    lines = [l for l in (r.stdout or "").strip().splitlines() if l.strip()]
    for line in reversed(lines):
        if line.startswith("{"):
            try:
                out = json.loads(line)
                out.setdefault("ok", r.returncode == 0)
                return out
            except ValueError:
                pass
    err = (r.stderr or r.stdout or "").strip().splitlines()
    return {"ok": False, "error": err[-1][:300] if err else f"voice tool exited {r.returncode}"}


def say(text, out_path, voice=None, rate=None, pitch=None):
    """One line with the Microsoft voice (health and smoke checks)."""
    d = defaults()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    # Values like "-2Hz" start with a dash, so they must be passed as --pitch=-2Hz
    return _run(["say", "--text", text, "--out", out_path, f"--voice={voice or d['voice']}",
                 f"--rate={rate or d['rate']}", f"--pitch={pitch or d['pitch']}"])


def microsoft_batch(plan, outdir, fresh=False):
    os.makedirs(outdir, exist_ok=True)
    for name in os.listdir(outdir):          # an empty clip left by a failed try would break the tool's length reader
        fp = os.path.join(outdir, name)
        if name.endswith(".mp3") and os.path.getsize(fp) < 1000:
            os.remove(fp)
    p = os.path.join(outdir, "plan.json")
    full = {**defaults(), **{k: v for k, v in plan.items() if k in ("rate", "pitch", "lines")}}
    if str(plan.get("voice", "")).startswith(tuple(cfg().get("microsoft_prefixes") or ["ta-", "en-"])):
        full["voice"] = plan["voice"]
    with open(p, "w", encoding="utf-8") as f:
        json.dump(full, f, ensure_ascii=False)
    r = _run(["batch", "--plan", p, "--outdir", outdir] + (["--fresh"] if fresh else []))
    r["provider"] = "microsoft"
    return r


def voices(lang="ta"):
    return _run(["voices", "--lang", lang], timeout=120)


# ---------------------------------------------------------------- ElevenLabs
def _ffmpeg():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def seconds(path):
    import re
    err = subprocess.run([_ffmpeg(), "-i", path], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups()
    return round(int(h) * 3600 + int(m) * 60 + float(s), 2)


def subscription():
    """This month's ElevenLabs credits: {used, limit, left, resets, tier}, or None when it cannot be read."""
    k = key()
    if not k:
        return None
    try:
        r = requests.get(eleven().get("base", "https://api.elevenlabs.io") + "/v1/user/subscription", headers={"xi-api-key": k}, timeout=20)
        if not r.ok:
            return None
        j = r.json()
        used, limit = int(j.get("character_count") or 0), int(j.get("character_limit") or 0)
        reset = j.get("next_character_count_reset_unix")
        return {"used": used, "limit": limit, "left": max(0, limit - used), "tier": j.get("tier"),
                "resets": dt.datetime.fromtimestamp(int(reset), status.IST).strftime("%Y-%m-%d") if reset else None}
    except Exception:
        return None


def ledger(drive):
    """Drive status/voice.json: what the voice cost this month, for the Control Room's usage card."""
    month = status.now().strftime("%Y-%m")
    led = None
    if drive:
        try:
            led = drive.read_json("status", "voice.json")
        except Exception:
            led = None
    if not led or led.get("month") != month:
        led = {"month": month, "reels": {"elevenlabs": 0, "microsoft": 0}, "credits_by_engine": 0, "lines_reused": 0, "recent": []}
    return led


def note_use(drive, provider, reel_id, credits=0, reused=0, why=None, sub=None):
    led = ledger(drive)
    led["reels"][provider] = led["reels"].get(provider, 0) + 1
    led["credits_by_engine"] = led.get("credits_by_engine", 0) + int(credits)
    led["lines_reused"] = led.get("lines_reused", 0) + int(reused)
    led["recent"] = ([{"at": status.stamp(), "reel_id": reel_id, "voice": provider, "credits": int(credits), "why": why}] + led.get("recent", []))[:300]
    sub = sub or subscription()
    if sub:
        led["subscription"] = {**sub, "read": status.stamp()}
    led["provider_now"] = provider
    led["updated"] = status.stamp()
    status.write(drive, "voice.json", led)
    return led


def _line_key(text, vid, model, vs):
    return hashlib.md5(json.dumps([text, vid, model, vs], ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def _cache_get(drive, name, path):
    """A line recorded earlier (its sound and its word timings), from Drive. True when both are back."""
    if not drive:
        return False
    try:
        folder = drive.folder(CACHE_FOLDER)
        for n, pth in ((name, path), (name + ".json", path + ".json")):
            f = drive.find_child(folder, n)
            if not f:
                return False
            drive.download(f["id"], pth)
        return os.path.getsize(path) > 1000
    except Exception:
        return False


def _cache_put(drive, name, path):
    if drive:
        try:
            drive.upload(path, CACHE_FOLDER, name)
            drive.upload(path + ".json", CACHE_FOLDER, name + ".json")
        except Exception:
            pass


def words_from(alignment):
    """ElevenLabs gives a time for every letter; subtitles and graphics want words: [{"w", "t", "d"}]."""
    chars = (alignment or {}).get("characters") or []
    t0s, t1s = (alignment or {}).get("character_start_times_seconds") or [], (alignment or {}).get("character_end_times_seconds") or []
    out, cur = [], None
    for c, a, b in zip(chars, t0s, t1s):
        if c.isspace():
            cur = None
            continue
        if cur is None:
            cur = {"w": "", "t": round(float(a), 3), "end": float(b)}
            out.append(cur)
        cur["w"] += c
        cur["end"] = float(b)
    words = []
    for w in out:
        text = w["w"].strip(".,!?;:\"'“”‘’()[]…-–—|")
        if text:
            words.append({"w": text, "t": w["t"], "d": round(max(0.05, w["end"] - w["t"]), 3)})
    return words


def _speak(text, out, vid, model, vs, seed, before=None, after=None):
    """One line, one call, with word timings. Returns the credits it cost. Raises on any refusal."""
    import base64
    e = eleven()
    body = {"text": text, "model_id": model, "voice_settings": vs, "seed": seed}
    if e.get("language_code") and model in (e.get("language_code_models") or []):
        body["language_code"] = e["language_code"]
    if model in (e.get("context_models") or []):         # the lines before and after, so the reel sounds like one read
        if before:
            body["previous_text"] = before[-300:]
        if after:
            body["next_text"] = after[:300]
    r = requests.post(f"{e.get('base', 'https://api.elevenlabs.io')}/v1/text-to-speech/{vid}/with-timestamps",
                      params={"output_format": e.get("output_format", "mp3_44100_128")},
                      headers={"xi-api-key": key(), "Content-Type": "application/json"}, json=body, timeout=120)
    if not r.ok:
        try:
            d = r.json().get("detail")
            msg = (d.get("message") or d.get("status")) if isinstance(d, dict) else str(d)
        except Exception:
            msg = r.text[:160]
        raise RuntimeError(f"ElevenLabs refused ({r.status_code}): {str(msg)[:200]}")
    j = r.json()
    audio = base64.b64decode(j.get("audio_base64") or "")
    if len(audio) < 1000:
        raise RuntimeError("ElevenLabs sent an empty clip")
    with open(out, "wb") as f:
        f.write(audio)
    with open(out + ".json", "w", encoding="utf-8") as f:
        json.dump(words_from(j.get("alignment") or j.get("normalized_alignment")), f, ensure_ascii=False)
    try:
        return int(r.headers.get("character-cost") or r.headers.get("x-character-count") or len(text))
    except ValueError:
        return len(text)


def elevenlabs_batch(plan, outdir, drive=None, reel_id=None, sub=None):
    """Every line once. Lines already recorded (this run, or kept in Drive) are reused and cost nothing."""
    e = eleven()
    if not key():
        return {"ok": False, "error": NO_KEY, "skipped": True}
    os.makedirs(outdir, exist_ok=True)
    vid = voice_id(plan.get("voice"))
    vs = {**(e.get("settings") or {}), **{k: v for k, v in (plan.get("settings") or {}).items() if k in ("stability", "similarity_boost", "style", "speed", "use_speaker_boost")}}
    if plan.get("speed"):
        vs["speed"] = min(1.2, max(0.7, float(plan["speed"])))
    texts = [str(l["text"]).strip() for l in plan["lines"]]
    seed = int(hashlib.md5(str(reel_id or "reel").encode()).hexdigest()[:7], 16)          # same plan, same reel (CLAUDE.md rule 2)
    last = None
    for model in (plan.get("models") or e.get("models") or ["eleven_multilingual_v2"]):
        clips, todo = [], []
        for i, t in enumerate(texts):
            name = f"{_line_key(t, vid, model, vs)}.mp3"
            out = os.path.join(outdir, name)
            have = os.path.exists(out) and os.path.getsize(out) > 1000 and os.path.exists(out + ".json")
            clips.append({"line": i, "file": out, "name": name})
            if not (have or _cache_get(drive, name, out)):
                todo.append(i)
        need = sum(len(texts[i]) for i in todo)
        if todo and sub is not None and sub["left"] - need < int(e.get("reserve_credits", 0)):
            return {"ok": False, "skipped": True, "error": f"ElevenLabs credits are nearly used up this month ({sub['left']} left, this reel needs about {need})"}
        spent = 0
        try:
            for i in todo:
                c = clips[i]
                spent += _speak(texts[i], c["file"], vid, model, vs, seed + i, " ".join(texts[:i]), " ".join(texts[i + 1:]))
                _cache_put(drive, c["name"], c["file"])
            out = []
            for c in clips:
                with open(c["file"] + ".json", encoding="utf-8") as f:
                    out.append({"line": c["line"], "file": os.path.abspath(c["file"]), "seconds": seconds(c["file"]), "words": json.load(f)})
            return {"ok": True, "provider": "elevenlabs", "model": model, "voice_id": vid, "credits": spent, "reused": len(texts) - len(todo), "clips": out}
        except Exception as ex:                         # try the next model once; lines already recorded stay kept
            last = str(ex)[:240]
            print("voice:", last, file=sys.stderr)
            if "401" in last or "quota" in last.lower() or "credit" in last.lower():
                break
    return {"ok": False, "error": last or "ElevenLabs gave no answer"}


# ---------------------------------------------------------------- one reel's voice
def order(want=None, drive=None):
    """Which voice first, which second. `want` is a plan's or a series' own choice; else Harish's setting; else the file."""
    lv = live(drive)
    first = str(want or lv.get("provider") or cfg().get("provider") or "elevenlabs").lower()
    first = first if first in PROVIDERS else "elevenlabs"
    backup = str(lv.get("backup") or cfg().get("backup") or "microsoft").lower()
    return [first] + ([backup] if backup in PROVIDERS and backup != first else [])


def job_drive():
    """The Drive of this job, for the sound mixer (it runs as its own program). None when there are no Drive keys."""
    if "d" not in _DRIVE:
        _DRIVE["d"] = None
        if secret("GDRIVE_ROOT_FOLDER_ID"):
            try:
                from .drive import Drive
                _DRIVE["d"] = Drive()
            except Exception:
                pass
    return _DRIVE["d"]


_DRIVE = {}


def main_voice(plan, outdir, drive=None, reel_id=None):
    """The ElevenLabs take of a reel's lines, when ElevenLabs is the voice to use and it answers.
    → (result or None, why). None means: the Microsoft voice speaks this reel; `why` says why in plain words."""
    first = order(plan.get("provider"), drive)[0]
    if first != "elevenlabs":
        return None, None
    sub, lv, p = subscription(), live(drive), dict(plan)
    if not p.get("voice") or str(p["voice"]).startswith(tuple(cfg().get("microsoft_prefixes") or ["ta-", "en-"])):
        p["voice"] = plan.get("elevenlabs_voice") or lv.get("elevenlabs_voice")     # a Microsoft name in a plan is for the backup only
    if lv.get("quality") == "economy" and eleven().get("economy_models"):
        p.setdefault("models", eleven()["economy_models"])
    if lv.get("speed"):
        p.setdefault("speed", lv["speed"])
    r = elevenlabs_batch(p, outdir, drive, reel_id, sub)
    if not r.get("ok"):
        print(f"voice: ElevenLabs did not record ({r.get('error')})", file=sys.stderr)
        return None, r.get("error")
    try:
        note_use(drive, "elevenlabs", reel_id, r.get("credits", 0), r.get("reused", 0), sub=subscription() if r.get("credits") else sub)
    except Exception:
        pass
    return r, None


def backup_note(drive, reel_id, why):
    """The backup spoke: count it, and say why in words Harish can read."""
    try:
        note_use(drive, "microsoft", reel_id, why=why)
    except Exception:
        pass
    return f"The backup voice (Microsoft) spoke this reel: {why}." if why else None


def batch(plan, outdir, fresh=False, drive=None, reel_id=None):
    """plan = {"lines":[{"text":...}], "provider":..., "voice":..., "rate":..., "pitch":..., "speed":...}
    → {"ok", "provider", "clips":[{"file","seconds"}], "note"}. `note` says in plain words when the backup spoke."""
    r, why = main_voice(plan, os.path.join(outdir, "elevenlabs"), drive, reel_id)
    if r:
        return r
    if "microsoft" not in order(plan.get("provider"), drive):
        return {"ok": False, "error": why or "no voice answered"}
    r = microsoft_batch(plan, os.path.join(outdir, "microsoft"), fresh)
    if not r.get("ok"):                           # one fresh try for the free voice (its service drops now and then)
        r = microsoft_batch(plan, os.path.join(outdir, "microsoft"), True)
    if r.get("ok"):
        note = backup_note(drive, reel_id, why)
        if note:
            r["note"] = note
    return r


def check():
    """For the Health job and the smoke test: is the main voice ready? Costs no credits."""
    if not key():
        return False, "No ElevenLabs key reaches this job (secret ELEVENLABS_API_KEY). The Microsoft backup voice is used."
    k, base = key(), eleven().get("base", "https://api.elevenlabs.io")
    sub = subscription()
    try:
        r = requests.get(f"{base}/v1/voices/{voice_id(None)}", headers={"xi-api-key": k}, timeout=20)
        if r.status_code == 401 and not sub:
            return False, "The ElevenLabs key was refused. The Microsoft backup voice is used."
        name = r.json().get("name") if r.ok else None
    except Exception as ex:
        return False, f"ElevenLabs did not answer ({str(ex)[:80]}). The Microsoft backup voice is used."
    credits = f"{sub['left']:,} of {sub['limit']:,} credits left, new credits on {sub['resets']}" if sub else "credits could not be read with this key"
    return True, f"ElevenLabs key works · voice: {name or 'set by id'} · {credits}"
