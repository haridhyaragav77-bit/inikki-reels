# Why breakdowns slide back to the old look (Priority 1A, 22 Nov 2026)

**In one line:** the 3 good reels were hand-built in the Workshop, with a new visual coded for each film. The daily
agent can't build visuals, and its instructions still point at the old screens, so it falls back to them.

## What we compared
All 18 breakdown plans from 14–22 Nov: the 3 good ones (Joker, Thani Oruvan, F1) and 15 the agent made on its own.

| Screen | Times in the 15 agent reels |
| --- | --- |
| `meter` (the speedometer) | 8 |
| `timeline` | 8 |
| `board` / `climb` / `track` (evidence board, staircase, race track) | 0 |
| `layers` | 1 |

## The 5 causes
1. **The custom visuals were coded by hand, one per film.** The staircase (Joker), evidence board (Thani Oruvan) and race
   track (F1) were written as new template code in a Workshop session. The daily agent writes only plan text, so it can
   pick from the library but never build. The rule "pick or build the illustration" only ever means "pick".
2. **The agent's instructions still list the old screens.** The breakdown series card
   (`niches/tamil-cinema/series/film-breakdown/series.yaml`, `graphics:`) lists the 14 old screens, speedometer included,
   and leaves out the 4 new ones. The reference reel it is told to copy is still the 13 Nov Vikram Vedha reel.
   AGENT.md 5.8 still names the old set too.
3. **The menu promises graphics that don't exist.** The motion library describes 68 graphics (camera path, light map, cut
   rhythm, fight map...), but the breakdown look can draw only 20. Viduthalai's one-shot train scene needed a camera
   path. There isn't one, so it got a timeline and a speedometer.
4. **The fixed structure makes every reel look alike.** The spine fixes 5 of every 9 screens: title, two "standoff"
   teasers, technique and end. The repeat check compares only with the last 2 reels and passes if one screen differs.
5. **The script is padded and not checked line by line.** The structure pushes a "3 secrets" filler. Viduthalai copied
   F1's "மூணு ரகசியம்" line. Facts are checked only by counting source links, not claim by claim, which leaves room for
   made-up details.

**Not the cause:** the GitHub render. It draws exactly what the plan says, and no code swaps one graphic for another.

## Fix plan (1B + 1C, for approval)
1. **Today, cheap:** point the agent at the new look. Update the series card's graphics list, make F1 the reference reel,
   and keep the speedometer out of breakdowns unless the point is about a number.
2. **Scene builder:** one new graphic the plan describes as data (objects, paths, moves), for example a train of coaches
   with a camera gliding through. Each breakdown gets its own visual without new code.
3. **No fixed structure:** a strong hook, one clear point, and the loop ending. Drop the "3 secrets" filler and the fixed
   standoff, technique and end screens.
4. **Fact check per line:** every claim in the script names its saved source; a claim without one is cut.
5. **Stronger repeat check:** compare with the last 10 breakdowns, not 2.
