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
    text = str(c.get("text") or "").strip()
    tags = " ".join(t if t.startswith("#") else "#" + t for t in (c.get("hashtags") or []))
    return (text + ("\n\n" + tags if tags else "")).strip(), (c.get("first_comment") or "").strip()


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
        trailers.want(drive, missing)
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
    return rec.get("hash") == h and rec.get("state") in ("ready", "held")


def todo(day, bank, date, only=(), retry=False):
    files, bank_files = plan_files(date)
    out = []
    for p, ledger, is_bank in [(f, day, False) for f in files] + [(f, bank, True) for f in bank_files]:
        rid = json.loads(p.read_text(encoding="utf-8")).get("reel_id") or p.stem
        if (not only or rid in only) and not is_done(ledger.get(rid), plan_hash(p), retry):
            out.append((p, is_bank))
    return out


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
    if a.check:
        print(f"{len(jobs)} reel(s) to make")
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write(f"todo={'true' if jobs and ctl.mode != 'sleep' else 'false'}\n")
        return
    if ctl.mode == "sleep":
        status.write(drive, "make.json", {"state": "asleep", "date": date, "note": "The master switch says Sleep. Nothing was made."})
        print("Asleep: nothing made.")
        return
    from . import render, plancheck
    out_root = "finished" if ctl.phase == "live" else "rehearsal"
    try:
        tight = bool((drive.read_json("status", "minutes.json") or {}).get("tight"))
    except Exception:
        tight = False
    made, held, skipped = [], [], []
    for path, is_bank in jobs:
        plan = json.loads(path.read_text(encoding="utf-8"))
        rid, series = plan.get("reel_id") or path.stem, plan.get("series", "")
        ledger = bank if is_bank else day
        if tight and (is_bank or plan.get("reserve")):      # cost guard (CLAUDE.md rule 5): main reels first
            ledger.upsert(rid, series=series, state="skipped", reason="Runner minutes are nearly used up this month: reserves and bank reels wait.")
            skipped.append(rid)
            continue
        when = slot_time(plan, date)
        first = (plan.get("screens") or [{}])[0]
        base = dict(series=series, post_at=when.isoformat() if when and not is_bank else None,
                    slot=when.strftime("%H:%M") if when and not is_bank else None, reserve=bool(plan.get("reserve")) or None,
                    for_slot=plan.get("for_slot"), trial=plan.get("trial"), tribute=bool(plan.get("tribute")) or None,
                    hash=plan_hash(path), hook=first.get("headline") or first.get("line"), virality=(plan.get("virality") or {}).get("total_100"))
        if ctl.series_paused(series):
            ledger.upsert(rid, **base, state="skipped", reason="The series is paused.")
            skipped.append(rid)
            continue
        errors, _ = plancheck.check(plan)
        visuals = ctl.series(series, niche_dir()).get("visuals")
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
            r = render.render(str(path), drive=drive, to_drive=f"{out_root}/{'bank' if is_bank else date}")
        except Exception as e:
            traceback.print_exc()
            ledger.upsert(rid, state="failed", reason=f"Could not be made: {str(e)[:160]}")
            ledger.save()
            held.append(rid)
            continue
        cap, comment = caption_of(plan)
        ok = r["ok"] and r["ids"].get("reel")
        ledger.upsert(rid, state="ready" if ok else "held",
                      reason=None if ok else held_reason(r["qc"].get("problems") or ["not uploaded"]),
                      seconds=round(r["total_s"], 1), cover_t=r["cover_t"], music=r["music"], drive_reel=r["ids"].get("reel"),
                      drive_cover=r["ids"].get("cover"), link=r["link"], caption=cap, first_comment=comment,
                      images_made=r["images_made"], made_at=status.now().isoformat(timespec="seconds"))
        ledger.save()
        (made if ok else held).append(rid)
        if ok and not is_bank and series == "breaking-news" and ctl.can_post:     # cannot wait for a slot
            from . import post
            post.breaking_now(drive, day, rid, ctl)
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
