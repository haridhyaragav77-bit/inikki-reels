"""Health job (AGENT.md 4.3), daily 04:00 IST: keys valid, credit left, storage, runner minutes, voice reachable.
Writes Drive status/health.json and one plain alert if anything needs Harish. Runs even when the switch says Sleep.

    python -m engine.health"""
import datetime as dt
import math
import os
import sys

import requests

from .settings import ENGINE, OUT, missing_secrets, secret
from . import status


def _day_minutes(repo, h, day):
    """GitHub counts each job rounded up to a whole minute; skipped jobs cost nothing."""
    api = f"https://api.github.com/repos/{repo}/actions/runs"
    mins, page = 0, 1
    while True:
        j = requests.get(api, headers=h, params={"created": day, "per_page": 100, "page": page}, timeout=30).json()
        runs = j.get("workflow_runs", [])
        for r in runs:
            jobs = requests.get(f"{api}/{r['id']}/jobs", headers=h, params={"per_page": 100}, timeout=30).json().get("jobs", [])
            for jb in jobs:
                if jb.get("started_at") and jb.get("completed_at") and jb.get("conclusion") != "skipped":
                    a = dt.datetime.fromisoformat(jb["started_at"].replace("Z", "+00:00"))
                    b = dt.datetime.fromisoformat(jb["completed_at"].replace("Z", "+00:00"))
                    mins += max(1, math.ceil((b - a).total_seconds() / 60))
        if len(runs) < 100:
            return mins
        page += 1


def runner_minutes(drive):
    """Counts the month's GitHub runner minutes, a few days per run (yesterday first), into Drive status/minutes.json."""
    repo, tok = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    led = {}
    try:
        led = drive.read_json("status", "minutes.json") or {}
    except Exception:
        pass
    if not (repo and tok):
        return led, "not counted (runs only on GitHub)"
    today = dt.datetime.now(dt.timezone.utc).date()
    month = (today - dt.timedelta(days=1)).strftime("%Y-%m")
    if led.get("month") != month:
        led = {"month": month, "days": {}}
    h = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}
    todo = [d for d in ((today - dt.timedelta(days=k)).isoformat() for k in range(1, 32)) if d.startswith(month) and d not in led["days"]]
    for d in todo[:4]:                       # newest first; earlier days are filled in on the next runs
        led["days"][d] = _day_minutes(repo, h, d)
    limit = int(ENGINE.get("runner", {}).get("minutes_month", 2000))
    led.update(minutes=sum(led["days"].values()), limit=limit, counted_days=len(led["days"]))
    led["tight"] = led["minutes"] >= limit * float(ENGINE.get("runner", {}).get("tight_share", 0.85))
    drive.write_json("status", "minutes.json", led)
    left = len(todo) - min(len(todo), 4)
    return led, f"{led['minutes']} of {limit} minutes used this month" + (f" ({left} earlier days still to count)" if left else "") + \
        (" (tight: extras paused)" if led["tight"] else "")


def main():
    checks = []

    def check(name, fn, fix):
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, str(e)[:200]
        checks.append({"name": name, "ok": bool(ok), "detail": detail, "you_do": "" if ok else fix})
        print(("OK   " if ok else "FAIL ") + name + ": " + detail)

    from .drive import Drive
    drive = None
    try:
        drive = Drive()
    except Exception as e:
        checks.append({"name": "Google Drive", "ok": False, "detail": str(e)[:200], "you_do": "Check the secret GDRIVE_SERVICE_ACCOUNT_JSON."})
    miss = missing_secrets()
    checks.append({"name": "Keys in GitHub", "ok": not miss, "detail": "all present" if not miss else "missing: " + ", ".join(miss),
                   "you_do": "" if not miss else "Add the missing secret(s) on GitHub (AGENT.md 19.2)."})
    if drive:
        check("Google Drive", lambda: (True, f"signed in as the Engine; {drive.quota().get('used_gb')} GB used in the account"),
              "Check the secret GDRIVE_SERVICE_ACCOUNT_JSON and the folder share.")

    def ig():
        from .instagram import Instagram
        g = Instagram()
        me = g.me()
        used, total = g.publishing_quota()
        perm = "posting permission OK" if total else "could not read the posting limit (the token may lack posting permission)"
        return bool(total), f"@{me.get('username')} · {me.get('followers_count')} followers · {perm}" + (f" · {g.note}" if g.note else "")
    check("Instagram", ig, "Make a fresh token with the instagram_content_publish permission and update IG_ACCESS_TOKEN.")

    def oa():
        r = requests.get("https://api.openai.com/v1/models", headers={"Authorization": f"Bearer {secret('OPENAI_API_KEY')}"}, timeout=30)
        if r.status_code == 403:          # a key limited to pictures may not list models: it is still a working key
            return True, "key works (limited to pictures, which is all the Engine needs)"
        return r.ok, "key works" if r.ok else f"refused ({r.status_code}: {r.text[:100]})"
    check("OpenAI key", oa, "Update the secret OPENAI_API_KEY (pictures fall back to free sources meanwhile).")
    if drive:
        def money():
            from .budget import Budget
            b = Budget(drive).summary()
            return b["pct"] < 90, f"images ₹{b['spent_inr']:.0f} of ₹{b['cap_inr']:.0f} this month ({b['mode']})"
        check("Image budget", money, "Nothing: near the cap the Engine uses free pictures only until the 1st.")
        check("Runner minutes", lambda: (lambda led_msg: (not led_msg[0].get("tight"), led_msg[1]))(runner_minutes(drive)),
              "Nothing: extras pause by themselves; the monthly review looks at it.")

        def store():
            s = drive.read_json("status", "storage.json") or {}
            gb = s.get("gb")
            return gb is None or gb < float(ENGINE["drive"]["retention"]["warn_gb"]), f"{gb if gb is not None else '?'} GB used by the folder (nightly count)"
        check("Storage", store, "Nothing now: clean-up tightens by itself.")

    def voice():
        from . import voice as v
        out = str(OUT / "health_voice.mp3")
        r = v.say(ENGINE["voice"]["smoke_text"], out)
        ok = r.get("ok") and os.path.exists(out) and os.path.getsize(out) > 1000
        return ok, "Microsoft's Tamil voice answers" if ok else f"no answer: {r.get('error', 'no file')}"
    check("Backup voice (Microsoft)", voice, "Nothing: reels with voice retry later, then post as silent versions with full on-screen text.")

    def main_voice():
        from . import voice as v
        ok, detail = v.check()
        sub = v.subscription()
        if sub and drive:
            led = v.ledger(drive)
            led["subscription"] = {**sub, "read": status.stamp()}
            status.write(drive, "voice.json", led)
        return ok, detail
    check("Main voice (ElevenLabs)", main_voice, "Check the secret ELEVENLABS_API_KEY on GitHub. Until then reels use the Microsoft backup voice.")
    bad = [c for c in checks if not c["ok"]]
    res = {"ok": not bad, "checks": checks}
    status.write(drive, "health.json", res)
    if bad and drive:
        status.alert(drive, f"Health check: {len(bad)} thing(s) need a look", "; ".join(f"{c['name']}: {c['detail']}" for c in bad)[:400],
                     "Everything else keeps running.", " ".join(c["you_do"] for c in bad if c["you_do"])[:300] or "nothing", level="warn")
    sys.exit(0)


if __name__ == "__main__":
    main()
