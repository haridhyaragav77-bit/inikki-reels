# iNiKKi Reels

A self-running Tamil cinema Instagram page (@inikki_reels).

**Running it day to day: `GUIDE.md`** (every control, loop and ready prompt, in plain language). The Control Room page: https://claude.ai/artifact/LiQvqiXriy9fZeWteZLWD6

**Changing it: start with `AGENT.md`.** It is the whole design in one file. Build sessions begin with the `workshop` skill.

- `runs/` — one card per thinking run · `control-room/` — the Control Room's instructions and page
- `config/` — global settings and the safety rules
- `team/` — one card per role
- `brands/inikki-reels/` — brand kit, colours, fonts, image styles
- `niches/tamil-cinema/` — niche profile, series, motion-graphics library, lineups, film bank, recommended-films log, sources, meme index
- `rules/` — the playbook the agent learns into, viral factors, notes for the older looks, change log
- `lab/` — ideas, pitches and pilot results for new series
- `plans/` — one small plan per reel, written by the Brain (the approved reference set is `plans/reference/`)
- `data/` — brief, metrics and feedback (text only)
- `engine/render/` and `templates/` — the reel maker: one plan file in, one finished, checked MP4 out (`templates/README.md`)
- `engine/`, `.github/workflows/` — the Engine (code): make, post, news watch, stats, brief, clean-up, health, dashboard, sync (AGENT.md 4.3)
- `.claude/skills/` — the saver skills the Brain uses
- `tools/` — the voice tool, the trailer helper, the Drive sign-in helper
- `archive/v1/` — the earlier design, kept for reference
