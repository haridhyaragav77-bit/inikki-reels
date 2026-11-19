#!/usr/bin/env python3
"""One extra sign-in for Google Drive (only needed if the smoke test says the robot account cannot upload).

Run this on your laptop:   python tools/drive_signin.py
It prints the steps, opens your browser for a Google sign-in, and ends by printing ONE line.
Paste that whole line as the GitHub Secret  GDRIVE_OAUTH_REFRESH_TOKEN . Never paste it into a chat.

YouTube Shorts (AGENT.md 5.15):   python tools/drive_signin.py --youtube
Same steps, but sign in with the Google account that owns the YouTube channel (pick the channel if Google asks), and
paste the printed line as the GitHub Secret  YOUTUBE_OAUTH_REFRESH_TOKEN . In the Cloud console, also turn on
"YouTube Data API v3" (APIs & Services > Library) for the same project.
"""
import glob
import json
import os
import subprocess
import sys

SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/spreadsheets"]
YT_SCOPES = ["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube.readonly"]
YT = "--youtube" in sys.argv
SECRET = "YOUTUBE_OAUTH_REFRESH_TOKEN" if YT else "GDRIVE_OAUTH_REFRESH_TOKEN"

STEPS = """
Before this works, Google needs a "sign-in client" for the iNiKKi project (one time, about 5 minutes):
 1. Open console.cloud.google.com and pick the project that has the Drive API turned on.
 2. Menu > APIs & Services > OAuth consent screen (or "Google Auth platform > Branding").
    Fill the app name (iNiKKi Reels) and your email. Audience: External. Save.
    Under "Audience" set Publishing status to  In production  (ignore the verification notice; only you use it).
 3. Menu > APIs & Services > Credentials > Create credentials > OAuth client ID > Application type: Desktop app.
    Download the JSON file and put it in the same folder as this script (name starts with client_secret).
 4. Run this script again. A browser opens. Sign in with the Google account that owns the iNiKKi Reels folder.
    If Google shows "This app isn't verified", click Advanced > Go to iNiKKi Reels (unsafe). It is your own app.
 5. Copy the one printed line into the GitHub Secret  GDRIVE_OAUTH_REFRESH_TOKEN  and delete the JSON file.
"""


def main():
    files = glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_secret*.json")) + glob.glob("client_secret*.json")
    if not files:
        print(STEPS)
        print("No client_secret*.json found next to this script yet. Do steps 1-3, then run again.")
        sys.exit(1)
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--quiet", "google-auth-oauthlib"])
        from google_auth_oauthlib.flow import InstalledAppFlow
    flow = InstalledAppFlow.from_client_secrets_file(files[0], scopes=YT_SCOPES if YT else SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not creds.refresh_token:
        print("Google did not give a long-lived token. Remove the app's access at myaccount.google.com/permissions and run again.")
        sys.exit(1)
    line = json.dumps({"client_id": creds.client_id, "client_secret": creds.client_secret, "refresh_token": creds.refresh_token})
    print(f"\nDone. Copy the ENTIRE next line into the GitHub Secret {SECRET}:\n")
    print(line)
    print("\nThen delete the client_secret JSON file from your laptop.")


if __name__ == "__main__":
    main()
