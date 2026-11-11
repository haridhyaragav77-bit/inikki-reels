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
