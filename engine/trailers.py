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


SUFFIXES = ("", "movie", "film", "trailer", "teaser", "glimpse", "official", "thetrailer", "officialtrailer")


def mentions(film, text):
    """The film's name as words, or as one hashtag like #Jailer2 or #96Movie (never inside another word, like 1996)."""
    f, t = norm(film), norm(text)
    if not f:
        return False
    if f" {f} " in f" {t} ":
        return True
    fs = f.replace(" ", "")
    return any(tok.startswith(fs) and tok[len(fs):] in SUFFIXES for tok in t.split())


def best_film(text, films):
    """The longest film name the text mentions, so 'Vikram Vedha trailer' is Vikram Vedha, not Vikram."""
    hits = [f for f in films if mentions(f, text)]
    return max(hits, key=lambda f: len(norm(f))) if hits else None


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
_POSTS = {}
OTHERS = []          # every film name we know, so a caption about a longer title is not taken for a shorter one
CACHE = {"drive": None, "data": None}
CACHE_HOURS = 6


def _cache():
    """Posts already read in the last 6 hours (Drive status/ig_posts.json), so repeat runs stay inside Instagram's limit
    of about 200 calls an hour for an app this size."""
    if CACHE["data"] is None:
        CACHE["data"] = {}
        if CACHE["drive"] is not None:
            try:
                CACHE["data"] = CACHE["drive"].read_json("status", "ig_posts.json") or {}
            except Exception:
                pass
    return CACHE["data"]


def save_cache():
    if CACHE["drive"] is not None and CACHE["data"]:
        try:
            CACHE["drive"].write_json("status", "ig_posts.json", CACHE["data"])
        except Exception:
            pass


class OutOfCalls(Exception):
    pass


STOPPED = {}


def limited(e):
    """Meta is refusing for now (hourly limit or a block): the whole run stops at once, it never tries the next account."""
    if any(w in str(e).lower() for w in ("api access blocked", "request limit", "too many calls", "(#4)", "(#17)", "(#32)", "(#613)")):
        STOPPED.setdefault("why", f"Instagram stopped the search: {str(e)[:160]}")
        return True
    return False


def budget():
    return int(settings().get("max_calls_per_run", 60))


def page(ig, acct, after=None):
    """One page (50 posts) of an official account. Stops the run before it nears Instagram's hourly limit."""
    if STOPPED:
        raise OutOfCalls(STOPPED["why"])
    if type(ig).calls >= budget():
        raise OutOfCalls(f"stopped at {type(ig).calls} Instagram calls (the per-run budget)")
    if type(ig).usage >= int(settings().get("max_usage_percent", 50)):
        raise OutOfCalls(f"stopped: Meta says {type(ig).usage}% of the hourly allowance is used; the rest is kept for posting")
    media = "media.limit(25)" + (f".after({after})" if after else "")
    j = ig.get(ig.user_id, fields=f"business_discovery.username({acct}){{username,{media}{{id,caption,media_type,media_url,permalink,timestamp}}}}")
    m = (j.get("business_discovery") or {}).get("media") or {}
    m["after"] = ((m.get("paging") or {}).get("cursors") or {}).get("after")
    return m


BAD_HOURS = 72


def posts(ig, acct, pages=2):
    """An account's recent posts (up to 50), read once per run and shared by every film."""
    c = _cache().get(acct)
    if acct not in _POSTS and c and status.now().timestamp() - c.get("t", 0) < (BAD_HOURS if c.get("bad") else CACHE_HOURS) * 3600:
        if c.get("bad"):
            raise RuntimeError(f"skipped: {c['bad']}")
        _POSTS[acct] = c["posts"]
    if acct not in _POSTS:
        out, after = [], None
        for _ in range(pages):
            m = page(ig, acct, after)
            out += m.get("data", [])
            after = m.get("after")
            if not after:
                break
        _POSTS[acct] = out
        _cache()[acct] = {"t": status.now().timestamp(), "posts": out}
    return _POSTS[acct]


