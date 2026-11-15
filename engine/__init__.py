"""iNiKKi Reels Engine: the mechanical half of the agent (AGENT.md section 4).
Runs on GitHub Actions with keys from GitHub Secrets. The Brain never imports this."""

from . import mask as _mask

_mask.install()          # job logs are public: every printed line has keys and emails masked first (AGENT.md 21)
