#!/usr/bin/env python3
"""
voice_tool.py — free text-to-speech with Microsoft neural voices (via edge-tts), plus optional dubbing onto a video.
Needs: Python 3.9+ and internet. Installs its own dependencies (edge-tts, imageio-ffmpeg) on first run.

Commands (all print a JSON result on the last line of stdout):
  python voice_tool.py voices [--lang ta]                     list available voices (optionally filter by language code)
  python voice_tool.py say  --text "..." --out out.mp3 [--voice V --rate +35% --pitch -2Hz]
  python voice_tool.py batch --plan plan.json --outdir clips  one MP3 per line + joined full.mp3
  python voice_tool.py dub  --plan plan.json --video in.mp4 [--out out.mp4]
                                                              speak each line at its start time onto the video,
                                                              lower the video's own audio under the voice

plan.json format:
{
  "voice": "ta-IN-ValluvarNeural",        # default voice (optional)
  "rate": "+35%", "pitch": "-2Hz",        # defaults (optional)
  "duck": 0.3,                            # dub only: video audio level while voice speaks (optional)
  "lines": [
    {"text": "...", "start": 0.0, "end": 4.2, "voice": "...", "rate": "+30%", "pitch": "+0Hz"}
  ]                                       # start/end only needed for dub; per-line voice/rate/pitch optional
}
"""
import argparse, asyncio, json, os, re, subprocess, sys

def need(pkg, mod):
    try: return __import__(mod)
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", pkg]); return __import__(mod)

# Behind a proxy (cloud workspaces), use the standard proxy and certificate settings. Harmless elsewhere.
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or None
def tts_lib():
    ca = os.environ.get("SSL_CERT_FILE")
    if ca and os.path.exists(ca) and "edge_tts" not in sys.modules:
        import certifi; certifi.where = lambda: ca
    return need("edge-tts", "edge_tts")

def ff():
    return need("imageio-ffmpeg", "imageio_ffmpeg").get_ffmpeg_exe()

def duration(path):
    err = subprocess.run([ff(), "-i", path], capture_output=True, text=True).stderr
    h, m, s = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err).groups(); return int(h) * 3600 + int(m) * 60 + float(s)

DEF = {"voice": "ta-IN-ValluvarNeural", "rate": "+35%", "pitch": "-2Hz"}

async def speak(text, out, voice, rate, pitch):
    tts = tts_lib()
    await tts.Communicate(text, voice, rate=rate, pitch=pitch, proxy=PROXY).save(out)
    return round(duration(out), 2)

def line_cfg(plan, ln):
    g = {k: plan.get(k, DEF[k]) for k in DEF}
    return {k: ln.get(k, g[k]) for k in DEF}

def cmd_voices(a):
    tts = tts_lib()
    vs = asyncio.run(tts.list_voices(proxy=PROXY))
    vs = [{"name": v["ShortName"], "gender": v["Gender"], "locale": v["Locale"]} for v in vs if not a.lang or v["Locale"].lower().startswith(a.lang.lower())]
    for v in vs: print(f'{v["name"]:32s} {v["gender"]:7s} {v["locale"]}')
    print(json.dumps({"ok": True, "voices": vs}, ensure_ascii=False))

def cmd_say(a):
    d = asyncio.run(speak(a.text, a.out, a.voice, a.rate, a.pitch))
    print(json.dumps({"ok": True, "file": os.path.abspath(a.out), "seconds": d}))

async def make_clips(plan, outdir, reuse=True):
    os.makedirs(outdir, exist_ok=True); res = []
    for i, ln in enumerate(plan["lines"]):
        out = os.path.join(outdir, f"line_{i:02d}.mp3"); c = line_cfg(plan, ln)
        d = round(duration(out), 2) if reuse and os.path.exists(out) else await speak(ln["text"], out, c["voice"], c["rate"], c["pitch"])
        res.append({"line": i, "file": os.path.abspath(out), "seconds": d}); print(f"  line {i + 1}/{len(plan['lines'])}: {d}s", flush=True)
    return res

