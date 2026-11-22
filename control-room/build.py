"""Builds the Control Room page: the template plus the guidebook (GUIDE.md), so the guide is written once, plus example
data taken from the real series files and the series framework (shown only until the live status loads).
    python control-room/build.py [page link]      writes control-room/page.html, the file that is published as the artifact"""
import json
import pathlib
import sys

here = pathlib.Path(__file__).parent
sys.path.insert(0, str(here.parent))
guide = (here.parent / "GUIDE.md").read_text(encoding="utf-8")
if len(sys.argv) > 1:
    guide = guide.replace("PAGE_URL", sys.argv[1])


def example():
    """The framework, the series as they are in the files, today's calendar and made-up usage numbers. No Drive, no keys."""
    try:
        from engine import almanac, dayplan, panel, status
        from engine.control import Control
        ctl = Control(None)
        from engine.settings import niche
        srcs = [{"name": c.get("name"), "where": c.get("platform"), "priority": c.get("priority"), "mode": c.get("study")}
                for c in sorted((niche().get("competitors") or []), key=lambda c: c.get("priority", 9)) if isinstance(c, dict)]
        ex = {"manual": {"count": 1, "urgent": 0, "warn_days": 2, "jobs": [
                  {"id": "laptop-example1", "kind": "laptop", "items": ["3 trailers for coming reels", "4 competitor shorts to study", "6 trending songs"],
                   "level": "soon", "due": "", "due_text": "by Wed 25 Nov, 19:30 (in 2 d 21 h)",
                   "title": "Laptop run: 3 trailers for coming reels, 4 competitor shorts to study, 6 trending songs",
                   "what": "Example: every 15 to 20 days. Open the folder with clip_helper.py, type cmd in the address bar, paste the line, press Enter. It gets its own list, updates itself and fetches everything.",
                   "why": "YouTube and Instagram do not let the cloud computers download these.", "suffers": ["3 coming reels use official YouTube frames instead of trailer moments",
                   "reels use the library music instead of this month's trending songs"], "command": "py clip_helper.py",
                   "after": "The Engine sorts the files, makes the trailer shot grids, studies the shorts and tags the songs at once."}]},
              "music": {"library": 412, "trending": [{"key": "song_example", "title": "Example Song (Example Film)", "film": "Example Film", "best": ["upbeat_percussive"],
                                                      "uses": 2, "added": "example", "fresh": True}]},
              "study": {"sources": srcs, "last": "example: studied 3 short(s); 2 on the laptop list"}, "youtube": {"on": True, "privacy": "private", "today": 0},
              "day_plan": dayplan.card(ctl), "volume": ctl.settings.get("volume"), "framework": panel.framework_card(ctl), "series": panel.series_cards(ctl, {}, None),
              "calendar": almanac.today(status.now().strftime("%Y-%m-%d"), ctl.settings.get("slots") or []),
              "usage": {"runner": {"minutes": 1180, "limit": 2000, "pct": 59, "forecast": 1890, "forecast_pct": 95, "per_day": 84, "stage": "normal", "month": "example",
                                   "ladder": ["Heading past 2000: reserve and bank reels wait", "At 85%: the same, and no extra news checks",
                                              "At 95%: only 3 new reels a day, so posting never stops", "At 100%: GitHub stops every job until the 1st."]},
                        "voice": {"main": "elevenlabs", "now": "elevenlabs", "used": 14200, "limit": 40000, "left": 25800, "resets": "example", "tier": "starter",
                                  "reels_elevenlabs": 31, "reels_microsoft": 2, "per_reel": 430, "covers_reels": 60, "reused_lines": 12},
                        "claude": {"runs": [{"name": k, "at": str(v)} for k, v in (ctl.settings.get("thinking_runs") or {}).items()], "quiet": ["05:37 (plan)", "16:37 (refresh)"],
                                   "note": "Example numbers. Your own appear when the page is opened in Claude with Google Drive connected."}},
              "insights": {"days": 14, "reels": 24, "solid": True, "need": 10, "headline": "Example: film-breakdown leads with 2,700 views in the middle (+160% vs the page).",
                           "do_next": [{"do": "Give film-breakdown one more slot", "why": "its middle reel gets 2,700 views, 160% above the page", "series": "film-breakdown", "more": "film-breakdown"},
                                       {"do": "Change the first frame of movie-recommendations", "why": "58% swipe away in the first seconds, against 49% for the page", "series": "movie-recommendations"}],
                           "series": [{"name": "film-breakdown", "reels": 9, "views": 2700, "vs_page": 1.6, "skip": .41, "share": .014},
                                      {"name": "movie-updates", "reels": 11, "views": 900, "vs_page": -.12, "skip": .47, "share": .009}]}}
        return ex
    except Exception as e:                          # the page still builds; it then shows the small built-in example
        print("example data left out:", str(e)[:160])
        return {}


page = (here / "page.template.html").read_text(encoding="utf-8")
page = page.replace("__GUIDE_JSON__", json.dumps(guide, ensure_ascii=False).replace("</", "<\\/"))
page = page.replace("__EXAMPLE_JSON__", json.dumps(example(), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/"))
(here / "page.html").write_text(page, encoding="utf-8")
print("built", here / "page.html", len(page), "bytes")
