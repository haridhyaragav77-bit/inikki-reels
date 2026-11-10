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
