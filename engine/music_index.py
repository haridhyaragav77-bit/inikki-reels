"""Music index (AGENT.md 5.4): every track in the Drive music folder is listened to once by code and tagged
with its length, tempo, energy, brightness, how drum-led it is, whether it builds, and a score for each mood.
Reels then pick tracks by mood from the index instead of by file name.

    python -m engine.music_index            tag new tracks (and anything dropped into music/inbox), write music/index.json
    python -m engine.music_index --all      tag every track again

Trending songs (Harish, 22 Nov; AGENT.md 5.4): files the laptop run names "song - <key> - <title> [<id>]" are also listed in
data/music/trending.json (key, title, mood, where the hook is, Drive id) for config `music.trending.days`, so plans can use them.

Free: plain signal maths on the runner, no AI. A track already in the index is skipped unless it changed."""
import argparse
import json
import os
import re
import subprocess
import sys
import time

import numpy as np

from .drive import Drive
from .settings import ENGINE, OUT

SR, HOP, WIN = 11025, 512, 1024
INDEX = "index.json"
MOODS = ["tension_pulse", "upbeat_percussive", "emotional_build", "suspense_ticks", "stinger", "soft_warm", "confident_mid"]


def features(path):
    """Signal features of one track (first 4 minutes)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-t", "240", "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    x = np.frombuffer(raw, np.float32)
    if len(x) < SR * 4:
        return None
    n = len(x) // HOP
    rms = np.sqrt((x[: n * HOP].reshape(n, HOP) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    frames = np.lib.stride_tricks.sliding_window_view(x, WIN)[::HOP] * np.hanning(WIN)
    S = np.abs(np.fft.rfft(frames, axis=1)).astype(np.float32)
    freqs = np.fft.rfftfreq(WIN, 1 / SR)
    centroid = float(np.median((S * freqs).sum(1) / (S.sum(1) + 1e-9)))
    flux = np.maximum(0, np.diff(np.log1p(S), axis=0)).sum(1)
    f = np.maximum(flux - np.convolve(flux, np.ones(16) / 16, "same"), 0)
    f = f - f.mean()
    ac = np.correlate(f, f, "full")[len(f) - 1:]
    fps = SR / HOP
    lags = np.arange(len(ac))
    bpm_at = 60 * fps / np.maximum(lags, 1)
    ok = (bpm_at >= 60) & (bpm_at <= 180)
    weight = np.exp(-0.5 * (np.log2(bpm_at / 110) / 0.9) ** 2)            # prefer ordinary dance and walking tempos
    k = int(np.argmax(np.where(ok, ac * weight, -np.inf)))
    third = max(1, n // 3)
    loud = db[db > np.percentile(db, 20)]
    win = max(1, int(8 * fps))                                          # the hook: the loudest 8 s in the first 70% of the track
    roll = np.convolve(db, np.ones(win) / win, "valid")
    span = max(1, int(len(roll) * .7))
    hook = round(float(np.argmax(roll[:span]) / fps), 1) if len(roll) else 0.0
    return {"bpm": round(float(60 * fps / k), 1), "pulse": round(float(ac[k] / (ac[0] + 1e-9)), 3),
            "energy_db": round(float(loud.mean()), 2), "dynamics_db": round(float(np.percentile(db, 95) - np.percentile(db, 30)), 2),
            "brightness_hz": round(centroid, 0), "drums": round(float(np.percentile(flux, 95) / (np.median(flux) + 1e-9)), 3),
            "build_db": round(float(db[-third:].mean() - db[:third].mean()), 2), "hook_s": hook}


def _pct(vals):
    """Rank of each value in the library, 0..1 (so moods compare tracks with each other, not with fixed numbers)."""
    order = np.argsort(np.argsort(vals))
    return order / max(1, len(vals) - 1)


def score_moods(items):
    """Give every track a 0..1 score for each mood, from its features compared with the rest of the library."""
    tagged = [it for it in items if it.get("f")]
    if not tagged:
        return
    col = lambda k: np.array([it["f"][k] for it in tagged], dtype=float)
    E, P, B, D, Y = _pct(col("energy_db")), _pct(col("pulse")), _pct(col("brightness_hz")), _pct(col("drums")), _pct(col("dynamics_db"))
    bpm, build = col("bpm"), col("build_db")
    band = lambda v, lo, hi: np.clip(1 - np.maximum(lo - v, v - hi) / 25, 0, 1)
    mid = lambda p: 1 - np.abs(p - 0.5) * 2
    rise = 1 / (1 + np.exp(-(build - 2) / 2))
    s = {"tension_pulse": 0.35 * P + 0.25 * (1 - B) + 0.2 * mid(E) + 0.2 * band(bpm, 85, 130),
         "upbeat_percussive": 0.35 * D + 0.3 * E + 0.35 * band(bpm, 105, 175),
         "emotional_build": 0.35 * (1 - D) + 0.3 * rise + 0.15 * (1 - E) + 0.2 * band(bpm, 55, 100),
         "suspense_ticks": 0.35 * (1 - E) + 0.3 * P + 0.35 * (1 - B),
         "stinger": 0.4 * Y + 0.35 * E + 0.25 * D,
         "soft_warm": 0.4 * (1 - E) + 0.35 * (1 - D) + 0.25 * mid(B),
         "confident_mid": 0.35 * E + 0.3 * band(bpm, 85, 120) + 0.35 * mid(D)}
    words, avoid = ENGINE.get("music", {}).get("mood_words", {}), ENGINE.get("music", {}).get("avoid_words", {})
    has = lambda name, ws: any(w in name.split() or (len(w) > 5 and w in name) for w in ws)
    for i, it in enumerate(tagged):
        name = re.sub(r"masstamilan\s*\w*", " ", re.sub(r"[^a-z0-9]+", " ", it["name"].lower()))
        moods = {}
        for m in MOODS:
            hint = (0.15 if has(name, words.get(m, [])) else 0.0) - (0.25 if has(name, avoid.get(m, [])) else 0.0)
            moods[m] = round(float(min(1.0, max(0.0, s[m][i] + hint))), 3)
        it["moods"] = moods
        it["best"] = sorted(moods, key=moods.get, reverse=True)[:2]


SONG = re.compile(r"^song - (song_[a-z0-9_]+) - (.+?)(?: \[[^\]]+\])?\.\w+$", re.I)


def trending(tracks, keep_days=45):
    """data/music/trending.json: the laptop run's songs, newest first, with the key a plan names and the hook's second.
    Kept on the list for keep_days after they arrive; older ones stay usable (still listed, fresh: false) for 60 more days."""
    from .settings import ROOT
    p = ROOT / "data" / "music" / "trending.json"
    try:
        old = {t["key"]: t for t in json.loads(p.read_text(encoding="utf-8")).get("tracks", [])}
    except Exception:
        old = {}
    uses = {}
    for f in (ROOT / "plans").glob("20??-??-??/*.json"):
        try:
            for sec in (json.loads(f.read_text(encoding="utf-8")).get("music") or {}).get("sections", []):
                uses[sec.get("track")] = uses.get(sec.get("track"), 0) + 1
        except Exception:
            continue
    now, out = time.time(), []
    for t in tracks:
        m = SONG.match(t.get("name", ""))
        if not m or t.get("retired"):
            continue
        key, title = m.group(1).lower(), m.group(2).strip()
        prev = old.get(key, {})
        added = prev.get("added") or time.strftime("%Y-%m-%d", time.gmtime())
        age = (now - time.mktime(time.strptime(added, "%Y-%m-%d"))) / 86400
        if age > keep_days + 60:
            continue
        film = re.search(r"\(([^)]+)\)\s*$", title)
        out.append({"key": key, "title": title, "film": film.group(1) if film else prev.get("film", ""), "drive_id": t["id"], "seconds": t.get("seconds"),
                    "best": t.get("best") or [], "hook_at": (t.get("f") or {}).get("hook_s", 0.0), "added": added,
                    "fresh": age <= keep_days, "uses": uses.get(key, 0)})
    out.sort(key=lambda x: x["added"], reverse=True)          # newest first, then the fresh ones ahead of the older ones
    out.sort(key=lambda x: not x["fresh"])
    p.parent.mkdir(parents=True, exist_ok=True)
    body = {"note": "Trending songs from the laptop run (AGENT.md 5.4). Music-only reels; organic posts only, never boosted.", "tracks": out}
    try:
        same = {k: v for k, v in json.loads(p.read_text(encoding="utf-8")).items() if k != "updated"} == body
    except Exception:
        same = False
    if not same:
        p.write_text(json.dumps({"updated": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), **body}, ensure_ascii=False, indent=1) + "\n",
                     encoding="utf-8")
    return out


def load(drive, folder_id):
    try:
        f = drive.find_child(folder_id, INDEX)
        return json.loads(drive.read_bytes(f["id"]).decode("utf-8")) if f else {"tracks": []}
    except Exception:
        return {"tracks": []}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--limit", type=int, default=0, help="tag at most this many new tracks (for a quick test)")
    a = ap.parse_args()
    d = Drive()
    mid = d.music_folder()
    if not mid:
        print("No music folder found in Drive.")
        return
    idx = load(d, mid)
    known = {t["id"]: t for t in idx.get("tracks", [])}
    inbox = d.find_child(mid, "inbox", "application/vnd.google-apps.folder")
    files = [(f, None) for f in d.children(mid) if f.get("mimeType", "").startswith("audio/")]
    if inbox:
        files += [(f, inbox["id"]) for f in d.children(inbox["id"]) if f.get("mimeType", "").startswith("audio/")]
    work = OUT / "work" / "music"
    os.makedirs(work, exist_ok=True)
    done, failed, t0 = 0, [], time.time()
    for f, from_inbox in files:
        old = known.get(f["id"])
        if old and old.get("f") and old.get("modified") == f.get("modifiedTime") and not a.all and not from_inbox:
            continue
        if a.limit and done >= a.limit:
            break
        local = str(work / "track")
        try:
            d.download(f["id"], local)
            feat = features(local)
            secs = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", local],
                                        capture_output=True, text=True).stdout.strip() or 0)
        except Exception as e:
            failed.append(f["name"])
            print("could not tag", f["name"], str(e)[:120], file=sys.stderr)
            continue
        entry = dict(old or {}, id=f["id"], name=f["name"], modified=f.get("modifiedTime"), seconds=round(secs, 1), f=feat)
        entry.setdefault("uses", [])
        entry.setdefault("retired", False)
        known[f["id"]] = entry
        if from_inbox:                                   # tagged: move it from the inbox into the music folder
            d.svc.files().update(fileId=f["id"], addParents=mid, removeParents=from_inbox, fields="id", supportsAllDrives=True).execute(num_retries=3)
        done += 1
        if done % 50 == 0:
            print(f"tagged {done} tracks ({time.time() - t0:.0f} s)", flush=True)
    live = {f["id"] for f, _ in files}
    tracks = [t for t in known.values() if t["id"] in live]       # tracks deleted from Drive leave the index
    score_moods(tracks)
    idx = {"updated": time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime()), "tracks": sorted(tracks, key=lambda t: t["name"].lower())}
    f = d.find_child(mid, INDEX)
    from googleapiclient.http import MediaInMemoryUpload
    media = MediaInMemoryUpload(json.dumps(idx, ensure_ascii=False, indent=1).encode("utf-8"), mimetype="application/json")
    if f:
        d.svc.files().update(fileId=f["id"], media_body=media, supportsAllDrives=True).execute(num_retries=3)
    else:
        d.svc.files().create(body={"name": INDEX, "parents": [mid]}, media_body=media, fields="id", supportsAllDrives=True).execute(num_retries=3)
    counts = {m: sum(1 for t in tracks if m in (t.get("best") or [])) for m in MOODS}
    try:
        songs = trending(tracks, int(((ENGINE.get("music") or {}).get("trending") or {}).get("days", 45)))
        print(f"Trending songs: {sum(1 for x in songs if x['fresh'])} on the list (data/music/trending.json)")
    except Exception as e:
        print("trending list not written:", str(e)[:160], file=sys.stderr)
    print(f"Music index: {len(tracks)} tracks, {done} tagged now, {len(failed)} could not be read. Tracks per mood (top two moods each): {counts}")
    os.makedirs(OUT / "peek" / "music", exist_ok=True)
    with open(OUT / "peek" / "music" / "summary.json", "w", encoding="utf-8") as fh:
        json.dump({"tracks": len(tracks), "tagged_now": done, "failed": failed[:20], "per_mood": counts,
                   "top": {m: [t["name"] for t in sorted(tracks, key=lambda t: -(t.get("moods") or {}).get(m, 0))[:8]] for m in MOODS}}, fh, ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
