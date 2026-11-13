# Change log

Every change has a number, a reason and an Undo (AGENT.md 1, 9). Newest first.

## #4 · 13 Nov 2026 · Harish's feedback, round 4 · set by Harish (hard rules)
**Why:** the Vikram Vedha reel had no subtitles; Instagram's right-side buttons and bottom profile/caption area can cover words; reels must reach Drive.

**What changed:**
1. Breakdowns carry Tamil + Tanglish subtitles synced to the voice, the spoken word lit (AGENT.md 5.3).
2. Breakdowns keep every word and key visual in the Instagram-safe column, with a band for subtitles (5.3, 6.6).
3. Everything goes through Drive: the "Make reels" cloud workflow renders and uploads full-quality reels to Drive and reads music from it (4.3, 19). Phone previews go to `rehearsal/<date>/` until the one-time Drive sign-in is added.
4. Every reel's sound is levelled to a fixed loudness: bold, but never so loud that Instagram squashes it.

**Undo:** revert this commit.

## #3 · 13 Nov 2026 · Harish's feedback, round 3 · set by Harish (hard rules)
**Why:** the motion graphics and style got a big yes. The Updates and Watch This Next music was too quiet to work as a hook. Recommendations needed proof (Letterboxd, reviews) and where to watch. The Inji Vellam reel was missing its official poster.

**What changed:**
1. The look and motion graphics are approved: keep this style.
2. Music is bold, never subtle: catchy, loud, recognisable, starting on its strongest part (AGENT.md 5.4).
3. Every recommended film shows proof (Letterboxd rating + one award, festival or famous fact) and where to watch in India from JustWatch; films not streaming in India are swapped (5.7, 6.6).
4. Breaking news always scouts the official poster and stills; with no visuals, lead with the biggest name (6.6).
5. Voice and rendering run only in the cloud, never on Harish's laptop (4.4).

**Undo:** revert this commit.

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
