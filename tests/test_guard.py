"""The Guard (AGENT.md 21) with made-up keys and a pretend Drive: masking, the key search, whose commands count,
the Brain's files, and the workflow safety rules.
Run: python -m tests.test_guard   (no real keys, nothing posted)"""
import glob
import io
import os
import re
import sys

FAKE = {"OPENAI_API_KEY": "sk-proj-" + "Ab3" * 20, "IG_ACCESS_TOKEN": "IGQ" + "x9Z" * 40, "META_APP_SECRET": "0f" * 16,
        "ELEVENLABS_API_KEY": "sk_" + "a1b2" * 12,
        "GDRIVE_OAUTH_REFRESH_TOKEN": '{"client_id": "123-abc.apps.googleusercontent.com", "client_secret": "GOCSPX-' + "q" * 28 + '", "refresh_token": "1//' + "r" * 60 + '"}',
        "GDRIVE_SERVICE_ACCOUNT_JSON": '{"client_email": "bot@proj.iam.gserviceaccount.com", "private_key_id": "' + "c4" * 20 + '", "private_key": "-----BEGIN PRIVATE KEY-----\\n' + "M" * 64 + '\\n-----END PRIVATE KEY-----\\n"}'}
os.environ.update(FAKE)                                 # before the Engine starts, so the Guard knows these as "its keys"

from engine import guard, relay, status, sync            # noqa: E402
from engine.settings import ROOT                         # noqa: E402
from tests.test_control_room import FakeDrive, check     # noqa: E402

OWNER, BOT, OTHER = "owner@example.org", "bot@proj.iam.gserviceaccount.com", "someone@elsewhere.net"


class _Call:
    def __init__(self, result):
        self.result = result

    def execute(self, **kw):
        return self.result


class _Files:
    def get(self, **kw):
        return _Call({"owners": [{"emailAddress": OWNER}]})


class _Perms:
    def __init__(self, drive):
        self.d = drive

    def list(self, fileId=None, **kw):
        return _Call({"permissions": list(self.d.perms.get(fileId, []))})

    def delete(self, fileId=None, permissionId=None, **kw):
        self.d.perms[fileId] = [p for p in self.d.perms.get(fileId, []) if p["id"] != permissionId]
        return _Call({})


class _Svc:
    def __init__(self, drive):
        self.d = drive

    def files(self):
        return _Files()

    def permissions(self):
        return _Perms(self.d)


class OwnedDrive(FakeDrive):
    """The pretend Drive, plus who owns what and who a folder is shared with."""
    root = "root"

    def __init__(self):
        super().__init__()
        self.svc = _Svc(self)
        mine = [{"id": "1", "type": "user", "role": "owner", "emailAddress": OWNER}, {"id": "2", "type": "user", "role": "writer", "emailAddress": BOT}]
        self.perms = {"root": list(mine), "control": list(mine), "control/inbox": list(mine), "status": list(mine)}

    def who(self):
        return OWNER

    def drop(self, name, action, by=OWNER):
        f = super().drop(name, action)
        f["owners"] = [{"emailAddress": by}]
        return f


