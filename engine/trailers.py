"""Trailers, fetched by code (AGENT.md 5.9). No AI, no cost.

The route is Instagram's own business discovery: the official studio, label and star accounts post every trailer,
teaser and glimpse there, and the Engine may read public posts of business accounts through the official API from the
cloud. Each trailer is saved to Drive clip-library/ with a shot grid (one picture, every shot numbered with its start
and end second) so the planning run picks the exact moment for each line, the way the Kaithi reel was made.
Trailers that are not on Instagram (older films) come from the laptop helper (tools/clip_helper.py).

    python -m engine.trailers --film "Jailer 2"              fetch one film's trailer into the clip library
    python -m engine.trailers --wanted                       fetch every film listed in Drive status/trailers_wanted.json
    python -m engine.trailers --probe "Jailer 2" "Vikram"    test the route; nothing saved to Drive"""
import argparse
import json
import os
import re
import shutil
import subprocess

import requests
import yaml

from .settings import OUT, niche_dir
from . import status

KINDS = [("trailer", ["trailer"]), ("teaser", ["teaser"]), ("glimpse", ["glimpse"]),
         ("promo", ["promo", "sneak peek", "first look", "motion poster", "announcement"]), ("song", ["lyric", "video song", "song"])]
WORK = OUT / "trailers"


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def mentions(film, text):
    f, t = norm(film), norm(text)
    return bool(f) and (f" {f} " in f" {t} " or f.replace(" ", "") in t.replace(" ", ""))


def kind_of(text):
    t = norm(text)
    for k, words in KINDS:
        if any(w in t for w in words):
            return k
    return None


def settings():
    s = yaml.safe_load((niche_dir() / "knowledge" / "sources.yaml").read_text(encoding="utf-8")) or {}
    return s.get("trailers") or {}


