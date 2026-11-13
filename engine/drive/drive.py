#!/usr/bin/env python3
"""Google Drive bridge for the Engine (AGENT.md 4.1: Drive is where media, status and settings live).

Runs in the cloud (GitHub Actions or a cloud session), never on Harish's laptop. Full-size files are uploaded
in chunks (resumable upload), so reels go to Drive at full quality.

Credentials come from environment variables (GitHub Secrets), never from files in the repository:
  GDRIVE_ROOT_FOLDER_ID          the "iNiKKi Reels" folder
  GDRIVE_OAUTH_CLIENT_ID         } Harish's one-time sign-in (needed to UPLOAD: a service account
  GDRIVE_OAUTH_CLIENT_SECRET     } cannot store files in a personal Drive)
  GDRIVE_OAUTH_REFRESH_TOKEN     }
  GDRIVE_SERVICE_ACCOUNT_JSON    optional: reads shared folders (music) when the sign-in is not set

Commands (each prints one JSON line at the end):
  check                          which sign-in works, and the folders in the root
  sync-music                     download the tracks in engine/music_index.json that are missing locally
  upload <file> <folder/path> [--name NAME]   create folders as needed; replace a file with the same name
  upload-out <folder> <plans...> upload finished reels for these plans into <folder>/<date>/
  download <file_id> <out>
"""
import sys, os, json, time, mimetypes

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
FOLDER = "application/vnd.google-apps.folder"


def session():
    """An authorised HTTP session: Harish's sign-in first (can upload), else the service account (read)."""
    cid, sec, tok = (os.environ.get(k, "").strip() for k in ("GDRIVE_OAUTH_CLIENT_ID", "GDRIVE_OAUTH_CLIENT_SECRET", "GDRIVE_OAUTH_REFRESH_TOKEN"))
    # The sign-in secret may also be the single line {"client_id":..,"client_secret":..,"refresh_token":..}
    # made by the earlier sign-in script; accept both shapes.
    if tok.startswith("{") or '"refresh_token"' in tok:
        import re
        m = re.search(r"\{[^{}]*refresh_token[^{}]*\}", tok, re.S)
        try:
            d = json.loads(m.group(0)) if m else {}
            cid, sec, tok = d.get("client_id", cid), d.get("client_secret", sec), d.get("refresh_token", "")
        except ValueError:
            tok = ""
    sa = os.environ.get("GDRIVE_SERVICE_ACCOUNT_JSON", "").strip()
    if not ((cid and sec and tok) or sa):
        return None, None
    from google.auth.transport.requests import AuthorizedSession
    if cid and sec and tok:
        from google.oauth2.credentials import Credentials
        creds = Credentials(None, refresh_token=tok, client_id=cid, client_secret=sec,
                            token_uri="https://oauth2.googleapis.com/token", scopes=["https://www.googleapis.com/auth/drive"])
        return AuthorizedSession(creds), "sign-in"
    if sa:
        from google.oauth2 import service_account
        creds = service_account.Credentials.from_service_account_info(json.loads(sa), scopes=["https://www.googleapis.com/auth/drive"])
        return AuthorizedSession(creds), "service-account"
    return None, None


def done(**kw):
    print(json.dumps(kw, ensure_ascii=False))


def q_escape(s):
    return s.replace("\\", "\\\\").replace("'", "\\'")


def children(s, parent, name=None, folders_only=False):
    q = [f"'{parent}' in parents", "trashed=false"]
    if name:
        q.append(f"name='{q_escape(name)}'")
    if folders_only:
        q.append(f"mimeType='{FOLDER}'")
    out, page = [], None
    while True:
        r = s.get(f"{API}/files", params={"q": " and ".join(q), "fields": "nextPageToken,files(id,name,mimeType,size)", "pageSize": 1000,
                                          "pageToken": page, "supportsAllDrives": True, "includeItemsFromAllDrives": True})
        r.raise_for_status(); d = r.json(); out += d.get("files", [])
        page = d.get("nextPageToken")
        if not page:
            return out


def folder_path(s, root, path):
    """Find or create root/a/b/c and return its id."""
    cur = root
    for part in [p for p in path.split("/") if p]:
        found = children(s, cur, part, folders_only=True)
        if found:
            cur = found[0]["id"]
        else:
            r = s.post(f"{API}/files", params={"supportsAllDrives": True}, json={"name": part, "mimeType": FOLDER, "parents": [cur]})
            r.raise_for_status(); cur = r.json()["id"]
    return cur


