"""Post job (AGENT.md 4.3, 12.1): at each slot, post the reel that is due. The switch is checked right before posting.

    python -m engine.post            the slot that is due now (GitHub's own timer: waits up to 15 minutes for a slot that is
                                     close, but only while the Claude clock is missing its times; see wait_for_slot)
    python -m engine.post --dry      upload one made reel as an unpublished container only: tests posting, shows nothing

Rehearsal phase: nothing is posted; the due reel is marked "rehearsed" at its time. Hold posts: the due reel is held.
The same run also does the news watch and the 2-hour stats (fewer runner minutes than separate jobs).

Runner minutes (AGENT.md 15.3): a run with nothing to post ends inside one billed minute. A reel is uploaded to Instagram
when it is made (unpublished; Instagram keeps it 24 hours), so the run at its slot only has to publish it. If that early
upload is missing, old or no longer matches the reel, the run uploads it the usual way: nothing is lost either way."""
import argparse
import datetime as dt
import hashlib
import json
import os
import sys
import time
import traceback

from .settings import ENGINE, OUT, ROOT, niche_dir
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
    from . import dayplan
    if dayplan.off(ctl, series) and not r.get("manual"):
        return dayplan.off(ctl, series)
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


def _post_cfg():
    return ENGINE.get("post") or {}


