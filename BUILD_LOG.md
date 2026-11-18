# Build log (plain words, newest first)

The design is AGENT.md. This file only says where the build stands, so a new Workshop session can pick up without re-reading everything.

## 18 Nov 2026 — Dependabot allowed to start jobs; Drive sign-in expired
GitHub's own package checker (`dependabot[bot]`) started a job on 16 Nov, which the daily look-around counts as a stranger and holds posting. It is now in `guard.trusted_actors` (it gets none of our keys). Separately, every job from 17 Nov fails because the Drive sign-in (`GDRIVE_OAUTH_REFRESH_TOKEN`) expired: the Google app was still in Testing (7-day limit). Harish publishes the app and makes a new sign-in (AGENT.md 19.2). The Engine now signs its saves with GitHub's own bot address, so a stranger's account named "engine" no longer shows as a contributor.

## 16 Nov 2026 — Public: minutes are free, and everything says so
The repository went public on 16 Nov (old logs, saved files and the Gmail in history were cleared first). The health job already lifts the slow-down; now the brief tells the Brain there is no minute limit (plan the full day, reserves included), and the panel and the page's Usage card show "no limit" instead of "of 2,000". `engine/brief.py`, `engine/panel.py`, `control-room/page.template.html`. Reserves were set back to 2 a day through the Control Room inbox at Harish's request.

## 16 Nov 2026 — Weekend check and weekly fresh chats
Weekend: every Plan (14, 15, 16 Nov), Refresh (14, 15) and the Weekly run (15) started on time; the catch-up checks found nothing missed.
Found: the dispatcher's check pulled into a local branch, a git hook then complained at every tick and the chat argued back;
by Monday each tick re-read about 285,000 tokens. Fixed: the check reads main without a branch and ignores git warnings,
and `runs/renew.md` replaces the clock and dispatcher with fresh chats every Monday 03:17 IST (rules in `runs/renew/`).

## 15 Nov 2026 — Ready to go public: audit and the Guard
Harish asked to make the repository public (free runner minutes) with security designed in. Design: AGENT.md 21.

**Audit (every branch, full history):** no key anywhere; Drive folders shared only with Harish and the robot account; no job runs for a stranger. Found and fixed: the smoke test printed the Drive sign-in email into job logs (old logs must be deleted before the switch); an error message showed the first 4 characters of a secret; typed job inputs were pasted into commands; actions were not fixed to exact versions; finished reels were kept with public runs; preview branches were never deleted.

| Piece | Where | In one line |
| --- | --- | --- |
| Masking | `engine/mask.py`, on from `engine/__init__.py` | Keys, key-shaped strings and emails become `[hidden]` in everything printed or saved |
| Key check | `engine/guard.py` `scan` / `staged` / `preview`, `.github/workflows/guard.yml` | Every push and pull request (no keys, read-only), every Engine commit, every preview branch, every Brain file |
| Only Harish's commands | `engine/relay.py`, `guard.trusted_people` | An inbox file from another account is refused, binned, and posting goes on hold |
| Daily look-around | `guard.watch` inside `engine/health.py` | Keys in files, Drive sharing (an open link is closed), who started jobs, posts not made by the Engine, voice credits; old preview branches deleted; Drive `status/security.json` |
| Job files | all of `.github/workflows/` | Exact action versions, inputs never inside a command, least permissions, reel copies only while private |
| Free minutes | `engine/health.py` | The health job sees the repository is public and stops the runner-minute slow-down |
| Tests | `python -m tests.test_guard` | 70 checks with made-up keys and a pretend Drive, including the job-file rules |

**Left for Harish (GitHub settings, AGENT.md 21.6):** secret scanning + push protection, outside-contributor approval, delete old job logs, Issues off, a spending limit at OpenAI, then flip to public. **Not done:** his Gmail is still in 7 early commits (needs a rewrite of `main`, only if he asks).
## 15 Nov 2026, night — Reserves control, clearer series names
Harish saw a reserve (Watch This Next, "Sudani from Nigeria") listed as an 8th reel and could not control reserves. Added Reserves Off/1/2/3 to Setup → Reels per day (`reserves.per_day`, default 2; the brief asks for that many, Make skips any extra). Every row now shows the full series name and a one-line promise (new `promise:` in each series file). The page also fills the day plan from its built-in copy when the status file is older.

