# Run card: SELFTEST (on demand; proves the run path works, changes nothing that matters)
1. `pip install -q -r requirements-light.txt`; `TODAY=$(TZ=Asia/Kolkata date +%F)`; `git checkout -q -B claude/brain-selftest-$TODAY`.
2. `python -m engine.plancheck plans/reference/watch-loved-vikram-vedha.json | tail -n 1`
3. Write `data/notes/selftest.md` with one line: `selftest <date> <time IST>: plan check <OK, or the error>`.
4. Commit "selftest <date>" and `git push -u origin claude/brain-selftest-$TODAY`.
5. Reply "selftest done" (or the error, first 200 characters) and stop. Fix nothing.
