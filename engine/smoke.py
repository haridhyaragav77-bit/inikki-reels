"""Phase 1 smoke tests (AGENT.md Block A, Phase 1). Nothing is posted publicly.

    python -m engine.smoke --tests all            # or: secrets,drive,sheet,voice,image,clip,instagram,runner
    python -m engine.smoke --image no             # skip the one paid OpenAI image

Every test ends as OK or FAIL with one plain sentence and, when it failed, the next step.
Results go to out/smoke/ (the run artifact), Drive rehearsal/smoke-<date>/ and Drive status/smoke.json.
"""
import argparse
import os
import platform
import shutil
import subprocess
import sys
import traceback

from . import status
from .settings import ENGINE, OUT, SECRET_NAMES, OPTIONAL_SECRETS, missing_secrets, secret, github_step_summary

OUTDIR = OUT / "smoke"
RESULTS = []
CTX = {}


def result(name, ok, detail, next_step=""):
    RESULTS.append({"test": name, "ok": bool(ok), "detail": detail, "next": next_step})
    print(f"[{'OK' if ok else 'FAIL'}] {name}: {detail}" + (f"  NEXT: {next_step}" if next_step else ""), flush=True)


def run_test(name, fn, *args):
    try:
        fn(*args)
    except Exception as e:  # a failing test never stops the others (fail soft)
        from .drive import plain_error
        print(traceback.format_exc()[-1500:], file=sys.stderr)
        result(name, False, plain_error(e))


# ---------------------------------------------------------------- tests
def t_secrets():
    missing = missing_secrets(SECRET_NAMES)
    extra = [n for n in OPTIONAL_SECRETS if secret(n)]
    note = f" Optional keys also present: {', '.join(extra)}." if extra else ""
    if missing:
        result("Keys in GitHub", False, f"Missing: {', '.join(missing)}.{note}",
               "Add each missing secret at github.com/haridhyaragav77-bit/inikki-reels/settings/secrets/actions (AGENT.md 19.2).")
    else:
        result("Keys in GitHub", True, f"All {len(SECRET_NAMES)} keys are present.{note}")


def t_drive_read():
    from .drive import Drive, FOLDER
    d = Drive()
    CTX["drive"] = d
    kids = d.children(d.root)
    names = sorted(k["name"] for k in kids)
    counts = {}
    for key in ["reference-reels", "meme-bank"]:
        f = d.find_child(d.root, key, FOLDER)
        counts[key] = len(d.children(f["id"])) if f else None
    m = d.music_folder()
    counts["music"] = len([x for x in d.children(m) if x.get("mimeType", "").startswith("audio/")]) if m else None
    CTX["drive_mode"] = d.mode
    who = d.who()
    parts = [f"Signed in as {who} ({'your sign-in' if d.mode == 'harish_signin' else 'robot account'}).",
             f"Root folder has {len(kids)} items: {', '.join(names)}."]
    for k, v in counts.items():
        parts.append(f"{k}: {'not found' if v is None else str(v) + ' files'}.")
    result("Drive: read", True, " ".join(parts))


def t_drive_write():
    d = CTX.get("drive")
    if not d:
        result("Drive: write", False, "Skipped because Drive read failed.")
        return
    from .drive import plain_error
    try:
        made = d.ensure_tree()
        f = d.write_text("rehearsal", "smoke_hello.txt", f"iNiKKi Reels smoke test at {status.stamp()}\n")
        CTX["drive_writable"] = True
        # Seed the master switch if the Control Room has not written it yet
        if not d.read_json("control", "switch.json"):
            import json
            seed = json.load(open(os.path.join(os.path.dirname(__file__), "seed", "control", "switch.json"), encoding="utf-8"))
            seed["at"] = status.stamp()
            seed["set_by"] = "engine (starter value)"
            d.write_json("control", "switch.json", seed)
        result("Drive: write", True, f"Wrote a test file into rehearsal/ ({d.link(f['id'])}). "
               + (f"Created folders: {', '.join(made)}." if made else "All folders already existed."))
    except Exception as e:
        CTX["drive_writable"] = False
        msg = plain_error(e)
        nxt = ""
        if "storage limit" in msg:
            nxt = ("Switch to your own sign-in: on your laptop run  python tools/drive_signin.py  (it prints the steps), "
                   "then add the secret GDRIVE_OAUTH_REFRESH_TOKEN and run the smoke test again.")
        result("Drive: write", False, msg, nxt)