def candidates(ig, film, accounts, report=None, enough=("trailer",)):
    """Video posts of the official accounts whose caption names the film and says trailer, teaser, glimpse ...
    The search stops at the first account that gives a real trailer with its video link (kinds in `enough`)."""
    found = []
    for acct in accounts:
        if any(f["kind"] in enough and f.get("url") for f in found):
            break
        try:
            ps = posts(ig, acct)
        except OutOfCalls:
            raise
        except Exception as e:
            if limited(e):
                raise OutOfCalls(STOPPED["why"])     # stop at once, never hammer
            _POSTS[acct] = []
            if not str(e).startswith("skipped"):
                _cache()[acct] = {"t": status.now().timestamp(), "posts": [], "bad": str(e)[:120]}
            if report is not None:
                report[acct] = f"not readable: {str(e)[:90]}"
            continue
        n = 0
        for p in ps:
            cap = p.get("caption") or ""
            if p.get("media_type") == "VIDEO" and mentions(film, cap) and kind_of(cap) and norm(best_film(cap, OTHERS + [film])) == norm(film):
                n += 1
                found.append({"account": acct, "id": p["id"], "kind": kind_of(cap), "url": p.get("media_url"),
                              "link": p.get("permalink"), "when": p.get("timestamp"), "title": cap.splitlines()[0][:100]})
        if report is not None and n:
            report[acct] = f"{n} match in {len(ps)} posts" + ("" if all(f.get("url") for f in found if f["account"] == acct) else " (no video link given)")
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
        if drive is None:
            return {"film": film, "kind": c["kind"], "duration": duration(local), "shots": meta, "account": c["account"]}
        return file_entry(drive, film, c["kind"], local, meta, "instagram", c["account"], c.get("link"), c.get("title"))
    raise RuntimeError("; ".join(errors) or "download failed")


def file_entry(drive, film, kind, local, meta, source, account, link=None, title=None, upload_video=True):
    entry = {"film": film, "kind": kind, "file": os.path.basename(local), "sheet": os.path.basename(local)[:-4] + ".jpg",
             "duration": duration(local), "shots": meta, "source": source, "account": account, "link": link, "title": title,
             "fetched": status.stamp()}
    if upload_video:
        drive.upload(local, "clip-library", name=entry["file"])
    drive.upload(str(WORK / "sheets" / entry["sheet"]), "clip-library/sheets", name=entry["sheet"])
    idx = index(drive)
    idx["trailers"] = [x for x in idx["trailers"] if x["file"] != entry["file"]] + [entry]
    drive.write_json("clip-library", "index.json", idx)
    return entry


def film_from_name(name, known=()):
    """'Vikram Kamal Haasan - Vikram Official Trailer [id].mp4' -> 'Vikram' (a film-bank title when one is named)."""
    hit = best_film(re.sub(r"\[.*?\]", " ", name), list(known))
    if hit:
        return hit
    base = re.sub(r"\.\w+$", "", name)
    base = base.split(" - ")[0]
    base = re.sub(r"\[.*?\]|\(.*?\)", " ", base)
    base = re.sub(r"(?i)\b(official|trailer|teaser|glimpse|promo|hd|4k|tamil|full|video)\b", " ", base)
    return re.sub(r"\s+", " ", base).strip(" -_") or name


def adopt(drive):
    """Trailers put in clip-library by hand or by the laptop helper: give each a shot grid and an index entry."""
    idx = index(drive)
    known = {x["file"] for x in idx["trailers"]}
    fid = drive.folder("clip-library", create=False)
    vids = [k for k in (drive.children(fid) if fid else []) if k.get("mimeType", "").startswith("video/") and k["name"] not in known]
    done = []
    for k in vids:
        local = str(WORK / k["name"])
        try:
            drive.download(k["id"], local)
            meta = grid(local, str(WORK / "sheets" / (k["name"][:-4] + ".jpg")))
            file_entry(drive, film_from_name(k["name"], films_we_cover(drive)), kind_of(k["name"]) or "trailer", local, meta, "clip-library", "added by hand",
                       upload_video=False)
            done.append(k["name"])
        except Exception as e:
            print("could not file", k["name"], str(e)[:120])
    return done


