"""AI images from OpenAI (AGENT.md 5.3, archive 11.2). No text inside images; templates add all text."""
import base64
import os

from .settings import ENGINE, OUT, load_yaml, AGENT, secret
from .budget import Budget, BudgetStop

NO_TEXT = ("No text, no letters, no numbers, no logos, no watermarks anywhere in the image. "
           "Vertical portrait composition with clear space at the top and bottom.")


class ImageError(Exception):
    pass


def styles():
    return load_yaml(f"brands/{AGENT['active']['brand']}/image_styles.yaml")


def build_prompt(subject, style_key=None):
    s = styles().get(style_key or "", {})
    parts = [subject]
    if s.get("look"):
        parts.append(s["look"])
    if s.get("people"):
        parts.append("People: " + s["people"])
    if s.get("layering_hint"):
        parts.append(s["layering_hint"])
    parts.append(NO_TEXT)
    return ". ".join(p.strip().rstrip(".") for p in parts) + "."


def estimate_usd(model, quality):
    return float(ENGINE["openai"]["price_usd_per_image"].get(model, {}).get(quality, 0.07))


def cost_from_usage(model, usage, quality):
    """Real cost from the API's token usage when it reports it, else the flat per-image price."""
    if not usage:
        return estimate_usd(model, quality), None
    p = ENGINE["openai"]["price_usd_per_m_tokens"].get(model)
    if not p:
        return estimate_usd(model, quality), usage
    det = usage.get("input_tokens_details") or {}
    text_in = det.get("text_tokens", usage.get("input_tokens", 0))
    image_in = det.get("image_tokens", 0)
    out = usage.get("output_tokens", 0)
    usd = (text_in * p["text_in"] + image_in * p["image_in"] + out * p["image_out"]) / 1e6
    return round(usd, 5), usage


def generate(subject, style_key=None, quality=None, purpose="reel", reel_id=None, out_path=None, budget=None, drive=None, model=None):
    """Make one image. Returns a dict with ok, path, model, cost. Raises nothing: failures come back as ok=False."""
    key = secret("OPENAI_API_KEY")
    if not key:
        return {"ok": False, "error": "Missing secret OPENAI_API_KEY"}
    try:
        from openai import OpenAI
    except ImportError:
        return {"ok": False, "error": "openai library not installed"}
    cfg = ENGINE["openai"]
    quality = quality or cfg["image_quality"]
    budget = budget or Budget(drive)
    prompt = build_prompt(subject, style_key)
    out_path = out_path or str(OUT / "images" / f"{reel_id or 'image'}.png")
    client = OpenAI(api_key=key)
    errors = []
    for model in ([model] if model else []) + [m for m in cfg["image_models"] if m != model]:
        try:
            budget.check(estimate_usd(model, quality))
        except BudgetStop as e:
            return {"ok": False, "error": str(e), "budget": budget.summary()}
        try:
            r = client.images.generate(model=model, prompt=prompt, size=cfg["image_size"], quality=quality, n=1)
        except Exception as e:  # model missing, refusal, network: try the next model
            errors.append(f"{model}: {str(e)[:200]}")
            continue
        data = r.data[0]
        if getattr(data, "b64_json", None):
            raw = base64.b64decode(data.b64_json)
        elif getattr(data, "url", None):
            import requests
            raw = requests.get(data.url, timeout=60).content
        else:
            errors.append(f"{model}: no image in the reply")
            continue
        os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
        with open(out_path, "wb") as f:
            f.write(raw)
        usage = r.usage.model_dump() if getattr(r, "usage", None) else None
        usd, usage = cost_from_usage(model, usage, quality)
        inr = budget.record(model, quality, usd, purpose, reel_id, usage)
        return {"ok": True, "path": out_path, "model": model, "quality": quality, "cost_usd": usd, "cost_inr": inr,
                "bytes": len(raw), "budget": budget.summary(), "prompt": prompt}
    return {"ok": False, "error": "No image model worked: " + " | ".join(errors)}
