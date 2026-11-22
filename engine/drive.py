"""The Drive bridge (AGENT.md 4.1, 14.2).

Signs in with the service account (GDRIVE_SERVICE_ACCOUNT_JSON). If Google blocks the service
account from creating files (the known storage-quota limit), the fallback is Harish's own
sign-in token (GDRIVE_OAUTH_REFRESH_TOKEN, made with tools/drive_signin.py), which is used for
everything when present.
"""
import io
import json
import mimetypes
import os

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload, MediaInMemoryUpload, MediaIoBaseDownload
from google.oauth2 import service_account
from google.oauth2 import credentials as oauth_credentials

from .settings import ENGINE, secret

SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
FOLDER = "application/vnd.google-apps.folder"
SHORTCUT = "application/vnd.google-apps.shortcut"
SHEET = "application/vnd.google-apps.spreadsheet"
FIELDS = "id,name,mimeType,size,modifiedTime,shortcutDetails,parents,owners(emailAddress)"


class DriveError(Exception):
    pass


def _esc(name):
    return name.replace("\\", "\\\\").replace("'", "\\'")


def plain_error(e):
    """Turn a Google error into one plain sentence."""
    s = str(e)
    if "storageQuotaExceeded" in s or "Service Accounts do not have storage quota" in s:
        return ("Google does not let the robot account create files in your Drive (its storage limit is zero). "
                "Fix: one extra sign-in on your laptop, then add the secret GDRIVE_OAUTH_REFRESH_TOKEN.")
    if "insufficientFilePermissions" in s or "403" in s and "permission" in s.lower():
        return "The robot account has no permission on this folder. Share the iNiKKi Reels folder with it as Editor."
    if "notFound" in s or "404" in s:
        return "The folder or file was not found. Check GDRIVE_ROOT_FOLDER_ID."
    if "invalid_grant" in s:
        return "The Drive sign-in token is no longer valid. Make a new one with tools/drive_signin.py."
    return s[:400]


