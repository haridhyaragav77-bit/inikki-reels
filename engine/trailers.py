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
    """The film's name as words, or as one hashtag like #Jailer2 or #96Movie (never inside another word, like 1996).
    A one-word title that is also an everyday word (Scene, Leo) counts only as a hashtag, in capitals, or right before
    trailer/teaser/glimpse, so 'behind the scene' is never taken for the film."""
    f, t, raw = norm(film), norm(text), str(text or "")
    if not f:
        return False
    fs = f.replace(" ", "")
    if any(tag.lower().startswith(fs) and tag.lower()[len(fs):] in SUFFIXES for tag in re.findall(r"#(\w+)", raw)):
        return True
    if " " not in f and not any(ch.isdigit() for ch in f):
        return bool(re.search(rf"(?<![A-Za-z]){re.escape(f.upper())}(?![A-Za-z])", raw)) or \
            bool(re.search(rf"(^| ){re.escape(f)} (official )?(trailer|teaser|glimpse|promo)", t))
    if f" {f} " in f" {t} ":
        return True
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


settings_cache = {}


def settings():
    if not settings_cache:
        s = yaml.safe_load((niche_dir() / "knowledge" / "sources.yaml").read_text(encoding="utf-8")) or {}
        settings_cache.update(s.get("trailers") or {})
    return settings_cache


def ffmpeg():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def duration(path):
    r = subprocess.run([ffmpeg(), "-i", path], capture_output=True, text=True)
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", r.stderr)
    return round(int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)), 2) if m else None


# ---------------------------------------------------------------- official Instagram accounts
_POSTS = {}
_LINKS = {}          # video links asked for in this run, by post id
_ASKED = {}          # link questions per account in this run
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
    if any(w in str(e).lower() for w in ("api access blocked", "blocked this app", "request limit", "too many calls", "(#4)", "(#17)", "(#32)", "(#613)")):
        STOPPED.setdefault("why", f"Instagram stopped the search: {str(e)[:160]}")
        return True
    return False


def budget():
    return int(settings().get("max_calls_per_run", 60))


def page(ig, acct, after=None, links=None, limit=None):
    """One page of an official account (page_size posts). Stops the run before it nears Meta's hourly meter.
    Meta's meter counts processing time, so a normal page reads only captions; the video link is asked for later,
    for the one post that matches (`links=True`, a page of `limit` posts from the same place)."""
    if STOPPED:
        raise OutOfCalls(STOPPED["why"])
    if type(ig).calls >= budget():
        raise OutOfCalls(f"stopped at {type(ig).calls} Instagram calls (the per-run budget)")
    if type(ig).usage >= int(settings().get("max_usage_percent", 50)):
        raise OutOfCalls(f"stopped: Meta says {type(ig).usage}% of the hourly allowance is used; the rest is kept for posting")
    if links is None:
        links = not settings().get("scan_without_links", True)
    size = int(limit or settings().get("page_size", 25))
    media = f"media.limit({size})" + (f".after({after})" if after else "")
    fields = "id,caption,media_type,timestamp" + (",media_url,permalink,thumbnail_url" if links else "")
    try:
        j = ig.get(ig.user_id, fields=f"business_discovery.username({acct}){{username,{media}{{{fields}}}}}")
    except Exception as e:
        if "reduce the amount of data" not in str(e).lower() or size <= 25:
            raise
        settings_cache["page_size"] = 25        # Meta wants smaller pages: use 25 for the rest of the run
        return page(ig, acct, after, links, limit)
    m = (j.get("business_discovery") or {}).get("media") or {}
    m["after"] = ((m.get("paging") or {}).get("cursors") or {}).get("after")
    for i, p in enumerate(m.get("data", [])):
        p["_cur"], p["_i"] = after, i          # where the post sits, so its video link can be asked for alone
        if p.get("caption"):
            p["caption"] = p["caption"][:400]
    return m


def link(ig, acct, hit):
    """The video link (and post link) of one matched post: a small call from the same place in the account.
    Why a link is missing is kept in hit["why"]: the post moved, or Meta sent no video link (Meta leaves the link out
    of posts it treats as holding copyrighted music)."""
    if hit.get("url"):
        return hit
    m = page(ig, acct, hit.get("_cur"), links=True, limit=int(hit.get("_i", 0)) + 3)
    p = next((x for x in m.get("data", []) if x.get("id") == hit["id"]), None)
    got = sum(1 for x in m.get("data", []) if x.get("media_url"))
    if p is None:
        hit["why"] = f"the post was not at its place any more (links for {got} of {len(m.get('data', []))} posts there)"
    elif not p.get("media_url"):
        hit["why"] = (f"Meta sent no video link for this post, and links for {got} of {len(m.get('data', []))} posts around it"
                      f" (fields: {', '.join(sorted(k for k in p if not k.startswith('_')))})")
    hit["url"], hit["link"], hit["thumb"] = (p or {}).get("media_url"), (p or {}).get("permalink"), (p or {}).get("thumbnail_url")
    return hit


