"""Build-time helper: a look at what is in Drive, for the Workshop (never part of the daily Engine).

    python -m engine.peek --what reference,music,memes,clips

Makes a contact sheet (grid of frames) for every reference reel, and lists the music, meme and
clip folders, into out/peek/. The workflow pushes that folder to the throwaway 'peek' branch.
"""
import argparse
import json
import os
import subprocess
import sys

from .drive import Drive, FOLDER
from .clips import contact_sheet, duration
from .settings import OUT

PEEK = OUT / "peek"


def list_folder(d, path, name):
    fid = d.folder(path, create=False) if path != "music" else d.music_folder()
    items = d.children(fid) if fid else []
    rows = [{"name": i["name"], "mime": i.get("mimeType"), "size": int(i.get("size", 0) or 0)} for i in items
            if i["mimeType"] != FOLDER]
    subs = [i["name"] for i in items if i["mimeType"] == FOLDER]
    with open(PEEK / f"{name}_list.json", "w", encoding="utf-8") as f:
        json.dump({"folder": path, "count": len(rows), "subfolders": subs, "files": sorted(rows, key=lambda r: r["name"])},
                  f, ensure_ascii=False, indent=1)
    print(f"{path}: {len(rows)} files, subfolders {subs}")
    return items


def reference(d):
    items = [i for i in list_folder(d, "reference-reels", "reference") if i.get("mimeType", "").startswith("video/")]
    os.makedirs(PEEK / "reference", exist_ok=True)
    info = []
    for it in items:
        local = str(OUT / "work" / "ref" / it["name"])
        d.download(it["id"], local)
        secs = duration(local)
        base = os.path.splitext(it["name"])[0][:60]
        sheet = str(PEEK / "reference" / f"{base}.jpg")
        png = sheet.replace(".jpg", ".png")
        try:
            contact_sheet(local, png, cols=4, rows=5, width=1080)
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", png, "-q:v", "4", sheet], check=True)
            os.remove(png)
        except Exception as e:
            print("sheet failed", it["name"], e, file=sys.stderr)
        # first frame at full size (the cover look)
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "0.5", "-i", local, "-frames:v", "1", "-q:v", "4",
                        str(PEEK / "reference" / f"{base}_cover.jpg")])
        # audio loudness, so the templates can match the samples' level
        r = subprocess.run(["ffmpeg", "-i", local, "-af", "ebur128=peak=true", "-f", "null", "-"], capture_output=True, text=True)
        lufs = next((l.strip() for l in r.stderr.splitlines() if "I:" in l and "LUFS" in l), "")
        info.append({"name": it["name"], "seconds": secs, "size_mb": round(int(it.get("size", 0) or 0) / 1e6, 1), "loudness": lufs})
        os.remove(local)
        print("sheet:", it["name"], secs, "s", lufs)
    with open(PEEK / "reference" / "info.json", "w", encoding="utf-8") as f:
        json.dump(info, f, ensure_ascii=False, indent=1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--what", default="reference,music,memes,clips")
    a = ap.parse_args()
    os.makedirs(PEEK, exist_ok=True)
    d = Drive()
    want = a.what.split(",")
    if "music" in want:
        list_folder(d, "music", "music")
    if "memes" in want:
        list_folder(d, "meme-bank", "memes")
    if "clips" in want:
        list_folder(d, "clip-library", "clips")
    if "reference" in want:
        reference(d)
    print("done:", sorted(os.listdir(PEEK)))


if __name__ == "__main__":
    main()
