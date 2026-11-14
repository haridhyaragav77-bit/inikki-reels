---
name: plan-reel
description: Fill the plan form for a reel's look once, validate it, save it.
---
# plan-reel
Approved looks (Stage, Bulletin, Poster Wall, Verdict, Flash): the plan form is templates/README.md. Copy the
series' reference plan (plans/reference/, named under "reference" in its series.yaml) and change only the content.
Work in this order (value first, AGENT.md 5.7): lead (topic, insight, sources) → worth_it answers → script (Tamil
voice lines in short sentences; each also written word for word in Tanglish as voice_tg) → screens and motion
graphics from niches/tamil-cinema/motion_library.md → pictures last → music → package.
- Breakdowns: pin one named technique on a "technique" screen (name, and a definition of 6 words or fewer) and
  recap it on the end card ("recap": "TECHNIQUE: <NAME>"). About 1 minute.
- Read the brief first: "Today" (day, hour, season: use it in hooks and titles), "Series settings changed in the
  Control Room" (they win over the series file) and "Breakdown designs used lately".
- Breakdowns, from 15 Nov: name a design kit in "design" (spotlight, blueprint, noir, neon, paper, forest, royal) that
  the last 3 breakdowns did not use, and build the middle from the graphics that fit THIS film's idea, not the last
  reel's order: pins, technique, loop, cards, moral, standoff, timeline (moments on a line, links setup → payoff),
  meter (a dial that climbs), versus (two stills, a moving cut), web (who is tied to whom). Fields: templates/README.md.
- Watch This Next, from 15 Nov: the title screen has a "kicker" (2-4 words tying the list to today, from the brief's
  Today lines) and 2 lines that fit the day; each film has "plot" (one sentence, 16 words or fewer, no spoilers) and
  "plot_beats" (2-3 beats, 6 words or fewer each); title 3.2 s, film 6.6 s, recap 5 s at most.
- Watch This Next: every film screen has rating (Letterboxd), proof (one award, festival or famous fact), watch
  (where to watch in India, checked on JustWatch today) and a reason of 6 words or fewer. Add each film to
  niches/tamil-cinema/knowledge/recommended_log.csv.
- Updates and breaking: music-only, no spoilers, 2 trusted sources in lead.sources.
- Pictures: the film's own official stills, posters or trailer frames (AGENT.md 5.11). An official YouTube frame is
  {"src": "engine/.cache/stills/<film>/<youtube id>_maxres2.jpg"} (maxresdefault, maxres1, maxres2, maxres3);
  anything else gives "fetch": {"url": "..."}. Add "crop": [x, y, w, h] (0-1) to cut baked-in text.
  A trailer's YouTube id: the brief's library list, or curl -s -A Mozilla/5.0
  "https://www.youtube.com/results?search_query=<film>+official+trailer" | grep -o '"videoId":"[^"]*"' | head -3;
  open https://i.ytimg.com/vi/<id>/maxresdefault.jpg to check it is the film's official trailer.
- Graphics land on a word the voice says: {"cue": {"word": "<a word from that screen's Tamil line>"}}.
- Music: 1-3 parts from engine/music_index.json that follow the story; the first starts on screen 0. Bold, never subtle.
- Package: caption lines, 3-5 hashtags, cover title (it names the reel in Drive), slot, first comment.
- The id is "<date>-<short name>" (e.g. 2026-11-14-breakdown-kaithi); save it as plans/<date>/<id>.json.
Validate with: python -m engine.plancheck <plan file>. Fix what it reports, then save.
Older looks (Diorama for Guess the Movie, Cinematic for Artwork + Quote): fill templates/<template>/plan_form.json
and validate the same way.
If the check cannot start because a module is missing: pip install -q pyyaml, then run it again.
