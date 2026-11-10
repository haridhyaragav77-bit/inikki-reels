# Control Room card library

Every card is drawn with the Visualizer in the iNiKKi style: clean white card, small coloured series badges (Breakdown gold, Update teal, Guess ticket-yellow, Viral amber, Review violet, Artwork soft gold, Breaking red), and at most 4 buttons. Each button calls `sendPrompt("<command>")` with the exact command text below. Every number on a card comes from a Drive file. A missing value shows as "—", never a guess.

| Card | Shows when | Reads | Content | Buttons → command |
| --- | --- | --- | --- | --- |
| **Today** | "hi", "status", "today" | status/today.json, status/budget.json, status/alerts.json | Date, day type (normal/event/away/respect), 4 tiles (Posted x of y, Ready, Held, Images ₹ spent of cap), one row per reel: time · badge · title · state pill | Tomorrow → "Show the Tomorrow card" · Voice session → "Show the Voice Session card" · Refresh → "Refresh the Today card" · Pause all → "Pause all posting" |
| **Tomorrow** | "tomorrow" | plans/ for tomorrow via status/tomorrow.json | Planned reels with lead scores and virality totals, reserves count | Swap a reel → "Swap a reel tomorrow" · Back to today → "Show the Today card" |
| **Reel** | Tapping or naming a reel | status/today.json, data/metrics | Frame strip (4 thumbnails), hook, caption, post time, why it was picked (lead + trend), virality factors, metrics if posted vs series median | Pull it → "Pull reel <id>" · Post now → "Post reel <id> now" · Swap meme → "Swap the meme in <id>" · Why? → "Explain reel <id>" |
| **Voice Session** | 7:30–9:30 PM in laptop mode, or on request | status/voice.json | Scripts waiting, total minutes, lines flagged for redo | Start session → "Start the voice session" · Audio uploaded → "Audio uploaded, continue" · Skip tonight → "Skip tonight and use silent versions" |
| **Audio Received** | After upload | status/voice.json | Files received x of y, sync check, names to listen to, ready-by time | Play flagged line → "Play the flagged line" · Tomorrow → "Show the Tomorrow card" |
| **Leads** | "leads" | state/lead_queue.json mirror | Top leads per slot with score and trend tag, 2 reserves each | Bump → "Bump lead <id>" · Drop → "Drop lead <id>" (both optional; no answer = system decides) |
| **Trends** | "trends" | status/trends.json | Rising, peak and fading topics with which series will use them | Use more → "Use trend <id> more" · Avoid → "Avoid trend <id>" |
| **Series Manager** | "series" | series settings mirror | One tile per series: status, per day, 4-week score vs page median, cost per reel | Edit rules → "Edit series <id>" · Pause → "Pause series <id>" · Add a series → "Add a new series" |
| **Add a Series** (wizard, 6 steps) | "Add a new series" | — | 1 name + idea · 2 how often · 3 template (Card, Cinematic, Diorama, New) · 4 voice yes/no · 5 clips, images or both · 6 example reels or links. Then a preview. | Next / Back / Start trial → "Start trial for <name>" |
| **Series Pitch** (Lab) | New pitch in lab/pitches | lab/pitches/*.md | Name, idea, why now (numbers), template, cost per reel, 3 sample hooks, pilot plan | Run it → "Run pitch <id>" · Veto → "Veto pitch <id>" · More like this → "More pitches like <id>" |
| **Lab Result** | Pilot finished | lab/results | Pilot metrics vs median, verdict (graduate/kill/one more) | Graduate → "Graduate <id>" · Kill → "Kill <id>" |
| **Meme Bank** | "memes" | memes index mirror | Top memes by result, new memes in inbox, overused memes | Show by mood → "Show memes by mood" · Retire → "Retire meme <id>" · Add memes → "How do I add memes" |
| **Weekly Report** | Mondays, or "weekly" | status/weekly_report.json | Best 3 and worst 3 reels, what the system changed and why, story-slot mix, costs (images ₹, Brain usage), Lab status | Undo a change → "Undo change <id>" · Details → "Show weekly details" |
| **Budget** | "budget" | status/budget.json | Images this month ₹ vs ₹500, per series, forecast to month end, Actions minutes, Brain runs status | Change cap → "Change image cap" |
| **Alert** | status/alerts.json has an open item | status/alerts.json | What broke, what the system already did, what Harish needs to do | Fix it → "Fix alert <id>" · Explain → "Explain alert <id>" · Snooze → "Snooze alert <id>" |
| **Confirmation** | After any setting change | changes/log.md | One line: what changed, from when | Undo → "Undo last change" |
| **Change Request** | After a feature ask | requests/*.md | What, why, what it affects, status (queued, building, testing, live) | Cancel → "Cancel request <id>" |
| **Celebration** | A reel is rising | status/alerts.json | Reel, how far above median | Make part 2 → "Make part 2 of <id>" · Pin a comment → "Pin a comment on <id>" |

## Layout rules
- Header: card title (left) and a status badge (right).
- Body: tiles first (numbers), then rows (reels, leads, series).
- Buttons in one row, wrapping on phones. Labels 1–3 words, sentence case, with a ↗ arrow.
- Works in light and dark mode. Readable on a phone (the Control Room will often be opened on mobile).