def upload(s, path, parent, name=None):
    """Resumable upload in 8 MB chunks; replaces a same-named file in the folder."""
    name = name or os.path.basename(path)
    mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
    size = os.path.getsize(path)
    existing = children(s, parent, name)
    if existing:
        url = f"{UPLOAD}/{existing[0]['id']}?uploadType=resumable&supportsAllDrives=true"
        r = s.patch(url, json={}, headers={"X-Upload-Content-Type": mime, "X-Upload-Content-Length": str(size)})
    else:
        url = f"{UPLOAD}?uploadType=resumable&supportsAllDrives=true"
        r = s.post(url, json={"name": name, "parents": [parent]}, headers={"X-Upload-Content-Type": mime, "X-Upload-Content-Length": str(size)})
    if r.status_code == 403 and "storageQuota" in r.text:
        raise SystemExit("Drive refused the upload: a service account has no storage. Add Harish's one-time sign-in "
                         "(GDRIVE_OAUTH_CLIENT_ID / _SECRET / _REFRESH_TOKEN, AGENT.md 19.2).")
    r.raise_for_status()
    loc, chunk, sent = r.headers["Location"], 8 * 1024 * 1024, 0
    with open(path, "rb") as f:
        while sent < size:
            data = f.read(chunk)
            end = sent + len(data) - 1
            for attempt in range(5):
                rr = s.put(loc, data=data, headers={"Content-Length": str(len(data)), "Content-Range": f"bytes {sent}-{end}/{size}"})
                if rr.status_code in (200, 201, 308):
                    break
                time.sleep(2 ** attempt)
            else:
                rr.raise_for_status()
            sent = end + 1
    return rr.json() if rr.status_code in (200, 201) else {"name": name}


def main():
    a = sys.argv[1:]
    cmd = a[0] if a else "check"
    s, how = session()
    root = os.environ.get("GDRIVE_ROOT_FOLDER_ID", "").strip()
    if cmd == "check":
        if not s or not root:
            missing = [k for k in ("GDRIVE_ROOT_FOLDER_ID", "GDRIVE_OAUTH_REFRESH_TOKEN", "GDRIVE_SERVICE_ACCOUNT_JSON") if not os.environ.get(k)]
            return done(ok=False, ready=False, reason="Drive keys are not set yet", missing=missing)
        try:
            names = sorted(f["name"] for f in children(s, root, folders_only=True))
        except Exception as e:  # wrong or expired key: say so plainly, don't crash the run
            return done(ok=False, ready=False, reason=f"Drive refused the sign-in: {str(e)[:160]}")
        return done(ok=True, ready=True, sign_in=how, can_upload=(how == "sign-in"), folders=names)
    if not s:
        raise SystemExit("No Drive credentials in this environment (see AGENT.md 19.2).")
    if cmd == "sync-music":
        idx = json.load(open(os.path.join(ROOT, "engine", "music_index.json"), encoding="utf-8"))
        cache = os.path.join(ROOT, "engine", ".cache", "music"); os.makedirs(cache, exist_ok=True)
        got = []
        for key, t in idx["tracks"].items():
            out = os.path.join(cache, key + ".mp3")
            if os.path.exists(out):
                continue
            r = s.get(f"{API}/files/{t['drive_id']}", params={"alt": "media", "supportsAllDrives": True}); r.raise_for_status()
            open(out, "wb").write(r.content); got.append(key)
        return done(ok=True, downloaded=got)
    if cmd == "download":
        r = s.get(f"{API}/files/{a[1]}", params={"alt": "media", "supportsAllDrives": True}); r.raise_for_status()
        open(a[2], "wb").write(r.content); return done(ok=True, file=a[2])
    if cmd == "upload":
        name = a[a.index("--name") + 1] if "--name" in a else None
        parent = folder_path(s, root, a[2])
        f = upload(s, a[1], parent, name)
        return done(ok=True, uploaded=f.get("name"), id=f.get("id"), folder=a[2])
    if cmd == "upload-out":
        folder, plans, sent = a[1], a[2:], []
        for p in plans:
            plan = json.load(open(p, encoding="utf-8"))
            mp4 = os.path.join(ROOT, "engine", ".work", "out", plan["id"] + ".mp4")
            if not os.path.exists(mp4):
                continue
            date = plan["id"][:10]
            title = plan.get("package", {}).get("cover", plan["id"]).replace("/", "-")
            parent = folder_path(s, root, f"{plan.get('drive_folder', folder)}/{date}")
            f = upload(s, mp4, parent, f"{date} · {title}.mp4")
            sent.append(f.get("name"))
            ins = os.path.join(ROOT, "engine", ".work", plan["id"], "inspect.json")
            if os.path.exists(ins):
                upload(s, ins, parent, f"{date} · {title} · checks.json")
        return done(ok=True, uploaded=sent)
    raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
