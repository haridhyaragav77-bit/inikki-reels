"""Instagram API with Instagram Login (archive 14). Phase 1 only reads; posting comes in Phase 3."""
import re

import requests

from .settings import ENGINE, secret


class InstagramError(Exception):
    pass


def plain_error(j):
    e = (j or {}).get("error", {}) if isinstance(j, dict) else {}
    msg = e.get("message", str(j)[:200])
    code = e.get("code")
    if code == 190 or "access token" in msg.lower() and ("expired" in msg.lower() or "invalid" in msg.lower()):
        return "The Instagram token has expired or is not valid. Make a new long-lived token and update the secret IG_ACCESS_TOKEN."
    if code == 10 or "permission" in msg.lower():
        return f"The Instagram token is missing a permission: {msg}"
    return msg


class Instagram:
    def __init__(self):
        self.token = secret("IG_ACCESS_TOKEN")
        self.user_id = secret("IG_USER_ID")
        if not self.token or not self.user_id:
            raise InstagramError("Missing secret " + ", ".join(n for n in ["IG_ACCESS_TOKEN", "IG_USER_ID"] if not secret(n)))
        self.base = ENGINE["instagram"]["base"]
        self.versions = list(ENGINE["instagram"]["api_versions"])
        self.version = self.versions[0]

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
        if out.get("facebook_login") == "ok" and out.get("instagram_login") != "ok":
            out["verdict"] = ("This is a Facebook-login token, but the Engine uses 'Instagram API with Instagram Login'. "
                              "Make the token from the Instagram login side of the Meta app (API setup with Instagram login > Generate token).")
        elif isinstance(out.get("token_check"), dict) and out["token_check"].get("valid") is False:
            out["verdict"] = "The token has expired or was revoked. Generate a new one and update the secret IG_ACCESS_TOKEN."
        elif "Cannot parse" in str(out.get("instagram_login", "")) or "Invalid OAuth" in str(out.get("instagram_login", "")):
            out["verdict"] = ("Instagram cannot read this token at all. Most likely it was copied incompletely or it is not an Instagram token. "
                              "Generate a fresh token for @inikki_reels and paste the whole thing into the secret IG_ACCESS_TOKEN.")
        else:
            out["verdict"] = "The token was refused. Generate a fresh one and update the secret IG_ACCESS_TOKEN."
        return out

    def account_insights(self):
        j = self.get(f"{self.user_id}/insights", metric="reach,views", period="day", metric_type="total_value")
        return {d["name"]: d.get("total_value", {}).get("value") for d in j.get("data", [])}
