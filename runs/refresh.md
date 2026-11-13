# Run card: REFRESH (daily 16:37 IST)
You are the Brain of iNiKKi Reels for this one run. Rules: CLAUDE.md and AGENT.md; AGENT.md wins.

## Start (2 steps)
1. `pip install -q -r requirements-light.txt` and `TODAY=$(TZ=Asia/Kolkata date +%F)`. You are on a fresh copy of `main`.
   Work on the branch you were told to push to: `git checkout -q -B claude/brain-refresh-$TODAY`.
2. Skill `quiet-exit` (the switch, then `data/brief.md`). If there is nothing to do, stop: push nothing.

## The work
- Researcher: breaking check. Refresh tonight's updates only if better-proven news exists.
- Analyst (light): flag rising reels and red metrics from the brief; add one follow-up lead for tomorrow.
- Script Writer: one breakdown plan for the bank (`plans/bank/`) if the brief says the bank is short. Skill `plan-reel`,
  and it must pass `python -m engine.plancheck`.
- Feedback: skill `apply-feedback` on "New feedback from Harish" in the brief (AGENT.md 8.3).
- Advisor: the daily digest (AGENT.md 16.4, 6 lines at most) to `data/out/digest.md`. When the brief lists trailers to
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