def t_sheet():
    d = CTX.get("drive")
    if not d:
        result("Dashboard sheet", False, "Skipped because Drive read failed.")
        return
    from .sheets import Dashboard
    db = Dashboard(d)
    added = db.ensure_tabs()
    db.append("Home", [["Smoke test", status.stamp(), "OK: the Engine can write to this sheet"]])
    CTX["sheet"] = db.link()
    result("Dashboard sheet", True, f"{'Created' if db.created else 'Found'} '{db.name}'"
           + (f", added tabs {', '.join(added)}" if added else "") + f", wrote one row. {db.link()}")


def t_voice():
    from . import voice
    out = str(OUTDIR / "voice_hello.mp3")
    r = voice.say(ENGINE["voice"]["smoke_text"], out)
    if r.get("ok") and os.path.exists(out) and os.path.getsize(out) > 1000:
        CTX["voice_file"] = out
        result("Voice from the cloud (Microsoft)", True,
               f"Tamil line recorded on the GitHub runner: {r.get('seconds')} s, {os.path.getsize(out) // 1024} KB. Voice jobs can run in the cloud.")
    else:
        result("Voice from the cloud (Microsoft)", False, f"Microsoft's voice service did not answer from the runner: {r.get('error', 'no file')}",
               "The evening laptop route (Voice Session card, 8 PM) becomes the voice plan; the Engine will retry the cloud each day.")


def t_image(spend):
    if not spend:
        result("One AI image (OpenAI)", True, "Skipped by choice (no money spent).")
        return
    from . import images
    d = CTX.get("drive") if CTX.get("drive_writable") else None
    r = images.generate(
        "A small-town Tamil Nadu single-screen cinema at golden hour, a yellow paper ticket resting on the counter, empty street, nostalgic",
        "painterly_warm", quality=ENGINE["openai"]["smoke_quality"], purpose="smoke test", reel_id="smoke",
        out_path=str(OUTDIR / "image_test.png"), drive=d)
    if r.get("ok"):
        CTX["image_file"] = r["path"]
        b = r["budget"]
        result("One AI image (OpenAI)", True,
               f"Made one {r['quality']}-quality test image with {r['model']} for about ₹{r['cost_inr']:.2f}. "
               f"Month so far: ₹{b['spent_inr']:.2f} of ₹{b['cap_inr']:.0f}.")
    else:
        result("One AI image (OpenAI)", False, r.get("error", "unknown error"),
               "Check the OpenAI key and that the account has credit ($5 top-up, auto-recharge off).")


def t_clip():
    from . import clips
    q = ENGINE["clips"]["smoke_query"]
    meta = clips.lookup(q)
    out = str(OUTDIR / "clip_test.mp4")
    clips.fetch(meta["url"], 5, ENGINE["clips"]["smoke_seconds"], out)
    secs = clips.duration(out)
    sheet = None
    try:
        sheet = clips.contact_sheet(out, str(OUTDIR / "clip_contact_sheet.png"), cols=4, rows=2)
    except Exception as e:
        print("contact sheet failed:", e, file=sys.stderr)
    CTX["clip_file"] = out
    CTX["clip_sheet"] = sheet
    result("One trailer clip (YouTube)", True,
           f"Fetched {secs} s from '{meta['title']}' ({meta['channel']}), {os.path.getsize(out) // 1024} KB"
           + (", and made a contact sheet." if sheet else ". Contact sheet failed (see log)."))


def t_instagram():
    from .instagram import Instagram
    ig = Instagram()
    me = ig.me()
    media = ig.media(8)
    reels = [m for m in media if m.get("media_product_type") == "REELS" or m.get("media_type") == "VIDEO"]
    detail = (f"Account @{me.get('username')}: {me.get('followers_count')} followers, {me.get('media_count')} posts "
              f"(API {ig.version}). Latest {len(media)} posts read.")
    metrics_ok = []
    if reels:
        ins, metrics_ok = ig.insights(reels[0]["id"])
        shown = ", ".join(f"{k} {v}" for k, v in list(ins.items())[:6])
        detail += f" Newest reel: {shown}. Metrics the API gives: {', '.join(metrics_ok)}."
    CTX["ig"] = {"username": me.get("username"), "followers": me.get("followers_count"), "posts": me.get("media_count"),
                 "api_version": ig.version, "reel_metrics": metrics_ok}
    result("Instagram numbers (read only)", True, detail)


