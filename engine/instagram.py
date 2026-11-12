"""Instagram: reading stats and publishing reels (AGENT.md 5 stages 9-10). Works through either kind of Meta token."""
import json
import os
import re
import time

import requests

from .settings import ENGINE, secret


class InstagramError(Exception):
    pass


def plain_error(j):
    e = (j or {}).get("error", {}) if isinstance(j, dict) else {}
    msg = e.get("message", str(j)[:200])
    code = e.get("code")
    if "api access blocked" in msg.lower():
        return ("Meta has blocked this app's API access (the app, not the token). Open developers.facebook.com > My Apps > the app: "
                "the banner at the top says why (often the yearly Data Use Checkup or a policy review). Fix that; the same token then works again.")
    if code == 190 or "access token" in msg.lower() and ("expired" in msg.lower() or "invalid" in msg.lower()):
        return ("The Instagram token has expired or is not valid. Make a new long-lived token and update the secret IG_ACCESS_TOKEN."
                f" (Meta says: {msg[:140]})")
    if code == 10 or "permission" in msg.lower():
        return f"The Instagram token is missing a permission: {msg}"
    return msg


ROUTES = {"instagram_login": "https://graph.instagram.com", "facebook_login": "https://graph.facebook.com"}


class Instagram:
    """Works with either kind of Meta token:
    - Instagram Login (graph.instagram.com), the route in the design
    - Facebook Login / System User (graph.facebook.com), which needs the account linked to a Facebook Page
    The route is found by probing once; the same calls work on both."""

    def __init__(self):
        self.token = secret("IG_ACCESS_TOKEN")
        self.user_id = secret("IG_USER_ID")
        if not self.token or not self.user_id:
            raise InstagramError("Missing secret " + ", ".join(n for n in ["IG_ACCESS_TOKEN", "IG_USER_ID"] if not secret(n)))
        self.versions = list(ENGINE["instagram"]["api_versions"])
        self.version = self.versions[0]
        self.route, self.base = self._probe()
        self.note = ""

    def _probe(self):
        said = {}
        for route, host in ROUTES.items():
            fields = "id,username" if route == "instagram_login" else "id,name"
            try:
                r = requests.get(f"{host}/{self.version}/me", params={"fields": fields, "access_token": self.token}, timeout=30).json()
            except Exception as e:
                said[route] = str(e)[:120]
                continue
            if "error" not in r:
                return route, host
            said[route] = r["error"].get("message", "")
        fb = str(said.get("facebook_login", ""))
        if "api access blocked" in fb.lower():     # Meta refuses the app right now: say so, plainly
            raise InstagramError(plain_error({"error": {"message": fb}}))
        if fb and "cannot parse" not in fb.lower():   # the Facebook door is the one this token uses: report its own answer
            raise InstagramError(f"Instagram refused the call. Meta says: {fb[:200]}")
        return "instagram_login", ROUTES["instagram_login"]

    def resolve_user(self):
        """Facebook route: find the Instagram professional account behind the token's Pages."""
        j = self.get("me/accounts", fields="name,instagram_business_account{id,username,followers_count,media_count}", limit=50)
        found = [(p["instagram_business_account"], p.get("name")) for p in j.get("data", []) if p.get("instagram_business_account")]
        return found

    def get(self, path, **params):
        params["access_token"] = self.token
        last = None
        for v in self.versions:
            r = requests.get(f"{self.base}/{v}/{path.lstrip('/')}", params=params, timeout=60)
            try:
                j = r.json()
            except ValueError:
                j = {"error": {"message": r.text[:200]}}
            if r.ok and "error" not in j:
                self.version = v
                return j
            last = j
            msg = str(j.get("error", {}).get("message", ""))
            if "version" in msg.lower() and ("unknown" in msg.lower() or "not supported" in msg.lower()):
                continue  # try an older API version
            raise InstagramError(plain_error(j))
        raise InstagramError(plain_error(last))

    def me(self):
        if self.route == "facebook_login":
            try:
                return self.get(self.user_id, fields="id,username,name,followers_count,follows_count,media_count")
            except InstagramError as e:
                found = self.resolve_user()
                if not found:
                    raise InstagramError(f"{e} No Instagram professional account is linked to a Facebook Page this token can see. "
                                         "Link @inikki_reels to a Facebook Page (Instagram app > Settings > Business tools), or use an Instagram-login token.")
                acct, page = found[0]
                self.note = f"IG_USER_ID did not match; the token sees @{acct.get('username')} (id {acct['id']}) through the Page '{page}'. Update the secret IG_USER_ID to {acct['id']}."
                self.user_id = acct["id"]
                return self.get(self.user_id, fields="id,username,name,followers_count,follows_count,media_count")
        return self.get(self.user_id, fields="user_id,username,name,account_type,followers_count,follows_count,media_count")

    def media(self, limit=10):
        j = self.get(f"{self.user_id}/media", limit=limit,
                     fields="id,caption,media_type,media_product_type,timestamp,permalink,like_count,comments_count")
        return j.get("data", [])

    def insights(self, media_id, wanted=None):
        """Insights for one reel. Unknown metric names are dropped automatically (the API lists the valid ones)."""
        wanted = list(wanted or ENGINE["instagram"]["reel_metrics_wanted"])
        for _ in range(4):
            try:
                j = self.get(f"{media_id}/insights", metric=",".join(wanted))
                return {d["name"]: (d.get("values", [{}])[0].get("value") if d.get("values") else d.get("total_value", {}).get("value"))
                        for d in j.get("data", [])}, wanted
            except InstagramError as e:
                msg = str(e)
                m = re.search(r"must be one of the following values: ([^\n]+)", msg)
                if m:
                    valid = {x.strip() for x in m.group(1).replace(".", "").split(",")}
                    keep = [w for w in wanted if w in valid]
                    if keep and keep != wanted:
                        wanted = keep
                        continue
                m = re.search(r"does not support the ([\w, ]+?) metric", msg)
                if m:
                    bad = {x.strip() for x in m.group(1).split(",")}
                    keep = [w for w in wanted if w not in bad]
                    if keep and keep != wanted:
                        wanted = keep
                        continue
                m = re.search(r"metric\[(\d+)\]", msg)
                if m and int(m.group(1)) < len(wanted):
                    wanted.pop(int(m.group(1)))
                    continue
                raise
        return {}, wanted

    def diagnose(self):
        """When the token is refused: say which kind of token it is and what to do, in plain words."""
        out = {}
        try:
            r = requests.get(f"{self.base}/{self.version}/me", params={"fields": "id,username", "access_token": self.token}, timeout=30).json()
            out["instagram_login"] = "ok" if "error" not in r else r["error"].get("message", "")[:160]
        except Exception as e:
            out["instagram_login"] = str(e)[:160]
        try:
            r = requests.get(f"https://graph.facebook.com/{self.version}/me", params={"fields": "id,name", "access_token": self.token}, timeout=30).json()
            out["facebook_login"] = "ok" if "error" not in r else r["error"].get("message", "")[:160]
        except Exception as e:
            out["facebook_login"] = str(e)[:160]
        app_id, app_secret = secret("META_APP_ID"), secret("META_APP_SECRET")
        if app_id and app_secret:
            try:
                r = requests.get(f"https://graph.facebook.com/{self.version}/debug_token",
                                 params={"input_token": self.token, "access_token": f"{app_id}|{app_secret}"}, timeout=30).json()
                d = r.get("data", {})
                if d:
                    import datetime as dt
                    exp = d.get("expires_at")
                    out["token_check"] = {"valid": d.get("is_valid"), "type": d.get("type"), "app_id": str(d.get("app_id")),
                                          "expires": dt.datetime.utcfromtimestamp(exp).strftime("%d %b %Y") if exp else "never",
                                          "scopes": d.get("scopes", []), "error": (d.get("error") or {}).get("message")}
                else:
                    out["token_check"] = r.get("error", {}).get("message", str(r))[:160]
            except Exception as e:
                out["token_check"] = str(e)[:160]
        if "api access blocked" in str(out.get("facebook_login", "")).lower() or "api access blocked" in str(out.get("token_check", "")).lower():
            out["verdict"] = ("Meta has blocked this app's API access (the app, not the token). Open developers.facebook.com > My Apps > the app "
                              "and follow the banner at the top (often the yearly Data Use Checkup). No new token is needed after that.")
        elif out.get("facebook_login") == "ok" and out.get("instagram_login") != "ok":
            out["verdict"] = ("This is a Facebook-side token (it works, and it never expires). The Engine now uses it through Facebook's door. "
                              "For stats it also needs the permission instagram_manage_insights; add it when you regenerate the token.")
        elif isinstance(out.get("token_check"), dict) and out["token_check"].get("valid") is False:
            out["verdict"] = "The token has expired or was revoked. Generate a new one and update the secret IG_ACCESS_TOKEN."
        elif ("Cannot parse" in str(out.get("instagram_login", "")) or "Invalid OAuth" in str(out.get("instagram_login", ""))) and \
                ("Cannot parse" in str(out.get("facebook_login", "")) or "Invalid OAuth" in str(out.get("facebook_login", ""))):
            out["verdict"] = ("Instagram cannot read this token at all. Most likely it was copied incompletely or it is not an Instagram token. "
                              "Generate a fresh token for @inikki_reels and paste the whole thing into the secret IG_ACCESS_TOKEN.")
        elif "expired" in str(out.get("facebook_login", "")).lower() or "session" in str(out.get("facebook_login", "")).lower():
            out["verdict"] = ("The token has expired (it was a short-lived token). Make a System User token that never expires: "
                              "Meta Business Settings > System users > Generate new token, then update the secret IG_ACCESS_TOKEN.")
        else:
            out["verdict"] = "The token was refused. Generate a fresh one and update the secret IG_ACCESS_TOKEN."
        return out

    # ------------------------------------------------------------------ publishing (resumable upload: no public link needed)
    def post(self, path, **params):
        params["access_token"] = self.token
        r = requests.post(f"{self.base}/{self.version}/{path.lstrip('/')}", data=params, timeout=120)
        try:
            j = r.json()
        except ValueError:
            j = {"error": {"message": r.text[:200]}}
        if not r.ok or "error" in j:
            raise InstagramError(plain_error(j))
        return j

    def token_scopes(self):
        chk = self.diagnose().get("token_check")
        return (chk.get("scopes") or []) if isinstance(chk, dict) else []

    def create_reel(self, video_path, caption, thumb_offset_ms=None, share_to_feed=True, trial=None):
        """Make an unpublished reel container and upload the video into it. Nothing is visible until publish()."""
        params = {"media_type": "REELS", "upload_type": "resumable", "caption": caption, "share_to_feed": "true" if share_to_feed else "false"}
        if thumb_offset_ms is not None:
            params["thumb_offset"] = str(int(thumb_offset_ms))
        if trial:     # Trial Reels: shown to non-followers first (AGENT.md 7)
            params["trial_params"] = json.dumps({"graduation_strategy": trial if isinstance(trial, str) else "SS_PERFORMANCE"})
        j = self.post(f"{self.user_id}/media", **params)
        cid = j["id"]
        uri = j.get("uri") or f"https://rupload.facebook.com/ig-api-upload/{self.version}/{cid}"
        size = os.path.getsize(video_path)
        with open(video_path, "rb") as f:
            r = requests.post(uri, headers={"Authorization": f"OAuth {self.token}", "offset": "0", "file_size": str(size)}, data=f, timeout=900)
        if not r.ok:
            raise InstagramError(f"The video upload to Instagram failed: {r.text[:200]}")
        return cid

    def wait_ready(self, cid, timeout=900):
        t0, last = time.time(), None
        while time.time() - t0 < timeout:
            j = self.get(cid, fields="status_code,status")
            last = j
            if j.get("status_code") == "FINISHED":
                return j
            if j.get("status_code") in ("ERROR", "EXPIRED"):
                raise InstagramError(f"Instagram could not process the video ({j.get('status') or j.get('status_code')}).")
            time.sleep(8)
        raise InstagramError(f"Instagram was still processing the video after {timeout // 60} minutes ({last}).")

    def copyright_status(self, cid):
        """Instagram's own music and copyright check on the container, before anything is published (the mute guard)."""
        try:
            return self.get(cid, fields="copyright_check_status").get("copyright_check_status")
        except InstagramError:
            return None

    def publish(self, cid):
        j = self.post(f"{self.user_id}/media_publish", creation_id=cid)
        mid = j["id"]
        try:
            info = self.get(mid, fields="permalink,shortcode,timestamp")
        except InstagramError:
            info = {}
        return mid, info

    def comment(self, media_id, text):
        return self.post(f"{media_id}/comments", message=text)

    def publishing_quota(self):
        try:
            j = self.get(f"{self.user_id}/content_publishing_limit", fields="quota_usage,config")
            d = (j.get("data") or [{}])[0]
            return d.get("quota_usage"), (d.get("config") or {}).get("quota_total")
        except InstagramError:
            return None, None

    def account_insights(self):
        j = self.get(f"{self.user_id}/insights", metric="reach,views", period="day", metric_type="total_value")
        return {d["name"]: d.get("total_value", {}).get("value") for d in j.get("data", [])}
