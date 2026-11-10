# iNiKKi Reels — Master Spec (v1, 10 Nov 2026)

This is the single source of truth for building and running iNiKKi Reels, a self-running Tamil cinema Instagram page. Whoever builds the system (Claude, in the Workshop) builds from this file. If anything else disagrees with it, this file wins. Change it only through a logged decision.

---

## 0. In one paragraph

Claude, running on Harish's Pro plan as scheduled cloud tasks, is the **brain**. It does trend research, leads, scripts, screen plans, captions and self-review, and it writes everything as small text files into a GitHub repository. GitHub Actions is the **muscle**. When those files land, free cloud runners do the mechanical work: generate images (OpenAI, capped at ₹500 a month), fetch movie clips, record Tamil voice (Harish's Microsoft voice tool), render the reels from fixed templates, quality-check them, post them to Instagram at set times, and pull the stats back every night. A Google Drive folder mirrors status and media so Harish can manage everything from a Claude Project chat, the **Control Room**, with cards and buttons. Five loops make it better over time: production, trend radar, virality check, weekly learning, and the Series Lab that invents and tests new series.

---

## 1. The page

| Item | Value |
| --- | --- |
| Handle | @inikki_reels (Creator account) |
| Display name | Currently "iNiKKi_PLAN". Change it to **iNiKKi Reels**. |
| Bio today | "Cinemas & Stories" |
| Mascot | Yellow ticket with a smiley face (profile picture) |
| State on 10 Nov 2026 | 12 posts, 37 followers, 127.9K views in 30 days |
| Proof of what works | "Guess the Tamil Movie #3" (pinned, 3D-render style): **104K views**. Newest cinematic reels: 203 and 17 views. Guess #1 (Kaithi) uses the same 3D style. |
| Language | Tamil cinema. On-screen headline in Tanglish or English, with a Tamil-script line under it. Voice in Tamil. |
| Audience time zone | IST (Asia/Kolkata). All times in this spec are IST. |

---

## 2. Decisions locked

1. **The main product is Film Breakdowns**, 2 a day (screenplay, filmmaking or cinematography, explained with motion graphics and real clips).
2. **Guess the Tamil Movie joins the daily mix.** It shares the "story slot" with Viral Stories. Starting mix: Guess 4 days a week, Viral 3 days. The weekly review moves the mix toward whichever wins.
3. **No approval gates.** The system checks itself and holds back anything that fails.
4. **Claude (Pro plan) is the brain.** It runs as scheduled cloud tasks, and holds no API keys.
5. **OpenAI is for images only.** Cheapest current image model, hard cap of ₹500 a month. Clips cost nothing: they are fetched by code.
6. **Voice uses Harish's Microsoft voice tool** (`tools/voice_tool.py`, edge-tts, Tamil neural voices). It runs on GitHub's cloud runners. If Microsoft blocks the cloud, it falls back to Harish's laptop at 8 PM.
7. **Real actors are shown as inspired-by illustrations** (mood, era, setting, look-alike styling), never as photoreal fakes or deepfakes.
8. **Everything runs in the cloud.** The laptop is a backup only.
9. **Series are plug-ins.** Adding, pausing or retiring a series never needs engine code changes, unless the series needs a new template.
10. **Token thrift:** Claude decides and writes; code does everything repetitive. No Claude tokens are spent on rendering, uploading or posting.

---

## 3. Daily content plan

**Base day: 6 reels. Busy day: up to 8. Never more than 8.**

| Slot | Series | Per day | Template | Visuals | Voice | Default post time (IST, to be learned) |
| --- | --- | --- | --- | --- | --- | --- |
| A | Movie Updates | 3 | Card | Real posters, stills, trailer clips | Yes | 08:30, 18:00, 21:30 |
| B | Film Breakdown | 2 | Card | Real clips | Yes | 12:30, 20:00 |
| C | Story slot: Guess the Tamil Movie **or** Viral Story | 1 | Diorama (Guess) / Cinematic (Viral) | AI images | No | 15:30 |
| Flex | Movie Review (release days, up to 2 on event days) **or** Artwork + Quote (after a dull stretch of 2–3 days) | 0–2 | Card + hype art / Cinematic | Clips + 1–2 AI images | No | 11:00 / 17:00 |
| Extra | Breaking News | 0–2 | Card (red) | Posters, stills | No | Within about an hour |
| Lab | Series Lab pilot, posted as an Instagram **Trial Reel** (non-followers first) | at most 1 every 2 days | Any existing template | Mostly AI images | Optional | 14:00 |

Rules:
- Breakdowns keep a **ready bank of 3–4 finished reels**, so the main series never goes empty.
- Trial Reels from the Lab don't show to followers first, so they don't count toward the 8 per day.
- If a slot has no lead scoring 60 or more, it takes a bank breakdown or a reserve story.

---

## 4. Architecture

