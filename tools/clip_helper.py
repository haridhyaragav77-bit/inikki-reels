#!/usr/bin/env python3
r"""iNiKKi laptop helper: THE ONE COMMAND, every 15 to 20 days (AGENT.md 16.6, Harish 22 Nov).

    py clip_helper.py

It updates itself, reads its own to-do list from the iNiKKi repository (data/laptop/todo.json: film names, public links and
song names), and gets everything the cloud computers cannot download: the trailers the coming reels need, the film-bank
top-up, the competitor shorts to study, and this month's trending songs. At the end it asks for any trending song you heard.
Everything lands in ONE folder, for_drive. If Google Drive for desktop is on this computer, the files are copied straight
into Google Drive > iNiKKi Reels > from-laptop and there is nothing to drag. Otherwise drag every file in for_drive into
that folder. Then press Done on the Control Room's Manual work tab. The Engine sorts the files by itself.

Windows (once):
  1. Install Python from python.org/downloads (on the first screen, tick "Add python.exe to PATH").
  2. Put this file in a folder, for example Downloads.
  3. Open that folder, click the address bar at the top, type  cmd  and press Enter.
  4. Type  py clip_helper.py  and press Enter. Leave it running (about 30 to 60 minutes, it works by itself).
Mac: in Terminal, type  python3 clip_helper.py  in the folder with this file.

Other uses:
  py clip_helper.py --drive "G:\My Drive\iNiKKi Reels"   tell it once where Google Drive for desktop keeps the folder
  py clip_helper.py --film-bank                     every film-bank trailer (the old full run)
  py clip_helper.py "Leo" "Amaran"                  only these films
  py clip_helper.py "Leo=https://www.youtube.com/watch?v=..."   one exact video for a film

It keeps only trailers whose title names the film and that come from an official channel (it prints each channel).
Running it again skips the files already in trailers_for_drive.

Shorts to study (AGENT.md 10.3): the Engine writes the ready line in Drive requests/study_to_get.md, for example
  py clip_helper.py --study https://www.youtube.com/shorts/... https://www.youtube.com/shorts/...
It saves only the sound of each short into  study_for_drive ; drag those files into
Google Drive > iNiKKi Reels > study-audio. The Engine turns them into text and deletes the sound.
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trailers_for_drive")
STUDY_OUT = os.path.join(HERE, "study_for_drive")
DROP = os.path.join(HERE, "for_drive")                  # the laptop run puts everything here (one folder, one drag)
SETTINGS = os.path.join(HERE, "clip_helper_settings.json")
REPO = "https://raw.githubusercontent.com/haridhyaragav77-bit/inikki-reels/main/"   # public: the helper and its to-do list

# The film bank (niches/tamil-cinema/knowledge/film_bank.json), copied here so this file works on its own.
FILMS = [("Kaithi", 2019), ("Jigarthanda", 2014), ("Ratsasan", 2018), ("Vikram", 2022), ("Vada Chennai", 2018), ("Super Deluxe", 2019),
         ("Aaranya Kaandam", 2011), ("Visaranai", 2016), ("Pariyerum Perumal", 2018), ("Asuran", 2019), ("Soorarai Pottru", 2020),
         ("Jai Bhim", 2021), ("Maharaja", 2024), ("Viduthalai Part 1", 2023), ("Mandela", 2021), ("Karnan", 2021), ("Nayakan", 1987),
         ("Thalapathi", 1991), ("Mouna Ragam", 1986), ("Pudhupettai", 2006), ("Subramaniyapuram", 2008), ("Aadukalam", 2011), ("96", 2018),
         ("Vikram Vedha", 2017), ("Thani Oruvan", 2015), ("Kaaka Muttai", 2015), ("Soodhu Kavvum", 2013), ("Pizza", 2012),
         ("Anbe Sivam", 2003), ("Virumaandi", 2004), ("Kuruthipunal", 1995), ("Mahanadhi", 1994), ("Leo", 2023), ("Jailer", 2023),
         ("Amaran", 2024), ("Maaveeran", 2023), ("Master", 2021), ("Lubber Pandhu", 2024),
         # English and world films for breakdowns and recommendations
         ("The Godfather", 1972), ("Pulp Fiction", 1994), ("The Dark Knight", 2008), ("Inception", 2010), ("Interstellar", 2014), ("Oppenheimer", 2023), ("Memento", 2000),
         ("The Prestige", 2006), ("Parasite", 2019), ("Joker", 2019), ("Whiplash", 2014), ("Fight Club", 1999), ("Se7en", 1995), ("Gone Girl", 2014),
         ("Prisoners", 2013), ("The Shawshank Redemption", 1994), ("Goodfellas", 1990), ("Taxi Driver", 1976), ("No Country for Old Men", 2007), ("Dune: Part Two", 2024),
         ("F1", 2025), ("Mad Max: Fury Road", 2015), ("Top Gun: Maverick", 2022), ("Spider-Man: Across the Spider-Verse", 2023),
         ("Avengers: Endgame", 2019), ("The Matrix", 1999), ("Mission: Impossible – Fallout", 2018)]

# Studios, music labels and TV channels whose uploads count as official (part of a channel name is enough).
OFFICIAL = ["sun tv", "sun pictures", "sony music south", "think music", "saregama", "lahari", "lyca", "red giant", "dream warrior",
            "raaj kamal", "rkfi", "2d entertainment", "studio green", "seven screen", "ags", "kvn", "vels", "wunderbar", "zee music south",
            "u1 records", "divo", "aditya music", "madras talkies", "y not", "passion studios", "think studios", "netflix", "prime video",
            "hotstar", "sun nxt", "trend music", "muzik247", "t-series tamil", "tips tamil", "ayngaran", "pyramid", "star music",
            "vijay television", "kalaignar", "thinkmusicindia", "onlysun", "shemaroo", "mass audios", "v creations", "kalaippuli",
            "grass root", "wunderbar", "y not", "ynot", "lyca", "sri thenandal", "gemini", "ap international", "raaj kamal",
            "kamal haasan", "ayngaran", "sathya jyothi", "escape artists", "fox star", "reliance", "eros", "rajshri tamil",
            "warner bros", "universal pictures", "sony pictures", "paramount", "20th century", "disney", "a24", "neon",
            "lionsgate", "focus features", "searchlight", "mubi", "criterion", "movieclips trailers", "rotten tomatoes trailers"]
BAD = ["reaction", "review", "explained", "breakdown", "fan made", "fanmade", "recreat", "spoof", "behind the scenes", "making of",
       "making video", "public opinion", "whatsapp status", "edit", "mashup", "remix", "status video", "shorts"]


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def pip(*pkgs):
    subprocess.call([sys.executable, "-m", "pip", "install", "--quiet", "--disable-pip-version-check", "--upgrade", *pkgs])


def tools():
    """yt-dlp and an ffmpeg that comes with Python (nothing else to install)."""
    try:
        import yt_dlp  # noqa: F401
        import imageio_ffmpeg  # noqa: F401
    except ImportError:
        print("Getting the download tools (once)...")
        pip("yt-dlp[default]", "imageio-ffmpeg")
    import imageio_ffmpeg
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    cmd = [sys.executable, "-m", "yt_dlp", "--no-warnings", "--ffmpeg-location", ffmpeg]
    deno = shutil.which("deno") or shutil.which("node")
    if deno:
        cmd += ["--js-runtimes", "deno" if "deno" in os.path.basename(deno) else "node"]
    return cmd


def search(cmd, q):
    r = subprocess.run(cmd + ["--flat-playlist", "--dump-single-json", "--skip-download", f"ytsearch10:{q}"], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "").strip().splitlines()[-1][:200] if (r.stderr or "").strip() else "search failed")
    return (json.loads(r.stdout) or {}).get("entries") or []


def find(cmd, film, year):
    """Three searches, from the most exact to the widest; the best official-looking trailer wins."""
    seen = []
    for q in (f"{film} {year} official trailer", f"{film} trailer", f"{film} movie trailer {year}"):
        es = search(cmd, q.strip())
        seen += es
        e, score = pick(film, es)
        if e:
            return e, seen
    return None, seen


NEXT_OK = {"", "official", "trailer", "teaser", "tamil", "movie", "film", "hd", "4k", "2k", "promo", "the", "theatrical", "new",
           "latest", "release", "glimpse", "showcase", "sneak", "full", "telugu", "hindi", "malayalam"}


def names_film(f, t):
    """The title names this film, not a longer one (Vikram, not Vikram Vedha; Jailer, not Jailer 2). Spellings and spacing
    may differ a little: VADACHENNAI, Kaakka Muttai, Subramaniapuram, Nayagan, Thalapathy all count."""
    from difflib import SequenceMatcher
    toks, want = t.split(), f.replace(" ", "")
    for i in range(len(toks)):
        for k in (1, 2, 3):
            if i + k > len(toks):
                break
            got = "".join(toks[i:i + k])
            if got != want and (got.startswith(want) and got[len(want):].isdigit() or abs(len(got) - len(want)) > 2):
                continue                    # a sequel (Jailer 2 for Jailer) or a longer title is not this film
            if got == want or (len(want) >= 6 and SequenceMatcher(None, got, want).ratio() >= 0.84):
                nxt = toks[i + k] if i + k < len(toks) else ""
                if nxt in NEXT_OK or not nxt.isalnum() or re.fullmatch(r"(19|20)\d\d", nxt):
                    return True
    return False


def pick(film, entries):
    """The result whose title names the film and says trailer, from an official channel, of trailer length."""
    f = norm(film)
    best, best_score = None, 0
    for e in entries:
        t, ch = norm(e.get("title")), norm(e.get("channel") or e.get("uploader"))
        d = e.get("duration") or 0
        score = 0
        score += 4 if names_film(f, t) else -10
        score += 2 if ("trailer" in t or "showcase" in t) else (1 if ("teaser" in t or "glimpse" in t) else -4)
        score += 1 if "official" in t else 0
        score += 3 if any(o in ch.replace(" ", "") or o in ch for o in OFFICIAL) else 0
        score -= 6 if any(b in t for b in BAD) else 0
        score -= 5 if d and (d < 40 or d > 360) else 0
        if score > best_score:
            best, best_score = e, score
    return (best if best_score >= 6 else None), best_score


def download(cmd, url, film, vid, out=None):
    out = out or OUT
    name = re.sub(r'[\\/:*?"<>|]+', " ", f"{film} - trailer [{vid}]").strip()
    if any(n.startswith(name) for n in os.listdir(out)):
        return "already there"
    r = subprocess.run(cmd + ["--no-playlist", "-f", "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[height<=720]/b",
                              "--merge-output-format", "mp4", "-o", os.path.join(out, name + ".%(ext)s"), url], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "").strip().splitlines()[-1][:200] if (r.stderr or "").strip() else "download failed")
    return "saved"


def study(urls, out=None, quiet=False):
    """Only the sound of each short, named with its id, for Drive study-audio/ (AGENT.md 10.3)."""
    STUDY = out or STUDY_OUT
    os.makedirs(STUDY, exist_ok=True)
    cmd, ok = tools(), 0
    for i, url in enumerate(urls, 1):
        vid = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{11})", url)
        if vid and any(f"[{vid.group(1)}]" in n for n in os.listdir(STUDY)):
            print(f"[{i}/{len(urls)}] already there")
            ok += 1
            continue
        r = subprocess.run(cmd + ["--no-playlist", "-f", "bestaudio[ext=m4a]/bestaudio", "-o",
                                  os.path.join(STUDY, "%(channel).40s - %(title).60s [%(id)s].%(ext)s"), url], capture_output=True, text=True)
        if r.returncode == 0:
            ok += 1
            print(f"[{i}/{len(urls)}] saved")
        else:
            err = (r.stderr or "").strip().splitlines()
            print(f"[{i}/{len(urls)}] could not get it: {(err[-1] if err else 'download failed')[:160]}")
    if quiet:
        return ok
    print(f"\nDone: {ok} of {len(urls)} in  {STUDY}")
    print("Next: drag every file in that folder into Google Drive > iNiKKi Reels > study-audio. That is all.")
    return ok


def get_trailers(cmd, wanted, out, years):
    """Download each (film, exact link or None); returns (saved films, skipped films, report lines)."""
    os.makedirs(out, exist_ok=True)
    ok, skipped, report = [], [], []
    for i, (film, url) in enumerate(wanted, 1):
        print(f"\n[{i}/{len(wanted)}] {film}")
        try:
            if url:
                vid = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{6,})", url)
                print("  " + download(cmd, url, film, vid.group(1) if vid else "link", out))
                ok.append(film)
                continue
            e, seen = find(cmd, film, years.get(film, ""))
            if not e:
                top = "; ".join(f"{x.get('title')} ({x.get('channel') or x.get('uploader')}, {int(x.get('duration') or 0)} s)" for x in seen[:3])
                print("  No official trailer found; skipped. Top results: " + top[:300])
                report.append(f"{film}: skipped, no official trailer. Top results: {top}")
                skipped.append(film)
                continue
            print(f"  {e.get('title')}  |  channel: {e.get('channel') or e.get('uploader')}  |  {int(e.get('duration') or 0)} s")
            print("  " + download(cmd, e.get("url") or f"https://www.youtube.com/watch?v={e['id']}", film, e["id"], out))
            report.append(f"{film}: {e.get('title')} | {e.get('channel') or e.get('uploader')} | https://www.youtube.com/watch?v={e['id']}")
            ok.append(film)
        except Exception as ex:
            msg = str(ex)
            if "javascript" in msg.lower() or "js runtime" in msg.lower():
                msg += "  (fix: install Node.js from nodejs.org, then run this again)"
            print(f"  Could not get it: {msg}")
            report.append(f"{film}: could not get it: {msg}")
            skipped.append(film)
    if report:
        with open(os.path.join(out, "helper_report.txt"), "a", encoding="utf-8") as fh:      # goes to Drive with the trailers
            fh.write("\n".join(report) + "\n")
    return ok, skipped, report


# ---------------------------------------------------------------- the laptop run (no arguments)
def fetch(path, timeout=30):
    import urllib.request
    req = urllib.request.Request(REPO + path, headers={"User-Agent": "inikki-laptop-helper"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def self_update():
    """Replace this file with the newest helper from the repository, then start again (once)."""
    if os.environ.get("INIKKI_HELPER_UPDATED") or "--no-update" in sys.argv:
        return
    try:
        new = fetch("tools/clip_helper.py")
        me = os.path.abspath(__file__)
        if new and b"def laptop_run" in new and new != open(me, "rb").read():
            with open(me + ".new", "wb") as fh:
                fh.write(new)
            os.replace(me + ".new", me)
            print("The helper updated itself. Starting the new version...")
            os.environ["INIKKI_HELPER_UPDATED"] = "1"
            os.execv(sys.executable, [sys.executable, me] + sys.argv[1:])
    except Exception as e:
        print(f"(Could not check for a newer helper: {str(e)[:80]}. Carrying on with this one.)")


def settings():
    try:
        return json.load(open(SETTINGS, encoding="utf-8"))
    except Exception:
        return {}


def drive_folder():
    """Where Google Drive for desktop keeps the iNiKKi Reels folder, if it is on this computer."""
    s = settings().get("drive_folder")
    if s and os.path.isdir(s):
        return s
    import glob
    import string
    spots = [f"{d}:\\My Drive\\iNiKKi Reels" for d in string.ascii_uppercase[3:]]
    spots += glob.glob(os.path.expanduser("~/Library/CloudStorage/GoogleDrive-*/My Drive/iNiKKi Reels"))
    spots += [os.path.expanduser("~/Google Drive/My Drive/iNiKKi Reels"), os.path.expanduser("~/My Drive/iNiKKi Reels")]
    return next((p for p in spots if os.path.isdir(p)), None)


def song_key(name):
    """The same key the Engine makes (engine/laptop.py song_key)."""
    k = re.sub(r"[^a-z0-9]+", "_", str(name).lower()).strip("_")[:28].strip("_")
    return "song_" + (k or "untitled")


def get_song(cmd, s, out):
    """The audio of one trending song: from its link (YouTube or Instagram), else the best official YouTube audio."""
    key, title = s["key"], s["song"] + (f" ({s['film']})" if s.get("film") else "")
    base = re.sub(r'[\\/:*?"<>|]+', " ", f"song - {key} - {title}").strip()
    if any(n.startswith(base) for n in os.listdir(out)):
        return "already there"
    url = s.get("link")
    if not url:
        r = subprocess.run(cmd + ["--flat-playlist", "--dump-single-json", "--skip-download", f"ytsearch8:{s.get('search') or title} official audio"],
                           capture_output=True, text=True)
        es = (json.loads(r.stdout) or {}).get("entries") or [] if r.returncode == 0 and r.stdout.strip() else []
        want = [w for w in norm(s["song"]).split() if len(w) > 2]
        def score(e):
            t, ch, d = norm(e.get("title")), norm(e.get("channel") or e.get("uploader")), e.get("duration") or 0
            return (3 if all(w in t for w in want) else 0) + (2 if any(o in ch for o in OFFICIAL) else 0) + \
                   (1 if "audio" in t or "lyric" in t else 0) - (4 if any(b in t for b in ("reaction", "cover", "karaoke", "instrumental", "8d")) else 0) - \
                   (3 if d and (d < 60 or d > 480) else 0)
        best = max(es, key=score, default=None)
        if not best or score(best) < 2:
            return "not found on YouTube (add an Instagram or YouTube link for it when the helper asks)"
        url = best.get("url") or f"https://www.youtube.com/watch?v={best['id']}"
    tries = [[]] + ([["--cookies-from-browser", b] for b in ("chrome", "edge", "firefox")] if "instagram.com" in url else [])
    for extra in tries:
        r = subprocess.run(cmd + extra + ["--no-playlist", "-f", "bestaudio[ext=m4a]/bestaudio", "-x", "--audio-format", "m4a",
                                          "-o", os.path.join(out, base + " [%(id)s].%(ext)s"), url], capture_output=True, text=True)
        if r.returncode == 0:
            return "saved"
    err = (r.stderr or "").strip().splitlines()
    return "could not get it: " + ((err[-1] if err else "download failed")[:140])


def ask_songs():
    """Songs Harish heard trending on Instagram this month (optional). Enter on an empty line to finish."""
    if not sys.stdin or not sys.stdin.isatty():
        return []
    print("\nAny song you heard trending on Instagram reels this month? Type its name (and film), or paste an Instagram or")
    print("YouTube link. One per line. Press Enter on an empty line to finish.")
    out = []
    while True:
        try:
            line = input("  song: ").strip()
        except EOFError:
            break
        if not line:
            break
        link = line if line.startswith("https://") else None
        name = line if not link else (re.search(r"/(?:reel|reels/audio|p|shorts)/([\w-]+)", line) or re.search(r"v=([\w-]+)", line) or [None, "link"])[1]
        out.append({"key": song_key(name if not link else "ig " + name), "song": name if not link else "Trending audio " + name,
                    "film": "", "search": name, "link": link})
    return out


def laptop_run():
    self_update()
    print("iNiKKi laptop run: getting the to-do list...")
    try:
        todo = json.loads(fetch("data/laptop/todo.json").decode("utf-8"))
    except Exception as e:
        todo = {}
        print(f"Could not read the to-do list ({str(e)[:80]}). Getting the film-bank trailers and your songs only.")
    os.makedirs(DROP, exist_ok=True)
    cmd, years = tools(), dict(FILMS)
    films = [(t["film"], t.get("url")) for t in todo.get("trailers") or []] + [(f, None) for f in todo.get("topup") or []]
    if not todo:
        films = [(f, None) for f, _ in FILMS]
    print(f"To get: {len(films)} trailers, {len(todo.get('study') or [])} shorts to study, {len(todo.get('songs') or [])} trending songs.")
    got_t, skipped, _ = get_trailers(cmd, films, DROP, years) if films else ([], [], [])
    got_s = study(todo.get("study") or [], DROP, quiet=True) if todo.get("study") else 0
    songs = list(todo.get("songs") or []) + ask_songs()
    got_m = 0
    for k, s in enumerate(songs, 1):
        res = get_song(cmd, s, DROP)
        print(f"[song {k}/{len(songs)}] {s['song']}: {res}")
        got_m += res in ("saved", "already there")
    files = [f for f in os.listdir(DROP) if os.path.isfile(os.path.join(DROP, f))]
    print(f"\nDone: {len(got_t)} trailers, {got_s} shorts, {got_m} songs ({len(files)} files in {DROP}).")
    if skipped:
        print("Trailers not found: " + ", ".join(skipped))
    dest = drive_folder()
    if dest and files:
        target = os.path.join(dest, "from-laptop")
        os.makedirs(target, exist_ok=True)
        for f in files:
            shutil.copy2(os.path.join(DROP, f), os.path.join(target, f))
        print(f"Copied into Google Drive: {target}")
        print("Nothing to drag. Wait until Google Drive for desktop finishes uploading, then press Done on the Manual work tab.")
        for f in files:                                    # the copies are in Drive now; keep the folder small for next time
            if not f.endswith(".txt"):
                os.remove(os.path.join(DROP, f))
    elif files:
        print("Next: drag every file in the folder  for_drive  into Google Drive > iNiKKi Reels > from-laptop,")
        print("then press Done on the Control Room's Manual work tab. The Engine sorts them by itself.")
        print('(Tip: if Google Drive for desktop is on this computer, run once: py clip_helper.py --drive "G:\\My Drive\\iNiKKi Reels")')


def main():
    if "--drive" in sys.argv:
        k = sys.argv.index("--drive")
        path = sys.argv[k + 1] if k + 1 < len(sys.argv) else ""
        if not os.path.isdir(path):
            print(f"That folder does not exist on this computer: {path}")
            return
        json.dump({**settings(), "drive_folder": path}, open(SETTINGS, "w", encoding="utf-8"))
        print(f"Saved. The laptop run will copy its files into {os.path.join(path, 'from-laptop')}.")
        del sys.argv[k:k + 2]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--study" in sys.argv:
        return study([x for x in args if x.startswith("http")])
    if not args and "--film-bank" not in sys.argv:
        return laptop_run()
    years = dict(FILMS)
    wanted = [(a.split("=", 1)[0].strip(), a.split("=", 1)[1].strip()) if "=http" in a else (a.strip(), None) for a in args] or [(f, None) for f, _ in FILMS]
    ok, skipped, _ = get_trailers(tools(), wanted, OUT, years)
    print(f"\nDone: {len(ok)} of {len(wanted)} trailers are in  {OUT}")
    if skipped:
        print("Skipped: " + ", ".join(skipped))
    print("Next: drag every file in that folder (helper_report.txt too) into Google Drive > iNiKKi Reels > clip-library. That is all.")


if __name__ == "__main__":
    main()
