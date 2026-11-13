#!/usr/bin/env python3
"""Which plans to render: a glob given by hand, or the plan files changed in the last push. No AI."""
import sys, glob, subprocess
pattern = sys.argv[1] if len(sys.argv) > 1 and sys.argv[1].strip() else ""
if pattern:
    files = sorted(glob.glob(pattern, recursive=True))
else:
    r = subprocess.run(["git", "diff", "--name-only", "HEAD~1", "HEAD", "--", "plans/"], capture_output=True, text=True)
    files = sorted(f for f in r.stdout.split() if f.endswith(".json"))
print("\n".join(files))
