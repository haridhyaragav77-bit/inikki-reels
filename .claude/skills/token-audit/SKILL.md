---
name: token-audit
description: Measure what each Claude chat of the agent cost (clock, dispatcher, renewer, thinking runs) from the session records, in a few cheap steps, and name the biggest cost. Workshop sessions only.
---
# token-audit
Use when Harish says usage is high, or before changing how runs are started. Never read AGENT.md whole.
1. `list_sessions` (mine, limit 40). Keep the ones titled "iNiKKi …" from the last 2 days.
2. For each long-lived chat (dispatcher, renewer) and the newest Plan and Refresh run: `list_events` with kinds ["result"].
   If the answer is too big it is saved to a file: read only the numbers with one python one-liner (regex on
   "created_at", "total_cost_usd", "cache_read_input_tokens" of the last "iterations" item = context per message).
3. Per chat: messages per day × context per message, and the day's cost (difference of total_cost_usd). A chat whose
   context per message passes 150,000 tokens is the problem: it should be renewed, or not be a chat at all.
4. Check the daily renewal ran: the newest dispatcher's title carries today's date. If not, read the renewer's last
   result and fix runs/renew/renewer.md or runs/renew.md.
5. Report in a small table (chat · per message · per day) and at most 3 fixes, in plain words.
Do not open run transcripts in full; the result events carry every number needed.
