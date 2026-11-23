# Run card: RENEW (daily, 03:17 IST; AGENT.md 4.2, "Fresh chats every day")
The dispatcher re-reads its whole chat at every message, and its messages are hours apart, so Claude's cache has
expired each time and the whole chat is paid for again. A fresh chat every day keeps each message small.
The clock is no longer a chat: the GitHub metronome starts the timed jobs (tools/metronome.py, AGENT.md 4.3).
This card writes no files and pushes nothing. Make the new first, remove the old last, so no message is lost.
Never touch a task that is not named in `runs/renew/tasks.json` (for example "iNiKKi Brain · Breaking (on demand)",
one-time reminders, other projects).

1. Read `runs/renew/dispatcher.md`, `runs/renew/renewer.md` and `runs/renew/tasks.json`. Load the claude-code-remote
   tools you need with ToolSearch: create_session, list_triggers, create_trigger, delete_trigger, archive_session, list_events.
2. `list_triggers` (limit 100). OLD = the persistent_session_id of each enabled task whose name is in the "dispatcher" list.
   CLOCK = the persistent_session_id of each task whose name is in the "clock" list (those are the metronome's now).
3. create_session: source_url "https://github.com/haridhyaragav77-bit/inikki-reels", source_revision "main",
   model "claude-haiku-5-5", tags ["inikki-brain"], title "iNiKKi Brain · dispatcher · <today>",
   append_system_prompt = dispatcher.md's text, prompt "Set-up check, no run yet. Reply READY in one word.".
   Wait about a minute, check it replied (list_events, kinds ["result"]). If not: archive it, stop, report.
4. For every entry in the "dispatcher" list: create_trigger with its name, prompt, cron_expression (left out when empty),
   persistent_session_id = the new chat, initiation "human_schedule". If the service says to wait (a creation limit),
   wait a minute and go on.
5. Only after step 4 fully worked: delete_trigger every task bound to an OLD id (whatever its name: old catch-up times
   included), and every task named in the "clock" list (any chat). If a delete is refused, switch that task off instead:
   update_trigger enabled false, name prefixed "OLD (off) · ". An old task must never stay on. Then archive_session each
   OLD and CLOCK chat.
6. Renew yourself last: create_session like step 3 with title "iNiKKi · renewer · <today>" and append_system_prompt =
   renewer.md's text; create_trigger for the "renewer" entry bound to it; delete_trigger the renewer task bound to this chat.
   Do not archive this chat; it ends by itself.
7. Reply in at most 3 plain lines: the new chat ids, tasks moved, anything that failed. If anything failed before
   step 5, delete nothing: the old chat keeps working.
