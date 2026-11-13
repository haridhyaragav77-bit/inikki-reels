#!/usr/bin/env python3
"""Audio and timeline for one reel plan. No AI: text-to-speech, mixing and timing only.

Usage: python3 engine/render/audio.py <plan.json> <workdir>
Writes <workdir>/audio.wav and <workdir>/timeline.json.

- Voice: Microsoft neural voice (edge-tts) with word timings, so graphics can land on the word.
- Music: 1-3 sections from the music library that follow the story; starts on frame 1, never silent;
  crossfades at story turns; ducks under the voice (AGENT.md 5.4).
- Sound effects: small synthesized whooshes, hits, ticks and stamps for transitions and big moments.
"""
import sys, os, json, asyncio, hashlib, subprocess
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SR = 48000
MUSIC_DIR = os.path.join(ROOT, "engine", ".cache", "music")
VOICE_CACHE = os.path.join(ROOT, "engine", ".cache", "voice")
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None


def rp(p):
    return p if os.path.isabs(p) else os.path.join(ROOT, p)


def decode(path, ch=2, start=0.0, dur=None):
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{max(0.0, start):.3f}", "-i", path]
    if dur:
        cmd += ["-t", f"{dur:.3f}"]
    cmd += ["-ac", str(ch), "-ar", str(SR), "-f", "f32le", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32).reshape(-1, ch).copy()


def rms(x):
    return float(np.sqrt(np.mean(x.astype(np.float64) ** 2)) + 1e-12)


def db(x):
    return 20 * np.log10(x + 1e-12)


