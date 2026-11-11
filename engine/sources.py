"""Where pictures come from (AGENT.md 5.9). Cheapest first; an AI image is the last step, not the first.

  1. our image library in Drive   everything ever made or collected, with tags      free
  2. a frame from an official trailer or promo in the clip library                   free
  3. free photo libraries that need no credit line (public domain, Pexels, Pixabay)  free
  4. an AI image (engine/images.py)                                                  paid, capped

Only sources that allow reuse, or the film's own official material. Other people's artwork is never taken.
Every picture found is saved to the library with where it came from, so the library grows and the next reel is cheaper."""
import hashlib
import json
import os
import re
import subprocess

import requests

from .settings import ENGINE, secret

INDEX = "index.json"
UA = {"User-Agent": "reel-engine/1.0"}


def words(text):
    stop = {"a", "an", "the", "of", "on", "in", "at", "and", "with", "to", "for", "by", "from", "is", "its", "one", "old", "big", "small"}
    return {w for w in re.sub(r"[^a-z0-9]+", " ", str(text or "").lower()).split() if len(w) > 2 and w not in stop}


class Library:
    """The index of the image library: one small JSON file in Drive image-library/."""

    def __init__(self, drive):
        self.drive = drive
        self.items = []
        if drive:
            try:
                self.items = (drive.read_json("image-library", INDEX) or {}).get("images", [])
            except Exception:
                self.items = []

    def search(self, query, film=None, kind=None, min_match=0.6):
        q = words(query)
        best, score = None, 0.0
        for it in self.items:
            if kind and it.get("kind") and it["kind"] != kind:
                continue
            t = set(it.get("tags", []))
            s = len(q & t) / max(1, len(q))
            if film and it.get("film") and it["film"].lower() == str(film).lower():
                s += 0.25
            if s > score:
                best, score = it, s
        return best if best and score >= min_match else None

    def add(self, local_path, name, record):
        """Save a picture to the library and remember where it came from."""
        if not self.drive:
            return
        try:
            self.drive.upload(local_path, "image-library", name=name)
            self.items = [i for i in self.items if i.get("file") != name] + [dict(record, file=name)]
            self.drive.write_json("image-library", INDEX, {"images": self.items})
        except Exception as e:
            print("image library could not be updated:", str(e)[:160])

    def fetch(self, item, out):
        fid = self.drive.folder("image-library", create=False)
        f = self.drive.find_child(fid, item["file"]) if fid else None
        return self.drive.download(f["id"], out) if f else None


def _download(url, out):
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    if len(r.content) < 20000:
        raise RuntimeError("picture too small")
    with open(out, "wb") as f:
        f.write(r.content)
    return out


def from_pexels(query, out):
    key = secret("PEXELS_API_KEY")
    if not key:
        return None
    j = requests.get("https://api.pexels.com/v1/search", params={"query": query, "orientation": "portrait", "size": "large", "per_page": 5},
                     headers={"Authorization": key}, timeout=30).json()
    for p in j.get("photos", []):
        if p.get("height", 0) >= 1400:
            _download(p["src"].get("large2x") or p["src"]["original"], out)
            return {"source": "pexels", "licence": "Pexels licence (free to use, no credit needed)", "credit": p.get("photographer"), "url": p.get("url")}
    return None


def from_pixabay(query, out):
    key = secret("PIXABAY_API_KEY")
    if not key:
        return None
    j = requests.get("https://pixabay.com/api/", params={"key": key, "q": query, "image_type": "photo", "orientation": "vertical", "safesearch": "true", "per_page": 5, "min_height": 1400}, timeout=30).json()
    for p in j.get("hits", []):
        _download(p.get("largeImageURL"), out)
        return {"source": "pixabay", "licence": "Pixabay content licence (free to use, no credit needed)", "credit": p.get("user"), "url": p.get("pageURL")}
    return None


