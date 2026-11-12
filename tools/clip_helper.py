#!/usr/bin/env python3
"""Clip helper for your laptop: gets official trailers and promos, ready for the clip library.

Why: YouTube blocks downloads from GitHub's cloud computers, so the Engine cannot fetch trailers itself.
From your own laptop it works. The Engine cuts its 2-4 second moments from whatever is in Drive "clip-library".

    python tools/clip_helper.py "Kaithi official trailer"            one film (the search words you would type on YouTube)
    python tools/clip_helper.py "Kaithi" "Vikram" "Jigarthanda"      several, one after another
    python tools/clip_helper.py https://www.youtube.com/watch?v=...  one exact video
    python tools/clip_helper.py --film-bank                          every film in the film bank (one time, about 30 films)

It saves the files into a folder called  clips_to_upload  next to this script.
Then drag those files into Drive > iNiKKi Reels > clip-library. That is all.
Use official channels only (the film's studio or music label): the tool shows the channel name so you can check.
"""
import json
import os
import re
import subprocess
import sys

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "clips_to_upload")


def ytdlp():
    try:
        import yt_dlp  # noqa: F401
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "--upgrade", "yt-dlp"])
    return [sys.executable, "-m", "yt_dlp"]


def fetch(what):
    target = what if what.startswith("http") else f"ytsearch1:{what} official trailer" if "trailer" not in what.lower() else f"ytsearch1:{what}"
    meta = subprocess.run(ytdlp() + ["--dump-single-json", "--no-playlist", "--skip-download", "--no-warnings", target], capture_output=True, text=True)
    if meta.returncode != 0:
        print(f"  Could not find '{what}': {(meta.stderr or '').strip().splitlines()[-1][:160] if meta.stderr.strip() else 'no result'}")
        return False
    j = json.loads(meta.stdout)
    j = j["entries"][0] if j.get("entries") else j
    film = what if not what.startswith("http") else j.get("title", "clip")
    film = re.sub(r"(?i)\b(official|trailer|teaser|promo)\b", "", film).strip(" -_") or "clip"
    name = re.sub(r'[\\/:*?"<>|]+', " ", f"{film} - {j.get('title', '')[:60]} [{j.get('id')}]").strip()
    print(f"  Found: {j.get('title')}  |  channel: {j.get('channel') or j.get('uploader')}  |  {int(j.get('duration') or 0)} s")
    os.makedirs(OUT, exist_ok=True)
    r = subprocess.run(ytdlp() + ["--no-playlist", "--no-warnings", "-f", "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[height<=720]",
                                  "--merge-output-format", "mp4", "-o", os.path.join(OUT, name + ".%(ext)s"), j.get("webpage_url") or target])
    return r.returncode == 0


def film_bank():
    """Every film in the film bank (niches/tamil-cinema/knowledge/film_bank.json), as 'Film year official trailer'."""
    p = os.path.join(os.path.dirname(OUT), "..", "niches", "tamil-cinema", "knowledge", "film_bank.json")
    with open(p, encoding="utf-8") as f:
        films = json.load(f).get("films", [])
    return [f"{x['film']} {x.get('year', '')} official trailer".replace("  ", " ") for x in films]


def main():
    wanted = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--film-bank" in sys.argv:
        wanted += film_bank()
    if not wanted:
        print(__doc__)
        return
    ok = 0
    for w in wanted:
        print(f"\n{w}")
        ok += bool(fetch(w))
    print(f"\nDone: {ok} of {len(wanted)} saved in  {OUT}")
    print("Now drag those files into Drive > iNiKKi Reels > clip-library.")


if __name__ == "__main__":
    main()
