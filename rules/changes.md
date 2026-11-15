# Change log

Every change the agent makes or Harish asks for gets a number, a reason, evidence and an Undo (AGENT.md 1, 9).
Newest first. #1 to #3 come from the first build (11 Nov); #4 to #8 are Harish's five rounds of feedback on the reels (13 Nov).
Short format for small changes:

`#n · date · scope (series / role / rule / schedule / brand) · before → after · why (evidence) · status (test on 5 reels / rule / undone)`

---

`#15 · 15 Nov 2026 · series (movie-updates) · stills cropped tight and titles that did not say the news → soft rule: keep faces and the key subject whole (crop only to cut baked-in text or channel marks, never into heads), and the title says the news in plain words (who + what, a number if there is one) · why (Harish: "Images cropped too much, poor titles", 2/5 on 2026-11-14-update-shaji-kumar-tribute) · test on 5 reels · undo: delete the movie-updates soft rule in rules/playbook.md`

`#14 · 14 Nov 2026 · rule (news watch) · a small film's trailer could not reach the score that wakes the Breaking run → fast pages (@chennaiist) are read at every pass; a trailer, teaser, first look or release date wakes it with 2 trusted sources, or one fast page naming the official account · Harish: the Ohm trailer was out and the page had nothing · rule · undo: Setup → "Watch fast pages" off, or `fire_score_drop: 8` in sources.yaml`

`#13 · 14 Nov 2026 · rule (all series) · hooks and titles were timeless → every brief opens with Today (day, hour, season, festivals, title angles); Watch This Next must use it · Harish: "Friday night, date night movies; midweek solo night" · rule · undo: Setup → "Calendar awareness" off`

`#12 · 14 Nov 2026 · rule (film-breakdown, trailer-breakdown) · every breakdown had the same gold stage and the same six screens in the same order → each names a design kit not used in the last 3 and a build not used in the last 2; 4 new graphics (timeline, meter, versus, web) · Harish: "repetitive pattern; unique motion graphics are the USP of the page" · rule from 15 Nov · undo: remove `unique_design` from the two series cards`

`#11 · 14 Nov 2026 · series (movie-recommendations) · weak hook frame, 7.6 s per film, plot never shown → title big in the middle of a moving poster wall with a timely kicker; a plot beat (2-3 beats, no spoilers) after each film card; title 3.2 s, film 7.4 s with the plot beat inside, recap 5 s at most · Harish: "people look at the centre of the screen; add the plot; move faster" · rule from 15 Nov · undo: remove `pace` from the series card (the look itself: revert templates/poster-wall/template.js)`

`#10 · 14 Nov 2026 · rule (voice) · Microsoft voice on every reel → ElevenLabs is the main voice (Ashwin, speed 1.1), Microsoft the backup; one take per line, kept and reused · Harish: "ElevenLabs was connected but not used; do not do 2 drafts" · rule · undo: Setup → Main voice → Microsoft`

`#9 · 13 Nov 2026 · schedule (movie-recommendations) · Watch This Next 17:00 → 15:30, Fri–Sun · the story slot keeps one time every day; 17:00 is a flex slot and would clash with release-day reviews on Fridays · rule · undo: slots back to ["17:00"] in the series card`

## #8 · 13 Nov 2026 · Harish's feedback, round 5 · set by Harish (hard rules)
**Why:** viewers may miss the voice; the breakdown didn't pin down exactly what the insight was; the Letterboxd rating was hard to read; reels need the page name.

**What changed:**
1. Voiced reels open with "TURN SOUND ON" (AGENT.md 5.3).
2. Every breakdown pins a named technique (frame story, ticking clock, match cut, leitmotif...): named on screen, defined, shown, explained, recapped (5.7).
3. Breakdowns aim for about 1 minute; shorter is fine (5.9).
4. Watch This Next: a bigger rating ring and a clear LETTERBOXD label.
5. Every reel ends with @inikki_reels (5.3).
6. This set of five reels is the new reference for each look; the earlier reference reels are retired (6.6).

**Undo:** revert this commit.

## #7 · 13 Nov 2026 · Harish's feedback, round 4 · set by Harish (hard rules)
**Why:** the Vikram Vedha reel had no subtitles; Instagram's right-side buttons and bottom profile/caption area can cover words; reels must reach Drive.

**What changed:**
1. Breakdowns carry Tamil + Tanglish subtitles synced to the voice, the spoken word lit (AGENT.md 5.3).
2. Breakdowns keep every word and key visual in the Instagram-safe column, with a band for subtitles (5.3, 6.6).
3. Everything goes through Drive: the "Make reels" cloud workflow renders and uploads full-quality reels to Drive and reads music from it (4.3, 19). Phone previews go to `rehearsal/<date>/` until the one-time Drive sign-in is added.
4. Every reel's sound is levelled to a fixed loudness: bold, but never so loud that Instagram squashes it.

**Undo:** revert this commit.

## #6 · 13 Nov 2026 · Harish's feedback, round 3 · set by Harish (hard rules)
**Why:** the motion graphics and style got a big yes. The Updates and Watch This Next music was too quiet to work as a hook. Recommendations needed proof (Letterboxd, reviews) and where to watch. The Inji Vellam reel was missing its official poster.

**What changed:**
1. The look and motion graphics are approved: keep this style.
2. Music is bold, never subtle: catchy, loud, recognisable, starting on its strongest part (AGENT.md 5.4).
3. Every recommended film shows proof (Letterboxd rating + one award, festival or famous fact) and where to watch in India from JustWatch; films not streaming in India are swapped (5.7, 6.6).
4. Breaking news always scouts the official poster and stills; with no visuals, lead with the biggest name (6.6).
5. Voice and rendering run only in the cloud, never on Harish's laptop (4.4).

**Undo:** revert this commit.

## #5 · 13 Nov 2026 · Harish's feedback, round 2 · set by Harish (hard rules)
**Why:** the motion graphics need much more animation, the new way of making reels must be the standard everywhere, and Movie Review and Breaking News need their own looks too.

**What changed:**
1. Lots of animation: nothing sits still for more than a second; enter, move and leave with motion; hits on the beat; moving transitions. The inspect stage checks for frozen pictures (AGENT.md 5.8, stage 8; motion library "Animation toolkit").
2. One standard for every reel, in every series and every Lab pilot (AGENT.md 5.10). New series must set their title screen, look, motion, music, voice and worth-it questions first. A niche switch keeps the standard.
3. Movie Review gets its own **Verdict** look; Breaking News gets its own **Flash** look (AGENT.md 6.6). 7 templates in all.
4. Every series file now names its title screen, music, motion graphics and extra worth-it questions.

**Undo:** revert this commit.

## #4 · 13 Nov 2026 · Harish's feedback on the first reels · set by Harish (hard rules)
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

---

`#3 · 11 Nov 2026 · series (viral-story) · the person was named in the hook → unnamed until a reveal near the end ("None other than …") · Harish: curiosity, and the inspired-by pictures do not match the real face · rule · undo: remove the first rule in the series card`

`#2 · 11 Nov 2026 · rule (all series) · reels opened on a calm first frame → every reel opens on a visual hook, pictures change with a transition, Guess the Movie scenes are 3D (AGENT.md 5.8) · Harish, after the first golden reels: "premium, a visual hook, brighter" · rule · undo: set hook to none in the series cards`

`#1 · 11 Nov 2026 · brand · page Night Navy → Marquee Indigo with Screen Violet light; muted text a step lighter · Harish: "slightly more brighter colours because people are scrolling" · rule · undo: in brand_tokens.json put gradient.previous_card_background back as card_background and remove indigo and glow from brand.yaml`
