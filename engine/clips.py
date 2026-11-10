"""Clips from official trailers and promos (AGENT.md 5.3, archive 11.1). Fetched by code with yt-dlp."""
import json
import os
import shutil
import subprocess

from .settings import ENGINE, OUT


def _ffmpeg():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def _ytdlp():
    exe = shutil.which("yt-dlp")
    return [exe] if exe else ["python", "-m", "yt_dlp"]


def _supports(flag):
    try:
        h = subprocess.run(_ytdlp() + ["--help"], capture_output=True, text=True, timeout=60).stdout
        return flag in h
    except Exception:
        return False


def lookup(query_or_url, timeout=90):
    """Metadata only: id, title, channel, duration, url."""
    cmd = _ytdlp() + ["--dump-single-json", "--no-playlist", "--skip-download", "--no-warnings", query_or_url]
    if _supports("--js-runtimes"):
        cmd[1:1] = ["--js-runtimes", "node"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 and "not a bot" in (r.stderr or ""):
        # second try with another player client, which sometimes passes on cloud computers
        r = subprocess.run(cmd[:1] + ["--extractor-args", "youtube:player_client=tv,android_vr"] + cmd[1:],
                           capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip().splitlines()[-1][:300] if (r.stderr or r.stdout).strip() else "yt-dlp failed")
    j = json.loads(r.stdout)
    if j.get("entries"):
        j = j["entries"][0]
    return {"id": j.get("id"), "title": j.get("title"), "channel": j.get("channel") or j.get("uploader"),
            "duration": j.get("duration"), "url": j.get("webpage_url") or j.get("original_url")}


def fetch(query_or_url, start_s, length_s, out_path, timeout=300):
    """Download one short section. Returns the path, or raises with a plain reason."""
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    h = ENGINE["clips"]["max_height"]
    cmd = _ytdlp() + [
        "--no-playlist", "--no-warnings", "--quiet",
        "-f", f"bv*[height<={h}][ext=mp4]+ba[ext=m4a]/b[height<={h}][ext=mp4]/b[height<={h}]",
        "--download-sections", f"*{start_s}-{start_s + length_s}", "--force-keyframes-at-cuts",
        "--merge-output-format", "mp4", "--ffmpeg-location", os.path.dirname(_ffmpeg()),
        "-o", out_path, query_or_url]
    if _supports("--js-runtimes"):
        cmd[1:1] = ["--js-runtimes", "node"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if r.returncode != 0 or not os.path.exists(out_path):
        msg = (r.stderr or r.stdout).strip().splitlines()
        raise RuntimeError(msg[-1][:300] if msg else "download failed")
    return out_path


def duration(path):
    r = subprocess.run([_ffmpeg().replace("ffmpeg", "ffprobe") if shutil.which("ffprobe") else _ffmpeg(), "-v", "error",
                        "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return round(float(r.stdout.strip()), 2)
    except ValueError:
        return None


def contact_sheet(video, out_png, cols=None, rows=None, width=None):
    """One image with a grid of frames and timestamps, so the Brain picks moments from a single picture."""
    c = ENGINE["clips"]["contact_sheet"]
    cols, rows, width = cols or c["cols"], rows or c["rows"], width or c["width"]
    d = duration(video) or 60
    n = cols * rows
    step = max(d / n, 0.5)
    tile_w = width // cols
    font = next((f for f in ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf"] if os.path.exists(f)), None)
    draw = f",drawtext=fontfile={font}:text='%{{pts\\:hms}}':x=8:y=8:fontsize=28:fontcolor=white:box=1:boxcolor=black@0.6" if font else ""
    vf = f"fps=1/{step:.3f},scale={tile_w}:-2{draw},tile={cols}x{rows}:padding=4:margin=4"
    os.makedirs(os.path.dirname(out_png) or ".", exist_ok=True)
    r = subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", video, "-vf", vf, "-frames:v", "1", out_png],
                       capture_output=True, text=True, timeout=300)
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip()[-300:])
    return out_png
