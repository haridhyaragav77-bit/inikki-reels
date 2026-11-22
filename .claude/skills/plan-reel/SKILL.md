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
- Breakdowns (from 23 Nov, Harish): write "lead.point" FIRST: one sentence of 25 words or fewer, what the viewer knows
  after watching. No fixed structure: the hook (title screen), the point told in the order that lands best for this
  film (2-6 screens), the end. Every screen except the end has "src" (the number of its link in lead.sources, or
  "analysis"); at least 2 sources, checked by web search. No formula phrases ("3 secrets", "secret 1"): the series
  card's avoid_phrases. A named technique only when it makes the point clearer (then name, definition of 6 words or
  fewer, recap on the end card).
- Read the brief first: "Today" (day, hour, season: use it in hooks and titles), "Series settings changed in the
  Control Room" (they win over the series file) and "Breakdown designs used lately".
- Breakdowns: name a design kit in "design" that the last 3 breakdowns did not use (the brief lists them). Draw the
  film's idea: one hero visual made for THIS film, best a "scene" (the scene builder: drawn props that move and act on
  the voice's words; copy plans/reference/breakdown-scene-viduthalai.json and templates/README.md), else board, climb,
  track, layers or detail when it shows the thing itself. Stock graphics the brief lists as cooling are refused.
- Watch This Next, from 15 Nov: the title screen has a "kicker" (2-4 words tying the list to today, from the brief's
  Today lines) and 2 lines that fit the day; each film has "plot" (one sentence, 16 words or fewer, no spoilers) and
  "plot_beats" (2-3 beats, 6 words or fewer each); title 3.2 s, film 7.4 s (card, then plot), recap 5 s at most.
- Watch This Next: every film screen has rating (Letterboxd), proof (one award, festival or famous fact), watch
  (where to watch in India, checked on JustWatch today) and a reason of 6 words or fewer. Add each film to
  niches/tamil-cinema/knowledge/recommended_log.csv.
- Updates and breaking: music-only, no spoilers, 2 trusted sources in lead.sources.
- Reviews (from 23 Nov): Quick Review (movie-review, release day) or Trusted Review (trusted-review, only reviewers from
  niches/tamil-cinema/knowledge/critics.yaml, at least 3). Copy plans/reference/review-quick.json or review-trusted.json.
  List every review in "rating" (stars as the critic gave them, else a verbal word), run the plan check: it prints the
  score and the answer (GO / WAIT / SKIP) to put in "rating" and on the stars screen. Never guess a score.
- Pictures: the film's own official stills, posters or trailer frames (AGENT.md 5.11). An official YouTube frame is
  {"src": "engine/.cache/stills/<film>/<youtube id>_maxres2.jpg"} (maxresdefault, maxres1, maxres2, maxres3);
  anything else gives "fetch": {"url": "..."}. Add "crop": [x, y, w, h] (0-1) to cut baked-in text.
  A trailer's YouTube id: the brief's library list, or curl -s -A Mozilla/5.0
  "https://www.youtube.com/results?search_query=<film>+official+trailer" | grep -o '"videoId":"[^"]*"' | head -3;
  open https://i.ytimg.com/vi/<id>/maxresdefault.jpg to check it is the film's official trailer.
- Graphics land on a word the voice says: {"cue": {"word": "<a word from that screen's Tamil line>"}}.
- Music: 1-3 parts that follow the story; the first starts on screen 0. Bold, never subtle. A trending song (brief:
  "Trending songs", data/music/trending.json) is the first choice when its mood fits: "track" = its key, "from" = its
  hook_at. Otherwise the library, engine/music_index.json.
- Package: caption lines, 3-5 hashtags, cover title (it names the reel in Drive), slot, first comment.
- The id is "<date>-<short name>" (e.g. 2026-11-14-breakdown-kaithi); save it as plans/<date>/<id>.json.
Breakdowns: start from the study cards (data/study/), bend the source (series card `bend`), check every fact by web
search (Wikipedia production section, IMDb trivia, interviews) and give each screen its "src". 8-18 words a screen;
"tail": 0.12 on every screen but the title. Before saving, read the script aloud in your head: if a screen does not
serve lead.point, cut it.
Pictures: the YouTube frames grid for the film (brief: Official stills, source youtube) or {"fetch": {"youtube": id, "frame": f}}.
Validate with: python -m engine.plancheck <plan file>. Fix what it reports, then save.
Older looks (Diorama for Guess the Movie, Cinematic for Artwork + Quote): fill templates/<template>/plan_form.json
and validate the same way.
If the check cannot start because a module is missing: pip install -q pyyaml, then run it again.
