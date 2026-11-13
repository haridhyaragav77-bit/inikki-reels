---
name: weekly-learn
description: Read the computed week table, undo changes that hurt, and output at most 5 numbered changes.
---
# weekly-learn
Read data/week_table.md only. First: every change it marks REVERT gets its Undo applied, logged as a
new numbered change. Changes marked "Harish's own rule" stay; put their numbers in the weekly report.
If the table says "Small numbers rule", make no rule changes. Otherwise, for each series: weakest
priority metric, one cause, one fix from AGENT.md table 2.4. Output at most 5 numbered changes:
target, before → after, evidence, test or rule, undo. Respect the limits in config/agent.yaml learning.