class Drive:
    def __init__(self):
        self.root = secret("GDRIVE_ROOT_FOLDER_ID")
        if not self.root:
            raise DriveError("Missing secret GDRIVE_ROOT_FOLDER_ID")
        self.mode, self.creds = self._credentials()
        self.svc = build("drive", "v3", credentials=self.creds, cache_discovery=False)
        self._folders = {"": self.root}

    # ---------- sign-in ----------
    @staticmethod
    def _credentials():
        tok = secret("GDRIVE_OAUTH_REFRESH_TOKEN")
        if tok:
            d = Drive._parse_signin(tok)
            # no scopes asked on refresh: the token keeps what it was granted, so a Drive-only sign-in still works
            c = oauth_credentials.Credentials(
                None, refresh_token=d["refresh_token"], token_uri="https://oauth2.googleapis.com/token",
                client_id=d["client_id"], client_secret=d["client_secret"])
            return "harish_signin", c
        sa = secret("GDRIVE_SERVICE_ACCOUNT_JSON")
        if sa:
            try:
                info = json.loads(sa)
            except ValueError as e:
                raise DriveError(f"GDRIVE_SERVICE_ACCOUNT_JSON is not valid JSON ({e})")
            return "service_account", service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        raise DriveError("No Drive key. Add the secret GDRIVE_OAUTH_REFRESH_TOKEN (the Drive sign-in, AGENT.md 19.2).")

    @staticmethod
    def _parse_signin(tok):
        """Accept the one line drive_signin.py prints, or the whole printout it sits in. Say what was pasted otherwise, without revealing it."""
        import re
        m = re.search(r"\{[^{}]*refresh_token[^{}]*\}", tok, re.S)
        if m:
            try:
                d = json.loads(m.group(0))
                if all(k in d for k in ("client_id", "client_secret", "refresh_token")):
                    return d
            except ValueError:
                pass
        shape = f"{len(tok)} characters"
        if tok.startswith("1//"):
            hint = "This looks like only the refresh token. The secret must be the whole line the script prints, which also holds client_id and client_secret."
        elif '"installed"' in tok or '"web"' in tok:
            hint = "This looks like the downloaded client_secret file. That file is not the secret: run  python tools/drive_signin.py  with the file next to it, sign in, and paste the single line it prints at the end."
        elif tok.startswith("ya29"):
            hint = "This looks like a short-lived access token. Run  python tools/drive_signin.py  and paste the single line it prints at the end."
        else:
            hint = "Run  python tools/drive_signin.py  on your laptop and paste the single line it prints at the end (it starts with {\"client_id\")."
        raise DriveError(f"The secret GDRIVE_OAUTH_REFRESH_TOKEN is not in the expected shape ({shape}). {hint}")

    def who(self):
        """Email the Engine is signed in as."""
        if self.mode == "service_account":
            return json.loads(secret("GDRIVE_SERVICE_ACCOUNT_JSON")).get("client_email", "service account")
        try:
            return self.svc.about().get(fields="user(emailAddress)").execute(num_retries=3)["user"]["emailAddress"]
        except HttpError:
            return "signed-in account"

    def quota(self):
        a = self.svc.about().get(fields="storageQuota").execute(num_retries=3).get("storageQuota", {})
        gb = lambda k: round(int(a.get(k, 0)) / 1e9, 2)
        return {"used_gb": gb("usage"), "limit_gb": gb("limit") if a.get("limit") else None, "in_drive_gb": gb("usageInDrive")}

    # ---------- reading ----------
    def _list(self, q):
        out, token = [], None
        while True:
            r = self.svc.files().list(q=q + " and trashed = false", fields=f"nextPageToken,files({FIELDS})", pageSize=200,
                                      pageToken=token, supportsAllDrives=True, includeItemsFromAllDrives=True).execute(num_retries=3)
            out += r.get("files", [])
            token = r.get("nextPageToken")
            if not token:
                return out

    def children(self, folder_id, resolve_shortcuts=True):
        items = self._list(f"'{folder_id}' in parents")
        if resolve_shortcuts:
            for it in items:
                if it["mimeType"] == SHORTCUT and it.get("shortcutDetails"):
                    it["id"] = it["shortcutDetails"]["targetId"]
                    it["mimeType"] = it["shortcutDetails"].get("targetMimeType", it["mimeType"])
        return items

    def find_child(self, parent_id, name, mime=None):
        q = f"'{parent_id}' in parents and name = '{_esc(name)}'"
        if mime:
            q += f" and mimeType = '{mime}'"
        items = self._list(q)
        if not items:
            return None
        # When names clash, prefer the item Harish owns over one the robot account made
        it = sorted(items, key=lambda x: self._is_mine(x))[0]
        if it["mimeType"] == SHORTCUT and it.get("shortcutDetails"):
            it["id"] = it["shortcutDetails"]["targetId"]
            it["mimeType"] = it["shortcutDetails"].get("targetMimeType", it["mimeType"])
        return it

    def folder(self, path, create=True):
        """Folder id for a path like 'status' or 'music/inbox' under the root. Creates it when missing."""
        path = path.strip("/")
        if path in self._folders:
            return self._folders[path]
        parent_path, _, name = path.rpartition("/")
        parent = self.folder(parent_path, create=create)
        if not parent:
            return None
        f = self.find_child(parent, name, FOLDER)
        if not f:
            if not create:
                return None
            f = self.svc.files().create(body={"name": name, "mimeType": FOLDER, "parents": [parent]}, fields="id",
                                        supportsAllDrives=True).execute(num_retries=3)
        self._folders[path] = f["id"]
        return f["id"]

    def _is_mine(self, item):
        mine = self.who() if self.mode == "service_account" else None
        return bool(mine) and any(o.get("emailAddress") == mine for o in item.get("owners", []))

    def tidy_duplicates(self):
        """Trash empty folders the robot account made when Harish already has one with the same name."""
        if self.mode != "service_account":
            return []
        seen, trashed = {}, []
        for it in self.children(self.root, resolve_shortcuts=False):
            if it["mimeType"] != FOLDER:
                continue
            seen.setdefault(it["name"], []).append(it)
        for name, items in seen.items():
            if len(items) < 2:
                continue
            for it in items:
                if self._is_mine(it) and not self.children(it["id"]):
                    self.trash(it["id"])
                    trashed.append(name)
                    self._folders.pop(name, None)
        return trashed

    def ensure_tree(self):
        made = []
        try:
            for n in self.tidy_duplicates():
                made.append(f"removed duplicate {n}")
        except HttpError as e:
            made.append(f"could not tidy: {plain_error(e)}")
        for p in ENGINE["drive"]["folders"]:
            if p == "music" and self.music_folder():
                continue
            before = self.folder(p, create=False)
            if not before:
                self.folder(p, create=True)
                made.append(p)
        return made

    def music_folder(self):
        """The music folder, by any of its known names (Harish's folder is 'background music (1)')."""
        if "music" in self._folders:
            return self._folders["music"]
        for name in ENGINE["drive"]["music_folder_aliases"]:
            f = self.find_child(self.root, name, FOLDER)
            if f:
                self._folders["music"] = f["id"]
                return f["id"]
        return None

    def read_bytes(self, file_id):
        buf = io.BytesIO()
        dl = MediaIoBaseDownload(buf, self.svc.files().get_media(fileId=file_id, supportsAllDrives=True))
        done = False
        while not done:
            _, done = dl.next_chunk(num_retries=3)
        return buf.getvalue()

    def read_text(self, folder_path, name, default=None):
        fid = self.folder(folder_path, create=False)
        f = self.find_child(fid, name) if fid else None
        return self.read_bytes(f["id"]).decode("utf-8") if f else default

    def read_json(self, folder_path, name, default=None):
        t = self.read_text(folder_path, name)
        return json.loads(t) if t else default

    def download(self, file_id, local_path):
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(self.read_bytes(file_id))
        return local_path

    # ---------- writing ----------
    def _put(self, media, parent_id, name, replace=True):
        existing = self.find_child(parent_id, name) if replace else None
        if existing and existing["mimeType"] != SHORTCUT:
            return self.svc.files().update(fileId=existing["id"], media_body=media, fields=FIELDS,
                                           supportsAllDrives=True).execute(num_retries=3)
        return self.svc.files().create(body={"name": name, "parents": [parent_id]}, media_body=media, fields=FIELDS,
                                       supportsAllDrives=True).execute(num_retries=3)

    def upload(self, local_path, folder_path, name=None, replace=True):
        name = name or os.path.basename(local_path)
        mime = mimetypes.guess_type(name)[0] or "application/octet-stream"
        media = MediaFileUpload(local_path, mimetype=mime, resumable=os.path.getsize(local_path) > 5_000_000)
        return self._put(media, self.folder(folder_path), name, replace)

    def write_text(self, folder_path, name, text, mime="text/plain"):
        media = MediaInMemoryUpload(text.encode("utf-8"), mimetype=mime)
        return self._put(media, self.folder(folder_path), name, replace=True)

    def write_json(self, folder_path, name, obj):
        return self.write_text(folder_path, name, json.dumps(obj, ensure_ascii=False, indent=2), "application/json")

    def trash(self, file_id):
        return self.svc.files().update(fileId=file_id, body={"trashed": True}, supportsAllDrives=True).execute(num_retries=3)

    def link(self, file_id):
        return f"https://drive.google.com/file/d/{file_id}/view"

    def folder_link(self, folder_id):
        return f"https://drive.google.com/drive/folders/{folder_id}"


