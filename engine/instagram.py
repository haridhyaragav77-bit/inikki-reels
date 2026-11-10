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

    def account_insights(self):
        j = self.get(f"{self.user_id}/insights", metric="reach,views", period="day", metric_type="total_value")
        return {d["name"]: d.get("total_value", {}).get("value") for d in j.get("data", [])}
