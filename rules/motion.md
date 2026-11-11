# Motion graphics library (AGENT.md 5.7)

One rule above all: **the graphic shows what the voice is saying right now.** With the sound off, the viewer should still get the point. If a graphic could sit on any reel, pick another.

How to choose: read the line, name the *kind* of point it makes (time, pressure, place, want, number, fact, comparison), and take the graphic in that row. One graphic per screen. It starts with the line and finishes before the line ends.

## Subtitles (every template)
- Every spoken line is on screen twice: **Tanglish** (English letters) on top, **Tamil script** under it.
- In a plan: `caption` is the Tanglish line, `voice_line` is the Tamil line that is spoken.
- Words light up as they are spoken. Keep a line to about 6 words, so it stays on one row.
- Reels without voice (stories, Guess the Movie) still give every text beat in both: an English or Tanglish line and a Tamil line.

## Card template (Updates, Breakdowns, Reviews, Breaking)
Set on a screen as `"motion": { "type": "<name>", ... }`.

| Name | What the viewer sees | Use it when the line says | Fields |
| --- | --- | --- | --- |
| `punch` | One or two big words punch in under the clip | The hook question. One key word. | `text`, `color` (teal or gold) |
| `points` | Numbered boxes appear one at a time. The one being talked about lights up. Finished ones get a tick. | "Three things." Naming the parts. Moving to point 2. | `items` (2–4), `active` (which one is being discussed), `build` (true the first time) |
| `timer` | A clock hand sweeps and a "time left" bar drains. A second bar can climb. | A deadline. Time running out. | `time` [from, to] as 0–1, `rise` [from, to], `labels` |
| `tension` | A line draws itself upward with a glowing head. Peaks can be named. | Suspense building. Stakes rising. A twist. | `points` (heights 0–1), `peaks` (names at a point) |
| `switch` | Place tabs. A "cut" streak jumps from one to the other. The place left behind keeps blinking. | The film cuts between places. Something is left hanging. | `places` (2–3), `from`, `to`, `pending` (label on the place left behind) |
| `goal` | A person, a goal, and a track between them. Barriers drop onto the track one by one. | A character wants one thing and keeps being stopped. | `who`, `goal`, `blocks` (names of the barriers, or a number) |
| `list` | Stacked bars build a recap | Summing up. "So remember." | `items` (up to 4), `from` (how many are already showing) |
| `count` | A big number counts up to its value | Money, days, views, years | `to`, `from`, `prefix`, `suffix`, `label` |
| `timeline` | Dated stops on a line. A marker travels to the current one. | Announced → shoot → release. Then and now. | `stops` (each: `label`, `sub`), `from`, `at` |
| `status` | Fact rows with a tick (confirmed), dots (awaited) or a cross (not true) | News: what is confirmed and what is not | `rows` (each: `label`, `state` yes / wait / no, `value`) |
| `versus` | Two names and a balance that tilts | Comparing two craft choices. Never star against star. | `left`, `right`, `tilt` (-1 to 1) |
| `quote` | Quote marks, the line, who said it | Quoting a person or a critic | `text`, `by` |
| `cast` | Name chips pop in as they are named | Who is in it. The team. | `names` (up to 4), `roles` |
| `callout` | A ring draws around a detail inside the clip, with a label | "Look at this." A prop. A framing choice. | `at` [x, y] as 0–1 inside the clip, `label` |
| `cta` | The mascot and the send pill | The last screen | `text` |

A screen may add one `callout` to another graphic: `"motion": [ {...}, {"type": "callout", ...} ]`. Never more than two.

## Cinematic template (Viral Story, Artwork + Quote)
Each beat has a kicker, a white line, a gold headline and a Tamil line. Set `"motion"` on a beat:

| Name | What the viewer sees | Use it when the beat is |
| --- | --- | --- |
| `slam` (default) | The gold headline lands hard, the Tamil line follows | Any beat |
| `count` | The number in the headline counts up to its value | Money, years, counts: the hook or the turn |
| `stamp` | One word is stamped at an angle just above the words, never on a face | A rejection, a verdict, a result (`stamp`: the word) |
| `underline` | A gold line sweeps under the key word (mark it with `*stars*`) | The one word the beat turns on |
| `reveal` | The picture dims, then the name lands with a flash: line "None other than", headline = the name | The name reveal near the end of every story |
| `question` | The last line grows and holds, with the send pill | The final beat |

Pictures move too: a slow push, pull or drift, with near and far parts of the picture moving at different speeds. Set `move` on an image only when the story needs it (`push`, `pull`, `left`, `right`).

## Diorama template (Guess the Tamil Movie)
The screens are fixed kinds, in this order: `title`, `clue` (three of them), `countdown`, `reveal`. Each clue scene has depth: near objects drift faster than far ones, with fog, dust and a moving light. The countdown ring ticks 3-2-1 with sound. The reveal lands the title and year.

## Visual hooks (every template, AGENT.md 5.8)
The first second of every reel. Set on a plan as `"hook": "<name>"`; if a plan gives none, the series card's hook is used. Pick the one that fits the film or story.

| Name | What the viewer sees | Fits |
| --- | --- | --- |
| `thunder` | Two lightning strikes, the frame lights up cold and shakes | Thrillers, horror, night stories, Guess the Movie |
| `flare` | A bright headlight streak crosses the frame | Road films, action, big announcements |
| `impact` | The frame punches in hard with a shock ring | Breaking news, a strong claim |
| `spotlight` | Darkness, then a spotlight snaps on | Stories about people, reviews, stage and theatre |
| `clap` | A clapperboard snaps shut and flies off | Breakdowns, filmmaking topics |

## Transitions (every template)
A new picture never fades in plainly. Card: a flash cut inside the frame. Cinematic: the new picture arrives on a flash and settles. Guess the Movie: the camera whips sideways to the next clue. Each has its sound.

## 3D scenes (Guess the Tamil Movie)
Each clue picture becomes a real 3D scene. Set on an image: `move` and `weather`.

| `move` | What the camera does | Use it for |
| --- | --- | --- |
| `push` | Travels into the scene | The title and the first clue |
| `track` | Slides sideways past the subject | Vehicles, streets, long objects |
| `orbit` | Circles slowly around the subject | A building, a single object |
| `crane` | Comes down from above | An establishing view |
| `pull` | Backs away | A reveal of the surroundings |

`weather`: `rain`, `dust` or `embers`, inside the scene. Lightning from the hook and the reveal lights the scene itself.

## Timing
- Parts of a graphic appear in the order the voice names them, spread across the spoken line.
- Small sounds land with each move (tick, pop, soft hit). They sit well under the voice.
- A picture change and a graphic change never fight: the picture changes first, the graphic follows a beat later.

## Adding a graphic
A new kind is a build request (Control Room → "new feature"). It is added here with its row only after it passes the golden-reel test.