# ---------- command line for the cloud jobs (GitHub Actions; never Harish's laptop) ----------
#   python -m engine.drive check                          which sign-in works, and the folders in the root
#   python -m engine.drive sync-music [plans...]          the tracks these plans use (all when none) into engine/.cache/music
#   python -m engine.drive upload-out <folder> [--here] <plans...>
#                                                         finished reels into <folder>/<date>/ (a plan's own drive_folder
#                                                         wins unless --here is given)
#   python -m engine.drive upload <file> <folder/path> [--name NAME]
#   python -m engine.drive download <file_id> <out>
# Each command prints one JSON line.
HERE = os.path.dirname(os.path.abspath(__file__))
MUSIC_CACHE = os.path.join(HERE, ".cache", "music")


def music_index():
    """The tracks the approved looks use: key -> Drive file id (engine/music_index.json), plus the trending songs from the
    laptop run (data/music/trending.json, AGENT.md 5.4)."""
    with open(os.path.join(HERE, "music_index.json"), encoding="utf-8") as f:
        idx = json.load(f)["tracks"]
    try:
        with open(os.path.join(HERE, "..", "data", "music", "trending.json"), encoding="utf-8") as f:
            for t in json.load(f).get("tracks", []):
                idx.setdefault(t["key"], {"drive_id": t["drive_id"], "title": t.get("title"), "mood": ", ".join(t.get("best") or []), "trending": True})
    except (OSError, ValueError, KeyError):
        pass
    return idx


def plan_tracks(plan):
    """Track keys a plan's music sections name."""
    return [s["track"] for s in (plan.get("music") or {}).get("sections", []) if s.get("track")]


def sync_music(drive, keys=None):
    """Download the named tracks (all when none) into engine/.cache/music; tracks already there are skipped."""
    idx = music_index()
    os.makedirs(MUSIC_CACHE, exist_ok=True)
    got, missing = [], []
    for key in keys or list(idx):
        if key not in idx:
            missing.append(key)
            continue
        out = os.path.join(MUSIC_CACHE, key + ".mp3")
        if not os.path.exists(out):
            drive.download(idx[key]["drive_id"], out)
            got.append(key)
    return got, missing


def finished_name(plan):
    """'<date> · <cover title>' — how a finished reel is named in Drive."""
    rid = plan.get("reel_id") or plan["id"]
    title = (plan.get("package") or {}).get("cover") or rid
    return rid[:10], f"{rid[:10]} · {title.replace('/', '-')}"


