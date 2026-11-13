#!/usr/bin/env python3
"""Inspect a finished reel (AGENT.md stage 8). No AI.
Usage: python3 engine/render/check_reel.py reel.mp4 timeline.json plan.json
Checks: sound in the first half-second, no unplanned silence over 1 s, no frozen picture over 1 s,
no black frames, length within the series range, loudness. Prints a JSON report; "pass" is true or false."""
import sys, json, re, subprocess, os
import numpy as np

mp4, tl_path, plan_path = sys.argv[1:4]
tl = json.load(open(tl_path, encoding="utf-8"))
plan = json.load(open(plan_path, encoding="utf-8"))
checks = {}


def ff(filters, audio=False):
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", mp4] + (["-af", filters, "-vn"] if audio else ["-vf", filters, "-an"]) + ["-f", "null", "-"]
    return subprocess.run(cmd, capture_output=True, text=True).stderr


# sound from the first half-second
raw = subprocess.run(["ffmpeg", "-v", "error", "-i", mp4, "-t", "0.5", "-ac", "1", "-ar", "48000", "-f", "f32le", "-"], capture_output=True).stdout
x = np.frombuffer(raw, dtype=np.float32)
first_db = float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)) if len(x) else -120
checks["sound_in_first_half_second"] = {"ok": first_db > -35, "db": round(first_db, 1)}

# silences over 1 s
sil = re.findall(r"silence_start: ([\d.]+)", ff("silencedetect=noise=-45dB:d=1", audio=True))
checks["no_silence_over_1s"] = {"ok": len(sil) == 0, "at": [round(float(s), 2) for s in sil]}

# frozen picture over 1 s
frz = re.findall(r"freeze_start: ([\d.]+)", ff("freezedetect=n=0.0015:d=1"))
checks["no_frozen_picture_over_1s"] = {"ok": len(frz) == 0, "at": [round(float(s), 2) for s in frz]}

# black frames
blk = re.findall(r"black_start:([\d.]+)", ff("blackdetect=d=0.3:pix_th=0.06"))
checks["no_black_frames"] = {"ok": len(blk) == 0, "at": [round(float(s), 2) for s in blk]}

# length within series range (content can stretch a breakdown to 75 s with a reason)
dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", mp4], capture_output=True, text=True).stdout.strip() or 0)
lo, hi = plan.get("length_s", [10, 75])
checks["length"] = {"ok": lo - 1 <= dur <= hi + 1, "seconds": round(dur, 1), "range": [lo, hi]}

# loudness (Instagram plays around -14 LUFS)
m = re.findall(r"I:\s+(-?[\d.]+) LUFS", ff("ebur128", audio=True))
lufs = float(m[-1]) if m else -99
checks["loudness"] = {"ok": -20 <= lufs <= -9, "lufs": lufs}

ok = all(c["ok"] for c in checks.values())
print(json.dumps({"pass": ok, "checks": checks}, ensure_ascii=False))
