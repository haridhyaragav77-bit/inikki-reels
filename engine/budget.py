"""Image budget: a hard stop in code (AGENT.md 15.3, safety rule 7).
Truth lives in Drive status/budget.json; a local copy is kept in out/ for the run artifact."""
import datetime as dt

from .settings import AGENT, ENGINE
from . import status


class BudgetStop(Exception):
    pass


class Budget:
    def __init__(self, drive=None):
        self.drive = drive
        self.cap_inr = float(AGENT["budgets"]["images_inr_month"])
        self.rate = float(ENGINE["openai"]["usd_to_inr"])
        self.month = status.now().strftime("%Y-%m")
        data = None
        if drive:
            try:
                data = drive.read_json("status", "budget.json")
            except Exception:
                data = None
        if not data or data.get("month") != self.month:
            data = {"month": self.month, "images": 0, "usd": 0.0, "inr": 0.0, "entries": []}
        self.data = data

    @property
    def spent_inr(self):
        return round(float(self.data["inr"]), 2)

    @property
    def pct(self):
        return round(100 * self.spent_inr / self.cap_inr, 1) if self.cap_inr else 0

    def mode(self):
        """normal | save (80%: reuse the library, fewer Guess days) | stop (100%: no new images)"""
        if self.pct >= 100:
            return "stop"
        if self.pct >= 80:
            return "save"
        return "normal"

    def check(self, est_usd):
        est_inr = est_usd * self.rate
        if self.spent_inr + est_inr > self.cap_inr:
            raise BudgetStop(f"Image budget: ₹{self.spent_inr:.0f} of ₹{self.cap_inr:.0f} used this month; "
                             f"this image (≈₹{est_inr:.1f}) would go over the cap. No new images until the 1st.")
        return est_inr

    def record(self, model, quality, cost_usd, purpose, reel_id=None, usage=None):
        inr = round(cost_usd * self.rate, 3)
        self.data["images"] += 1
        self.data["usd"] = round(self.data["usd"] + cost_usd, 5)
        self.data["inr"] = round(self.data["inr"] + inr, 3)
        self.data["entries"] = ([{"at": status.stamp(), "model": model, "quality": quality, "usd": round(cost_usd, 5),
                                  "inr": inr, "purpose": purpose, "reel_id": reel_id, "usage": usage}]
                                + self.data["entries"])[:400]
        self.save()
        return inr

    def summary(self):
        return {"month": self.month, "images": self.data["images"], "spent_inr": self.spent_inr, "cap_inr": self.cap_inr,
                "pct": self.pct, "mode": self.mode()}

    def save(self):
        obj = dict(self.data)
        obj.update(self.summary())
        status.write(self.drive, "budget.json", obj)
