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
- Watch This Next: every film screen has rating (Letterboxd), proof (one award, festival or famous fact), watch
  (where to watch in India, checked on JustWatch today) and a reason of 6 words or fewer. Add each film to
  niches/tamil-cinema/knowledge/recommended_log.csv.
- Updates and breaking: music-only, no spoilers, 2 trusted sources in lead.sources.
- Pictures: the film's own official stills, posters or trailer frames (AGENT.md 5.11). An official YouTube frame is
  {"src": "engine/.cache/stills/<film>/<youtube id>_maxres2.jpg"} (maxresdefault, maxres1, maxres2, maxres3);
  anything else gives "fetch": {"url": "..."}. Add "crop": [x, y, w, h] (0-1) to cut baked-in text.
- Graphics land on a word the voice says: {"cue": {"word": "<a word from that screen's Tamil line>"}}.
- Music: 1-3 parts from engine/music_index.json that follow the story; the first starts on screen 0. Bold, never subtle.
- Package: caption lines, 3-5 hashtags, cover title (it names the reel in Drive), slot, first comment.
- The id is "<date>-<short name>" (e.g. 2026-11-14-breakdown-kaithi); save it as plans/<date>/<id>.json.
Validate with: python -m engine.plancheck <plan file>. Fix what it reports, then save.
Older looks (Diorama for Guess the Movie, Cinematic for Artwork + Quote): fill templates/<template>/plan_form.json
and validate the same way.
If the check cannot start because a module is missing: pip install -q pyyaml, then run it again.
