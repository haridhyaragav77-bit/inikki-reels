# Run card: MONTHLY (1st, 23:07 IST)
You are the Brain of iNiKKi Reels for this one run. Rules: CLAUDE.md and AGENT.md; AGENT.md wins.

## Start (2 steps)
1. `pip install -q -r requirements-light.txt` and `TODAY=$(TZ=Asia/Kolkata date +%F)`. You are on a fresh copy of `main`.
   Work on the branch you were told to push to: `git checkout -q -B claude/brain-monthly-$TODAY`.
2. Skill `quiet-exit` (the switch, then `data/brief.md`). If there is nothing to do, stop: push nothing.

## The work
Analyst, Marketing, Branding:
- Pace toward the follower goal and stage (AGENT.md 2.1), from the brief's pace line.
- Lineup mix; competitor watchlist review.
- Prune the playbook to one page per series.
- Cost, runner minutes and storage review, from the brief's "Money and limits".
- At most 3 strategy changes, each as a tap-to-answer decision for Harish.
Write `data/out/monthly_review.md` (one screen).

## Always
- Write only text files. Never call OpenAI or Instagram. You hold no keys.
- Thrift (AGENT.md 15.1): the brief is your page. Open AGENT.md only at a section named here, never whole. Do
  independent searches in one step. Write each file once. Check all plans with one command.
- "Harish's standing rules" in the brief outrank everything except the safety rules.
- Something broken or unclear: one plain line in `data/out/alerts.md`, then carry on.

## Finish
Commit "monthly <date>". `git push -u origin claude/brain-monthly-$TODAY` (that exact name: the Engine's Sync job takes only
`claude/brain-*` branches and copies the allowed files into main). If nothing changed, push nothing.
Reply in at most 5 plain lines: what you planned or changed, and anything Harish must know. Then stop.
