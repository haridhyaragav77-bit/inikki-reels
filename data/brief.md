# Brief · plan run · 2026-11-22 (written 2026-11-22 05:13 IST)

Switch: **run** · Phase: **live** · Respect mode: **off** · Approval: autopilot
Control Room settings copied to data/control/: switch.json, overrides.yaml, feedback.jsonl, commands.jsonl

## To do
1. Plan 5 reel(s) for 2026-11-22 at the slots below, plus 2 reserve(s) ("reserve": true). Save each to plans/2026-11-22/<reel_id>.json and check it with: python -m engine.plancheck <file>.

## Harish's standing rules (set in the Control Room; follow them in every plan, AGENT.md 8.4)
- every series: When posting always use "#" captions as #fyp #trending #viral #explorepage #reels (2026-11-13)
- breaking-news: Make sure there are gradrail for images picked and avoid risks of random images being picked (2026-11-13)
- film-breakdown: Make music sublte and less louder than the voiceover, make voice over more natural and paced for people to understand and loud and clear but don't compromise the music either make them play well together. (2026-11-13)
- film-breakdown: A reel may make several points, but each point must be clear, focused and worth the viewer's time, stated in plain words (e.g. 'In the film, Maara is an Air Force officer. In real life, Captain G.R. Gopinath was an Army officer.'), and the viewer must know what the reel is about from the hook. (2026-11-20)
- film-breakdown: Motion graphics are made fresh for each reel like the Joker and F1 samples, and each screen shows exactly what that line says; the visual must suit the subject (a person gets a person-style visual such as a portrait card with name and role, never axonometric grids or diagrams used just because they  (2026-11-20)
- film-breakdown: When naming the real person behind a character, introduce them simply with who they are (e.g. 'Bommi is based on Bhargavi, Gopinath's wife') so the name never feels strange. (2026-11-20)
- film-breakdown: The loop is seamless: the last spoken line flows straight into the hook with no extra bridging line, and a reel never ends on a dangling word like 'yenna'. (2026-11-20)
- film-breakdown: No word may be said twice in a row in the script or the ElevenLabs voice; listen back to the finished voice track and redo any line where a word repeats. (2026-11-20)
- movie-recommendations: Make reels slightly longer, match the reading pace of a person to the reel and secondly add a motion graphics of the plot of the movie and extend length of reel accordingly so ppl get excited about the plot of each movie also without any spoilers (2026-11-13)
- movie-review: Change series to be more direct of its content which is movie review, people may skip thinking it's something else and use the actors make sure a popular element like the actors face, post is on the first fram and make it feel richer for the visual hook and interesting visual desings to it make the  (2026-11-13)

## Today (use it in hooks and titles; AGENT.md 10.5)
Sunday 22 Nov 2026 · lazy Sunday, family at home · season: Chennai rains (north-east monsoon)
Words that fit each slot's hour: 08:30 morning: TODAY / THIS WEEK · 11:00 morning: TODAY / THIS WEEK · 12:30 afternoon: TONIGHT / AFTER WORK · 18:00 evening: TONIGHT · 20:00 evening: TONIGHT · 21:30 late night: LATE NIGHT / BEFORE YOU SLEEP
Title angles for today (fill {N} and {FILM}; a film in today's news makes the strongest tie-in): RAINY NIGHT: {N} FILMS | MAZHAI + MOVIE: {N} PICKS | LAZY SUNDAY: {N} FEEL-GOOD FILMS | SUNDAY FAMILY WATCH: {N} FILMS

## Series settings changed in the Control Room (these win over the series file; AGENT.md 6.5)
- artwork-quote: per_day = 0
- film-breakdown: per_day = 2; slots = ["20:00", "21:30"]
- movie-updates: per_day = 4; slots = ["08:30", "11:00", "12:30", "18:00"]
- trailer-breakdown: status = "live"

## Releases (knowledge/releases.yaml; keep it up to date: confirmed dates for the next 14 days, 2 sources)
No release today or tomorrow in the calendar. Add any confirmed release dates you find.

## Films the updates covered in the last 3 days (pick other films unless there is real new news; lead.film, lead.new_event)
- appa-kutty · dorothy-rotterdam · jailer-2 · mookuthi-amman-2-week-one · om · om-day-1 · om-mammootty-siya · om-tomorrow-undercover · ramayana · releases-27-nov · sathyavan-savithiri-july-to-november · sathyavan-savithiri-tomorrow · scene-ott-netflix · suriya-2026-total · thagappan · weekend-four-films · weekend-ott-drops
Today: at least 3 different films, and one update from outside the top films (smaller film, OTT drop, another-language or Hollywood release in Tamil Nadu, industry story). Use the news watch's lower-ranked stories too.

## Breakdown designs used lately (the next breakdown names another kit in "design" and a different build; AGENT.md 5.8)
- 2026-11-22-breakdown-f1-real-racing: kit blueprint · track → layers → standoff → quote → standoff → source → technique
- 2026-11-21-breakdown-thani-oruvan-villain: kit spotlight · versus → board → standoff → detail → standoff → chain → technique
- 2026-11-21-breakdown-amaran-indhu-voice: kit royal · pins → timeline → standoff → versus → standoff → meter → technique
- 2026-11-20-breakdown-soorarai-pottru-real-maara: kit noir · pins → timeline → standoff → layers → standoff → versus → quote → technique

## Today's slots (2026-11-22)
| time | series | template | notes |
| --- | --- | --- | --- |
| - | movie-recommendations | paused |  |
| 08:30 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 11:00 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 12:30 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 18:00 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 20:00 | film-breakdown | stage | voice, 45-90 s |
| 21:30 | film-breakdown | stage | voice, 45-90 s |

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
- Jail Mates: 4 stills, grid: clip-library/sheets/Jail Mates - youtube.jpg
- Manikanda: 23 stills, grid: clip-library/sheets/Manikanda - youtube.jpg
Older-look visual: {type: image, still: {film: <film>, n: <number on the grid>}, ai: false, label: <2-word tag>}. Pick the still that shows what the line says; skip stills that are mostly text.

## Trailers to get (Harish runs the laptop helper; the command is in Drive requests/trailers_to_get.md)
Waiting: Sathyavan Savithiri, Jail Mates, OM: Chapter One, OM, Om, O.M, Manikanda. Plans for these wait until they arrive.
Researcher: for each, find the official YouTube trailer (studio or music label channel) and add a line 'Film = link' to data/notes/trailer_links.md, so the command has the exact video.
Flex slots 11:00, 17:00: trailer-breakdown when a new trailer lands, movie-review on release days. Turned off by Harish: artwork-quote.

Plans already in plans/2026-11-22/: ?

## Yesterday's numbers (per reach; colour against the series median)
| reel | series | views | skip | watch | share | follow |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-21-update-om-day1-record | movie-updates | 1519 | 54.5% green | 37.5% green | 0.0% grey | - grey |
| 2026-11-21-update-weekend-ott-drops | movie-updates | 170 | 81.8% red | 17.9% red | 0.0% grey | - grey |
| 2026-11-21-update-suriya-643cr-year | movie-updates | 1819 | 48.4% green | 44.7% green | 0.5% grey | - grey |
| 2026-11-21-update-om-netflix | movie-updates | 65 | 70.9% amber | 37.7% green | 0.0% grey | - grey |
| 2026-11-21-breakdown-thani-oruvan-villain | film-breakdown | 736 | 56.5% green | 19.4% green | 0.0% grey | - grey |
| 2026-11-21-breakdown-amaran-indhu-voice | film-breakdown | 174 | 64.1% green | 12.0% red | 0.0% grey | - grey |

## Trends from the news watch (top 5, no AI; verify before use)
- [11.2] 'O.M' OTT release date: Here's when and where you can watch Dhanush, Mammootty, Sai Pallavi and Sreeleela · 15 publishers (4 trusted)
- [11.2] Dhanush, Mammootty-starrer Om's trailer springs a surprise; reveals Dhanush is with the TN intelligence unit · 31 publishers (9 trusted)
- [11.2] 'O.M: Operation Mole' Box Office Day 1: Dhanush and Mammootty's film collects Rs 33.7 crore worldwide · 22 publishers (6 trusted)
- [10.0] How Suriya turned his biggest box office failures into a Rs 600 crore comeback · 31 publishers (8 trusted)
- [8.4] 'O.M: Operation Mole' box office collection day 1: Mammootty, Dhanush, Sai Pallavi starrer opens strong; · 4 publishers (2 trusted)

## Changes in force (newest first)
- #17 · 19 Nov 2026 · series (film-breakdown) · stock graphics reused across reels, scripts that let viewers drift → illustrated graphics drawn for the film's idea (at most
- #16 · 19 Nov 2026 · series (film-breakdown, trailer-breakdown) · a named technique as the hook, 40-62 s, one film once in 21 days → lead with one specific detail or a tru
- #15 · 15 Nov 2026 · series (movie-updates) · stills cropped tight and titles that did not say the news → soft rule: keep faces and the key subject whole (crop only to cut
- #14 · 14 Nov 2026 · rule (news watch) · a small film's trailer could not reach the score that wakes the Breaking run → fast pages (@chennaiist) are read at every pass; a 
- #13 · 14 Nov 2026 · rule (all series) · hooks and titles were timeless → every brief opens with Today (day, hour, season, festivals, title angles); Watch This Next must u

## New feedback from Harish
- 2026-11-21-breakdown-amaran-indhu-voice: rated 2/5 · Hook slow, Visuals weak · Bad content
- 2026-11-21-breakdown-amaran-indhu-voice: rated 2/5 · Content doesn't make sense
- 2026-11-21-breakdown-amaran-indhu-voice: rated 2/5 · Not worth it · Too short

## Open alerts
- 2026-11-21 23:43 IST: Drive storage is getting full
- 2026-11-21 16:41 IST: Some Brain changes were not applied
- 2026-11-21 16:41 IST: A note from the thinking run
- 2026-11-21 08:55 IST: Health check: 1 thing(s) need a look
- 2026-11-21 02:02 IST: Manual work is urgent: Study 12 competitor shorts with the laptop helper

## Money and limits
- Images ₹26 of ₹500 this month
- Runner minutes: 1797 used this month. No limit (the repository is public): plan the full day, reserves included, nothing held back for minutes.
- Storage: 6.45 GB of 8 GB

Plan forms: templates/<template>/plan_form.json · motion library: rules/motion.md · check: python -m engine.plancheck <file>
