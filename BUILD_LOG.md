# Build log (plain words, newest first)

The design is AGENT.md. This file only says where the build stands, so a new Workshop session can pick up without re-reading everything.

## 11 Nov 2026 — Phase 1 done (smoke tests), Phase 2 next
Smoke workflow: `.github/workflows/smoke.yml` (manual run, nothing is posted). Last run: 6 of 9 pass.

| Check | Result | Note |
| --- | --- | --- |
| Keys in GitHub | OK | all 7 present; the Engine trims stray spaces and line breaks |
| Drive read | OK | robot account `inikki-bot@…` reads the folder; music folder is named "background music (1)" (581 tracks) and is found by alias |
| Drive write | partly | can update existing status files; cannot create new files (service accounts have no storage). Fix: `tools/drive_signin.py` → secret `GDRIVE_OAUTH_REFRESH_TOKEN` (waiting on Harish) |
| Dashboard sheet | OK | created by Harish's account in the root; 7 tabs; the Engine writes to it |
| Voice from the cloud | OK | edge-tts works on the GitHub runner, so no laptop voice sessions are needed |
| One OpenAI image | OK | gpt-image-1-mini, low quality, ₹0.31; budget counter works |
| Trailer clip from YouTube | blocked | runner is bot-blocked; design fallback = Drive clip-library/, fed from Harish's laptop (helper to build in Phase 2) or by hand |
| Instagram read | OK, stats pending | token is a Facebook-side system-user token (never expires); Engine supports both routes. Stats need the permission `instagram_manage_insights` (waiting on Harish) |

Drive seeds made by hand (owned by Harish): `rehearsal/`, `iNiKKi Dashboard`, `status/{smoke,budget,alerts}.json`, `control/switch.json`.
Folders `control, status, work, finished, clip-library, image-library, inspiration, manual-post, requests` were created by the robot account on the first run.

Open items for Harish: Drive sign-in (A), token permission (B), clips decision (C). Details in Drive `rehearsal/Phase 1 report`.

## 10 Nov 2026 — Step 0 done
Files from AGENT.md 14.2 unpacked with Blocks C, E, F, G. Existing starter content reused as is.
