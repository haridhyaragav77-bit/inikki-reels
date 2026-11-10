# iNiKKi Reels — Kickstart Pack (start here)

This folder holds everything needed to build the self-running iNiKKi Reels system. Follow the 5 steps in order.

## What's inside

| File | What it is | What you do with it |
| --- | --- | --- |
| `00_MASTER_SPEC.md` | The full design: series, loops, trend radar, virality engine, Series Lab, templates, budget, guardrails, scenarios, build phases | Goes into the repo and the Control Room. This is the file Claude builds from. |
| `01_CONTROL_ROOM_PROJECT_INSTRUCTIONS.md` | Instructions for the Control Room chat | Copy the box into a new Claude Project's Instructions |
| `02_WORKSHOP_CLAUDE.md` | The rulebook for the code workspace | Becomes `CLAUDE.md` in the repo |
| `03_KICKOFF_PROMPT.md` | Part A starts the build. Part B holds the 6 prompts for the daily runs. | Paste Part A into a new Claude Code session |
| `04_ACCOUNTS_CHECKLIST.md` | Accounts and keys to set up | Tick through it first |
| `05_CARD_LIBRARY.md` | Every Control Room card and its buttons | Upload to the Control Room project |
| `series/` | 7 series, ready to plug in | Into the repo |
| `design/` | Brand colours, fonts, image styles, pronunciation list | Into the repo |
| `memes/` | Index of your 50 memes and 40 recordings, with duplicates and clean-up flagged | Into the repo |
| `state/` | Starter film bank (32 films) and the trusted-sources template | Into the repo. Fill in `sources.yaml`. |
| `playbook/`, `lab/` | Starting rules from your samples, and seed ideas for new series | Into the repo |
| `tools/` | Your voice tool, unchanged | Into the repo |

## The 5 steps

1. **Accounts (about 1–2 hours):** work through `04_ACCOUNTS_CHECKLIST.md`. Upload your sample reels to Drive `iNiKKi Reels/reference-reels/`, and your memes and recordings to `iNiKKi Reels/meme-bank/`.
2. **Repo:** create the private GitHub repo `inikki-reels` and upload this whole folder into it.
3. **Build:** open claude.ai/code, pick the repo, choose the most capable model you have, and paste **Part A** of `03_KICKOFF_PROMPT.md`. Claude works phase by phase and stops after each one to show you results.
4. **Control Room:** create a Claude Project "iNiKKi Reels — Control Room". Paste the box from `01_CONTROL_ROOM_PROJECT_INSTRUCTIONS.md` into Instructions, and upload `00_MASTER_SPEC.md`, `05_CARD_LIBRARY.md`, `design/brand_tokens.json` and `memes/meme_index.csv`. Say "hi".
5. **Go live:** after the 3-day rehearsal passes, the build turns on posting: 3 a day for the first week, then the full 6.

## The first thing to watch for
In Phase 1, the build tests whether your voice tool works from the cloud.
- **If it works:** there's no evening laptop session at all, and updates are voiced the same morning.
- **If not:** you spend about 15 minutes on your laptop at 8 PM, and the Control Room's Voice Session card guides you.
