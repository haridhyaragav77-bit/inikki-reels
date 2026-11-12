---
name: plan-reel
description: Fill the plan form for a reel's template once, validate it, save it.
---
# plan-reel
Fill the plan form for the series' template in templates/<template>/plan_form.json. Fill every
field once: lead, hook, screens, visuals, motion graphic, music, meme, voice lines with both
subtitles (Tanglish and Tamil), caption, hashtags, cover, time, fallbacks. Pick each motion
graphic from rules/motion.md by what the line says. Keep each screen to one line of headline.
Validate with: python -m engine.plancheck <plan file>. Fix what it reports, then save.
Breakdowns: copy the structure of plans/reference/kaithi-breakdown.json (AGENT.md 5.10): 45 s, 16-19 screens,
3 named points, each proven by specific scenes of the film. Breakdowns and updates use only trailer clips of a film
listed in the brief: open its shot grid (Google Drive, clip-library/sheets/), pick the shot that shows what each line
says, and write {type: clip, film, start: shot start + 0.2, len: 2.5, label}. Times are in data/trailers.json.
A news film with no trailer in the library yet: write the plan without start seconds and add
"trailer_from": [its studio, label or star Instagram accounts] so the Engine searches those first. The reel waits;
when the trailer arrives the brief lists it under "Re-pick moments" and you fill the seconds from its grid.
Stories: AI pictures for the build-up, written as exact film shots with one character description repeated word for
word; the reveal beat uses {trailer: {film, at}} from the person's own trailer.
If the check cannot start because a module is missing: pip install -q pyyaml, then run it again.