def films_we_cover(drive):
    bank = json.loads((niche_dir() / "knowledge" / "film_bank.json").read_text(encoding="utf-8")).get("films", [])
    return list(dict.fromkeys([f["film"] for f in bank] + wanted(drive)))


def crawl(drive, ig):
    """Works back through each official account's history, one page at a time and inside the call budget, filing the
    trailers of the films we cover (film bank and wanted list). Where it stopped is kept in Drive status/ig_crawl.json."""
    state = drive.read_json("status", "ig_crawl.json") or {}
    films = films_we_cover(drive)
    idx = index(drive)
    have_films = {norm(x["film"]) for x in idx["trailers"]}
    filed, pages = [], 0
    accounts = [a for a in settings().get("instagram_accounts", []) if not (state.get(a) or {}).get("done")]
    try:
        while accounts:
            for acct in list(accounts):
                st = state.setdefault(acct, {})
                try:
                    m = page(ig, acct, st.get("after"))
                except OutOfCalls:
                    raise
                except Exception as e:
                    if limited(e):          # Meta's limit: stop for now and keep the place, never mark the account done
                        raise OutOfCalls(STOPPED["why"])
                    st.update(done=True, note=str(e)[:100])
                    accounts.remove(acct)
                    continue
                pages += 1
                for p in m.get("data", []):
                    cap = p.get("caption") or ""
                    kind = kind_of(cap)
                    if p.get("media_type") != "VIDEO" or kind not in ("trailer", "teaser", "glimpse") or not p.get("media_url"):
                        continue
                    film = best_film(cap, films)
                    if not film or norm(film) in have_films:
                        continue
                    safe = re.sub(r'[\\/:*?"<>|]+', " ", f"{film} - {kind} [{p['id']}]").strip()
                    local = str(WORK / f"{safe}.mp4")
                    try:
                        download(p["media_url"], local)
                        meta = grid(local, str(WORK / "sheets" / f"{safe}.jpg"))
                        file_entry(drive, film, kind, local, meta, "instagram", acct, p.get("permalink"), cap.splitlines()[0][:100])
                        have_films.add(norm(film))
                        filed.append(f"{film} ({kind}, @{acct})")
                    except Exception as e:
                        print("could not file", film, str(e)[:120])
                st["after"], st["read"] = m.get("after"), st.get("read", 0) + len(m.get("data", []))
                if not m.get("after"):
                    st["done"] = True
                    accounts.remove(acct)
    except OutOfCalls:
        pass
    finally:
        drive.write_json("status", "ig_crawl.json", state)
    return filed, pages


def wanted(drive):
    try:
        return (drive.read_json("status", "trailers_wanted.json") or {}).get("films", [])
    except Exception:
        return []