```
            ┌───────────────────── BRAIN (Claude, Pro plan, scheduled cloud tasks) ─────────────────────┐
            │  Trend radar · leads · scripts · screen plans · captions · virality check · weekly review │
            │  Series Lab · writes ONLY text/JSON into the GitHub repo · no API keys                    │
            └──────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                   │ git push (plans/, series/, playbook/)
            ┌──────────────────────────────────────▼──────────────────────────────────────────────────┐
            │  GITHUB REPO  inikki-reels  (private)  — code, templates, plans, logs (no media)          │
            └──────────────────────────────────────┬──────────────────────────────────────────────────┘
                                                   │ on push / on cron
            ┌──────────────────────────────────────▼──────────────────────────────────────────────────┐
            │  MUSCLE (GitHub Actions, free runners) — holds all keys as GitHub Secrets                 │
            │  OpenAI images · clip fetch · edge-tts voice · depth layers · render · QC · post · track │
            │  hourly news watcher (no LLM) → fires the Brain's API trigger when big news breaks        │
            └───────────────┬───────────────────────────────────────────────┬──────────────────────────┘
                            │ media + status (service account)              │ Instagram API
            ┌───────────────▼──────────────┐                     ┌──────────▼─────────┐
            │ GOOGLE DRIVE "iNiKKi Reels"  │◄── reads/writes ──► │ CONTROL ROOM       │
            │ media, status, control files │                     │ Claude Project chat│
            └──────────────────────────────┘                     └────────────────────┘
                   ▲ fallback only: laptop voice helper (voice_tool.py) at 8 PM
```

### 4.1 Brain runs (Claude scheduled tasks, Default "Trusted" cloud environment, connectors: Google Drive only)

| Run | Time (IST) | Job | Model |
| --- | --- | --- | --- |
| Morning | 05:37 | Trend radar · news scan · today's 3 updates (scripts + screen plans) · breaking check | Daily model (fast, cheap) |
| Midday | 12:37 | Breaking check · top up the breakdown bank · tomorrow's story-slot reel | Daily model |
| Evening | 16:37 | Breaking check · refresh the 21:30 update with the latest news · flex decision (review/artwork) | Daily model |
| Night | 21:37 | Read today's stats · daily notes · plan tomorrow · Control Room sync | Daily model |
| Weekly | Sun 22:37 | Learning review (playbook + series rules) · Series Lab (every 2nd week) | Most capable model on the plan |
| On demand | API trigger | Breaking news, fired by the Muscle's watcher | Daily model |

- Times sit a few minutes past the hour on purpose, because on-the-hour runs can start late.
- Each run is self-contained. It reads `state/`, does its job, writes files, commits to `main` with a clear message, and stops.
- **Usage budget:** measure in the rehearsal week. If Pro limits are reached, merge the Midday run into the Evening run first.

### 4.2 Muscle jobs (GitHub Actions)

| Workflow | Trigger | Does |
| --- | --- | --- |
| `produce.yml` | push to `plans/**` | For each new reel plan: images → clips → depth layers → voice → render → QC → upload to Drive → add to the posting queue |
| `post.yml` | cron every 15 min | Posts due reels. Checks `control/` (pause, cap) before every post. Sets cover frame, caption, first comment. |
| `track.yml` | cron 23:15 nightly + 2h after each post | Pulls insights (views, reach, avg watch time, skip rate, likes, comments, saves, shares/sends, reposts, follows) → `data/metrics/` |
| `watch.yml` | cron hourly | No-LLM news watcher on trusted RSS/pages + YouTube channel feeds. On a strong signal, it POSTs to the Brain's API trigger. |
| `status.yml` | after every job | Writes `status/today.json`, `status/alerts.json`, `status/budget.json` to Drive |
| `health.yml` | daily 04:00 | Token expiry, OpenAI balance, Actions minutes, Drive space, voice service reachable |
| `tests.yml` | every PR | Template renders, schema checks, 3 golden reels compared frame-by-frame |

### 4.3 Why this split

- Claude never spends tokens on mechanical work, so the Pro plan goes to thinking.
- API keys stay in GitHub Secrets. The Brain needs no keys, and its network can stay on the default allowlist.
- Templates make rendering deterministic: the same plan always gives the same reel.

---

## 5. Repository layout

```
inikki-reels/
  CLAUDE.md                     ← Workshop rulebook (from 02_WORKSHOP_CLAUDE.md)
  docs/MASTER_SPEC.md           ← this file
  series/<series_id>/series.yaml + examples/ (links or small refs)
  templates/card/  templates/cinematic/  templates/diorama/   ← render engines
  engine/ (python)  images.py clips.py depth.py voice.py render.py qc.py post.py track.py watch.py drive.py budget.py
  tools/voice_tool.py           ← Harish's tool, unchanged
  plans/YYYY-MM-DD/<reel_id>.json   ← written by the Brain
  state/  posted_log.jsonl  bank.json  calendar.json  trends.json  lead_queue.json  experiments.json
  playbook/playbook.md  playbook/changes.md
  lab/backlog.md  lab/pitches/  lab/results/
  memes/meme_index.csv  memes/recordings_index.csv
  design/brand_tokens.json  design/DESIGN_SYSTEM.md
  data/metrics/YYYY-MM.jsonl
  .github/workflows/*.yml
```

