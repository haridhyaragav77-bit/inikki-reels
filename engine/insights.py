"""Insights (AGENT.md 9.4): what the posted reels are telling us, worked out by code, no AI.

It reads the numbers the nightly job already keeps (Drive status/metrics.json) and answers four questions in plain words:
which series earn their slot, which hour works, which reels won or lost, and what to do next. The Control Room shows it
(Insights tab) and the weekly brief carries its "do next" lines, so the weekly thinking run starts from findings instead
of raw tables. Small samples are called early signals, never facts."""
import datetime as dt
import statistics

from .settings import AGENT

DOW = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def _med(xs):
    xs = [x for x in xs if isinstance(x, (int, float))]
    return round(statistics.median(xs), 4) if xs else None


def _rate(r, k):
    return (r.get("rates") or {}).get(k)


def _group(reels, key):
    out = {}
    for r in reels:
        k = key(r)
        if k is not None:
            out.setdefault(k, []).append(r)
    return out


def _row(name, rs, page_views):
    v = _med([r.get("views") for r in rs])
    return {"name": name, "reels": len(rs), "views": v, "skip": _med([_rate(r, "skip_rate") for r in rs]),
            "watch": _med([_rate(r, "watch_through") for r in rs]), "share": _med([_rate(r, "share_rate") for r in rs]),
            "follow": _med([_rate(r, "follow_rate") for r in rs]),
            "vs_page": round(v / page_views - 1, 2) if v is not None and page_views else None}


def build(metrics, now=None, days=14):
    """metrics = the content of status/metrics.json. Returns the insight card, or a card that says what is still missing."""
    now = now or dt.datetime.now(dt.timezone.utc)
    since = (now - dt.timedelta(days=days)).strftime("%Y-%m-%d")
    reels = [r for r in (metrics.get("reels") or []) if str(r.get("posted_at", ""))[:10] >= since and isinstance(r.get("views"), (int, float))]
    need = int((AGENT.get("learning") or {}).get("min_reels", 10))
    out = {"days": days, "reels": len(reels), "solid": len(reels) >= need, "need": need, "do_next": []}
    if not reels:
        out["headline"] = "No measured reels yet. The first numbers arrive the night after a reel posts."
        return out
    page = _med([r.get("views") for r in reels])
    out["page"] = _row("page", reels, page)
    series = sorted((_row(k, v, page) for k, v in _group(reels, lambda r: r.get("series")).items()), key=lambda x: -(x["views"] or 0))
    slots = sorted((_row(k, v, page) for k, v in _group(reels, lambda r: str(r.get("posted_at", ""))[11:13] + ":00" if len(str(r.get("posted_at", ""))) >= 13 else None).items()),
                   key=lambda x: -(x["views"] or 0))
    wdays = []
    for k, v in _group(reels, lambda r: dt.date.fromisoformat(str(r["posted_at"])[:10]).weekday() if r.get("posted_at") else None).items():
        wdays.append(_row(DOW[k], v, page))
    wdays.sort(key=lambda x: -(x["views"] or 0))
    ranked = sorted(reels, key=lambda r: -r["views"])
    card = lambda r: {"id": r.get("reel_id"), "series": r.get("series"), "hook": (r.get("hook") or "")[:60], "views": r.get("views"),
                      "skip": _rate(r, "skip_rate"), "share": _rate(r, "share_rate"), "link": r.get("permalink")}
    out.update(series=series, slots=slots[:6], weekdays=wdays, top=[card(r) for r in ranked[:3]], bottom=[card(r) for r in ranked[-3:][::-1]] if len(ranked) > 5 else [])
    early = "" if out["solid"] else " (early signal)"
    do = out["do_next"]
    strong = [s for s in series if s["reels"] >= 3 and (s["vs_page"] or 0) >= 0.3]
    weak = [s for s in series if s["reels"] >= 4 and (s["vs_page"] or 0) <= -0.4]
    for s in strong[:2]:
        do.append({"do": f"Give {s['name']} one more slot", "why": f"its middle reel gets {int(s['views'])} views, {int(s['vs_page'] * 100)}% above the page{early}", "series": s["name"], "more": s["name"]})
    for s in weak[:2]:
        do.append({"do": f"Rework or pause {s['name']}", "why": f"its middle reel gets {int(s['views'])} views, {int(-s['vs_page'] * 100)}% below the page over {s['reels']} reels{early}", "series": s["name"]})
    ps = out["page"].get("skip")
    for s in series:
        if s["reels"] >= 3 and s["skip"] is not None and ps is not None and s["skip"] - ps >= 0.08:
            do.append({"do": f"Change the first frame of {s['name']}", "why": f"{int(s['skip'] * 100)}% swipe away in the first seconds, against {int(ps * 100)}% for the page{early}", "series": s["name"]})
            break
    sh = [s for s in series if s["reels"] >= 3 and s["share"] is not None]
    if len(sh) >= 2:
        best = max(sh, key=lambda s: s["share"])
        if best["share"] > 0 and best["share"] >= 1.5 * (out["page"].get("share") or 0):
            do.append({"do": f"Study what gets {best['name']} sent to friends", "why": f"it is shared {best['share'] * 100:.1f}% of the time, the page {((out['page'].get('share') or 0) * 100):.1f}%{early}", "series": best["name"]})
    full = [s for s in slots if s["reels"] >= 3]
    if len(full) >= 2 and full[-1]["views"] and full[0]["views"] >= 1.5 * full[-1]["views"]:
        do.append({"do": f"Move a reel from {full[-1]['name']} towards {full[0]['name']}", "why": f"reels posted around {full[0]['name']} get {int(full[0]['views'])} views in the middle, around {full[-1]['name']} only {int(full[-1]['views'])}{early}", "move": {"from": full[-1]["name"], "to": full[0]["name"]}})
    if not out["solid"]:
        do.append({"do": f"Keep posting: {need - len(reels)} more measured reels before the numbers are solid", "why": f"{len(reels)} reels in {days} days is a small sample; one lucky reel can move every line above"})
    lead = strong[0] if strong else (series[0] if series else None)
    if lead and lead.get("views") is not None:
        vs = f" ({int(lead['vs_page'] * 100):+d}% against the page)" if lead.get("vs_page") else ""
        said = (f"{lead['name']} leads with {int(lead['views'])} views on its one measured reel{vs}" if lead["reels"] == 1
                else f"{lead['name']} leads: its middle reel gets {int(lead['views'])} views{vs}")
        out["headline"] = f"{said}. The page's middle reel gets {int(page)} views over {len(reels)} reels{early}."
    else:
        out["headline"] = f"{len(reels)} reels measured."
    return out


def lines(card):
    """The card as a few lines for the weekly brief."""
    if not card.get("reels"):
        return [card.get("headline", "")]
    L = [card["headline"]]
    L += [f"- {d['do']}: {d['why']}." for d in card.get("do_next", [])]
    return L