BAD_HOURS = 72


def posts(ig, acct, pages=2, deep=False):
    """An account's posts, newest first, read once per run and shared by every film. Asking for more pages carries on
    from where the last read stopped (one call per 25 posts); the 6-hour copy in Drive is used first."""
    if acct not in _POSTS:
        c = _cache().get(acct)
        if c and status.now().timestamp() - c.get("t", 0) < (BAD_HOURS if c.get("bad") else CACHE_HOURS) * 3600:
            if c.get("bad"):
                raise RuntimeError(f"skipped: {c['bad']}")
            if "pages" in c:
                _POSTS[acct] = {k: c[k] for k in ("posts", "after", "pages", "end")}
            elif not deep:                         # an older copy without its place: fine for a normal read
                _POSTS[acct] = {"posts": c["posts"], "after": None, "pages": 2, "end": True}
    st = _POSTS.setdefault(acct, {"posts": [], "after": None, "pages": 0, "end": False})
    while st["pages"] < pages and not st["end"]:
        m = page(ig, acct, st["after"])
        st["posts"] += m.get("data", [])
        st["after"], st["pages"] = m.get("after"), st["pages"] + 1
        st["end"] = not st["after"]
        _cache()[acct] = {"t": status.now().timestamp(), **st}
    return st["posts"]


def split_hint(film):
    """'Jailer 2@sunpictures+anirudhofficial' -> ('Jailer 2', ['sunpictures', 'anirudhofficial']): the film's own
    accounts, named by the planning run or by hand, are searched first and further back."""
    name, _, accts = str(film).partition("@")
    return name.strip(), [x.strip().lstrip("@") for x in accts.split("+") if x.strip()]


def _matches(film, acct, ps):
    out = []
    for p in ps:
        cap = p.get("caption") or ""
        if p.get("media_type") == "VIDEO" and mentions(film, cap) and kind_of(cap) and norm(best_film(cap, OTHERS + [film])) == norm(film):
            out.append({"account": acct, "id": p["id"], "kind": kind_of(cap), "url": p.get("media_url"),
                        "link": p.get("permalink"), "when": p.get("timestamp"), "title": cap.splitlines()[0][:100],
                        "_cur": p.get("_cur"), "_i": p.get("_i", 0)})
    return out


def _rank(kinds):
    return lambda h: (kinds.index(h["kind"]) if h["kind"] in kinds else 99, -int(re.sub(r"\D", "", str(h.get("when") or "0"))[:14] or 0))


def _ask(ig, acct, hits, kinds):
    """Ask for the video link of the best matching post not asked about yet (one small call). True if a link came back."""
    pend = sorted([_LINKS.get(h["id"], h) for h in hits if h["kind"] in kinds], key=_rank(kinds))
    pend = [h for h in pend if not h.get("url") and not h.get("_asked")]
    if not pend or _ASKED.get(acct, 0) >= 2:          # at most 2 link questions per account per run
        return False
    _ASKED[acct] = _ASKED.get(acct, 0) + 1
    h = pend[0]
    h["_asked"] = True
    _LINKS[h["id"]] = link(ig, acct, h)
    return bool(h.get("url"))