Media (images, clips, voice, renders) live in Google Drive, never in git.

---

## 6. Data contracts

### 6.1 `series.yaml` (one per series)

```yaml
id: film-breakdown
name: Film Breakdown
status: live            # draft | trial | live | paused | retired
badge: { text: "THE SCREENPLAY BREAKDOWN", color: gold }
per_day: 2
slots: ["12:30", "20:00"]
template: card          # card | cinematic | diorama
visuals: clips          # clips | ai_images | mixed
voice: true
length_s: [40, 50]
image_cap_per_reel: 0
lead_sources: [film_bank, news_hooks, comments]
story_shape: [hook_question, numbered_reasons_3, payoff, send_to_friend]
hook_examples: ["Phone-a thoda vidala. Yen?", "Yaaru yaarai iyakkuraanga?"]
meme_use: ending_only   # never | ending_only | anywhere
success_metric: sends_per_reach
trend_hooks: true       # may tie a breakdown to a trending film/person/event
done_well: ["KAITHI_Premium_Reels_Aligned_VOICED.mp4", "JIGARTHANDA_Filmmaking_Tamil_VOICED.mp4"]
```

### 6.2 Reel plan `plans/YYYY-MM-DD/<reel_id>.json` (written by the Brain)

```json
{
  "reel_id": "2026-11-11-breakdown-01",
  "series": "film-breakdown",
  "post_at": "2026-11-11T12:30:00+05:30",
  "lead": {"topic": "Kaithi: why time, place and want drive the film", "score": 82, "sources": ["url1", "url2"], "trend_ref": "trend-2026-11-10-lokesh"},
  "virality": {"hook": 8, "send_trigger": 9, "comment_trigger": 7, "save_trigger": 6, "retention": 8, "loop": 5, "trend_originality": 9, "total_100": 74},
  "voice": {"voice": "ta-IN-ValluvarNeural", "rate": "+35%", "pitch": "-2Hz"},
  "screens": [
    {"n": 1, "dur": 1.5, "kicker": "KAITHI / THE SCREENPLAY BREAKDOWN", "headline": "Phone-a thoda vidala.", "tamil": "ஃபோனைத் தொடவே தோணலையே?",
     "visual": {"type": "clip", "film": "Kaithi", "query": "Dilli lorry close-up", "len": 2.5},
     "motion": "card_pop", "chips": [], "voice_line": "ஃபோனைத் தொடவே தோணலையா?"},
    {"n": 2, "dur": 4.0, "headline": "Fight mattum illa.", "chips": ["NERAM", "IDAM", "AASAI"], "visual": {"type": "clip", "query": "Dilli fight wide"}, "motion": "chips_in", "voice_line": "..."},
    {"n": 9, "dur": 3.0, "headline": "Sandai mattum ezhudhaadha da!", "visual": {"type": "meme", "mood": "calling_friend"}, "cta": "SEND TO THAT FRIEND"}
  ],
  "caption": {"text": "...", "hashtags": ["#Kaithi", "#TamilCinema"], "first_comment": "Neenga endha scene-la note pannineenga?"},
  "cover": {"screen": 1, "title_safe_3x4": true},
  "fallbacks": {"if_clip_missing": "still_frame", "if_voice_fails": "silent_with_music"}
}
```

### 6.3 Other files

- `state/posted_log.jsonl`: one line per posted reel, with topic fingerprint, film, people, images used, clips used, meme used, hook type. Used for no-repeat checks.
- `state/trends.json`: see section 8.
- `status/today.json` (Drive): reels with id, series, time, state (`planned | rendering | ready | posted | held | failed`), thumbnail link, reason if held.
- `control/overrides.yaml` (Drive): settings changed from the Control Room (pause flags, per_day, times, caps, banned topics, retired memes). The Muscle reads this before every job. The Brain merges it into `series/` at its next run and logs the change.
- `control/commands.jsonl` (Drive): one-off commands (post now, pull reel, redo voice line, make part 2).

---

## 7. The five loops

| Loop | Speed | Purpose |
| --- | --- | --- |
| L1 Production | Every run | Lead → script → screen plan → render → QC → post → track |
| L2 Trend Radar | Every Brain run + hourly watcher | Know what Tamil cinema audiences care about right now, and feed it into every series |
| L3 Virality Check | Before every post, and on metrics after | Make every reel more likely to be watched, sent and commented on, and learn which features predict that |
| L4 Learning | Weekly | Rewrite the playbook and series rules from real results |
| L5 Series Lab | Every 2 weeks | Invent, pilot and graduate new series. Retire weak ones. |

