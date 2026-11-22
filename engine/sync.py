"""Sync job (AGENT.md 4.3, Block D): takes a thinking run's branch (claude/brain-*), copies only the files the Brain may
write into main, puts the Brain's notes (data/out/*.md) in Drive status/, and reports anything refused in plain words.
This is the code check behind "the Brain writes only small text files" (CLAUDE.md roles).

    python -m engine.sync --branch claude/brain-plan-2026-11-13 [--dry]"""
import argparse
import fnmatch
import json
import os
import subprocess
import sys

import yaml

from . import status

ALLOW = ["plans/20??-??-??/*.json", "plans/20??-??-??/*.md", "plans/bank/*.json", "rules/*.md", "lab/*.md", "lab/*/*.md",
         "lab/*/*.json", "lab/*/*.yaml", "niches/*/series/*/series.yaml", "niches/*/lineups/*.yaml", "niches/*/knowledge/film_bank.json", "niches/*/knowledge/releases.yaml",
         "niches/*/knowledge/pronunciations.yaml", "niches/*/knowledge/trending_songs.yaml", "niches/*/knowledge/*.md", "niches/*/knowledge/recommended_log.csv", "niches/*/memes/meme_index.csv", "data/out/*.md", "data/notes/*.md"]
# Settings the Brain may only propose (AGENT.md 9.2): a change to these keys is refused and reported.
PROTECTED = {"series.yaml": ["per_day", "per_day_max", "template", "paused", "retired", "rules", "voice", "expires_h"],
             "lineups": ["per_day", "max", "bank_target", "trial_reels", "max_per_2_days"]}
MAX_BYTES = 200_000


def git(*args, check=True):
    r = subprocess.run(["git", *args], capture_output=True, text=True)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[:300]}")
    return r.stdout


def strip_keys(obj, keys):
    if isinstance(obj, dict):
        return {k: strip_keys(v, keys) for k, v in obj.items() if k not in keys}
    if isinstance(obj, list):
        return [strip_keys(v, keys) for v in obj]
    return obj


def pick(obj, keys):
    """Only the protected keys, wherever they sit."""
    if isinstance(obj, dict):
        return {k: (v if k in keys else pick(v, keys)) for k, v in obj.items() if k in keys or isinstance(v, (dict, list))}
    if isinstance(obj, list):
        return [pick(v, keys) for v in obj]
    return None


def verdict(path, new_text, old_text):
    """None when the Brain may make this change, else the reason in plain words."""
    if not any(fnmatch.fnmatch(path, p) for p in ALLOW) or path.startswith("plans/reference/"):
        return "not a file the Brain may change"
    if new_text is None:
        return None
    if len(new_text.encode("utf-8")) > MAX_BYTES:
        return "too big for a text note"
    from .guard import scan_text
    hit = scan_text(new_text)
    if hit:                                                # the repository is public: nothing key-shaped comes in (AGENT.md 21)
        return f"line {hit[0][1]} looks like {hit[0][0]}"
    try:
        if path.endswith(".json"):
            json.loads(new_text)
        if path.endswith((".yaml", ".yml")):
            new, old = yaml.safe_load(new_text), yaml.safe_load(old_text) if old_text else None
            keys = PROTECTED["series.yaml"] if path.endswith("series.yaml") else PROTECTED["lineups"] if "/lineups/" in path else []
            if old is not None and keys and pick(new, keys) != pick(old, keys):
                return "changes a setting only Harish decides (" + ", ".join(keys) + ")"
    except ValueError as e:
        return f"not valid ({str(e)[:60]})"
    return None


def run(branch, dry=False):
    git("config", "user.name", "iNiKKi Engine")
    git("config", "user.email", "41898283+github-actions[bot]@users.noreply.github.com")
    git("fetch", "-q", "origin", "main", branch)
    base = git("merge-base", "origin/main", f"origin/{branch}").strip()
    head_msg = git("log", "-1", "--format=%s", f"origin/{branch}").strip()
    changed = [l.split("\t") for l in git("diff", "--name-status", "--no-renames", base, f"origin/{branch}").splitlines() if l.strip()]
    git("checkout", "-q", "-B", "main", "origin/main")
    taken, refused = [], []
    for st, path in changed:
        new = None if st == "D" else git("show", f"origin/{branch}:{path}", check=False)
        old = git("show", f"origin/main:{path}", check=False) or None
        why = verdict(path, new, old)
        if why:
            refused.append(f"{path}: {why}")
            continue
        if st == "D":
            if old is not None:
                git("rm", "-q", path)
        else:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(new)
            git("add", path)
        taken.append(path)
    import re
    plans = sorted({p.split("/")[1] for p in taken if p.startswith("plans/") and re.fullmatch(r"20\d\d-\d\d-\d\d|bank", p.split("/")[1])})
    notes = [p for p in taken if p.startswith("data/out/") and os.path.exists(p)]
    if not dry and git("diff", "--cached", "--name-only").strip():
        git("commit", "-q", "-m", f"brain: {head_msg[:80]}")
        for _ in range(4):
            if subprocess.run(["git", "push", "-q", "origin", "main"]).returncode == 0:
                break
            git("pull", "-q", "--rebase", "origin", "main")
        else:
            raise RuntimeError("could not push to main")
    drive = None
    if not dry and (notes or refused):
        from .drive import Drive
        drive = Drive()
        for p in notes:
            drive.write_text("status", os.path.basename(p), open(p, encoding="utf-8").read(), "text/markdown")
        if any(os.path.basename(p) == "alerts.md" for p in notes):
            status.alert(drive, "A note from the thinking run", open("data/out/alerts.md", encoding="utf-8").read()[:300],
                         "Saved in Drive status/alerts.md.", "Read it when convenient.", level="info")
        if refused:
            status.alert(drive, "Some Brain changes were not applied", "; ".join(refused)[:400],
                         "Everything else from that run was applied.", "Nothing, unless you want one of them: say so in the Control Room.", level="info")
    summary = {"branch": branch, "taken": taken, "refused": refused, "plans": plans}
    print(json.dumps(summary, ensure_ascii=False, indent=1))
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"plans={' '.join(plans)}\n")
    return summary


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--branch", required=True)
    ap.add_argument("--dry", action="store_true")
    a = ap.parse_args()
    if not a.branch.startswith("claude/brain-"):
        sys.exit("Only claude/brain-* branches are synced.")
    run(a.branch, a.dry)


if __name__ == "__main__":
    main()
