# CLAUDE.md — iNiKKi Reels Workshop

Save this file as `CLAUDE.md` at the root of the `inikki-reels` GitHub repository.

---

## What this repo is
The engine for @inikki_reels, a self-running Tamil cinema Instagram page. The full design is `docs/MASTER_SPEC.md`. Read it before any change. If this file and the spec disagree, the spec wins.

## The two roles in this repo
- **Brain** (Claude scheduled tasks): writes only text and JSON in `plans/`, `state/`, `playbook/`, `lab/`, `series/`. It never calls OpenAI or Instagram, never holds keys, and never renders.
- **Muscle** (GitHub Actions + `engine/`): does everything mechanical. All keys come from GitHub Secrets.

Keep this split. If a Brain run needs something done, it writes a file and the Muscle acts on it.

## Folder rules
- `series/<id>/series.yaml` must match the schema in spec 6.1. Validate it in CI.
- `plans/YYYY-MM-DD/<reel_id>.json` must match spec 6.2. Validate it in CI and before rendering.
- No media in git. Images, clips, audio and video go to Google Drive via `engine/drive.py`.
- `tools/voice_tool.py` is Harish's tool. Call it, don't rewrite it.

## Building rules
1. **Plan first.** For any feature, write a short plan in the PR description: what changes, what could break, how it's tested.
2. **Test before live.** Every template change re-renders the 3 golden reels (`tests/golden/`) and compares frames. Every engine change runs a dry day (`make dry-day`) that renders into Drive `rehearsal/` and posts nothing.
3. **Code goes live only when all tests pass.** Scheduled Brain runs may open PRs for small fixes, but merge to `main` only when CI is green.
4. **Deterministic rendering.** The same plan gives the same reel. No randomness without a seed taken from `reel_id`.
5. **Cost guards in code, not in prompts.** `engine/budget.py` checks the OpenAI caps before every image call and logs real cost from the API response.
6. **Fail soft.** Every step has a fallback (spec sections 11 and 12). A failure holds one reel, never the whole day.
7. **Status always.** Every workflow ends by updating `status/` in Drive, even when it fails.

## Token thrift (Brain runs)
- Read only the `state/` files the run needs. Keep files small: summaries, not raw dumps.
- Pick clip moments from one contact-sheet image per trailer, never from frames one by one.
- Write reel plans in one pass using the series rules and the playbook. Revise only the 2 weakest virality factors, once.
- Weekly runs may use the most capable model. Daily runs use the faster model.

## Style for anything Harish reads
Plain words, short sentences, no jargon. He manages this from the Control Room chat, not from code.

## Commands (to be created in Phase 1)
- `make setup`: install Python and Node dependencies, fonts, ffmpeg
- `make smoke`: Drive, OpenAI, voice, clip fetch and Instagram smoke tests
- `make golden`: re-render the golden reels and compare them
- `make dry-day`: full day into `rehearsal/`, no posting
- `make render PLAN=plans/...json`: render one reel locally
