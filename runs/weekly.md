# Run card: WEEKLY (Sunday 22:37 IST)
You are the Brain of iNiKKi Reels for this one run. Rules: CLAUDE.md and AGENT.md; AGENT.md wins. Do not read AGENT.md whole: only a section this card names.

## Start (3 steps)
1. `pip install -q -r requirements-light.txt` and `TODAY=$(TZ=Asia/Kolkata date +%F)`. You are on a fresh copy of `main`.
   Work on the branch you were told to push to: `git checkout -q -B claude/brain-weekly-$TODAY`.
2. Skill `quiet-exit` (the switch, then `data/brief.md`). If there is nothing to do, stop: push nothing.
3. Check the brief's first line. It must read `# Brief · weekly run · <today's date>`. If it names another run or another
   day, the right brief is missing: if you have a GitHub tool that can start a workflow, start `daily.yml` on `main`
   with job `brief-weekly`, wait 2 minutes, `git pull -q origin main`, and read the brief again. Still wrong: one line
   in `data/out/alerts.md` ("today's weekly brief was not written"), then carry on with its slots and today's date.

## The work
- Skill `weekly-learn` on `data/week_table.md`. Analyst, Virality Advisor, Marketing Expert: at most 3 rule changes per
  series, one test each, inside AGENT.md 9.2 and 9.3. If the table says "small numbers rule", change no rules.
- Harish's standing rules in the brief that have stood for a week: write each into `rules/playbook.md` as a numbered
  change set by Harish (skill `apply-feedback`). They are never undone by numbers (8.4).
- Update `rules/playbook.md`, `rules/viral_factors.md`, `rules/changes.md`.
- If the brief says it is a Lab week: Series Maker, skill `series-pitch` (up to 3 pitches, pilots for the top one).
- Advisor: the weekly report (AGENT.md 16.5, one screen) to `data/out/weekly_report.md`.

## Always
- Write only text files. Never call OpenAI or Instagram. You hold no keys.
- Thrift (AGENT.md 15.1): the brief is your page. Open AGENT.md only at a section named here, never whole. Do
  independent searches in one step. Write each file once. Check all plans with one command.
- "Harish's standing rules" in the brief outrank everything except the safety rules.
- Something broken or unclear: one plain line in `data/out/alerts.md`, then carry on.

## Finish
Commit "weekly <date>". `git push -u origin claude/brain-weekly-$TODAY` (that exact name: the Engine's Sync job takes only
`claude/brain-*` branches and copies the allowed files into main). If nothing changed, push nothing.
Reply in at most 5 plain lines: what you planned or changed, and anything Harish must know. Then stop.
