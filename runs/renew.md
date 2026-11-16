# Run card: RENEW (weekly, Monday 03:17 IST; AGENT.md 4.2, "Fresh chats every week")
The clock and dispatcher chats re-read their whole conversation at every tick, so they get more expensive every day.
Once a week this card replaces both with fresh chats. It writes no files and pushes nothing. Order matters: make the new
first, remove the old last, so no tick is lost. Never touch any task that is not named in `runs/renew/tasks.json`
(for example "iNiKKi Brain · Breaking (on demand)" and one-time reminders).

1. Read `runs/renew/clock.md`, `runs/renew/dispatcher.md` and `runs/renew/tasks.json` (main). Load the claude-code-remote
   tools you need with ToolSearch: create_session, list_triggers, create_trigger, delete_trigger, archive_session, list_events.
2. `list_triggers` (limit 100). For each chat ("clock" names start "iNiKKi Clock ·", "dispatcher" names start
   "iNiKKi Brain ·" and are listed in tasks.json), note OLD = the persistent_session_id of the enabled tasks whose name is
   in that chat's list.
3. Make two chats with create_session, each: source_url "https://github.com/haridhyaragav77-bit/inikki-reels",
   source_revision "main", model "claude-haiku-5-5", tags ["inikki-brain"], append_system_prompt = the file's text, prompt
   "Set-up check, no run yet. Reply READY in one word.":
   title "iNiKKi Engine · clock · <today>" (clock.md) and title "iNiKKi Brain · dispatcher · <today>" (dispatcher.md).
   Wait about a minute, then check each replied (list_events, kinds ["result"]). One did not: archive it, stop, and report.
4. For every entry in tasks.json, create_trigger with name, prompt, cron_expression (leave it out when empty),
   persistent_session_id = the new chat for that list, initiation "human_schedule".
5. Only after step 4 fully worked: delete_trigger for every task whose name is in tasks.json and whose
   persistent_session_id is an OLD id (never one bound to a new chat). Then archive_session each OLD chat.
6. Renew yourself last, so this chat never grows either: create_session like step 3 with title
   "iNiKKi · renewer · <today>", append_system_prompt = `runs/renew/renewer.md`, then create_trigger for the
   "renewer" entry in tasks.json bound to it, then delete_trigger the old renewer task (the one bound to this chat).
   Do not archive this chat; it ends by itself.
7. Reply in at most 4 plain lines: new chat ids, tasks moved, anything that failed. If anything failed before step 5,
   delete nothing: the old chats keep working.
