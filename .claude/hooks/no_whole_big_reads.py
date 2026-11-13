"""Project hook (AGENT.md 15.1): refuse a whole-file Read of any file over 40 KB, so a session never pays
for all of AGENT.md (about 30,000 tokens) when it needs one section. Read with offset/limit instead."""
import json
import os
import sys

try:
    call = json.load(sys.stdin)
    args = call.get("tool_input") or {}
    path = args.get("file_path") or ""
    if call.get("tool_name") == "Read" and not args.get("limit") and os.path.getsize(path) > 40_000:
        name = os.path.basename(path)
        print(f"{name} is large ({os.path.getsize(path) // 1000} KB). Do not read it whole. Find the section first "
              f"(for example: grep -n '^#' {name}), then Read with offset and limit.", file=sys.stderr)
        sys.exit(2)
except Exception:
    pass      # fail soft: never block a read because the guard itself broke
