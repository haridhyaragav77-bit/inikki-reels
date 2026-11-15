"""Masking (AGENT.md 21): keys, key-shaped strings and email addresses are taken out of every line the Engine prints
(job logs are public) and of everything it saves. Switched on when the Engine starts (engine/__init__.py).
The rest of the Guard is engine/guard.py."""
import json
import os
import re
import sys

from .settings import OPTIONAL_SECRETS, SECRET_NAMES

HIDDEN = "[hidden]"
# Real keys (a copy in public means: replace it). Account ids and folder ids are not keys and are not searched for.
KEY_NAMES = ["OPENAI_API_KEY", "IG_ACCESS_TOKEN", "META_APP_SECRET", "GDRIVE_SERVICE_ACCOUNT_JSON", "GDRIVE_OAUTH_REFRESH_TOKEN",
             "BRAIN_FIRE_URL", "BRAIN_FIRE_TOKEN", "PEXELS_API_KEY", "PIXABAY_API_KEY", "ELEVENLABS_API_KEY", "GITHUB_TOKEN", "GH_TOKEN"]
INNER = ("private_key", "private_key_id", "client_secret", "refresh_token")
PATTERNS = [
    ("an OpenAI key", r"\bsk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{32,}"),
    ("an ElevenLabs key", r"\bsk_[a-f0-9]{40,}\b"),
    ("a Google key", r"\bAIza[0-9A-Za-z_-]{35}\b"),
    ("a Google sign-in secret", r"\bGOCSPX-[A-Za-z0-9_-]{20,}"),
    ("a Google sign-in token", r"\b1//[0-9A-Za-z_-]{40,}"),
    ("a Google access token", r"\bya29\.[A-Za-z0-9_-]{30,}"),
    ("a private key", r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    ("a GitHub token", r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{40,})"),
    ("a Meta token", r"\b(?:EAA|IGQ|IGA)[A-Za-z0-9_-]{60,}"),
    ("a Slack token", r"\bxox[baprs]-[A-Za-z0-9-]{20,}"),
    ("a Claude key", r"\bsk-ant-[A-Za-z0-9_-]{30,}"),
]
_PAT = [(n, re.compile(p)) for n, p in PATTERNS]
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_EMAIL_OK = ("noreply.github.com", "noreply@github.com", "noreply@anthropic.com", "example.com")
_needles = None


def needles():
    """The exact key values this run holds (from the environment only), longest first. Never printed, never saved."""
    global _needles
    if _needles is not None:
        return _needles
    out = set()
    for name in dict.fromkeys(KEY_NAMES + [n for n in SECRET_NAMES + OPTIONAL_SECRETS if n.endswith(("_KEY", "_TOKEN", "_SECRET"))]):
        v = (os.environ.get(name) or "").strip()
        if len(v) < 12:
            continue
        out.add(v)
        try:
            m = re.search(r"\{.*\}", v, re.S)
            d = json.loads(m.group(0)) if m else {}
        except ValueError:
            d = {}
        for k in INNER:
            if isinstance(d.get(k), str):
                out.add(d[k])
                out.add(d[k].replace("\n", "\\n"))
        for piece in list(out):
            out.update(line for line in piece.splitlines() if len(line) >= 24 and not line.startswith("-----"))
    _needles = sorted((n for n in out if len(n) >= 12), key=len, reverse=True)
    return _needles


def redact(text, emails=True):
    """The same text with every key, key-shaped string and email address masked."""
    if not isinstance(text, str) or not text:
        return text
    for n in needles():
        if n in text:
            text = text.replace(n, HIDDEN)
    for _, rx in _PAT:
        text = rx.sub(HIDDEN, text)
    if emails and "@" in text:
        text = _EMAIL.sub(lambda m: m.group(0) if m.group(0).lower().endswith(_EMAIL_OK) else "[email hidden]", text)
    return text


def clean(obj, emails=False):
    """redact() for anything that is about to be saved as JSON. Drive status files are private, so emails stay by default."""
    if isinstance(obj, str):
        return redact(obj, emails)
    if isinstance(obj, dict):
        return {k: clean(v, emails) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v, emails) for v in obj]
    return obj


class _Masked:
    """Stands in for stdout/stderr: everything the Engine prints goes through redact() first (job logs are public)."""
    def __init__(self, stream):
        self._s = stream

    def write(self, text):
        try:
            text = redact(text)
        except Exception:
            pass
        return self._s.write(text)

    def __getattr__(self, name):
        return getattr(self._s, name)


def install():
    """Called once when the Engine starts (engine/__init__.py)."""
    for name in ("stdout", "stderr"):
        s = getattr(sys, name)
        if s is not None and not isinstance(s, _Masked):
            setattr(sys, name, _Masked(s))
