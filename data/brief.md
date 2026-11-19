# Brief · plan run · 2026-11-20 (written 2026-11-20 05:13 IST)

Switch: **run** · Phase: **live** · Respect mode: **off** · Approval: autopilot
Control Room settings copied to data/control/: switch.json, overrides.yaml, feedback.jsonl, commands.jsonl

## To do
1. Plan 6 reel(s) for 2026-11-20 at the slots below, plus 2 reserve(s) ("reserve": true). Save each to plans/2026-11-20/<reel_id>.json and check it with: python -m engine.plancheck <file>.

## Harish's standing rules (set in the Control Room; follow them in every plan, AGENT.md 8.4)
- every series: When posting always use "#" captions as #fyp #trending #viral #explorepage #reels (2026-11-13)
- breaking-news: Make sure there are gradrail for images picked and avoid risks of random images being picked (2026-11-13)
- film-breakdown: Make music sublte and less louder than the voiceover, make voice over more natural and paced for people to understand and loud and clear but don't compromise the music either make them play well together. (2026-11-13)
- movie-recommendations: Make reels slightly longer, match the reading pace of a person to the reel and secondly add a motion graphics of the plot of the movie and extend length of reel accordingly so ppl get excited about the plot of each movie also without any spoilers (2026-11-13)
- movie-review: Change series to be more direct of its content which is movie review, people may skip thinking it's something else and use the actors make sure a popular element like the actors face, post is on the first fram and make it feel richer for the visual hook and interesting visual desings to it make the  (2026-11-13)

