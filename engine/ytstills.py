"""Frames from YouTube, automatically (AGENT.md 5.11 step 5): free, from the cloud, no key.

    python -m engine.ytstills "Joker" "F1"      these films
    python -m engine.ytstills --wanted          the films in Drive status/trailers_wanted.json (the trailer job runs this)

YouTube refuses video downloads to cloud computers, but every video's 4 frames (its thumbnails) are free. For a film this
finds its official uploads (trailer, teaser, songs, promos) with a plain search, keeps those from the official channels
in sources.yaml (youtube_official) whose title names the film, saves the frames with a numbered grid to Drive
clip-library/stills/<film>/ and lists them in the clip index. A plan uses one as
{"src": "engine/.cache/stills/<film>/<id>_<frame>.jpg", "fetch": {"youtube": "<id>", "frame": "<frame>"}}."""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys

from .settings import ENGINE, OUT, niche_dir
from . import status

CFG = {"queries": ["{film} {year} official trailer", "{film} teaser", "{film} video song", "{film} sneak peek", "{film} promo"],
       "per_query": 8, "max_videos": 10, "frames": ["maxresdefault", "maxres1", "maxres2", "maxres3"], **(ENGINE.get("yt_stills") or {})}


def official_names():
    import yaml
    try:
        y = yaml.safe_load((niche_dir() / "knowledge" / "sources.yaml").read_text(encoding="utf-8")) or {}
    except Exception:
        y = {}
    return [str(n).lower() for n in (y.get("youtube_official") or [])]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def search(q, n):
    r = subprocess.run([sys.executable, "-m", "yt_dlp", "--flat-playlist", "--dump-single-json", "--no-warnings", f"ytsearch{n}:{q}"],
                       capture_output=True, text=True, timeout=90)
    return (json.loads(r.stdout or "{}") or {}).get("entries") or []


def find(film, year=""):
    """The film's official uploads: title names the film, channel is official, no reactions or fan edits."""
    off, f, out, seen = official_names(), norm(film), [], set()
    bad = ("reaction", "review", "explained", "fan made", "spoof", "edit", "status")
    for q in CFG["queries"]:
        try:
            es = search(q.format(film=film, year=year).strip(), int(CFG["per_query"]))
        except Exception as e:
            print(f"{film}: search '{q}' failed ({str(e)[:80]})", file=sys.stderr)
            continue
        for e in es:
            vid, t, ch = e.get("id"), norm(e.get("title")), norm(e.get("channel") or e.get("uploader"))
            if not vid or vid in seen or f not in t or any(b in t for b in bad):
                continue
            if off and not any(o in ch or o.replace(" ", "") in ch.replace(" ", "") for o in off):
                continue
            seen.add(vid)
            out.append({"id": vid, "title": e.get("title", ""), "channel": e.get("channel") or e.get("uploader") or ""})
        if len(out) >= int(CFG["max_videos"]):
            break
    return out[:int(CFG["max_videos"])]


def stills(drive, film, year=""):
    from .trailers import WORK, _safe, download_image, index, stills_grid
    vids = find(film, year)
    if not vids:
        raise RuntimeError(f"no official YouTube uploads found for {film}")
    folder = WORK / "stills" / (_safe(film) + " - youtube")
    shutil.rmtree(folder, ignore_errors=True)
    items = []
    for v in vids:
        for fr in CFG["frames"]:
            name = f"{len(items) + 1:02d}.jpg"
            try:
                download_image(f"https://i.ytimg.com/vi/{v['id']}/{fr}.jpg", str(folder / name))
            except Exception:
                continue                                  # older videos have no maxres frames
            items.append({"n": len(items) + 1, "file": name, "account": v["channel"], "post": f"https://www.youtube.com/watch?v={v['id']}",
                          "date": "", "kind": "youtube frame", "caption": v["title"][:90], "youtube": v["id"], "frame": fr})
    if not items:
        raise RuntimeError(f"no frames for {film}")
    sheet = f"{_safe(film)} - youtube.jpg"
    stills_grid(items, str(folder), str(WORK / "sheets" / sheet))
    entry = {"film": film, "kind": "stills", "source": "youtube", "folder": f"clip-library/stills/{_safe(film)} - youtube", "sheet": sheet,
             "stills": items, "fetched": status.stamp(),
             "use": 'a frame as {"src": "engine/.cache/stills/<film>/<youtube>_<frame>.jpg", "fetch": {"youtube": <youtube>, "frame": <frame>}}'}
    if drive is not None:
        for it in items:
            drive.upload(str(folder / it["file"]), entry["folder"], name=it["file"])
        drive.upload(str(WORK / "sheets" / sheet), "clip-library/sheets", name=sheet)
        idx = index(drive)
        idx["stills"] = [x for x in idx.get("stills", []) if not (norm(x["film"]) == norm(film) and x.get("source") == "youtube")] + [entry]
        drive.write_json("clip-library", "index.json", idx)
    try:                                                  # a quick look on the 'peek' branch, like the trailer grids
        os.makedirs(OUT / "peek" / "trailers" / "sheets", exist_ok=True)
        shutil.copy(str(WORK / "sheets" / sheet), str(OUT / "peek" / "trailers" / "sheets" / sheet))
        (OUT / "peek" / "trailers" / "sheets" / (sheet[:-4] + ".json")).write_text(json.dumps(entry, indent=1, ensure_ascii=False))
    except Exception:
        pass
    return entry


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("films", nargs="*")
    ap.add_argument("--wanted", action="store_true")
    ap.add_argument("--no-drive", action="store_true", help="find and grid only (testing)")
    a = ap.parse_args()
    drive = None
    if not a.no_drive:
        from .drive import Drive
        drive = Drive()
    films = [(f, "") for f in a.films]
    if a.wanted and drive:
        from .trailers import wanted
        films += [(f.get("film"), f.get("year", "")) if isinstance(f, dict) else (str(f), "") for f in wanted(drive)]
    done = []
    for film, year in films[:int(CFG.get("max_films_per_run", 12))]:
        try:
            e = stills(drive, film, year)
            done.append(f"{film}: {len(e['stills'])} frames")
        except Exception as ex:
            done.append(f"{film}: {str(ex)[:100]}")
    print("YouTube frames: " + ("; ".join(done) or "nothing wanted"))


if __name__ == "__main__":
    main()