## 15 Nov 2026, evening — Reels per day, per series (the day plan)
Harish asked to set how many reels each series posts a day, pick their times from a list, and switch the extras off, from Setup. Built: Setup → Reels per day (Off/1–4 buttons per series, a time list per reel, Extras On/Off and "up to N" per extra, a live total, one Save, one Undo). Engine: `engine/dayplan.py`, relay action `day_plan`, the plan run, Make and Post follow it (AGENT.md 12.3). Times are only the 8 that already have timers, so no new runner minutes. Tests: `tests/test_control_room.py` 2b. **To watch:** the first plan run after a Save lists the new counts.

## 15 Nov 2026, later — Moving work from GitHub to Claude: checked, not done
Harish asked to move part of the work to Claude near the limit. Checked: Claude already does the thinking and the clock; making and posting need keys and a strong machine; only about 4 minutes a day could move (two briefs, two flex-slot checks), for more Claude usage and a new way to fail. Decision and reasons are in AGENT.md 15.3. Nothing in the Engine changed. The weekly renewal of the clock and dispatcher chats is a separate task already set for 16 Nov.

## 15 Nov 2026 — Runner minutes: the same day for about half the minutes
Harish: 5 reels a day plus news and reviews inside 2,000 minutes, with no saver, no loss of quality, and reels must still post when Claude has no usage left.

