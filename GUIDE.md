# iNiKKi Reels · Your guidebook

How to run the agent without reading code. Every control, every loop, and the exact words to use.
Last updated 14 Nov 2026. The full design is `AGENT.md`; this guide is the short version you actually use.

## 1. The whole thing in one minute

| Part | What it is | What it does |
| --- | --- | --- |
| **Brain** | Claude, on a clock | Thinks. Picks topics, writes each reel's plan, learns from the numbers. Writes only small text files. |
| **Engine** | GitHub, on a clock | Does. Makes the reels, posts them, pulls the numbers, cleans up. Holds the keys. |
| **Drive** | Your folder "iNiKKi Reels" | The meeting point. Finished reels, your settings, the status file. |
| **You** | The Control Room | Look, preview, steer. Nothing needs you for a normal day. |

## 2. Your three places

| Place | Use it for | Token cost |
| --- | --- | --- |
| **Control Room page** (https://claude.ai/artifact/LiQvqiXriy9fZeWteZLWD6) | Looking, previewing, pressing buttons: status, countdown, hold, skip, change words, rate, pause a series, settings | **None** |
| **Control Room chat** (your Claude Project) | Anything that needs words: writing a new hook together, a question, a decision | Small |
| **Workshop** (a Claude Code session on `inikki-reels`) | Changing the machine itself: a new series, a new look, the schedule, a new feature | Larger, and rare |

**Rule of thumb:** buttons first. Chat when you need words. Workshop when you want the machine changed.

**How your changes travel:** the page or the chat drops one small note into Drive (`control/inbox`). The Engine picks up the notes at the start of its next job, applies them, and writes back what happened. You see the result under "Your last actions". The page shows when the next job is. By day the wait is at most about 2.5 hours; Hold and Sleep always count before the next post. To apply at once, see "Apply now" in section 14.

## 3. A normal day (India time)

| Time | Who | What happens |
| --- | --- | --- |
| 04:01 | Engine | Health check: keys, credit, storage, voice |
| 04:52 | Engine | Fetches new trailers |
| 05:12 | Engine | Writes the 1-page brief for the Brain (yesterday's numbers, your rules, your ideas) |
| **05:37** | **Brain** | **Plan run:** plans the day's 6 reels and 2 reserves |
| about 05:50 | Engine | Checks the plans and makes the reels (06:42 is the safety net) |
| 08:30, 12:30, 15:30, 18:00, 20:00, 21:30 | Engine | Posts the reel for that slot (the job starts 12 minutes early). 11:00 and 17:00 are flex slots for trailers, reviews and breaking news. |
| 2 hours after each post | Engine | First numbers |
| 16:12 → **16:37** | Engine → **Brain** | Brief, then the **Refresh run:** news check, evening refresh, one breakdown for the bank, your feedback applied, the daily digest |
| 17:22 | Engine | Makes anything new from the Refresh run |
| 23:40 | Engine | Nightly: all numbers, the dashboard sheet, clean-up |

**What keeps time:** GitHub's own timer runs this project's jobs about 7 hours late, so the posts, the briefs and the nightly job are started on time by a small Claude "clock" task. It costs a little (13 short ticks a day on the cheapest model). Section 12 has a free replacement.

**If a run is missed** (your Claude usage ran out, or a session did not start): five times a day (07:07, 09:37, 13:07, 18:37, 21:07) the dispatcher runs a quick check that uses no AI. A missed run starts then. A late Plan run does not cancel reels: it moves them to the post times still open, flex slots included. What still does not fit is kept in the bank for a later day, except news that would be stale by then. If the run already happened, the check costs almost nothing. Weekly catches up until Tuesday, Monthly until the 3rd.

**Your moments, if you want them:**
- **Morning, after about 07:00:** today's reels are made. Preview them on the page. Change words, hold or skip before the first slot.
- **Evening, after 17:00:** read the digest (6 lines) on the page.
- **Any time:** the master switch.

## 4. The week and the month (the outer loop)

| When | Run | What it does | What you do |
| --- | --- | --- | --- |
| **Sunday 22:37** | Weekly | Compares each series with its own 14-day middle value. Undoes any change that cost 20% or more. Makes at most 3 rule changes per series, one test each. Every second week it pitches up to 3 new series. Writes the weekly report (one screen). | Read the report on Monday. Undo anything you disagree with. Answer its one question, if it has one. |
| **1st, 23:07** | Monthly | Pace toward 1,000 followers, the mix of series, competitors, costs, storage. Trims the playbook. Offers at most 3 decisions. | Tap your answers. |

**What the agent changes alone:** hook styles, story shapes, lengths, music moods, caption wording, hashtags, post times by up to an hour.
**What it only proposes:** brand, niche, safety rules, budgets, daily volume, pausing or adding a series.
**Guard rails:** no rule changes until 10 reels have been measured over 14 days. One thing changed per test. A change that hurts is undone by itself.

**The loop in one line:** post → measure (every night) → **Insights** (worked out by code, no tokens) → decide → change → post.
Open the page's **Insights** tab any day: it says which series earn their slot, which hour works, which first frames lose people, and gives a short "do next" list with the number behind each line. Tap **Send to the agent** on a line you agree with. The Sunday run starts from the same findings, so it thinks less and decides better. With fewer than 10 measured reels, every line is marked as an early signal.

**Where you fit in the loop:**
- Your **feedback** on a reel becomes a soft rule, tried on the next 5 reels. If the numbers disagree, you see both and choose.
- Your **standing rule** applies from the next Plan run and is never undone by numbers.
- The same note three times becomes a hard rule at once.

## 5. Everyday controls

| I want to… | On the page | Or say in the chat |
| --- | --- | --- |
| See how today stands | **Today** tab | `status` |
| Watch a reel before it posts | Today → **Watch** | `preview 2` |
| See what runs next and when | The countdown at the top, and the **Next** tab | `next` |
| See tomorrow's slots | **Next** tab | `tomorrow` |
| See numbers and what they mean | **Insights** tab | `numbers` · `insights` |
| See costs, limits and voice credits | **Usage** tab | `money` |
| Stop everything now | **Sleep** | `stop everything` |
| Keep making reels but post nothing | **Hold posts** | `hold posts` |
| Start again | **Run** | `resume` |
| Hold one reel | the reel → **Hold** | `hold 2` |
| Drop one reel | the reel → **Skip** | `skip 2` |
| Post one reel now | the reel → **Post now** | `post 2 now` |
| Change a hook or caption before it posts | the reel → **Change words** | `change the hook on 2 to …` |
| Make a better version of a posted reel | the reel → **New version** | `new version of 1 with the hook …` |
| Rate a reel | the reel → **Love it / Not good** and the reason chips | `feedback on 1: hook slow` |
| Set a habit for a series | **Series** → **Add a rule** | `rule for watch this next: …` |
| Pause or resume a series | **Series** → **Pause / Resume** | `pause guess the movie` |
| Suggest a topic | **Today** → idea box | `cover this: …` |
| Change reels per day, slot times, budgets, switches | **Setup** tab | `post 5 a day` |
| How many reels each series posts, and at what time; extras on or off; how many reserves | **Setup** → Reels per day: tap a number per series, pick each time, tap Save day plan | `2 movie updates a day, no extras` |
| Take something back | **Setup** → Your last actions → **Undo** | `undo` |
| Clear the alerts | **Today** → alerts → **Mark all read** | `clear alerts` |

### Switches and usage (page → Setup, page → Usage)
- **Setup → Switches:** main voice (ElevenLabs, with Microsoft always as the backup), which ElevenLabs voice, voice quality and speed, breaking news on/off, calendar awareness, the fast-page watch (Chennaiist), a different design for every breakdown, saver mode, approval, away mode. One tap each; Undo is under "Your last actions".
- **Usage:** GitHub runner minutes with where the month is heading, ElevenLabs credits and how many reels they still cover, pictures, storage, and the two times of day to keep Claude free for the runs.
- **Runner minutes, since 15 Nov:** a normal day (5 reels plus news and reviews) should use about 60 of the 2,000 monthly minutes, with no saver. Both timers still post (the Claude clock on time, GitHub's own timer as the late backstop), so a day when Claude has no usage left still posts. Building and testing in the Workshop is the part to keep small: about 200 minutes a month.
- **If the runner minutes run out:** GitHub stops every job until the 1st. Nothing moves to Claude. The Engine slows down by itself before that (fewer extras, then 3 new reels a day) so posting does not stop. Saver mode and "one fewer reel a day" are your two levers.

## 6. Refinement loops: making it better

There are four loops. Pick by asking two questions: **one reel or every reel?** and **has it posted?**

| Situation | Use | Counts from |
| --- | --- | --- |
| One reel, **not posted yet** | **Change words**: the Engine swaps the words, re-checks, makes it again, and you preview it. It cannot post half-changed. | About 10 minutes after the next Engine job |
| One reel, **already posted** | **Not good** + reason. Instagram does not let anyone swap a posted video, so this teaches the next reels. Add **New version** only if you want it re-posted. | The next Plan run |
| **Every reel of a series** | A **standing rule**: one sentence, stays until you remove it | The next Plan run (05:37) |
| **The look itself** (layout, animation, a stronger picture on the title screen) | The **Workshop**, with a ready prompt from section 14 | When the build is merged |

### Worked example: the "Loved Jailer 2? Watch these 4" hook felt weak

It has already posted, so:
1. **Tell the agent.** On the page: the reel → **Not good** → **Hook slow**. One tap.
2. **Set the habit.** Series → Watch This Next → **Add a rule**:
   *"Open with a promise and a number, then who it is for: 4 FILMS TO WATCH TONIGHT / IF YOU LOVED JAILER 2. Never open with a question about the last film."*
   Tomorrow's 05:37 plan follows it. Sunday's Weekly run writes it into the playbook.
3. **Optional: re-post a stronger version.** The reel → **New version** → type the new hook. It is made as a new reel and waits. Preview it, press **Post now**, and delete the old one in the Instagram app if you want only one.
4. **Check it worked.** Insights tab: the skip rate of the next 5 Watch This Next reels against the series' middle value.

If the words are fine but the title screen needs a stronger *picture*, that is the look: use the Workshop prompt "Change a look" in section 14.

**Writing a good hook rule:** say what to do, give one example in capitals, say what to avoid. One sentence beats three.

## 7. Previews: today, tomorrow, later

| What | Where | Notes |
| --- | --- | --- |
| **Today's reels** | Page → Today → **Watch** opens the finished video in Drive | Ready from about 07:00. Each reel shows its slot, hook, caption and score. |
| **Hold until I have looked** | **Hold** on a reel, watch it, then **Post now** | For a whole day of looking first: **Hold posts**, then **Post now** on each reel you approve |
| **Tomorrow** | Page → Next → Tomorrow | The slots and series are known today. The topics are decided at 05:37. To steer them: add an idea or a rule before 05:30. |
| **Later this week** | The weekly report | What is being tested next, and any new series pitch |
| **The breakdown bank** | Page → Today | Breakdowns made ahead. They fill a slot if a reel fails. |

## 8. Series: pause, change, add, replace, retire

A series is one settings card (name, look, slot, length, rules). A lineup says which series fill the day. Nothing about a series lives in code.

Every series is the same **7 blocks**: Basics → Structure → Visuals → Voice → Music → Caption and hashtags → Rules. Open a series on the page to see them.

| I want to… | How | Where |
| --- | --- | --- |
| Pause or resume | **Series** → Pause / Resume | Page |
| Change anything about it | **Series** → open it → open a block → **Edit** → **Save this block** | Page |
| Add a section after another one | **Structure** → Edit → press **＋** on the line above, type it, Save | Page |
| Reorder or remove sections | **Structure** → Edit → **↑ ↓ ✕** | Page |
| Change its voice | **Voice** → Edit → provider (ElevenLabs or Microsoft), voice, speed | Page |
| Change hashtags or caption style | **Caption and hashtags** → Edit | Page |
| Add a habit | **Rules** → Add a rule | Page |
| Test it | **Make a test reel**: its reference reel, made with today's settings, lands in Drive `rehearsal/tests`. Never posted. | Page |
| Improve it with sample reels | **Train with samples**: paste a link and one line on what to learn. The Sunday run studies them. Or copy the training prompt and train it now in a chat. | Page (or Workshop) |
| **Add** a new series | **Add a series**: 7 short steps of questions, or start from a copy. It starts as a **draft**: one reel every other day lands in Drive for you to watch, and nothing posts until you press **Move to trial**. | Page |
| Move it forward | **Move to trial** → **Make it live** | Page |
| **Retire** one | **Retire** (its history is kept; Undo brings it back) | Page |
| A brand-new look | Workshop prompt "Add a series" (section 14) | Workshop |
| Let the agent suggest one | Every second Sunday it pitches up to 3, with evidence and cost. | Weekly report |

A change you make shows a small gold dot until it is undone. Everything here costs no tokens; it counts from the next Plan run.

**Life of a series:** pitch → trial (2 weeks, Trial Reels) → live → reworked or retired. A new series needs its own title screen, look, music and rules before its first reel.

## 9. Changing the agent itself

| Change | Where | How |
| --- | --- | --- |
| Reels per day, slot times, budgets, switches | Page → Setup | Counts from the next plan |
| Go live / back to rehearsal | Page → Setup (asks you to confirm) | Rehearsal makes everything but posts nothing |
| A habit for the whole page | Page → Series → **Rule for every series** | Next plan |
| What a thinking run does | Workshop: "Change a run" | Each run has a one-page card in `runs/` |
| A look, animation, music handling | Workshop: "Change a look" | Tested against the reference reels first |
| Brand colours, name, fonts | Workshop: "Rebrand" | One file holds the brand |
| A different topic (niche) | Workshop: "Switch niche" | A pilot week first; a new account is usually safer |
| A brand-new feature | Workshop: describe it in one paragraph | It comes back with a preview |

Every change gets a number, a reason and an Undo in the change log.

## 10. Keeping tokens low

**Where tokens go, measured on 13 Nov:**
| Activity | Before | Now |
| --- | --- | --- |
| A Plan run | About 5.5 million tokens for 3 reels: the run woke one long chat and re-read all of it at every step | Each run starts in a clean chat, so it re-reads only its own work |
| A Refresh run | About 3 million tokens | Same fix |
| Looking at status | The chat searched Drive, opened several files and drew a card: 2 to 3% of a 5-hour limit each time | The page: nothing. The chat: one small file. |
| Making a change | The chat read files, then tried to rewrite them | One small note, nothing read first |

**Habits that keep it low:**
1. **Page first.** Looking and pressing cost nothing there.
2. **Short words in the chat:** `status`, `next`, `hold 2`. The chat is set up to answer from one small file.
3. **One topic per chat.** Start a new chat when the topic changes. Long chats cost more with every message.
4. **Do not upload `AGENT.md` to the Control Room project.** This guide is its only file.
5. **Workshop:** one task per session, and start with "Use the workshop skill." Open a new session for the next task.
6. **Do not ask for drawings** unless you want one. The page already has the cards.
7. **Keep your Claude account lean.** Every new session first loads every plugin and connector you have switched on: about 60,000 tokens before it does anything (measured 13 Nov). Switch off the ones this agent does not use at claude.ai → Customize (plugins and connectors). The agent needs only GitHub, Google Drive and the Claude Code session tools.
9. **The two helper chats renew themselves.** Every Monday at 03:17 the clock and dispatcher chats are replaced by fresh ones, so their cost does not keep growing. Nothing to do on your side.
8. **AGENT.md is never read whole** (about 30,000 tokens). Sessions read its map and one section; a project hook enforces it.

## 11. Files and clean-up

**Where things live:**
| Place | Holds | Size |
| --- | --- | --- |
| GitHub `inikki-reels` | Settings, plans, rules, numbers, this guide. Text only. | Tiny |
| Drive "iNiKKi Reels" | Reels, pictures, music, status, your settings | Capped at 8 GB |
| Instagram | The posted reels | — |

**What is deleted by itself, every night at 23:40:**
| Kind of file | Kept for | Then |
| --- | --- | --- |
| Working files of a reel | 3 days | Binned |
| Rehearsal reels | 14 days | Binned |
| Finished reels | 30 days (14 when storage is tight) | Binned, except the top 10% by views. They live on Instagram. |
| Clip library | Capped at 3 GB | Oldest first |
| Picture library | Capped at 1.5 GB | Oldest first |
| Daily status files | 30 days | Binned |
| Plans (text) | Forever | Packed into one file per month after 30 days |
| Your notes in the inbox | Until applied | Binned, and logged |

- "Binned" means Drive's bin: you can restore for 30 days.
- **Never touched:** `reference-reels`, `meme-bank`, your music folder, `control`.
- Warning on the page at 6 GB. At 7.5 GB the clean-up tightens by itself.
- **GitHub tidies itself:** each thinking run's branch is deleted once its work is taken in. Each run's session is archived by the next run.
- **You never need to delete anything by hand.** If Drive ever feels full, empty Drive's bin.

## 12. When something goes wrong

Every alert says: what happened → what the system already did → what you need to do (usually nothing).

| You see | It means | You do |
| --- | --- | --- |
| "A reel was held" | It failed the plan check or the inspection. A reserve or a bank reel takes its slot. | Nothing. **Make again** if you want that exact reel. |
| "A reel could not be posted" | Instagram refused once. The slot was skipped. | Nothing, unless it repeats: then the Instagram key needs a look (Workshop). |
| "The … job did not finish" | One job stopped. The next run starts fresh. | Nothing, unless it repeats. |
| "A change you asked for was not made" | Your new words failed the check (too long, or the wrong number of lines) | Try again with shorter words |
| "Health check: … need a look" | A key, credit or limit needs attention. It names which. | Follow the one line it gives |
| "Respect mode is on" | Sad news was reported by two trusted sources. Only fitting reels post today. | Nothing. Say `respect mode off` if it is wrong. |
| The page says "updated" hours ago | No Engine job has run since | Check GitHub → Actions; ask the Workshop to "check the clock" |

**Emergency:** press **Sleep**. Nothing posts until you press **Run**.

### Security (the repository is public)
Anyone can read the files and the job logs. Nobody else can change anything, start a job, or see a key. The Engine masks keys and your email before it prints or saves anything, takes commands only from your own Drive account, and looks around once a day (04:01, with the health check).

| You see | It means | You do |
| --- | --- | --- |
| "Security: a command came from an account that is not yours" | Someone else put a file in the Control Room inbox. It was refused. Posting is on hold. | Drive → iNiKKi Reels → Share: remove anyone you do not know. Then **Resume**. |
| "Security: a Drive folder was open to anyone with the link" | The Engine has closed it again. | If you did not open it: change your Google password. |
| "Security: a job was started by someone who is not you" | Someone else used your GitHub account. Posting is on hold. | "If someone gets in", below. |
| "Security: a key may be visible in the repository" | A file holds something shaped like a key. | "If a key leaks", below. |
| "Security: a post appeared that the Engine did not make" | A reel or post is on the page that the Engine did not publish. | If it was you: nothing. If not: "If a key leaks" for Instagram. |
| "Security: voice credits were used outside the Engine" | ElevenLabs credits went down more than the Engine used. | If it was you or a test: nothing. If not: make a new ElevenLabs key. |

**If a key leaks (5 minutes).** 1. Make a new key on that service's own site and delete the old one there (the list of sites is in AGENT.md 21.4; for Instagram, change your password first). 2. GitHub → Settings → Secrets and variables → Actions → click the secret → **Update**. 3. Press **Resume** if posting was on hold. The old key is dead the moment you delete it, so nothing more is needed.

**If someone gets in to GitHub.** 1. Press **Sleep**. 2. GitHub → Settings → Password: change it; Settings → Sessions: sign out everything else; Settings → Applications: remove anything you do not know. 3. Replace every key (the list above), because a job could have read them. 4. Press **Run**.

### A free clock, if you want one (10 minutes, once)
The Claude clock works, but it spends a few tokens every day. A free outside pinger does the same job with none:
1. On GitHub: Settings → Developer settings → Fine-grained tokens → new token for `inikki-reels` only, permission **Actions: Read and write**.
2. On cron-job.org (free): one job per line of the clock table in `runs/README.md`. Each job sends a POST to `https://api.github.com/repos/haridhyaragav77-bit/inikki-reels/actions/workflows/<workflow>.yml/dispatches` with the header `Authorization: Bearer <your token>` and the body `{"ref":"main"}` (for a daily job: `{"ref":"main","inputs":{"job":"brief-plan"}}`).
3. Tell a Workshop session "the outside clock is set up": it switches the Claude clock tasks off.
Or ask the Workshop: "walk me through the free clock, one step at a time."

## 13. The skills (what makes repeat work cheap)

A skill is a short card that tells Claude exactly how to do one repeated job, so it does not work it out again each time.

| Skill | Used by | Does |
| --- | --- | --- |
| `quiet-exit` | Every thinking run | Stops in one step when the switch is off or there is nothing to do |
| `daily-brief` | Every thinking run | Starts from the one-page brief, not from raw files |
| `plan-reel` | Plan run | A fill-in form per look, so plans are right first time |
| `score-reel` | Plan run | The fixed 8-line score, value first |
| `pick-clips` | Plan run | Picks trailer moments from one picture grid |
| `apply-feedback` | Refresh and Weekly | Turns each piece of your feedback or rule into one numbered change |
| `weekly-learn` | Weekly | Reads one computed table, undoes what hurt, at most 5 changes |
| `series-pitch` | Weekly, alternate weeks | The fixed pitch form with evidence and cost |
| `advisor-voice` | Anything you read | Short, plain, card first |
| `series-change` | Workshop | The fixed steps to add, replace, pause or retire a series |
| `workshop` | Workshop | How a build session starts cheaply, tests and ships |
| Control Room instructions | Control Room chat | One read, short answers, one-note actions |

## 14. Ready prompts

### In the Control Room chat
Short is best: `status` · `next` · `tomorrow` · `numbers` · `money` · `alerts` · `series` · `preview 2` · `hold 2` · `skip 2` · `post 2 now` · `stop everything` · `resume`

- `change the hook on 2 to 4 FILMS TO WATCH TONIGHT / IF YOU LOVED JAILER 2`
- `new version of 1 with a stronger hook` (it offers three, you pick)
- `feedback on 1: hook slow, great style`
- `rule for watch this next: open with a promise and a number`
- `rule for every series: never start with a question`
- `pause guess the movie` · `resume guess the movie`
- `cover this: 5 one-night thrillers on Netflix`
- `post 5 a day` · `move the 21:30 slot to 22:00`
- `undo` · `clear alerts`

### In the Workshop (open a Claude Code session on `inikki-reels`, paste one)

**Apply now**
> Use the workshop skill. Apply my Control Room changes now: run the post workflow on main, then tell me what was applied.

**Add a series**
> Use the workshop skill and the series-change skill. Add a new series: [name]. Idea: [one or two sentences]. It should post [how often, which slot]. Closest existing series: [name]. Start it as a trial. Show me its settings card and one sample plan before merging.

**Replace a series**
> Use the workshop skill and the series-change skill. Replace [old series] with [new series idea] in the same slot. Keep the old one's history. Show me the new settings card before merging.

**Retire a series**
> Use the workshop skill and the series-change skill. Retire [series]. Tell me what fills its slot.

**Change a look** (the Jailer 2 title screen is this kind of change)
> Use the workshop skill. In the [Poster Wall] look, make the title screen stronger: [one striking full-screen still behind the hook instead of the four-poster grid; hook in two lines, the number largest]. Re-render the reference reel and show me before and after frames. Do not change the other looks.

**Change a run**
> Use the workshop skill. Change the [Plan] run card so that [what you want]. Show me the before and after lines.

**Check the clock**
> Use the workshop skill. Check that the Engine's jobs ran on time in the last 24 hours (posts at their slots, both briefs, the nightly job) and that the thinking runs started. Say whether GitHub's own timer is still late. List anything that did not run and fix what you can.

**Renew the clock** (every few weeks)
> Use the workshop skill. Make a new clock chat from the rules in runs/README.md, move the clock tasks to it, and switch the old ones off.

**Measure thinking cost**
> Use the workshop skill. Read the usage of the last Plan, Refresh and Weekly sessions (tag inikki-brain), work out tokens and cost per reel, write one line to data/notes/usage.json for the panel, and tell me the numbers in a small table.

**Self-test the thinking runs**
> Use the workshop skill. Fire "RUN selftest" at the dispatcher and tell me whether the note reached main.

**Monthly tidy**
> Use the workshop skill. Tidy up: list branches older than a week, open pull requests, old test files in Drive rehearsal/, and sessions tagged inikki-brain that are not archived. Tell me what you would remove, then remove what is safe.

**Full audit**
> Use the workshop skill. Audit the last 7 days: jobs that failed, reels held and why, alerts that repeated, costs against limits. Give me 5 lines and at most 3 fixes.