## Today (use it in hooks and titles; AGENT.md 10.5)
Friday 20 Nov 2026 · Friday night, date night, new releases in theatres · season: Chennai rains (north-east monsoon)
Words that fit each slot's hour: 08:30 morning: TODAY / THIS WEEK · 11:00 morning: TODAY / THIS WEEK · 12:30 afternoon: TONIGHT / AFTER WORK · 15:30 afternoon: TONIGHT / AFTER WORK · 18:00 evening: TONIGHT · 20:00 evening: TONIGHT · 21:30 late night: LATE NIGHT / BEFORE YOU SLEEP
Title angles for today (fill {N} and {FILM}; a film in today's news makes the strongest tie-in): RAINY NIGHT: {N} FILMS | MAZHAI + MOVIE: {N} PICKS | FRIDAY NIGHT: {N} FILMS | DATE NIGHT: {N} FILMS | LOVED {FILM}? WATCH THESE {N}

## Series settings changed in the Control Room (these win over the series file; AGENT.md 6.5)
- artwork-quote: per_day = 0
- movie-updates: per_day = 4; slots = ["08:30", "18:00", "21:30", "11:00"]
- trailer-breakdown: status = "live"

## Films the updates covered in the last 3 days (pick other films unless there is real new news; lead.film, lead.new_event)
- inji-vellam-rahman-19 · mookuthi-amman-2-week-one · nayanthara-birthday · nayanthara-birthday-eve · om-2-days-178-min · om-five-distributors · om-mammootty-7-months · om-mammootty-siya · om-operation-mole · om-tomorrow-undercover · sai-pallavi-two-films · sathyavan-savithiri-2-days · sathyavan-savithiri-3-days · sathyavan-savithiri-july-to-november · sathyavan-savithiri-tomorrow · scene-overseas-83cr · weekend-four-films
Today: at least 3 different films, and one update from outside the top films (smaller film, OTT drop, another-language or Hollywood release in Tamil Nadu, industry story). Use the news watch's lower-ranked stories too.

## Breakdown designs used lately (the next breakdown names another kit in "design" and a different build; AGENT.md 5.8)
- 2026-11-22-breakdown-f1-real-racing: kit blueprint · track → layers → standoff → quote → standoff → source → technique
- 2026-11-21-breakdown-thani-oruvan-villain: kit spotlight · versus → board → standoff → detail → standoff → chain → technique
- 2026-11-20-breakdown-joker-stairs: kit neon · pins → climb → standoff → quote → standoff → climb → source → technique
- 2026-11-19-breakdown-peranbu: kit royal · technique → cards → loop → moral

## Today's slots (2026-11-20)
| time | series | template | notes |
| --- | --- | --- | --- |
| 08:30 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 11:00 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 12:30 | film-breakdown | stage | voice, 45-90 s |
| 15:30 | movie-recommendations | poster-wall | no voice, 20-45 s |
| 18:00 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 20:00 | film-breakdown | stage | voice, 45-90 s |
| 21:30 | movie-updates | bulletin | voice: case by case, 15-30 s |

## Pictures for the approved looks (AGENT.md 5.11, skill plan-reel)
Breakdowns, updates, Watch This Next, reviews and breaking use official YouTube frames and posters, which the Engine fetches itself: an asset {"src": "engine/.cache/stills/<film>/<YouTube id>_maxres2.jpg"} (maxresdefault, maxres1, maxres2 or maxres3), or a poster with "fetch": {"url": ...}. Any film works; no film waits for the library. The YouTube ids of the trailers below are in their grid names, e.g. Kaithi [g79CvhHaj5I].

## Trailers in the clip library (older looks: Guess the Movie, Artwork; and trailer ids for the frames above)
- Lubber Pandhu (trailer, 50 shots, grid: clip-library/sheets/Lubber Pandhu - trailer [oP88LHBukW8].jpg)
- Master (trailer, 50 shots, grid: clip-library/sheets/Master - trailer [1_iUFT3nWHk].jpg)
- Maaveeran (trailer, 50 shots, grid: clip-library/sheets/Maaveeran - trailer [EcNACt-LOi0].jpg)
- Amaran (trailer, 40 shots, grid: clip-library/sheets/Amaran - trailer [hylIXfZeB4c].jpg)
- Jailer (trailer, 37 shots, grid: clip-library/sheets/Jailer - trailer [Y5BeWdODPqo].jpg)
- Leo (trailer, 36 shots, grid: clip-library/sheets/Leo - trailer [Po3jStA673E].jpg)
- Virumaandi (trailer, 42 shots, grid: clip-library/sheets/Virumaandi - trailer [RVN_g9XYUsY].jpg)
- Pizza (trailer, 40 shots, grid: clip-library/sheets/Pizza - trailer [1ORbkrHs5JU].jpg)
- Soodhu Kavvum (trailer, 33 shots, grid: clip-library/sheets/Soodhu Kavvum - trailer [JwDc_9J9QqI].jpg)
- Vikram Vedha (trailer, 50 shots, grid: clip-library/sheets/Vikram Vedha - trailer [eLucCWmf6V4].jpg)
- 96 (trailer, 39 shots, grid: clip-library/sheets/96 - trailer [r0synl-lI4I].jpg)
- Karnan (trailer, 37 shots, grid: clip-library/sheets/Karnan - trailer [pgfUzQ8nzBY].jpg)
- Viduthalai Part 1 (trailer, 41 shots, grid: clip-library/sheets/Viduthalai Part 1 - trailer [GYeSfq_bj_M].jpg)
- Maharaja (trailer, 26 shots, grid: clip-library/sheets/Maharaja - trailer [Otcr-vRuaQs].jpg)
- Jai Bhim (trailer, 50 shots, grid: clip-library/sheets/Jai Bhim - trailer [Gc6dEDnL8JA].jpg)
- Soorarai Pottru (trailer, 35 shots, grid: clip-library/sheets/Soorarai Pottru - trailer [fa_DIwRsa9o].jpg)
- Pariyerum Perumal (trailer, 30 shots, grid: clip-library/sheets/Pariyerum Perumal - trailer [GMNsUxJe4R4].jpg)
- Aaranya Kaandam (trailer, 33 shots, grid: clip-library/sheets/Aaranya Kaandam - trailer [haI-Rq8PX3g].jpg)
- Super Deluxe (trailer, 36 shots, grid: clip-library/sheets/Super Deluxe - trailer [3-Xq_Zz3nPA].jpg)
- Vikram (trailer, 25 shots, grid: clip-library/sheets/Vikram - trailer [OKBMCL-frPU].jpg)
- Ratsasan (trailer, 50 shots, grid: clip-library/sheets/Ratsasan - trailer [GsrN7rNch9Y].jpg)
- Jigarthanda (trailer, 39 shots, grid: clip-library/sheets/Jigarthanda - trailer [_T8n-EHr4ZE].jpg)
- Kaithi (trailer, 24 shots, grid: clip-library/sheets/Kaithi - trailer [g79CvhHaj5I].jpg)
For an older look, open a film's grid (Google Drive) and pick the shot whose picture shows each line; shot times are in data/trailers.json. Check its timeline sheet (same folder, '... - timeline.jpg', a frame every 1.5 s): the tiles from your start second for as long as the line lasts (2-4 s) must all show what the line says. Older-look visual: {type: clip, film: <film>, start: <second>, len: 2.5, label: <2-word tag>}.

## Official stills in the library (older looks; approved looks use the official frames above)
- Jailer 2: 30 stills, grid: clip-library/sheets/Jailer 2 - stills.jpg
- Scene: 30 stills, grid: clip-library/sheets/Scene - stills.jpg
- Inji Vellam: 1 stills, grid: clip-library/sheets/Inji Vellam - stills.jpg
- OM: 8 stills, grid: clip-library/sheets/OM - stills.jpg
- O.M: 11 stills, grid: clip-library/sheets/O.M - stills.jpg
Older-look visual: {type: image, still: {film: <film>, n: <number on the grid>}, ai: false, label: <2-word tag>}. Pick the still that shows what the line says; skip stills that are mostly text.

## Trailers to get (Harish runs the laptop helper; the command is in Drive requests/trailers_to_get.md)
Waiting: Sathyavan Savithiri, Jail Mates, OM: Chapter One, OM, Om, O.M, Manikanda. Plans for these wait until they arrive.
Researcher: for each, find the official YouTube trailer (studio or music label channel) and add a line 'Film = link' to data/notes/trailer_links.md, so the command has the exact video.
Flex slots 11:00, 17:00: trailer-breakdown when a new trailer lands, movie-review on release days. Turned off by Harish: artwork-quote.

## Today's reels
| slot | reel | series | state | note |
| --- | --- | --- | --- | --- |
| 20:00 | 2026-11-20-breakdown-joker-stairs | film-breakdown | ready |  |

## Yesterday's numbers (per reach; colour against the series median)
| reel | series | views | skip | watch | share | follow |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-19-update-om-tomorrow-undercover | movie-updates | 848 | 58.4% green | 28.4% green | 0.0% grey | - grey |
| 2026-11-18-breakdown-thani-oruvan | film-breakdown | 255 | 68.5% amber | 14.5% green | 0.0% grey | - grey |
| 2026-11-19-breakdown-jai-bhim | film-breakdown | 149 | 79.1% amber | 10.1% red | 0.0% grey | - grey |
| 2026-11-19-update-om-mammootty-siya | movie-updates | 487 | 62.6% green | 25.8% amber | 0.0% grey | - grey |
| 2026-11-19-breakdown-peranbu | film-breakdown | 125 | 65.0% green | 12.7% green | 0.0% grey | - grey |
| 2026-11-19-update-sathyavan-savithiri-tomorrow | movie-updates | 52 | 77.8% red | 16.2% red | 0.0% grey | - grey |

## Trends from the news watch (top 5, no AI; verify before use)
- [11.2] OM trailer reveals too much: Dhanush, Mammootty, Sai Pallavi get their own Dhurandhar-meets-Pushpa | Hindustan · 9 publishers (3 trusted)
- [11.2] Dhanush, Mammootty-starrer Om's trailer springs a surprise; reveals Dhanush is with the TN intelligence unit · 22 publishers (9 trusted)
- [10.0] How Suriya turned his biggest box office failures into a Rs 600 crore comeback · 30 publishers (8 trusted)
- [8.0] 'Mookuthi Amman 2' box office collection day 6 vs 'Jailer 2' day 28: Nayanthara's film adds Rs 1 crore to · 5 publishers (2 trusted)
- [6.0] Scene grosses over 200 crore; Suriya scripts Tamil cinema history · 12 publishers (3 trusted)

## Changes in force (newest first)
- #17 · 19 Nov 2026 · series (film-breakdown) · stock graphics reused across reels, scripts that let viewers drift → illustrated graphics drawn for the film's idea (at most
- #16 · 19 Nov 2026 · series (film-breakdown, trailer-breakdown) · a named technique as the hook, 40-62 s, one film once in 21 days → lead with one specific detail or a tru
- #15 · 15 Nov 2026 · series (movie-updates) · stills cropped tight and titles that did not say the news → soft rule: keep faces and the key subject whole (crop only to cut
- #14 · 14 Nov 2026 · rule (news watch) · a small film's trailer could not reach the score that wakes the Breaking run → fast pages (@chennaiist) are read at every pass; a 
- #13 · 14 Nov 2026 · rule (all series) · hooks and titles were timeless → every brief opens with Today (day, hour, season, festivals, title angles); Watch This Next must u

## Money and limits
- Images ₹26 of ₹500 this month
- Runner minutes: 1352 used this month. No limit (the repository is public): plan the full day, reserves included, nothing held back for minutes.
- Storage: 5.94 GB of 8 GB

Plan forms: templates/<template>/plan_form.json · motion library: rules/motion.md · check: python -m engine.plancheck <file>
