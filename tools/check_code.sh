#!/usr/bin/env bash
# Every push and pull request (guard.yml), and before a Workshop merge: the Engine's tests (no keys) and a check for
# code that would crash only on some days (a name used before it is set, an unknown name). 24 Nov 2026, after the
# refresh brief crashed on 23 Nov and the crash was found only when the day's reels were missing.
set -u
fail=0
python -m pylint --disable=all --enable=used-before-assignment,possibly-used-before-assignment,undefined-variable \
  --score=n engine tools tests || fail=1
for t in tests/test_*.py; do
  m=${t%.py}; m=${m//\//.}
  if python -m "$m" > /tmp/test.log 2>&1; then echo "pass  $m"; else echo "FAIL  $m"; tail -n 20 /tmp/test.log; fail=1; fi
done
exit $fail
