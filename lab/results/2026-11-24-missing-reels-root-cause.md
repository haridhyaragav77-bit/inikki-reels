# Why only 1 of 6 reels was made on 24 Nov 2026, and why failures kept coming back

## What happened today
| Time (IST) | What | Result |
| --- | --- | --- |
| 05:12 | Brief for the Plan run | Fine: asked for 6 reels and 2 reserves |
| 05:37 | Plan run (Claude) | Wrote **1** plan (08:30 O.M on Netflix) and stopped. Its note: "no fresh news with 2 sources" for the 3 other updates; the bank breakdowns "fail today's check", so no breakdowns; no reserves |
| 05:40 | Make job | Made the 1 plan it was given. Nothing failed: there was nothing else to make |
| 11:00 | Post job | "nothing due". 4 finished bank reels were ready, but none was used |

Nothing crashed today. The day was empty because of two gaps that line up:

1. **The Plan run was allowed to give up.** Its instructions said what to plan, but not what to do when the news is thin.
   After about 13 searches it planned 1 reel and stopped. Updated bank plans would have needed fixing for the 23 Nov
   breakdown rules (scene visual, cooling graphics), and it chose to skip them instead.
2. **The safety net had a hole.** The design (AGENT.md 20, "Quiet news day") says weak updates are swapped for bank
   breakdowns. The code did this only when a *planned* reel failed. A slot with *no plan at all* was left empty,
   so 5 slots were silent while 4 bank reels sat ready.

## Why failures keep coming back (the root cause)
Looking at the last week: 23 Nov the refresh brief crashed twice (a Python name used before it was set, only on days
with a new trailer in the library); 22 Nov the study job broke (a library update); 22 Nov the inbox 403 repeated every
job; 16 and 22 Nov the brief re-showed old feedback. Each was fixed after it hurt a real day.

**The common cause: nothing ran the Engine's tests before a change went live.** The repository has 8 test files and all
of them pass without any keys, but on every push only the Guard's own test ran. CLAUDE.md rule 3 ("merge only when
tests pass") depended on a person remembering to run them. A bug that shows only on some days (like the 23 Nov one)
then reached main and was found when a day's reels were missing.

## Fixes
| Gap | Fix | Where |
| --- | --- | --- |
| Changes go live untested | Every push and pull request now runs **all** Engine tests plus a code check that finds names used before they are set (the 23 Nov kind of crash). A pull request that fails cannot be merged by the Workshop rules | `.github/workflows/guard.yml`, `tools/check_code.sh` |
| The brief was never tested | New test builds the brief for all 5 runs with a fake Drive and a fresh trailer; it fails on the old code with the exact 23 Nov error | `tests/test_brief.py` |
| 23 Nov crash | `dayplan` imported once at the top (no hidden local imports); same tidy in `make.py`; one more fragile spot fixed in `sources.py` | `engine/brief.py`, `engine/make.py`, `engine/sources.py` |
| Empty slot stays empty | At each slot time, a slot with no reel is filled by a ready reserve, else a ready bank reel (up to 60 min late) | `engine/post.py` `fill_empty_slot`, AGENT.md 20 |
| Plan run gives up | "Fill the day": fallbacks in order (lower-ranked news, the checked release calendar, an evergreen reel), fix a bank plan instead of dropping it | `runs/plan.md` |

## How to know it works
- `bash tools/check_code.sh` passes (9 test files, code check clean).
- Today: once this is on main, the 12:30, 18:00, 20:00 and 21:30 post runs fill their empty slots from the 4 ready bank reels.