def t_runner():
    ff = shutil.which("ffmpeg")
    ver = subprocess.run([ff, "-version"], capture_output=True, text=True).stdout.split("\n")[0][:60] if ff else "missing"
    node = shutil.which("node")
    nv = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip() if node else "missing"
    tamil = subprocess.run(["fc-list", ":lang=ta"], capture_output=True, text=True).stdout.strip().count("\n") + 1 if shutil.which("fc-list") else 0
    result("Runner tools", True, f"Python {platform.python_version()}, {ver}, node {nv}, Tamil fonts installed: {tamil if tamil else 'none yet (added in Phase 2)'}.")


# ---------------------------------------------------------------- report
def write_report(tests_run):
    ok = sum(1 for r in RESULTS if r["ok"])
    lines = [f"# Smoke test — {status.stamp()}", "",
             f"**{ok} of {len(RESULTS)} passed.** Nothing was posted. Tests run: {tests_run}.", "",
             "| Test | Result | What happened | Next step |", "| --- | --- | --- | --- |"]
    for r in RESULTS:
        lines.append(f"| {r['test']} | {'✅ OK' if r['ok'] else '❌ FAIL'} | {r['detail']} | {r['next'] or '—'} |")
    md = "\n".join(lines) + "\n"
    os.makedirs(OUTDIR, exist_ok=True)
    with open(OUTDIR / "smoke_report.md", "w", encoding="utf-8") as f:
        f.write(md)
    github_step_summary(md)
    print("\n" + md)

    d = CTX.get("drive")
    summary = {"passed": ok, "total": len(RESULTS), "results": RESULTS, "drive_mode": CTX.get("drive_mode"),
               "drive_writable": CTX.get("drive_writable"), "sheet": CTX.get("sheet"), "instagram": CTX.get("ig"),
               "voice_cloud_ok": any(r["test"].startswith("Voice") and r["ok"] for r in RESULTS)}
    status.write(d if CTX.get("drive_writable") else None, "smoke.json", summary)
    if d and CTX.get("drive_writable"):
        folder = f"rehearsal/smoke-{status.now().strftime('%Y-%m-%d-%H%M')}"
        try:
            for name in sorted(os.listdir(OUTDIR)):
                d.upload(str(OUTDIR / name), folder)
            print(f"Uploaded {len(os.listdir(OUTDIR))} files to Drive {folder}/ → {d.folder_link(d.folder(folder))}")
        except Exception as e:
            print("Upload to Drive rehearsal/ failed:", e, file=sys.stderr)
    return ok == len(RESULTS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tests", default="all")
    ap.add_argument("--image", default="yes", help="yes/no: spend about ₹0.50 on one OpenAI test image")
    a = ap.parse_args()
    want = [t.strip() for t in a.tests.split(",")] if a.tests and a.tests != "all" else None
    spend = str(a.image).lower() in ("yes", "true", "1", "y")
    os.makedirs(OUTDIR, exist_ok=True)
    order = [("secrets", "Keys in GitHub", t_secrets, ()), ("runner", "Runner tools", t_runner, ()),
             ("drive", "Drive: read", t_drive_read, ()), ("drive", "Drive: write", t_drive_write, ()),
             ("sheet", "Dashboard sheet", t_sheet, ()), ("voice", "Voice from the cloud (Microsoft)", t_voice, ()),
             ("image", "One AI image (OpenAI)", t_image, (spend,)), ("clip", "One trailer clip (YouTube)", t_clip, ()),
             ("instagram", "Instagram numbers (read only)", t_instagram, ())]
    ran = []
    for key, name, fn, args in order:
        if want and key not in want:
            continue
        if key not in ran:
            ran.append(key)
        run_test(name, fn, *args)
    all_ok = write_report(", ".join(ran))
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
