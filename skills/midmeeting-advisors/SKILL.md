---
name: midmeeting-advisors
description: Creates or tunes MidMeeting advisors in settings.json without breaking the app. Use on "create a MidMeeting agent", "add an advisor", "my agent never speaks". Not for joining a meeting (midmeeting).
---

# MidMeeting advisors

Produces one advisor entry in MidMeeting's `settings.json` that loads cleanly and speaks when it should. Needs first: what the advisor is for, and for a meeting advisor, who the meeting is with and what it is about.

This skill writes to the app's settings file and stops and restarts the app.

## The file

`<data dir>/MidMeeting/settings.json`:
- Linux: `~/.local/share/MidMeeting/settings.json`
- macOS: `~/Library/Application Support/MidMeeting/settings.json`
- Windows: `%APPDATA%\MidMeeting\settings.json`

Advisors live in the `agents` array. One entry:

```json
{
  "id": "custom-<short-slug>",
  "name": "<shown in the app, 1 to 3 words>",
  "role_prompt": "<see step 4>",
  "glyph": "gear",
  "cadence": "balanced",
  "mode": "proactive",
  "thinking": "brief",
  "enabled": true,
  "builtin": false
}
```

| Field | Allowed values |
|---|---|
| `glyph` | `gear`, `crown`, `pen`, `megaphone`, `flame`, `magnifier`, `list` |
| `cadence` | `relaxed`, `balanced`, `chatty` (how often its cards may appear) |
| `mode` | `proactive` (joins every cycle), `on_demand` (only when poked) |
| `thinking` | `quick`, `brief`, `deep` |

## Steps

1. Check whether the app is running. If the user is at the screen, offer the app's own agent editor instead: it validates what it saves. Otherwise, before writing, ask the user to close it or stop it yourself by its process id. Never kill by a name pattern that also matches your own shell command. The app may save over this file while it runs, so an edit made with it open can be lost.
2. Copy the file to `settings.json.bak-<date>` beside it.
3. Pick a `glyph` from the table. Never an emoji: some color emoji crash the app's web view on launch.
4. Write the `role_prompt` in this order:
   1. Who the advisor is and who it serves, in one sentence.
   2. The context it cannot get from the transcript: the other party, the project, what the user already knows and does not know. Only what the user told you; ask for anything missing instead of filling it in.
   3. A list of triggers, each starting "Write a note when". Name concrete situations, never "when relevant".
   4. What never to do: summarise, cheer, repeat a point, invent facts.
   5. Which card kinds to prefer: `idea`, `question`, `risk`, `claim_check`, `correction`.

   A prompt that says only "speak when it truly matters" stays silent all meeting. For a learning call, say "speak up readily".
5. Set `cadence` and `mode` to what the user asked for. When unsure, pick `balanced` and `proactive`.
6. Append the entry, or replace the one with the same `id`. Keep every other field of the file untouched, and keep emoji in other entries as they are.
7. Check the copilot setting (`brain.provider`). With `agent_bridge`, the advisor speaks only while an AI agent is attached to the bridge (the midmeeting skill). Tell the user in one line if the provider is not what they expect.
8. Start the app the way it was running before (desktop launcher, Start menu or Applications folder; on Linux `gtk-launch midmeeting` when a desktop entry exists) and wait 15 seconds.
9. Check: the app process is still running, the file still parses as JSON, the new `id` is in `agents` with a glyph from the table, and there is no new crash report for the app's web process. On Linux: `coredumpctl list --since "-1min"` prints nothing. Any failure: restore the backup, restart, and tell the user what failed.

## Stopping rule

If the app fails to start twice with the new entry, restore the backup and stop. Tell the user which field you suspect, and suggest creating the advisor in the app's editor instead.
