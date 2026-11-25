"""Cloud first (Harish, 25 Nov; AGENT.md 16.6). Every night the cloud tries the laptop run's list itself with yt-dlp:
trailers, the film-bank top-up, the shorts to study and the trending songs. What it gets goes into Drive from-laptop/ and
is sorted and taken in exactly as if the laptop had sent it, so the laptop list shrinks by itself.

YouTube refuses most cloud computers unless they are signed in. With the GitHub secret YOUTUBE_COOKIES (the cookies.txt
of a spare Google account) yt-dlp signs in. Without it, or once the cookies expire, the first refusal stops the run at
once (no runner minutes wasted) and everything waits for the laptop run, as before. The cookies are written to a
private temporary file, never printed, never saved in the repository.

    python -m engine.autofetch          try the list (caps: config/engine.yaml autofetch)
    python -m engine.autofetch --show   print what it would try, nothing downloaded
"""
import argparse
import contextlib
import importlib.util
import io
import os
import shutil
import sys
import tempfile
import time

from .settings import ENGINE, ROOT
from . import laptop, status

CFG = {"max_files": 25, "max_minutes": 40, **(ENGINE.get("autofetch") or {})}
REFUSED = ("sign in to confirm", "not a bot", "http error 429", "too many requests", "login required",
           "this video is unavailable in your country", "use --cookies")


def helper():
    """tools/clip_helper.py, the laptop's own download code: the cloud uses the same search, names and checks."""
    spec = importlib.util.spec_from_file_location("clip_helper", ROOT / "tools" / "clip_helper.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def cookies_file(tmp):
    """The YOUTUBE_COOKIES secret as a private file (Netscape cookies.txt), or None."""
    text = (os.environ.get("YOUTUBE_COOKIES") or "").strip()
    if not text:
        return None
    path = os.path.join(tmp, "cookies.txt")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(text + "\n")
    return path


def ytdlp_cmd(cookies=None):
    import imageio_ffmpeg
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--socket-timeout", "30", "--ffmpeg-location", imageio_ffmpeg.get_ffmpeg_exe()]
    if shutil.which("node"):
        cmd += ["--js-runtimes", "node"]
    if cookies:
        cmd += ["--cookies", cookies]
    return cmd


def refused(text):
    low = str(text or "").lower()
    return any(r in low for r in REFUSED)


def jobs(t):
    """The list as single steps, most useful first: trailers coming reels need, songs, shorts to study, the top-up."""
    out = [("trailer", (x["film"], x.get("url"))) for x in t.get("trailers") or []]
    out += [("song", s) for s in t.get("songs") or [] if "instagram.com" not in str(s.get("link") or "")]   # Instagram: laptop only
    out += [("study", u) for u in t.get("study") or []]
    out += [("trailer", (f, None)) for f in t.get("topup") or []]
    return out


def run_one(h, cmd, kind, item, out):
    """One download into out/. Returns (ok, what the helper said)."""
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        if kind == "trailer":
            got, _, _ = h.get_trailers(cmd, [item], out, dict(h.FILMS))
            ok = bool(got)
        elif kind == "song":
            res = h.get_song(cmd, item, out)
            print(res)
            ok = res in ("saved", "already there")
        else:
            h.tools = lambda: cmd                 # the helper's study() builds its own command; give it the signed-in one
            ok = h.study([item], out, quiet=True) > 0
    return ok, buf.getvalue()


def run(drive, dry=False):
    t = laptop.todo(drive)
    todo = jobs(t)
    if dry or not todo:
        return {"tried": 0, "got": 0, "waiting": len(todo), "note": "nothing to fetch" if not todo else "dry run",
                "list": [f"{k}: {(i[0] if isinstance(i, tuple) else i.get('song') if isinstance(i, dict) else i)}" for k, i in todo][:40]}
    tmp = tempfile.mkdtemp(prefix="autofetch-")
    out = os.path.join(tmp, "out")
    os.makedirs(out)
    cookies = cookies_file(tmp)
    h, cmd, t0 = helper(), ytdlp_cmd(cookies), time.time()
    tried, got, kinds, stop = 0, 0, {}, None
    try:
        for kind, item in todo:
            if got >= int(CFG["max_files"]) or time.time() - t0 > 60 * float(CFG["max_minutes"]):
                stop = "the nightly cap was reached; the rest is tried tomorrow"
                break
            tried += 1
            ok, said = run_one(h, cmd, kind, item, out)
            if ok:
                got += 1
                kinds[kind] = kinds.get(kind, 0) + 1
            elif refused(said):
                stop = ("YouTube refused this cloud computer" + (" even signed in: the YOUTUBE_COOKIES may have expired"
                        if cookies else " (no YOUTUBE_COOKIES secret yet)") + "; the laptop run does the rest")
                break
        sent = 0
        for f in sorted(os.listdir(out)):
            p = os.path.join(out, f)
            if os.path.isfile(p) and not f.endswith(".txt"):
                drive.upload(p, laptop.DROP, name=f)
                sent += 1
        if sent:
            laptop.sort_drop(drive)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)          # the cookies file goes with it
    return {"tried": tried, "got": got, "kinds": kinds, "signed_in": bool(cookies), "waiting": len(todo) - got, "note": stop or "done"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", action="store_true")
    a = ap.parse_args()
    from .drive import Drive
    from .control import Control
    drive = Drive()
    if Control(drive).mode == "sleep":
        status.write(drive, "autofetch.json", {"state": "asleep"})
        print("Asleep: nothing fetched.")
        return
    try:
        res = run(drive, dry=a.show)
    except Exception as e:                       # fail soft: the laptop list stays as it is
        res = {"state": "failed", "note": str(e)[:200]}
    if not a.show:
        status.write(drive, "autofetch.json", {**res, "at": status.stamp()})
        if res.get("signed_in") and "expired" in str(res.get("note")):
            status.alert(drive, "YouTube sign-in for the cloud fetch has expired",
                         "Tonight YouTube refused the cloud even with the saved sign-in, so trailers, shorts and songs wait for the laptop run.",
                         "Nothing else stops.", "Export the spare account's cookies again and replace the GitHub secret YOUTUBE_COOKIES "
                         "(GUIDE.md, laptop run section).", level="info")
        if res.get("got"):
            from .manual import start_after
            print("pick-up:", start_after("laptop"))
    print("cloud fetch:", {k: v for k, v in res.items() if k != "list"})
    for line in res.get("list") or []:
        print(" ", line)


if __name__ == "__main__":
    main()
