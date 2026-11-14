---
name: series-change
description: The fixed steps to add, replace, pause or retire a series, with the tests to run. Workshop sessions only.
---
# series-change
A series is one folder: niches/<niche>/series/<id>/series.yaml. A lineup (niches/<niche>/lineups/<name>.yaml) says which
series fill the day. Nothing about a series lives in code (CLAUDE.md rule 1).

Pause or resume (no build needed): the Control Room does it: {"do":"series","id":"<id>","set":{"paused":true}}.

Every series card is the same 7 blocks (config/framework.yaml): basics, structure, visuals, voice, music, caption,
rules. Harish can change any field, add a series (it starts as lab), test, feed sample reels and retire from the
Control Room page with no tokens; those changes live in Drive control/overrides.yaml and the brief lists them.
In the Workshop, fold them into the series file when asked ("make the Control Room changes permanent").

Train a series from sample reels: say in 3 lines what makes each sample work, ask up to 5 short questions one at a
time, turn the answers into block-by-block changes (before → after), apply the approved ones, run the tests, make one
test reel (python -m engine.render <its reference plan> --to-drive rehearsal/tests/<id>).

Change a series (times, length, rules, title screen): edit its series.yaml. Log one line in rules/changes.md.

Add a series:
1. Copy the nearest series.yaml; set id, name, status: trial, template (one of templates/), slots, length_s, rules,
   title_screen, music, motion_presets, worth_it_extra (the standard, AGENT.md 5.10).
2. Add a reference plan in plans/reference/ and name it under `reference:`. It must pass python -m engine.plancheck.
3. Put it in the lineup: a fixed slot, the story slot, or flex.
4. Test: python -m tests.test_control_room, then print tomorrow's lineup and read the TOMORROW line:
   python -c "from tests.test_control_room import FakeDrive; from engine import panel; print(panel.text(panel.build(FakeDrive())))"
5. A new look (template) is a separate build: templates/<name>/ + its plan form + a golden reel (CLAUDE.md rule 3).

Replace: add the new one as above, then set the old one's status: retired and take it out of the lineup.
Retire: status: retired, out of the lineup. Never delete the folder (its history and reference stay).

Always: AGENT.md 6.2 table and rules/changes.md updated in the same commit. Tell Harish in 3 lines what changed and
from which day it shows.