def from_openverse(query, out):
    """Public-domain pictures only (CC0 and public domain mark): no credit line is owed."""
    j = requests.get("https://api.openverse.org/v1/images/", params={"q": query, "license": "cc0,pdm", "aspect_ratio": "tall", "size": "large", "page_size": 8, "mature": "false"}, headers=UA, timeout=30).json()
    for p in j.get("results", []):
        if (p.get("height") or 0) >= 1200 and str(p.get("url", "")).lower().split("?")[0].endswith((".jpg", ".jpeg", ".png")):
            try:
                _download(p["url"], out)
            except Exception:
                continue
            return {"source": "openverse", "licence": f"{p.get('license', '').upper()} (public domain)", "credit": p.get("creator"), "url": p.get("foreign_landing_url")}
    return None


def from_trailer(spec, drive, out, work):
    """A still from an official trailer in Drive clip-library: {"film": ..., "at": seconds} (the Brain picks the moment from a contact sheet)."""
    if not drive or not spec:
        return None
    fid = drive.folder("clip-library", create=False)
    vids = [k for k in (drive.children(fid) if fid else []) if k.get("mimeType", "").startswith("video/")]
    film = re.sub(r"[^a-z0-9]+", " ", str(spec.get("film", "")).lower()).strip()
    hit = next((k for k in vids if film and film in re.sub(r"[^a-z0-9]+", " ", k["name"].lower())), None)
    if not hit:
        return None
    src = drive.download(hit["id"], os.path.join(work, "trailer_" + re.sub(r"[^\w.]+", "_", hit["name"])))
    r = subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(float(spec.get("at", 5))), "-i", src, "-frames:v", "1", "-q:v", "2", out], capture_output=True)
    if r.returncode != 0 or not os.path.exists(out):
        return None
    return {"source": "trailer", "licence": "official trailer frame, used inside commentary and design", "credit": hit["name"], "url": None}


def house_look(path, look=None):
    """Sourced photos get the page's look by code, so they sit beside our other pictures: deeper contrast, richer colour, portrait crop."""
    from PIL import Image, ImageEnhance
    im = Image.open(path).convert("RGB")
    w, h = im.size
    want = 2 / 3
    if w / h > want:                      # too wide: keep the middle
        nw = int(h * want)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    im = im.resize((1080, 1620), Image.LANCZOS)
    im = ImageEnhance.Contrast(im).enhance(1.12)
    im = ImageEnhance.Color(im).enhance(1.18)
    if look == "night":
        im = ImageEnhance.Brightness(im).enhance(0.82)
    im.save(path, quality=92)
    return path


def find(spec, n, reel_id, work, drive=None, library=None, film=None):
    """Try every free step for one picture. Returns {"src", "source", ...} or None (then the caller makes an AI image)."""
    query = spec.get("find") or ""
    order = spec.get("sources") or ENGINE.get("images", {}).get("ladder", ["library", "trailer", "pexels", "pixabay", "openverse"])
    out = os.path.join(work, f"found_{n:02d}.jpg")
    lib = library or Library(drive)
    for step in order:
        try:
            if step == "library" and query:
                it = lib.search(query, film=film)
                got = lib.fetch(it, out) if it else None
                if got:
                    return {"src": out, "source": "library", "from": it.get("source"), "credit": it.get("credit"), "reused": True}
            elif step == "trailer" and spec.get("trailer"):
                rec = from_trailer(spec["trailer"], drive, out, work)
            elif step in ("pexels", "pixabay", "openverse") and query:
                rec = {"pexels": from_pexels, "pixabay": from_pixabay, "openverse": from_openverse}[step](query, out)
            else:
                rec = None
            if step != "library" and rec:
                house_look(out, spec.get("look"))
                name = f"web_{re.sub(r'[^a-z0-9]+', '-', query.lower())[:40]}_{hashlib.md5((rec.get('url') or query).encode()).hexdigest()[:6]}.jpg" if step != "trailer" else f"trailer_{reel_id}_{n:02d}.jpg"
                lib.add(out, name, dict(rec, tags=sorted(words(query) | words(film)), film=film, query=query))
                return dict(rec, src=out)
        except Exception as e:
            print(f"picture source '{step}' did not answer:", str(e)[:140])
    return None