def main():
    # 1. masking: nothing the Engine prints or saves shows a key or an email
    line = f"refused: https://graph.instagram.com/me?access_token={FAKE['IG_ACCESS_TOKEN']} for harish.someone@gmail.com (key {FAKE['OPENAI_API_KEY']})"
    safe = guard.redact(line)
    check(not any(v in safe for v in (FAKE["IG_ACCESS_TOKEN"], FAKE["OPENAI_API_KEY"], "harish.someone")), "a printed line loses its keys and its email")
    check("41898283+github-actions[bot]@users.noreply.github.com" in guard.redact("by 41898283+github-actions[bot]@users.noreply.github.com"), "the Engine's own no-reply address is left alone")
    check("M" * 64 not in guard.redact("key line " + "M" * 64), "one line of the robot account's private key is masked too")
    check("r" * 60 not in guard.redact("token 1//" + "r" * 60), "the Drive sign-in token inside the one-line secret is masked")
    check(guard.redact("11-14-update-sathyavan-savithiri-risk-of-a-very-long-reel-name-here-ok") == "11-14-update-sathyavan-savithiri-risk-of-a-very-long-reel-name-here-ok",
          "an ordinary long reel name is not mistaken for a key")
    buf = io.StringIO()
    out = guard._Masked(buf)
    out.write("token " + FAKE["META_APP_SECRET"] + "\n")
    check(FAKE["META_APP_SECRET"] not in buf.getvalue() and guard.HIDDEN in buf.getvalue(), "the Engine's printing goes through the mask")
    check(isinstance(sys.stdout, guard._Masked), "the mask is on from the moment the Engine starts")
    saved = guard.clean({"detail": "bad key " + FAKE["ELEVENLABS_API_KEY"], "who": "harish.someone@gmail.com"})
    check(FAKE["ELEVENLABS_API_KEY"] not in str(saved) and "harish.someone@gmail.com" in str(saved), "status files in Drive lose keys but keep who (they are private)")

    # 2. the key search
    check(guard.scan_text("x = 1\nOPENAI = '" + FAKE["OPENAI_API_KEY"] + "'") == [("one of the Engine's real keys", 2, True)], "a real key in a file is found, with its line")
    check(guard.scan_text("ghp_" + "A1" * 20)[0][0] == "a GitHub token", "a key the Engine does not hold is found by its shape")
    check(guard.scan_text('{"refresh_token": "<Refresh token>"}') == [], "a placeholder in the guide is not a key")
    found = guard.scan_repo()
    check(found == [], "the repository's own files hold no key" + ("" if not found else ": " + guard.plain(found)))

    # 3. whose commands count
    d = OwnedDrive()
    d.write_json("control", "switch.json", {"mode": "run"})
    check(guard.trusted_people(d) == {OWNER, BOT}, "trusted: the folder's owner and the Engine's own accounts")
    d.drop("1-mine.json", {"do": "idea", "text": "cover this: 5 one-night thrillers"})
    d.drop("2-theirs.json", {"do": "set", "settings": {"phase": "live"}}, by=OTHER)
    n = relay.run(d)
    log = relay._lines(d.read_text("control", "log.jsonl"))
    check(n == 1 and [x["result"] for x in log] == ["applied", "refused"], "Harish's command is applied, a stranger's is refused")
    check(d.read_json("control", "switch.json").get("mode") == "hold_posts" and d.read_json("control", "switch.json").get("set_by") == "guard",
          "a stranger's command puts posting on hold")
    al = (d.read_json("status", "alerts.json") or {}).get("alerts", [])
    check(bool(al) and al[0]["title"].startswith("Security:") and "Resume" in al[0]["what_was_done"], "and Harish is told in plain words")
    check("2-theirs.json" in d.binned, "the stranger's file is binned")

    # 4. Drive sharing: an open link is closed on the spot
    d = OwnedDrive()
    ok, detail, alarm = guard.w_drive(d)
    check(ok and alarm is None, "a folder only Harish and the Engine can open passes")
    d.perms["control/inbox"].append({"id": "9", "type": "anyone", "role": "writer"})
    ok, detail, alarm = guard.w_drive(d)
    check(not ok and "closed again" in detail and all(p["type"] != "anyone" for p in d.perms["control/inbox"]), "'anyone with the link' is found and closed")
    d.perms["root"].append({"id": "7", "type": "user", "role": "reader", "emailAddress": OTHER})
    ok, detail, alarm = guard.w_drive(d)
    check(not ok and OTHER in detail and alarm["level"] == "warn", "an unknown person on the folder is reported")

    # 5. posts and voice credits the Engine did not use
    prev = {"voice": {"used": 1000, "mine": 400, "month": "2026-11"}}
    d.write_json("status", "voice.json", {"month": "2026-11", "credits_by_engine": 900, "subscription": {"used": 1500}})
    check(guard.w_voice(d, prev)[0], "voice credits that match the Engine's use pass")
    d.write_json("status", "voice.json", {"month": "2026-11", "credits_by_engine": 900, "subscription": {"used": 21500}})
    check(not guard.w_voice(d, prev)[0], "voice credits used somewhere else are noticed")

    # 6. the Brain's files: nothing key-shaped comes in, and plan folders are dates only
    check(sync.verdict("rules/playbook.md", "use this: " + "AIza" + "B" * 35, None) is not None, "a Brain note with a key-shaped string is refused")
    check(sync.verdict("rules/playbook.md", "Open with a promise and a number.", None) is None, "an ordinary Brain note is taken")
    check(sync.verdict(".github/workflows/post.yml", "on: push", None) is not None and sync.verdict("engine/post.py", "x", None) is not None,
          "the Brain cannot change jobs or Engine code")

    # 7. the workflow safety rules
    for f in sorted(glob.glob(str(ROOT / ".github" / "workflows" / "*.yml"))):
        text, name = open(f, encoding="utf-8").read(), os.path.basename(f)
        loose = [u for u in re.findall(r"uses:\s*(\S+)", text) if not re.search(r"@[0-9a-f]{40}$", u)]
        check(not loose, f"{name}: every action is an exact version" + (f" (not {loose})" if loose else ""))
        check(re.search(r"^permissions:", text, re.M) is not None, f"{name}: says what it may touch")
        check("pull_request_target" not in text and "issue_comment" not in text, f"{name}: never runs with keys for a stranger")
        typed = [l.strip()[:70] for l in _commands(text) if re.search(r"\$\{\{\s*(inputs|github\.event\.(?!schedule|repository|name)|steps\.[^}]*outputs|github\.head_ref)", l)]
        check(not typed, f"{name}: no typed input inside a command" + (f" ({typed})" if typed else ""))
        if "pull_request" in text:
            check("secrets." not in text and "contents: read" in text, f"{name}: the pull-request check holds no keys and can only read")
    sys.exit(1 if check.failed else 0)


def _commands(text):
    """The shell lines of a workflow: one-line `run:` values and the lines of `run: |` blocks."""
    out, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        m = re.match(r"^(\s*)(?:- )?run:\s*(.*)$", lines[i])
        if m:
            if m.group(2).strip() not in ("|", ">", "|-", ">-"):
                out.append(m.group(2))
            else:
                ind = len(m.group(1))
                i += 1
                while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > ind):
                    out.append(lines[i])
                    i += 1
                continue
        i += 1
    return out


if __name__ == "__main__":
    main()
