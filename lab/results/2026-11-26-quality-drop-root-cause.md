# Quality drop, 23-25 Nov: root cause (26 Nov 2026)

**Harish:** reels look weaker than the Suriya ₹643 Cr update of 21 Nov.

## What the plans show (screens between the title and the end)
| Day | Writer of the Plan run | Movie updates | Sound hits a reel |
| --- | --- | --- | --- |
| 20-21 Nov | Opus | count-ups (`number`) and bar charts (`bars`) in every update | 7 |
| 22-23 Nov | Opus | one animated screen, the rest text cards | 6 |
| 24-25 Nov | **Sonnet** (from 23 Nov, 15:28 IST, token audit) | **text cards only** (`title`, `title`, `title`) | 5 |

Same story twice: 21 Nov Suriya ₹643 Cr = title, bars, bars, end. 25 Nov Suriya ₹770 Cr = title, title, title, end,
with "₹770 CR" typed as words on a still. Breakdowns: 9-10 screens and 11-12 hits (20-22 Nov), 6 screens and 6 hits on 25 Nov.
The renderer did not change (no change to templates/ or the renderer since 22 Nov).

## Why it got through
The plan check counted screens and rules but never how much moved. Any model can write a valid but still reel.

## Fix
1. Plan and Refresh back on Opus medium (`config/agent.yaml` `thinking_models`).
2. The Plan run builds each reel like its series' reference plan, not less, not more (`runs/plan.md`). No hard animation
   count (Harish, 26 Nov: a floor would push plans to over-animate). Opus at medium effort, not high (cheaper, enough).
