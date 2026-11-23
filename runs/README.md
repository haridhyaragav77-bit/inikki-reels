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

## The clock (GitHub metronome) and the dispatcher (made fresh every day)
The timed jobs are started by the GitHub metronome (`tools/metronome.py`), from the "clock" list in `runs/renew/tasks.json`.
No Claude chat is involved. The dispatcher's rules and its scheduled tasks live in `runs/renew/` (`dispatcher.md`,
`tasks.json`). Every day at 03:17 IST the task "iNiKKi · Daily fresh chats" sends `RENEW` to the small renewer chat
(`runs/renew/renewer.md`), which follows `runs/renew.md`: a new dispatcher, its tasks moved, the old ones removed, and a new
renewer. Change those files, not the scheduled tasks by hand. To see what the chats cost: skill `token-audit`.
