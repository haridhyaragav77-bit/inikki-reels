"""The Guard (AGENT.md 21): what keeps a public repository safe.

Four jobs, all in code:
1. redact()   every line the Engine prints or saves has keys and emails masked first (engine/mask.py).
2. scan       no key-shaped text gets into git: run in tests, before every Engine commit and on the Brain's files.
3. trusted    Control Room commands are taken only from Harish's own Drive account (engine/relay.py).
4. watch      once a day (inside the health job): keys in the repository, Drive sharing, who started jobs, posts the
              Engine did not make, voice credits used elsewhere. Clear signs of a break-in hold posting and say what to do.

    python -m engine.guard scan                      exit 1 when something key-shaped is in the repository's files
    python -m engine.guard staged                    files about to be committed: data/ is masked, a key anywhere stops the save
    python -m engine.guard preview --dir out/peek    a preview folder about to be pushed: masked, and a key stops the push
"""
import datetime as dt
import fnmatch
import json
import os
import re
import subprocess
import sys

from .mask import HIDDEN, _Masked, _PAT, clean, install, needles, redact   # noqa: F401  (masking lives in engine/mask.py)
from .settings import ENGINE, ROOT

CFG = ENGINE.get("guard") or {}


# ---------- scan: nothing key-shaped in git ----------
def scan_text(text):
    """[(what, line number, exact)] for one text. `exact` means it is one of this run's real keys."""
    hits = []
    for i, line in enumerate(text.splitlines(), 1):
        if any(n in line for n in needles()):
            hits.append(("one of the Engine's real keys", i, True))
            continue
        for what, rx in _PAT:
            if rx.search(line):
                hits.append((what, i, False))
                break
    return hits


def _skip(rel):
    return any(fnmatch.fnmatch(rel, g) for g in CFG.get("scan_skip") or [])


def scan_files(paths, base=ROOT):
    """Findings for these files: [{file, line, what, exact}]. The key itself is never part of a finding."""
    out = []
    for rel in paths:
        p = os.path.join(base, rel)
        if _skip(rel) or not os.path.isfile(p) or os.path.getsize(p) > 3_000_000:
            continue
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            continue                                     # pictures and other non-text files cannot hold a pasted key
        out += [{"file": rel, "line": n, "what": what, "exact": exact} for what, n, exact in scan_text(text)]
    return out


def _git(*args):
    r = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    return [l for l in r.stdout.splitlines() if l.strip()] if r.returncode == 0 else []


def scan_repo(staged=False):
    return scan_files(_git("diff", "--cached", "--name-only", "--diff-filter=ACM") if staged else _git("ls-files"))


def mask_staged():
    """Files the Engine itself wrote (data/) and is about to commit: keys and emails are masked in place. Returns the files changed."""
    changed = []
    for rel in _git("diff", "--cached", "--name-only", "--diff-filter=ACM"):
        p = os.path.join(ROOT, rel)
        if not any(fnmatch.fnmatch(rel, g) for g in CFG.get("mask_in") or ["data/*"]) or not os.path.isfile(p):
            continue
        try:
            with open(p, encoding="utf-8") as f:
                text = f.read()
        except (UnicodeDecodeError, OSError):
            continue
        safe = redact(text)
        if safe != text:
            with open(p, "w", encoding="utf-8") as f:
                f.write(safe)
            subprocess.run(["git", "add", rel], cwd=ROOT)
            changed.append(rel)
    return changed


def scan_dir(folder):
    files = [os.path.relpath(os.path.join(d, f), folder) for d, _, fs in os.walk(folder) if ".git" not in d.split(os.sep) for f in fs]
    return scan_files(files, base=folder)


def mask_dir(folder):
    """A preview folder about to be pushed to a public branch: keys and emails in its text files are masked in place."""
    for d, _, fs in os.walk(folder):
        if ".git" in d.split(os.sep):
            continue
        for f in fs:
            p = os.path.join(d, f)
            try:
                with open(p, encoding="utf-8") as fh:
                    text = fh.read()
            except (UnicodeDecodeError, OSError):
                continue
            if redact(text) != text:
                with open(p, "w", encoding="utf-8") as fh:
                    fh.write(redact(text))


def plain(findings):
    return "; ".join(f"{f['file']} line {f['line']} looks like {f['what']}" for f in findings[:6]) + \
        (f" (and {len(findings) - 6} more)" if len(findings) > 6 else "")


