"""Render one reel from its plan (AGENT.md 5 stage 7, archive 13).

    python -m engine.render plans/reference/kaithi-breakdown.json --local          # placeholders, no keys needed
    python -m engine.render <plan.json> --snap 0,1.2,6.5 --local                  # just a few frames as PNG, to look at
    python -m engine.render <plan.json> --to-drive rehearsal/phase2               # real assets, upload the result

Templates are HTML pages (templates/<name>/index.html). Each frame is a pure function of time, drawn by headless
Chromium and piped to ffmpeg, so the same plan always gives the same reel (CLAUDE.md rule 2).
Output: out/reels/<reel_id>/{reel.mp4, cover.jpg, plan_resolved.json, qc.json, notes.md}
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time

from .settings import ENGINE, OUT, ROOT, load_yaml, niche_dir, secret
from .brandkit import kit
from . import status

FPS = 30
W, H = 1080, 1920


def _ffmpeg():
    return shutil.which("ffmpeg") or __import__("imageio_ffmpeg").get_ffmpeg_exe()


def series_for(plan):
    sid = plan.get("series")
    p = niche_dir() / "series" / str(sid) / "series.yaml"
    return load_yaml(p.relative_to(ROOT)) if sid and p.exists() else {}


# ---------------------------------------------------------------- the browser
class Frames:
    """Headless Chromium that draws template frames on demand."""

    def __init__(self, template, debug_safe=False):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        exe = os.environ.get("CHROMIUM_PATH") or ("/opt/pw-browsers/chromium" if os.path.exists("/opt/pw-browsers/chromium") else None)
        args = ["--disable-gpu", "--hide-scrollbars", "--font-render-hinting=none", "--disable-lcd-text", "--allow-file-access-from-files"]
        try:
            self.browser = self._pw.chromium.launch(executable_path=exe, args=args) if exe else self._pw.chromium.launch(args=args)
        except Exception:
            self.browser = self._pw.chromium.launch(channel="chrome", args=args)
        self.page = self.browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        self.page.goto((ROOT / "templates" / template / "index.html").as_uri())
        if debug_safe:
            self.page.evaluate("window.DEBUG_SAFE = true")

    def setup(self, plan, brand):
        return self.page.evaluate("([p, b]) => window.setup(p, b)", [plan, brand])

    def frame(self, t, fmt="jpeg"):
        self.page.evaluate("t => window.renderFrame(t)", t)
        return self.page.screenshot(type=fmt, quality=92 if fmt == "jpeg" else None, clip={"x": 0, "y": 0, "width": W, "height": H})

    def qc_flags(self):
        return self.page.evaluate("window.QC || []")

    def close(self):
        try:
            self.browser.close()
        finally:
            self._pw.stop()


def encode_video(frames, total_s, out_mp4):
    """frames(t) → bytes; pipes JPEG frames into ffmpeg → H.264 1080x1920 30 fps."""
    n = int(round(total_s * FPS))
    cmd = [_ffmpeg(), "-y", "-v", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "pipe:0",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(FPS), "-movflags", "+faststart", "-an", out_mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    t0 = time.time()
    for i in range(n):
        p.stdin.write(frames(i / FPS))
        if i % 150 == 0:
            print(f"  frame {i}/{n} ({time.time() - t0:.0f}s)", flush=True)
    p.stdin.close()
    err = p.stderr.read().decode()
    if p.wait() != 0:
        raise RuntimeError("ffmpeg encode failed: " + err[-400:])
    return n


# ---------------------------------------------------------------- resolving a plan
def _voice(res, plan, series, work, local, notes):
    """Record the voice lines. Real line lengths decide the screen lengths (AGENT.md 4.4)."""
    v = plan.get("voice")
    voice_on = v.get("on", True) if isinstance(v, dict) else (bool(v) if v is not None else bool(series.get("voice")))
    lines = [(i, s["voice_line"]) for i, s in enumerate(res["screens"]) if s.get("voice_line")]
    res["voice_clips"] = []
    if not voice_on or not lines:
        return
    try:
        says = load_yaml((niche_dir() / "knowledge" / "pronunciations.yaml").relative_to(ROOT)) or {}
    except FileNotFoundError:
        says = {}

    def spoken(t):
        for k, val in says.items():
            t = t.replace(k, val)
        return t
    vdir = os.path.join(work, "voice")
    os.makedirs(vdir, exist_ok=True)
    clips = None
    if local:   # stand-in tones with estimated lengths, so timing and mixing can be tested without Microsoft's service
        clips = []
        for n, (_, txt) in enumerate(lines):
            secs = round(min(7.0, max(0.9, len(txt) * 0.062)), 2)
            f = os.path.join(vdir, f"line_{n:02d}.mp3")
            subprocess.run([_ffmpeg(), "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=frequency=170:duration={secs}",
                            "-af", "tremolo=f=6:d=0.7,volume=0.5", f], check=True)
            clips.append({"file": f, "seconds": secs})
    else:
        from . import voice as V
        cfg = {k: val for k, val in (v or {}).items() if k in ("voice", "rate", "pitch")} if isinstance(v, dict) else {}
        cfg["lines"] = [{"text": spoken(txt)} for _, txt in lines]
        r = V.batch(cfg, vdir)
        if not r.get("ok"):   # one retry, then the silent version (fail soft)
            time.sleep(8)
            r = V.batch(cfg, vdir)
        if r.get("ok"):
            clips = r["clips"]
        else:
            notes.append(f"Voice could not be recorded ({r.get('error')}). This reel is the silent version with music and full on-screen text.")
            res["voice_failed"] = True
    if clips:
        for (i, _), c in zip(lines, clips):
            s = res["screens"][i]
            s["dur_planned"] = s.get("dur")
            s["dur"] = round(max(float(s.get("min_dur", 1.2)), c["seconds"] + float(s.get("pause", 0.34))), 2)
            s["say_dur"] = c["seconds"]
            res["voice_clips"].append({"screen": i, "file": c["file"], "seconds": c["seconds"]})


def _runs(screens):
    """Group screens that share one picture: "same" continues the previous one; the same image number also continues."""
    runs, prev_key = [], None
    for i, s in enumerate(screens):
        v = s.get("visual")
        if v is None and "image" in s:
            v = s["visual"] = {"type": "image", "image": s["image"]}
        key = ("image", v["image"]) if isinstance(v, dict) and v.get("type") == "image" and "image" in v else None
        if runs and (v == "same" or (key is not None and key == prev_key)):
            runs[-1]["screens"].append(i)
        else:
            runs.append({"spec": None if v == "same" else v, "screens": [i]})
        prev_key = key if v != "same" else prev_key
    return runs


def resolve(plan, work, local, drive=None, budget=None):
    """Turn the Brain's plan into what the template needs: files for every picture, voice lengths, final timings, music."""
    from .assets import Assets
    from .settings import AGENT
    series = series_for(plan)
    reel_id = plan["reel_id"]
    A = Assets(work, reel_id, drive=drive, local=local, budget=budget, series=series)
    template = plan.get("template") or series.get("template") or "card"
    image_cap = plan.get("image_cap", series.get("image_cap_per_reel"))
    style_default = plan.get("image_style") or series.get("image_style") or (series.get("image_style_options") or [None])[0]
    res = json.loads(json.dumps(plan))
    res["template"] = template
    if "badge" not in res and series.get("badge"):
        res["badge"] = series["badge"]
    for s in res["screens"]:
        s.setdefault("dur", 3.0)
    _voice(res, plan, series, work, local, A.notes)

    counter = {"img": 0, "n": 0}

    def one(v, length):
        """Resolve one picture spec for a run that lasts `length` seconds."""
        if not isinstance(v, dict):
            return {"type": "mascot"}
        counter["n"] += 1
        n, kind = counter["n"], v.get("type")
        out = dict(v)
        if kind == "image" and "image" in v and res.get("images"):
            im = res["images"][v["image"]]
            if "src" not in im:
                counter["img"] += 1
                im.update(A.image(im, counter["img"], style_default, image_cap))
                if template == "diorama":
                    from . import depth
                    im["layers"], im["depth_source"] = depth.layers(im["src"], os.path.join(work, f"layers_{v['image']:02d}"), local=local)
                    if im["depth_source"] != "model" and not local:
                        A.notes.append(f"Scene {v['image'] + 1}: the depth model was not available, so a simpler layered look was used.")
            out.update({k: im[k] for k in ("src", "source", "style", "layers", "focus", "motion") if k in im})
        elif kind == "image":
            counter["img"] += 1
            out.update(A.image(v, counter["img"], style_default, image_cap))
        elif kind == "clip":
            out.update(A.clip(v, n, length))
        elif kind == "meme":
            out.update(A.meme(v, n, length))
        elif kind in ("stack", "split"):
            for side in (("top", "bottom") if kind == "stack" else ("left", "right")):
                out[side] = one(v.get(side) or {}, length)
        return out

    for run in _runs(res["screens"]):
        idxs = run["screens"]
        total = sum(float(res["screens"][i]["dur"]) for i in idxs)
        vis = one(run["spec"], total) if run["spec"] is not None else None
        off = 0.0
        for k, i in enumerate(idxs):
            s = res["screens"][i]
            s["visual"] = vis
            s["voff"], s["vdur"], s["visual_changed"] = round(off, 3), round(total, 3), k == 0
            off += float(s["dur"])
    moods = (load_yaml(f"niches/{AGENT['active']['niche']}/niche.yaml") or {}).get("music_moods", {})
    mood = (plan.get("music") or {}).get("mood") or moods.get(plan.get("series"), "soft_warm")
    total = sum(float(s["dur"]) for s in res["screens"])
    res["music_resolved"] = A.music(mood, plan.get("series"), total, track=(plan.get("music") or {}).get("track"))
    res["music_resolved"]["mood"] = mood
    res["total_s"] = round(total, 2)
    res["notes"] = A.notes
    res["images_made"] = A.images_made
    return res, template