def candidates(ig, film, accounts, report=None, enough=("trailer",), deep=(), want=("trailer", "teaser", "glimpse", "promo")):
    """Video posts of the official accounts whose caption names the film and says trailer, teaser, glimpse ...
    The search stops at the first account that gives a real trailer with its video link (kinds in `enough`); on the
    film's own accounts (`deep`) any wanted kind is enough, and they are read back up to `deep_pages` pages.
    Pages are read without video links (Meta's meter counts time); the link is asked for only for the best match.
    When Meta's meter or the call budget stops the run, what was found so far is still returned."""
    found = []
    have_it = lambda: any(f.get("url") and f["kind"] in (want if f["account"] in deep else enough) for f in found)
    hits_of = lambda acct, ps: [_LINKS.get(h["id"], h) for h in _matches(film, acct, ps)]
    stopped = None
    for acct in accounts:
        if have_it():
            break
        top = int(settings().get("deep_pages", 8)) if acct in deep else 1      # other accounts: the newest page (a new drop)
        kinds = want if acct in deep else enough
        ps = []
        try:
            for k in range(1, top + 1):
                ps = posts(ig, acct, pages=k, deep=acct in deep)
                if _ask(ig, acct, hits_of(acct, ps), kinds) or any(h.get("url") and h["kind"] in kinds for h in hits_of(acct, ps)) \
                        or _POSTS[acct]["end"]:
                    break
        except OutOfCalls as e:
            stopped = str(e)
        except Exception as e:
            if limited(e):
                stopped = STOPPED["why"]
            else:
                _POSTS[acct] = {"posts": [], "after": None, "pages": 99, "end": True}
                if not str(e).startswith("skipped"):
                    _cache()[acct] = {"t": status.now().timestamp(), "posts": [], "bad": str(e)[:120]}
                if report is not None:
                    report[acct] = f"not readable: {str(e)[:90]}"
                continue
        hits = hits_of(acct, ps)
        found += hits
        if report is not None:
            back = min((p.get("timestamp") or "")[:10] for p in ps) if ps else "-"
            report[acct] = f"{len(hits)} match in {len(ps)} posts back to {back}" + "".join(
                f" | {h['kind']} {str(h.get('when'))[:10]}{'' if h.get('url') else ' (no video link: ' + h.get('why', 'not asked') + ')'}: {h['title'][:60]}"
                for h in sorted(hits, key=lambda h: (not h.get("_asked"), _rank(list(want))(h)))[:4])
        if stopped:
            break
        if acct in deep and not any(a in deep for a in accounts[accounts.index(acct) + 1:]) and \
                any(f.get("_asked") and not f.get("url") and f["account"] in deep for f in found):
            if report is not None:
                report["note"] = "the film's own accounts have the posts but Meta gave no video link; other accounts were not searched"
            break
    if not stopped and not any(f.get("url") and f["kind"] in want for f in found):
        try:                                   # no trailer anywhere: the best teaser or glimpse found on the way
            for acct in dict.fromkeys(f["account"] for f in sorted(found, key=_rank(list(want)))):
                if _ask(ig, acct, [f for f in found if f["account"] == acct], list(want)):
                    break
        except OutOfCalls as e:
            stopped = str(e)
        found = [_LINKS.get(f["id"], f) for f in found]
    if stopped:
        if report is not None:
            report["stopped"] = stopped
        if not any(f.get("url") for f in found):
            raise OutOfCalls(stopped)
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


# ---------------------------------------------------------------- official stills (news updates, AGENT.md 5.9)
def _safe(name):
    return re.sub(r'[\\/:*?"<>|]+', " ", str(name)).strip()


