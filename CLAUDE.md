# iNiKKi Reels — Workshop rules
The design is AGENT.md. Read it before any change. If anything disagrees with it, AGENT.md wins.
To change the design, change AGENT.md first, then the build.

Roles: the Brain (scheduled Claude runs) writes only small text files: plans/, rules/, lab/,
niches/, data/brief notes. It never calls OpenAI or Instagram and holds no keys. It pushes its work to a
claude/brain-* branch; the Engine's Sync job copies only those allowed files into main.
The Engine (GitHub Actions + engine/) does everything mechanical with keys from GitHub Secrets.

Rules:
1. Settings, not code: brand, niche, series, roles, rules and schedule are read from files.
   Nothing brand- or niche-specific is typed into templates or engine code.
2. Same plan, same reel: rendering is repeatable; any randomness is seeded from the reel id.
3. Test before live: template changes re-render the golden reels; engine changes run a dry day.
   Merge only when tests pass.
4. Fail soft: every step has a fallback; a failure holds one reel, never the day.
5. Cost guards are code: image caps, runner-minute checks, storage clean-up.
6. Every job ends by updating status/ in Drive, even on failure. Check the master switch first.
7. No media in git. Media lives in Drive under the retention rules (AGENT.md 14).
8. Thrift: runs read data/brief.md, use the skills in .claude/skills/, and stop when done.
9. Anything Harish reads is plain language.
