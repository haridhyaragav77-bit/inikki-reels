#!/usr/bin/env python3
"""Music profile: energy over time, tempo and beat times for a track (no AI, numpy only).
Usage: python3 engine/tools/music_profile.py track.mp3 [--json out.json]
Prints a compact energy strip (one char per second) so a planner can pick calm / build / intense parts."""
import sys, json, subprocess, numpy as np
SR = 22050
def load(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.float32)
def profile(path):
    x = load(path); dur = len(x) / SR
    hop = 512; win = 1024
    n = 1 + (len(x) - win) // hop
    frames = np.lib.stride_tricks.as_strided(x, shape=(n, win), strides=(x.strides[0] * hop, x.strides[0]))
    spec = np.abs(np.fft.rfft(frames * np.hanning(win), axis=1))
    flux = np.maximum(0, np.diff(np.log1p(spec), axis=0)).sum(axis=1); flux = np.concatenate([[0], flux])
    flux = (flux - flux.mean()) / (flux.std() + 1e-9)
    fps = SR / hop
    # tempo by autocorrelation of onset strength (60-180 BPM)
    ac = np.correlate(flux, flux, mode="full")[len(flux) - 1:]
    lags = np.arange(len(ac)); bpm_l = (60 * fps / np.maximum(lags, 1))
    ok = (bpm_l >= 70) & (bpm_l <= 170)
    lag = lags[ok][np.argmax(ac[ok])]; bpm = 60 * fps / lag
    # beat phase: best offset of a comb over onset strength
    period = lag; best = max(range(int(period)), key=lambda o: flux[o::int(period)].sum())
    beats = [round((best + k * period) / fps, 3) for k in range(int((len(flux) - best) / period) + 1)]
    # energy per second (RMS dB)
    sec = int(dur); rms = [float(20 * np.log10(np.sqrt(np.mean(x[i * SR:(i + 1) * SR] ** 2)) + 1e-9)) for i in range(sec)]
    return {"file": path, "duration": round(dur, 2), "bpm": round(float(bpm), 1), "beats": beats, "rms_db": [round(r, 1) for r in rms]}
if __name__ == "__main__":
    p = profile(sys.argv[1])
    if "--json" in sys.argv: json.dump(p, open(sys.argv[sys.argv.index("--json") + 1], "w"))
    lo, hi = min(p["rms_db"]), max(p["rms_db"])
    chars = " .:-=+*#%@"
    strip = "".join(chars[min(9, int((r - lo) / (hi - lo + 1e-9) * 9.99))] for r in p["rms_db"])
    print(f'{p["file"].split("/")[-1]:24s} {p["duration"]:6.1f}s {p["bpm"]:5.1f}bpm  dB {lo:.0f}..{hi:.0f}')
    for i in range(0, len(strip), 60): print(f"   {i:3d}s |{strip[i:i+60]}|")
