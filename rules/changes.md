# Change log

Every change has a number, a reason and an Undo (AGENT.md 1, 9). Newest first.

## #2 · 13 Nov 2026 · Harish's feedback, round 2 · set by Harish (hard rules)
**Why:** the motion graphics need much more animation, the new way of making reels must be the standard everywhere, and Movie Review and Breaking News need their own looks too.

**What changed:**
1. Lots of animation: nothing sits still for more than a second; enter, move and leave with motion; hits on the beat; moving transitions. The inspect stage checks for frozen pictures (AGENT.md 5.8, stage 8; motion library "Animation toolkit").
2. One standard for every reel, in every series and every Lab pilot (AGENT.md 5.10). New series must set their title screen, look, motion, music, voice and worth-it questions first. A niche switch keeps the standard.
3. Movie Review gets its own **Verdict** look; Breaking News gets its own **Flash** look (AGENT.md 6.6). 7 templates in all.
4. Every series file now names its title screen, music, motion graphics and extra worth-it questions.

**Undo:** revert this commit.

## #1 · 13 Nov 2026 · Harish's feedback on the first reels · set by Harish (hard rules)
**Why:** some breakdowns opened with about 5 seconds of silence, then calm music played under intense moments. Graphics were wordy and repeated, and didn't help people follow along. Scripts were built around the pictures that could be found, not around an insight. The opening text didn't say what the reel was about. Updates, Breakdowns and Recommendations all looked the same. Updates gave away spoilers.

**What changed:**
1. Value is the hero: insight → script → motion graphics → visuals last. A worth-it test runs before every script (AGENT.md 1, 5.7).
2. Topic scoring: Value 25 and Relevance 20 lead; "visuals ready" drops from 15 to 5. Cult classics and current films first (5.1, 10.1).
3. Breakdowns cover any craft: screenplay, camera, set, editing, sound, acting.
4. Screen 1 is a big title saying the film and what the reel is (5.3).
5. Motion graphics show the idea, stay on pace with the voice, use 3 words or fewer, never repeat in a reel, and come from a shared library (5.8, `niches/tamil-cinema/motion_library.md`).
6. Music starts on frame 1 and follows the story in 2–3 sections. The inspect stage checks both (5.4, stage 8).
7. Length is set by the content: usually 45 s or less, breakdowns up to 75 s (5.9).
8. Updates: no spoilers, a title saying exactly what the update is, often music-only (series file).
9. Each series gets its own look: Stage, Bulletin, Poster Wall (6.6).
10. New trial series: Watch This Next (movie recommendations), Fri–Sun 17:00 (6.2).

**Undo:** revert this commit. Taste rules from Harish are kept even if numbers disagree, but the Advisor will show both (AGENT.md 8.4).
