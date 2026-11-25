"""Manual work (AGENT.md 16.6): every job that needs Harish to act on his laptop, in one list.

Each job says what it is, why it is needed, when it is due, which reels or runs suffer if it is skipped, and the exact
command to paste. The panel carries the list (Control Room tab "Manual work", the badge, the chat's panel section).
"Done" on the page goes through the inbox (relay `manual_done`): the job leaves the list and the Engine starts the
step that picks up the files. Two days before a job turns urgent, and again when it turns urgent, an alert is raised,
so no run waits halfway.

Since 22 Nov (Harish) the downloads are ONE job, the laptop run, every 15-20 days (engine/laptop.py builds its list):
  trailers   Drive status/trailers_wanted.json (Make and the news watch add films), and the film-bank top-up
  study      Drive requests/study_to_get.md: shorts YouTube will not give the cloud
  songs      this month's trending songs (niches/<niche>/knowledge/trending_songs.yaml, AGENT.md 5.4)
  sign-in    its own card, only while the Engine still uses the robot account (it cannot create new Drive files)
State: Drive status/manual.json (first seen, warnings sent). Done marks: Drive control/manual.json (written by the relay).
Settings: config/engine.yaml `manual`.
"""
import datetime as dt
import json

from .settings import ENGINE
from . import status

CFG = {"urgent_hours": 24, "warn_days": 2, "make_hours": 3, "news_hours": 24, "other_days": 3, "topup_days": 14,
       "done_hold_hours": 48, "laptop_every_days": 15, "fallback_after": 3, "laptop_late_days": 20, "laptop_first_days": 3, **(ENGINE.get("manual") or {})}
ORDER = {"overdue": 0, "urgent": 1, "soon": 2, "later": 3}


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


def fetch_fails(drive):
    """Nights in a row the cloud fetch (engine/autofetch.py) failed; 0 when it works or has not run yet."""
    try:
        return int((drive.read_json("status", "autofetch.json") or {}).get("fails_in_a_row") or 0)
    except Exception:
        return 0


def laptop_jobs(drive, now, seen, done):
    """The laptop run (Harish, 22 Nov): one job every 15-20 days for every download the cloud cannot do."""
    from . import laptop
    fails = fetch_fails(drive)
    if fails < int(CFG["fallback_after"]):          # cloud first (Harish, 25 Nov): the laptop is the rare fallback
        return []
    t = laptop.todo(drive)
    c = laptop.counts(t)
    if not any(c.values()):
        return []
    runs = sorted(dt.datetime.fromisoformat(d["at"]) for d in done.values()
                  if isinstance(d, dict) and d.get("at") and d.get("kind") in ("laptop", "trailers", "topup", "study"))
    last = runs[-1] if runs else None
    due = last + dt.timedelta(days=CFG["laptop_late_days"]) if last else seen.get("laptop-first", now) + dt.timedelta(days=CFG["laptop_first_days"])
    parts = [f"{c['trailers']} trailer{'s' if c['trailers'] != 1 else ''} for coming reels" if c["trailers"] else "",
             f"{c['topup']} older film trailer{'s' if c['topup'] != 1 else ''} (library top-up)" if c["topup"] else "",
             f"{c['study']} competitor short{'s' if c['study'] != 1 else ''} to study" if c["study"] else "",
             f"{c['songs']} trending song{'s' if c['songs'] != 1 else ''}" if c["songs"] else ""]
    parts = [x for x in parts if x]
    suffers = []
    if c["trailers"]:
        suffers.append(f"{c['trailers']} coming reel{'s' if c['trailers'] != 1 else ''} use official YouTube frames instead of trailer moments")
    if c["study"]:
        suffers.append(f"the Weekly learning run learns from {c['study']} fewer competitor shorts")
    if c["songs"]:
        suffers.append("reels use the library music instead of this month's trending songs")
    if c["topup"]:
        suffers.append("later breakdowns of older films use still pictures")
    since = (f"Last run {(now - last).days} days ago. " if last else
             "First time: do the 4 set-up steps in 'How to do the laptop run' above (Python, Drive for desktop, the iNiKKi folder, "
             "the iNiKKi Laptop Run file). ")
    return [{"id": f"laptop-after-{last.strftime('%Y%m%d%H%M')}" if last else f"laptop-first-{now.strftime('%Y%m%d')}", "kind": "laptop", "items": parts,
             "title": "Laptop run: " + ", ".join(parts),
             "what": since + "Every 15 to 20 days: double-click 'iNiKKi Laptop Run' in the iNiKKi folder on your Desktop (set-up steps: "
                     "'How to do the laptop run' above). Keep the window open about 30 to 60 minutes. If Google Drive for desktop is on "
                     "the laptop the files go straight into Drive; otherwise drag every file in for_drive into Google Drive › iNiKKi Reels › from-laptop.",
             "why": f"The cloud downloads failed {fails} nights in a row, so the laptop is needed this time: " + "; ".join(parts) + ".",
             "suffers": suffers[:4], "due": due, "command": "Double-click: Desktop › iNiKKi › iNiKKi Laptop Run",
             "after": "The Engine sorts the files, makes the trailer shot grids, studies the shorts and tags the songs at once."}]


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
    for fn in (lambda: laptop_jobs(drive, now, seen, done), lambda: signin_jobs(drive, now, seen)):
        try:
            jobs += fn()
        except Exception as e:                                   # fail soft: one source, never the list
            print("manual work: a source was not readable:", str(e)[:140])
    out = []
    for j in jobs:
        if j["id"] in done:
            continue
        j["items"] = [i for i in j["items"] if i not in hold] if j["kind"] not in ("signin", "laptop") else j["items"]
        if j["kind"] == "laptop" and any(isinstance(d, dict) and d.get("kind") == "laptop" and d.get("at") and
                                         now - dt.datetime.fromisoformat(d["at"]) < dt.timedelta(hours=CFG["done_hold_hours"]) for d in done.values()):
            continue                                             # just done: the Engine is picking the files up
        if not j["items"]:
            continue
        lvl = level(j["due"], now)
        out.append({**j, "level": lvl, "due_text": due_text(j["due"], now), "due": _iso(j["due"])})
    out.sort(key=lambda j: (ORDER[j["level"]], j["due"]))
    new_seen = {k: _iso(v) for k, v in seen.items()}
    for j in out:
        new_seen.setdefault(j["id"], _iso(now))
        if j["kind"] == "laptop":
            new_seen.setdefault("laptop-first", _iso(now))
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
AFTER = {"trailers": [["trailers.yml", "-f", "adopt=true"]], "topup": [["trailers.yml", "-f", "adopt=true"]], "study": [["study.yml"]],
         "laptop": [["trailers.yml", "-f", "adopt=true"], ["study.yml"], ["music.yml"]]}


def start_after(kind):
    """Start the pick-up step at once. Returns a plain line. Fails soft: the nightly run picks the files up anyway."""
    runs = AFTER.get(kind)
    if not runs:
        return "nothing to start"
    import os
    import subprocess
    out = []
    for args in runs:
        name = args[0].replace(".yml", "")
        try:
            r = subprocess.run(["gh", "workflow", "run", args[0], "--ref", os.environ.get("GITHUB_REF_NAME", "main"), *args[1:]],
                               capture_output=True, text=True, timeout=60)
            out.append(f"started {name} now" if r.returncode == 0 else f"{name} at its next scheduled run")
        except Exception:
            out.append(f"{name} at its next scheduled run")
    return "; ".join(out)
