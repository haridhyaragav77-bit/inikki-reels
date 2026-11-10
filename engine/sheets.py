"""The Dashboard sheet "iNiKKi Dashboard" (AGENT.md 13.2). Lives in the Drive root folder."""
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from .drive import SHEET, DriveError, plain_error
from .settings import ENGINE


class Dashboard:
    def __init__(self, drive):
        self.drive = drive
        self.name = ENGINE["drive"]["dashboard_sheet_name"]
        self.tabs = ENGINE["drive"]["dashboard_tabs"]
        self.svc = build("sheets", "v4", credentials=drive.creds, cache_discovery=False)
        self.id, self.created = self._find_or_create()

    def _find_or_create(self):
        f = self.drive.find_child(self.drive.root, self.name, SHEET)
        if f:
            return f["id"], False
        try:
            f = self.drive.svc.files().create(body={"name": self.name, "mimeType": SHEET, "parents": [self.drive.root]},
                                              fields="id", supportsAllDrives=True).execute(num_retries=3)
            return f["id"], True
        except HttpError as e:
            raise DriveError(
                f"Could not create the sheet: {plain_error(e)} "
                f"Quick fix: create a blank Google Sheet named '{self.name}' inside the iNiKKi Reels folder; the Engine will fill it.")

    def link(self):
        return f"https://docs.google.com/spreadsheets/d/{self.id}"

    def ensure_tabs(self):
        meta = self.svc.spreadsheets().get(spreadsheetId=self.id, fields="sheets.properties").execute(num_retries=3)
        have = [s["properties"]["title"] for s in meta["sheets"]]
        reqs = [{"addSheet": {"properties": {"title": t}}} for t in self.tabs if t not in have]
        if reqs:
            self.svc.spreadsheets().batchUpdate(spreadsheetId=self.id, body={"requests": reqs}).execute(num_retries=3)
        # Rename the default "Sheet1" to the first tab if it is still there and the first tab was just added
        if "Sheet1" in have and self.tabs[0] not in have:
            pass  # Keep it simple: Sheet1 stays until the Dashboard job rewrites the layout in Phase 3
        return [t for t in self.tabs if t not in have]

    def write(self, tab, a1, rows):
        return self.svc.spreadsheets().values().update(
            spreadsheetId=self.id, range=f"'{tab}'!{a1}", valueInputOption="USER_ENTERED",
            body={"values": rows}).execute(num_retries=3)

    def append(self, tab, rows):
        return self.svc.spreadsheets().values().append(
            spreadsheetId=self.id, range=f"'{tab}'!A1", valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS", body={"values": rows}).execute(num_retries=3)

    def clear(self, tab):
        return self.svc.spreadsheets().values().clear(spreadsheetId=self.id, range=f"'{tab}'!A:Z", body={}).execute(num_retries=3)
