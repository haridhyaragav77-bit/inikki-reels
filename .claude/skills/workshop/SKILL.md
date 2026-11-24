---
name: workshop
description: How a build session on inikki-reels starts cheaply, tests, and ships. Use at the start of any Workshop task.
---
# workshop
Read first, and only these: CLAUDE.md, GUIDE.md section 2 (who does what), and `grep -n '^#' AGENT.md` for the map.
Open AGENT.md by section (sed -n 'a,bp'), never whole: it is long. BUILD_LOG.md: the newest entry only (it is at the top: `sed -n '1,40p'`).
A project hook refuses a whole-file Read of any file over 40 KB: read by section.

Where things are:
- What Harish sets: Drive control/ (inbox → engine/relay.py). What he sees: engine/panel.py → Drive status/panel.*.
- A run's instructions: runs/<run>.md. Series: niches/<niche>/series/. Schedule: .github/workflows/*.yml (UTC).
- The Control Room page: control-room/page.html, published as an artifact (its link is in GUIDE.md).

Change order (CLAUDE.md): AGENT.md first, then the build. Settings before code.

Test before live:
- Every change: `bash tools/check_code.sh` (all tests and the code check; the same runs on every push and must pass).
- Control Room path: python -m tests.test_control_room (no keys).
- A plan: python -m engine.plancheck <file>.
- Against the real Drive, nothing posted: Actions → daily → Run workflow on your branch, job `panel` or `clean-dry`.
- A change to templates/ or engine/render/ re-renders the golden set by itself on push. Touch them only when asked.

Ship: commit on your branch, open a pull request, merge when the tests pass. The Engine runs from main.
"Apply now" from Harish: run the daily workflow with job `control` on main.
Token habits: one script for many edits, quiet command output, no re-reading files you just wrote.
End with 5 lines for Harish in plain words, and one line added to BUILD_LOG.md.
