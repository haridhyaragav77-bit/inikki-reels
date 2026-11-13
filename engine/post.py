"""Post job (AGENT.md 4.3, 12.1): at each slot, post the reel that is due. The switch is checked right before posting.

    python -m engine.post            the slot that is due now (waits up to 15 minutes if the run started early)
    python -m engine.post --dry      upload one made reel as an unpublished container only: tests posting, shows nothing

Rehearsal phase: nothing is posted; the due reel is marked "rehearsed" at its time. Hold posts: the due reel is held.
The same run also does the news watch and the 2-hour stats (fewer runner minutes than separate jobs)."""
import argparse
import datetime as dt
import json
import sys
import time
import traceback

from .settings import OUT, ROOT, niche_dir
from . import status
from .control import Control
from .day import Bank, Day, today


# ---------------------------------------------------------------- rules that can stop a reel
def respect_today(drive, date, ctl=None):
    """Respect mode (AGENT.md 10.2): set by the Breaking run (plans/<date>/respect.json) or by the watcher (status/respect.json).
    Harish can turn it off for the day from the Control Room (settings.respect.off_date)."""
    ctl = ctl or Control(drive)
    if str((ctl.settings.get("respect") or {}).get("off_date", "")) == date:
        return None
    p = ROOT / "plans" / date / "respect.json"
    if p.exists():
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
            if j.get("on", True):
                return j
        except ValueError:
            pass
    try:
        j = drive.read_json("status", "respect.json") or {}
        if j.get("on") and j.get("date") == date:
            return j
    except Exception:
        pass
    return None


def stopper(r, ctl, respect, now):
    """Why this reel must not post now, in plain words (or None)."""
    series = r.get("series", "")
    if ctl.series_paused(series):
        return "The series is paused."
    if respect and not r.get("tribute"):
        allow = respect.get("allow_series") or ctl.settings.get("respect", {}).get("allow_series", [])
        if series not in allow:
            return f"Respect mode today ({respect.get('why', 'sad news')}). Only fitting reels post."
    card = ctl.series(series, niche_dir())
    if card.get("expires_h") and r.get("made_at"):
        age = now - dt.datetime.fromisoformat(r["made_at"])
        if age > dt.timedelta(hours=float(card["expires_h"])):
            return f"News older than {card['expires_h']} hours is not posted."
    return None


# ---------------------------------------------------------------- posting
def _append_line(drive, folder, name, obj):
    old = drive.read_text(folder, name) or ""
    drive.write_text(folder, name, old + json.dumps(obj, ensure_ascii=False) + "\n", "application/x-ndjson")


def retire_track(drive, track_name, why):
    """A track Instagram flags is never used again (AGENT.md 0, honest limits)."""
    try:
        mid = drive.music_folder()
        f = drive.find_child(mid, "index.json") if mid else None
        if not f:
            return
        idx = json.loads(drive.read_bytes(f["id"]).decode("utf-8"))
        for t in idx.get("tracks", []):
            if t.get("name") == track_name:
                t["retired"], t["retired_why"] = True, why
        from googleapiclient.http import MediaInMemoryUpload
        drive.svc.files().update(fileId=f["id"], media_body=MediaInMemoryUpload(json.dumps(idx, ensure_ascii=False, indent=1).encode("utf-8"),
                                 mimetype="application/json"), supportsAllDrives=True).execute(num_retries=3)
    except Exception as e:
        print("could not retire track:", e, file=sys.stderr)


