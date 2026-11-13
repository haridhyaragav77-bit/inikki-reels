# Templates and the plan form

One plan file makes one reel: `node engine/render/render.mjs plans/<date>/<reel>.json`.
It writes the voice, mixes the music, animates every frame, encodes the MP4 and runs the checks (AGENT.md stage 8).
Examples for every series are in `plans/2026-11-13/`.

## Plan: common fields
| Field | Meaning |
| --- | --- |
| `id`, `series`, `template` | Reel id, series id, look (`stage`, `bulletin`, `poster-wall`, `verdict`, `flash`) |
| `length_s` | Allowed length for the checks; over 45 s needs `length_reason` |
| `lead`, `worth_it` | Topic, insight, sources, and the worth-it answers (AGENT.md 5.7) |
| `voice` | `{ "on": true, "voice": "ta-IN-ValluvarNeural", "rate": "+33%", "pitch": "-2Hz" }` or `{ "on": false }` |
| `music.sections` | 1–3 parts that follow the story: `{ "track", "from" (seconds into the track), "screen" (where it starts), "mood" }`. Music starts on frame 1. |
| `assets` | Stills: `{ "src": "engine/.cache/stills/...", "crop": [x, y, w, h] }` (crop in 0–1, used to cut baked-in trailer text) |
| `screens` | The reel, screen by screen (below) |
| `package` | Caption lines, hashtags, cover title, slot, first comment |

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
| `stage` (Film Breakdown) | `title` (film, type, image) · `pins` (still + label pins + slam lines + optional `extra` still) · `loop` (4-node story loop) · `cards` (question cards with stills) · `moral` (black / white / grey hero moment) · `standoff` (still + particle "?" + slam) · `end` |
| `bulletin` (Movie Updates) | `title` (still or `band`, big lines) · `number` (count-up money) · `bars` (comparison bars) · `ladder` (milestone climb) · `end` |
| `poster-wall` (Watch This Next) | `title` (fanned posters + 2 lines) · `film` (poster, number, title, meta, director, reason) · `recap` (2×2 list + save prompt) |
| `verdict` (Movie Review) | `title` · `stamp` (verdict stamp) · `scale` (works vs doesn't) · `critics` (named quote cards) · `who` (watch it if you love) · `end` |
| `flash` (Breaking News) | `title` (film + what) · `date` (calendar flip) · `team` (name blocks) · `fact` (two big lines) · `end` |

Every `end` screen takes `echo` (screen 1 again), `question` lines, `cta` and an optional `sub`.

## Files
- `templates/_shared/runtime.js` — timing, easing, images, kinetic text, particles, light, transitions (frames are computed from time only, so renders repeat exactly)
- `templates/_shared/motion.js` — shared motion graphics: end card, ticket mascot, label pins, particle shapes, count-ups, chips
- `templates/<look>/template.js` — each series' own look and screen kinds
- `engine/render/audio.py` — voice (word timings), music sections, ducking, sound effects, timeline
- `engine/render/check_reel.py` — the stage 8 checks
- `engine/tools/` — music energy profile, official stills fetcher, contact sheet
