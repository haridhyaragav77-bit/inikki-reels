"""Make job (AGENT.md 4.3): plans → finished reels in Drive, ready for their slot.

    python -m engine.make                     today's plans (IST) plus the breakdown bank
    python -m engine.make --date 2026-11-13   another day
    python -m engine.make --check             only say whether anything new needs making (for the light first step)

Rehearsal phase: reels go to Drive rehearsal/<date>/. Live phase: finished/<date>/. A reel that fails the plan check or
inspection is held, and a reserve or bank reel takes its slot at post time (fail soft: one reel, never the day).
Breaking news posts as soon as it is made when live (AGENT.md 10.2)."""
import argparse
import hashlib
import json
import os
import sys
import traceback

from .settings import ROOT, niche_dir
from . import status
from .control import Control
from .day import Bank, Day, slot_time, today


def plan_files(date):
    d, b = ROOT / "plans" / date, ROOT / "plans" / "bank"
    day = sorted(p for p in d.glob("*.json") if p.name != "respect.json") if d.exists() else []
    return day, (sorted(b.glob("*.json")) if b.exists() else [])


def caption_of(plan):
    c = plan.get("caption") or {}
    pk = plan.get("package") or {}          # the approved plan form keeps the caption in "package" (templates/README.md)
    text = c.get("text") or pk.get("caption") or ""
    if isinstance(text, list):
        text = "\n\n".join(str(x).strip() for x in text if str(x).strip())
    tags = " ".join(t if t.startswith("#") else "#" + t for t in (c.get("hashtags") or pk.get("hashtags") or []))
    text = str(text).strip()
    return (text + ("\n\n" + tags if tags else "")).strip(), (c.get("first_comment") or pk.get("first_comment") or "").strip()


def held_reason(problems):
    """Why a made reel did not pass inspection, with what fixes it, in plain words."""
    why = "Inspection: " + "; ".join(problems[:2])
    if any("stand-in" in p for p in problems):
        why += (". No real pictures were found. Trailers in Drive clip-library, or the free photo keys PEXELS_API_KEY and"
                " PIXABAY_API_KEY, fix this; the reel is then made again with --retry.")
    return why


def clip_films(plan):
    out = []
    def walk(v):
        if isinstance(v, dict):
            if v.get("type") == "clip" and v.get("film") and not v.get("reference"):
                out.append(v["film"])
            if v.get("type") == "image" and isinstance(v.get("still"), dict) and v["still"].get("film"):
                out.append(v["still"]["film"])
            for k in ("top", "bottom", "left", "right"):
                walk(v.get(k))
    for s in plan.get("screens", []):
        walk(s.get("visual"))
    for im in plan.get("images") or []:
        if isinstance(im.get("trailer"), dict) and im["trailer"].get("film"):
            out.append(im["trailer"]["film"])
    return list(dict.fromkeys(out))


def need_trailers(drive, plan, visuals=None):
    """Films the plan cuts from that are not in the clip library yet: fetched now from the official accounts
    (engine/trailers.py); for updates (visuals: official) the film's official stills are enough. Any still missing go on
    the wanted list and are returned."""
    from . import trailers
    films = clip_films(plan)
    if not films:
        return []
    idx = trailers.index(drive)
    official = visuals == "official"
    missing = [f for f in films if not trailers.have(f, idx) and not (official and trailers.have_stills(f, idx))]
    if not missing:
        return []
    hint = "+".join(plan.get("trailer_from") or [])       # the film's own accounts, named in the plan: searched first
    missing = [f"{f}@{hint}" if hint else f for f in missing]
    try:
        from .instagram import Instagram
        ig = Instagram()
        trailers.CACHE["drive"] = drive
        for f in list(missing):
            try:
                trailers.fetch(drive, ig, f)
                missing.remove(f)
            except Exception as e:
                print(f"trailer for {f}: {str(e)[:160]}", file=sys.stderr)
                if official and not isinstance(e, trailers.OutOfCalls):
                    try:
                        trailers.stills(drive, ig, f)
                        missing.remove(f)
                    except Exception as e2:
                        print(f"official stills for {f}: {str(e2)[:160]}", file=sys.stderr)
        trailers.save_cache()
    except Exception as e:
        print("trailers could not be fetched now:", str(e)[:160], file=sys.stderr)
    if missing:
        trailers.want(drive, missing, why=f"needed by the plan {plan.get('reel_id', '')}")
    return missing


