"""The laptop run (AGENT.md 16.6, Harish 22 Nov): one command on Harish's laptop every 15-20 days does every download the
cloud computers cannot: trailers (and the film-bank top-up), competitor shorts to study, and this month's trending songs.

    python -m engine.laptop --publish     write the to-do list: data/laptop/todo.json (public, committed) + Drive requests/
    python -m engine.laptop --sort        move what the laptop dropped into Drive from-laptop/ to where each file belongs
    python -m engine.laptop --show        print the to-do list (no Drive writes)

The to-do list holds only film names, public video links and song names: nothing private (the repository is public).
The laptop helper (tools/clip_helper.py, no arguments) reads it from the repository, so Harish never copies a command.
No AI, no keys beyond the Drive sign-in the jobs already have."""
import argparse
import datetime as dt
import json
import re
import sys

from .settings import ENGINE, ROOT, niche_dir
from . import status

DROP = "from-laptop"
TODO = ROOT / "data" / "laptop" / "todo.json"
TRENDING = ROOT / "data" / "music" / "trending.json"
AUDIO = (".m4a", ".mp3", ".webm", ".opus", ".aac", ".wav", ".ogg")


def song_key(name):
    """A short, stable key for a song: 'song_' + its name in plain letters (the key plans name in music.sections)."""
    k = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")[:28].strip("_")
    return "song_" + (k or "untitled")


def trending_have():
    try:
        return {t["key"] for t in json.loads(TRENDING.read_text(encoding="utf-8")).get("tracks", [])}
    except Exception:
        return set()


def songs_wanted():
    """Songs the Weekly run listed (niches/<niche>/knowledge/trending_songs.yaml) that are not in the library yet."""
    from .settings import load_yaml
    p = niche_dir() / "knowledge" / "trending_songs.yaml"
    try:
        data = load_yaml(p.relative_to(ROOT)) if p.exists() else {}
    except Exception as e:
        print("trending songs list not readable:", str(e)[:120], file=sys.stderr)
        data = {}
    have, out = trending_have(), []
    for s in (data or {}).get("songs") or []:
        if not isinstance(s, dict) or not s.get("song"):
            continue
        key = song_key(s["song"])
        if key in have or any(x["key"] == key for x in out):
            continue
        out.append({"key": key, "song": str(s["song"])[:80], "film": str(s.get("film") or "")[:60],
                    "search": str(s.get("search") or f"{s['song']} {s.get('film') or ''} full song").strip()[:120],
                    "link": s.get("link") if str(s.get("link") or "").startswith("https://") else None})
    return out[:int((ENGINE.get("laptop") or {}).get("songs_max", 15))]


def study_wanted(drive):
    """The shorts still waiting to be studied: the links in Drive requests/study_to_get.md (written by the study job)."""
    text = drive.read_text("requests", "study_to_get.md") or ""
    cmd = next((ln.strip() for ln in text.splitlines() if ln.strip().startswith("py clip_helper.py --study")), "")
    return [u for u in cmd.split()[3:] if u.startswith("https://")] if cmd else []


def todo(drive):
    """Everything the next laptop run should fetch, in one list."""
    from . import trailers as T
    names, topup, why, _, links = T.request_parts(drive)
    films = [{"film": n, "url": links[T.norm(n)][1] if T.norm(n) in links else None, "why": str(why.get(n) or "")[:140]} for n in names]
    try:
        study = study_wanted(drive)
    except Exception as e:
        print("study list not readable:", str(e)[:120], file=sys.stderr)
        study = []
    return {"updated": status.stamp(), "drop_folder": DROP, "trailers": films, "topup": topup, "study": study, "songs": songs_wanted(),
            "note": "Read by tools/clip_helper.py on Harish's laptop (AGENT.md 16.6). Film names, public links and song names only."}


def counts(t):
    return {"trailers": len(t.get("trailers") or []), "topup": len(t.get("topup") or []), "study": len(t.get("study") or []),
            "songs": len(t.get("songs") or [])}


def publish(drive):
    t = todo(drive)
    TODO.parent.mkdir(parents=True, exist_ok=True)
    old = TODO.read_text(encoding="utf-8") if TODO.exists() else ""
    body = {k: v for k, v in t.items() if k != "updated"}
    if not old or {k: v for k, v in json.loads(old).items() if k != "updated"} != body:      # rewrite only when the list changed
        TODO.write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    try:
        drive.write_json("requests", "laptop_todo.json", t)
    except Exception as e:
        print("Drive copy of the laptop list not saved:", str(e)[:120], file=sys.stderr)
    return t


def _music_inbox(drive):
    mid = drive.music_folder() or drive.folder("music")
    f = drive.find_child(mid, "inbox", "application/vnd.google-apps.folder")
    if f:
        return f["id"]
    return drive.svc.files().create(body={"name": "inbox", "mimeType": "application/vnd.google-apps.folder", "parents": [mid]},
                                    fields="id", supportsAllDrives=True).execute(num_retries=3)["id"]


def where(name):
    """Which Drive folder a dropped file belongs in, by its name (the helper names every file this way)."""
    low = name.lower()
    if low.startswith("song - "):
        return "music/inbox"
    if " - trailer [" in low or low == "helper_report.txt" or low.endswith(".mp4"):
        return "clip-library"
    if low.endswith(AUDIO):
        return "study-audio"
    return None


def sort_drop(drive):
    """Move every file in Drive from-laptop/ to its folder. Safe to run again; a file it cannot place stays and is named."""
    src = drive.folder(DROP, create=False)
    if not src:
        return {"moved": 0, "left": []}
    moved, left = 0, []
    for f in drive.children(src, resolve_shortcuts=False):
        if f.get("mimeType") == "application/vnd.google-apps.folder":
            for g in drive.children(f["id"], resolve_shortcuts=False):          # a dragged folder: its files count too
                moved += _move(drive, g, f["id"], left)
            continue
        moved += _move(drive, f, src, left)
    if moved or left:
        print(f"laptop drop: {moved} file(s) sorted" + (f"; left in {DROP}/: {', '.join(left[:5])}" if left else ""))
    return {"moved": moved, "left": left}


def _move(drive, f, parent, left):
    dest = where(f.get("name", ""))
    if not dest:
        left.append(f.get("name", "?"))
        return 0
    to = _music_inbox(drive) if dest == "music/inbox" else drive.folder(dest)
    drive.svc.files().update(fileId=f["id"], addParents=to, removeParents=parent, fields="id", supportsAllDrives=True).execute(num_retries=3)
    return 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--sort", action="store_true")
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    from .drive import Drive
    d = Drive()
    if a.sort:
        try:
            sort_drop(d)
        except Exception as e:                      # fail soft: the files stay in from-laptop/ for the next job
            print("laptop drop not sorted:", str(e)[:160], file=sys.stderr)
    if a.publish or a.show:
        t = publish(d) if a.publish else todo(d)
        print("laptop run list:", json.dumps(counts(t)))


if __name__ == "__main__":
    main()
