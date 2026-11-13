"""Edits (AGENT.md 8.5): Harish changes a reel's words from the Control Room, with no thinking run.

    python -m engine.edits

    edit     a reel that has not posted: the words in its plan are changed, the plan check runs, the reel is made again
    remake   a posted reel: a copy of its plan with the new words becomes a new reel that waits for "post now"
    retry    a held or failed reel is made again

Only words change, never the structure: a change must point at text that is already in the plan, and the changed plan
must pass the plan check, or it is refused and the reel stays as it was (fail soft). The workflow step that runs this
saves the changed plans to main and starts Make for them."""
import copy
import json
import os
import re
import sys

from .settings import ROOT
from . import status
from .control import Control
from .day import Bank, Day, today

SCREEN_TEXT = ("lines", "headline", "headline2", "line", "kicker", "film", "type", "what", "caption", "caption_tamil", "tamil",
               "voice", "voice_tg", "poster_tag", "title", "reason")
PACKAGE_TEXT = ("caption", "hashtags", "cover", "first_comment")
HOOK_KEYS = ("lines", "headline", "what", "line")           # where a look keeps its opening words, first match wins
DONE = ("posted", "rehearsed", "used")


def find_plan(rid, date=None):
    for d in (date or today(), rid[:10], "bank"):
        p = ROOT / "plans" / d / f"{rid}.json"
        if p.exists():
            return p
    for p in list((ROOT / "plans").glob("20??-??-??/*.json")) + list((ROOT / "plans" / "bank").glob("*.json")):
        try:
            j = json.loads(p.read_text(encoding="utf-8"))
        except ValueError:
            continue
        if rid in (j.get("id"), j.get("reel_id")):
            return p
    return None


def _texts(v):
    """A text value as a list of strings, or None when it is not text."""
    if isinstance(v, str):
        return [v]
    if isinstance(v, list) and v and all(isinstance(x, str) for x in v):
        return list(v)
    if isinstance(v, list) and v and all(isinstance(x, dict) and isinstance(x.get("text"), str) for x in v):
        return [x["text"] for x in v]
    return None


def words(plan):
    """The words of a plan that can be changed from the Control Room: {path: text}. Lines are joined with ' / '."""
    out = {}
    first = (plan.get("screens") or [{}])[0]
    for k in SCREEN_TEXT:
        t = _texts(first.get(k))
        if t:
            out[f"screens.0.{k}"] = " / ".join(t)
    pk = plan.get("package") or {}
    for k in PACKAGE_TEXT:
        t = _texts(pk.get(k))
        if t:
            out[f"package.{k}"] = ("\n\n" if k == "caption" else " ").join(t)
    return out


def hook_path(plan):
    first = (plan.get("screens") or [{}])[0]
    return next((f"screens.0.{k}" for k in HOOK_KEYS if _texts(first.get(k))), None)


def set_path(plan, path, value):
    """Replace one piece of text. Raises ValueError in plain words when the change is not allowed."""
    parts = str(path).split(".")
    if parts[0] == "screens" and len(parts) == 3 and parts[1].isdigit() and parts[2] in SCREEN_TEXT:
        screens = plan.get("screens") or []
        if int(parts[1]) >= len(screens):
            raise ValueError(f"the reel has no screen {parts[1]}")
        home, key = screens[int(parts[1])], parts[2]
    elif parts[0] == "package" and len(parts) == 2 and parts[1] in PACKAGE_TEXT:
        home, key = plan.setdefault("package", {}), parts[1]
    else:
        raise ValueError(f"'{path}' is not text that can be changed from the Control Room")
    old = home.get(key)
    if _texts(old) is None:
        raise ValueError(f"this reel has no '{key}' text to change")
    if isinstance(value, str):
        sep = r"\n\s*\n" if key == "caption" else r"\s*/\s*" if key != "hashtags" else r"[\s,]+"
        new = [x.strip() for x in re.split(sep, value.strip()) if x.strip()] if isinstance(old, list) else [value.strip()]
    elif isinstance(value, list) and all(isinstance(x, str) for x in value):
        new = [x.strip() for x in value if x.strip()]
    else:
        raise ValueError(f"'{key}' must be text")
    if not new or not all(new):
        raise ValueError(f"the new '{key}' is empty")
    if isinstance(old, str):
        home[key] = " ".join(new) if key != "caption" else "\n\n".join(new)
    elif isinstance(old[0], dict):                    # lines with a hand-set size and place: same number of lines only
        if len(new) != len(old):
            raise ValueError(f"this title has {len(old)} lines with fixed places; give {len(old)} lines, separated by ' / '")
        for o, n in zip(old, new):
            o["text"] = n
    else:
        home[key] = new
    return plan


def change(plan, cmd):
    """Apply one edit or remake command to a copy of the plan."""
    plan = copy.deepcopy(plan)
    sets = dict(cmd.get("set") or {})
    if cmd.get("hook"):
        hp = hook_path(plan)
        if not hp:
            raise ValueError("this look has no single hook line; change its title fields by name instead")
        old = words(plan).get(hp, "")
        sets[hp] = cmd["hook"]
        pk = plan.get("package") or {}
        if isinstance(pk.get("cover"), str) and re.sub(r"\W+", "", pk["cover"]).lower() == re.sub(r"\W+", "", old).lower():
            sets.setdefault("package.cover", re.sub(r"\s*/\s*", " ", str(cmd["hook"])).strip())
    for k in ("caption", "first_comment", "hashtags"):
        if cmd.get(k):
            sets[f"package.{k}"] = cmd[k]
    if not sets:
        raise ValueError("nothing to change was given")
    for path, value in sets.items():
        set_path(plan, path, value)
    return plan


