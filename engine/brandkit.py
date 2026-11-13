"""The brand kit the templates read: brand.yaml + brand_tokens.json merged into one dict (AGENT.md 11.1)."""
import os

from .settings import AGENT, ROOT, brand, brand_tokens


def kit(brand_id=None):
    bid = brand_id or AGENT["active"]["brand"]
    b = brand() if bid == AGENT["active"]["brand"] else __import__("yaml").safe_load(open(ROOT / "brands" / bid / "brand.yaml", encoding="utf-8"))
    try:
        tokens = brand_tokens()
    except FileNotFoundError:
        tokens = {}
    out = dict(b)
    out["id"] = bid
    out["tokens"] = tokens
    mascot = ROOT / "brands" / bid / str(b.get("mascot") or "")
    out["mascot_src"] = mascot.as_uri() if b.get("mascot") and mascot.exists() else None
    return out
