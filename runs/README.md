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

## The clock and the dispatcher (made fresh every week)
Their exact rules and every scheduled task now live in `runs/renew/`: `clock.md`, `dispatcher.md`, `tasks.json`. Every
Monday 03:17 IST the task "iNiKKi · Weekly fresh chats" starts a session that follows `runs/renew.md`: new chats first,
then the tasks moved to them, then the old ones removed. Change those files, not the scheduled tasks by hand.
