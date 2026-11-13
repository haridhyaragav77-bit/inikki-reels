---
name: quiet-exit
description: Start of every run: read the master switch and the brief, stop in one step if there is nothing to do.
---
# quiet-exit
Use at the start of every run. Read data/control/switch.json (the Engine's copy of Drive
control/switch.json). If mode is "sleep", stop now.
If mode is "hold_posts", continue (planning is allowed). Then read data/brief.md. If it lists
nothing to do for this run, stop without committing anything.