def _save(path, plan):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _checked(plan):
    from . import plancheck
    errors, _ = plancheck.check(plan)
    if errors:
        raise ValueError("the plan check says: " + " ".join(errors[:2]))


def do_edit(cmd, day, bank):
    rid = cmd["reel_id"]
    path = find_plan(rid, day.date)
    if not path:
        raise ValueError("its plan was not found")
    ledger = bank if path.parent.name == "bank" else day
    rec = ledger.get(rid) or {}
    if rec.get("state") in DONE:
        raise ValueError("it has already posted; ask for a new version instead")
    plan = change(json.loads(path.read_text(encoding="utf-8")), cmd)
    _checked(plan)
    _save(path, plan)
    if rec:
        ledger.upsert(rid, state="planned", reason="Being made again with Harish's change.")
    return rid, "changed; being made again"


def do_remake(cmd, day):
    rid = cmd["reel_id"]
    path = find_plan(rid, day.date)
    if not path:
        raise ValueError("its plan was not found (plans older than 30 days are packed away)")
    plan = json.loads(path.read_text(encoding="utf-8"))
    if cmd.get("hook") or cmd.get("set") or cmd.get("caption"):
        plan = change(plan, cmd)
    stem = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", re.sub(r"-v\d+$", "", rid))
    n = 2
    while (ROOT / "plans" / day.date / f"{day.date}-{stem}-v{n}.json").exists():
        n += 1
    new_id = f"{day.date}-{stem}-v{n}"
    key = "id" if "id" in plan else "reel_id"
    plan[key] = new_id
    plan.update(reserve=True, manual=True, remake_of=plan.get("remake_of") or rid)     # the first original, so its films stay allowed
    for k in ("slot", "post_at", "for_slot"):
        plan.pop(k, None)
    if isinstance(plan.get("package"), dict):
        plan["package"]["slot"] = "reserve"
    _checked(plan)
    _save(ROOT / "plans" / day.date / f"{new_id}.json", plan)
    return new_id, f"new version {new_id} is being made; it waits for 'post now'"


def main(drive=None):
    if drive is None:
        from .drive import Drive
        drive = Drive()
    ctl = Control(drive)
    if ctl.mode == "sleep":
        print("Asleep: no edits applied.")
        return
    try:
        book = drive.read_json("status", "edits.json") or {}
    except Exception:
        book = {}
    done = book.setdefault("done", {})
    todo = [c for c in ctl.lines("commands.jsonl") if c.get("cmd") in ("edit", "remake", "retry") and c.get("id") and c["id"] not in done]
    if not todo:
        print("No edits waiting.")
        return
    day, bank = Day(drive), Bank(drive)
    make, retry = [], False
    for c in todo:
        try:
            if c["cmd"] == "edit":
                rid, note = do_edit(c, day, bank)
            elif c["cmd"] == "remake":
                rid, note = do_remake(c, day)
            else:
                rid, note, retry = c["reel_id"], "being made again", True
                if not ((day.get(rid) or bank.get(rid) or {}).get("state") in ("held", "failed")):
                    raise ValueError("only a held or failed reel can be made again")
            make.append(rid)
            done[c["id"]] = {"ok": True, "note": note, "at": status.stamp(), "reel_id": rid}
        except ValueError as e:
            done[c["id"]] = {"ok": False, "note": str(e)[:240], "at": status.stamp(), "reel_id": c.get("reel_id")}
            status.alert(drive, "A change you asked for was not made", f"{c.get('cmd')} on {c.get('reel_id')}: {str(e)[:240]}",
                         "The reel stays as it was.", "Try again with different words, or ask in the Control Room chat.", level="info")
        except Exception as e:                          # fail soft: one command, never the job
            done[c["id"]] = {"ok": False, "note": f"could not be applied ({str(e)[:160]})", "at": status.stamp(), "reel_id": c.get("reel_id")}
        print(f"edit {c.get('cmd')} {c.get('reel_id')}: {done[c['id']]['note']}")
    day.save()
    bank.save()
    book["done"] = dict(list(done.items())[-200:])
    status.write(drive, "edits.json", book)
    if make and os.environ.get("GITHUB_ACTIONS"):
        ship(list(dict.fromkeys(make)), day.date, retry)


def ship(ids, date, retry):
    """On GitHub: save the changed plans to the branch this job runs on (main), then start Make for just these reels."""
    import subprocess
    ref = os.environ.get("GITHUB_REF_NAME", "main")
    run = lambda *a: subprocess.run(a, capture_output=True, text=True)
    run("git", "add", "-A", "plans")
    if run("git", "diff", "--cached", "--quiet").returncode:
        run("git", "-c", "user.name=iNiKKi Engine", "-c", "user.email=engine@users.noreply.github.com", "commit", "-q", "-m",
            f"engine: Control Room change to {', '.join(ids)[:80]}")
        for _ in range(4):
            if run("git", "push", "-q", "origin", f"HEAD:{ref}").returncode == 0:
                break
            run("git", "pull", "-q", "--rebase", "origin", ref)
        else:
            print("edits: the changed plans could not be saved; they will be tried again", file=sys.stderr)
            return
    r = run("gh", "workflow", "run", "make.yml", "--ref", ref, "-f", f"date={date}", "-f", f"only={','.join(ids)}", *(["-f", "retry=true"] if retry else []))
    print("Make started for: " + ", ".join(ids) if r.returncode == 0 else f"Make could not be started ({r.stderr.strip()[:160]}); the 17:22 or 06:42 Make run picks it up.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("edits skipped:", str(e)[:300], file=sys.stderr)