def ffmpeg():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def duration(path):
    r = subprocess.run([ffmpeg(), "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return round(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)), 2) if m else None


# ---------------------------------------------------------------- official Instagram accounts
def candidates(ig, film, accounts, pages=6, report=None):
    """Video posts of the official accounts whose caption names the film and says trailer, teaser, glimpse ..."""
    found = []
    for acct in accounts:
        after, seen = None, 0
        for _ in range(pages):
            media = "media.limit(50)" + (f".after({after})" if after else "")
            try:
                j = ig.get(ig.user_id, fields=f"business_discovery.username({acct}){{username,{media}{{id,caption,media_type,media_url,permalink,timestamp}}}}")
            except Exception as e:
                if report is not None:
                    report[acct] = f"not readable: {str(e)[:90]}"
                break
            m = (j.get("business_discovery") or {}).get("media") or {}
            for p in m.get("data", []):
                seen += 1
                cap = p.get("caption") or ""
                if p.get("media_type") == "VIDEO" and mentions(film, cap) and kind_of(cap):
                    found.append({"account": acct, "id": p["id"], "kind": kind_of(cap), "url": p.get("media_url"),
                                  "link": p.get("permalink"), "when": p.get("timestamp"), "title": cap.splitlines()[0][:100]})
            after = ((m.get("paging") or {}).get("cursors") or {}).get("after")
            if not after or any(f["account"] == acct for f in found):
                break
        if report is not None and acct not in report:
            n = sum(1 for f in found if f["account"] == acct)
            report[acct] = f"ok, {seen} posts read, {n} match" + ("" if n == 0 or all(f.get("url") for f in found if f["account"] == acct) else " (no video link given)")
    return found


def download(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(path, "wb") as f:
            for chunk in r.iter_content(1 << 20):
                f.write(chunk)
    if os.path.getsize(path) < 100_000:
        raise RuntimeError("the download came back empty")
    return path


# ---------------------------------------------------------------- shot grid (no AI)
def shots(video, threshold=0.3):
    """Every shot as [start, end] seconds, from the cuts ffmpeg finds."""
    r = subprocess.run([ffmpeg(), "-i", video, "-vf", f"select='gt(scene,{threshold})',showinfo", "-an", "-f", "null", "-"],
                       capture_output=True, text=True, timeout=600)
    cuts = sorted({round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", r.stderr)})
    d = duration(video) or (cuts[-1] + 2 if cuts else 0)
    edges = [0.0] + [c for c in cuts if 0.3 < c < d - 0.3] + [d]
    return [[edges[i], edges[i + 1]] for i in range(len(edges) - 1) if edges[i + 1] - edges[i] >= 0.8]


def grid(video, out_jpg, max_tiles=40):
    """One picture: each usable shot as a numbered tile with its start and end. Black frames and title cards are left out."""
    from PIL import Image, ImageDraw, ImageFont, ImageStat
    tmp = WORK / "tiles"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    keep = []
    for i, (a, b) in enumerate(shots(video)):
        f = tmp / f"{i:03d}.jpg"
        subprocess.run([ffmpeg(), "-y", "-v", "error", "-ss", f"{(a + b) / 2:.2f}", "-i", video, "-frames:v", "1", "-vf", "scale=320:-2", str(f)],
                       capture_output=True, timeout=60)
        if not f.exists():
            continue
        im = Image.open(f).convert("L")
        dark = sum(im.histogram()[:28]) / (im.width * im.height)
        if ImageStat.Stat(im).mean[0] < 22 or dark > 0.72:       # black frame, or text on black (title card)
            continue
        keep.append({"n": len(keep) + 1, "start": round(a, 2), "end": round(b, 2), "tile": str(f)})
    if len(keep) > max_tiles:
        keep = sorted(sorted(keep, key=lambda s: -(s["end"] - s["start"]))[:max_tiles], key=lambda s: s["start"])
        for k, s in enumerate(keep, 1):
            s["n"] = k
    if not keep:
        raise RuntimeError("no usable shots found")
    cols, tw = 5, 320
    th = Image.open(keep[0]["tile"]).height
    rows = (len(keep) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 6) + 6, rows * (th + 6) + 6), (12, 12, 20))
    fp = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(fp, 22) if os.path.exists(fp) else ImageFont.load_default()
    dr = ImageDraw.Draw(sheet)
    for k, s in enumerate(keep):
        x, y = 6 + (k % cols) * (tw + 6), 6 + (k // cols) * (th + 6)
        sheet.paste(Image.open(s["tile"]).resize((tw, th)), (x, y))
        label = f"#{s['n']}  {s['start']:.1f}-{s['end']:.1f}s"
        dr.rectangle([x, y, x + 12 * len(label) + 8, y + 28], fill=(0, 0, 0))
        dr.text((x + 5, y + 3), label, fill=(255, 214, 64), font=font)
    os.makedirs(os.path.dirname(out_jpg), exist_ok=True)
    sheet.save(out_jpg, quality=86)
    return [{k: s[k] for k in ("n", "start", "end")} for s in keep]


# ---------------------------------------------------------------- the library
def index(drive):
    try:
        return drive.read_json("clip-library", "index.json") or {"trailers": []}
    except Exception:
        return {"trailers": []}


def have(film, idx):
    return [t for t in idx["trailers"] if norm(t["film"]) == norm(film)]


def fetch(drive, ig, film, want=("trailer", "teaser", "glimpse", "promo"), force=False, report=None):
    """Find, download and file one trailer for a film. Returns the library entry or raises with a plain reason."""
    idx = index(drive) if drive is not None else {"trailers": []}
    if have(film, idx) and not force:
        return have(film, idx)[0]
    order = {k: i for i, k in enumerate(want)}
    cands = [c for c in candidates(ig, film, settings().get("instagram_accounts", []), report=report) if c["kind"] in order and c.get("url")]
    if not cands:
        raise RuntimeError(f"no official trailer for {film} on the studio accounts (add it with the laptop helper)")
    cands.sort(key=lambda c: (order[c["kind"]], -(int(re.sub(r"\D", "", c.get("when") or "0")[:14] or 0))))
    errors = []
    for c in cands[:3]:
        safe = re.sub(r'[\\/:*?"<>|]+', " ", f"{film} - {c['kind']} [{c['id']}]").strip()
        local = str(WORK / f"{safe}.mp4")
        try:
            download(c["url"], local)
            meta = grid(local, str(WORK / "sheets" / f"{safe}.jpg"))
        except Exception as e:
            errors.append(f"{c['account']}: {str(e)[:120]}")
            continue
        entry = {"film": film, "kind": c["kind"], "file": f"{safe}.mp4", "sheet": f"{safe}.jpg", "duration": duration(local),
                 "shots": meta, "source": "instagram", "account": c["account"], "link": c.get("link"), "title": c.get("title"),
                 "fetched": status.stamp()}
        if drive is not None:
            drive.upload(local, "clip-library", name=entry["file"])
            drive.upload(str(WORK / "sheets" / entry["sheet"]), "clip-library/sheets", name=entry["sheet"])
            idx = index(drive)
            idx["trailers"] = [t for t in idx["trailers"] if t["file"] != entry["file"]] + [entry]
            drive.write_json("clip-library", "index.json", idx)
        return entry
    raise RuntimeError("; ".join(errors) or "download failed")


def wanted(drive):
    try:
        return (drive.read_json("status", "trailers_wanted.json") or {}).get("films", [])
    except Exception:
        return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", action="append", default=[])
    ap.add_argument("--wanted", action="store_true")
    ap.add_argument("--probe", nargs="*")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    from .instagram import Instagram
    ig = Instagram()
    ig.me()
    if a.probe is not None:
        out = {}
        for film in a.probe:
            rep = {}
            try:
                e = fetch(None, ig, film, report=rep, force=True)
                rep["result"] = f"OK: {e['account']} / {e['kind']} / {e['duration']} s / {len(e['shots'])} shots"
            except Exception as ex:
                rep["result"] = f"FAILED: {ex}"
            out[film] = rep
            print(film, json.dumps(rep, indent=1, ensure_ascii=False))
        os.makedirs(OUT / "peek" / "trailers", exist_ok=True)
        (OUT / "peek" / "trailers" / "probe.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
        if (WORK / "sheets").exists():
            shutil.copytree(WORK / "sheets", OUT / "peek" / "trailers" / "sheets", dirs_exist_ok=True)
        return
    from .drive import Drive
    drive = Drive()
    films = a.film + (wanted(drive) if a.wanted else [])
    done, failed = [], {}
    for film in dict.fromkeys(films):
        try:
            e = fetch(drive, ig, film, force=a.force)
            done.append(f"{film}: {e['kind']} from {e['account']}")
        except Exception as ex:
            failed[film] = str(ex)[:200]
    status.write(drive, "trailers.json", {"fetched": done, "failed": failed})
    print(json.dumps({"fetched": done, "failed": failed}, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
