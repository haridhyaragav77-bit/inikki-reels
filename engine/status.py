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
    obj = dict(obj)
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


def close_alerts(drive, reel_id=None, title_prefix=None):
    """Open alerts that a later success answered: a reel that failed and then posted (reel_id), or an older health
    warning after a newer health check (title_prefix). Closed alerts stop showing in the Control Room."""
    if not drive:
        return
    try:
        cur = drive.read_json("status", "alerts.json", {"alerts": []}) or {"alerts": []}
    except Exception:
        return
    hit = False
    for a in cur.get("alerts", []):
        hit_reel = reel_id and a.get("what_happened", "").startswith(f"{reel_id}:")
        hit_title = title_prefix and a.get("title", "").startswith(title_prefix)
        if a.get("open") and (hit_reel or hit_title):
            a["open"], a["closed"], hit = False, f"answered by a later run ({stamp()})", True
    if hit:
        write(drive, "alerts.json", cur)


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
    write(drive, "jobs.json", jobs)
    if result == "success" and drive:          # this job working again answers its earlier "did not finish" warning
        close_alerts(drive, title_prefix=f"The {name} job did not finish")
    if result not in ("success", "skipped", "cancelled"):
        alert(drive, f"The {name} job did not finish", f"The {name} job stopped with: {result}.",
              "One reel or one step is affected, not the day; the next run starts fresh.", f"Nothing, unless it repeats. Details: {run}", level="warn")
    if drive:                                   # the Control Room page follows every job (AGENT.md 16.2); fail soft
        try:
            from . import room
            room.save(drive)
        except Exception as e:
            print("control room page not updated:", str(e)[:200])
        if name in ("post", "make"):            # the sheet's Home tab shows today's reels, so it follows posts too (AGENT.md 13.2)
            try:
                from . import dashboard
                dashboard.build(drive)
            except Exception as e:
                print("dashboard not updated:", str(e)[:200])


if __name__ == "__main__":
    import sys
    job_end(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "success")