def cmd_batch(a):
    plan = json.load(open(a.plan, encoding="utf-8"))
    res = asyncio.run(make_clips(plan, a.outdir, reuse=not a.fresh))
    full = os.path.join(a.outdir, "full.mp3"); ins = []; parts = []
    for i, r in enumerate(res):
        ins += ["-i", r["file"]]; parts.append(f"[{i}:a]aresample=24000,apad=pad_dur=0.3[a{i}]")
    parts.append("".join(f"[a{i}]" for i in range(len(res))) + f"concat=n={len(res)}:v=0:a=1[o]")
    subprocess.run([ff(), "-y", "-v", "error", *ins, "-filter_complex", ";".join(parts), "-map", "[o]", full], check=True)
    print(json.dumps({"ok": True, "clips": res, "full": os.path.abspath(full), "total_seconds": round(duration(full), 2)}))

def cmd_dub(a):
    plan = json.load(open(a.plan, encoding="utf-8")); lines = plan["lines"]
    outdir = os.path.splitext(a.video)[0] + "_voice_clips"
    res = asyncio.run(make_clips(plan, outdir, reuse=not a.fresh))
    inputs = ["-i", a.video]; parts = []; labels = []; report = []
    for i, (ln, r) in enumerate(zip(lines, res)):
        inputs += ["-i", r["file"]]
        slot = max(0.5, ln.get("end", ln["start"] + r["seconds"] + 1) - ln["start"] - 0.1)
        tempo = min(1.35, max(1.0, r["seconds"] / slot)); ms = int(ln["start"] * 1000 + 80)
        parts.append(f"[{i + 1}:a]aresample=48000,atempo={tempo:.3f},adelay={ms}|{ms},apad[v{i}]"); labels.append(f"[v{i}]")
        report.append({"line": i, "voice_seconds": r["seconds"], "slot_seconds": round(slot, 2), "speedup": round(tempo, 2), "overruns": r["seconds"] / tempo > slot + 0.05})
    parts.append(f"{''.join(labels)}amix=inputs={len(lines)}:normalize=0:duration=longest[vo]")
    has_audio = "Audio:" in subprocess.run([ff(), "-i", a.video], capture_output=True, text=True).stderr
    if has_audio:
        duck = plan.get("duck", 0.3)
        parts += ["[vo]asplit=2[vo1][vo2]", f"[0:a]aresample=48000[m];[m][vo2]sidechaincompress=threshold=0.02:ratio={max(2, 1 / max(duck, 0.05)):.1f}:attack=20:release=400[d]",
                  "[d][vo1]amix=inputs=2:normalize=0:duration=first,alimiter=limit=0.95[a]"]
    else: parts.append("[vo]alimiter=limit=0.95[a]")
    out = a.out or os.path.splitext(a.video)[0] + "_VOICED.mp4"
    subprocess.run([ff(), "-y", "-v", "error", *inputs, "-filter_complex", ";".join(parts), "-map", "0:v", "-map", "[a]", "-c:v", "copy",
                    "-c:a", "aac", "-b:a", "192k", "-t", f"{duration(a.video):.3f}", "-movflags", "+faststart", out], check=True)
    print(json.dumps({"ok": True, "video": os.path.abspath(out), "lines": report}))

def main():
    p = argparse.ArgumentParser(description="Free Microsoft neural TTS + video dubbing"); s = p.add_subparsers(dest="cmd", required=True)
    v = s.add_parser("voices"); v.add_argument("--lang"); v.set_defaults(f=cmd_voices)
    y = s.add_parser("say"); y.add_argument("--text", required=True); y.add_argument("--out", required=True)
    for q in (y,):
        q.add_argument("--voice", default=DEF["voice"]); q.add_argument("--rate", default=DEF["rate"]); q.add_argument("--pitch", default=DEF["pitch"])
    y.set_defaults(f=cmd_say)
    b = s.add_parser("batch"); b.add_argument("--plan", required=True); b.add_argument("--outdir", required=True); b.add_argument("--fresh", action="store_true"); b.set_defaults(f=cmd_batch)
    d = s.add_parser("dub"); d.add_argument("--plan", required=True); d.add_argument("--video", required=True); d.add_argument("--out"); d.add_argument("--fresh", action="store_true"); d.set_defaults(f=cmd_dub)
    a = p.parse_args()
    try: a.f(a)
    except Exception as e: print(json.dumps({"ok": False, "error": str(e)})); sys.exit(1)

if __name__ == "__main__":
    main()
