"""Manual work (AGENT.md 16.6) with a pretend Drive: the one laptop run (trailers, top-up, shorts, songs in one job), its
15-20 day cycle and levels, the warnings, Done through the inbox, the laptop drop sorting, and the panel section.
Run: python -m tests.test_manual   (no keys, nothing started for real)"""
import datetime as dt
import sys

from engine import laptop, manual, panel, relay, status
from tests.test_control_room import FakeDrive, check


def main():
    manual.start_after = lambda kind: "test: nothing started"     # never start a real workflow from a test
    d = FakeDrive()
    d.write_json("control", "switch.json", {"mode": "run"})
    now = status.now().replace(second=0, microsecond=0)
    d.write_json("status", "trailers_wanted.json", {"films": ["Film A", "Film B"],
                                                     "why": {"Film A": "needed by the plan r-soon", "Film B": "news: a new trailer was reported"}})
    d.write_text("requests", "study_to_get.md", "# Shorts to study\n\npy clip_helper.py --study https://youtu.be/v1 https://youtu.be/v2\n")
    laptop.songs_wanted = lambda: [{"key": "song_test", "song": "Test Song", "film": "Film C", "search": "Test Song Film C", "link": None}]

    t = laptop.todo(d)
    c = laptop.counts(t)
    check(c["trailers"] == 2 and c["study"] == 2 and c["songs"] == 1, f"the laptop list has the trailers, shorts and songs: {c}")
    check(all(u.startswith("https://") for u in t["study"]) and "@" not in str(t), "the list holds public links and names only")

    check(not manual.build(d, now, warn=False)["jobs"], "cloud first: while the cloud fetch works, no laptop card")
    d.write_json("status", "autofetch.json", {"fails_in_a_row": 2})
    check(not manual.build(d, now, warn=False)["jobs"], "2 failed nights: still no laptop card")
    d.write_json("status", "autofetch.json", {"fails_in_a_row": 3})
    M = manual.build(d, now)
    lap = [j for j in M["jobs"] if j["kind"] == "laptop"]
    check(len(lap) == 1 and len(M["jobs"]) == 1, f"one job for every download (was three commands): {[j['kind'] for j in M['jobs']]}")
    j = lap[0]
    check("iNiKKi Laptop Run" in j["command"], "the card says: double-click iNiKKi Laptop Run")
    check("2 trailers" in j["title"] and "2 competitor shorts" in j["title"] and "1 trending song" in j["title"], "the title counts each part: " + j["title"])
    check("First time" in j["what"], "the first run says how to get the new helper once")
    check(j["level"] in ("soon", "later") and "in 3 d" in j["due_text"] or "in 2 d" in j["due_text"], f"the first run is due within 3 days ({j['due_text']})")

    # Done: through the inbox; the job leaves the list for 48 hours, then the next cycle is 20 days out
    d.drop("1-manual_done.json", {"do": "manual_done", "job": j["id"], "kind": "laptop", "items": j["items"], "title": j["title"]})
    relay.run(d)
    log = [x for x in relay.State(d).log if x.get("do") == "manual_done"]
    check(log and log[-1]["result"] == "applied" and "Manual work done" in log[-1]["summary"], "Done is applied by the relay: " + (log[-1].get("summary", "") if log else "-"))
    check(not manual.build(d, now)["jobs"], "right after Done the laptop job is gone while the Engine picks the files up")
    later = manual.build(d, now + dt.timedelta(days=5), warn=False)["jobs"]
    check(later and later[0]["level"] == "later" and "Last run 5 days ago" in later[0]["what"], "5 days later: the next run shows, not urgent yet")
    soon = manual.build(d, now + dt.timedelta(days=17, hours=1))["jobs"]
    check(soon and soon[0]["level"] == "soon", f"day 17: due soon, with a warning ({soon[0]['level'] if soon else '-'})")
    check(any("due soon" in a["title"] for a in d.read_json("status", "alerts.json")["alerts"]), "the early warning is raised")
    urgent = manual.build(d, now + dt.timedelta(days=19, hours=2))["jobs"]
    check(urgent and urgent[0]["level"] == "urgent", "day 19: urgent")
    over = manual.build(d, now + dt.timedelta(days=21), warn=False)["jobs"]
    check(over and over[0]["level"] == "overdue", "day 21: overdue")
    d.drop("2-bad.json", {"do": "manual_done", "job": "../etc"})
    relay.run(d)
    check(relay.State(d).log[-1]["result"] == "refused", "a Done with a strange job name is refused")

    # nothing to fetch: no job at all
    d.write_json("status", "trailers_wanted.json", {"films": []})
    d.write_text("requests", "study_to_get.md", "# Shorts to study\n\nNothing waiting.\n")
    laptop.songs_wanted = lambda: []
    T = __import__("engine.trailers", fromlist=["request_parts"])
    orig = T.request_parts
    T.request_parts = lambda drive: ([], [], {}, None, {})
    check(not manual.build(d, now + dt.timedelta(days=30), warn=False)["jobs"], "nothing to fetch: no laptop job")
    T.request_parts = orig

    # the drop folder: each file goes where it belongs, by its name
    want = {"song - song_x - X (Film) [ab].m4a": "music/inbox", "Leo - trailer [abc].mp4": "clip-library", "helper_report.txt": "clip-library",
            "Expert FX - a short [abcdefghijk].m4a": "study-audio", "photo.png": None}
    check(all(laptop.where(k) == v for k, v in want.items()), "the laptop drop is sorted by file name")

    # the panel: the section in the chat text and the count for the badge
    txt = "\n".join(l for l in panel.text.__code__.co_consts if isinstance(l, str))   # cheap guard that the section exists
    check("MANUAL WORK" in txt, "the chat panel has a Manual work section")
    print("\nALL PASSED" if not check.failed else f"\n{check.failed} FAILED")
    sys.exit(1 if check.failed else 0)


if __name__ == "__main__":
    main()