def lufs(x):
    """Integrated loudness (EBU R128) of a stereo float buffer, measured by ffmpeg."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-af", "ebur128", "-f", "null", "-"], input=x.astype(np.float32).tobytes(), capture_output=True)
    import re
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r.stderr.decode(errors="ignore"))
    return float(m[-1]) if m else -99.0


# ---------------------------------------------------------------- voice
def tts_module():
    ca = os.environ.get("SSL_CERT_FILE")
    if ca and os.path.exists(ca) and "edge_tts" not in sys.modules:
        import certifi
        certifi.where = lambda: ca
    import edge_tts
    return edge_tts


async def speak(text, voice, rate, pitch):
    """Returns (mp3_path, words). Cached by content."""
    os.makedirs(VOICE_CACHE, exist_ok=True)
    key = hashlib.sha1(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
    mp3 = os.path.join(VOICE_CACHE, key + ".mp3")
    meta = mp3 + ".json"
    if os.path.exists(mp3) and os.path.exists(meta):
        return mp3, json.load(open(meta, encoding="utf-8"))
    edge_tts = tts_module()
    words = []
    for attempt in range(3):
        try:
            comm = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, proxy=PROXY, boundary="WordBoundary")
            with open(mp3, "wb") as f:
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "WordBoundary":
                        words.append({"w": chunk["text"], "t": chunk["offset"] / 1e7, "d": chunk["duration"] / 1e7})
            break
        except Exception as e:  # network hiccup: retry
            words = []
            if attempt == 2:
                raise
            await asyncio.sleep(2 + attempt * 3)
    json.dump(words, open(meta, "w", encoding="utf-8"), ensure_ascii=False)
    return mp3, words


# ---------------------------------------------------------------- sound effects (synthesized, royalty-free)
def onepole_lp(x, a):
    """One-pole low-pass with per-sample coefficient array a (0..1)."""
    y = np.empty_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc += a[i] * (x[i] - acc)
        y[i] = acc
    return y


def sfx(kind, seed=1):
    r = np.random.default_rng(seed)
    if kind == "whoosh":
        d = 0.5; n = int(SR * d); t = np.arange(n) / SR
        noise = r.standard_normal(n)
        sweep = 0.02 + 0.35 * np.sin(np.pi * t / d) ** 2
        y = onepole_lp(noise, sweep) - onepole_lp(noise, sweep * 0.08)
        y *= np.sin(np.pi * t / d) ** 3 * 1.6
    elif kind == "impact":
        d = 1.1; n = int(SR * d); t = np.arange(n) / SR
        f = 40 + 70 * np.exp(-t * 9)
        sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
        burst = onepole_lp(r.standard_normal(n), np.full(n, 0.25)) * np.exp(-t * 35)
        y = sub * 0.9 + burst * 0.8
    elif kind == "stamp":
        d = 0.45; n = int(SR * d); t = np.arange(n) / SR
        f = 55 + 110 * np.exp(-t * 25)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 14) + r.standard_normal(n) * np.exp(-t * 70) * 0.6
    elif kind == "tick":
        d = 0.06; n = int(SR * d); t = np.arange(n) / SR
        y = np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 160) * 0.7 + r.standard_normal(n) * np.exp(-t * 600) * 0.3
    elif kind == "pop":
        d = 0.12; n = int(SR * d); t = np.arange(n) / SR
        f = 500 + 500 * (t / d)
        y = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 40) * 0.6
    elif kind == "glitch":
        d = 0.28; n = int(SR * d); t = np.arange(n) / SR
        gate = (np.floor(t / 0.018) % 2 == 0).astype(float) * (r.random(int(d / 0.018) + 2)[(t / 0.018).astype(int)] > 0.3)
        sq = np.sign(np.sin(2 * np.pi * (220 + 900 * r.random()) * t))
        crushed = np.round(r.standard_normal(n) * 3) / 3
        y = (sq * 0.35 + crushed * 0.35) * gate * np.exp(-t * 4)
    elif kind == "riser":
        d = 0.9; n = int(SR * d); t = np.arange(n) / SR
        f = 180 * (1 + 5 * (t / d) ** 2)
        y = (np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + onepole_lp(r.standard_normal(n), 0.05 + 0.4 * (t / d)) * 0.7) * (t / d) ** 2
    else:
        return np.zeros((1, 2), dtype=np.float32)
    y = y / (np.max(np.abs(y)) + 1e-9)
    return np.stack([y, y], axis=1).astype(np.float32)


SFX_GAIN = {"whoosh": 0.22, "impact": 0.42, "stamp": 0.45, "tick": 0.16, "pop": 0.16, "glitch": 0.22, "riser": 0.2}
AUTO_SFX = {"whip": ("whoosh", -0.18), "zoom": ("whoosh", -0.2), "flash": ("impact", -0.02), "glitch": ("glitch", -0.1),
            "wipe": ("whoosh", -0.2), "push": ("whoosh", -0.2)}


# ---------------------------------------------------------------- music
def music_profile(track):
    j = os.path.join(MUSIC_DIR, track + ".json")
    if not os.path.exists(j):
        sys.path.insert(0, os.path.join(ROOT, "engine", "tools"))
        from music_profile import profile
        json.dump(profile(os.path.join(MUSIC_DIR, track + ".mp3")), open(j, "w"))
    return json.load(open(j))


def match_word(words, key):
    k = key.strip().lower()
    for w in words:
        if k in w["w"].lower() or w["w"].lower() in k and len(w["w"]) > 2:
            return w
    return None


def main(plan_path, work):
    plan = json.load(open(plan_path, encoding="utf-8"))
    os.makedirs(work, exist_ok=True)
    vcfg = plan.get("voice", {})
    voice_on = bool(vcfg.get("on"))
    screens = plan["screens"]

    # 1. voice lines
    voice_clips = {}
    if voice_on:
        async def all_lines():
            for i, s in enumerate(screens):
                if s.get("voice"):
                    voice_clips[i] = await speak(s["voice"], vcfg.get("voice", "ta-IN-ValluvarNeural"),
                                                 s.get("rate", vcfg.get("rate", "+25%")), vcfg.get("pitch", "-2Hz"))
        asyncio.run(all_lines())

    # 2. timeline
    t = 0.0
    tl = []
    voice_audio = {}
    for i, s in enumerate(screens):
        lead = s.get("lead", 0.45 if i == 0 else 0.12)
        entry = {"i": i, "kind": s.get("kind"), "start": round(t, 3)}
        if i in voice_clips:
            mp3, words = voice_clips[i]
            v = decode(mp3, ch=1)
            vd = len(v) / SR
            voice_audio[i] = v
            dur = max(s.get("min", 0.0), lead + vd + s.get("tail", 0.3))
            entry["voice_at"] = round(t + lead, 3)
            entry["voice_end"] = round(t + lead + vd, 3)
            entry["words"] = [{"w": w["w"], "t": round(t + lead + w["t"], 3), "d": round(w["d"], 3)} for w in words]
        else:
            dur = float(s.get("dur", 3.0))
            entry["words"] = []
        entry["end"] = round(t + dur, 3)
        tl.append(entry)
        t += dur
    total = round(t, 3)
    N = int(round(total * SR))

    # 3. voice track
    voice = np.zeros(N, dtype=np.float32)
    for i, v in voice_audio.items():
        a = int(tl[i]["voice_at"] * SR)
        seg = v[:, 0][: max(0, N - a)]
        voice[a:a + len(seg)] += seg
    if voice_on and np.any(voice):
        voiced = np.abs(voice) > 1e-4
        voice *= (10 ** (-17 / 20)) / rms(voice[voiced])

    # 4. music sections
    m = plan.get("music", {})
    secs = m.get("sections", [])
    xf = float(m.get("xfade", 0.7))
    music = np.zeros((N, 2), dtype=np.float32)
    beats = []
    sec_out = []
    starts = []
    for k, sec in enumerate(secs):
        st = tl[sec["screen"]]["start"] if "screen" in sec else float(sec.get("at", 0))
        starts.append(st)
    target = 10 ** ((m.get("level_db", -18 if voice_on else -15)) / 20)
    for k, sec in enumerate(secs):
        st = starts[k]
        en = starts[k + 1] if k + 1 < len(secs) else total
        pre = xf / 2 if k > 0 else 0.0
        post = xf / 2 if k + 1 < len(secs) else 0.0
        need = (en - st) + pre + post
        path = os.path.join(MUSIC_DIR, sec["track"] + ".mp3")
        frm = float(sec.get("from", 0))
        seg = decode(path, 2, frm - pre, need + 0.05)
        while len(seg) < int(need * SR):  # loop if the track is short
            seg = np.concatenate([seg, decode(path, 2, frm, need)])
        seg = seg[: int(need * SR)]
        seg *= target / rms(seg) * float(sec.get("gain", 1.0))
        n = len(seg)
        env = np.ones(n, dtype=np.float32)
        fin = int((xf if k > 0 else 0.02) * SR)
        env[:fin] = np.linspace(0, 1, fin) ** 0.8 if fin > 0 else env[:fin]
        if k + 1 < len(secs):
            fo = int(xf * SR)
            env[-fo:] = np.linspace(1, 0, fo) ** 0.8
        else:
            fo = int(float(m.get("fade_out", 1.0)) * SR)
            env[-fo:] = np.linspace(1, 0, fo) ** 1.5
        seg *= env[:, None]
        a = int((st - pre) * SR)
        b = min(N, a + n)
        music[a:b] += seg[: b - a]
        prof = music_profile(sec["track"])
        for bt in prof["beats"]:
            rt = bt - frm + st
            if st - 0.01 <= rt < en:
                beats.append(round(rt, 3))
        sec_out.append({"track": sec["track"], "from": frm, "start": st, "end": en, "mood": sec.get("mood", "")})

    # ducking under voice
    if voice_on and np.any(voice):
        hop = int(SR * 0.01)
        frames = len(voice) // hop
        e = np.sqrt(np.mean(voice[: frames * hop].reshape(frames, hop) ** 2, axis=1))
        e = np.clip(e / 0.02, 0, 1)
        sm = np.zeros_like(e)
        acc = 0.0
        for i in range(frames):
            c = 0.5 if e[i] > acc else 0.04  # fast attack, slow release
            acc += c * (e[i] - acc)
            sm[i] = acc
        g = 1 - (1 - float(m.get("duck", 0.28))) * np.clip(sm * 1.5, 0, 1)
        gain = np.repeat(g, hop)
        gain = np.concatenate([gain, np.full(N - len(gain), gain[-1] if len(gain) else 1.0)])
        music *= gain[:, None].astype(np.float32)

    # 5. sound effects
    fx = np.zeros((N, 2), dtype=np.float32)
    fx_events = []
    for i, s in enumerate(screens):
        tin = s.get("in")
        if i > 0 and tin in AUTO_SFX:
            kind, off = AUTO_SFX[tin]
            fx_events.append({"t": tl[i]["start"] + off, "type": kind})
        for e in s.get("sfx", []):
            at = e.get("at", 0)
            if isinstance(at, dict) and "word" in at:
                w = match_word(tl[i]["words"], at["word"])
                tt = (w["t"] if w else tl[i]["start"]) + at.get("off", 0)
            elif at == "end":
                tt = tl[i]["end"]
            else:
                tt = tl[i]["start"] + float(at)
            fx_events.append({"t": tt, "type": e["type"]})
    for k, ev in enumerate(fx_events):
        y = sfx(ev["type"], seed=k + 7) * SFX_GAIN.get(ev["type"], 0.2) * float(plan.get("sfx_gain", 1.0))
        a = int(max(0, ev["t"]) * SR)
        b = min(N, a + len(y))
        if b > a:
            fx[a:b] += y[: b - a]

    # 6. mix, level to a fixed loudness (bold but inside the check range), gentle limiter
    mix = music + fx + np.stack([voice, voice], axis=1)
    target = float(m.get("target_lufs", -13.0 if voice_on else -11.0))
    measured = lufs(mix)
    if measured > -70:
        mix *= 10 ** ((target - measured) / 20)
    knee, ceil = 0.7, 0.89  # soft-knee limiter: below the knee nothing changes; peaks bend smoothly under the ceiling
    ax = np.abs(mix)
    mix = np.where(ax <= knee, mix, np.sign(mix) * (knee + (ceil - knee) * np.tanh((ax - knee) / (ceil - knee))))
    raw = mix.astype(np.float32).tobytes()
    wav = os.path.join(work, "audio.wav")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-c:a", "pcm_s16le", wav],
                   input=raw, check=True)

    timeline = {"id": plan["id"], "duration": total, "fps": plan.get("fps", 30), "screens": tl,
                "beats": sorted(set(beats)), "music": sec_out, "sfx": fx_events}
    json.dump(timeline, open(os.path.join(work, "timeline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    first = rms(mix[: int(0.5 * SR)])
    print(json.dumps({"ok": True, "duration": total, "screens": len(tl), "beats": len(beats),
                      "first_half_second_db": round(float(db(first)), 1)}))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