Measured first (GitHub run history): a live day cost about 115 minutes. Posting was the biggest part: 20 Post runs for 8 reels (the clock and GitHub's late timer both run one per slot), most of them billed 2 to 4 minutes for doing nothing. Building used about three quarters of the month so far.

| Piece | Where | In one line |
| --- | --- | --- |
| Cheap empty Post runs | `engine/post.py` `watch_due`, `main` | No second news read within 50 minutes, no Drive writes when nothing changed |
| Late timer waits only when needed | `engine/post.py` `clock_alive`, `wait_for_slot`; Drive `status/clock.json` | Clock on time → the late run leaves a close slot to it; clock missing → waits and posts on time as before |
| Upload when made | `engine/post.py` `prepare`, `prep_usable`, `publish`; `engine/make.py` | Unpublished upload at Make; the slot's run publishes; any doubt → uploads then, as before |
| Quicker status step | `engine/panel.py` `Once` | Each Drive file read once, one listing per folder |
| Make is one job | `.github/workflows/make.yml`, `engine/make.py` `still_waiting` | The check is the first step, not a second billed job; a reel skipped to save minutes no longer starts the heavy tools on every run |
| Nightly not doubled | `.github/workflows/daily.yml`, `engine/status.py` `recent` | The late copy stops when the clock already ran it |
| Golden test once | `.github/workflows/make-reels.yml`, `engine/tools/pick_plans.py` | Branch only, and only the looks a push touched |
| Honest counter | `engine/health.py` | A day that cannot be counted is tried again, never saved as 0; month recounted |
| Tests | `tests/test_minutes.py` | 37 checks, no keys |

**Not changed:** encoder, frame rate, voice, music, slot times, the 3-hours-late rule, both timers.
**To watch:** the first live day's minutes on the Usage tab (expected about 60); the first "using the upload made ahead of the slot" line in a Post run.

## 14 Nov 2026, later — Control Room v2, ElevenLabs voice, unique designs, calendar, scouts
Harish asked for: a far better Control Room (series as a framework, easy small changes, add/test/train/retire a series, more switches, usage), ElevenLabs actually used, a stronger Watch This Next, unique breakdown designs, calendar awareness, the missed "Ohm" trailer fixed, and a simple outer loop with insights.

| Piece | Where | In one line |
| --- | --- | --- |
| ElevenLabs is the main voice | `engine/voice.py`, `engine/render/audio.py`, `config/engine.yaml` `voice` | ElevenLabs with word timings, Microsoft as the backup for the whole reel; one take per line, kept in Drive `work/voice-cache` and reused; credits read before each reel. Checked on GitHub: the key works (smoke test). |
| Series framework | `config/framework.yaml` | Every series is 7 blocks; the page's editor, the add-a-series questions and the relay's checks all come from this one file |
| Relay actions | `engine/relay.py`, `engine/control.py` | `series` (any framework field), `series_add` (a draft: watched, never posted), `series_remove`, `test`, `sample`, dotted `set` for switches; undo leaves nothing behind |
| Control Room page | `control-room/page.template.html`, `build.py` | Tabs Today · Next · Series · Insights · Usage · Setup · Guide; a series opens as its 7 blocks with Edit; sections reorder with ↑ ↓ ＋ ✕ |
| Test reels | `engine/make.py` `tests`, `engine/edits.py` | "Make a test reel" renders the series' reference plan into Drive `rehearsal/tests` and starts Make at once |
| New series become files | `engine/brief.py` `series_files`, `daily.yml` | A series added on the page is written to `niches/<niche>/series/<id>/series.yaml` by the next brief job and planned at its times |
| Usage | `engine/health.py`, `engine/panel.py` `usage` | Runner minutes with month-end forecast and stages (save → tight → last), voice credits, Claude's quiet times |
| Insights | `engine/insights.py` | No-AI findings and a "do next" list from the nightly numbers; in the page and in the weekly brief |
| News watch | `engine/watch.py`, `sources.yaml` `scouts` | Fast pages (@chennaiist) read through Instagram's API; a trailer is one story across sources and wakes the Breaking run with 2 trusted sources or a scout naming the official account; source study in `status/scouts.json` |
| Calendar | `engine/almanac.py`, `knowledge/calendar.yaml` | Day, mood, season, festivals, slot-hour words and title angles at the top of every brief |
| Watch This Next | `templates/poster-wall/template.js`, its series card `pace` | Centre-weighted hook frame with a moving poster wall and a timely kicker; a plot beat after each film card; faster pace enforced by the plan check from 15 Nov |
| Unique breakdowns | `templates/stage/template.js`, series cards `unique_design` | 7 design kits and 4 new graphics (timeline, meter, versus, web); the plan check refuses a repeated kit or build from 15 Nov |
| Fixed in passing | `.github/workflows/render.yml` | The render workflow could not make the approved looks (the drawing tools were not installed there) |
| Tests | `tests/test_control_room.py`, `test_voice.py`, `test_watch.py` | 41 + 10 + 8 checks, no keys needed |

**Checked on GitHub (14 Nov, branch run, nothing posted):** the Vikram Vedha breakdown and Watch This Next reference reels were made with the new code and passed every inspection (54 s and 33 s), into Drive `rehearsal/workshop-14nov`. ElevenLabs spoke the whole breakdown in one take: 325 credits for about 814 Tamil characters (about 0.42 credits a character), so a 1-minute breakdown costs about 325 credits. The news watch read @chennaiist through Instagram (12 posts). Health: every check green; 502 of 2,000 runner minutes used, heading for about 1,721 by month end.

**Changed after review:** a series added on the page starts as a **draft** (one reel every other day into Drive `rehearsal/drafts`, never posted), because "trial" already means posting to non-followers. Watch This Next films are 7.4 s at most including the plot beat (Harish's reading-pace rule of 13 Nov, a little faster per 14 Nov). The plan check and the voice read a series with the Control Room's changes (through the mirrored `data/control/overrides.yaml`).

**Not done / to watch:** a real ElevenLabs reel should be listened to once (speed 1.1, voice Ashwin; both are switches). The first plans under the new rules are written on 15 Nov: watch that morning's Plan run. The page must be published again from `control-room/page.html` to the same link. Sample reels and "train" still need the weekly run or a chat: studying a reel cannot be done without AI.

## 14 Nov 2026 — Cheaper session starts, missed runs catch up
Harish: every session burned half the usage limit just reading context, and a missed run never happened later.
| Piece | Where | In one line |
| --- | --- | --- |
| No whole AGENT.md | `CLAUDE.md`, run cards, `.claude/hooks/no_whole_big_reads.py` | Sessions read the map and one section; a hook refuses whole reads of files over 40 KB (AGENT.md is about 30,000 tokens) |
| Catch-up check | `tools/run_due.py`, `config/agent.yaml` `catch_up` | No-AI check of main: each run is done, not yet, due or too late; a late Plan plans only the slots with time left |
| Missed reels move, not cancel | `runs/plan.md` step 4, `tools/run_due.py` | A late Plan run gives missed reels the open times (flex slots too); leftovers go to the bank unless stale news |
| Dispatcher v2 | `runs/README.md` | Repository attached; `RUN catchup` five times a day starts only the runs that are due |
| Measured | — | A new session with no repository loaded about 60,000 tokens of plugin and connector lists before its first step; unused ones should be switched off (GUIDE 10) |

## 13 Nov 2026, night — Managing the agent (Control Room round)
Harish asked for: buttons before chat, far fewer tokens, easy refinement loops, a guidebook, and a safety audit.

**Built (AGENT.md first: 4.2, 4.3, 8.5, 8.6, 12.1, 12.5, 13.3, 15, 16, Blocks B and D)**
| Piece | Where | In one line |
| --- | --- | --- |
| Relay | `engine/relay.py`, Drive `control/inbox/` | The Control Room creates one small file per action; every job takes them in, applies, logs, bins. Undo for switch, settings, series, rules. |
| Panel | `engine/panel.py`, Drive `status/panel.md` + `panel.txt` | One status file after every job: reels, next runs, tomorrow, numbers, money, alerts, last actions. |
| Word changes | `engine/edits.py` | Change a hook or caption before posting; new version of a posted reel that waits for "post now". |
| Standing rules, ideas | `engine/brief.py` | Printed at the top of every brief. |
| Hold posts = approve first | `engine/post.py` | "Post now" releases one reel while posts are on Hold (never on Sleep). |
| Control Room page | `control-room/page.html`, https://claude.ai/artifact/LiQvqiXriy9fZeWteZLWD6 | Cards and buttons; reads the panel and writes the inbox through the Google Drive connector. No Claude tokens. |
| Clean chat per run | `runs/*.md`, dispatcher chat | Scheduled tasks send `RUN <name>`; a dispatcher on the cheapest model starts a new session that reads its run card. |
| Guidebook, skills | `GUIDE.md`, `.claude/skills/{apply-feedback,series-change,workshop}` | Every control, loop and ready prompt. |

**Found in the audit**
| Finding | Status |
| --- | --- |
| No scheduled GitHub job had ever fired (0 runs with event "schedule"); everything so far ran by hand. The 18:00, 20:00 and 21:30 slots of 13 Nov did not post. | Clock files re-saved on main by this merge; checked again after the 23:40 nightly. See the next entry. |
| Two "PIPELINE TEST" reels were still marked ready for 18:00 and 20:00 on the live page | Skipped through the new inbox (also the first real test of the relay) |
| Thinking runs woke one long chat: about 200,000 tokens re-read per step (Plan run 5.5 million tokens, about $2.7 at list price, for 3 reels) | Clean chat per run; self-test passed end to end |
| The Control Room had never managed to write a setting (the Drive connector can create files but not rewrite them) | Inbox design: create only |
| Dashboard sheet settings sat under `runner:` in `config/engine.yaml`, so the nightly dashboard job failed | Fixed |
| Image cap ignored a change from the Control Room; a reel Harish skipped was made again at the next Make run | Fixed |
| Dead branch triggers in five workflows | Removed |
| Approval levels "check_in" and "hands_on" and away mode are shown but the Engine does not act on them | Not built; "Hold posts" + "Post now" is the working approve-first mode |
| The Breaking run still wakes the long-lived chat (its API link is tied to that task) | Left as is: rare. To move it, make a new API trigger and update the two GitHub secrets. |

**The clock, checked at 02:30 on 14 Nov:** GitHub's timer does fire, but every tick arrives about 7 hours late (09:48 UTC came at 17:23, 10:42 at 18:00, 11:52 at 18:48, 14:18 at 20:53). The earlier "never fired" was this delay, seen 9 hours after the files reached main. Fix: Claude scheduled tasks send `TICK <job>` to a small clock chat that starts the GitHub job on time (AGENT.md 4.3, `runs/README.md`). GitHub's timer stays as a late backstop. A free outside pinger can replace the Claude clock (`GUIDE.md` 12).

**Tests:** `python -m tests.test_control_room` (no keys). On the real Drive: `daily` → `panel` and `control` from the branch; `RUN selftest` through the dispatcher reached main.

**Scheduled tasks now:** Plan, Refresh, Weekly, Monthly and Self-test send `RUN <name>` to "iNiKKi Brain · dispatcher". The four long-chat tasks are switched off (kept, named OLD). One one-time safety net for the first clean Plan run: 14 Nov 06:20.


## 13 Nov 2026: the approved looks, and the two builds joined into one
Harish reviewed reels in five rounds (rules/changes.md #4 to #8) and approved five looks: Stage (breakdowns), Bulletin
(updates), Poster Wall (Watch This Next), Verdict (review) and Flash (breaking). Their plans are the reference set in
`plans/reference/` (the Brain cannot change that folder); the reels are in Drive `reference-reels/2026-11-13/`.

That work was built on a second branch (claude/clever-clarke-b0wco6). This branch now holds both builds:

| Part | Now |
| --- | --- |
| Rulebook | One AGENT.md. Harish's approved rules win; the Engine's sections came across (pictures 5.11, Watch This Next 5.12, trailer breakdowns 5.13, older looks 5.14) |
| Reel maker | `engine/render/` (Node + Chromium) draws the approved looks; `engine/render.py` hands those plans to it and still draws the older looks (Diorama for Guess the Movie, Cinematic for Artwork) |
| Drive | One module, `engine/drive.py`, with a command line for the jobs (`python -m engine.drive check / sync-music / upload-out`) |
| Daily Make | Workflow "make" (now also on this branch): plan check, render, Drive `rehearsal/<date>/<reel>/`, ledger, status |
| By hand / golden test | Workflow "Make reels": chosen plans, or after a change to the looks the reference set into Drive `rehearsal/golden-check/` |
| Plans | The approved plan form (templates/README.md): `id`, `package` (caption, cover, slot). Make, Post and the golden test read both forms |
| Retired | The Card look and the Kaithi model (16-19 screens): plans moved to `archive/plans-v1/` |

Then, the same day:
- Plan check for the approved form (`engine/plancheck.py` check_look); skills plan-reel, score-reel (8 checks) and
  weekly-learn rewritten; role cards synced to AGENT.md.
- Tests in the cloud, all passed: golden (same picture twice, 5 looks, re-made into Drive `rehearsal/golden-check/`),
  the daily Make job on two copies of reference plans (both "ready" in Drive `rehearsal/2026-11-13/`, then the test
  plans were removed; in rehearsal they are only marked "rehearsed"), Instagram read, health.
- **Instagram:** the "API access blocked" spell has cleared on Meta's side. Health: "posting permission OK".
  The trailer job now runs once a day (04:52, as AGENT.md 5.11 says): both blocks came on heavy-reading days.
- **On main** (Harish's go-ahead): the schedules run from there. Phase: rehearsal.
- Learning loop: the week table now checks whether each recent change helped (14 days before and after, each
  series' own number) and marks REVERT at -20%; Harish's rules are only shown, never undone; the small numbers
  rule needs 10 reels and 14 days. The brief and the week table now see every change (#1-#9).
- Sync takes the recommended-films log; the brief gives picture instructions for the approved looks.
- The 5 thinking runs: made as scheduled tasks in the `inikki-reels` cloud environment (which has the repository).

Open: the Bulletin look cannot carry a voice yet (voiced updates are held by the plan check: music-only for now);
Guess the Movie and Artwork keep their earlier looks until rebuilt; a still from any trailer second (not only the
4 official YouTube frames) would give breakdowns more pictures.

## 12 Nov 2026 (evening): the trailer library, new series, sample reels
Harish ran the laptop helper: 23 of 38 trailers into Drive `clip-library/` (grids made by the adopt-only run).
His feedback and what was done:

| He said | Done |
| --- | --- |
| 15 films did not download (Vada Chennai, Asuran, Nayakan, Thalapathi...) | Helper: spelling- and spacing-tolerant titles (VADACHENNAI, Kaakka, Nayagan), sequels refused (Jailer 2 for Jailer), more official channels, three searches, a report file that goes to Drive with the trailers |
| Do the top-up about every 2 weeks; new trailers can come a day later | Drive `requests/trailers_to_get.md`: one ready command for new trailers and one for the library top-up; the digest's "Needs you" line points to it; the Plan run adds official links |
| Find updates before they drop | The news watch notes announced trailer dates; the brief shows trailers expected and new ones in the library |
| Trailer breakdowns of new trailers | New series `trailer-breakdown` (AGENT.md 5.12), flex slot |
| Breakdowns of English films too | 20 English films in the film bank and the helper |
| Replace Viral Story with Movie Recommendations (actors, Hollywood directors, musicians, Letterboxd) | New series `movie-recommendations` (AGENT.md 5.11), every "X recommends Y" sourced; viral-story paused |

Grid maker: dark or fast trailers read again more finely, long stretches split into 3.5-second moments, logo cards
dropped (Vikram 13 -> 25 moments, Maharaja 7 -> 26, Kaithi 15 -> 24); `regrid` remade all 23.
Bug found in review: a redone plan with the same reel id got this morning's stock photos back (pictures were reused
by reel id and number only); saved pictures now carry a fingerprint of the picture asked for.

Sample reels (Drive `rehearsal/samples-2026-11-12/`): Leo and Vikram Vedha breakdowns, Jailer 2 and Scene updates on
official stills (Scene with the makers' own figures), the first recommendation reel (4 films Rajinikanth praised,
each sourced). First render reviewed frame by frame; Leo had moments landing on title cards, fixed from the finer grid.

Lessons from four review rounds (all built into the Engine, so planning runs get them for free):
- Trailers dissolve between shots and carry star and director credits, so one frame per shot misleads. New: a
  **timeline sheet** per trailer (a frame every 1.5 s) for planning, and a **frames check** in the trailer job
  (frames at +0..+3 s of each planned start) for reviews.
- A line often lasts longer than its moment. New: `max_len` on a clip: the moment plays in gentle slow motion (at most
  1.6x) and holds its last frame, never running into the next shot or a credit card.
- The voice service failed once (edge-tts "No audio was received"); the reel came out silent as designed (fail soft)
  and was simply made again.

## 12 Nov 2026 (afternoon): Harish's review of rehearsal day 1, and the fixes
Harish: only the Kaithi reel was up to standard. Breakdowns were 27 s with vague topics, pictures did not match the words,
story pictures were weak, trailers must come automatically. Fixes (AGENT.md 5.9 and 5.10 first):

| Fix | Where |
| --- | --- |
| Breakdowns follow the Kaithi model: 45 s, 16-19 screens, 3 named points proven by real scenes; the plan check refuses anything else | AGENT.md 5.10, `engine/plancheck.py`, series cards |
| Breakdowns and updates use only the film's own trailer clips (no stock photos, no AI); no trailer, no reel | AGENT.md 5.9, plan check, `engine/make.py` |
| Trailers by code from the official studio, label, star and streaming accounts on Instagram (official API), each with a numbered shot grid; planning runs pick the exact second per line | `engine/trailers.py`, `.github/workflows/trailers.yml` (04:52, 12:52, 20:52 IST) |
| News drops go on a wanted list; Make fetches a plan's missing trailer first; trailers dropped into clip-library by hand get grids automatically | `engine/watch.py`, `engine/make.py`, `trailers.adopt` |
| Story pictures: full image model, real-film look, exact-shot prompts with one character description | `brands/inikki-reels/image_styles.yaml` (cinematic_real), viral-story card |
| No YouTube workarounds from the cloud; older films come from the laptop helper (`--film-bank`, one command) | `engine/clips.py`, `tools/clip_helper.py` |

Lesson: Instagram allows this app about 200 calls an hour. The first trailer test read 30 accounts x 8 films and hit
"(#4) Application request limit reached" (it also blocks posting while it lasts). Now: at most 40 calls a run, 2 pages
of 25 posts per account, a 6-hour shared copy, and the search stops when Meta's own usage header says 50%.
The earlier "API access blocked" (morning) cleared by itself: Meta's side.

Later the same afternoon (15:14 IST): Instagram answered again, but Meta's meter read 51% after only 19 calls, so the
search stopped as designed. Changes after that run:
- A film's own accounts come first and are read further back (`Film@account`, or a plan's `trailer_from`), 50 posts a call.
- The search stops at the first real trailer; wrong account names are remembered for 3 days; one refusal stops the run.
- One-word titles (Scene, Leo) match only as a hashtag, in capitals, or right before "trailer".
- Hand-added trailers get grids even when Instagram says no; every run puts its report and new grids on the `peek` branch.
- Make asks for a plan's trailer before the moments are picked; the brief lists reels whose trailer has arrived.

What the runs at 16:19 and 17:23 IST showed (Meta's own meter readings are now in each report):
- The meter that fills is **processing time** (`total_time`), not the call count: each account page takes Meta 3-8 seconds,
  so about 20 calls use half the hourly allowance. Pages are now read as captions only; the video link is asked for the
  matching post alone, at most twice per account per run.
- Sun Pictures has 24 Jailer 2 videos in its last 300 posts (trailer posts on 6 and 11 Oct), but Meta sent no video link
  for the ones asked. The next report says why (moved post, or Meta leaving the link out, which it does for posts it
  treats as holding copyrighted music).
- Wrong account names found: rkfi_official, madrastalkies_, 7screenstudio (skipped for 3 days, to be corrected).
- Fact check before writing: "Inji Vellam on 29 January" is not confirmed (only "January 2027"); "extra 30 minutes" for
  Jailer 2 is not confirmed; both left out. Leo: "Sathya doubts him" is not confirmed; that point became "the denial".

19:30 IST, the answer: Meta sent no video for the Jailer 2 trailer posts (7 of 32 posts around them had links), but it
does send each post's cover picture. Meta's documentation: the video is left out for licensed music or when the owner
turned downloads off. Vijay's account has no Leo trailer post; Lyca has no Inji Vellam post; Sivakarthikeyan's account
cannot be read by the app.

**Harish decided (19:45 IST): official stills for news, real clips for breakdowns.** Built:
- `trailers.stills()`: the covers of the film's video posts and its picture posts, from its own accounts, up to 30, saved
  to Drive `clip-library/stills/<film>/` with a numbered grid; the trailer job falls back to stills when Meta gives no
  video, and has a stills-only option. Updates pick `{type: image, still: {film, n}, ai: false}`; the plan check accepts
  clips or official stills for updates, clips only for breakdowns (series card `visuals: official`).
- The laptop helper (`tools/clip_helper.py`, also in Drive) works on its own: film list inside (film bank + 6 well-known
  films), ffmpeg bundled, only official channels and exact titles (not Jailer 2 for Jailer, not Vikram Vedha for Vikram),
  skips what it already has. Steps for Harish: Drive doc "iNiKKi — fill the trailer library".
- A trailer folder dragged into Drive whole is used too; the library index picks the exact trailer file.
- The news watch reads film titles cleanly from headlines and searches the accounts a headline names first.

Redone so far: the story (Sivakarthikeyan) in Drive `rehearsal/redo-2026-11-12/`, inspection passed, pictures checked by eye.
Waiting: the trailer runs (hourly while needed), then the 3 updates from fetched trailers; the breakdowns need
their films' trailers (history search over a few days, or the laptop helper once).

## 12 Nov 2026 — Phase 3: the daily jobs (rehearsal) and Phase 4 hand-over
Harish approved the reels and the sound. Design first: AGENT.md **4.3** (Sync job), **4.5** (rehearsal, then live), **10.2** (respect mode), **12.1** (hold), Block D (how thinking runs hand over their work), Block E (`phase`, `respect`).

| Job | Code | Workflow | When (IST) |
| --- | --- | --- | --- |
| Make | `engine/make.py` | `make.yml` | when plans arrive (Sync starts it), plus 06:42 and 17:22 as a safety net; a 1-minute check first |
| Post | `engine/post.py` | `post.yml` | 8 runs, about 12 minutes before each slot; waits for the slot; also runs the news watch and 2-hour stats |
| News watch | `engine/watch.py` | inside Post | no AI; trusted feeds in `niches/tamil-cinema/knowledge/sources.yaml` (proposed, Harish to confirm) |
| Stats | `engine/measure.py` | `daily.yml` 23:40 | rates per reach, health colours against the series median, `data/metrics/` |
| Brief | `engine/brief.py` | `daily.yml` 05:12, 16:12, Sun 22:12, 1st 22:42 | `data/brief.md`, Control Room copy in `data/control/`, `data/week_table.md` |
| Clean-up | `engine/clean.py` | `daily.yml` 23:40 | retention rules from `config/engine.yaml`; to Drive's bin; old plans packed into `plans/archive/` |
| Health | `engine/health.py` | `daily.yml` 04:01 | keys, posting permission, image budget, runner minutes (counted from GitHub), storage, voice |
| Dashboard | `engine/dashboard.py` | `daily.yml` 23:40 | rewrites the 7 tabs of the sheet |
| Sync | `engine/sync.py` | `brain-sync.yml` | when a thinking run pushes a `claude/brain-*` branch: only allowed text files reach main, the rest is refused and reported |

How a day runs: Brief (05:12) → Plan run (05:37) pushes plans → Sync → Make → Post at each slot (rehearsal: marks "rehearsed") → Refresh (16:37) → nightly stats, dashboard, clean-up.
Day status in Drive `status/days/<date>.json` and `status/today.json`; jobs save only the reels they touched, so Make and Post can run at once.
Every workflow ends with `python -m engine.status <job> <result>` (CLAUDE.md rule 6). Cost guards: runner minutes counted daily; above 85% reserves and bank reels wait.

Tested: offline (fake Drive) for slot choice, reserves, bank, respect mode, 24-hour news expiry, two-job saving; the Sync guard in a throwaway repository (took a plan and a note, refused a code change and a volume change); on GitHub: Post, Make check, Brief and the news watch (4 of 5 feeds answer).
Scheduled tasks made from a build session get no repository (tested twice), so the 5 thinking runs are created by Harish on the Routines page (Block D).

Rehearsal day 1 (12 Nov, made by hand as the Brain): 6 plans + 2 reserves. Reserves (the two approved golden reels) came out ready.
The 3 news reels and 2 breakdowns were first held by inspection: no real pictures (clip-library is empty; free-photo keys not added yet;
the public-domain search was too strict). After a wider search and the neighbour-picture fallback, a retry made 4 of the 5:
7 of 8 reels ready; the Scene box-office update stays held (no free photo at all). They also ran short (16-27 s against 30-50 s): the plan check now warns.
Health check on GitHub: Drive OK, voice OK, image budget ₹14 of ₹500, OpenAI key OK (limited to pictures), news feeds 4 of 4.
**Instagram: Meta answers "API access blocked" for the app itself** (the Facebook door and the app's own token check). Not a token problem.
Harish opens developers.facebook.com > My Apps > the app and follows the banner; the same token then works. Posting waits for this.
Waiting on Harish: Meta app block (above), merge to main (schedules only run there), the 5 routines, optional keys `PEXELS_API_KEY` and `PIXABAY_API_KEY`, `BRAIN_FIRE_URL` and `BRAIN_FIRE_TOKEN` from the Breaking routine, trailers in `clip-library/`, confirm the trusted news list, then "go live" after the rehearsal days.

## 11 Nov 2026 (later) — Phase 2, round two: Harish's feedback on the golden reels
Harish watched the first three. Voice and music: fine. Asked for: Guess the Movie in real 3D, the story to name the person at the end,
a premium and brighter look with a visual hook and transitions, and pictures from existing sources before AI.

Design first (AGENT.md): **5.8** the look (visual hook, no logo intro, transitions, brighter, 3D Guess, name reveal) and **5.9** where pictures come from.
Brand kit gained Marquee Indigo and Screen Violet (rules/changes.md #1 to #3, each with an undo).

| Built | Where | Note |
| --- | --- | --- |
| Visual hooks | `templates/common/hooks.js` | thunder, flare, impact, spotlight, clap; each with its sound; default per series card (`hook:`) |
| 3D scenes | `templates/common/relief.js` | picture + depth map as a real surface (WebGL2, software on the runner); camera push / track / orbit / crane / pull; focus, light, fog, rain, dust; lightning lights the scene. Falls back to layered scenes |
| Transitions | all templates | Card flash cut, Cinematic flash and settle, Guess whip to the next clue |
| Name reveal | Cinematic `reveal` motion | "None other than …"; the plan check refuses a Viral Story without it |
| Picture ladder | `engine/sources.py` | library index → trailer frame → Pexels / Pixabay / public domain → AI. Plan image fields `find`, `trailer`, `ai: false` |
| Scratch branches | `peek` (build-time looks into Drive), `review` (render review sheets) | delete both after the build |

Local template work with real pictures: `INIKKI_LOCAL_IMAGES=<folder> python -m engine.render <plan> --local` (pictures named `<reel_id>_NN.jpg`, optional `_depth.png` beside them).
Second render of the golden reels goes to Drive `rehearsal/phase2-golden-v2/`.

**Music index** (Harish: "if you can categorise them and use them intelligently, great"): `engine/music_index.py` listens to every track once
(tempo, energy, brightness, drums, build) and scores it for each mood; written to `index.json` in the Drive music folder.
Reels pick by mood from it, never the same track twice in a series within 7 days. Job: `.github/workflows/music.yml` (weekly, and on demand); it also tags and files anything dropped into `music/inbox`.

**Voice hiccup (12 Nov, render run 7):** Microsoft's voice service failed for the Kaithi reel, so it fell back to the silent version, as designed.
The voice test passed again an hour later. Retries now start clean (a half-written clip is never reused) and wait 10 s, then 30 s.

Still open: real word timing for subtitles; AI video for moving characters (a cost decision for Harish).

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

**Golden reels: made on GitHub Actions, all three passed inspection (11 Nov, render run 4)**
| Reel | Template | Length | Voice | New AI images | Size | Loudness |
| --- | --- | --- | --- | --- | --- | --- |
| golden-kaithi-breakdown | Card | 45.3 s | 18 lines (Microsoft, from the cloud) | 0 | 10.6 MB | -14.0 LUFS |
| golden-second-tier | Cinematic | 42.1 s | none | 6 (first run; reused after) | 27.9 MB | -14.1 LUFS |
| golden-kaithi-guess | Diorama | 30.0 s | none | 3 (first run; reused after) | 7.6 MB | -14.4 LUFS |

They are in Drive `rehearsal/phase2-golden/`, with a plain report ("READ ME FIRST"). Image spend this month: about ₹11 of ₹500.
A full run of the three takes about 10 minutes on the runner. The depth model downloaded and ran (no fallback notes).

**Waiting on Harish:** watch and listen to the three reels ("same quality or better", or what to change); put trailers into Drive `clip-library/`.
The build session cannot hear: loudness and timing were measured, not listened to.

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