# ---------- trusted: whose Drive files count as Harish's ----------
def control_room_email():
    """Harish's personal Google account, the one his Claude Google Drive connector uses (GitHub secret CONTROL_ROOM_EMAIL;
    never in git). The Control Room page reads and writes Drive as this account."""
    return str(os.environ.get("CONTROL_ROOM_EMAIL") or "").strip().lower()


def link_control_room(drive, email):
    """Share the iNiKKi Reels folder with that account as an editor, once (fail soft). No email is sent."""
    if getattr(link_control_room, "done", False):
        return
    link_control_room.done = True
    try:
        perms = drive.svc.permissions().list(fileId=drive.root, fields="permissions(emailAddress)", supportsAllDrives=True).execute(num_retries=3)
        if any(str(x.get("emailAddress", "")).lower() == email for x in perms.get("permissions", [])):
            return
        drive.svc.permissions().create(fileId=drive.root, body={"type": "user", "role": "writer", "emailAddress": email},
                                       sendNotificationEmail=False, supportsAllDrives=True).execute(num_retries=3)
        print("guard: the iNiKKi Reels folder is now shared with the Control Room account")
    except Exception as e:
        print("guard: could not share the folder with the Control Room account:", str(e)[:120])


def trusted_people(drive):
    """Emails allowed to give the Engine commands: the owner(s) of the iNiKKi Reels folder and the Engine's own sign-in.
    Empty when Drive will not say (then nothing is refused: fail soft)."""
    people = set()
    try:
        r = drive.svc.files().get(fileId=drive.root, fields="owners(emailAddress)", supportsAllDrives=True).execute(num_retries=3)
        people |= {o.get("emailAddress", "").lower() for o in r.get("owners", [])}
        if people:
            people.add(str(drive.who()).lower())
            try:                                         # the robot account, also when the Engine signs in as Harish
                people.add(str(json.loads(os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON") or "{}").get("client_email", "")).lower())
            except ValueError:
                pass
            people |= {str(e).lower() for e in CFG.get("extra_people") or []}
            mine = control_room_email()
            if mine:
                people.add(mine)
                link_control_room(drive, mine)
    except Exception as e:
        print("guard: could not read who owns the Drive folder:", str(e)[:120])
        return set()
    return {p for p in people if "@" in p}


def stranger(item, people):
    """True when a Drive file was made by an account that is not Harish's or the Engine's."""
    owners = {o.get("emailAddress", "").lower() for o in item.get("owners") or [] if o.get("emailAddress")}
    return bool(people) and bool(owners) and not (owners & people)


# ---------- lockdown ----------
def lockdown(drive, why):
    """Hold posting (the reels stay ready). Only Harish lifts it: Control Room → Resume."""
    try:
        sw = drive.read_json("control", "switch.json") or {}
        if sw.get("mode", "run") != "run":
            return False
        from . import status
        drive.write_json("control", "switch.json", {"mode": "hold_posts", "set_by": "guard", "at": status.stamp(), "why": why[:200]})
        return True
    except Exception as e:
        print("guard: could not hold posting:", str(e)[:120])
        return False


# ---------- watch: the daily look-around ----------
def _gh(path, **params):
    import requests
    repo, tok = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not (repo and tok):
        return None
    r = requests.request(params.pop("_method", "GET"), f"https://api.github.com/repos/{repo}{path}", params=params or None, timeout=30,
                         headers={"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"})
    if r.status_code == 204:
        return {}
    return r.json() if r.ok else None


def repo_is_public():
    """True / False, or None when it cannot be read (not on GitHub)."""
    j = _gh("")
    return None if not j or "private" not in j else not j["private"]


def w_repo():
    f = scan_repo()
    if not f:
        return True, "no key-shaped text in the repository's files", None
    exact = any(x["exact"] for x in f)
    return False, plain(f), {"level": "high", "title": "A key may be visible in the repository",
                             "you_do": "Replace that key now (GUIDE.md 12, 'If a key leaks'), then tell the Workshop to remove the line." if exact
                             else "Open the file and look: if it is a real key, replace the key (GUIDE.md 12, 'If a key leaks')."}


def w_drive(drive):
    """Nothing in the iNiKKi Reels folder is open to 'anyone with the link'. An open link is closed on the spot."""
    people = trusted_people(drive)
    opened, others, closed = [], set(), []
    for path in [""] + list(CFG.get("drive_folders") or ["control", "control/inbox", "status"]):
        fid = drive.folder(path, create=False) if path else drive.root
        if not fid:
            continue
        perms = drive.svc.permissions().list(fileId=fid, fields="permissions(id,type,role,emailAddress)", supportsAllDrives=True).execute(num_retries=3)
        for p in perms.get("permissions", []):
            if p.get("type") in ("anyone", "domain"):
                opened.append(path or "the main folder")
                try:
                    drive.svc.permissions().delete(fileId=fid, permissionId=p["id"], supportsAllDrives=True).execute(num_retries=3)
                    closed.append(path or "the main folder")
                except Exception:
                    pass
            elif people and (p.get("emailAddress") or "").lower() not in people:
                others.add((p.get("emailAddress") or "someone").lower())
    if opened:
        left = [o for o in opened if o not in closed]
        return False, f"open to anyone with the link: {', '.join(sorted(set(opened)))}" + ("; closed again by the Engine" if not left else ""), {
            "level": "high", "title": "A Drive folder was open to anyone with the link",
            "you_do": "Nothing more: it is closed again. If you did not open it yourself, change your Google password." if not left
            else "In Drive: right-click the folder → Share → General access → Restricted."}
    if others:
        return False, f"also shared with {len(others)} other account(s): {', '.join(sorted(others))}", {
            "level": "warn", "title": "The Drive folder is shared with someone else",
            "you_do": "If you shared it, add that address to guard.extra_people in the settings. If not: Drive → Share → remove them."}
    return True, "only you and the Engine can open the folder", None


def w_jobs(prev):
    """Every job in the last two days was started by the owner or by GitHub itself, and none ran for a stranger's request."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=2)).strftime("%Y-%m-%d")
    j = _gh("/actions/runs", created=f">={since}", per_page=100)
    if j is None:
        return True, "not checked (runs only on GitHub)", None
    ok_people = {repo.split("/")[0].lower(), "github-actions[bot]"} | {str(a).lower() for a in CFG.get("trusted_actors") or []}
    bad_events = set(CFG.get("stranger_events") or ["pull_request_target", "issue_comment", "issues", "fork", "watch", "discussion", "discussion_comment"])
    seen, bad = set(prev.get("jobs_seen") or []), []
    for r in j.get("workflow_runs", []):
        who = ((r.get("triggering_actor") or r.get("actor") or {}).get("login") or "").lower()
        if r["id"] in seen or (who in ok_people and r.get("event") not in bad_events) or (r.get("event") == "pull_request" and r.get("name") == "guard"):
            continue
        bad.append({"id": r["id"], "who": who or "unknown", "job": r.get("name"), "event": r.get("event")})
    prev["jobs_seen"] = (list(seen) + [b["id"] for b in bad])[-200:]
    if bad:
        return False, "; ".join(f"{b['job']} started by {b['who']} ({b['event']})" for b in bad[:5]), {
            "level": "high", "lock": True, "title": "A job was started by someone who is not you",
            "you_do": "If it was a helper you added, put their GitHub name in guard.trusted_actors. If not: GUIDE.md 12, 'If someone gets in'."}
    return True, "every job was started by you or by GitHub's clock", None


def w_posts(drive, prev):
    """Posts on the page that the Engine did not make (a sign the Instagram key is being used elsewhere)."""
    from .instagram import Instagram
    media = Instagram().media(limit=int(CFG.get("posts_checked", 30)))
    ours = set()
    for line in (drive.read_text("status", "posted.jsonl", "") or "").splitlines():
        try:
            ours.add(str(json.loads(line).get("media_id")))
        except ValueError:
            pass
    first = "posts_seen" not in prev
    seen = set(prev.get("posts_seen") or [])
    new = [m for m in media if str(m["id"]) not in seen and str(m["id"]) not in ours]
    prev["posts_seen"] = (list(seen) + [str(m["id"]) for m in media if str(m["id"]) not in seen])[-300:]
    if new and not first:
        return False, f"{len(new)} post(s) on the page were not made by the Engine: " + ", ".join(m.get("permalink", m["id"]) for m in new[:3]), {
            "level": "warn", "title": "A post appeared that the Engine did not make",
            "you_do": "If you posted it yourself, nothing. If not: change your Instagram password and replace IG_ACCESS_TOKEN (GUIDE.md 12, 'If a key leaks')."}
    return True, "every new post on the page came from the Engine" if not first else "starting point noted; checked from tomorrow", None


def w_voice(drive, prev):
    """ElevenLabs credits that went down more than the Engine used (a sign the voice key is being used elsewhere)."""
    led = drive.read_json("status", "voice.json") or {}
    used, mine = (led.get("subscription") or {}).get("used"), led.get("credits_by_engine")
    if used is None or mine is None:
        return True, "not checked (no voice numbers yet)", None
    was = prev.get("voice") or {}
    prev["voice"] = {"used": used, "mine": mine, "month": led.get("month")}
    if was.get("month") != led.get("month") or used < was.get("used", 0):
        return True, "new month: starting point noted", None
    extra = (used - was["used"]) - max(0, mine - was.get("mine", 0))
    if extra > int(CFG.get("voice_margin", 6000)):
        return False, f"about {extra} voice credits were used since yesterday that the Engine did not use", {
            "level": "info", "title": "Voice credits were used outside the Engine",
            "you_do": "If you used ElevenLabs yourself (or a test ran), nothing. If not: make a new ElevenLabs key and update ELEVENLABS_API_KEY."}
    return True, "voice credits match what the Engine used", None


def tidy_branches():
    """Preview branches (peek, review*) are deleted a day after their last change: in a public repository anyone can see them."""
    hours, gone = float(CFG.get("preview_hours", 24)), []
    for b in _gh("/branches", per_page=100) or []:
        name = b.get("name", "")
        if not any(fnmatch.fnmatch(name, g) for g in CFG.get("preview_branches") or ["peek", "review", "review-*"]):
            continue
        c = _gh(f"/commits/{b['commit']['sha']}") or {}
        when = ((c.get("commit") or {}).get("committer") or {}).get("date")
        if when and dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(when.replace("Z", "+00:00")) > dt.timedelta(hours=hours):
            if _gh(f"/git/refs/heads/{name}", _method="DELETE") is not None:
                gone.append(name)
    return gone


def watch(drive):
    """The daily look-around. Returns health-style checks; raises alerts; holds posting on a clear break-in sign."""
    from . import status
    prev = {}
    if drive:
        try:
            prev = drive.read_json("status", "security.json") or {}
        except Exception:
            pass
    jobs = [("Security: keys in the repository", w_repo), ("Security: who started jobs", lambda: w_jobs(prev))]
    if drive:
        jobs += [("Security: Drive sharing", lambda: w_drive(drive)), ("Security: posts on the page", lambda: w_posts(drive, prev)),
                 ("Security: voice credits", lambda: w_voice(drive, prev))]
    checks, locked = [], False
    for name, fn in jobs:
        try:
            ok, detail, alarm = fn()
        except Exception as e:                           # fail soft: one look that cannot be done never stops the others
            ok, detail, alarm = True, f"not checked this time ({str(e)[:100]})", None
        checks.append({"name": name, "ok": bool(ok), "detail": detail, "you_do": (alarm or {}).get("you_do", "")})
        print(("OK   " if ok else "FAIL ") + name + ": " + detail)
        if alarm:
            did = "Nothing was changed."
            if alarm.get("lock") and drive and lockdown(drive, alarm["title"]):
                locked, did = True, "Posting is on hold until you press Resume in the Control Room. Ready reels are kept."
            if drive:
                status.alert(drive, "Security: " + alarm["title"], detail[:400], did, alarm["you_do"],
                             level="info" if alarm["level"] == "info" else "warn")
    try:
        gone = tidy_branches()
        if gone:
            print("guard: old preview branches deleted:", ", ".join(gone))
    except Exception as e:
        print("guard: preview branches not tidied:", str(e)[:100])
    prev.update(checked=status.stamp(), public=repo_is_public(), locked=locked, checks=checks)
    if drive:
        status.write(drive, "security.json", prev)
    return checks


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=["scan", "staged", "preview"])
    ap.add_argument("--dir", default=None)
    a = ap.parse_args()
    if a.what == "staged" and not a.dir:
        masked = mask_staged()
        if masked:
            print("Guard: private details masked before saving in " + ", ".join(masked))
    if a.what == "preview":
        mask_dir(a.dir or str(ROOT / "out" / "peek"))
        a.dir = a.dir or str(ROOT / "out" / "peek")
    found = scan_dir(a.dir) if a.dir else scan_repo(staged=a.what == "staged")
    if found:
        print("Guard: stopped. " + plain(found) + ". Nothing was saved to the repository.")
        sys.exit(1)
    print("Guard: no keys in " + (a.dir or ("the files about to be saved" if a.what == "staged" else "the repository")) + ".")


if __name__ == "__main__":
    main()