---

## 8. L2 — Trend Radar

**Goal:** every series rides what is happening now, especially breakdowns, reviews and updates.

**Sources (scanned with web search and fetch, no paid tools):**
- Tamil cinema news from the trusted source list (`state/sources.yaml`, to be confirmed by Harish)
- Official production-house and star accounts (announcements, posters, trailer drops)
- YouTube: view speed on new trailers and songs from official channels (RSS feeds, free)
- Google Trends, India / Tamil Nadu, for film and actor names
- Reddit r/kollywood and other public fan discussion (reading only)
- The page's own comments: questions, guesses, requests
- Calendar: releases, re-releases, OTT drops, film anniversaries (10/15/20/25 years), star birthdays, festivals (Diwali, Pongal), award nights. Kept in `state/calendar.json`.
- Format trends: new reel formats spreading on Instagram (seen through web coverage and Harish's notes in the Control Room)

**Output: `state/trends.json`**
```json
{"id": "trend-2026-11-10-lokesh", "topic": "Lokesh Kanagaraj new film announcement", "type": "person|film|format|hook|meme|event",
 "velocity": "rising|peak|fading", "evidence": ["url", "url"], "sentiment": "positive|mixed|negative", "risk": "none|fan_war|sensitive",
 "fit": {"film-breakdown": 0.9, "movie-updates": 1.0, "guess-the-movie": 0.6, "viral-story": 0.3}, "expires": "2026-11-13"}
```

**How trends feed the series:**

| Series | Trend use |
| --- | --- |
| Film Breakdown | A **news hook**. Example: a director announces a film, so break down their best earlier film today. Anniversaries and re-releases do the same. |
| Movie Review | Uses what audiences and trusted critics are saying in the first 24 hours, quoted fairly, plus the page's own verdict angle |
| Updates | Ranked by velocity and proof. Fading stories are dropped. |
| Guess the Movie | Picks films in the conversation (a birthday, a re-release, an anniversary) |
| Viral Story | Ties the story to a current moment (a star's milestone, a debut anniversary) |
| Series Lab | Repeated format trends become series pitches |

**Respect mode:** if the radar sees a death or tragedy in the industry, it sets `control/respect_mode` for the day. Hype reels, memes and jokes pause, and only a fitting tribute may post.

---

## 9. L3 — Virality engine

### 9.1 What the research says Instagram rewards
- Instagram's head, Adam Mosseri, named the three most important ranking signals as **watch time, likes and sends**, and told creators to track **average watch time, likes per reach and sends per reach**. Sends matter slightly more for reaching non-followers. ([Social Media Today, Jan 2025](https://www.socialmediatoday.com/news/instagram-shares-algorithm-2025/738034/))
- The Instagram API now reports **Reels skip rate** (the share of views skipped in the first 3 seconds) and **repost counts**, and can publish **Trial Reels**. ([Meta for Developers, Dec 2025](https://developers.facebook.com/blog/post/2025/12/03/instragram-api-updates/))
- Instagram favours original content over reposted clips, so clips are always used with commentary, design and the page's own voice on top.

### 9.2 Pre-post virality check (by the Brain, on the screen plan, before render)

Each plan is scored 0–10 on 7 factors, out of 70, converted to a score out of 100:

| Factor | Question | Instagram metric it predicts |
| --- | --- | --- |
| Hook | Does screen 1 (≤1.5 s) create a question or a surprise, readable in one glance? | Skip rate |
| Send trigger | Is there a specific person the viewer will want to send this to? ("that friend", the fan of this star) | Sends per reach |
| Comment trigger | Is there an easy, fun reply that doesn't start a fan war? (guess, number, 1/2/3) | Comments |
| Save trigger | Is there something worth keeping? (facts, a list, a filmmaking lesson) | Saves |
| Retention shape | A new visual every 2–3 s, a payoff before the end, no dead screens | Average watch time |
| Loop | Does the last screen lead back into the first? | Replays, watch time |
| Trend fit + originality | Is it timely, and is it clearly iNiKKi's own take? | Reach, non-follower distribution |

- **Under 65:** the Brain revises the weakest 2 factors once.
- **Still under 65:** the reel goes to the bank as a reserve, and a reserve plan is used instead.
- Every factor score is stored with the reel, so the weekly review can see which factors actually predicted results.

### 9.3 Screen Planner (the "content screens" manager)

Every reel is a list of screens. The Brain writes only the screen plan; templates turn it into video. Rules:
1. Screen 1 lasts at most 1.5 s and carries the hook.
2. Something visibly changes every 2–3 s: a new image, clip, chip, number or camera move.
3. Text per screen: a kicker (optional), a headline of 7 words or fewer, a Tamil line, and at most 3 chips.
4. AI images: each image carries at most 2 screens (as in the viral samples). The cap is set per series.
5. Clips: 2–4 s each, from official trailers or promos, always framed inside the card design with commentary.
6. The last screen holds the share or comment prompt and visually echoes screen 1, to encourage a loop.
7. Voice lines are written in Tamil script, short sentences with full stops (per `tools/VOICE_TOOL.md`), and timed after `batch` returns real lengths.
8. The cover frame is designed: title inside the middle 3:4 area of the frame (the profile grid crops to 3:4), set with the API's cover option.

### 9.4 After posting
- 2 hours after posting: pull early metrics. If a reel is far above its series average, flag it as **rising**. Tomorrow's leads then include a "part 2", a follow-up update, or a pinned comment.
- 24 hours and 7 days after posting: final scores. Each reel's score is compared with its own series median.

---

## 10. Leads engine

| Factor | Points |
| --- | --- |
| Fresh (new today or newly relevant) | 15 |
| Trend fit (from `trends.json`) | 15 |
| Proof (2 trusted sources agree. News without this is dropped.) | 20 |
| Hook strength (best of 5 written hooks, scored against past winners) | 15 |
| Series fit (rules + past winners) | 10 |
| Visuals ready (clips or images actually available) | 15 |
| Not a repeat (differs from the last 30 days) | 10 |
| Risk (fan-war bait, rumour, sensitive) | minus up to 30 |

A lead under 60 is never used. Each slot keeps 2 reserves. Lead weights are tuned in L4.

**Film bank:** `state/film_bank.json` holds Tamil films worth breaking down, with available angles (screenplay, cinematography, editing, music cue, performance), clip availability and the date last used. The weekly run adds films. A film can't repeat within 21 days, or 60 days for the same angle.

---

## 11. Visuals

### 11.1 Movie clips
- Source: official trailers, songs and promos on official YouTube channels, fetched by code in the Muscle.
- To pick moments, the Muscle makes a contact sheet (a grid of frames with timestamps). The Brain looks at **one image** per trailer and picks timestamps. That's cheap: one image, not a video.
- Clips are 2–4 s, saved to `clip-library/` in Drive with tags (film, scene, people, mood), and reused before anything new is fetched.
- If the cloud is blocked from YouTube: (1) use the library, (2) use a still frame, (3) the laptop helper fetches during the fallback session.
- Clip use is logged per film and studio. A muted reel or a claim shortens clip length for that studio, and repeated claims pause clips from it.

### 11.2 AI images (OpenAI)
- **Model:** the cheapest current image model that looks good at portrait size. When this spec was written, `gpt-image-2` had the lowest token prices on [OpenAI's pricing page](https://developers.openai.com/api/docs/pricing). Re-check before building.
- **Size and quality:** portrait (1024×1536), medium quality by default, upscaled to 1080×1920 by code. Low quality is used for background plates.
- **No text inside images.** All text is added by templates, so Tamil spelling is always exact.
- **Real people:** inspired-by illustrations (mood, era, costume, setting). If the model refuses, the fallback is back views, silhouettes, or a stylised painterly look (as in the Suriya and Vikram samples).
- **Style presets** (`design/image_styles.yaml`): `painterly_warm` (Suriya, VJS accountant), `cinematic_real` (VJS Second Tier, Petta), `arcane_painterly` (Vikram Sethu), `diorama_moody` (Guess the Movie).
- **Budget:** ₹500 a month, about $5.7 (OpenAI's minimum top-up is $5). Expected use is about 150–200 images a month. `budget.py` logs the real cost of every call from the API's usage data and enforces caps:
  - daily soft cap: 1/30 of the monthly budget, carried over if unused
  - per-series caps per reel
  - at 80% of the monthly budget: library reuse only for Viral and Artwork, and Guess the Movie drops to 3 days a week
  - at 100%: no new images until the 1st. Image series switch to library images or skip.
- Every generated image goes to `image-library/` in Drive with tags, for reuse.

### 11.3 Memes
See `memes/meme_index.csv` (50 unique memes, auto-tag draft) and `memes/recordings_index.csv` (37 unique raw recordings).
- One-time clean-up: remove duplicates, trim to the punchline, crop out TV logos and YouTube player bars (recordings), normalise loudness, then tag.
- Picking: the screen plan asks for a mood. Matches are filtered by cooldown (not in the last 10 days, at most twice a month) and ranked by past performance, then trimmed to 1–4 s.
- Rules: at most 1 meme per reel. Never on deaths, accidents, health, legal or sad news. Respect mode turns memes off for the day. Memes react to a situation and never mock a real person in the news. Viral, Artwork and Guess stay meme-free.
- New memes: drop them into Drive `meme-bank/inbox/`. They are cleaned and tagged automatically and shown on the Meme Bank card.

---

## 12. Voice

- Tool: `tools/voice_tool.py` (edge-tts, Microsoft neural voices). Defaults: `ta-IN-ValluvarNeural`, rate `+35%`, pitch `-2Hz`.
- Flow: the Brain writes voice lines → the Muscle runs `batch` → reads real line lengths → sets screen timings → renders with voice under the music.
- Used for: Updates and Breakdowns. Optional for Lab pilots. Never for Breaking, Viral, Artwork or Guess (on-screen text only, as in the samples).
- **Pronunciation list:** `design/pronunciations.yaml` maps names to spoken spellings (for example, a star's name written as it should be said). `Redo line` in the Control Room adds entries.
- **Fallback chain:** cloud edge-tts → retry in 10 minutes → laptop helper (Voice Session card at 8 PM, `tools/laptop_voice_helper` runs `batch` on waiting voice packs and uploads the audio to Drive) → silent version with music and full on-screen text.
- **Must be tested on day 1 of the build**, because whether the cloud can reach Microsoft decides the evening routine.

---

## 13. Templates and design system

All reels are 1080×1920 at 30 fps. Templates are code (HTML/React rendered with headless Chromium, for example Remotion or Playwright frame capture), so the same plan always gives the same reel.

### 13.1 Brand tokens (`design/brand_tokens.json`)
- **Ticket Yellow** (mascot, Guess the Movie badge): the primary brand colour
- **Reel Gold**: big headlines and numbers
- **Signal Teal**: kickers, chips, timers
- **Night Navy → Deep Violet**: card backgrounds
- **Breaking Red**: breaking news only
- **Fonts:** a tall condensed font for cinematic headlines (Anton or Bebas Neue style), a clean sans for cards (Inter or Manrope style), a Tamil font (Noto Sans Tamil or Mukta Malar style). All free Google Fonts.
- **Text order everywhere:** small kicker → big headline → Tamil line
- **Sign-off:** the ticket mascot appears on every end card, at the same place
- **Safe zones:** nothing important in the top 250 px or bottom 380 px, or the right 120 px (Instagram's buttons). Cover title inside the middle 3:4 area.

### 13.2 The three templates

| Template | Used by | Look (from Harish's samples) | Motion presets |
| --- | --- | --- | --- |
| **Card** | Updates, Breakdowns, Reviews, Breaking | Navy-violet starfield, header line "FILM / THE … BREAKDOWN" or "TAMIL CINEMA / DATE EDITION", framed clip card with a name tag, chips, timer dials and progress bars, bottom caption box (Tanglish + Tamil), meme ending, "SEND TO THAT FRIEND" pill | card_pop, chips_in, timer_dial, tension_bar, split_compare (two clips side by side), list_reveal, meme_end |
| **Cinematic** | Viral Story, Artwork + Quote, review hype art | Full-bleed AI image with slow push, teal small-caps kicker, white line + gold condensed headline (italic variant allowed), Tamil line, dark bottom gradient. Each image carries 2 text beats. | push_in, pan_lr, crossfade, text_beat_swap, final_question |
| **Diorama** (new) | Guess the Tamil Movie | Yellow "GUESS THE TAMIL MOVIE" badge, "Guess the Movie #N", clue pill, 3D-feeling scenes, countdown ring 3-2-1, gold title + year reveal, "Comment 1, 2 or 3" | see 13.3 |

### 13.3 Diorama template — Guess the Movie in the cloud

**Target:** get as close as possible to the 3D-render style (Guess the Movie #1 Kaithi; #3 reached 104K views) while rendering on free cloud runners, with no Claude tokens per reel.

**How it works:**
1. The Brain picks a film and writes 3 clues, from easy to hard by default (Lab will test hard to easy). Each clue is one object or scene description, plus the reveal.
2. OpenAI makes **one image per clue** (4 images per reel including the reveal) in the `diorama_moody` style: miniature tabletop or isometric diorama look, fog, practical lights, no text.
3. A free depth model (for example Depth Anything V2 small, on CPU) splits each image into 3–4 depth layers. Holes behind the subject are filled by inpainting with OpenCV (free).
4. A three.js scene places the layers on planes at different depths and adds real 3D touches: volumetric-looking fog cards, dust or rain particles, a moving light sweep, a slight camera dolly or orbit, depth of field, and simple 3D props from free CC0 low-poly kits where they help (handcuffs, a lorry, a clapboard).
5. Headless Chromium on the GitHub runner renders it frame by frame (target: under 10 minutes for a 30 s reel). ffmpeg encodes it, with a sound bed (royalty-free) and tick sounds on the countdown.
6. The UI layer is drawn on top: badge, episode number, clue pill, countdown ring, answer reveal, comment prompt.

**Structure (30 s):** title + Clue 1 (0–8 s) → Clue 2 (8–15 s) → Clue 3 (15–22 s) → "Lock your answer" countdown 3-2-1 (22–25 s) → reveal FILM · YEAR (25–28 s) → "Got it at clue 1, 2 or 3? Comment" (28–30 s).

**Optional, later:** a "Premium 3D" episode once a week using Blender with a fixed scene kit, only if the Lab shows the true-3D version clearly beats 2.5D. It would need a cheap cloud GPU or a public repository (free unlimited Actions minutes), so it stays a Phase 3 experiment.

---

## 14. Posting and tracking

- **Instagram API with Instagram Login** (Creator account). Permissions: basic, content publish, manage insights, manage comments.
- Reels are uploaded through the API's resumable upload where available. Otherwise a short-lived public link is used and deleted after posting.
- Each post gets a cover frame (`thumb_offset` or cover image), a caption, hashtags (3–5, from the series set and the trend), and a first comment (the comment prompt).
- Lab pilots post as **Trial Reels**.
- Captions: a short Tanglish line + a Tamil line + the question + hashtags. No more than 2 emoji. No engagement bait that Instagram penalises (for example "comment YES to…").
- The tracker stores every metric the API gives per reel at 2 hours, 24 hours and 7 days.
- The long-lived login lasts 60 days. `health.yml` refreshes it and warns 7 days before expiry.

---

## 15. Guardrails (fixed, only Harish changes them)

1. No rumours stated as fact. Unconfirmed news is labelled "reportedly", or skipped.
2. No fan-war bait. No insults to actors, fans or films. Comparisons are about craft, not "who is bigger".
3. Respect mode for deaths and tragedies.
4. Short clips only, always transformed with commentary and design.
5. Music: royalty-free library or none. Never copyrighted songs baked into reels, except short clip audio that is part of a trailer moment and is ducked under the voice.
6. AI images of real people are illustrations only, never photoreal fakes, never in false or embarrassing situations.
7. Daily and monthly budget caps are hard stops.
8. Nothing posts that fails QC. QC failure = held + reserve used + alert.
9. Corrections: a wrong fact gets a pinned correction comment within the next run, or the reel is deleted if the error is serious. The source is downgraded.

### QC checks (code, in `qc.py`)
Black or blank frames · text outside safe zones · Tamil text overflow · audio peaks and loudness (−14 LUFS target) · voice and screen sync · duration in range · cover frame present · no duplicate of anything in `posted_log` (perceptual hash of frames) · file size and format within Instagram's limits.

---

## 16. L4 — Learning (weekly)

Inputs: the week's metrics, virality factor scores, lead scores, trends used, QC failures, costs, comments summary.

Outputs (written to `playbook/playbook.md` with a dated entry in `playbook/changes.md`):
- What worked and what didn't, per series, compared with each series' median
- Changes the system **makes itself**: post times, hook styles, story shapes, lengths, lead weights, virality thresholds, meme choices, hashtag sets, story-slot mix (Guess vs Viral)
- Changes it **proposes only**: pausing or retiring a series, new templates, code fixes, guardrail changes
- **Test before switching:** about 1 reel in 5 tests one change. A change becomes the rule after it wins for 2 weeks.
- A process health section: which step failed most, the cost per reel, and Brain usage.

Every change is shown in the Weekly Report card with an **Undo** button.

---

## 17. L5 — Series Lab

**Purpose:** keep the page fresh by inventing, testing and graduating new series from real data, and by retiring tired ones.

**Every 2nd Sunday the Lab:**
1. Reads performance by series, hook type and topic, the trend radar, comment requests, and `lab/backlog.md`.
2. Writes up to **3 series pitches** (`lab/pitches/YYYY-MM-DD-<id>.md`), each with: name, one-line idea, why now (evidence with numbers), which template it reuses, cost per reel (images, voice), 3 sample hooks, a pilot plan and a kill rule.
3. Picks the top pitch and **builds 2–3 pilot reels**, using existing templates and OpenAI images within the Lab's budget share (at most 20% of monthly images).
4. Posts the pilots as **Trial Reels** (non-followers first), at most 1 every 2 days.
5. **Graduation rule:** across 3 pilots, it beats the page median on sends per reach **and** skip rate. It then becomes a `trial` series (flex slot, about 3 a week for 2 weeks), then `live` through L4.
6. **Kill rule:** 3 pilots below median on both. The idea is archived with what was learned.
7. **Retirement:** any live series in the bottom quarter for 4 straight weeks gets a "retire or rework" proposal.

Harish sees each pitch as a card with **Veto**, **Run it**, and **More like this**. With no answer, the top pitch runs.

**A pitch that needs a new template** becomes a change request in the Workshop. The pilot waits until the template passes tests.

Seed ideas are in `lab/backlog.md`.

---

## 18. Control Room (Claude Project chat)

- One Claude Project. Instructions are in `01_CONTROL_ROOM_PROJECT_INSTRUCTIONS.md`, and the card designs in `05_CARD_LIBRARY.md`.
- It reads live status from Drive (`status/`) and writes changes to Drive (`control/`).
- Every status reply is a card drawn with the Visualizer, with at most 4 buttons. Buttons send short commands into the chat.
- **Settings** (times, counts, pause, caps, ban a topic, retire a meme, story-slot mix) apply instantly through `control/overrides.yaml`.
- **Features** (new templates, formats, sources, platforms) become change requests (`requests/` in Drive), which the Workshop picks up.

---

## 19. Scenarios

| Scenario | What the system does | What Harish sees |
| --- | --- | --- |
| Normal day | 6 reels (3 Updates, 2 Breakdowns, 1 Guess or Viral) | Today card, all green |
| Big release day (Diwali, 3 films) | Up to 2 reviews in the flex slot, using trusted critics and audience talk | "Event day: 8 reels" |
| Urgent news at 11 AM | Watcher fires the Brain. A breaking reel posts within about an hour, without voice. | New reel on the Today card |
| Quiet news day | Updates under 60 are swapped for bank breakdowns or a reserve story | "2 updates swapped" |
| Page dull 2–3 days | Artwork + Quote switches on | Leads card note |
| Trend spike (re-release, anniversary) | Breakdown and Guess pick it up the same day | Trend tag on the reel card |
| A reel goes viral | "Part 2" or a follow-up gets top priority tomorrow, and a pinned comment is added | Celebration card with Make part 2 |
| Voice cloud blocked | Laptop helper at 8 PM, or silent versions | Voice Session card, alert |
| Harish away a week | Bank breakdowns, silent updates if needed, everything else runs | "Away mode" banner |
| Pro usage limit reached | The Muscle keeps posting from the bank and plans already written. Missed Brain runs catch up at the next window. | Alert |
| OpenAI cap or refusal | Library images, stylised fallback, or skip | Note on the reel |
| GitHub Actions minutes low (private repo free tier) | Lower render resolution for Lab pilots first, then alert | Health alert |
| News wrong by morning | Pulled and replaced with a corrected update | Alert: "Pulled 1, replaced" |
| Death or tragedy | Respect mode | Banner |
| Fan war in comments | Topic muted for 7 days | Weekly Report note |
| Muted reel or copyright claim | Logged, clips shortened for that studio, repeated claims pause that source | Alert |
| Instagram login near expiry or posting fails | Auto-refresh, 3 retries, then hold | Alert with Fix it |
| Wrong fact posted | Pinned correction or delete, source downgraded | Alert with both options |
| Duplicate topic posted | Later one deleted, repeat rule tightened | Weekly note |
| Guess the Movie too hard or easy | Clue difficulty adjusted from the comment answer mix (1/2/3) | Weekly note |
| Harish wants a new series | Add a Series wizard → trial | Wizard cards |
| Lab invents a series | Pitch card → pilots as Trial Reels → graduate or kill | Pitch and result cards |
| Harish posts his own reel | Drop it into Drive `manual/`. It takes a slot and is tracked. | Today card |
| A week performs badly | L4 shifts the mix and runs more tests | Weekly Report explains |

---

## 20. Build phases and acceptance tests

| Phase | Work | Done when |
| --- | --- | --- |
| 0. Accounts | Harish completes `04_ACCOUNTS_CHECKLIST.md` | All secrets set; the Claude GitHub App is installed on the repo |
| 1. Smoke tests | Repo skeleton, Drive bridge, **voice from the cloud test**, OpenAI test image, Instagram test publish to a private test (or a Trial Reel), clip fetch test | Each prints OK in an Actions run |
| 2. Templates | Card, Cinematic, Diorama, matched to the samples | Recreate the Kaithi breakdown, the VJS Second Tier viral and the Kaithi Guess the Movie from plan files. Harish says "same quality or better". |
| 3. Brain runs | 5 scheduled tasks + API trigger, prompts in `03_KICKOFF_PROMPT.md` (section B) | One full dry day produces 6 plans that pass schema and virality checks |
| 4. Rehearsal | 3 full days, reels go to Drive `rehearsal/` and are not posted | 18 reels, at least 16 pass QC, Brain usage within Pro, OpenAI spend on track for ₹500 |
| 5. Go live | 3 a day for a week, then 6 | Posting runs a week with no manual fix |
| 6. Loops on | L4 weekly after 2 weeks of data. L5 after 4 weeks. | First Weekly Report and first Lab pitch delivered |

---

## 21. Open items

1. Trusted source list (news sites and accounts).
2. Approve the story-slot starting mix (Guess 4 days, Viral 3 days).
3. Display name change and new bio (suggested: "Tamil cinema, broken down. Daily breakdowns, updates and Guess the Movie.").
4. Royalty-free music library preference (or let the system pick).
5. Whether to make the repository public later, for unlimited free Actions minutes. Keys stay secret either way, but plans and code become visible.
