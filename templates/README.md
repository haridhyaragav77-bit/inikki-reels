# Templates and the plan form

One plan file makes one reel: `node engine/render/render.mjs plans/<date>/<reel>.json` (the daily Make job does this through `python -m engine.make`).
It writes the voice, mixes the music, animates every frame, encodes the MP4 and runs the checks (AGENT.md stage 8).
Examples for every series are in `plans/reference/`.

## Plan: common fields
| Field | Meaning |
| --- | --- |
| `id`, `series`, `template` | Reel id, series id, look (`stage`, `bulletin`, `poster-wall`, `verdict`, `flash`) |
| `length_s` | Allowed length for the checks; over 45 s needs `length_reason` |
| `lead`, `worth_it` | Topic, insight, sources, and the worth-it answers (AGENT.md 5.7) |
| `voice` | `{ "on": true }` or `{ "on": false }`. The voice itself is a setting (AGENT.md 4.4): ElevenLabs first, Microsoft as backup. `voice`, `rate`, `pitch` in a plan are used only when the Microsoft voice speaks; `provider`, `elevenlabs_voice`, `speed` choose for this one reel. |
| `part` (breakdowns) | A film week's place, `[1, 3]`: PART 1/3 on the title and end screens (AGENT.md 5.7) |
| `design` (breakdowns) | The reel's design kit: `spotlight`, `blueprint`, `noir`, `neon`, `paper`, `forest`, `royal`. Not one of the last 3 breakdowns' kits. |
| `music.sections` | 1–3 parts that follow the story: `{ "track", "from" (seconds into the track), "screen" (where it starts), "mood" }`. Music starts on frame 1. |
| `assets` | Stills: `{ "src": "engine/.cache/stills/...", "crop": [x, y, w, h] }` (crop in 0–1, used to cut baked-in trailer text) |
| `screens` | The reel, screen by screen (below) |
| `package` | Caption lines, hashtags, cover title, slot, first comment |
| `drive_folder` | Where the finished reel goes in Drive (`rehearsal` until go-live, then `finished`); the date folder is added by itself |
| `beat` (screen, breakdowns) | Where the screen sits on the spine: hook, lead, body, loop, cta (AGENT.md 5.7) |
| `voice_tg` (screen) | The Tanglish line, word for word with the Tamil `voice`, for subtitles |

## Screen: common fields
| Field | Meaning |
| --- | --- |
| `kind` | The screen type for that template (below) |
| `voice` | Tamil line for this screen. The screen lasts as long as the line (plus `lead` / `tail`). Without voice, set `dur` in seconds. |
| `in` | How the screen arrives: `whip`, `push`, `zoom`, `flash`, `glitch`, `wipe`, `cut`. A matching sound plays by itself. |
| cues | `{ "word": "கேள்வி" }` lands a graphic on the word the voice says; `{ "at": 1.2 }` is seconds into the screen |
| `sfx` | Extra sounds: `{ "at": cue, "type": "impact" | "whoosh" | "stamp" | "tick" | "pop" | "riser" | "glitch" }` |

## Screen kinds per template
| Template (series) | Kinds |
| --- | --- |
| `stage` (Film Breakdown, Trailer Breakdown) | `title` (film, type, image; TURN SOUND ON appears by itself when the voice is on) · `timeline` (`heading`, `events`: 2-5 of `{label, sub, cue}`, `links`: `[[0, 3]]` draws setup → payoff, `footer`) · `meter` (`heading`, `label`, `levels`: `{label, value 0-100, cue}`; the top level shakes the frame) · `versus` (`left` / `right`: `{image, label, sub, cue}`, `tilt` -1 or 1 with `tilt_cue`, `slam_text` with `slam_cue`) · `web` (`heading`, `center`: `{label, image}`, `nodes`: 3-6 of `{label, image, link, cue}`, `footer`) · `pins` (still + label pins + slam lines + optional `extra` still) · `technique` (the named technique: `kicker`, `name`, `definition`, `outer_label`, `inner` boxes) · `loop` (4-node story loop) · `cards` (question cards with stills) · `moral` (black / white / grey hero moment) · `standoff` (still + particle "?" + slam) · `detail` (`image`, `spot` {x, y} 0-1 in the frame, `zoom`, `cue`, `label` ≤3 words, `label_cue`, `count` [n, of], `heading`: a lens finds the detail) · `chain` (`heading`, `steps`: 3-5 of `{label, cue}`, the last is the payoff) · `quote` (`image` optional portrait, `name`, `role`, `phrase` ≤6 words, `source` e.g. "SIFY · 2017", `cues`: {name, phrase}) · `source` (`heading`, `left` / `right`: `{title, beats: 2-4 of {label, cue}}`, `links`: `[{from, to, cue}]` counted from 0, `slam_text`, `slam_cue`) · `board` (`heading`, `center` {label, sub, image}, `clues` 3-5 of {label, sub, image, cue}, `slam_text`, `slam_cue`: an evidence board with red string) · `climb` (`heading`, `phases` 1-2 of {dir: up|down, label, sub, cue}, `steps`, `rain`, `slam_text`: a staircase a figure climbs or dances down) · `track` (`heading`, `shape` circuit|route or `points`, `lap`, `start_cue`, `markers` [{at 0-1, label, cue}], `speed` {from, to, unit, cue}: a car laps a circuit) · `layers` (`heading`, `layers` 2-4 of {label, sub, cue} bottom first, `split_cue`, `slam_text`: slabs stack, then lift apart) · `end` |
| `bulletin` (Movie Updates) | `title` (still or `band`, big lines) · `number` (count-up; `unit` e.g. " CR", " NOV", " DAYS"; ₹ appears only for money units, or set `money: true|false`) · `bars` (comparison bars) · `ladder` (milestone climb) · `end` |
| `poster-wall` (Watch This Next) | `title` (a moving wall of the films' posters, the 2 `lines` big in the middle, a `kicker` above them, an optional `tag` below) · `film` (poster, number, title, meta, director, reason; with `plot` and `plot_beats` the card lifts and the plot is told in 2-3 beats from `plot_at`, default about 3 s in) · `recap` (2×2 list + save prompt) |
| `verdict` (Movie Review) | `title` · `stamp` (verdict stamp) · `scale` (works vs doesn't) · `critics` (named quote cards) · `who` (watch it if you love) · `end` |
| `flash` (Breaking News) | `title` (film + what) · `date` (calendar flip) · `team` (name blocks) · `fact` (two big lines) · `end` |

Every `end` screen takes `echo` (screen 1 again), `question` lines, `cta` and an optional `sub`; a breakdown's end screen also takes `recap` ("TECHNIQUE: FRAME STORY"). The page name (@inikki_reels) is added by itself.

Check a plan before it is made: `python -m engine.plancheck <plan file>` (what it checks: `engine/plancheck.py`, `check_look`).

## Files
- `templates/_shared/runtime.js` — timing, easing, images, kinetic text, particles, light, transitions (frames are computed from time only, so renders repeat exactly)
- `templates/_shared/motion.js` — shared motion graphics: end card, ticket mascot, label pins, particle shapes, count-ups, chips
- `templates/<look>/template.js` — each series' own look and screen kinds
- `engine/render/audio.py` — voice (word timings), music sections, ducking, sound effects, timeline
- `engine/render/check_reel.py` — the stage 8 checks
- `engine/tools/` — music energy profile, official stills fetcher, contact sheet
