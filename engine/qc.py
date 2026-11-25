"""Inspection (AGENT.md 5 stage 8, safety rule 8): nothing posts that fails here.
A failing reel is held; the day carries on with a reserve (fail soft)."""
import json
import os
import re
import shutil
import subprocess

from . import audio
from .assets import media_duration

MAX_MB = 95


def _ffmpeg():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def _probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=codec_type,codec_name,width,height,r_frame_rate",
                        "-of", "json", path], capture_output=True, text=True)
    try:
        return json.loads(r.stdout).get("streams", [])
    except ValueError:
        return []


def check(final_mp4, res, series, template_flags, cover_path):
    problems, warnings, checks = [], [], {}
    total = media_duration(final_mp4)
    checks["seconds"] = round(total, 2)
    lo, hi = (series.get("length_s") or [3, 90])[:2]
    if total < 3 or total > 90:
        problems.append(f"length {total:.1f} s is outside what Instagram accepts for this kind of reel")
    elif isinstance(series.get("strict_length"), dict) and total < float(series["strict_length"].get("floor_s") or lo - 2):   # Harish, 25 Nov (AGENT.md 5.9)
        problems.append(f"length {total:.1f} s is under this series' floor of {series['strict_length'].get('floor_s')} s; the plan needs more voice")
    elif total < lo - 2 or total > hi + 3:
        warnings.append(f"length {total:.1f} s is outside the series range {lo}-{hi} s")

    streams = _probe(final_mp4)
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), {})
    checks["video"] = f"{v.get('codec_name')} {v.get('width')}x{v.get('height')} {v.get('r_frame_rate')}"
    checks["audio"] = a.get("codec_name")
    if (v.get("width"), v.get("height")) != (1080, 1920):
        problems.append(f"frame size is {v.get('width')}x{v.get('height')}, not 1080x1920")
    if v.get("codec_name") != "h264" or a.get("codec_name") != "aac":
        problems.append("file is not H.264 video with AAC sound")
    mb = os.path.getsize(final_mp4) / 1e6
    checks["size_mb"] = round(mb, 1)
    if mb > MAX_MB:
        problems.append(f"file is {mb:.0f} MB, over the {MAX_MB} MB limit")

    # blank or black stretches
    r = subprocess.run([_ffmpeg(), "-i", final_mp4, "-vf", "blackdetect=d=0.4:pix_th=0.05", "-an", "-f", "null", "-"],
                       capture_output=True, text=True).stderr
    black = re.findall(r"black_start:([\d.]+) black_end:([\d.]+)", r)
    checks["black_stretches"] = len(black)
    if black:
        problems.append("blank frames at " + ", ".join(f"{float(b[0]):.1f}-{float(b[1]):.1f} s" for b in black[:3]))

    # loudness
    lufs = audio.loudness(final_mp4)
    checks["loudness_lufs"] = lufs
    if lufs is None:
        problems.append("no sound could be measured")
    elif not (-17.0 <= lufs <= -11.0):
        problems.append(f"loudness {lufs:.1f} LUFS is outside -17 to -11 (target {audio.TARGET_LUFS:.0f})")

    # voice and screens in step
    late = [vc for vc in res.get("voice_clips", []) if vc["seconds"] > float(res["screens"][vc["screen"]]["dur"]) + 0.05]
    checks["voice_lines"] = len(res.get("voice_clips", []))
    if late:
        problems.append(f"{len(late)} voice line(s) run past their screen")
    if res.get("voice_failed"):
        warnings.append("voice was not recorded; this is the silent version")

    # what the template itself noticed: text that would not fit, anything outside the safe zones
    fit = [f for f in template_flags if "does not fit" in f.get("flag", "")]
    safe = [f for f in template_flags if "safe line" in f.get("flag", "") or "buttons" in f.get("flag", "") or "left edge" in f.get("flag", "")]
    soft = [f for f in template_flags if f not in fit and f not in safe]
    checks["template_flags"] = template_flags
    if fit:
        problems.append(f"{len(fit)} text block(s) do not fit: " + "; ".join(f.get("text", "")[:40] for f in fit[:3]))
    if safe:
        problems.append("outside the safe zones: " + "; ".join(sorted({f"screen {f['screen'] + 1}: {f['flag']} ({f['by']} px)" for f in safe})[:4]))
    for f in soft[:4]:
        warnings.append(f"screen {f.get('screen', 0) + 1}: {f['flag']}")

    if not (cover_path and os.path.exists(cover_path) and os.path.getsize(cover_path) > 5000):
        problems.append("cover image is missing")

    # stand-in pictures must never post
    if res.get("images"):
        stand_ins = sum(1 for im in res["images"] if im.get("source") == "placeholder")
    else:
        stand_ins = sum(1 for s in res["screens"] if isinstance(s.get("visual"), dict) and s["visual"].get("source") == "placeholder" and s.get("visual_changed"))
    if any(str(vc.get("file", "")).endswith(".mp3") and res.get("voice_stand_in") for vc in res.get("voice_clips", [])):
        problems.append("the voice is a stand-in tone, not the real voice")
    checks["stand_in_pictures"] = stand_ins
    if stand_ins:
        problems.append(f"{stand_ins} picture(s) are stand-ins, not real images")

    stand_in_only = bool(problems) and all("stand-in" in p for p in problems)     # a test run with stand-ins is held, but nothing is broken
    return {"pass": not problems, "problems": problems, "warnings": warnings, "checks": checks, "stand_in_only": stand_in_only}
