# Brief · plan run · 2026-11-14 (written 2026-11-14 05:13 IST)

Switch: **run** · Phase: **live** · Respect mode: **off** · Approval: autopilot
Control Room settings copied to data/control/: switch.json, overrides.yaml, commands.jsonl

## To do
1. Plan 7 reel(s) for 2026-11-14 at the slots below, plus 2 reserve(s) ("reserve": true). Save each to plans/2026-11-14/<reel_id>.json and check it with: python -m engine.plancheck <file>.

## Harish's standing rules (set in the Control Room; follow them in every plan, AGENT.md 8.4)
- every series: When posting always use "#" captions as #fyp #trending #viral #explorepage #reels (2026-11-13)
- breaking-news: Make sure there are gradrail for images picked and avoid risks of random images being picked (2026-11-13)
- film-breakdown: Make music sublte and less louder than the voiceover, make voice over more natural and paced for people to understand and loud and clear but don't compromise the music either make them play well together. (2026-11-13)
- movie-recommendations: Make reels slightly longer, match the reading pace of a person to the reel and secondly add a motion graphics of the plot of the movie and extend length of reel accordingly so ppl get excited about the plot of each movie also without any spoilers (2026-11-13)
- movie-review: Change series to be more direct of its content which is movie review, people may skip thinking it's something else and use the actors make sure a popular element like the actors face, post is on the first fram and make it feel richer for the visual hook and interesting visual desings to it make the  (2026-11-13)

## Today's slots (2026-11-14)
| time | series | template | notes |
| --- | --- | --- | --- |
| 08:30 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 12:30 | film-breakdown | stage | voice, 40-62 s |
| 15:30 | movie-recommendations | poster-wall | no voice, 20-45 s |
| 18:00 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 20:00 | film-breakdown | stage | voice, 40-62 s |
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
Older-look visual: {type: image, still: {film: <film>, n: <number on the grid>}, ai: false, label: <2-word tag>}. Pick the still that shows what the line says; skip stills that are mostly text.

## Trailers to get (Harish runs the laptop helper; the command is in Drive requests/trailers_to_get.md)
Waiting: Sathyavan Savithiri, Jail Mates. Plans for these wait until they arrive.
Researcher: for each, find the official YouTube trailer (studio or music label channel) and add a line 'Film = link' to data/notes/trailer_links.md, so the command has the exact video.

## New trailers in the library (last 3 days)
- Lubber Pandhu (trailer, grid: clip-library/sheets/Lubber Pandhu - trailer [oP88LHBukW8].jpg)
- Master (trailer, grid: clip-library/sheets/Master - trailer [1_iUFT3nWHk].jpg)
- Maaveeran (trailer, grid: clip-library/sheets/Maaveeran - trailer [EcNACt-LOi0].jpg)
- Amaran (trailer, grid: clip-library/sheets/Amaran - trailer [hylIXfZeB4c].jpg)
- Jailer (trailer, grid: clip-library/sheets/Jailer - trailer [Y5BeWdODPqo].jpg)
- Leo (trailer, grid: clip-library/sheets/Leo - trailer [Po3jStA673E].jpg)
Flex slot: plan one trailer-breakdown (AGENT.md 5.13) for the newest of these that is a new release.
Flex slots 11:00, 17:00: trailer-breakdown when a new trailer lands, movie-review on release days, artwork-quote after a dull stretch.

## Yesterday's numbers (per reach; colour against the series median)
| reel | series | views | skip | watch | share | follow |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-13-watch-loved-jailer-2 | movie-recommendations | 131 | 70.5% green | 30.7% green | 0.0% grey | - grey |
| 2026-11-13-update-jailer2-ott | movie-updates | 703 | 85.6% green | 17.6% green | 0.0% grey | - grey |

## Trends from the news watch (top 5, no AI; verify before use)
- [10.0] How Suriya turned his biggest box office failures into a Rs 600 crore comeback · 15 publishers (6 trusted)
- [7.5] Mani Ratnam returns to romance: Vijay Sethupathi, Sai Pallavi’s Inji Vellam gets release date · 3 publishers (2 trusted)
- [6.0] Noted cinematographer Shaji Kumar passes away · 1 publishers (1 trusted)
- [6.0] Scene grosses over 200 crore; Suriya scripts Tamil cinema history · 9 publishers (3 trusted)
- [6.0] Jail Mates title teaser: KP Jagan introduces Tamil cinema's first meta film with Vijay reference · 1 publishers (1 trusted)

## Changes in force (newest first)
- #9 · 13 Nov 2026 · schedule (movie-recommendations) · Watch This Next 17:00 → 15:30, Fri–Sun · the story slot keeps one time every day; 17:00 is a flex slot and would cla
- #8 · 13 Nov 2026 · Harish's feedback, round 5 · set by Harish (hard rules)
- #7 · 13 Nov 2026 · Harish's feedback, round 4 · set by Harish (hard rules)
- #6 · 13 Nov 2026 · Harish's feedback, round 3 · set by Harish (hard rules)
- #5 · 13 Nov 2026 · Harish's feedback, round 2 · set by Harish (hard rules)

## Open alerts
- 2026-11-13 16:42 IST: The sync job did not finish
- 2026-11-13 16:42 IST: A note from the thinking run
- 2026-11-13 16:11 IST: A reel could not be posted
- 2026-11-13 12:45 IST: The make job did not finish
- 2026-11-12 07:13 IST: 1 reel(s) held for 2026-11-12

## Money and limits
- Images ₹26 of ₹500 this month
- Runner minutes: 368 of 2000 this month
- Storage: 4.22 GB of 8 GB

Plan forms: templates/<template>/plan_form.json · motion library: rules/motion.md · check: python -m engine.plancheck <file>
