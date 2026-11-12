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


def runner_minutes(drive):
    """Adds yesterday's GitHub runner minutes (each job rounded up, as GitHub counts them) to the month's total."""
    repo, tok = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    led = {}
    try:
        led = drive.read_json("status", "minutes.json") or {}
    except Exception:
        pass
    if not (repo and tok):
        return led, "not counted (runs only on GitHub)"
    day = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1)).strftime("%Y-%m-%d")
    month = day[:7]
    if led.get("month") != month:
        led = {"month": month, "days": {}}
    if day not in led["days"]:
        h = {"Authorization": f"Bearer {tok}", "Accept": "application/vnd.github+json"}
        api = f"https://api.github.com/repos/{repo}/actions/runs"
        mins, page = 0, 1
        while True:
            j = requests.get(api, headers=h, params={"created": day, "per_page": 100, "page": page}, timeout=30).json()
            runs = j.get("workflow_runs", [])
            for r in runs:
                t = requests.get(f"{api}/{r['id']}/timing", headers=h, timeout=30).json()
                for os_name, b in (t.get("billable") or {}).items():
                    mins += sum(math.ceil(jr.get("duration_ms", 0) / 60000) for jr in b.get("job_runs", [])) or math.ceil(b.get("total_ms", 0) / 60000)
            if len(runs) < 100:
                break
            page += 1
        led["days"][day] = mins
    limit = int(ENGINE.get("runner", {}).get("minutes_month", 2000))
    led.update(minutes=sum(led["days"].values()), limit=limit)
    led["tight"] = led["minutes"] >= limit * float(ENGINE.get("runner", {}).get("tight_share", 0.85))
    drive.write_json("status", "minutes.json", led)
    return led, f"{led['minutes']} of {limit} minutes used this month" + (" (tight: extras paused)" if led["tight"] else "")


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
        return r.ok, "key works" if r.ok else f"refused ({r.status_code})"
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
    check("Voice", voice, "Nothing: reels with voice retry later, then post as silent versions with full on-screen text.")
    bad = [c for c in checks if not c["ok"]]
    res = {"ok": not bad, "checks": checks}
    status.write(drive, "health.json", res)
    if bad and drive:
        status.alert(drive, f"Health check: {len(bad)} thing(s) need a look", "; ".join(f"{c['name']}: {c['detail']}" for c in bad)[:400],
                     "Everything else keeps running.", " ".join(c["you_do"] for c in bad if c["you_do"])[:300] or "nothing", level="warn")
    sys.exit(0)


if __name__ == "__main__":
    main()