def publish(drive, day, r, ctl, dry=False):
    """Upload and publish one made reel. With dry=True: upload, let Instagram process and check it, never publish."""
    from .instagram import Instagram, InstagramError
    rid = r["reel_id"]
    try:
        ig = Instagram()
        ig.me()
        local = drive.download(r["drive_reel"], str(OUT / "post" / f"{rid}.mp4"))
        cid = ig.create_reel(local, r.get("caption") or "", thumb_offset_ms=int(float(r.get("cover_t") or 1) * 1000), trial=r.get("trial"))
        ig.wait_ready(cid)
        cr = {}
        for _ in range(8):                      # Instagram's music/copyright check finishes shortly after processing
            cr = ig.copyright_status(cid) or {}
            if str(cr.get("status", "complete")).lower() != "in_progress":
                break
            time.sleep(8)
        if cr.get("matches_found") in (True, "true"):
            if r.get("music"):
                retire_track(drive, r["music"], f"copyright match on {rid}")
            day.upsert(rid, state="held", reason="Instagram's own check found a copyright match. Not posted; its music track is retired.")
            status.alert(drive, "A reel was stopped by Instagram's music check", f"{rid}: Instagram found a copyright match before posting.",
                         "It was not posted. Its music track will not be used again.", "nothing", level="warn")
            return False
        if dry:
            day.upsert(rid, dry_upload=f"ok {status.stamp()}")
            print(f"Dry upload worked for {rid}: Instagram processed it and it was NOT published (the container expires by itself).")
            return True
        if Control(drive).mode != "run":       # read the switch once more, right before publishing (AGENT.md 12.1)
            day.upsert(rid, state="held", reason="The master switch changed just before posting.")
            return False
        mid, info = ig.publish(cid)
        note = None
        if r.get("first_comment"):
            try:
                ig.comment(mid, r["first_comment"])
            except InstagramError as e:
                note = f"Posted, but the first comment was not added: {str(e)[:120]}"
        when = status.now().isoformat(timespec="seconds")
        day.upsert(rid, state="posted", media_id=mid, permalink=info.get("permalink"), posted_at=when, reason=note)
        _append_line(drive, "status", "posted.jsonl", {"reel_id": rid, "media_id": mid, "series": r.get("series"), "posted_at": when,
                                                        "permalink": info.get("permalink"), "seconds": r.get("seconds"), "hook": r.get("hook"),
                                                        "virality": r.get("virality"), "music": r.get("music"), "trial": bool(r.get("trial"))})
        print(f"Posted {rid}: {info.get('permalink')}")
        return True
    except Exception as e:
        traceback.print_exc()
        if not dry:
            day.upsert(rid, state="failed", reason=f"Posting failed: {str(e)[:200]}")
        status.alert(drive, "A reel could not be posted" if not dry else "The posting test did not pass", f"{rid}: {str(e)[:220]}",
                     "Its slot is skipped; the next slot carries on." if not dry else "Nothing was posted.",
                     "Nothing, unless it repeats (then the Instagram token or its permissions need a look).", level="warn")
        return False


def deliver(drive, day, r, ctl, respect):
    """Decide what happens to the due reel: post, rehearse, hold or skip."""
    rid = r["reel_id"]
    why = stopper(r, ctl, respect, status.now())
    if why:
        day.upsert(rid, state="skipped", reason=why)
        return "skipped"
    if ctl.phase != "live":
        day.upsert(rid, state="rehearsed", reason="Rehearsal: this is when it would have posted.")
        return "rehearsed"
    if ctl.mode != "run":
        day.upsert(rid, state="held", reason="Not posted: the master switch was on Hold.")
        return "held"
    return "posted" if publish(drive, day, r, ctl) else "failed"


def breaking_now(drive, day, rid, ctl):
    """Breaking news posts as soon as it is made, max per day from settings (AGENT.md 10.2)."""
    cap = int(ctl.settings.get("budgets", {}).get("breaking_per_day", 2))
    if sum(1 for x in day.reels("posted") if x.get("series") == "breaking-news") >= cap:
        day.upsert(rid, state="skipped", reason=f"Already {cap} breaking reels today.")
        return
    deliver(drive, day, day.get(rid), ctl, respect_today(drive, day.date, ctl))
    day.save()


# ---------------------------------------------------------------- what is due
def choose(day, bank, now, ctl):
    """The planned reel whose time has come (up to 3 hours late), one per run. If it is held or failed:
    a ready reserve (same slot, then same series, then any), then a ready bank reel takes its place."""
    due = []
    for r in day.reels():
        if r.get("reserve") or not r.get("post_at"):
            continue
        t = dt.datetime.fromisoformat(r["post_at"])
        if now - dt.timedelta(hours=3) <= t <= now + dt.timedelta(minutes=5) and r.get("state") in ("ready", "held", "failed"):
            due.append(r)
    for r in sorted(due, key=lambda x: x["post_at"]):
        if r.get("state") == "ready":
            return r
        reserves = [x for x in day.reels("ready") if x.get("reserve") and not x.get("manual")]   # a new version waits for "post now"
        sub = (next((x for x in reserves if x.get("for_slot") in (r.get("slot"), r["reel_id"])), None)
               or next((x for x in reserves if x.get("series") == r.get("series")), None) or (reserves[0] if reserves else None))
        if sub:
            day.upsert(sub["reel_id"], post_at=r["post_at"], slot=r.get("slot"), reserve=False, reason=f"Took the slot of {r['reel_id']}.")
            day.upsert(r["reel_id"], state="skipped", reason=(r.get("reason") or "") + " A reserve took its slot.")
            return day.get(sub["reel_id"])
        b = next(iter(bank.reels("ready")), None)
        if b:
            if ctl.can_post:                  # rehearsal does not use up the bank
                bank.upsert(b["reel_id"], state="used", used_for=r["reel_id"], used_at=status.now().isoformat(timespec="seconds"))
            fields = {k: v for k, v in b.items() if k not in ("reel_id", "state", "updated", "reason")}
            day.upsert(b["reel_id"], **fields, post_at=r["post_at"], slot=r.get("slot"), state="ready", reason=f"From the breakdown bank, for {r['reel_id']}.")
            day.upsert(r["reel_id"], state="skipped", reason=(r.get("reason") or "") + " A bank breakdown took its slot.")
            return day.get(b["reel_id"])
    return None


