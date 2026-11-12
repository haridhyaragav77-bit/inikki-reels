"""What Harish sets from the Control Room (AGENT.md 12, 16.3): master switch, setting changes, one-off commands, feedback.
They live in Drive control/. Every job reads them first (CLAUDE.md rule 6). The repository files are the defaults;
control/overrides.yaml wins over them."""
import copy
import json

import yaml

from .settings import AGENT, load_yaml


def deep_merge(base, extra):
    out = copy.deepcopy(base)
    for k, v in (extra or {}).items():
        out[k] = deep_merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


class Control:
    def __init__(self, drive=None):
        self.drive = drive
        self.switch = self._json("switch.json") or {"mode": AGENT.get("switch", "run")}
        self.overrides = self._yaml("overrides.yaml") or {}
        self.settings = deep_merge(AGENT, self.overrides.get("settings", {}))

    def _text(self, name):
        if not self.drive:
            return None
        try:
            return self.drive.read_text("control", name)
        except Exception:
            return None

    def _json(self, name):
        t = self._text(name)
        try:
            return json.loads(t) if t else None
        except ValueError:
            return None

    def _yaml(self, name):
        t = self._text(name)
        try:
            return yaml.safe_load(t) if t else None
        except yaml.YAMLError:
            return None

    def lines(self, name):
        """control/commands.jsonl, control/feedback.jsonl: one JSON object per line."""
        out = []
        for line in (self._text(name) or "").splitlines():
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except ValueError:
                    pass
        return out

    @property
    def mode(self):
        return str(self.switch.get("mode", "run")).lower()

    @property
    def phase(self):
        return str(self.settings.get("phase", "rehearsal")).lower()

    @property
    def can_post(self):
        """Posting happens only when the page is live AND the master switch says Run (AGENT.md 12.1)."""
        return self.phase == "live" and self.mode == "run"

    def series_paused(self, series_id):
        s = (self.overrides.get("series") or {}).get(series_id) or {}
        return bool(s.get("paused"))

    def series(self, series_id, niche_dir):
        """A series card with any Control Room changes applied."""
        p = niche_dir / "series" / series_id / "series.yaml"
        base = yaml.safe_load(p.read_text(encoding="utf-8")) if p.exists() else {}
        return deep_merge(base, (self.overrides.get("series") or {}).get(series_id) or {})
