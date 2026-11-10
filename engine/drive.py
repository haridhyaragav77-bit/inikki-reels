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
FIELDS = "id,name,mimeType,size,modifiedTime,shortcutDetails,parents"


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
    return s[:300]


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
            try:
                d = json.loads(tok)
                c = oauth_credentials.Credentials(
                    None, refresh_token=d["refresh_token"], token_uri="https://oauth2.googleapis.com/token",
                    client_id=d["client_id"], client_secret=d["client_secret"], scopes=SCOPES)
                return "harish_signin", c
            except (ValueError, KeyError) as e:
                raise DriveError(f"GDRIVE_OAUTH_REFRESH_TOKEN is not the one-line JSON that tools/drive_signin.py prints ({e})")
        sa = secret("GDRIVE_SERVICE_ACCOUNT_JSON")
        if sa:
            try:
                info = json.loads(sa)
            except ValueError as e:
                raise DriveError(f"GDRIVE_SERVICE_ACCOUNT_JSON is not valid JSON ({e})")
            return "service_account", service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
        raise DriveError("No Drive key. Add the secret GDRIVE_SERVICE_ACCOUNT_JSON.")

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
        it = items[0]
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

    def ensure_tree(self):
        made = []
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