def download_image(url, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    if len(r.content) < 8000:
        raise RuntimeError("the picture came back empty")
    with open(path, "wb") as f:
        f.write(r.content)
    return path


def stills_grid(items, folder, out_jpg):
    """One picture with every still numbered, so the planning run picks the still that shows each line."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    cols, tw, th = 5, 240, 300
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 6) + 6, rows * (th + 6) + 6), (12, 12, 20))
    fp = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    font = ImageFont.truetype(fp, 20) if os.path.exists(fp) else ImageFont.load_default()
    dr = ImageDraw.Draw(sheet)
    for k, it in enumerate(items):
        x, y = 6 + (k % cols) * (tw + 6), 6 + (k // cols) * (th + 6)
        im = ImageOps.fit(Image.open(os.path.join(folder, it["file"])).convert("RGB"), (tw, th))
        sheet.paste(im, (x, y))
        label = f"#{it['n']} {it['date'][5:]}"
        dr.rectangle([x, y, x + 11 * len(label) + 8, y + 26], fill=(0, 0, 0))
        dr.text((x + 5, y + 3), label, fill=(255, 214, 64), font=font)
    os.makedirs(os.path.dirname(out_jpg), exist_ok=True)
    sheet.save(out_jpg, quality=86)
    return out_jpg


def stills(drive, ig, film, report=None):
    """The film's official stills: the cover of each video post and each picture post on its own accounts that names it
    (Meta gives these even when it withholds the video). Saved to clip-library/stills/<film>/ with a numbered grid;
    returns the library entry. `film` may carry its accounts ('Jailer 2@sunpictures')."""
    film, hint = split_hint(film)
    accounts, deep = hint or settings().get("instagram_accounts", []), set(hint)     # named accounts are read further back
    found, report = [], report if report is not None else {}
    for acct in accounts:
        try:
            ps = posts(ig, acct, pages=int(settings().get("deep_pages", 6)) if acct in deep else 1, deep=acct in deep)
        except OutOfCalls as e:
            report["stopped"] = str(e)
            break
        except Exception as e:
            if limited(e):
                report["stopped"] = STOPPED["why"]
                break
            report[acct] = f"not readable: {str(e)[:90]}"
            continue
        mine = [p for p in ps if p.get("media_type") in ("VIDEO", "IMAGE") and mentions(film, p.get("caption") or "")
                and norm(best_film(p.get("caption") or "", OTHERS + [film])) == norm(film)]
        found += [(acct, p) for p in mine]
        report[acct] = f"{len(mine)} posts of {film} in {len(ps)}"
    found = found[:int(settings().get("max_stills", 30))]
    pages_needed = {}
    for acct, p in found:
        if not (p.get("thumbnail_url") or (p.get("media_type") == "IMAGE" and p.get("media_url"))):
            pages_needed.setdefault((acct, p.get("_cur")), []).append(p)
    for (acct, cur), ps in pages_needed.items():       # one call per page that holds the film's posts
        try:
            m = page(ig, acct, cur, links=True, limit=max(int(x.get("_i", 0)) for x in ps) + 3)
        except OutOfCalls as e:
            report["stopped"] = str(e)
            break
        except Exception as e:
            if limited(e):
                report["stopped"] = STOPPED["why"]
                break
            continue
        got = {x.get("id"): x for x in m.get("data", [])}
        for p in ps:
            q = got.get(p["id"]) or {}
            for k in ("thumbnail_url", "media_url", "permalink"):
                if q.get(k):
                    p[k] = q[k]
    folder = WORK / "stills" / _safe(film)
    shutil.rmtree(folder, ignore_errors=True)
    items = []
    for acct, p in found:
        url = p.get("thumbnail_url") if p.get("media_type") == "VIDEO" else p.get("media_url")
        if not url:
            continue
        name = f"{len(items) + 1:02d}.jpg"
        try:
            download_image(url, str(folder / name))
        except Exception:
            continue
        cap = p.get("caption") or ""
        items.append({"n": len(items) + 1, "file": name, "account": acct, "post": p.get("permalink"), "date": (p.get("timestamp") or "")[:10],
                      "kind": "video cover" if p.get("media_type") == "VIDEO" else "picture", "caption": cap.splitlines()[0][:90] if cap else ""})
    if not items:
        raise RuntimeError(f"no official stills for {film} on {', '.join(accounts[:4])}" + (f" ({report['stopped']})" if report.get("stopped") else ""))
    sheet = f"{_safe(film)} - stills.jpg"
    stills_grid(items, str(folder), str(WORK / "sheets" / sheet))
    entry = {"film": film, "kind": "stills", "folder": f"clip-library/stills/{_safe(film)}", "sheet": sheet, "stills": items,
             "accounts": accounts, "fetched": status.stamp()}
    if drive is not None:
        for it in items:
            drive.upload(str(folder / it["file"]), entry["folder"], name=it["file"])
        drive.upload(str(WORK / "sheets" / sheet), "clip-library/sheets", name=sheet)
        idx = index(drive)
        idx["stills"] = [x for x in idx.get("stills", []) if norm(x["film"]) != norm(film)] + [entry]
        drive.write_json("clip-library", "index.json", idx)
    try:
        os.makedirs(OUT / "peek" / "trailers" / "sheets", exist_ok=True)
        shutil.copy(str(WORK / "sheets" / sheet), str(OUT / "peek" / "trailers" / "sheets" / sheet))
        (OUT / "peek" / "trailers" / "sheets" / (sheet[:-4] + ".json")).write_text(json.dumps(entry, indent=1, ensure_ascii=False))
    except Exception:
        pass
    return entry


def have_stills(film, idx):
    return [x for x in idx.get("stills", []) if norm(x["film"]) == norm(split_hint(film)[0])]


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
    film, hint = split_hint(film)
    idx = index(drive) if drive is not None else {"trailers": []}
    if have(film, idx) and not force:
        return have(film, idx)[0]
    order = {k: i for i, k in enumerate(want)}
    accounts = hint or settings().get("instagram_accounts", [])     # a film's own accounts, when named, are the whole search
    cands = [c for c in candidates(ig, film, accounts, report=report, deep=set(hint), want=want) if c["kind"] in order and c.get("url")]
    if not cands:
        raise RuntimeError(f"no official trailer for {film} on the studio accounts (add it with the laptop helper)")
    cands.sort(key=lambda c: (order[c["kind"]], c["account"] not in hint, -(int(re.sub(r"\D", "", c.get("when") or "0")[:14] or 0))))
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
    try:                                  # the shot times beside the grid on the 'peek' branch (a quick look)
        os.makedirs(OUT / "peek" / "trailers" / "sheets", exist_ok=True)
        (OUT / "peek" / "trailers" / "sheets" / (entry["sheet"][:-4] + ".json")).write_text(json.dumps(entry, indent=1, ensure_ascii=False))
    except Exception:
        pass
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
    kids = drive.children(fid) if fid else []
    for sub in [k for k in kids if k.get("mimeType") == "application/vnd.google-apps.folder" and k["name"] not in ("sheets", "stills")]:
        kids += drive.children(sub["id"])          # a folder dragged in whole (for example trailers_for_drive) counts too
    vids = [k for k in kids if k.get("mimeType", "").startswith("video/") and k["name"] not in known]
    done, cover = [], films_we_cover(drive) if vids else []
    for k in vids:
        local = str(WORK / k["name"])
        try:
            drive.download(k["id"], local)
            meta = grid(local, str(WORK / "sheets" / (k["name"][:-4] + ".jpg")))
            film = film_from_name(k["name"], cover)
            file_entry(drive, film, kind_of(k["name"]) or "trailer", local, meta, "clip-library", "added by hand", upload_video=False)
            done.append(f"{film}: {len(meta)} shots")
        except Exception as e:
            print("could not file", k["name"], str(e)[:120])
        finally:
            try:
                os.remove(local)            # keep the runner's disk small; the video stays in Drive
            except OSError:
                pass
    return done


def films_we_cover(drive):
    bank = json.loads((niche_dir() / "knowledge" / "film_bank.json").read_text(encoding="utf-8")).get("films", [])
    return list(dict.fromkeys([f["film"] for f in bank] + [split_hint(f)[0] for f in wanted(drive)]))


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
                    if p.get("media_type") != "VIDEO" or kind not in ("trailer", "teaser", "glimpse"):
                        continue
                    film = best_film(cap, films)
                    if not film or norm(film) in have_films:
                        continue
                    if not p.get("media_url"):          # pages are read without links: ask for this one post's link
                        h = link(ig, acct, {"id": p["id"], "_cur": p.get("_cur"), "_i": p.get("_i", 0)})
                        p["media_url"], p["permalink"] = h.get("url"), h.get("link")
                        if not p["media_url"]:
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
    cur["films"] = [f for f in dict.fromkeys(cur.get("films", []) + list(films)) if norm(split_hint(f)[0]) not in have_now]
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
    ap.add_argument("--stills", action="append", default=[], help="a film's official stills only ('Film@account')")
    ap.add_argument("--adopt-only", action="store_true", help="only give the trailers dropped into Drive their grids (no Instagram)")
    a = ap.parse_args()
    from .instagram import Instagram
    os.makedirs(OUT / "peek" / "trailers", exist_ok=True)
    drive, adopted = None, []
    if a.probe is None:
        from .drive import Drive
        drive = Drive()
        CACHE["drive"] = drive
        adopted = adopt(drive)          # Drive only: hand-added trailers get their grids even when Instagram says no
        if a.adopt_only:
            res = {"adopted": adopted, "at": status.stamp()}
            status.write(drive, "trailers.json", res)
            (OUT / "peek" / "trailers" / "result.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
            if (WORK / "sheets").exists():
                shutil.copytree(WORK / "sheets", OUT / "peek" / "trailers" / "sheets", dirs_exist_ok=True)
            print(json.dumps(res, indent=1, ensure_ascii=False))
            return
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
        out["meta_usage_percent"], out["instagram_calls"], out["meta_meters"] = type(ig).usage, type(ig).calls, type(ig).usage_raw
        (OUT / "peek" / "trailers" / "probe.json").write_text(json.dumps(out, indent=1, ensure_ascii=False))
        if (WORK / "sheets").exists():
            shutil.copytree(WORK / "sheets", OUT / "peek" / "trailers" / "sheets", dirs_exist_ok=True)
        return
    films = a.film + (wanted(drive) if a.wanted else [])
    done, failed, notes = [], {}, {}
    for film in dict.fromkeys(a.stills):
        try:
            st = stills(drive, ig, film, report=notes.setdefault(film, {}))
            done.append(f"{st['film']}: {len(st['stills'])} official stills")
        except OutOfCalls as ex:
            failed[film] = str(ex)
            break
        except Exception as ex:
            failed[film] = str(ex)[:200]
    for film in dict.fromkeys(films):
        try:
            e = fetch(drive, ig, film, force=a.force, report=notes.setdefault(film, {}))
            done.append(f"{film}: {e['kind']} from {e['account']}")
        except OutOfCalls as ex:
            failed[film] = str(ex)
            break
        except Exception as ex:
            failed[film] = str(ex)[:200]
            if have_stills(film, index(drive)) and not a.force:
                continue
            try:                         # no video from Meta: the film's official stills, for news updates (AGENT.md 5.9)
                st = stills(drive, ig, film, report=notes.setdefault(film, {}))
                done.append(f"{st['film']}: {len(st['stills'])} official stills (Meta gave no video)")
            except OutOfCalls as ex2:
                failed[film] += f"; stills: {ex2}"
                break
            except Exception as ex2:
                failed[film] += f"; stills: {str(ex2)[:160]}"
    save_cache()
    filed, pages = crawl(drive, ig) if a.crawl else ([], 0)
    want(drive, [])          # drop the films that now have a trailer
    res = {"adopted": adopted, "fetched": done, "failed": failed, "history_search": f"{pages} pages read, filed: {filed}",
           "instagram_calls": type(ig).calls, "accounts": {f: n for f, n in notes.items() if n}, "meta_meters": type(ig).usage_raw,
           "seconds_per_call": type(ig).seconds}
    status.write(drive, "trailers.json", res)
    print(json.dumps(res, indent=1, ensure_ascii=False))
    (OUT / "peek" / "trailers" / "result.json").write_text(json.dumps({**res, "at": status.stamp(), "meta_usage_percent": type(ig).usage},
                                                                      indent=1, ensure_ascii=False))
    if (WORK / "sheets").exists():      # the new grids, for a quick look on the 'peek' branch (the real copies are in Drive)
        shutil.copytree(WORK / "sheets", OUT / "peek" / "trailers" / "sheets", dirs_exist_ok=True)


def accounts_in(text):
    """Official accounts named in a headline: a studio, label or star in sources.yaml trailers.handles (longest names first,
    so 'Vijay Sethupathi' is not read as 'Vijay')."""
    t, out = f" {norm(text)} ", []
    for name, acct in sorted((settings().get("handles") or {}).items(), key=lambda kv: -len(kv[0])):
        if f" {norm(name)} " in t:
            t = t.replace(f" {norm(name)} ", " ")
            out += [acct] if isinstance(acct, str) else list(acct)
    return list(dict.fromkeys(out))


def titles_in(headline):
    """Film titles in a news headline: words in quotes, else the capitalised words just before trailer/teaser/glimpse.
    Possessives are dropped first ("Rajinikanth's Jailer 2 trailer" -> Jailer 2)."""
    h = re.sub(r"(\w)['’]s\b", r"\1", str(headline or ""))
    q = re.findall(r"[‘'\"“]([^’'\"”]{2,40})[’'\"”]", h)
    if q:
        return [x.strip() for x in q]
    m = re.search(r"((?:[A-Z0-9][\w.]*\s){1,3})(?i:official\s)?(?i:trailer|teaser|glimpse)", h)
    if not m:
        return []
    words = m.group(1).split()
    while words and words[-1].lower() in ("official", "new", "first"):
        words = words[:-1]
    names = {norm(n) for n in (settings().get("handles") or {})}
    try:
        names |= {norm(n) for n in ((yaml.safe_load((niche_dir() / "knowledge" / "sources.yaml").read_text(encoding="utf-8")) or {})
                                    .get("watch") or {}).get("names", [])}
    except Exception:
        pass
    names |= {"the", "a", "new", "watch", "first", "official", "superstar", "thalaivar"}
    try:
        known = {norm(f["film"]) for f in json.loads((niche_dir() / "knowledge" / "film_bank.json").read_text(encoding="utf-8")).get("films", [])}
    except Exception:
        known = set()
    changed = True
    while words and changed and norm(" ".join(words)) not in known:      # leading star names are not part of the title
        changed = False
        for k in (2, 1):
            if len(words) > k - 1 and norm(" ".join(words[:k])) in names and len(words) > k:
                words, changed = words[k:], True
                break
    return [" ".join(words)] if words else []


if __name__ == "__main__":
    main()
