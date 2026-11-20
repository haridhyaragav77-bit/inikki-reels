"""Manual work (AGENT.md 16.6) with a pretend Drive: the list, due dates and levels, the 2-day warning, Done through the
inbox, and the panel section. Run: python -m tests.test_manual   (no keys, nothing started for real)"""
import datetime as dt
import sys

from engine import manual, panel, relay, status
from tests.test_control_room import FakeDrive, check


def main():
    manual.start_after = lambda kind: "test: nothing started"     # never start a real workflow from a test
    d = FakeDrive()
    d.write_json("control", "switch.json", {"mode": "run"})
    now = status.now().replace(second=0, microsecond=0)
    soon_reel = (now + dt.timedelta(hours=60))          # due 3 h before: 57 h away → inside the 2-day warning window
    manual.plan_slot = lambda rid: (soon_reel.date().isoformat(), soon_reel.strftime("%H:%M")) if rid == "r-soon" else None
    d.write_json("status", "trailers_wanted.json", {"films": ["Film A", "Film B"],
                                                     "why": {"Film A": "needed by the plan r-soon", "Film B": "news: a new trailer was reported"}})
    d.write_json("status", "study.json", {"study": {"laptop": ["v1", "v2"]}})
    d.write_text("requests", "study_to_get.md", "# Shorts to study\n\npy clip_helper.py --study https://youtu.be/v1 https://youtu.be/v2\n")

    M = manual.build(d, now)
    kinds = {j["kind"]: j for j in M["jobs"]}
    check({"trailers", "study"} <= set(kinds), "trailers and study jobs are listed")
    t = kinds["trailers"]
    check(t["command"].startswith("py clip_helper.py ") and '"Film A"' in t["command"] and '"Film B"' in t["command"], "trailer job carries the exact command")
    check(t["level"] == "urgent", f"a news trailer makes the job urgent (due within a day): {t['level']}, {t['due_text']}")
    check(any("r-soon" in s and "still pictures" in s for s in t["suffers"]), "the reel that suffers is named with its date")
    check(kinds["study"]["command"].startswith("py clip_helper.py --study") and "Weekly learning run" in kinds["study"]["suffers"][0],
          "study job: command from the request file, the Weekly run named")
    check(M["jobs"][0]["level"] in ("overdue", "urgent"), "most urgent job first")
    alerts = (d.read_json("status", "alerts.json") or {}).get("alerts", [])
    check(any("Manual work is urgent" in a["title"] for a in alerts), "an alert is raised when a job is urgent")
    n = len(alerts)
    manual.build(d, now)
    check(len((d.read_json("status", "alerts.json") or {}).get("alerts", [])) == n, "the same warning is not raised twice")

    # the 2-day warning: only the reel's film, due in 57 h → "soon"
    d.write_json("status", "trailers_wanted.json", {"films": ["Film A"], "why": {"Film A": "needed by the plan r-soon"}})
    t2 = next(j for j in manual.build(d, now)["jobs"] if j["kind"] == "trailers")
    check(t2["level"] == "soon", f"2 days before it turns urgent the job is 'soon' ({t2['due_text']})")
    check(any("due soon" in a["title"] for a in d.read_json("status", "alerts.json")["alerts"]), "the 2-day early warning is raised")
    later = manual.build(d, now - dt.timedelta(days=3), warn=False)
    check(next(j for j in later["jobs"] if j["kind"] == "trailers")["level"] == "later", "earlier than that it is 'later'")

    # Done from the page: through the inbox, the job leaves the list, its films wait for the Engine
    d.drop("1-manual_done.json", {"do": "manual_done", "job": t2["id"], "kind": "trailers", "items": t2["items"], "title": t2["title"]})
    relay.run(d)
    log = [x for x in relay.State(d).log if x.get("do") == "manual_done"]
    check(log and log[-1]["result"] == "applied" and "Manual work done" in log[-1]["summary"], "Done is applied by the relay: " + (log[-1].get("summary", "") if log else "-"))
    after = manual.build(d, now)
    check(not any(j["kind"] == "trailers" for j in after["jobs"]), "after Done the trailer job is gone")
    d.drop("2-bad.json", {"do": "manual_done", "job": "../etc"})
    relay.run(d)
    check(relay.State(d).log[-1]["result"] == "refused", "a Done with a strange job name is refused")

    # the panel: the section in the chat text and the count for the badge
    P = {"manual": after}
    txt = "\n".join(l for l in panel.text.__code__.co_consts if isinstance(l, str))   # cheap guard that the section exists
    check("MANUAL WORK" in txt, "the chat panel has a Manual work section")
    check(after["count"] == len(after["jobs"]) and P["manual"]["count"] >= 1, "the badge count matches the list")
    print("\nALL PASSED" if not check.failed else f"\n{check.failed} FAILED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