# ---------------------------------------------------------------- main flow
def render(plan_path, local=False, to_drive=None, snap=None, debug_safe=False, drive=None, sheet=None):
    with open(plan_path, encoding="utf-8") as f:
        plan = json.load(f)
    reel_id = plan["reel_id"]
    outdir = OUT / "reels" / reel_id
    work = OUT / "work" / reel_id
    os.makedirs(outdir, exist_ok=True)
    budget = None
    if not local and drive is None:
        try:
            from .drive import Drive
            drive = Drive()
        except Exception as e:
            print("Drive not available, rendering with local placeholders:", e, file=sys.stderr)
            local = True
    if drive:
        from .budget import Budget
        budget = Budget(drive)
    brand = kit(plan.get("brand"))
    res, template = resolve(plan, work, local, drive, budget)
    with open(outdir / "plan_resolved.json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=1)
    fr = Frames(template, debug_safe)
    try:
        info = fr.setup(res, brand)
        total = float(info["total"])
        if sheet is not None:      # one picture with a frame from every screen (or a burst across one stretch), to review a template at a glance
            from PIL import Image
            import io
            if sheet and ":" in sheet:
                a, b, n = sheet.split(":")
                times = [float(a) + (float(b) - float(a)) * i / (int(n) - 1) for i in range(int(n))]
            else:
                at = float(sheet) if sheet else 0.8
                times = [sc["start"] + (sc["end"] - sc["start"]) * at for sc in info["screens"]]
            cols = 5 if len(times) > 8 else 4
            tw, th = 432, 768
            rows = (len(times) + cols - 1) // cols
            im = Image.new("RGB", (cols * tw, rows * th), (0, 0, 0))
            for k, t in enumerate(times):
                fr_im = Image.open(io.BytesIO(fr.frame(min(t, total - 0.01), "png"))).convert("RGB").resize((tw, th), Image.LANCZOS)
                im.paste(fr_im, ((k % cols) * tw, (k // cols) * th))
            p = outdir / "sheet.jpg"
            im.save(p, quality=88)
            print("sheet:", p, "times:", [round(t, 2) for t in times])
            print("qc flags:", fr.qc_flags())
            return {"ok": True, "sheet": str(p), "total_s": total}
        if snap is not None:
            times = [float(x) for x in snap.split(",")] if snap else [0.3, total / 2, total - 0.5]
            paths = []
            for t in times:
                p = outdir / f"snap_{t:05.1f}s.png"
                with open(p, "wb") as f:
                    f.write(fr.frame(min(t, total - 0.01), "png"))
                paths.append(str(p))
            print("snapshots:", *paths, sep="\n  ")
            print("qc flags:", fr.qc_flags() + fr.page.evaluate("T.safeCheck(-1)"))
            return {"ok": True, "snapshots": paths, "total_s": total}
        silent = str(outdir / "video_silent.mp4")
        print(f"Rendering {reel_id} with the {template} template: {total:.1f} s, {int(total * FPS)} frames")
        encode_video(lambda t: fr.frame(t), total, silent)
        safe = []
        for sc in info["screens"]:   # safe zones and overflow, checked late in each screen when everything is on
            fr.page.evaluate("t => window.renderFrame(t)", sc["start"] + (sc["end"] - sc["start"]) * 0.85)
            safe += fr.page.evaluate("i => T.safeCheck(i)", sc["i"])
        # cover frame
        cs = res.get("cover", {}).get("screen", 1)
        scr = info["screens"][min(max(int(cs) - 1, 0), len(info["screens"]) - 1)]
        ct = scr["start"] + min(1.0, (scr["end"] - scr["start"]) * 0.6)
        with open(outdir / "cover.jpg", "wb") as f:
            f.write(fr.frame(ct, "jpeg"))
        flags = fr.qc_flags() + safe
    finally:
        fr.close()
    from . import audio, qc
    mix = audio.build(res, work, total)
    final = str(outdir / "reel.mp4")
    subprocess.run([_ffmpeg(), "-y", "-v", "error", "-i", silent, "-i", mix, "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", final], check=True)
    os.remove(silent)
    report = qc.check(final, res, series_for(plan), flags, str(outdir / "cover.jpg"))
    with open(outdir / "qc.json", "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    notes = ["# " + reel_id, "", f"Template: {template}. Length: {total:.1f} s. Music: {res['music_resolved']['name']} ({res['music_resolved']['mood']}).",
             f"Images made: {res.get('images_made', 0)}. Voice: {'yes' if res.get('voice_clips') else 'no'}{' (failed, silent version)' if res.get('voice_failed') else ''}.", ""]
    notes += ["QC: " + ("PASS" if report["pass"] else "HOLD") + " — " + "; ".join(report["problems"] or ["all checks passed"]), ""]
    notes += ["Fallbacks used:"] + ["- " + n for n in res.get("notes", [])] if res.get("notes") else ["No fallbacks were needed."]
    with open(outdir / "notes.md", "w", encoding="utf-8") as f:
        f.write("\n".join(notes) + "\n")
    print("\n".join(notes))
    if to_drive and drive:
        folder = to_drive.rstrip("/") + "/" + reel_id
        for name in ["reel.mp4", "cover.jpg", "notes.md", "qc.json", "plan_resolved.json"]:
            drive.upload(str(outdir / name), folder)
        print("uploaded to Drive", folder, "→", drive.folder_link(drive.folder(folder)))
    shutil.rmtree(work, ignore_errors=True)
    return {"ok": report["pass"], "reel": final, "qc": report, "total_s": total}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plans", nargs="+")
    ap.add_argument("--local", action="store_true", help="placeholders instead of Drive/OpenAI (for testing templates)")
    ap.add_argument("--to-drive", default=None, help="Drive folder to upload the result to, e.g. rehearsal/phase2")
    ap.add_argument("--snap", nargs="?", const="", default=None, help="only PNG frames at these times, e.g. 0,2,10")
    ap.add_argument("--safe", action="store_true", help="draw the safe zones (debug)")
    ap.add_argument("--sheet", nargs="?", const="", default=None, help="one picture with a frame per screen (give 0-1 for where in each screen), or a burst as start:end:count")
    a = ap.parse_args()
    ok = True
    for p in a.plans:
        r = render(p, local=a.local, to_drive=a.to_drive, snap=a.snap, debug_safe=a.safe, sheet=a.sheet)
        ok = ok and r.get("ok", False)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
