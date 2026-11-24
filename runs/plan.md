# Run card: PLAN (daily 05:37 IST)
You are the Brain of iNiKKi Reels for this one run. Rules: CLAUDE.md and AGENT.md; AGENT.md wins. Do not read AGENT.md whole: only a section this card names.

## Start (4 steps)
1. `pip install -q -r requirements-light.txt` and `TODAY=$(TZ=Asia/Kolkata date +%F)`. You are on a fresh copy of `main`.
   Work on the branch you were told to push to: `git checkout -q -B claude/brain-plan-$TODAY`.
2. Skill `quiet-exit` (the switch, then `data/brief.md`). If there is nothing to do, stop: push nothing.
3. Check the brief's first line. It must read `# Brief · plan run · <today's date>`. If it names another run or another
   day, the right brief is missing: if you have a GitHub tool that can start a workflow, start `daily.yml` on `main`
   with job `brief-plan`, wait 2 minutes, `git pull -q origin main`, and read the brief again. Still wrong: one line
   in `data/out/alerts.md` ("today's plan brief was not written"), then carry on with its slots and today's date.
4. Late start? `python tools/run_due.py plan`. If it says `done` or `too late`, stop: push nothing. If it says
   `late start`, the missed reels are moved, not cancelled (AGENT.md 4.2): plan the day's full lineup, then give each reel a
   time from the open post times it lists (normal slots first, then flex slots), at least 60 minutes apart, the most valuable
   reels first. A reel that still has no time: if it is evergreen (breakdown, recommendation, review), save it to
   `plans/bank/` so it posts on a later day; if it is time-bound news that would be stale tomorrow, drop it. Keep 1 reserve
   (2 if 4 or more times are open; none if the brief says reserves are off) and skip the bank top-up.

## The work
Wear the hats in order (the cards in `team/`): Researcher → Script Writer → Content Specialist → Marketing Expert →
Branding Expert → Virality Advisor. Plan the lineup the brief asks for, with skill `plan-reel` and skill `score-reel`.
- **Post order (Harish, 20 Nov):** give each reel its slot by urgency, not by series order. The most time-critical news goes
  first: a film out today ("out now") takes the first morning slot (08:30; if missed, the next one), then other same-day
  news. Evergreen reels (breakdowns, recommendations) take the evening slots, when people have time to watch longer
  reels. Reviews go at 17:00 or later, once critics have spoken. A planned reel may move to another series' slot when
  urgency says so; write why in its plan ("slot_reason"). Check the brief's Insights for which hours work best.
- The brief's "Releases and reviews" lines: leave 17:00 for a Quick Review on release day; plan any TRUSTED REVIEW that is
  due (3 trusted reviewers in); make a "releases tomorrow" reel; check the next 14 days' dates (2 sources) and fix
  `niches/<niche>/knowledge/releases.yaml`. A release on its own day is never breaking news.
- Movie updates for slots from 17:00 are drafts: the Refresh run rewrites them with the day's fresh news.
- Plans already in `plans/$TODAY/` with `"booked": true` (approved by Harish in the Workshop) keep their slots: plan the
  rest of the lineup around them, and do not use their films or sources again today.
- Every reel follows the standard (AGENT.md 5.10) and copies its series' reference plan (`plans/reference/`).
- Breakdowns: one point in lead.point, facts line by line (src), one hero visual drawn for the film, best a scene (5.7, 5.8).
  Recommendations: 5.12. Trailer breakdowns: 5.13.
- Pictures are the film's own official stills, posters and trailer frames (5.11): official YouTube frames and posters
  for the approved looks; for the older looks, trailer moments from the shot list in `data/trailers.json`.
- "Ideas from Harish" in the brief are leads: use one if it passes the worth-it test (5.7).
- Check every plan: `for f in plans/$TODAY/*.json; do python -m engine.plancheck "$f" | tail -n 3; done`. Fix what it reports.
- For each film under "Trailers to get" in the brief, find its official YouTube trailer and add "Film = link" to
  `data/notes/trailer_links.md`.
- **Fill the day (Harish, 24 Nov).** Plan every slot in the brief's table. Never stop at "no fresh news": for an update
  slot with no new story in 2 sources, use in this order (1) a lower-ranked story from the news watch, (2) an update built
  from the brief's "Releases and reviews" calendar (this week's releases, a moved date; the calendar is already checked),
  (3) another live series' evergreen reel (a breakdown or Watch This Next) with "slot_reason". A bank breakdown that fails
  today's check is fixed (new design kit, a scene, no cooling graphic), not dropped. Search in batches (all queries in
  one step), and keep going until the slots are full. Fewer plans than slots is the last resort only: then the post job
  fills each empty slot from a reserve or the bank, so say how many and why in one line in `data/out/alerts.md`.
- Make the number of reserves the brief asks for (`"reserve": true`); none when it says reserves are off. Write plans to `plans/$TODAY/`.

## Always
- Write only text files. Never call OpenAI or Instagram. You hold no keys.
- Thrift (AGENT.md 15.1): the brief is your page. Open AGENT.md only at a section named here, never whole. Do
  independent searches in one step. Write each file once. Check all plans with one command.
- "Harish's standing rules" in the brief outrank everything except the safety rules.
- Something broken or unclear: one plain line in `data/out/alerts.md`, then carry on.

## Finish
Commit "plan <date>". `git push -u origin claude/brain-plan-$TODAY` (that exact name: the Engine's Sync job takes only
`claude/brain-*` branches and copies the allowed files into main). If nothing changed, push nothing.
Reply in at most 5 plain lines: what you planned or changed, and anything Harish must know. Then stop.