def slots(ctl):
    return sorted(set(ctl.settings.get("slots", []) + ctl.settings.get("flex_slots", [])))


def wait_for_slot(ctl, max_wait_min=15):
    """Runs are scheduled a little before each slot (GitHub can start them late); wait so the reel goes out on time."""
    now = status.now()
    for s in slots(ctl):
        h, m = (int(x) for x in s.split(":"))
        t = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if dt.timedelta(0) < t - now <= dt.timedelta(minutes=max_wait_min):
            print(f"Waiting {int((t - now).total_seconds())} s for the {s} slot.")
            time.sleep((t - now).total_seconds())
            return s
    return None


def apply_commands(ctl, day):
    """One-off commands from the Control Room (control/commands.jsonl): hold, unhold, post_now, skip."""
    for c in ctl.lines("commands.jsonl")[-80:]:
        r = day.get(c.get("reel_id", ""))
        if not r:
            continue
        cmd, st = c.get("cmd"), r.get("state")
        if cmd == "hold" and st == "ready":
            day.upsert(r["reel_id"], state="held", reason="Held by Harish.")
        elif cmd == "unhold" and st == "held" and r.get("reason") == "Held by Harish.":
            day.upsert(r["reel_id"], state="ready", reason=None)
        elif cmd == "skip" and st in ("ready", "held", "planned"):
            day.upsert(r["reel_id"], state="skipped", reason="Skipped by Harish.")
        elif cmd == "post_now" and st == "ready" and not r.get("now_done"):
            day.upsert(r["reel_id"], post_at=status.now().isoformat(timespec="seconds"), reserve=False, now_done=True)


def extras(drive, ctl):
    for name, mod, fn in (("news watch", "engine.watch", "run"), ("2-hour stats", "engine.measure", "checkpoints")):
        try:
            getattr(__import__(mod, fromlist=[fn]), fn)(drive, ctl)
        except Exception as e:
            print(f"{name} skipped: {str(e)[:200]}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--no-wait", action="store_true")
    ap.add_argument("--skip-extras", action="store_true")
    ap.add_argument("--now", default="", help="post this made reel id at once (live phase only), outside its slot")
    a = ap.parse_args()
    from .drive import Drive
    drive = Drive()
    ctl = Control(drive)
    if ctl.mode == "sleep":
        status.write(drive, "post.json", {"state": "asleep"})
        print("Asleep: nothing posted.")
        return
    if not (a.no_wait or a.dry):
        wait_for_slot(ctl)
        ctl = Control(drive)                    # the switch may have changed while waiting
    day, bank = Day(drive), Bank(drive)
    apply_commands(ctl, day)
    result = "nothing due"
    if a.now:
        r = next((x for x in day.reels() if x["reel_id"] == a.now.strip()), None)
        if not r or not r.get("drive_reel"):
            result = f"{a.now}: not found among today's made reels"
        elif ctl.phase != "live":
            result = f"{a.now}: not posted, the phase is rehearsal"
        elif r.get("state") == "posted":
            result = f"{a.now}: already posted"
        else:
            result = f"{a.now}: " + ("posted now" if publish(drive, day, r, ctl) else "not posted (see alerts)")
    elif a.dry:
        r = next((x for x in reversed(day.reels("ready", "rehearsed", "held")) if x.get("drive_reel")), None) \
            or next((x for x in bank.reels("ready") if x.get("drive_reel")), None)
        if not r:
            result = "no made reel to test with"
        else:
            result = "dry upload ok" if publish(drive, day, r, ctl, dry=True) else "dry upload failed"
    else:
        r = choose(day, bank, status.now(), ctl)
        if r:
            result = f"{r['reel_id']}: " + deliver(drive, day, r, ctl, respect_today(drive, day.date, ctl))
    day.save()
    bank.save()
    status.write(drive, "post.json", {"last": result, "phase": ctl.phase, "switch": ctl.mode})
    print(result)
    if not (a.skip_extras or a.dry):
        extras(drive, ctl)


if __name__ == "__main__":
    main()
