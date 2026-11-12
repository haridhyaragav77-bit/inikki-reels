"""Measure job (AGENT.md 4.3, 2.2, 2.3): stats 2 hours after each post and every night. No AI.
Rates are per reach. Health colours compare each reel with its series median (green / amber up to 20% below / red).

    python -m engine.measure --nightly     all reels of the last 30 days + followers; writes data/metrics/ and Drive status/metrics.json
    python -m engine.measure               the 2-hour checkpoints only (the Post job also calls this)"""
import argparse
import datetime as dt
import json
import statistics
import sys

from .settings import AGENT, ROOT
from . import status
from .day import load_json_lines

RATES = ["skip_rate", "watch_through", "share_rate", "follow_rate", "like_rate", "save_rate", "comment_rate", "repost_rate"]
LOWER_BETTER = {"skip_rate"}
PER_REACH = {"share_rate": "shares", "follow_rate": "follows", "like_rate": "likes", "save_rate": "saved",
             "comment_rate": "comments", "repost_rate": "reposts"}


def rates(m, seconds):
    reach = float(m.get("reach") or 0)
    out = {}
    skip = next((m[k] for k in ("reels_skip_rate", "ig_reels_skip_rate", "skip_rate") if m.get(k) is not None), None)
    if skip is not None:
        skip = float(skip)
        out["skip_rate"] = round(skip / 100 if skip > 1 else skip, 4)
    if m.get("ig_reels_avg_watch_time") and seconds:
        out["watch_through"] = round(float(m["ig_reels_avg_watch_time"]) / 1000 / float(seconds), 4)
    for r, k in PER_REACH.items():
        if reach and m.get(k) is not None:
            out[r] = round(float(m[k]) / reach, 5)
    return out


def colour(v, median, lower_better=False):
    if v is None or not median:
        return "grey"
    gap = (median - v) / median if not lower_better else (v - median) / median
    return "green" if gap <= 0 else ("amber" if gap <= 0.20 else "red")


def posted(drive):
    try:
        return load_json_lines(drive.read_text("status", "posted.jsonl") or "")
    except Exception:
        return []


def checkpoints(drive, ctl=None):
    """2 hours after a post: first numbers for the Refresh run (status/checks.json)."""
    from .instagram import Instagram
    now = status.now()
    rows = [p for p in posted(drive) if dt.timedelta(hours=2) <= now - dt.datetime.fromisoformat(p["posted_at"]) <= dt.timedelta(hours=30)]
    checks = drive.read_json("status", "checks.json") or {"reels": {}}
    todo = [p for p in rows if p["media_id"] not in checks["reels"]]
    if not todo:
        return checks
    ig = Instagram()
    for p in todo:
        try:
            m, _ = ig.insights(p["media_id"])
        except Exception as e:
            print("checkpoint skipped:", p["reel_id"], str(e)[:120], file=sys.stderr)
            continue
        age = round((now - dt.datetime.fromisoformat(p["posted_at"])).total_seconds() / 3600, 1)
        checks["reels"][p["media_id"]] = {"reel_id": p["reel_id"], "series": p.get("series"), "age_h": age, "at": status.stamp(),
                                          "views": m.get("views"), "reach": m.get("reach"), "rates": rates(m, p.get("seconds"))}
    keep = {k: v for k, v in checks["reels"].items() if v.get("at", "")[:10] >= (now - dt.timedelta(days=3)).strftime("%Y-%m-%d")}
    checks = {"updated": status.stamp(), "reels": keep}
    drive.write_json("status", "checks.json", checks)
    return checks


def baselines(rows, days=14):
    """Median of each rate per series over the last 14 days (AGENT.md 2.3), plus the page median."""
    cut = (status.now() - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    recent = [r for r in rows if r["posted_at"][:10] >= cut]
    out = {}
    for key, group in [("_page", recent)] + [(s, [r for r in recent if r.get("series") == s]) for s in sorted({r.get("series") for r in recent})]:
        med = {}
        for k in RATES + ["views"]:
            vals = [r["rates"].get(k) if k != "views" else r.get("views") for r in group]
            vals = [v for v in vals if v is not None]
            if vals:
                med[k] = round(statistics.median(vals), 5)
        out[key] = {"reels": len(group), "median": med}
    return out


def nightly(drive, ctl=None):
    from .instagram import Instagram
    ig = Instagram()
    me = ig.me()
    today = status.now().strftime("%Y-%m-%d")
    fpath = ROOT / "data" / "metrics" / "followers.jsonl"
    fpath.parent.mkdir(parents=True, exist_ok=True)
    lines = [l for l in load_json_lines(fpath.read_text(encoding="utf-8") if fpath.exists() else "") if l.get("date") != today]
    lines.append({"date": today, "followers": me.get("followers_count"), "media": me.get("media_count")})
    fpath.write_text("".join(json.dumps(l) + "\n" for l in lines[-400:]), encoding="utf-8")
    cut = (status.now() - dt.timedelta(days=30)).strftime("%Y-%m-%d")
    rows = []
    for p in posted(drive):
        if p["posted_at"][:10] < cut:
            continue
        try:
            m, _ = ig.insights(p["media_id"])
        except Exception as e:
            print("stats skipped:", p["reel_id"], str(e)[:120], file=sys.stderr)
            continue
        rows.append({"reel_id": p["reel_id"], "media_id": p["media_id"], "series": p.get("series"), "posted_at": p["posted_at"],
                     "seconds": p.get("seconds"), "hook": p.get("hook"), "virality": p.get("virality"), "trial": p.get("trial"),
                     "permalink": p.get("permalink"), "views": m.get("views"), "reach": m.get("reach"), "raw": m,
                     "rates": rates(m, p.get("seconds")), "measured": status.stamp()})
    base = baselines(rows)
    for r in rows:
        med = (base.get(r.get("series")) or base.get("_page") or {}).get("median", {})
        r["health"] = {k: colour(r["rates"].get(k), med.get(k), k in LOWER_BETTER) for k in RATES}
    by_month = {}
    for r in rows:
        by_month.setdefault(r["posted_at"][:7], []).append(r)
    for month, rs in by_month.items():              # one file per month, latest numbers per reel (text only, AGENT.md 14)
        mp = ROOT / "data" / "metrics" / f"{month}.jsonl"
        old = {x["media_id"]: x for x in load_json_lines(mp.read_text(encoding="utf-8") if mp.exists() else "")}
        old.update({r["media_id"]: r for r in rs})
        mp.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in sorted(old.values(), key=lambda x: x["posted_at"])), encoding="utf-8")
    out = {"updated": status.stamp(), "followers": me.get("followers_count"), "baselines": base,
           "reels": [{k: r[k] for k in ("reel_id", "series", "posted_at", "views", "reach", "rates", "health", "hook", "virality", "permalink")} for r in rows]}
    drive.write_json("status", "metrics.json", out)
    print(f"stats: {len(rows)} reels measured, followers {me.get('followers_count')}")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--nightly", action="store_true")
    a = ap.parse_args()
    from .drive import Drive
    from .control import Control
    d = Drive()
    ctl = Control(d)
    if ctl.mode == "sleep":
        print("Asleep: no stats taken.")
        return
    nightly(d, ctl) if a.nightly else checkpoints(d, ctl)


if __name__ == "__main__":
    main()
