"""The news watch with pretend feeds: a trailer from a small film must reach the Breaking run (the "Ohm" case, 14 Nov 2026).
Run: python -m tests.test_watch   (no keys, nothing fetched)"""
import datetime as dt
import sys

from engine import status, watch
from tests.test_control_room import FakeDrive


def main():
    ok = True

    def check(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("ok   " if cond else "FAIL ") + name)

    now = status.now()
    if not 8 <= now.hour < 22:                      # the watch only wakes the Breaking run in the day; pretend it is noon
        noon = now.replace(hour=12)
        status.now = lambda: noon
        now = noon
    ago = lambda m: now - dt.timedelta(minutes=m)
    news = [{"title": "‘Ohm’ Trailer: a gripping thriller", "link": "https://example.com/a", "at": ago(20), "publisher": "Cinema Express", "feed": "t", "feed_tier": None}]
    scout = [{"title": "Ohm trailer out now", "text": "Ohm trailer out now 🔥 @sunpictures #Ohm", "link": "https://www.instagram.com/chennaiist/", "at": ago(50),
              "publisher": "@chennaiist", "feed": "@chennaiist", "feed_tier": 2, "scout": "chennaiist", "post_id": "p1", "mentions": ["sunpictures"]},
             {"title": "Rain in Chennai today", "text": "Rain in Chennai today", "link": "", "at": ago(30), "publisher": "@chennaiist", "feed": "@chennaiist",
              "feed_tier": 2, "scout": "chennaiist", "post_id": "p2", "mentions": []}]
    fired = []
    watch.fetch = lambda feed: []
    watch.fire_breaking = lambda text: fired.append(text) or "woke the Breaking run"
    src = watch.load_sources()

    # 1. Two trusted sources (a fast page and a newspaper) on a small film's trailer: wakes the Breaking run.
    d = FakeDrive()
    watch.scout_items = lambda s, report: list(scout) + list(news)
    radar = watch.run(d)
    st = next((s for s in radar["stories"] if s["key"] == "f|ohm|trailer"), None)
    check("a film's trailer is one story across sources", st and len(st["publishers"]) == 2)
    check("a trailer with 2 trusted sources wakes the Breaking run", len(fired) == 1 and "Ohm" in fired[0])
    check("the film goes on the trailer wanted list with the tagged account", "sunpictures" in str(d.read_json("status", "trailers_wanted.json") or d.files))
    study = d.read_json("status", "scouts.json")
    pg = study["pages"]["chennaiist"]
    check("the study counts posts, film posts and named accounts", pg["posts"] == 2 and pg["film_posts"] == 1 and pg["mentions"].get("sunpictures") == 1)
    check("the study knows the fast page was first, by 30 minutes", pg["first"] == 1 and pg["lead_min"] == [30])
    watch.run(d)
    check("the same story never wakes it twice", len(fired) == 1)

    # 2. One fast page alone that names the film's official account: enough for a drop.
    fired.clear()
    d = FakeDrive()
    watch.scout_items = lambda s, report: [scout[0]]
    watch.run(d)
    check("one fast page naming the official account wakes it", len(fired) == 1)

    # 3. One fast page alone, no official account named: a signal on the radar only.
    fired.clear()
    d = FakeDrive()
    watch.scout_items = lambda s, report: [{**scout[0], "text": "Ohm trailer out now", "mentions": []}]
    radar = watch.run(d)
    check("an unconfirmed post stays a signal", not fired and radar["stories"])
    print("\nALL PASSED" if ok else "\nFAILED")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
