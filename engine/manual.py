"""Manual work (AGENT.md 16.6): every job that needs Harish to act on his laptop, in one list.

Each job says what it is, why it is needed, when it is due, which reels or runs suffer if it is skipped, and the exact
command to paste. The panel carries the list (Control Room tab "Manual work", the badge, the chat's panel section).
"Done" on the page goes through the inbox (relay `manual_done`): the job leaves the list and the Engine starts the
step that picks up the files. Two days before a job turns urgent, and again when it turns urgent, an alert is raised,
so no run waits halfway.

Sources, all read from Drive or the repository (no AI, no keys):
  trailers   Drive status/trailers_wanted.json (Make and the news watch add films) → the laptop helper fetches them
  top-up     film-bank films with no trailer in the library (low urgency)
  study      Drive requests/study_to_get.md: shorts YouTube will not give the cloud → read before the Weekly run
  sign-in    only while the Engine still uses the robot account (it cannot create new Drive files)
State: Drive status/manual.json (first seen, warnings sent). Done marks: Drive control/manual.json (written by the relay).
Settings: config/engine.yaml `manual`.
"""
import datetime as dt
import hashlib
import json
import re

from .settings import ENGINE, ROOT
from . import status

CFG = {"urgent_hours": 24, "warn_days": 2, "make_hours": 3, "news_hours": 24, "other_days": 3, "topup_days": 14,
       "done_hold_hours": 48, **(ENGINE.get("manual") or {})}
ORDER = {"overdue": 0, "urgent": 1, "soon": 2, "later": 3}


def _id(kind, items):
    return f"{kind}-" + hashlib.md5("|".join(sorted(items)).encode("utf-8")).hexdigest()[:8]


def _iso(t):
    return t.isoformat(timespec="minutes")


def level(due, now):
    """overdue · urgent (within urgent_hours) · soon (within warn_days before urgent: the warning) · later."""
    left = (due - now).total_seconds() / 3600
    if left <= 0:
        return "overdue"
    if left <= CFG["urgent_hours"]:
        return "urgent"
    if left <= CFG["urgent_hours"] + 24 * CFG["warn_days"]:
        return "soon"
    return "later"


