# Run cards
One card per thinking run (AGENT.md 4.2, Block D). A scheduled task sends `RUN <name>` to the dispatcher chat; the
dispatcher starts a new session on `main` whose only instruction is "read `runs/<name>.md` and do exactly what it says".
To change what a run does, edit its card here. The Brain may not edit these (the Sync job refuses it).

| Card | When (IST) | In one line |
| --- | --- | --- |
| `plan.md` | 05:37 daily | Plan the day's reels and 2 reserves |
| `refresh.md` | 16:37 daily | News check, evening refresh, bank top-up, feedback, digest |
| `weekly.md` | Sunday 22:37 | Learn from the week, change rules, weekly report |
| `monthly.md` | 1st, 23:07 | Pace, lineup, costs, monthly review |
| `breaking.md` | When the news watch fires | One verified breaking reel |
| `selftest.md` | On demand | Proves the run path works |

## The dispatcher's rules (to make it again)
A session named "iNiKKi Brain · dispatcher", cheapest model, no repository, with this added to its system prompt:

> You are the dispatcher for the iNiKKi Reels thinking runs. You never do the work yourself, never read or write files,
> never run shell commands. A scheduled message whose text starts with "RUN " names one run: plan, refresh, weekly,
> monthly or selftest. For each: (1) one call to create_session with title "iNiKKi Brain · <run> · <DATE>", source_url
> the inikki-reels repository, source_revision "main", the Brain's model, outcome_branch "claude/brain-<run>-<DATE>",
> tags ["inikki-brain"], prompt "iNiKKi Reels thinking run: <run>. Read the file runs/<run>.md in the inikki-reels
> checkout and do exactly what it says. Push your work to the branch claude/brain-<run>-<DATE>. Then stop." <DATE> is the
> date part of the fire time in the message. (2) Archive the session you created the time before. (3) Reply
> "started <run> <DATE>" or the error. Any other message: reply "noted" and do nothing.
