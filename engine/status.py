"""Status files in Drive status/ (written by every job, even on failure: CLAUDE.md rule 6)."""
import datetime as dt
import json
import os
from zoneinfo import ZoneInfo

from .settings import AGENT, OUT

IST = ZoneInfo(AGENT.get("timezone", "Asia/Kolkata"))


def now():
    return dt.datetime.now(IST)


def stamp():
    return now().strftime("%Y-%m-%d %H:%M IST")


def local_write(name, obj):
    """Fallback when Drive is not writable: keep the status file in out/status for the run artifact."""
    os.makedirs(OUT / "status", exist_ok=True)
    with open(OUT / "status" / name, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    return OUT / "status" / name


def write(drive, name, obj):
    from .mask import clean
    obj = clean(dict(obj))                     # a key that slipped into an error message is masked before it is saved
    obj.setdefault("updated", stamp())
    local_write(name, obj)
    if drive:
        try:
            drive.write_json("status", name, obj)
            return True
        except Exception:
            return False
    return False


def alert(drive, title, happened, did, you_do="nothing", level="info"):
    """Bad news in the Advisor's shape: what happened → what was done → what you need to do."""
    item = {"id": now().strftime("%Y%m%d-%H%M%S"), "at": stamp(), "level": level, "title": title,
            "what_happened": happened, "what_was_done": did, "what_you_do": you_do, "open": True}
    current = {"alerts": []}
    if drive:
        try:
            current = drive.read_json("status", "alerts.json", {"alerts": []}) or {"alerts": []}
        except Exception:
            pass
    current["alerts"] = [item] + current.get("alerts", [])[:49]
    write(drive, "alerts.json", current)
    return item


def job_end(name, result):
    """Last step of every workflow, even on failure (CLAUDE.md rule 6): Drive status/jobs.json, plus an alert on failure."""
    from .drive import Drive
    drive = None
    try:
        drive = Drive()
    except Exception:
        pass
    run = f"{os.environ.get('GITHUB_SERVER_URL', '')}/{os.environ.get('GITHUB_REPOSITORY', '')}/actions/runs/{os.environ.get('GITHUB_RUN_ID', '')}"
    jobs = {"jobs": {}}
    if drive:
        try:
            jobs = drive.read_json("status", "jobs.json") or jobs
        except Exception:
            pass
    jobs.setdefault("jobs", {})[name] = {"result": result, "at": stamp(), "run": run}
    if result not in ("success", "skipped", "cancelled"):     # failed runs are kept for the Control Room (last 40)
        jobs["failed"] = [{"job": name, "result": result, "at": stamp(), "iso": now().isoformat(timespec="minutes"), "run": run}] + (jobs.get("failed") or [])[:39]
    write(drive, "jobs.json", jobs)
    if result not in ("success", "skipped", "cancelled"):
        alert(drive, f"The {name} job did not finish", f"The {name} job stopped with: {result}.",
              "One reel or one step is affected, not the day; the next run starts fresh.", f"Nothing, unless it repeats. Details: {run}", level="warn")
    if drive:                                    # the Control Room account can always see the folder (AGENT.md 13.3)
        try:
            from . import guard
            if guard.control_room_email():
                guard.link_control_room(drive, guard.control_room_email())
        except Exception as e:
            print("status: Control Room sharing skipped:", str(e)[:120])
    if drive:                                    # the Control Room's one file, fresh after every job (AGENT.md 13.3)
        try:
            from . import panel
            panel.save(drive)
        except Exception as e:
            print("panel not updated:", str(e)[:200])


def recent(name, hours):
    """True when the job `name` ended well within the last `hours` (Drive status/jobs.json). Unknown counts as no."""
    try:
        from .drive import Drive
        j = ((Drive().read_json("status", "jobs.json") or {}).get("jobs") or {}).get(name) or {}
        at = dt.datetime.strptime(j["at"], "%Y-%m-%d %H:%M IST").replace(tzinfo=IST)
        return j.get("result") == "success" and dt.timedelta(0) <= now() - at <= dt.timedelta(hours=float(hours))
    except Exception:
        return False


if __name__ == "__main__":
    import sys
    if sys.argv[1] == "--recent":            # exit 0 = done a short while ago (the late backstop has nothing to do)
        sys.exit(0 if recent(sys.argv[2], sys.argv[3]) else 1)
    job_end(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "success")
