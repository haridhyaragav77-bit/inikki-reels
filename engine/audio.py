"""The sound mix for one reel (AGENT.md 5.4): music bed, voice on top, music dropped under the voice,
clip or meme sound where the plan asks, countdown ticks, then levelled to the same loudness every time."""
import json
import os
import re
import shutil
import subprocess

from .assets import media_duration

TARGET_LUFS = -14.0


def _ffmpeg():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


SFX = {   # small synthesized sounds (no files, no licences): source, filter chain
    "tick":   ("sine=frequency=1500:duration=0.035", "afade=t=out:st=0.005:d=0.03,volume=0.22"),
    "tock":   ("sine=frequency=720:duration=0.11", "afade=t=out:st=0.01:d=0.1,volume=0.75"),
    "pop":    ("sine=frequency=580:duration=0.09", "afade=t=out:st=0.01:d=0.08,volume=0.32"),
    "whoosh": ("anoisesrc=color=pink:duration=0.42:seed=3", "highpass=f=700,lowpass=f=5000,afade=t=in:d=0.22,afade=t=out:st=0.22:d=0.2,volume=0.2"),
    "thud":   ("sine=frequency=92:duration=0.24", "afade=t=out:st=0.02:d=0.22,volume=0.85"),
    "ding":   ("sine=frequency=1320:duration=0.7", "afade=t=out:st=0.01:d=0.69,volume=0.22"),
    "hit":    ("sine=frequency=56:duration=1.0", "afade=t=out:st=0.04:d=0.96,volume=1.3"),
}


def _sfx_file(kind, work):
    """Make one small sound once per reel; every cue of that kind reuses the file."""
    kind = kind if kind in SFX else "pop"
    path = os.path.join(work, f"sfx_{kind}.wav")
    if not os.path.exists(path):
        src, chain = SFX[kind]
        subprocess.run([_ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", src, "-af", chain + ",aresample=48000,aformat=channel_layouts=stereo", path], check=True)
    return path


def build(res, work, total, cues=None):
    """Returns the path of the finished audio (AAC, 48 kHz), exactly `total` seconds long."""
    os.makedirs(work, exist_ok=True)
    starts, t = [], 0.0
    for s in res["screens"]:
        starts.append(t)
        t += float(s["dur"])
    music = res["music_resolved"]["path"]
    mdur = media_duration(music)
    offset = 0.0 if mdur < total + 25 else round(min(mdur - total - 5, mdur * 0.08), 2)
    cmd = [_ffmpeg(), "-y", "-v", "error", "-stream_loop", "-1", "-ss", str(offset), "-i", music]
    parts, fg, extra, n = [], [], [], 1

    for vc in res.get("voice_clips", []):
        cmd += ["-i", vc["file"]]
        ms = int(round((starts[vc["screen"]] + 0.08) * 1000))
        parts.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}:all=1[f{n}]")
        fg.append(f"[f{n}]")
        n += 1
    voiced = {vc["screen"] for vc in res.get("voice_clips", [])}
    for i, s in enumerate(res["screens"]):
        v = s.get("visual") or {}
        a = v.get("audio") if isinstance(v, dict) else None
        wants = s.get("sound", v.get("type") == "meme" and i not in voiced) if isinstance(v, dict) else False
        if a and wants and os.path.exists(a) and s.get("visual_changed", True):
            cmd += ["-i", a]
            ms = int(round(starts[i] * 1000))
            parts.append(f"[{n}:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{float(s.get('vdur', s['dur'])):.2f},volume=0.9,adelay={ms}:all=1[f{n}]")
            fg.append(f"[f{n}]")
            n += 1
    if res.get("sfx", True):
        for q in (cues or [])[:90]:          # the template says when each move lands; the sound lands with it
            cmd += ["-i", _sfx_file(q.get("kind"), work)]
            parts.append(f"[{n}:a]adelay={int(round(max(0.0, float(q['t'])) * 1000))}:all=1[x{n}]")
            extra.append(f"[x{n}]")
            n += 1

    fade_out = max(0.0, total - 0.9)
    level = 0.55 if fg else 0.95
    parts.append(f"[0:a]aresample=48000,aformat=channel_layouts=stereo,atrim=0:{total:.3f},afade=t=in:d=0.35,afade=t=out:st={fade_out:.3f}:d=0.9,volume={level}[m]")
    if fg:
        parts.append(f"{''.join(fg)}amix=inputs={len(fg)}:normalize=0,apad,atrim=0:{total:.3f},asplit=2[fga][fgb]")
        parts.append("[m][fgb]sidechaincompress=threshold=0.02:ratio=9:attack=15:release=450[md]")   # music drops under the voice
        mix_in = ["[md]", "[fga]"] + extra
    else:
        mix_in = ["[m]"] + extra
    parts.append(f"{''.join(mix_in)}amix=inputs={len(mix_in)}:normalize=0,apad,atrim=0:{total:.3f}[mix]")
    raw = os.path.join(work, "mix_raw.wav")
    r = subprocess.run(cmd + ["-filter_complex", ";".join(parts), "-map", "[mix]", "-ar", "48000", "-ac", "2", raw], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("audio mix failed: " + r.stderr.strip()[-400:])

    # level to the target loudness in two passes (measure, then apply), so every reel sounds equally loud
    out = os.path.join(work, "mix.m4a")
    m = subprocess.run([_ffmpeg(), "-i", raw, "-af", f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    j = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", m, re.S)
    af = f"loudnorm=I={TARGET_LUFS}:TP=-1.5:LRA=11"
    if j:
        d = json.loads(j.group(0))
        if d.get("input_i") not in ("-inf", "inf"):
            af += (f":measured_I={d['input_i']}:measured_TP={d['input_tp']}:measured_LRA={d['input_lra']}"
                   f":measured_thresh={d['input_thresh']}:offset={d['target_offset']}:linear=true")
    subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", raw, "-af", af + ",aresample=48000", "-c:a", "aac", "-b:a", "192k", out], check=True)
    got = loudness(out)
    if got is not None and abs(got - TARGET_LUFS) > 0.8:     # wide-ranging music can miss the target: lift it and hold the peaks
        fix = f"volume={TARGET_LUFS - got:.2f}dB,alimiter=limit=0.84:attack=5:release=60:level=false,aresample=48000"
        subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", raw, "-af", af + "," + fix, "-c:a", "aac", "-b:a", "192k", out], check=True)
    os.remove(raw)
    return out


def loudness(path):
    """Integrated loudness (LUFS) of a finished file."""
    r = subprocess.run([_ffmpeg(), "-i", path, "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True).stderr
    m = re.findall(r"I:\s+(-?[\d.]+) LUFS", r)
    return float(m[-1]) if m else None
