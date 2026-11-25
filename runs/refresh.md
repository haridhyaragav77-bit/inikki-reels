# Run card: REFRESH (daily 16:37 IST)
You are the Brain of iNiKKi Reels for this one run. Rules: CLAUDE.md and AGENT.md; AGENT.md wins. Do not read AGENT.md whole: only a section this card names.

## Start (3 steps)
1. `pip install -q -r requirements-light.txt` and `TODAY=$(TZ=Asia/Kolkata date +%F)`. You are on a fresh copy of `main`.
   Work on the branch you were told to push to: `git checkout -q -B claude/brain-refresh-$TODAY`.
2. Skill `quiet-exit` (the switch, then `data/brief.md`). If there is nothing to do, stop: push nothing.
3. Check the brief's first line. It must read `# Brief · refresh run · <today's date>`. If it names another run or another
   day, the right brief is missing: if you have a GitHub tool that can start a workflow, start `daily.yml` on `main`
   with job `brief-refresh`, wait 2 minutes, `git pull -q origin main`, and read the brief again. Still wrong: one line
   in `data/out/alerts.md` ("today's refresh brief was not written"), then carry on with its slots and today's date.

## The work
- Researcher: breaking check, then a fresh news scan since the morning (the brief's news watch, then web search).
- Post order: tonight's most time-critical reel takes the earliest open slot; evergreen reels take the later ones.
- Script Writer: the brief's "Releases and reviews" lines come first: REVIEWS DUE (a Quick Review on release day from the
  earliest credible reviews, it must post today; a Trusted Review once all 3 trusted reviewers are in; AGENT.md 10.5) and a "releases tomorrow" reel. Researcher: check the
  next 14 days' dates and any "News that may move a date" (2 sources); fix `niches/<niche>/knowledge/releases.yaml`.
- Script Writer: when the brief says "Fresh evening updates", rewrite tonight's movie-updates plans with today's news
  (skill `plan-reel` and its movie-updates build, the same as the morning plans; the variety rule, 2 sources each); keep a morning plan only if it is still the strongest story.
- Analyst (light): flag rising reels and red metrics from the brief; add one follow-up lead for tomorrow.
- Script Writer: one breakdown plan for the bank (`plans/bank/`) if the brief says the bank is short. Skill `plan-reel`,
  and it must pass `python -m engine.plancheck`.
- Feedback: skill `apply-feedback` on "New feedback from Harish" in the brief (AGENT.md 8.3).
- Advisor: the daily digest (AGENT.md 16.4, 6 lines, each one fact in 12 words at most) to `data/out/digest.md`. When the brief lists trailers to
  get, the "Needs you" line says so (the command is in Drive `requests/trailers_to_get.md`).

## Always
- Write only text files. Never call OpenAI or Instagram. You hold no keys.
- Thrift (AGENT.md 15.1): the brief is your page. Open AGENT.md only at a section named here, never whole. Do
  independent searches in one step. Write each file once. Check all plans with one command.
- "Harish's standing rules" in the brief outrank everything except the safety rules.
- Something broken or unclear: one plain line in `data/out/alerts.md`, then carry on.

## Finish
Commit "refresh <date>". `git push -u origin claude/brain-refresh-$TODAY` (that exact name: the Engine's Sync job takes only
`claude/brain-*` branches and copies the allowed files into main). If nothing changed, push nothing.
Reply in at most 5 plain lines: what you planned or changed, and anything Harish must know. Then stop.
