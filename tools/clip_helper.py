#!/usr/bin/env python3
"""iNiKKi trailer helper, for your own computer. It downloads the official trailers for the breakdown library.

Windows (once):
  1. Install Python from python.org/downloads (on the first screen, tick "Add python.exe to PATH").
  2. Put this file in a folder, for example Downloads.
  3. Open that folder, click the address bar at the top, type  cmd  and press Enter.
  4. Type  py clip_helper.py  and press Enter. Leave it running (about 30 to 40 minutes, it works by itself).
  5. Open the new folder  trailers_for_drive  and drag every file in it into
     Google Drive > iNiKKi Reels > clip-library. The Engine makes the shot grids by itself.
Mac: in Terminal, type  python3 clip_helper.py  in the folder with this file.

Other uses:
  py clip_helper.py "Leo" "Amaran"                  only these films
  py clip_helper.py "Leo=https://www.youtube.com/watch?v=..."   one exact video for a film

It keeps only trailers whose title names the film and that come from an official channel (it prints each channel).
Running it again skips the files already in trailers_for_drive.
"""
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "trailers_for_drive")

# The film bank (niches/tamil-cinema/knowledge/film_bank.json), copied here so this file works on its own.
FILMS = [("Kaithi", 2019), ("Jigarthanda", 2014), ("Ratsasan", 2018), ("Vikram", 2022), ("Vada Chennai", 2018), ("Super Deluxe", 2019),
         ("Aaranya Kaandam", 2011), ("Visaranai", 2016), ("Pariyerum Perumal", 2018), ("Asuran", 2019), ("Soorarai Pottru", 2020),
         ("Jai Bhim", 2021), ("Maharaja", 2024), ("Viduthalai Part 1", 2023), ("Mandela", 2021), ("Karnan", 2021), ("Nayakan", 1987),
         ("Thalapathi", 1991), ("Mouna Ragam", 1986), ("Pudhupettai", 2006), ("Subramaniyapuram", 2008), ("Aadukalam", 2011), ("96", 2018),
         ("Vikram Vedha", 2017), ("Thani Oruvan", 2015), ("Kaaka Muttai", 2015), ("Soodhu Kavvum", 2013), ("Pizza", 2012),
         ("Anbe Sivam", 2003), ("Virumaandi", 2004), ("Kuruthipunal", 1995), ("Mahanadhi", 1994), ("Leo", 2023), ("Jailer", 2023),
         ("Amaran", 2024), ("Maaveeran", 2023), ("Master", 2021), ("Lubber Pandhu", 2024)]

# Studios, music labels and TV channels whose uploads count as official (part of a channel name is enough).
OFFICIAL = ["sun tv", "sun pictures", "sony music south", "think music", "saregama", "lahari", "lyca", "red giant", "dream warrior",
            "raaj kamal", "rkfi", "2d entertainment", "studio green", "seven screen", "ags", "kvn", "vels", "wunderbar", "zee music south",
            "u1 records", "divo", "aditya music", "madras talkies", "y not", "passion studios", "think studios", "netflix", "prime video",
            "hotstar", "sun nxt", "trend music", "muzik247", "t-series tamil", "tips tamil", "ayngaran", "pyramid", "star music",
            "vijay television", "kalaignar", "thinkmusicindia", "onlysun", "shemaroo", "mass audios"]
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


def search(cmd, film, year):
    q = f"ytsearch8:{film} {year} official trailer"
    r = subprocess.run(cmd + ["--flat-playlist", "--dump-single-json", "--skip-download", q], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "").strip().splitlines()[-1][:200] if (r.stderr or "").strip() else "search failed")
    return (json.loads(r.stdout) or {}).get("entries") or []


NEXT_OK = {"", "official", "trailer", "teaser", "tamil", "movie", "film", "hd", "4k", "2k", "promo", "the", "theatrical", "new",
           "latest", "release", "glimpse", "showcase", "sneak", "full", "telugu", "hindi", "malayalam"}


def names_film(f, t):
    """The title names this film, not a longer one (Vikram, not Vikram Vedha; Jailer, not Jailer 2)."""
    m = re.search(rf"(^| ){re.escape(f)}( |$)", t)
    if not m:
        return False
    rest = t[m.end():].split()
    return (rest[0] if rest else "") in NEXT_OK


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
        score += 3 if any(o in ch for o in OFFICIAL) else -2
        score -= 6 if any(b in t for b in BAD) else 0
        score -= 5 if d and (d < 40 or d > 360) else 0
        if score > best_score:
            best, best_score = e, score
    return best if best_score >= 6 else None


def download(cmd, url, film, vid):
    name = re.sub(r'[\\/:*?"<>|]+', " ", f"{film} - trailer [{vid}]").strip()
    if any(n.startswith(name) for n in os.listdir(OUT)):
        return "already there"
    r = subprocess.run(cmd + ["--no-playlist", "-f", "bv*[height<=720][ext=mp4]+ba[ext=m4a]/b[height<=720][ext=mp4]/b[height<=720]/b",
                              "--merge-output-format", "mp4", "-o", os.path.join(OUT, name + ".%(ext)s"), url], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or "").strip().splitlines()[-1][:200] if (r.stderr or "").strip() else "download failed")
    return "saved"


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    years = dict(FILMS)
    wanted = [(a.split("=", 1)[0].strip(), a.split("=", 1)[1].strip()) if "=http" in a else (a.strip(), None) for a in args] or [(f, None) for f, _ in FILMS]
    os.makedirs(OUT, exist_ok=True)
    cmd = tools()
    ok, skipped = [], []
    for i, (film, url) in enumerate(wanted, 1):
        print(f"\n[{i}/{len(wanted)}] {film}")
        try:
            if url:
                vid = re.search(r"(?:v=|youtu\.be/|shorts/)([\w-]{6,})", url)
                print("  " + download(cmd, url, film, vid.group(1) if vid else "link"))
                ok.append(film)
                continue
            e = pick(film, search(cmd, film, years.get(film, "")))
            if not e:
                print("  No official trailer found in the first results; skipped.")
                skipped.append(film)
                continue
            print(f"  {e.get('title')}  |  channel: {e.get('channel') or e.get('uploader')}  |  {int(e.get('duration') or 0)} s")
            print("  " + download(cmd, e.get("url") or f"https://www.youtube.com/watch?v={e['id']}", film, e["id"]))
            ok.append(film)
        except Exception as ex:
            msg = str(ex)
            if "javascript" in msg.lower() or "js runtime" in msg.lower():
                msg += "  (fix: install Node.js from nodejs.org, then run this again)"
            print(f"  Could not get it: {msg}")
            skipped.append(film)
    print(f"\nDone: {len(ok)} of {len(wanted)} trailers are in  {OUT}")
    if skipped:
        print("Skipped: " + ", ".join(skipped))
    print("Next: drag every file in that folder into Google Drive > iNiKKi Reels > clip-library. That is all.")


if __name__ == "__main__":
    main()
