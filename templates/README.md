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
| `lead.point` (breakdowns) | The reel's one point in one sentence, 25 words at most: what the viewer knows after watching (AGENT.md 5.7, from 23 Nov) |
| `src` (screen, breakdowns) | Where the screen's fact comes from: the number of a link in `lead.sources` (from 0), a list of them, or `"analysis"` for our own reasoning with no new fact. Every screen except the end. |
| `beat` (screen, breakdowns) | Plans before 23 Nov only: where the screen sat on the old spine (hook, lead, body, loop, cta) |
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
| `stage` (Film Breakdown, Trailer Breakdown) | `title` (film, type, image; TURN SOUND ON appears by itself when the voice is on) · `timeline` (`heading`, `events`: 2-5 of `{label, sub, cue}`, `links`: `[[0, 3]]` draws setup → payoff, `footer`) · `meter` (`heading`, `label`, `levels`: `{label, value 0-100, cue}`; the top level shakes the frame) · `versus` (`left` / `right`: `{image, label, sub, cue}`, `tilt` -1 or 1 with `tilt_cue`, `slam_text` with `slam_cue`) · `web` (`heading`, `center`: `{label, image}`, `nodes`: 3-6 of `{label, image, link, cue}`, `footer`) · `pins` (still + label pins + slam lines + optional `extra` still) · `technique` (the named technique: `kicker`, `name`, `definition`, `outer_label`, `inner` boxes) · `loop` (4-node story loop) · `cards` (question cards with stills) · `moral` (black / white / grey hero moment) · `standoff` (still + particle "?" + slam) · `detail` (`image`, `spot` {x, y} 0-1 in the frame, `zoom`, `cue`, `label` ≤3 words, `label_cue`, `count` [n, of], `heading`: a lens finds the detail) · `chain` (`heading`, `steps`: 3-5 of `{label, cue}`, the last is the payoff) · `quote` (`image` optional portrait, `name`, `role`, `phrase` ≤6 words, `source` e.g. "SIFY · 2017", `cues`: {name, phrase}) · `source` (`heading`, `left` / `right`: `{title, beats: 2-4 of {label, cue}}`, `links`: `[{from, to, cue}]` counted from 0, `slam_text`, `slam_cue`) · `board` (`heading`, `center` {label, sub, image}, `clues` 3-5 of {label, sub, image, cue}, `slam_text`, `slam_cue`: an evidence board with red string) · `climb` (`heading`, `phases` 1-2 of {dir: up|down, label, sub, cue}, `steps`, `rain`, `slam_text`: a staircase a figure climbs or dances down) · `track` (`heading`, `shape` circuit|route or `points`, `lap`, `start_cue`, `markers` [{at 0-1, label, cue}], `speed` {from, to, unit, cue}: a car laps a circuit) · `layers` (`heading`, `layers` 2-4 of {label, sub, cue} bottom first, `split_cue`, `slam_text`: slabs stack, then lift apart) · `scene` (the scene builder, below) · `end` |
| `bulletin` (Movie Updates) | `title` (still or `band`, big lines) · `number` (count-up; `unit` e.g. " CR", " NOV", " DAYS"; ₹ appears only for money units, or set `money: true|false`) · `bars` (comparison bars) · `ladder` (milestone climb) · `end` |
| `poster-wall` (Watch This Next) | `title` (a moving wall of the films' posters, the 2 `lines` big in the middle, a `kicker` above them, an optional `tag` below) · `film` (poster, number, title, meta, director, reason; with `plot` and `plot_beats` the card lifts and the plot is told in 2-3 beats from `plot_at`, default about 3 s in) · `recap` (2×2 list + save prompt) |
| `verdict` (Quick Review, Trusted Review) | `title` · `stars` (from 23 Nov, right after the title: `heading`, `score`, `out_of` 5, `verdict` GO/WAIT/SKIP, `line`, `basis`, `land`: five stars fill to the score, the number counts up, the answer stamps down) · `stamp` (verdict stamp) · `scale` (works vs doesn't) · `critics` (named quote cards; `rating` shows each critic's own stars or word) · `who` (watch it if you love) · `end`. The plan carries `rating`: `{kind: quick|trusted, critics: [{name, outlet, stars 0-5 or verbal (rave, positive, mostly_positive, mixed, mostly_negative, negative, pan), quote, src}], score, verdict}`; the plan check works out the score and the answer (knowledge/critics.yaml). Examples: `plans/reference/review-quick.json`, `review-trusted.json` |
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

## The scene builder (`stage` kind `scene`, AGENT.md 5.8)
The custom visual for one film, described in the plan: drawn props in a box (x and y from 0 to 1; the ground line is at y 0.8),
moving and acting on the words the voice says. Example: `plans/reference/breakdown-scene-viduthalai.json` (a camera glides through
train coaches; the last coach falls off a bridge; a counter runs to 8 MIN).

| Field | Meaning |
| --- | --- |
| `heading` | Words at the top (3-6) |
| `ground` | `floor` (default), `road`, `rail`, `water`, `city`, `sky`, `map` (a top-down floor plan), `grid`, `none`; `scroll` moves a road or rail (px a second) |
| `props` | 1-8 of `{id, icon, x, y, size (1 = 160 px), count (copies in a row, e.g. coaches), gap, flip, color (accent, second, white, red), label (≤3 words), label_at (below, above), cue (when it appears), enter (pop, drop, slide, rise, fade)}` |
| moving | `path`: 2-8 points `[x, y]`; `move` seconds; `move_cue`; `trail` (the path draws on, default on); `face` (turns along the path); `loop` |
| `acts` (on a prop) | `{do, cue}`: `fall` (drops off with a tilt), `shake`, `blast` (ring, sparks, flash), `light` (glows gold), `spin`, `grow` (`to`), `fade`, `pulse`, `swap` (`icon`: becomes another icon); `copy` picks one copy of a `count` row |
| `links` | `{from, to, cue, style (line, string = red evidence string, beam = a light cone, arrow), label}` between two props' ids |
| `focus` | `{on: a prop id or [x, y], to: 1.1-1.8, cue, d}`: the camera pushes in |
| `counter` | `{from, to, unit, cue, d, x, y}`: a number counts up; no ₹ unless the unit is crore or lakh |
| `slam_text`, `slam_cue` | The punch line, slammed in under the box |

Icons (drawn, facing right): camera, film, clapper, mic, spotlight, screen, person, runner, crowd, car, racecar, bike, train,
coach, plane, boat, bridge, building, house, tree, mountain, sun, moon, star, cloud, rain, fire, bomb, blast, gun, knife, phone,
clock, hourglass, heart, eye, crown, key, lock, door, book, letter, note, trophy, flag, skull, mask, throne, ball, ticket,
question, exclaim, check, cross, arrow, target, pin, dot. A new icon is added in the Workshop (template and plan check together).
To see a plan's frames anywhere, without keys: `python -m engine.render <plan> --local --snap 1,4,8`.