def due_text(due, now):
    left = due - now
    when = due.strftime("%a %d %b, %H:%M")
    if left.total_seconds() <= 0:
        return f"overdue since {when}"
    h = int(left.total_seconds() // 3600)
    return f"by {when} (in {h // 24} d {h % 24} h)" if h >= 24 else f"by {when} (in {h} h {int(left.total_seconds() % 3600 // 60)} min)"


def plan_slot(reel_id):
    """(date, 'HH:MM') of a planned reel, from plans/<date>/<reel_id>.json; None when not found."""
    for f in sorted((ROOT / "plans").glob(f"*/{reel_id}.json")):
        try:
            d = json.loads(f.read_text(encoding="utf-8"))
            slot = str((d.get("package") or {}).get("slot") or d.get("slot") or "")
            if re.fullmatch(r"\d{1,2}:\d{2}", slot):
                return f.parent.name, slot
            return f.parent.name, None
        except Exception:
            continue
    return None


def _at(date, hm):
    h, m = (hm or "08:30").split(":")
    return dt.datetime.combine(dt.date.fromisoformat(date), dt.time(int(h), int(m)), status.now().tzinfo)


def trailer_jobs(drive, now, seen):
    from . import trailers as T
    names, topup, why, command, _ = T.request_parts(drive)
    jobs = []
    if names:
        dues, suffer = [], []
        for n in names:
            reason = str(why.get(n, ""))
            m = re.search(r"needed by the plan (\S+)", reason)
            spot = plan_slot(m.group(1)) if m else None
            if spot:
                due = _at(spot[0], spot[1]) - dt.timedelta(hours=CFG["make_hours"])
                suffer.append(f"{m.group(1)} ({spot[0]}{' ' + spot[1] if spot[1] else ''}): {n} has no trailer moments, so it uses still pictures")
            elif reason.startswith("news"):
                due = seen.get(f"film:{n}", now) + dt.timedelta(hours=CFG["news_hours"])
                suffer.append(f"the news reel about {n} goes out without the new trailer's moments")
            else:
                due = seen.get(f"film:{n}", now) + dt.timedelta(days=CFG["other_days"])
                suffer.append(f"the next reel about {n} uses still pictures")
            dues.append(due)
        jobs.append({"id": _id("trailers", names), "kind": "trailers", "items": names,
                     "title": f"Get {len(names)} trailer{'s' if len(names) != 1 else ''} with the laptop helper",
                     "what": "YouTube and Instagram do not let the cloud computers download these trailers, so your laptop does. "
                             "Open the folder with clip_helper.py, type cmd in the address bar, paste the line, press Enter. Then drag the "
                             "files in trailers_for_drive (helper_report.txt too) into Drive: iNiKKi Reels › clip-library.",
                     "why": "; ".join(f"{n}: {why.get(n) or 'needed by a coming reel'}" for n in names)[:600],
                     "suffers": suffer[:8], "due": min(dues), "command": command(names),
                     "after": "The Engine makes the shot grids from clip-library at once (trailer job, intake only)."})
    if topup:
        jobs.append({"id": _id("topup", topup), "kind": "topup", "items": topup,
                     "title": f"Library top-up: {len(topup)} older film trailer{'s' if len(topup) != 1 else ''}",
                     "what": "The same laptop helper, for films in the film bank that have no trailer in the library yet. "
                             "Then drag trailers_for_drive into Drive › clip-library.",
                     "why": "Breakdowns and recommendations of these films can then show real trailer moments.",
                     "suffers": ["future breakdowns and recommendations of these films use still pictures"],
                     "due": seen.get(_id("topup", topup), now) + dt.timedelta(days=CFG["topup_days"]), "command": command(topup),
                     "after": "The Engine makes the shot grids from clip-library at once (trailer job, intake only)."})
    return jobs


def next_weekly(now):
    """The Weekly run reads the study cards; the study job before it runs at 02:17, so the files must be in by Sunday 02:00."""
    days = (6 - now.weekday()) % 7
    d = (now + dt.timedelta(days=days)).replace(hour=2, minute=0, second=0, microsecond=0)
    return d if d > now else d + dt.timedelta(days=7)


def study_jobs(drive, now):
    """From Drive requests/study_to_get.md (written by the study job): its command line lists every short still waiting."""
    text = drive.read_text("requests", "study_to_get.md") or ""
    cmd = next((ln.strip() for ln in text.splitlines() if ln.strip().startswith("py clip_helper.py --study")), "")
    ids = cmd.split()[3:] if cmd else []
    if not ids:
        return []
    due = next_weekly(now)
    run_day = (due + dt.timedelta(hours=20, minutes=37)).strftime("%a %d %b")
    return [{"id": _id("study", [str(i) for i in ids]), "kind": "study", "items": [str(i) for i in ids],
             "title": f"Study {len(ids)} competitor short{'s' if len(ids) != 1 else ''} with the laptop helper",
             "what": "YouTube does not let the cloud computers fetch these shorts. Open the folder with clip_helper.py, type cmd in "
                     "the address bar, paste the line, press Enter. Then drag the files in study_for_drive into Drive › iNiKKi Reels › study-audio.",
             "why": "The channel study turns what top channels say into patterns the Weekly learning run uses.",
             "suffers": [f"Weekly learning run on {run_day}: learns from {len(ids)} fewer competitor shorts"],
             "due": due, "command": cmd, "after": "The Engine starts the study job at once and reads the audio."}]


def signin_jobs(drive, now, seen):
    if getattr(drive, "mode", None) != "service_account":
        return []
    return [{"id": "signin-drive", "kind": "signin", "items": ["drive"],
             "title": "Sign the Engine in to Google Drive as you (one time)",
             "what": "Run the line on your laptop in the inikki-reels folder, sign in, then add the single line it prints as the GitHub "
                     "secret GDRIVE_OAUTH_REFRESH_TOKEN (Settings › Secrets › Actions).",
             "why": "The robot account cannot create new files in your Drive (its storage limit is zero).",
             "suffers": ["every job that saves a new file to Drive (finished reels, new status files) can fail"],
             "due": seen.get("signin-drive", now), "command": "python tools/drive_signin.py",
             "after": "Nothing to start: the next job uses your sign-in by itself."}]


def build(drive, now=None, warn=True):
    """The list for the panel: open jobs, most urgent first. Updates Drive status/manual.json and raises the warnings."""
    now = now or status.now()
    state = drive.read_json("status", "manual.json") or {}
    seen = {k: dt.datetime.fromisoformat(v) for k, v in (state.get("seen") or {}).items()}
    done = (drive.read_json("control", "manual.json") or {}).get("done") or {}
    hold = {i for d in done.values() if isinstance(d, dict) and d.get("at")
            and now - dt.datetime.fromisoformat(d["at"]) < dt.timedelta(hours=CFG["done_hold_hours"]) for i in d.get("items") or []}
    jobs = []
    for fn in (lambda: trailer_jobs(drive, now, seen), lambda: study_jobs(drive, now), lambda: signin_jobs(drive, now, seen)):
        try:
            jobs += fn()
        except Exception as e:                                   # fail soft: one source, never the list
            print("manual work: a source was not readable:", str(e)[:140])
    out = []
    for j in jobs:
        if j["id"] in done:
            continue
        j["items"] = [i for i in j["items"] if i not in hold] if j["kind"] != "signin" else j["items"]
        if not j["items"]:
            continue
        lvl = level(j["due"], now)
        out.append({**j, "level": lvl, "due_text": due_text(j["due"], now), "due": _iso(j["due"])})
    out.sort(key=lambda j: (ORDER[j["level"]], j["due"]))
    new_seen = {k: _iso(v) for k, v in seen.items()}
    for j in out:
        new_seen.setdefault(j["id"], _iso(now))
        for i in j["items"]:
            new_seen.setdefault(f"film:{i}", _iso(now))
    warned = dict(state.get("warned") or {})
    if warn:
        for j in out:
            key = f"{j['id']}:{'warn' if j['level'] == 'soon' else 'urgent'}"
            if j["level"] == "later" or key in warned:
                continue
            warned[key] = _iso(now)
            ahead = j["level"] == "soon"
            status.alert(drive, f"Manual work {'due soon' if ahead else 'is urgent'}: {j['title']}",
                         f"Due {j['due_text']}. If it is skipped: {'; '.join(j['suffers'][:2])}.",
                         "Everything keeps running; this is your early warning." if ahead else "The Engine carries on with its fallback until you do it.",
                         "Control Room › Manual work: copy the command, run it on your laptop, then press Done.",
                         level="info" if ahead else "warn")
    keep = {k: v for k, v in new_seen.items() if now - dt.datetime.fromisoformat(v) < dt.timedelta(days=30)}
    try:
        status.write(drive, "manual.json", {"updated": status.stamp(), "seen": keep, "warned": {k: v for k, v in warned.items()
                                                                                                if now - dt.datetime.fromisoformat(v) < dt.timedelta(days=30)}})
    except Exception as e:
        print("manual work: state not saved:", str(e)[:120])
    return {"count": len(out), "urgent": sum(1 for j in out if j["level"] in ("overdue", "urgent")),
            "warn_days": CFG["warn_days"], "jobs": out}


# what "Done" starts, per kind (relay `manual_done`); a job that needs nothing started is just marked done
AFTER = {"trailers": ["trailers.yml", "-f", "adopt=true"], "topup": ["trailers.yml", "-f", "adopt=true"], "study": ["study.yml"]}


def start_after(kind):
    """Start the pick-up step at once. Returns a plain line. Fails soft: the nightly run picks the files up anyway."""
    args = AFTER.get(kind)
    if not args:
        return "nothing to start"
    import os
    import subprocess
    try:
        r = subprocess.run(["gh", "workflow", "run", args[0], "--ref", os.environ.get("GITHUB_REF_NAME", "main"), *args[1:]],
                           capture_output=True, text=True, timeout=60)
        if r.returncode == 0:
            return f"started {args[0].replace('.yml', '')} now"
        return f"picked up at its next scheduled run ({(r.stderr or '').strip()[:80] or 'could not start it from this job'})"
    except Exception as e:
        return f"picked up at its next scheduled run ({str(e)[:80]})"
