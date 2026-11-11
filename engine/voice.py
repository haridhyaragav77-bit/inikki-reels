"""Tamil voice through Harish's tools/voice_tool.py (AGENT.md 4.4). Call it, never rewrite it."""
import json
import os
import subprocess
import sys

from .settings import ENGINE, ROOT

TOOL = str(ROOT / ENGINE["voice"]["tool"])


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


def defaults():
    v = ENGINE["voice"]
    return {"voice": v["voice"], "rate": v["rate"], "pitch": v["pitch"]}


def say(text, out_path, voice=None, rate=None, pitch=None):
    d = defaults()
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    # Values like "-2Hz" start with a dash, so they must be passed as --pitch=-2Hz
    return _run(["say", "--text", text, "--out", out_path, f"--voice={voice or d['voice']}",
                 f"--rate={rate or d['rate']}", f"--pitch={pitch or d['pitch']}"])


def batch(plan, outdir, fresh=False):
    """plan = {"voice":..., "rate":..., "pitch":..., "lines":[{"text":...}, ...]} → clips + full.mp3 with real lengths.
    fresh=True remakes every clip (used on a retry, so a half-written clip from a failed try is never reused)."""
    os.makedirs(outdir, exist_ok=True)
    for name in os.listdir(outdir):          # an empty clip left by a failed try would break the tool's length reader
        fp = os.path.join(outdir, name)
        if name.endswith(".mp3") and os.path.getsize(fp) < 1000:
            os.remove(fp)
    p = os.path.join(outdir, "plan.json")
    full = {**defaults(), **plan}
    with open(p, "w", encoding="utf-8") as f:
        json.dump(full, f, ensure_ascii=False)
    return _run(["batch", "--plan", p, "--outdir", outdir] + (["--fresh"] if fresh else []))


def voices(lang="ta"):
    return _run(["voices", "--lang", lang], timeout=120)