def prep_key(r):
    """What an early upload was made from. Any change to the reel (made again, new words, new cover) changes the key."""
    parts = [r.get("drive_reel"), r.get("made_at"), r.get("caption") or "", int(float(r.get("cover_t") or 1) * 1000), r.get("trial")]
    return hashlib.sha1(json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def prep_usable(r, now):
    """The early upload of this reel, if it is still this exact reel and young enough for Instagram to publish."""
    pre = r.get("ig_prepared") or {}
    try:
        age = now - dt.datetime.fromisoformat(pre["at"])
    except Exception:
        return None
    ok = pre.get("id") and pre.get("key") == prep_key(r) and dt.timedelta(0) <= age <= dt.timedelta(hours=float(_post_cfg().get("early_upload_max_hours", 20)))
    return pre["id"] if ok else None


def prepare(drive, ledger, rid, local=None, now=None):
    """Right after a reel is made: upload it to Instagram as an unpublished container, so the Post run at its slot only has
    to publish it (about a minute less on the runner per post). Nothing is visible to anyone. Fails soft: without it the
    Post run uploads the reel itself, exactly as before."""
    r = ledger.get(rid) or {}
    if not _post_cfg().get("early_upload", True) or not r.get("drive_reel") or not r.get("post_at"):
        return None
    now = now or status.now()
    try:
        ahead = dt.datetime.fromisoformat(r["post_at"]) - now
        if not dt.timedelta(hours=-3) <= ahead <= dt.timedelta(hours=float(_post_cfg().get("early_upload_max_hours", 20)) - 1):
            return None                                   # its slot is beyond Instagram's 24 hours (or long gone)
        from .instagram import Instagram
        if not (local and os.path.exists(local)):
            local = drive.download(r["drive_reel"], str(OUT / "post" / f"{rid}.mp4"))
        cid = Instagram().create_reel(local, r.get("caption") or "", thumb_offset_ms=int(float(r.get("cover_t") or 1) * 1000), trial=r.get("trial"))
        ledger.upsert(rid, ig_prepared={"id": cid, "at": now.isoformat(timespec="seconds"), "key": prep_key(r)})
        print(f"[{rid}] uploaded to Instagram ahead of its slot (unpublished)")
        return cid
    except Exception as e:
        print(f"[{rid}] early upload skipped (the Post run uploads it instead): {str(e)[:160]}", file=sys.stderr)
        return None


def publish(drive, day, r, ctl, dry=False, forced=False):
    """Upload and publish one made reel. With dry=True: upload, let Instagram process and check it, never publish."""
    from .instagram import Instagram, InstagramError
    rid = r["reel_id"]
    try:
        ig = Instagram()
        ig.me()
        cid = None if dry else prep_usable(r, status.now())
        if cid:                                 # uploaded when it was made: check it is still good, else upload afresh
            try:
                st = ig.get(cid, fields="status_code").get("status_code")
                if st == "PUBLISHED":           # an earlier run published it and stopped before writing that down
                    day.upsert(rid, state="posted", posted_at=status.now().isoformat(timespec="seconds"),
                               reason="Instagram already had this reel published; marked as posted.")
                    print(f"{rid}: already published on Instagram, marked as posted")
                    return True
                ig.wait_ready(cid, timeout=40)
                print(f"{rid}: using the upload made ahead of the slot")
            except Exception as e:
                print(f"{rid}: the early upload cannot be used ({str(e)[:120]}); uploading now", file=sys.stderr)
                cid = None
        if not cid:
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
        mode = Control(drive).mode             # read the switch once more, right before publishing (AGENT.md 12.1)
        if mode == "sleep" or (mode != "run" and not forced):
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


def deliver(drive, day, r, ctl, respect, forced=False):
    """Decide what happens to the due reel: post, rehearse, hold or skip.
    forced: Harish pressed "post now" on this reel, which also counts while the switch is on Hold posts (never on Sleep)."""
    rid = r["reel_id"]
    why = stopper(r, ctl, respect, status.now())
    if why:
        day.upsert(rid, state="skipped", reason=why)
        return "skipped"
    if ctl.phase != "live":
        day.upsert(rid, state="rehearsed", reason="Rehearsal: this is when it would have posted.")
        return "rehearsed"
    if ctl.mode != "run" and not forced:
        day.upsert(rid, state="held", reason="Not posted: the master switch was on Hold.")
        return "held"
    return "posted" if publish(drive, day, r, ctl, forced=forced) else "failed"


def breaking_now(drive, day, rid, ctl):
    """Breaking news posts as soon as it is made, max per day from settings (AGENT.md 10.2)."""
    cap = int(ctl.settings.get("budgets", {}).get("breaking_per_day", 2))
    if sum(1 for x in day.reels("posted") if x.get("series") == "breaking-news") >= cap:
        day.upsert(rid, state="skipped", reason=f"Already {cap} breaking reels today.")
        return
    deliver(drive, day, day.get(rid), ctl, respect_today(drive, day.date, ctl))
    day.save()


# ---------------------------------------------------------------- what is due
def choose(day, bank, now, ctl, early_min=5):
    """The planned reel whose time has come (up to 3 hours late), one per run. If it is held or failed:
    a ready reserve (same slot, then same series, then any), then a ready bank reel takes its place.
    early_min=0: only reels whose time has passed (a run that leaves a coming slot to the clock must not post it early)."""
    due = []
    for r in day.reels():
        if r.get("reserve") or not r.get("post_at"):
            continue
        t = dt.datetime.fromisoformat(r["post_at"])
        if now - dt.timedelta(hours=3) <= t <= now + dt.timedelta(minutes=early_min) and r.get("state") in ("ready", "held", "failed"):
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


def last_slot_before(ctl, now):
    """The newest slot time that has passed (yesterday's last slot, early in the morning)."""
    past = []
    for back in (0, 1):
        d = now - dt.timedelta(days=back)
        for s in slots(ctl):
            h, m = (int(x) for x in s.split(":"))
            t = d.replace(hour=h, minute=m, second=0, microsecond=0)
            if t <= now:
                past.append(t)
    return max(past) if past else None


def clock_file(drive):
    try:
        return drive.read_json("status", "clock.json") or {}
    except Exception:
        return {}


def clock_alive(ck, ctl, now):
    """True when the Claude clock started the Post run for the newest slot that has passed (AGENT.md 4.3). Anything
    unknown or unreadable counts as not alive, so GitHub's own timer then behaves as the full backstop."""
    try:
        tick, prev = dt.datetime.fromisoformat(ck["post_tick"]), last_slot_before(ctl, now)
        return bool(prev) and tick >= prev - dt.timedelta(minutes=2)
    except Exception:
        return False


def wait_for_slot(ctl, max_wait_min=15, alive=False):
    """A run from GitHub's own timer can start shortly before a slot. Returns the minutes of "early" posting allowed.
    Clock missing its times: wait for the slot (up to 15 minutes), so the reel goes out on time: the backstop.
    Clock alive: do not wait on a paid runner; the clock posts that reel at its time, and this run leaves it alone."""
    now = status.now()
    for s in slots(ctl):
        h, m = (int(x) for x in s.split(":"))
        t = now.replace(hour=h, minute=m, second=0, microsecond=0)
        if dt.timedelta(0) < t - now <= dt.timedelta(minutes=max_wait_min):
            if alive:
                print(f"The {s} slot is close and the clock is on time: left to the clock (no waiting on the runner).")
                return 0
            print(f"Waiting {int((t - now).total_seconds())} s for the {s} slot.")
            time.sleep((t - now).total_seconds())
            return 5
    return 5


RELEASABLE = ("Held by Harish.", "Not posted: the master switch was on Hold.")


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
        elif cmd == "post_now" and not r.get("now_done") and (st == "ready" or (st == "held" and str(r.get("reason", "")).startswith(RELEASABLE))):
            # also releases a reel Harish held, or one that waited while the switch was on Hold; never one that failed inspection
            day.upsert(r["reel_id"], state="ready", reason=None, post_at=status.now().isoformat(timespec="seconds"), reserve=False, now_done=True)


def watch_due(ck, now):
    """The news watch runs with the Post run at every slot. A second run close behind it (GitHub's late timer, a button)
    skips it: the same feeds were read minutes ago. The gap is shorter than the shortest gap between two slots."""
    try:
        return now - dt.datetime.fromisoformat(ck["watch_at"]) >= dt.timedelta(minutes=float(_post_cfg().get("watch_gap_minutes", 50)))
    except Exception:
        return True


def extras(drive, ctl, ck=None, tick=False):
    now, ck = status.now(), dict(ck if ck is not None else clock_file(drive))
    ck.pop("updated", None)
    jobs = [("2-hour stats", "engine.measure", "checkpoints")]
    if watch_due(ck, now):
        jobs.insert(0, ("news watch", "engine.watch", "run"))
        ck["watch_at"] = now.isoformat(timespec="seconds")
    else:
        print("news watch: read a short while ago, not repeated")
    if tick:
        ck["post_tick"] = now.isoformat(timespec="seconds")
    if tick or jobs[0][0] == "news watch":
        status.write(drive, "clock.json", ck)
    for name, mod, fn in jobs:
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
    ck, early = clock_file(drive), 5
    tick = a.no_wait and not (a.now or a.dry)   # started on time by the clock (or by hand), not by GitHub's own timer
    if not (a.no_wait or a.dry):
        t0 = time.time()
        early = wait_for_slot(ctl, alive=clock_alive(ck, ctl, status.now()))
        if time.time() - t0 > 5:
            ctl = Control(drive)                # the switch may have changed while waiting
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
        respect, out = respect_today(drive, day.date, ctl), []
        for r in [x for x in day.reels("ready") if x.get("now_done") and x.get("drive_reel")]:      # "post now" from the Control Room
            out.append(f"{r['reel_id']}: " + deliver(drive, day, r, ctl, respect, forced=True) + " (post now)")
        r = choose(day, bank, status.now(), ctl, early_min=early)
        if r:
            out.append(f"{r['reel_id']}: " + deliver(drive, day, r, ctl, respect))
        result = "; ".join(out) or result
    if day.dirty or not day.data.get("updated"):        # nothing changed: nothing to write (each Drive write is runner time)
        day.save()
    if bank.dirty or not bank.data.get("updated"):
        bank.save()
    status.write(drive, "post.json", {"last": result, "phase": ctl.phase, "switch": ctl.mode})
    print(result)
    if not (a.skip_extras or a.dry):
        extras(drive, ctl, ck, tick)
    elif tick:
        status.write(drive, "clock.json", {**{k: v for k, v in ck.items() if k != "updated"}, "post_tick": status.now().isoformat(timespec="seconds")})


if __name__ == "__main__":
    main()