def plan_hash(path):
    return hashlib.md5(path.read_bytes()).hexdigest()[:12]


def is_done(rec, h, retry=False):
    """Already made from this exact plan (or already posted): skip, so re-runs cost nothing.
    With retry, held and failed reels are made again (after trailers or picture keys were added)."""
    if not rec:
        return False
    if rec.get("state") in ("posted", "rehearsed", "used"):
        return True
    if retry and rec.get("state") in ("held", "failed") and not str(rec.get("reason", "")).startswith("Plan check"):
        return False
    if rec.get("hash") == h and rec.get("state") == "skipped" and rec.get("reason") == "Skipped by Harish.":
        return True                                # his skip stands; the reel is not made again
    return rec.get("hash") == h and rec.get("state") in ("ready", "held")


def todo(day, bank, date, only=(), retry=False):
    files, bank_files = plan_files(date)
    out = []
    for p, ledger, is_bank in [(f, day, False) for f in files] + [(f, bank, True) for f in bank_files]:
        d = json.loads(p.read_text(encoding="utf-8"))
        rid = d.get("reel_id") or d.get("id") or p.stem
        if (not only or rid in only) and not is_done(ledger.get(rid), plan_hash(p), retry):
            out.append((p, is_bank))
    return out


def saving(drive, ctl):
    """The month's runner-minute stage (engine/health.py): tight = reserves and bank reels wait; cap = reels a day at the end."""
    try:
        mins = drive.read_json("status", "minutes.json") or {}
    except Exception:
        mins = {}
    from .settings import ENGINE
    tight = bool(mins.get("tight")) or ctl.on("saver", False)
    return tight, int(ENGINE.get("runner", {}).get("last_reels_day", 3)) if mins.get("stage") == "last" else None


def still_waiting(rec, plan, is_bank, h, tight, cap_day, ctl):
    """This exact plan was skipped by an earlier run for a reason that still holds (minutes being saved, series paused).
    The light check then does not count it, so the heavy tools are not installed just to skip it again."""
    if not rec or rec.get("state") != "skipped" or rec.get("hash") != h:
        return False
    reserve = plan.get("reserve") or str((plan.get("package") or {}).get("slot") or "").lower() == "reserve"
    if tight and (is_bank or reserve):
        return True
    if cap_day is not None and str(rec.get("reason", "")).startswith("Runner minutes are almost used up"):
        return True
    from . import dayplan
    return ctl.series_paused(plan.get("series", "")) or bool(dayplan.off(ctl, plan.get("series", "")))


DRAFT_NOTE = "Draft series: made for you to watch; it is never posted. Move the series to trial in the Control Room to post it."


def pending_tests(drive, ctl):
    done = {}
    try:
        done = (drive.read_json("status", "tests.json") or {}).get("done") or {}
    except Exception:
        pass
    return [c for c in ctl.lines("commands.jsonl") if c.get("cmd") == "test" and c.get("id") not in done], done


