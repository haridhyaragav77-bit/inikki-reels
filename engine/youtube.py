"""YouTube Shorts (AGENT.md 5.15): each reel Instagram posted today also goes to the page's YouTube channel, for free.

Called by the Post run after Instagram (engine/post.py). Fails soft: YouTube never touches Instagram, a failed upload
is tried again by the next Post run that day (youtube.tries), then the reel is marked and the panel says why.

    python -m engine.youtube --check     is the YouTube sign-in working? (lists the channel; uploads nothing)

The key is the secret YOUTUBE_OAUTH_REFRESH_TOKEN: the one line tools/drive_signin.py --youtube prints, made with the
Google account that owns the channel. Without it nothing is tried."""
import argparse
import json
import re
import sys
import traceback

from .settings import ENGINE, OUT, secret
from . import status

CFG = ENGINE.get("youtube") or {}
UPLOAD_SCOPE = "https://www.googleapis.com/auth/youtube.upload"


class NotConnected(Exception):
    pass


def service():
    from google.oauth2 import credentials as oauth_credentials
    from googleapiclient.discovery import build
    from .drive import Drive
    tok = secret("YOUTUBE_OAUTH_REFRESH_TOKEN")
    if not tok:
        raise NotConnected("YouTube is not connected (no YOUTUBE_OAUTH_REFRESH_TOKEN secret).")
    d = Drive._parse_signin(tok)                    # same one-line form as the Drive sign-in
    c = oauth_credentials.Credentials(None, refresh_token=d["refresh_token"], token_uri="https://oauth2.googleapis.com/token",
                                      client_id=d["client_id"], client_secret=d["client_secret"])
    return build("youtube", "v3", credentials=c, cache_discovery=False)


def _clean(s, n):
    return re.sub(r"[<>]", "", str(s or "")).strip()[:n]


def metadata(r):
    """Title, description and tags from what the reel already has (cover title, caption, hashtags)."""
    cap = str(r.get("caption") or "")
    head = r.get("hook") or (cap.splitlines()[0] if cap else r["reel_id"])
    title = _clean(head, 100 - len(" #Shorts")).rstrip(" ·-") + " #Shorts"
    tags = [t.lstrip("#") for t in re.findall(r"#\w+", cap)][:15]
    return {"title": title, "description": _clean(cap, 4900), "tags": tags}


def upload(yt, path, meta):
    from googleapiclient.http import MediaFileUpload
    body = {"snippet": {"title": meta["title"], "description": meta["description"], "tags": meta["tags"],
                        "categoryId": str(CFG.get("category_id", "1"))},
            "status": {"privacyStatus": CFG.get("privacy", "private"), "selfDeclaredMadeForKids": bool(CFG.get("made_for_kids", False))}}
    req = yt.videos().insert(part="snippet,status", body=body, media_body=MediaFileUpload(str(path), mimetype="video/mp4", chunksize=8 * 1024 * 1024, resumable=True))
    resp = None
    while resp is None:
        _, resp = req.next_chunk(num_retries=3)
    return resp


def allowed(r):
    s = CFG.get("series", "all")
    return s == "all" or (isinstance(s, list) and r.get("series") in s)


def run(drive, day, ctl):
    """Upload today's Instagram-posted reels that are not on YouTube yet. Returns a short line for the log."""
    if not CFG.get("enabled", True):
        return "YouTube: switched off (config/engine.yaml youtube.enabled)"
    if not secret("YOUTUBE_OAUTH_REFRESH_TOKEN"):
        return "YouTube: not connected"
    if ctl.phase != "live" or ctl.mode != "run":     # rehearsal, Hold and Sleep post nothing here either (AGENT.md 5.15)
        return "YouTube: nothing (rehearsal or the switch is not on Run)"
    posted = day.reels("posted")
    done_today = sum(1 for r in posted if r.get("yt_id"))
    todo = [r for r in posted if not r.get("yt_id") and r.get("drive_reel") and allowed(r)
            and int(r.get("yt_tries") or 0) < int(CFG.get("tries", 2))]
    room = max(0, int(CFG.get("max_per_day", 8)) - done_today)
    if not todo or not room:
        return "YouTube: nothing new"
    try:
        yt = service()
    except Exception as e:
        return f"YouTube: sign-in failed ({str(e)[:120]})"
    out = []
    for r in todo[:room]:
        rid = r["reel_id"]
        try:
            local = OUT / "post" / f"{rid}.mp4"
            if not local.exists():
                drive.download(r["drive_reel"], str(local))
            meta = metadata(r)
            resp = upload(yt, local, meta)
            vid = resp.get("id")
            got = (resp.get("status") or {}).get("privacyStatus")
            day.upsert(rid, yt_id=vid, yt_url=f"https://youtube.com/shorts/{vid}", yt_privacy=got, yt_reason=None)
            line = {"reel_id": rid, "yt_id": vid, "privacy": got, "series": r.get("series"), "at": status.now().isoformat(timespec="seconds")}
            try:
                old = drive.read_text("status", "youtube.jsonl", "") or ""
                drive.write_text("status", "youtube.jsonl", old + json.dumps(line, ensure_ascii=False) + "\n")
            except Exception:
                pass
            out.append(f"{rid} on YouTube ({got})")
        except Exception as e:
            traceback.print_exc()
            tries = int(r.get("yt_tries") or 0) + 1
            day.upsert(rid, yt_tries=tries, yt_reason=f"YouTube upload failed: {str(e)[:180]}")
            out.append(f"{rid} not on YouTube yet ({str(e)[:80]})")
            if tries >= int(CFG.get("tries", 2)):
                status.alert(drive, "A reel did not go to YouTube", f"{rid}: {str(e)[:200]}",
                             "Instagram was not touched. YouTube was tried twice; this reel is left off YouTube.",
                             "Nothing, unless it repeats (then the YouTube sign-in or the channel needs a look).", level="warn")
    return "YouTube: " + "; ".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    if a.check:
        try:
            yt = service()
            ch = yt.channels().list(part="snippet", mine=True).execute().get("items", [])
            print("YouTube sign-in works." + (f" Channel: {ch[0]['snippet']['title']}" if ch else " (no channel on this account yet)"))
        except NotConnected as e:
            print(e)
        except Exception as e:
            print(f"YouTube sign-in did not work: {str(e)[:200]}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
