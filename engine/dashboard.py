"""Dashboard job (AGENT.md 13.2): rewrites the "iNiKKi Dashboard" sheet after the nightly stats. For looking only;
all changes go through the Control Room.

    python -m engine.dashboard"""
import datetime as dt
import re
import statistics

from .settings import AGENT, ROOT
from . import status
from .day import Day, load_json_lines
from .measure import RATES

NAMES = {"skip_rate": "Skip", "watch_through": "Watch-through", "share_rate": "Share", "follow_rate": "Follow", "like_rate": "Like",
         "save_rate": "Save", "comment_rate": "Comment", "repost_rate": "Repost"}


def pct(v):
    return "" if v is None else f"{v * 100:.2f}%"


def rows_all():
    out = []
    for mp in sorted((ROOT / "data" / "metrics").glob("20*.jsonl")):
        out += load_json_lines(mp.read_text(encoding="utf-8"))
    return out


def worst(h):
    cols = list((h or {}).values())
    return "red" if "red" in cols else "amber" if "amber" in cols else "green" if "green" in cols else ""


def build(drive):
    from .control import Control
    from .sheets import Dashboard
    ctl = Control(drive)
    sh = Dashboard(drive)
    sh.ensure_tabs()
    reels = rows_all()
    g = ctl.settings.get("goal", {})
    start = dt.date.fromisoformat(str(g.get("start_date")))
    days = (status.now().date() - start).days
    f0, f1, span = g.get("start_followers", 0), g.get("followers", 1000), g.get("by_days", 90)
    fl = load_json_lines((ROOT / "data" / "metrics" / "followers.jsonl").read_text(encoding="utf-8")) if (ROOT / "data" / "metrics" / "followers.jsonl").exists() else []
    now_f = fl[-1]["followers"] if fl else f0
    target = round(f0 + (f1 - f0) * min(1, days / span))
    day = Day(drive)
    alerts = [a for a in (drive.read_json("status", "alerts.json") or {"alerts": []}).get("alerts", []) if a.get("open")][:8]
    home = [["iNiKKi Reels", f"updated {status.stamp()}"], [],
            ["Phase", ctl.phase, "Switch", ctl.mode],
            ["Followers", now_f, "Target line today", target, "Days left", max(0, span - days), "Ahead / behind", now_f - target], [],
            ["Today's reels"], ["Slot", "Reel", "Series", "State", "Note", "Drive link"]]
    home += [[r.get("slot") or "", r["reel_id"], r.get("series", ""), r.get("state", ""), (r.get("reason") or "")[:80], r.get("link") or ""] for r in day.reels()]
    home += [[], ["Alerts"], ["When", "What happened", "What you do"]] + [[a["at"], a["title"], a.get("what_you_do", "")] for a in alerts]
    by_day = {}
    for r in reels:
        by_day.setdefault(r["posted_at"][:10], []).append(r)
    metrics = [["Date", "Reels", "Median views"] + [NAMES[k] for k in RATES]]
    for d in sorted(by_day, reverse=True)[:60]:
        rs = by_day[d]
        med = lambda k: statistics.median([x["rates"][k] for x in rs if x.get("rates", {}).get(k) is not None] or [0])
        metrics.append([d, len(rs), int(statistics.median([x.get("views") or 0 for x in rs]))] + [pct(med(k)) for k in RATES])
    m = drive.read_json("status", "metrics.json") or {}
    series = [["Series", "Reels (14 days)", "Median views"] + [NAMES[k] for k in RATES]]
    for s, b in sorted((m.get("baselines") or {}).items()):
        md = b.get("median", {})
        series.append(["Whole page" if s == "_page" else s, b.get("reels"), md.get("views")] + [pct(md.get(k)) for k in RATES])
    reel_rows = [["Posted", "Reel", "Series", "Hook", "Score before", "Views", "Reach"] + [NAMES[k] for k in RATES] + ["Health", "Link"]]
    for r in sorted(reels, key=lambda x: x["posted_at"], reverse=True)[:300]:
        reel_rows.append([r["posted_at"][:16].replace("T", " "), r["reel_id"], r.get("series"), (r.get("hook") or "")[:60], r.get("virality"),
                          r.get("views"), r.get("reach")] + [pct(r.get("rates", {}).get(k)) for k in RATES] + [worst(r.get("health")), r.get("permalink")])
    lab = [["File", "First line"]]
    for d in ("pitches", "results"):
        for p in sorted((ROOT / "lab" / d).glob("*.md")) if (ROOT / "lab" / d).exists() else []:
            lab.append([f"{d}/{p.name}", (p.read_text(encoding="utf-8").strip().splitlines() or [""])[0][:120]])
    ch = [["#", "Date", "Scope", "Change", "Why", "Status"]]
    for line in (ROOT / "rules" / "changes.md").read_text(encoding="utf-8").splitlines():
        if re.match(r"^`#\d+", line.strip()):
            parts = [x.strip() for x in line.strip().strip("`").split(" · ")]
            ch.append((parts + [""] * 6)[:5] + [" · ".join(parts[5:])])
    try:
        from .budget import Budget
        b = Budget(drive).summary()
    except Exception:
        b = {}
    mins = drive.read_json("status", "minutes.json") or {}
    stor = drive.read_json("status", "storage.json") or {}
    costs = [["Item", "Used", "Limit"], ["Images this month (₹)", round(b.get("spent_inr", 0)), b.get("cap_inr", 500)],
             ["Runner minutes this month", mins.get("minutes", ""), mins.get("limit", 2000)],
             ["Drive storage (GB)", stor.get("gb", ""), ctl.settings.get("budgets", {}).get("storage_gb", 15)]]
    for tab, rows in (("Home", home), ("Metrics", metrics), ("Series", series), ("Reels", reel_rows), ("Lab", lab), ("Changes", ch), ("Costs", costs)):
        sh.clear(tab)
        sh.write(tab, "A1", [[("" if c is None else c) for c in r] for r in rows] or [[""]])
    status.write(drive, "dashboard.json", {"ok": True, "link": sh.link()})
    print("dashboard updated:", sh.link())


def main():
    from .drive import Drive
    d = Drive()
    try:
        build(d)
    except Exception as e:
        msg = str(e)
        hint = "Turn on the Google Sheets API in the Google Cloud project (AGENT.md 19.1)." if "sheets" in msg.lower() or "403" in msg else "nothing"
        status.write(d, "dashboard.json", {"ok": False, "error": msg[:300]})
        status.alert(d, "The dashboard sheet was not updated", msg[:200], "Everything else carries on.", hint, level="info")
        print("dashboard not updated:", msg[:300])


if __name__ == "__main__":
    main()
