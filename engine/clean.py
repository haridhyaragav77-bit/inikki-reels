"""Clean job (AGENT.md 14.3, 14.4), nightly: deletes working files by the retention rules and reports storage.
Deleted files go to Drive's bin (recoverable for 30 days). reference-reels/, meme-bank/, music/ and control/ are never touched.

    python -m engine.clean            clean and report
    python -m engine.clean --dry      only say what would be deleted"""
import argparse
import datetime as dt
import json
import re
import shutil
import sys

from .settings import ENGINE, ROOT
from . import status
from .day import load_json_lines

FOLDER = "application/vnd.google-apps.folder"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def files_under(drive, fid, path=""):
    out = []
    for it in drive.children(fid, resolve_shortcuts=False):
        p = f"{path}/{it['name']}" if path else it["name"]
        if it["mimeType"] == FOLDER:
            out += files_under(drive, it["id"], p)
        else:
            out.append(dict(it, path=p))
    return out


def storage(drive):
    by, total = {}, 0
    for it in drive.children(drive.root, resolve_shortcuts=False):
        size = sum(int(f.get("size") or 0) for f in files_under(drive, it["id"])) if it["mimeType"] == FOLDER else int(it.get("size") or 0)
        by[it["name"]] = round(size / 1e9, 3)
        total += size
    return round(total / 1e9, 2), by


def top_reels(share):
    rows = []
    for mp in (ROOT / "data" / "metrics").glob("20*.jsonl"):
        rows += load_json_lines(mp.read_text(encoding="utf-8"))
    rows.sort(key=lambda r: -(r.get("views") or 0))
    return {r["reel_id"] for r in rows[: max(1, int(len(rows) * share))]} if rows else set()


def run(drive, dry=False):
    R = ENGINE["drive"]["retention"]
    never = set(ENGINE["drive"]["never_auto_delete"])
    today = status.now().date()
    gone, kept, failed = [], [], []

    def trash(f, why):
        if f["path"].split("/")[0] in never:
            return
        if dry:
            gone.append(f"{f['path']} ({why})")
            return
        try:
            drive.trash(f["id"])
            gone.append(f"{f['path']} ({why})")
        except Exception as e:
            failed.append(f"{f['path']}: {str(e)[:80]}")

    gb, by = storage(drive)
    tight = gb >= float(R["tight_gb"])
    keep = top_reels(float(R["keep_top_share"]))
    for root, days in (("finished", R["finished_days_tight"] if tight else R["finished_days"]), ("rehearsal", R["rehearsal_days"]),
                       ("work", R["work_days"]), ("status/days", R["status_days"]), ("study", R.get("study_text_days", 90))):
        fid = drive.folder(root, create=False)
        if not fid:
            continue
        for f in files_under(drive, fid, root):
            parts = f["path"].split("/")
            if root in ("finished", "rehearsal") and not any(DATE.match(x) for x in parts) and "bank" not in parts:
                continue                      # named folders (golden reels, references) are kept
            stamp = next((p for p in parts if DATE.match(p)), None) or (DATE.match(f["name"][:10]) and f["name"][:10]) or f.get("modifiedTime", "")[:10]
            try:
                age = (today - dt.date.fromisoformat(stamp)).days
            except ValueError:
                continue
            if age <= int(days):
                continue
            if root == "finished" and any(f["name"].startswith(k) for k in keep):
                kept.append(f["path"])
                continue
            trash(f, f"older than {days} days")
    for lib, cap in (("clip-library", R["clip_library_gb"]), ("image-library", R["image_library_gb"])):
        fid = drive.folder(lib, create=False)
        if not fid:
            continue
        fs = [f for f in files_under(drive, fid, lib) if not f["name"].endswith(".json")]
        size = sum(int(f.get("size") or 0) for f in fs)
        removed = []
        for f in sorted(fs, key=lambda f: f.get("modifiedTime", "")):       # oldest first
            if size <= float(cap) * 1e9:
                break
            trash(f, f"{lib} over {cap} GB")
            size -= int(f.get("size") or 0)
            removed.append(f["name"])
        if removed and lib == "image-library" and not dry:
            try:
                idx = drive.read_json("image-library", "index.json") or {"images": []}
                idx["images"] = [i for i in idx.get("images", []) if i.get("file") not in set(removed)]
                drive.write_json("image-library", "index.json", idx)
            except Exception as e:
                failed.append(f"image index: {str(e)[:80]}")
    packed = pack_plans(dry)
    gb2, by2 = (gb, by) if dry else storage(drive)
    report = {"gb": gb2, "by_folder": by2, "tight": tight, "deleted": len(gone), "kept_top": len(kept), "failed": failed[:10],
              "plans_packed": packed, "examples": gone[:10], "dry": dry}
    status.write(drive, "storage.json", report)
    if gb2 >= float(R["warn_gb"]) and not dry:
        status.alert(drive, "Drive storage is getting full", f"The iNiKKi Reels folder uses {gb2} GB of {ENGINE['drive'].get('cap_gb', 15)} GB.",
                     "Clean-up keeps finished reels 14 days instead of 30 from 7.5 GB.", "Nothing now. The monthly review looks at it.", level="warn")
    print(json.dumps({k: report[k] for k in ("gb", "deleted", "kept_top", "plans_packed", "tight")}))
    return report


def pack_plans(dry=False):
    """Plans older than 30 days are packed into plans/archive/YYYY-MM.jsonl (text kept forever, AGENT.md 14.3)."""
    cut = status.now().date() - dt.timedelta(days=30)
    n = 0
    for d in sorted((ROOT / "plans").glob("20??-??-??")):
        if not d.is_dir() or dt.date.fromisoformat(d.name) >= cut:
            continue
        arc = ROOT / "plans" / "archive" / f"{d.name[:7]}.jsonl"
        if not dry:
            arc.parent.mkdir(parents=True, exist_ok=True)
            with open(arc, "a", encoding="utf-8") as f:
                for p in sorted(d.glob("*.json")):
                    f.write(json.dumps({"date": d.name, "file": p.name, "plan": json.loads(p.read_text(encoding="utf-8"))}, ensure_ascii=False) + "\n")
            shutil.rmtree(d)
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    from .drive import Drive
    run(Drive(), a.dry)


if __name__ == "__main__":
    main()
