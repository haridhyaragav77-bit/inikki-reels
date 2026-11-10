"""Settings and secrets. Everything configurable is read from files; keys only from the environment."""
import os
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"

SECRET_NAMES = [
    "OPENAI_API_KEY", "IG_USER_ID", "IG_ACCESS_TOKEN", "META_APP_ID", "META_APP_SECRET",
    "GDRIVE_ROOT_FOLDER_ID", "GDRIVE_SERVICE_ACCOUNT_JSON",
]
OPTIONAL_SECRETS = ["GDRIVE_OAUTH_REFRESH_TOKEN", "BRAIN_FIRE_URL", "BRAIN_FIRE_TOKEN"]


def load_yaml(rel):
    with open(ROOT / rel, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


AGENT = load_yaml("config/agent.yaml")
ENGINE = load_yaml("config/engine.yaml")


def brand():
    return load_yaml(f"brands/{AGENT['active']['brand']}/brand.yaml")


def brand_tokens():
    import json
    with open(ROOT / f"brands/{AGENT['active']['brand']}/brand_tokens.json", encoding="utf-8") as f:
        return json.load(f)


def niche():
    return load_yaml(f"niches/{AGENT['active']['niche']}/niche.yaml")


def niche_dir():
    return ROOT / "niches" / AGENT["active"]["niche"]


def secret(name):
    v = os.environ.get(name, "").strip()
    return v or None


def missing_secrets(names=None):
    return [n for n in (names or SECRET_NAMES) if not secret(n)]


def github_step_summary(text):
    """Append to the GitHub Actions job summary when running there."""
    p = os.environ.get("GITHUB_STEP_SUMMARY")
    if p:
        with open(p, "a", encoding="utf-8") as f:
            f.write(text + "\n")
