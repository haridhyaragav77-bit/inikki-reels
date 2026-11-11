# Build log (plain words, newest first)

The design is AGENT.md. This file only says where the build stands, so a new Workshop session can pick up without re-reading everything.

## 11 Nov 2026 — Phase 2: templates, motion graphics, golden reels
Work continues on branch `claude/gallant-dijkstra-6madni` (the earlier branch was fast-forwarded into it).

**Phase 1 is closed.** Smoke run: 8 of 9 pass, 1 on the planned fallback (YouTube is blocked from GitHub's computers; clips come from Drive `clip-library/`).
Open items A and B are done: the Drive sign-in works (files are created as Harish), and the Instagram token now reads reel stats
(views, reach, likes, comments, shares, saves, reposts, watch time). Item C (clips) has its helper: `tools/clip_helper.py`.

**Design change from Harish (in AGENT.md 5.7, then built):**
1. Every screen's motion graphic must show what the voice is saying. Decoration is not allowed.
2. Every spoken line is on screen twice: Tanglish (English letters) and Tamil script. Words light up as they are spoken.
The library and when to use each graphic: `rules/motion.md`. The plan check refuses plans that break either rule.

**Built**
| Piece | Where | Note |
| --- | --- | --- |
| Card template | `templates/card/` | 15 motion graphics (`motion.js`), two-line subtitles with word highlight, single / stacked / split pictures |
| Cinematic template | `templates/cinematic/` | story beats in type: slam, count, stamp, underline, question; pictures move with depth |
| Diorama template | `templates/diorama/` | Guess the Movie: title, 3 clues, countdown ring, reveal; depth scenes with fog, dust, light |
| Depth scenes | `templates/common/scene.js`, `engine/depth.py` | free depth model on the runner splits a picture into far / middle / near |
| Renderer | `engine/render.py` | plan → pictures, voice, timings → frames by headless Chromium → ffmpeg. Voice length sets screen length |
| Sound | `engine/audio.py` | music bed, voice on top, music drops under the voice, small sounds land with each move, levelled to -14 LUFS |
| Inspection | `engine/qc.py` | size, format, blank frames, loudness, voice in step, text fit, safe zones, stand-in pictures |
| Plan check | `engine/plancheck.py` | the rules as code; `--selftest` keeps template, plan form and rulebook in agreement |
| Same plan, same picture | `engine/golden.py` | draws each golden plan twice and compares exactly |
| Plan forms | `templates/<name>/plan_form.json` | what the Brain fills in |
| Golden plans | `plans/reference/` | Kaithi breakdown, Second Tier story, Kaithi Guess the Movie |
| Workflows | `.github/workflows/render.yml`, `peek.yml` | render: plans → Drive `rehearsal/`; peek: build-time look into Drive (delete after the build, with the `peek` branch) |

**How to re-render the golden reels:** Actions → render → Run workflow (defaults are the three golden plans, into Drive `rehearsal/phase2-golden/`).
A push that touches `templates/` or the renderer runs a free stand-in test first (no AI images, nothing spent).

**Known limits, written down so nobody is surprised**
- Word highlight timing is estimated from word length, not measured from the voice. It is close; exact timing needs the voice service's word marks (later).
- Music is matched by words in the file name until the music index exists (Phase 3). The golden plans pin their tracks.
- The Kaithi golden reel cuts its film moments from Harish's own reference reel, because `clip-library/` is empty. Real reels need trailers there.
- Not built yet (Phase 3): posting, measuring, brief, watcher, clean-up, health, dashboard job, duplicate check against posted reels.

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
