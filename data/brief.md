# Brief · plan run · 2026-11-25 (written 2026-11-25 05:12 IST)

Switch: **run** · Phase: **live** · Respect mode: **off** · Approval: autopilot
Control Room settings copied to data/control/: switch.json, overrides.yaml, feedback.jsonl, commands.jsonl

## To do
1. Plan 6 reel(s) for 2026-11-25 at the slots below, plus 2 reserve(s) ("reserve": true). Save each to plans/2026-11-25/<reel_id>.json and check it with: python -m engine.plancheck <file>.

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
Wednesday 25 Nov 2026 · midweek, solo evening · season: Chennai rains (north-east monsoon)
Words that fit each slot's hour: 08:30 morning: TODAY / THIS WEEK · 11:00 morning: TODAY / THIS WEEK · 12:30 afternoon: TONIGHT / AFTER WORK · 18:00 evening: TONIGHT · 20:00 evening: TONIGHT · 21:30 late night: LATE NIGHT / BEFORE YOU SLEEP
Title angles for today (fill {N} and {FILM}; a film in today's news makes the strongest tie-in): RAINY NIGHT: {N} FILMS | MAZHAI + MOVIE: {N} PICKS | SOLO NIGHT: {N} FILMS | MIDWEEK ESCAPE: {N} FILMS

## Series settings changed in the Control Room (these win over the series file; AGENT.md 6.5)
- artwork-quote: per_day = 0
- film-breakdown: per_day = 2; slots = ["20:00", "21:30"]
- movie-updates: per_day = 4; slots = ["08:30", "11:00", "12:30", "18:00"]
- trailer-breakdown: status = "live"

## Releases and reviews (knowledge/releases.yaml: every Tamil release in the next 8 weeks; AGENT.md 10.5)
Calendar: 15 film(s) in the next 21 days: Cosmic Samson 11-27, Delivery Boy 11-27, Minnum Oar Iravu 11-27, Mouna Mozhigal 11-27, Benz 12-01 (tentative), Mental Manadhil 12-01 (tentative), Un Varugaikkaga Anandhi 12-01 (tentative), Valli Mayil 12-01 (tentative), The Proof 12-03 (tentative), Hello Kadhal 12-04 (tentative), Hide And Silk 12-04 (tentative), Makkal Kaavalan 12-04 (tentative).
Missed reviews: Appa Kutty (Quick), O.M: Operation Mole (Trusted), Sathyavan Savithiri (Trusted). A Trusted Review can still go out today if the reviews are in; say so in the digest.
No release today or tomorrow and no review due. Keep the calendar complete: add any confirmed date you find (2 sources).

## What the channels we study teach (AGENT.md 10.3)
Breakdowns lead with one specific detail or a true story (AGENT.md 5.7). Patterns, in our words: lab/study/patterns.md. Their best recent shorts: data/study/channels.md. Never copy their wording or order; check any story in 2 trusted sources and credit the original interview.

## Films the updates covered in the last 3 days (pick other films unless there is real new news; lead.film, lead.new_event)
- delivery-boy · dharman · hello-kadhal · mahabharat-ek-dharmayudh · mouna-mozhigal · om-day-2 · om-ott · om-weekend · pocket-novel · pongal-2027 · raawadi · scene · train · vettuvam
Today: at least 3 different films, and one update from outside the top films (smaller film, OTT drop, another-language or Hollywood release in Tamil Nadu, industry story). Use the news watch's lower-ranked stories too.

## Breakdown designs used lately (the next breakdown names another kit in "design" and a different build; AGENT.md 5.8)
- 2026-11-23-breakdown-fallout-broken-ankle: kit neon · scene → quote → versus → chain → scene
- 2026-11-23-breakdown-dune-two-infrared: kit noir · scene → source → layers → chain → scene
- 2026-11-22-breakdown-viduthalai-long-take: kit forest · timeline → meter → standoff → quote → standoff → chain → technique
- 2026-11-22-breakdown-f1-real-racing: kit blueprint · track → layers → standoff → quote → standoff → source → technique
- Cooling now (refused in the next breakdown): meter (used in 2026-11-22-breakdown-viduthalai-long-take), versus (used in 2026-11-23-breakdown-fallout-broken-ankle)
- Hero visual drawn for the film: scene (the scene builder, templates/README.md), or board, climb, track, layers, detail.

## Today's slots (2026-11-25)
| time | series | template | notes |
| --- | --- | --- | --- |
| - | guess-the-movie | paused |  |
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
- Mission: Impossible – Fallout (trailer, 50 shots, grid: clip-library/sheets/Mission  Impossible – Fallout - trailer [wb49-oV0F78].jpg)
- The Matrix (trailer, 34 shots, grid: clip-library/sheets/The Matrix - trailer [vKQi3bBA1y8].jpg)
- Avengers: Endgame (trailer, 22 shots, grid: clip-library/sheets/Avengers  Endgame - trailer [ee1172yeqyE].jpg)
- Top Gun: Maverick (trailer, 50 shots, grid: clip-library/sheets/Top Gun  Maverick - trailer [giXco2jaZ_4].jpg)
- F1 (trailer, 50 shots, grid: clip-library/sheets/F1 - trailer [69ffwl-8pCU].jpg)
- Dune: Part Two (trailer, 50 shots, grid: clip-library/sheets/Dune  Part Two - trailer [Way9Dexny3w].jpg)
- Taxi Driver (trailer, 49 shots, grid: clip-library/sheets/Taxi Driver - trailer [T5IligQP7Fo].jpg)
- Goodfellas (trailer, 26 shots, grid: clip-library/sheets/Goodfellas - trailer [2ilzidi_J8Q].jpg)
- The Shawshank Redemption (trailer, 39 shots, grid: clip-library/sheets/The Shawshank Redemption - trailer [NmzuHjWmXOc].jpg)
- Prisoners (trailer, 39 shots, grid: clip-library/sheets/Prisoners - trailer [bpXfcTF6iVk].jpg)
- Gone Girl (trailer, 35 shots, grid: clip-library/sheets/Gone Girl - trailer [2-_-1nJf8Vg].jpg)
- Se7en (trailer, 26 shots, grid: clip-library/sheets/Se7en - trailer [u5pP9dWGCu8].jpg)
- Fight Club (trailer, 41 shots, grid: clip-library/sheets/Fight Club - trailer [qtRKdVHc-cE].jpg)
- Whiplash (trailer, 20 shots, grid: clip-library/sheets/Whiplash - trailer [zIP_gtjDtfE].jpg)
- Joker (trailer, 50 shots, grid: clip-library/sheets/Joker - trailer [4xr59w5r6Hw].jpg)
- Parasite (trailer, 35 shots, grid: clip-library/sheets/Parasite - trailer [isOGD_7hNIY].jpg)
- Memento (trailer, 28 shots, grid: clip-library/sheets/Memento - trailer [xpmSH3nx6Sw].jpg)
For an older look, open a film's grid (Google Drive) and pick the shot whose picture shows each line; shot times are in data/trailers.json. Check its timeline sheet (same folder, '... - timeline.jpg', a frame every 1.5 s): the tiles from your start second for as long as the line lasts (2-4 s) must all show what the line says. Older-look visual: {type: clip, film: <film>, start: <second>, len: 2.5, label: <2-word tag>}.

## Official stills in the library (older looks; approved looks use the official frames above)
- Jailer 2: 30 stills, grid: clip-library/sheets/Jailer 2 - stills.jpg
- Scene: 30 stills, grid: clip-library/sheets/Scene - stills.jpg
- Inji Vellam: 1 stills, grid: clip-library/sheets/Inji Vellam - stills.jpg
- OM: 8 stills, grid: clip-library/sheets/OM - stills.jpg
- O.M: 11 stills, grid: clip-library/sheets/O.M - stills.jpg
- Jail Mates: 4 stills, grid: clip-library/sheets/Jail Mates - youtube.jpg
- Manikanda: 34 stills, grid: clip-library/sheets/Manikanda - youtube.jpg
Older-look visual: {type: image, still: {film: <film>, n: <number on the grid>}, ai: false, label: <2-word tag>}. Pick the still that shows what the line says; skip stills that are mostly text.

## Trailers expected (announced dates)
- Hello Kadhal: To Drop Today (Hello Kadhal Trailer Release Time: Arya, Nikhila Vimal & Vaishnavi Chaitanya's F)

## New trailers in the library (last 3 days)
- Mission: Impossible – Fallout (trailer, grid: clip-library/sheets/Mission  Impossible – Fallout - trailer [wb49-oV0F78].jpg)
- The Matrix (trailer, grid: clip-library/sheets/The Matrix - trailer [vKQi3bBA1y8].jpg)
- Avengers: Endgame (trailer, grid: clip-library/sheets/Avengers  Endgame - trailer [ee1172yeqyE].jpg)
- Top Gun: Maverick (trailer, grid: clip-library/sheets/Top Gun  Maverick - trailer [giXco2jaZ_4].jpg)
- F1 (trailer, grid: clip-library/sheets/F1 - trailer [69ffwl-8pCU].jpg)
- Dune: Part Two (trailer, grid: clip-library/sheets/Dune  Part Two - trailer [Way9Dexny3w].jpg)
Flex slot: plan one trailer-breakdown (AGENT.md 5.13) for the newest of these that is a new release.
Flex slots 11:00, 17:00: trailer-breakdown when a new trailer lands, movie-review (Quick Review) on release days, trusted-review 1-4 days after a release. Turned off by Harish: artwork-quote.

## Yesterday's numbers (per reach; colour against the series median)
| reel | series | views | skip | watch | share | follow |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-11-24-update-om-ott-netflix | movie-updates | 43 | 48.4% green | 34.3% green | 0.0% grey | - grey |
| 2026-11-15-breakdown-virumaandi | film-breakdown | 2061 | 46.4% green | 24.1% green | 1.1% green | - grey |
| 2026-11-24-update-hello-kadhal-trailer | movie-updates | 147 | 68.7% amber | 24.9% amber | 0.0% grey | - grey |
| 2026-11-16-breakdown-jigarthanda | film-breakdown | 391 | 58.9% green | 11.9% red | 0.9% green | - grey |

## Trends from the news watch (top 5, no AI; verify before use)
- [14.0] OM box office collection Day 2: Dhanush-Mammootty film sees 14.9% drop, earns Rs 60 crore · 31 publishers (8 trusted)
- [11.2] 'O.M' OTT release date: Here's when and where you can watch Dhanush, Mammootty, Sai Pallavi and Sreeleela · 16 publishers (4 trusted)
- [11.2] Dhanush, Mammootty-starrer Om's trailer springs a surprise; reveals Dhanush is with the TN intelligence unit · 33 publishers (9 trusted)
- [11.2] OM worldwide box office collection day 3: Dhanush gets his biggest opening weekend as makers say film with Mam · 7 publishers (4 trusted)
- [10.0] How Suriya turned his biggest box office failures into a Rs 600 crore comeback · 31 publishers (8 trusted)

## Changes in force (newest first)
- #17 · 19 Nov 2026 · series (film-breakdown) · stock graphics reused across reels, scripts that let viewers drift → illustrated graphics drawn for the film's idea (at most
- #16 · 19 Nov 2026 · series (film-breakdown, trailer-breakdown) · a named technique as the hook, 40-62 s, one film once in 21 days → lead with one specific detail or a tru
- #15 · 15 Nov 2026 · series (movie-updates) · stills cropped tight and titles that did not say the news → soft rule: keep faces and the key subject whole (crop only to cut
- #14 · 14 Nov 2026 · rule (news watch) · a small film's trailer could not reach the score that wakes the Breaking run → fast pages (@chennaiist) are read at every pass; a 
- #13 · 14 Nov 2026 · rule (all series) · hooks and titles were timeless → every brief opens with Today (day, hour, season, festivals, title angles); Watch This Next must u

## Open alerts
- 2026-11-24 21:33 IST: A reel could not be posted
- 2026-11-24 16:39 IST: A note from the thinking run

## Money and limits
- Images ₹26 of ₹500 this month
- Runner minutes: 3415 used this month. No limit (the repository is public): plan the full day, reserves included, nothing held back for minutes.
- Storage: 7.54 GB of 15 GB

Plan forms: templates/<template>/plan_form.json · motion library: rules/motion.md · check: python -m engine.plancheck <file>