def upload_out(drive, folder, plan_paths, here=False):
    sent = []
    for p in plan_paths:
        with open(p, encoding="utf-8") as f:
            plan = json.load(f)
        rid = plan.get("reel_id") or plan["id"]
        mp4 = os.path.join(HERE, ".work", "out", rid + ".mp4")
        if not os.path.exists(mp4):
            continue
        date, name = finished_name(plan)
        where = f"{folder if here else plan.get('drive_folder', folder)}/{date}"
        drive.upload(mp4, where, name + ".mp4")
        checks = os.path.join(HERE, ".work", rid, "inspect.json")
        if os.path.exists(checks):
            drive.upload(checks, where, name + " · checks.json")
        sent.append(f"{where}/{name}.mp4")
    return sent


def copy_old(d, dry=False):
    """One-time move to a new Google account: copy everything from the old 'iNiKKi Reels' folder, shared with the
    new account, into the new root folder. Copies stay inside Google (nothing is downloaded). Safe to run again:
    a file whose name is already in the same place is left alone. Shortcuts are followed, so their contents come too."""
    if d.mode != "harish_signin":
        return {"ok": False, "reason": "needs the Drive sign-in of the new account (GDRIVE_OAUTH_REFRESH_TOKEN)"}
    name = ENGINE["drive"].get("root_name", "iNiKKi Reels")
    q = f"sharedWithMe and name = '{_esc(name)}' and mimeType = '{FOLDER}' and trashed = false"
    old = [f for f in d._list(q) if f["id"] != d.root]
    if len(old) != 1:
        return {"ok": False, "reason": f"found {len(old)} shared folders named '{name}'; share exactly one old folder with the new account"}
    counts = {"copied": 0, "already_there": 0, "folders": 0, "failed": []}

    def walk(src, dst, path):
        here = {(it["name"], it["mimeType"] == FOLDER): it["id"] for it in d.children(dst, resolve_shortcuts=False)} if dst else {}
        for it in d.children(src):
            kind = it["mimeType"]
            if kind == SHORTCUT:
                continue                              # a shortcut whose target is gone or out of reach
            p = f"{path}/{it['name']}"
            if kind == FOLDER:
                sub = here.get((it["name"], True))
                if not sub and not dry:
                    sub = d.svc.files().create(body={"name": it["name"], "mimeType": FOLDER, "parents": [dst]},
                                               fields="id", supportsAllDrives=True).execute(num_retries=3)["id"]
                counts["folders"] += 1
                walk(it["id"], sub, p)
            elif (it["name"], False) in here:
                counts["already_there"] += 1
            else:
                if not dry:
                    try:
                        d.svc.files().copy(fileId=it["id"], body={"name": it["name"], "parents": [dst]},
                                           fields="id", supportsAllDrives=True).execute(num_retries=3)
                    except HttpError as e:
                        counts["failed"].append(f"{p}: {plain_error(e)}")
                        continue
                counts["copied"] += 1

    walk(old[0]["id"], d.root, "")
    counts["failed"] = counts["failed"][:20]
    return {"ok": not counts["failed"], "dry": dry, **counts}


def main(argv=None):
    import sys
    a = list(sys.argv[1:] if argv is None else argv)
    cmd = a.pop(0) if a else "check"

    def say(**kw):
        print(json.dumps(kw, ensure_ascii=False))
        return kw

    if cmd == "check":
        try:
            d = Drive()
            names = sorted(it["name"] for it in d.children(d.root, resolve_shortcuts=False) if it["mimeType"] == FOLDER)
            return say(ok=True, ready=True, sign_in=d.mode, can_upload=d.mode == "harish_signin", folders=names)
        except Exception as e:          # a missing or wrong key: say so plainly; the job carries on without Drive
            return say(ok=False, ready=False, reason=plain_error(e))
    d = Drive()
    if cmd == "sync-music":
        keys = []
        for p in a:
            with open(p, encoding="utf-8") as f:
                keys += plan_tracks(json.load(f))
        got, missing = sync_music(d, sorted(set(keys)) or None)
        return say(ok=not missing, downloaded=got, not_in_index=missing)
    if cmd == "upload-out":
        here = "--here" in a
        a = [x for x in a if x != "--here"]
        return say(ok=True, uploaded=upload_out(d, a[0], a[1:], here))
    if cmd == "upload":
        name = a[a.index("--name") + 1] if "--name" in a else None
        f = d.upload(a[0], a[1], name)
        return say(ok=True, uploaded=f.get("name"), id=f.get("id"), folder=a[1])
    if cmd == "download":
        d.download(a[0], a[1])
        return say(ok=True, file=a[1])
    if cmd == "copy-old":
        return say(**copy_old(d, dry="--dry" in a))
    raise SystemExit(f"unknown command: {cmd}")


if __name__ == "__main__":
    main()
