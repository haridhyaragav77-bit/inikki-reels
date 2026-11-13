# Brief · plan run · 2026-11-13 (written 2026-11-13 12:22 IST)

Switch: **run** · Phase: **rehearsal** (nothing posts; plan exactly as if live) · Respect mode: **off** · Approval: autopilot
Control Room settings copied to data/control/: switch.json

## To do
1. Plan 6 reel(s) for 2026-11-13 at the slots below, plus 2 reserve(s) ("reserve": true). Save each to plans/2026-11-13/<reel_id>.json and check it with: python -m engine.plancheck <file>.

## Today's slots (2026-11-13)
| time | series | template | notes |
| --- | --- | --- | --- |
| 08:30 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 12:30 | film-breakdown | stage | voice, 40-62 s |
| 15:30 | movie-recommendations | poster-wall | no voice, 20-45 s |
| 18:00 | movie-updates | bulletin | voice: case by case, 15-30 s |
| 20:00 | film-breakdown | stage | voice, 40-62 s |
| 21:30 | movie-updates | bulletin | voice: case by case, 15-30 s |

## Trailers in the clip library (breakdowns and updates may only use these films)
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
Open a film's grid (Google Drive) and pick the shot whose picture shows each line; shot times are in data/trailers.json. Then check its timeline sheet (same folder, '... - timeline.jpg', a frame every 1.5 s): the tiles from your start second for as long as the line lasts (2-4 s) must all show what the line says; trailers dissolve between shots. Visual: {type: clip, film: <film>, start: <second>, len: 2.5, label: <2-word tag>}.

## Official stills (movie updates may use these when the film has no clips)
- Jailer 2: 30 stills, grid: clip-library/sheets/Jailer 2 - stills.jpg
- Scene: 30 stills, grid: clip-library/sheets/Scene - stills.jpg
- Inji Vellam: 1 stills, grid: clip-library/sheets/Inji Vellam - stills.jpg
Visual: {type: image, still: {film: <film>, n: <number on the grid>}, ai: false, label: <2-word tag>}. Pick the still that shows what the line says; skip stills that are mostly text.

## New trailers in the library (last 3 days)
- Lubber Pandhu (trailer, grid: clip-library/sheets/Lubber Pandhu - trailer [oP88LHBukW8].jpg)
- Master (trailer, grid: clip-library/sheets/Master - trailer [1_iUFT3nWHk].jpg)
- Maaveeran (trailer, grid: clip-library/sheets/Maaveeran - trailer [EcNACt-LOi0].jpg)
- Amaran (trailer, grid: clip-library/sheets/Amaran - trailer [hylIXfZeB4c].jpg)
- Jailer (trailer, grid: clip-library/sheets/Jailer - trailer [Y5BeWdODPqo].jpg)
- Leo (trailer, grid: clip-library/sheets/Leo - trailer [Po3jStA673E].jpg)
Flex slot: plan one trailer-breakdown (AGENT.md 5.13) for the newest of these that is a new release.
Flex slots 11:00, 17:00: trailer-breakdown when a new trailer lands, movie-review on release days, artwork-quote after a dull stretch.

## Today's reels
| slot | reel | series | state | note |
| --- | --- | --- | --- | --- |
| 18:00 | 2026-11-13-pipeline-test-update | movie-updates | ready |  |
| 20:00 | 2026-11-13-pipeline-test-breakdown | film-breakdown | ready |  |

## Yesterday's numbers (per reach; colour against the series median)
Rehearsal: nothing posted yet, so no numbers.

## Trends from the news watch (top 5, no AI; verify before use)
- [20.0] How Suriya turned his biggest box office failures into a Rs 600 crore comeback · 13 publishers (6 trusted)
- [6.2] Mani Ratnam returns to romance: Vijay Sethupathi, Sai Pallavi’s Inji Vellam gets release date · 2 publishers (1 trusted)
- [6.0] Noted cinematographer Shaji Kumar passes away · 1 publishers (1 trusted)
- [4.5] மணிரத்னத்தின் ‘இஞ்சி வெல்லம்’ ஜன.29-ல் ரிலீஸ் · 6 publishers (1 trusted)
- [4.0] Jithu Madhavan reveals the plot twist of Suriya starrer 'Scene' was leaked before the first look, admits · 1 publishers (1 trusted)

## Changes in force (newest first)
- #9 · 13 Nov 2026 · schedule (movie-recommendations) · Watch This Next 17:00 → 15:30, Fri–Sun · the story slot keeps one time every day; 17:00 is a flex slot and would cla
- #8 · 13 Nov 2026 · Harish's feedback, round 5 · set by Harish (hard rules)
- #7 · 13 Nov 2026 · Harish's feedback, round 4 · set by Harish (hard rules)
- #6 · 13 Nov 2026 · Harish's feedback, round 3 · set by Harish (hard rules)
- #5 · 13 Nov 2026 · Harish's feedback, round 2 · set by Harish (hard rules)

## Open alerts
- 2026-11-12 07:13 IST: 1 reel(s) held for 2026-11-12
- 2026-11-12 06:50 IST: 5 reel(s) held for 2026-11-12
- 2026-11-12 06:30 IST: 5 reel(s) held for 2026-11-12
- 2026-11-12 06:22 IST: Health check: 2 thing(s) need a look

## Money and limits
- Images ₹26 of ₹500 this month
- Runner minutes: 368 of 2000 this month
- Storage: 3.07 GB of 8 GB

Plan forms: templates/<template>/plan_form.json · motion library: rules/motion.md · check: python -m engine.plancheck <file>
