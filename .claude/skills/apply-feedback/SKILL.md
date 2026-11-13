---
name: apply-feedback
description: Turn each piece of Harish's feedback or standing rule into one numbered change, in a fixed form.
---
# apply-feedback
Input: "New feedback from Harish" and "Harish's standing rules" in data/brief.md. Nothing else is read.
For each item, pick ONE row of AGENT.md 8.3 by its reason and do only that:
- Fact wrong / Spoiler → one line in data/out/alerts.md naming the reel (the Advisor handles the correction).
- Not worth it → one line under that series in rules/playbook.md: "Avoid: <topic or angle>".
- Taste note (hook slow, too long, too wordy, too static, unclear title, visuals weak) → a soft rule for that series,
  tried on the next 5 reels.
- Praise → add the reel id as an example under that series in rules/playbook.md.
- A standing rule that has stood a week → a hard rule in rules/playbook.md, "set by Harish".
Log each in rules/changes.md in the short form:
`#n · date · scope (series) · before → after · why (Harish: "<his words>") · status (test on 5 reels | rule, set by Harish) · undo: <how>`
One line per change. The same note three times is a hard rule at once (8.4). Never argue with a taste note.