def tests(drive, ctl, out_root="rehearsal"):
    """"Test this series" from the Control Room: its reference reel is made with today's settings (voice, look, pace) and
    put in Drive rehearsal/tests/<series>. Never posted. One reel per press; a failure is written down, never raised."""
    todo, done = pending_tests(drive, ctl)
    if not todo:
        return
    from . import render
    for c in todo[:2]:
        sid = c.get("series")
        ref = ((ctl.series(sid, niche_dir()).get("reference") or {}).get("plan"))
        rec = {"series": sid, "at": status.stamp(), "ok": False}
        try:
            if not ref or not (ROOT / ref).exists():
                rec["note"] = "This series has no reference reel yet. Its first planned reel becomes the test."
            else:
                r = render.render(str(ROOT / ref), drive=drive, to_drive=f"rehearsal/tests/{sid}")
                rec.update(ok=bool(r.get("ok")), link=r.get("link"), seconds=round(r.get("total_s") or 0, 1),
                           note="Made. Watch it in Drive." if r.get("ok") else "Made, but it did not pass inspection: " + "; ".join((r.get("qc") or {}).get("problems") or [])[:200])
        except Exception as e:
            rec["note"] = f"Could not be made: {str(e)[:160]}"
        done[c["id"]] = rec
        print(f"test {sid}: {rec['note']}")
    status.write(drive, "tests.json", {"done": dict(list(done.items())[-30:])})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", default=None)
    ap.add_argument("--only", default="", help="comma-separated reel ids")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--retry", action="store_true", help="make held or failed reels again")
    a = ap.parse_args()
    from .drive import Drive
    drive = Drive()
    ctl = Control(drive)
    date = a.date or today()
    only = {x.strip() for x in a.only.split(",") if x.strip()}
    day, bank = Day(drive, date), Bank(drive)
    jobs = todo(day, bank, date, only, a.retry)
    tight, cap_day = saving(drive, ctl)
    if a.check:
        waiting = len(pending_tests(drive, ctl)[0])

        def waits(path, is_bank):
            plan = json.loads(path.read_text(encoding="utf-8"))
            rid = plan.get("reel_id") or plan.get("id") or path.stem
            return still_waiting((bank if is_bank else day).get(rid), plan, is_bank, plan_hash(path), tight, cap_day, ctl)
        jobs = [j for j in jobs if not waits(*j)]
        print(f"{len(jobs)} reel(s) to make, {waiting} test reel(s)")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"todo={'true' if (jobs or waiting) and ctl.mode != 'sleep' else 'false'}\n")
        return
    if ctl.mode == "sleep":
        status.write(drive, "make.json", {"state": "asleep", "date": date, "note": "The master switch says Sleep. Nothing was made."})
        print("Asleep: nothing made.")
        return
    from . import render, plancheck
    out_root = "finished" if ctl.phase == "live" else "rehearsal"
    made, held, skipped = [], [], []
    tests(drive, ctl, out_root)
    for path, is_bank in jobs:
        plan = json.loads(path.read_text(encoding="utf-8"))
        rid, series = plan.get("reel_id") or plan.get("id") or path.stem, plan.get("series", "")
        pslot = str((plan.get("package") or {}).get("slot") or "")
        if pslot.lower() == "reserve":
            plan["reserve"] = True
        elif not plan.get("slot") and pslot:
            plan["slot"] = pslot
        ledger = bank if is_bank else day
        if tight and (is_bank or plan.get("reserve")):      # cost guard (CLAUDE.md rule 5): main reels first
            ledger.upsert(rid, series=series, hash=plan_hash(path), state="skipped", reason="Saving runner minutes this month: reserves and bank reels wait.")
            skipped.append(rid)
            continue
        if cap_day is not None and not is_bank and series != "breaking-news" and \
                len([r for r in day.reels("ready", "posted", "rendering") if r["reel_id"] != rid]) >= cap_day:
            ledger.upsert(rid, series=series, hash=plan_hash(path), state="skipped", reason=f"Runner minutes are almost used up this month: only {cap_day} new reels a day until the 1st, so posting never stops.")
            skipped.append(rid)
            continue
        try:
            when = slot_time(plan, date)
        except Exception:                                    # fail soft: a bad time holds this reel, not the day
            when = None
        first = (plan.get("screens") or [{}])[0]
        base = dict(series=series, post_at=when.isoformat() if when and not is_bank else None,
                    slot=when.strftime("%H:%M") if when and not is_bank else None, reserve=bool(plan.get("reserve")) or None,
                    for_slot=plan.get("for_slot"), trial=plan.get("trial"), tribute=bool(plan.get("tribute")) or None,
                    manual=bool(plan.get("manual")) or None, remake_of=plan.get("remake_of"),
                    hash=plan_hash(path), hook=first.get("headline") or first.get("line") or (plan.get("package") or {}).get("cover"), virality=(plan.get("virality") or {}).get("total_100"))
        from . import dayplan
        why = "The series is paused." if ctl.series_paused(series) else dayplan.off(ctl, series)
        cap = dayplan.chosen(ctl.overrides, series) if dayplan.roles(ctl.settings).get(series, ("",))[0] == "extra" else None
        if not why and cap and not is_bank and len([r for r in day.reels("ready", "posted", "rendering") if r.get("series") == series and r["reel_id"] != rid]) >= cap:
            why = f"Already {cap} {series} reel(s) today, the most set in the Control Room."
        if why and not plan.get("manual"):
            ledger.upsert(rid, **base, state="skipped", reason=why)
            skipped.append(rid)
            continue
        errors, _ = plancheck.check(plan)
        card = ctl.series(series, niche_dir())
        visuals, draft = card.get("visuals"), card.get("status") == "draft"
        missing = need_trailers(drive, plan, visuals)       # asked for even when the plan still needs its moments picked
        if missing and visuals in ("clips", "official"):
            films = [m.split("@")[0] for m in missing]
            ledger.upsert(rid, **base, state="held", waiting_for=films, reason=f"No trailer yet for {', '.join(films)} (on the trailer wanted list; "
                          "once it arrives the planning run picks the moments from its grid and the reel is made).")
            held.append(rid)
            continue
        if errors:
            ledger.upsert(rid, **base, state="held", reason="Plan check: " + " ".join(errors[:2]))
            held.append(rid)
            continue
        ledger.upsert(rid, **base, state="rendering", reason=None, waiting_for=[])
        ledger.save()
        try:
            r = render.render(str(path), drive=drive, to_drive=f"rehearsal/drafts/{series}" if draft else f"{out_root}/{'bank' if is_bank else date}")
        except Exception as e:
            traceback.print_exc()
            ledger.upsert(rid, state="failed", reason=f"Could not be made: {str(e)[:160]}")
            ledger.save()
            held.append(rid)
            continue
        cap, comment = caption_of(plan)
        ok = r["ok"] and r["ids"].get("reel")
        ledger.upsert(rid, state=("rehearsed" if draft else "ready") if ok else "held",
                      reason=(DRAFT_NOTE if draft else None) if ok else held_reason(r["qc"].get("problems") or ["not uploaded"]),
                      seconds=round(r["total_s"], 1), cover_t=r["cover_t"], music=r["music"], drive_reel=r["ids"].get("reel"),
                      drive_cover=r["ids"].get("cover"), link=r["link"], caption=cap, first_comment=comment,
                      images_made=r["images_made"], made_at=status.now().isoformat(timespec="seconds"))
        ledger.save()
        (made if ok else held).append(rid)
        if ok and not draft and not is_bank and series == "breaking-news" and ctl.can_post:     # cannot wait for a slot
            from . import post
            post.breaking_now(drive, day, rid, ctl)
        elif ok and not draft and not is_bank and not plan.get("reserve") and ctl.can_post:
            # uploaded to Instagram now, unpublished, so the Post run at its slot only publishes (fewer runner minutes)
            from . import post
            if post.prepare(drive, day, rid, local=r.get("reel")):
                day.save()
    day.save()
    bank.save()
    summary = {"date": date, "phase": ctl.phase, "switch": ctl.mode, "made": made, "held": held, "skipped": skipped,
               "bank_ready": len(bank.reels("ready"))}
    status.write(drive, "make.json", summary)
    print(json.dumps(summary, ensure_ascii=False))
    if held:
        status.alert(drive, f"{len(held)} reel(s) held for {date}",
                     "Some reels did not pass the plan check or inspection: " + ", ".join(held[:4]) + ".",
                     "They will not post. A reserve or a bank reel takes their slot.", "nothing", level="warn")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        traceback.print_exc()
        try:
            from .drive import Drive
            status.write(Drive(), "make.json", {"state": "failed", "error": str(e)[:300]})
        except Exception:
            status.local_write("make.json", {"state": "failed", "error": str(e)[:300]})
        sys.exit(1)