def want(drive, films):
    """Put films on the trailer wanted list (fetched at the next trailer run; the planning run sees the list in the brief)."""
    try:
        cur = drive.read_json("status", "trailers_wanted.json") or {"films": []}
    except Exception:
        cur = {"films": []}
    have_now = {norm(x["film"]) for x in index(drive)["trailers"]}
    cur["films"] = [f for f in dict.fromkeys(cur.get("films", []) + list(films)) if norm(f) not in have_now]
    cur["updated"] = status.stamp()
    drive.write_json("status", "trailers_wanted.json", cur)
    return cur["films"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--film", action="append", default=[])
    ap.add_argument("--wanted", action="store_true")
    ap.add_argument("--probe", nargs="*")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--crawl", action="store_true", help="also work back through the accounts' history (inside the call budget)")
    a = ap.parse_args()
    from .instagram import Instagram
    os.makedirs(OUT / "peek" / "trailers", exist_ok=True)
    drive, adopted = None, []
    if a.probe is None:
        from .drive import Drive
        drive = Drive()
        CACHE["drive"] = drive
        adopted = adopt(drive)          # Drive only: hand-added trailers get their grids even when Instagram says no
    try:
        ig = Instagram()
        me = ig.me()
    except Exception as e:
        (OUT / "peek" / "trailers" / "probe.json").write_text(json.dumps({"instagram": f"refused: {str(e)[:300]}", "at": status.stamp()}, indent=1))
        print("Instagram refused:", str(e)[:300])
        if drive is not None:
            status.write(drive, "trailers.json", {"adopted": adopted, "instagram": f"refused: {str(e)[:200]}", "at": status.stamp()})
        raise SystemExit(1)
    try:
        OTHERS.extend(f["film"] for f in json.loads((niche_dir() / "knowledge" / "film_bank.json").read_text(encoding="utf-8")).get("films", []))
    except Exception:
        pass
    if a.probe is not None:
        out = {"instagram": f"ok as @{me.get('username')}", "at": status.stamp()}
        for film in a.probe:
            rep = {}
            try:
                e = fetch(None, ig, film, report=rep, force=True)
                rep["result"] = f"OK: {e['account']} / {e['kind']} / {e['duration']} s / {len(e['shots'])} shots"
            except Exception as ex:
                rep["result"] = f"FAILED: {ex}"
            out[film] = rep
            print(film, json.dumps(rep, indent=1, ensure_ascii=False))
        out["meta_usage_percent"], out["instagram_calls"] = type(ig).usage, type(ig).calls
        (OUT / "peek" / "trailers" / "probe.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
        if (WORK / "sheets").exists():
            shutil.copytree(WORK / "sheets", OUT / "peek" / "trailers" / "sheets", dirs_exist_ok=True)
        return
    films = a.film + (wanted(drive) if a.wanted else [])
    done, failed = [], {}
    for film in dict.fromkeys(films):
        try:
            e = fetch(drive, ig, film, force=a.force)
            done.append(f"{film}: {e['kind']} from {e['account']}")
        except OutOfCalls as ex:
            failed[film] = str(ex)
            break
        except Exception as ex:
            failed[film] = str(ex)[:200]
    save_cache()
    filed, pages = crawl(drive, ig) if a.crawl else ([], 0)
    want(drive, [])          # drop the films that now have a trailer
    res = {"adopted": adopted, "fetched": done, "failed": failed, "history_search": f"{pages} pages read, filed: {filed}",
           "instagram_calls": type(ig).calls}
    status.write(drive, "trailers.json", res)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    (OUT / "peek" / "trailers" / "result.json").write_text(json.dumps({**res, "at": status.stamp(), "meta_usage_percent": type(ig).usage},
                                                                      indent=1, ensure_ascii=False))
    if (WORK / "sheets").exists():      # the new grids, for a quick look on the 'peek' branch (the real copies are in Drive)
        shutil.copytree(WORK / "sheets", OUT / "peek" / "trailers" / "sheets", dirs_exist_ok=True)


def titles_in(headline):
    """Film titles in a news headline: words in quotes, else the capitalised words just before trailer/teaser/glimpse."""
    q = re.findall(r"[‘'\"“]([^’'\"”]{2,40})[’'\"”]", headline)
    if q:
        return [x.strip() for x in q]
    m = re.search(r"((?:[A-Z0-9][\w.]*\s){1,3})(?:official\s)?(?:trailer|teaser|glimpse)", headline, re.I)
    return [re.sub(r"(?i)\s+official$", "", m.group(1).strip())] if m else []


if __name__ == "__main__":
    main()
