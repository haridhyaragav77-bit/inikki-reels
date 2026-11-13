"""Tamil voice through ElevenLabs (AGENT.md 4.4). The key is the GitHub Secret ELEVENLABS_API_KEY.
The voice, model and speed are settings (config/agent.yaml voice:); a series may set its own voice_id.
Every call returns a dict with "ok", like the old voice tool, so callers fail soft."""
import json
import os
import re
import subprocess
import urllib.error
import urllib.request

from .settings import AGENT, ENGINE

API = ENGINE["voice"].get("api", "https://api.elevenlabs.io/v1")


def _key():
    return os.environ.get("ELEVENLABS_API_KEY", "").strip()


def _ffmpeg():
    import shutil
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def duration(path):
    """Length of an audio file in seconds (ffmpeg prints it; no extra library needed)."""
    r = subprocess.run([_ffmpeg(), "-hide_banner", "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr or "")
    return round(int(m[1]) * 3600 + int(m[2]) * 60 + float(m[3]), 2) if m else 0.0


def _call(method, path, body=None, raw=False, timeout=120):
    key = _key()
    if not key:
        return {"ok": False, "error": "ELEVENLABS_API_KEY is not set (GitHub Secret)"}
    req = urllib.request.Request(API + path, method=method, headers={"xi-api-key": key, "Content-Type": "application/json",
                                                                     "Accept": "audio/mpeg" if raw else "application/json"},
                                 data=json.dumps(body, ensure_ascii=False).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = r.read()
            return {"ok": True, "bytes": data} if raw else {"ok": True, **json.loads(data or b"{}")}
    except urllib.error.HTTPError as e:
        detail = e.read()[:300].decode("utf-8", "replace")
        return {"ok": False, "status": e.code, "error": f"ElevenLabs {e.code}: {detail}"}
    except Exception as e:  # network, timeout
        return {"ok": False, "error": f"ElevenLabs unreachable: {e}"}


def defaults(series=None):
    v = dict(AGENT.get("voice") or {})
    if series and series.get("voice_id"):
        v["voice_id"] = series["voice_id"]
    return v


def say(text, out_path, voice_id=None, series=None, **_ignored):
    """One line → mp3. Old keyword args (voice, rate, pitch) are ignored: those were Microsoft settings."""
    v = defaults(series)
    body = {"text": text, "model_id": v.get("model", "eleven_multilingual_v2"), "language_code": "ta",
            "voice_settings": {"stability": v.get("stability", 0.45), "similarity_boost": v.get("similarity_boost", 0.8),
                               "speed": v.get("speed", 1.0)}}
    fmt = ENGINE["voice"].get("output_format", "mp3_44100_128")
    r = _call("POST", f"/text-to-speech/{voice_id or v['voice_id']}?output_format={fmt}", body, raw=True)
    if not r["ok"] and r.get("status") in (400, 422) and "language_code" in r.get("error", ""):
        body.pop("language_code")                       # a model that does not take language_code
        r = _call("POST", f"/text-to-speech/{voice_id or v['voice_id']}?output_format={fmt}", body, raw=True)
    if not r["ok"]:
        return r
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "wb") as f:
        f.write(r["bytes"])
    return {"ok": True, "file": os.path.abspath(out_path), "seconds": duration(out_path), "chars": len(text)}


def batch(plan, outdir, fresh=False, series=None):
    """plan = {"lines":[{"text":...}, ...], "voice_id"?: ...} → line_NN.mp3 clips + full.mp3, with real lengths.
    fresh=True remakes every clip; otherwise a good clip from an earlier try is reused (no credits spent twice)."""
    os.makedirs(outdir, exist_ok=True)
    clips, chars = [], 0
    for n, ln in enumerate(plan.get("lines", [])):
        f = os.path.join(outdir, f"line_{n:02d}.mp3")
        if not fresh and os.path.exists(f) and os.path.getsize(f) > 1000:
            clips.append({"file": f, "seconds": duration(f)})
            continue
        r = say(ln["text"], f, voice_id=ln.get("voice_id") or plan.get("voice_id"), series=series)
        if not r.get("ok"):
            return {"ok": False, "error": r.get("error"), "clips_done": n}
        chars += r["chars"]
        clips.append({"file": r["file"], "seconds": r["seconds"]})
    full = os.path.join(outdir, "full.mp3")
    if clips:
        gap = float(ENGINE["voice"].get("gap_s", 0.3))
        args, parts = [_ffmpeg(), "-y", "-v", "error"], []
        for i, c in enumerate(clips):
            args += ["-i", c["file"]]
            parts.append(f"[{i}:a]apad=pad_dur={gap}[a{i}]")
        args += ["-filter_complex", ";".join(parts) + ";" + "".join(f"[a{i}]" for i in range(len(clips)))
                 + f"concat=n={len(clips)}:v=0:a=1[out]", "-map", "[out]", full]
        subprocess.run(args, check=False)
    return {"ok": True, "clips": clips, "full": os.path.abspath(full), "chars": chars,
            "total_seconds": duration(full) if os.path.exists(full) else 0}


def voices():
    r = _call("GET", "/voices")
    if r.get("ok"):
        r["voices"] = [{"id": x["voice_id"], "name": x["name"]} for x in r.get("voices", [])]
    return r


def usage():
    """The subscription numbers: plan, credits used / limit / left, reset date."""
    r = _call("GET", "/user/subscription")
    if not r.get("ok"):
        return r
    used, limit = int(r.get("character_count", 0)), int(r.get("character_limit", 0) or 0)
    reset = r.get("next_character_count_reset_unix")
    from datetime import datetime, timezone
    return {"ok": True, "plan": r.get("tier"), "credits_used": used, "credit_limit": limit, "credits_left": max(0, limit - used),
            "pct_used": round(used / limit, 4) if limit else None,
            "next_reset": datetime.fromtimestamp(reset, timezone.utc).isoformat() if reset else None}


def guard(series_id, u=None):
    """Cost guard (AGENT.md 4.4). Returns ("full" | "hook_payoff" | "silent", reason)."""
    g = (AGENT.get("voice") or {}).get("guard", {})
    u = u or usage()
    if not u.get("ok") or u.get("pct_used") is None:
        return "full", None                              # cannot read usage: voice normally, the voice call itself will tell
    p = u["pct_used"]
    if p >= g.get("silent_at", 1.0):
        return "silent", f"ElevenLabs credits are used up ({p:.0%}); silent versions until the reset ({u.get('next_reset', '?')[:10]})."
    if p >= g.get("breakdown_only_at", 0.95) and series_id not in (AGENT.get("voice") or {}).get("breakdown_series", ["film-breakdown"]):
        return "silent", f"ElevenLabs credits are {p:.0%} used; only Film Breakdown is voiced until the reset."
    if p >= g.get("hook_payoff_at", 0.80):
        return "hook_payoff", f"ElevenLabs credits are {p:.0%} used; only the hook and the payoff are voiced."
    return "full", None


def usage_report(drive=None, chars_today=0, reels_today=0):
    """Write status/voice_usage.json for the Control Room (AGENT.md 4.4). Returns the dict."""
    from . import status
    u = usage()
    b = AGENT.get("budgets") or {}
    out = {"ok": u.get("ok", False), "provider": "elevenlabs", "voice": (AGENT.get("voice") or {}).get("voice_name")}
    if u.get("ok"):
        out.update({k: u[k] for k in ("plan", "credits_used", "credit_limit", "credits_left", "pct_used", "next_reset")})
        price_usd = b.get("elevenlabs_plan_usd")
        rate = float(b.get("usd_to_inr", 84))
        if price_usd:
            out["plan_price_inr"] = round(float(price_usd) * rate)
            out["spent_inr_cycle"] = round(float(price_usd) * rate * (u["pct_used"] or 0), 2)
    else:
        out["error"] = u.get("error")
    prev = {}
    if drive:
        try:
            prev = drive.read_json("status", "voice_usage.json", {}) or {}
        except Exception:
            prev = {}
    today = status.now().strftime("%Y-%m-%d")
    same = prev.get("day") == today
    out["day"] = today
    out["chars_today"] = (prev.get("chars_today", 0) if same else 0) + int(chars_today)
    out["reels_today"] = (prev.get("reels_today", 0) if same else 0) + int(reels_today)
    cyc = (prev.get("reels_cycle", 0) if prev.get("next_reset") == out.get("next_reset") else 0) + int(reels_today)
    out["reels_cycle"] = cyc
    if out.get("spent_inr_cycle") is not None and cyc:
        out["inr_per_reel"] = round(out["spent_inr_cycle"] / cyc, 2)
    status.write(drive, "voice_usage.json", out)
    return out
