"""Visual and sound assets for one reel (AGENT.md 5.3, 5.4; archive 11).

Every visual in a plan becomes something the template can show:
  image  → a file path (AI image from OpenAI, or the image library in Drive)
  clip   → a folder of frames cut from a trailer in Drive clip-library/ (+ its sound)
  meme   → the same, from Drive meme-bank/ (by mood, from the meme index)
  still  → a brand card with the film name (the fallback when a clip is missing)
In --local mode (no keys, no Drive) placeholders are drawn so templates can be tested anywhere.
"""
import csv
import hashlib
import json
import os
import re
import shutil
import subprocess

from .settings import ENGINE, ROOT, niche_dir, secret
from . import status

FPS = 30


def _ffmpeg():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def _run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout).strip().splitlines()[-1][:300] if (r.stderr or r.stdout).strip() else "ffmpeg failed")
    return r


def norm(s):
    return re.sub(r"[^a-z0-9]+", " ", str(s or "").lower()).strip()


def media_duration(path):
    r = subprocess.run([_ffmpeg().replace("ffmpeg", "ffprobe") if shutil.which("ffprobe") else "ffprobe", "-v", "error",
                        "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


class Assets:
    def __init__(self, work_dir, reel_id, drive=None, local=False, budget=None, series=None):
        self.work = str(work_dir)
        self.reel_id = reel_id
        self.drive = drive
        self.local = local or drive is None
        self.budget = budget
        self.series = series or {}
        self.notes = []       # plain-language notes about fallbacks used
        self.images_made = 0
        self.compose = ""     # where the subject should sit so the template's words never cover it (set per template)
        os.makedirs(self.work, exist_ok=True)

    # ---------------------------------------------------------------- images
    def image(self, spec, n, style_default=None, cap=None):
        """spec: {prompt|subject, style, reuse?}. Returns {"src": path, "source": "openai|library|placeholder"}."""
        subject = spec.get("prompt") or spec.get("subject") or "Tamil cinema scene"
        style = spec.get("style") or style_default
        out = os.path.join(self.work, f"image_{n:02d}.png")
        if self.local or not secret("OPENAI_API_KEY"):
            real = os.path.join(os.environ.get("INIKKI_LOCAL_IMAGES", ""), f"{self.reel_id}_{n:02d}.jpg")
            if os.environ.get("INIKKI_LOCAL_IMAGES") and os.path.exists(real):     # template work with real pictures, offline
                return {"src": real, "source": "placeholder", "style": style}
            self._placeholder(out, subject, style, n)
            return {"src": out, "source": "placeholder", "style": style}
        saved = None if spec.get("fresh") else self._made_before(n, out)
        if saved:                      # same plan, same reel: the picture made for this reel is used again, at no cost
            return {"src": saved, "source": "library", "style": style, "reused": True}
        if spec.get("find") or spec.get("trailer"):      # the free steps first (AGENT.md 5.9); an AI image only if they find nothing
            from . import sources
            self.library = getattr(self, "library", None) or sources.Library(self.drive)
            got = sources.find(spec, n, self.reel_id, self.work, drive=self.drive, library=self.library, film=spec.get("film"))
            if got:
                self.notes.append(f"Picture {n}: found without AI ({got['source']}).")
                if self.drive:
                    try:
                        self.drive.upload(got["src"], "image-library", name=f"{self.reel_id}_{n:02d}.png")     # so a re-render uses the same picture
                    except Exception:
                        pass
                return {"src": got["src"], "source": got["source"], "style": style, "credit": got.get("credit")}
            if spec.get("ai") is False:
                self.notes.append(f"Picture {n}: nothing free was found for '{spec.get('find')}', and this picture may not be made by AI. A card was used.")
                self._placeholder(out, subject, style, n)
                return {"src": out, "source": "placeholder", "style": style}
        if cap is not None and self.images_made >= cap:
            self.notes.append(f"Image {n}: the series cap of {cap} images was reached, a library image or a card was used instead.")
            lib = self._library_image(subject)
            if lib:
                return {"src": lib, "source": "library", "style": style}
            self._placeholder(out, subject, style, n)
            return {"src": out, "source": "placeholder", "style": style}
        from . import images
        r = images.generate(subject + ". " + self.compose if self.compose else subject, style, purpose=f"reel {self.reel_id}", reel_id=self.reel_id, out_path=out, budget=self.budget, drive=self.drive)
        if r.get("ok"):
            self.images_made += 1
            self._upscale(out)
            try:                       # remember it in the library index, so a later reel can reuse it instead of paying again
                from . import sources
                self.library = getattr(self, "library", None) or sources.Library(self.drive)
                self.library.items = [i for i in self.library.items if i.get("file") != f"{self.reel_id}_{n:02d}.png"] + [{"file": f"{self.reel_id}_{n:02d}.png", "source": "ai", "tags": sorted(sources.words(spec.get("find") or subject)), "film": spec.get("film"), "query": subject[:200], "style": style}]
            except Exception:
                pass
            if self.drive:
                try:
                    self.drive.upload(out, "image-library", name=f"{self.reel_id}_{n:02d}.png")
                    self.drive.write_json("image-library", "index.json", {"images": self.library.items})
                except Exception as e:
                    self.notes.append(f"Image {n} could not be saved to the image library: {e}")
            return {"src": out, "source": "openai", "model": r.get("model"), "cost_inr": r.get("cost_inr"), "style": style}
        self.notes.append(f"Image {n}: {r.get('error', 'no image')}. A library image or a card was used instead.")
        lib = self._library_image(subject)
        if lib:
            return {"src": lib, "source": "library", "style": style}
        self._placeholder(out, subject, style, n)
        return {"src": out, "source": "placeholder", "style": style}

    def _made_before(self, n, out):
        if not self.drive:
            return None
        try:
            fid = self.drive.folder("image-library", create=False)
            f = self.drive.find_child(fid, f"{self.reel_id}_{n:02d}.png") if fid else None
            return self.drive.download(f["id"], out) if f else None
        except Exception:
            return None

    def _library_image(self, subject):
        if not self.drive:
            return None
        try:
            fid = self.drive.folder("image-library", create=False)
            items = [i for i in (self.drive.children(fid) if fid else []) if i.get("mimeType", "").startswith("image/")]
        except Exception:
            return None
        if not items:
            return None
        words = set(norm(subject).split())
        best = max(items, key=lambda i: len(words & set(norm(i["name"]).split())))
        out = os.path.join(self.work, "lib_" + best["name"])
        self.drive.download(best["id"], out)
        return out

    @staticmethod
    def _upscale(path):
        """1024x1536 → 1080x1620 cover (the template crops to 1080x1920 anyway); keeps the file small."""
        try:
            from PIL import Image
            im = Image.open(path).convert("RGB")
            if im.width < 1080:
                im = im.resize((1080, round(im.height * 1080 / im.width)), Image.LANCZOS)
                im.save(path)
        except Exception:
            pass

    def _placeholder(self, out, subject, style, n):
        """A deterministic stand-in image (only for local tests): soft gradient + a dim label."""
        from PIL import Image, ImageDraw, ImageFilter
        h = int(hashlib.md5(f"{self.reel_id}:{n}:{subject}".encode()).hexdigest(), 16)
        pal = {"painterly_warm": ((40, 22, 10), (235, 160, 60)), "cinematic_real": ((8, 10, 20), (90, 120, 150)),
               "arcane_painterly": ((10, 30, 40), (120, 224, 208)), "diorama_moody": ((12, 14, 30), (120, 90, 200))}.get(style, ((10, 15, 24), (33, 25, 55)))
        W, H = 1080, 1620
        im = Image.new("RGB", (W, H), pal[0])
        d = ImageDraw.Draw(im)
        for y in range(H):
            k = y / H
            d.line([(0, y), (W, y)], fill=tuple(int(pal[0][i] * (1 - k) + pal[1][i] * k * 0.8) for i in range(3)))
        rnd = lambda i: ((h >> (i * 7)) % 1000) / 1000
        for i in range(6):   # a few soft shapes so push-ins and parallax are visible
            cx, cy, r = int(rnd(i) * W), int(rnd(i + 6) * H), int(120 + rnd(i + 12) * 320)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=tuple(min(255, int(c * (0.6 + rnd(i + 18)))) for c in pal[1]))
        im = im.filter(ImageFilter.GaussianBlur(14))
        d = ImageDraw.Draw(im)
        d.rectangle([0, H - 60, W, H], fill=(0, 0, 0))
        d.text((20, H - 48), f"placeholder {n}: {subject[:70]}", fill=(140, 140, 140))
        im.save(out)
        return out

    # ---------------------------------------------------------------- clips and memes
    def clip(self, spec, n, length=None):
        """spec: {film, query, start, len, file?, audio?, reference?, crop?}. Returns a frames visual or a still fallback."""
        length = float(length or spec.get("len") or 3.0)
        src, crop = None, None
        if self.local:
            src = self._local_test_video(spec, n, length)
        elif spec.get("reference"):     # build-time only: a moment from one of Harish's own reference reels
            src, crop = self._reference_reel(spec["reference"]), spec.get("crop")
        else:
            src = self._clip_from_library(spec)
        if not src:
            self.notes.append(f"Clip {n} ({spec.get('film', '')}: {spec.get('query', '')}): no file in clip-library/, a still card was used.")
            return self.still(spec.get("film") or spec.get("query") or "", n, kind="clip")
        start = 0 if self.local else spec.get("start")
        if start is None:
            total = media_duration(src)
            h = int(hashlib.md5(f"{self.reel_id}:{n}".encode()).hexdigest(), 16)
            start = round(5 + (h % 1000) / 1000 * max(0.0, total - length - 10), 1) if total > length + 10 else 0
        try:
            return self._frames_from(src, float(start), length, n, label=spec.get("label"), audio=bool(spec.get("audio")), crop=crop)
        except RuntimeError as e:      # one bad clip never stops the reel (fail soft): a still card takes its place
            self.notes.append(f"Clip {n} ({spec.get('film', '')}) could not be cut ({e}); a still card was used.")
            return self.still(spec.get("film") or spec.get("query") or "", n, kind="clip")

    def _reference_reel(self, name):
        local = os.path.join(self.work, "ref_" + re.sub(r"[^\w.]+", "_", name))
        if os.path.exists(local):
            return local
        try:
            fid = self.drive.folder("reference-reels", create=False)
            f = self.drive.find_child(fid, name) if fid else None
            return self.drive.download(f["id"], local) if f else None
        except Exception as e:
            self.notes.append(f"Reference reel '{name}' could not be fetched: {e}")
            return None

    def meme(self, spec, n, length=None):
        """spec: {mood, file?, len?}. Picks from the meme index by mood; trims long memes to the punchline (the end)."""
        rows = []
        try:
            with open(niche_dir() / "memes" / "meme_index.csv", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
        except FileNotFoundError:
            pass
        want = norm(spec.get("mood"))
        pick = None
        if spec.get("file"):
            pick = next((r for r in rows if r["file"] == spec["file"]), {"file": spec["file"], "seconds": "0"})
        elif want:
            cands = [r for r in rows if want in norm(r.get("moods", "")) or want in norm(r.get("good_for", ""))]
            cands = [r for r in cands if not r.get("duplicate_of")] or cands
            if cands:
                h = int(hashlib.md5(f"{self.reel_id}:meme".encode()).hexdigest(), 16)
                pick = cands[h % len(cands)]
        if not pick:
            self.notes.append(f"Meme for mood '{spec.get('mood')}' not found in the meme index; the mascot end card was used.")
            return {"type": "mascot"}
        secs = float(pick.get("seconds") or 0)
        length = float(length or spec.get("len") or min(3.5, secs or 3.5))
        src = None
        if self.local:
            src = self._local_test_video({"query": pick["file"]}, n, length, meme=True)
        elif self.drive:
            try:
                fid = self.drive.folder("meme-bank", create=False)
                f = self.drive.find_child(fid, pick["file"]) if fid else None
                if f:
                    src = self.drive.download(f["id"], os.path.join(self.work, "meme_src.mp4"))
            except Exception as e:
                self.notes.append(f"Meme file could not be fetched: {e}")
        if not src:
            self.notes.append(f"Meme '{pick['file']}' is not in Drive meme-bank/; the mascot end card was used.")
            return {"type": "mascot"}
        total = media_duration(src) or secs
        start = max(0.0, total - length) if total > 4 else 0.0       # the punchline is at the end
        v = self._frames_from(src, start, min(length, total or length), n, label=None, audio=True)
        v["type"] = "meme"
        v["meme"] = pick["file"]
        return v

    def _clip_from_library(self, spec):
        if not self.drive:
            return None
        try:
            fid = self.drive.folder("clip-library", create=False)
            items = []
            for it in (self.drive.children(fid) if fid else []):
                if it["mimeType"] == "application/vnd.google-apps.folder":
                    items += [(it["name"] + " " + k["name"], k) for k in self.drive.children(it["id"]) if k.get("mimeType", "").startswith("video/")]
                elif it.get("mimeType", "").startswith("video/"):
                    items.append((it["name"], it))
        except Exception as e:
            self.notes.append(f"clip-library/ could not be read: {e}")
            return None
        if spec.get("file"):
            hit = next((k for name, k in items if k["name"] == spec["file"]), None)
        else:
            film = norm(spec.get("film"))
            words = set((film + " " + norm(spec.get("query"))).split())
            scored = sorted(items, key=lambda x: (-(film and film in norm(x[0])), -len(words & set(norm(x[0]).split()))))
            hit = scored[0][1] if scored and (film and film in norm(scored[0][0])) else None
        if not hit:
            return None
        return self.drive.download(hit["id"], os.path.join(self.work, "clip_" + re.sub(r"[^\w.]+", "_", hit["name"])))

    def _frames_from(self, src, start, length, n, label=None, audio=False, crop=None):
        d = os.path.join(self.work, f"frames_{n:02d}")
        if os.path.isdir(d):
            shutil.rmtree(d)
        os.makedirs(d)
        cropf = f"crop={crop[2]}:{crop[3]}:{crop[0]}:{crop[1]}," if crop else ""
        _run([_ffmpeg(), "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", src,
              "-vf", f"{cropf}fps={FPS},scale=1080:-2:flags=lanczos", "-q:v", "3", os.path.join(d, "f%04d.jpg")])
        count = len([f for f in os.listdir(d) if f.endswith(".jpg")])
        if not count:
            raise RuntimeError(f"no frames could be cut from {os.path.basename(src)} at {start:.1f}s")
        out = {"type": "clip", "frames": {"dir": "file://" + d, "count": count, "fps": FPS, "ext": "jpg"}, "label": label, "src_file": os.path.basename(src), "start": start, "len": length}
        if audio:
            a = os.path.join(self.work, f"audio_{n:02d}.m4a")
            try:
                _run([_ffmpeg(), "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{length:.3f}", "-i", src, "-vn", "-c:a", "aac", "-b:a", "160k", a])
                out["audio"] = a
            except RuntimeError:
                pass
        return out

    def _local_test_video(self, spec, n, length, meme=False):
        """A short test video drawn by ffmpeg (moving bars + a label) so clip handling can be tested without Drive."""
        p = os.path.join(self.work, f"testclip_{n:02d}.mp4")
        label = (spec.get("film") or spec.get("query") or "clip")[:30].replace("'", "").replace(":", " ")
        col = "0x3a2a6a" if not meme else "0x6a2a2a"
        _run([_ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc2=size=1280x720:rate=30:duration={length + 1:.1f}",
              "-f", "lavfi", "-i", f"sine=frequency={220 if not meme else 440}:duration={length + 1:.1f}",
              "-vf", f"hue=s=0.3,colorbalance=rs=0.1,drawbox=0:0:1280:720:{col}@0.35:t=fill,drawtext=text='{label}':x=(w-tw)/2:y=(h-th)/2:fontsize=64:fontcolor=white",
              "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", p])
        return p

    def still(self, text, n, kind="clip"):
        """Brand card used when a clip is missing: the film name on the card background (no fake footage)."""
        return {"type": "none", "label": text, "fallback": kind}

    # ---------------------------------------------------------------- music
    def music(self, mood, series_id, length_s, track=None):
        """One track from Drive music/ by mood (file-name keywords), else a seeded pick. Locally: a synthesized bed.
        `track` pins an exact file name (used by tests and by the learning loop when a track is proven)."""
        out = os.path.join(self.work, "music_src.mp3")
        if self.local or not self.drive:
            self._synth_bed(out, mood, length_s)
            return {"path": out, "name": f"synthesized bed ({mood})", "source": "local"}
        try:
            fid = self.drive.music_folder()
            tracks = [i for i in (self.drive.children(fid) if fid else []) if i.get("mimeType", "").startswith("audio/")]
        except Exception as e:
            self.notes.append(f"Music folder could not be read ({e}); a synthesized bed was used.")
            self._synth_bed(out, mood, length_s)
            return {"path": out, "name": "synthesized bed", "source": "local"}
        if not tracks:
            self._synth_bed(out, mood, length_s)
            return {"path": out, "name": "synthesized bed (music folder empty)", "source": "local"}
        picked = self._from_index(mood, series_id, length_s, track)          # the music index first (engine/music_index.py)
        if picked:
            try:
                self.drive.download(picked["id"], out)
                return {"path": out, "name": picked["name"], "source": "drive", "matched_mood": True, "score": picked.get("moods", {}).get(mood)}
            except Exception as e:
                self.notes.append(f"Music track '{picked['name']}' could not be fetched ({e}); another was picked.")
        words = (ENGINE.get("music", {}).get("mood_words", {}) or {}).get(mood, [])
        clean = lambda name: re.sub(r"masstamilan\s*\w*", " ", norm(name))          # site tags in file names are not mood words
        hits = [t for t in tracks if any(w in clean(t["name"]).split() or (len(w) > 5 and w in clean(t["name"])) for w in words)]
        pinned = [t for t in tracks if track and t["name"] == track]
        pool = pinned or hits or tracks
        h = int(hashlib.md5(f"{self.reel_id}:{series_id}:music".encode()).hexdigest(), 16)
        pick = pool[h % len(pool)]
        try:
            self.drive.download(pick["id"], out)
        except Exception as e:
            self.notes.append(f"Music track '{pick['name']}' could not be fetched ({e}); a synthesized bed was used.")
            self._synth_bed(out, mood, length_s)
            return {"path": out, "name": "synthesized bed", "source": "local"}
        return {"path": out, "name": pick["name"], "source": "drive", "matched_mood": bool(hits)}

    def _from_index(self, mood, series_id, length_s, track=None):
        """Best tracks for the mood from the music index; not the same track twice in a series within 7 days;
        retired (muted) tracks never. A seeded pick among the top few keeps reels varied and repeatable."""
        try:
            fid = self.drive.music_folder()
            f = self.drive.find_child(fid, "index.json") if fid else None
            if not f:
                return None
            idx = json.loads(self.drive.read_bytes(f["id"]).decode("utf-8"))
        except Exception:
            return None
        tracks = [t for t in idx.get("tracks", []) if t.get("moods") and not t.get("retired")]
        if track:
            return next((t for t in tracks if t["name"] == track), None)
        import datetime as dt
        week_ago = (status.now() - dt.timedelta(days=7)).strftime("%Y-%m-%d")
        recent = lambda t: any(u.get("series") == series_id and u.get("at", "") >= week_ago and u.get("reel") != self.reel_id for u in t.get("uses", []))
        fits = lambda t: (t.get("seconds") or 0) >= min(40.0, length_s * 0.7)
        pool = sorted([t for t in tracks if not recent(t) and fits(t)] or tracks, key=lambda t: -t["moods"].get(mood, 0))[:6]
        if not pool:
            return None
        h = int(hashlib.md5(f"{self.reel_id}:{series_id}:music".encode()).hexdigest(), 16)
        pick = pool[h % min(3, len(pool))]
        try:                                   # remember the use, so the same track is not repeated in this series this week
            if not any(u.get("reel") == self.reel_id for u in pick.get("uses", [])):
                pick.setdefault("uses", []).append({"series": series_id, "reel": self.reel_id, "at": status.now().strftime("%Y-%m-%d")})
                pick["uses"] = pick["uses"][-30:]
                from googleapiclient.http import MediaInMemoryUpload
                media = MediaInMemoryUpload(json.dumps(idx, ensure_ascii=False, indent=1).encode("utf-8"), mimetype="application/json")
                self.drive.svc.files().update(fileId=f["id"], media_body=media, supportsAllDrives=True).execute(num_retries=3)
        except Exception:
            pass
        return pick

    def _synth_bed(self, out, mood, length_s):
        freq = {"tension_pulse": 55, "upbeat_percussive": 110, "emotional_build": 65, "suspense_ticks": 58, "stinger": 80, "soft_warm": 72, "confident_mid": 98}.get(mood, 60)
        dur = max(10, int(length_s) + 2)
        _run([_ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration={dur}",
              "-f", "lavfi", "-i", f"sine=frequency={freq * 1.5:.1f}:duration={dur}",
              "-f", "lavfi", "-i", f"anoisesrc=color=brown:amplitude=0.08:duration={dur}:seed=7",
              "-filter_complex", "[0:a]volume=0.35[a];[1:a]volume=0.12,tremolo=f=2:d=0.6[b];[2:a]lowpass=f=400[c];[a][b][c]amix=inputs=3:normalize=0,volume=0.9", "-c:a", "libmp3lame", "-q:a", "4", out])
        return out
