---
name: midmeeting
description: Use on "/midmeeting", "listen to my meeting", "join the meeting", "watch MidMeeting", "attach to the bridge": attaches this session to a MidMeeting desktop app's agent bridge, streams the live transcript in, answers questions asked in the app, and plays any agent turns it is armed for.
---

# MidMeeting agent bridge

MidMeeting is a local-first meeting recorder. When its Copilot provider is set to
Agent bridge, the app hands the live transcript to whatever agent CLI is running
on the same machine instead of calling a cloud API key.

## Attach

Check the bridge is up before doing anything else:

```sh
midmeeting-bridge status
```

Exit 0 means it printed `connected <endpoint>`. Any other exit code means the
bridge is not running: tell the user MidMeeting is not running with the agent
bridge on, and stop.

`midmeeting-bridge` finds the bridge on its own on Linux, macOS and Windows.
From inside WSL, point it at the Windows state file instead: `midmeeting-bridge
--state /mnt/c/Users/<you>/AppData/Local/midmeeting/bridge.json status` (this
needs mirrored networking; see midmeeting.com/agents for setup).

Once attached, start `midmeeting-bridge tail` as a persistent background
process using whatever mechanism this agent supports for a long-running monitor
(background shell, watcher task). Read every JSON line it prints as it arrives.
Do not run `tail` in the foreground and block on it. Tell the user you are
listening, then stay quiet until there is a reason to speak.

## Respond

- `ask` lines are always answered. Ground the answer in the transcript seen so
  far, and verify factual claims with other tools when they are available and
  relevant. A question starting with `Over the whole meeting:` is a summary
  preset: its `selection.text` is the full transcript, and the answer can run
  long, sent back via `answer <id> @/path/to/file` or `answer <id> -` on stdin.
- `agent` lines are one armed agent's turn. Play the role in its `system` field
  against the transcript window in `user`. PASS is the default reply
  (`midmeeting-bridge answer <id> PASS`): most turns deserve no comment. Only
  reply with a card when a sharp colleague in the room would actually interrupt,
  and no more than about one card every few minutes. A card reply is JSON:
  `{"kind":"idea","text":"<40 words or fewer>","why":"<20 words>"}`, kind one of
  claim_check, risk, question, idea, correction.
- `segment` and `tail` lines are not answered directly, they are context: fold
  them into what the agent and ask replies are grounded in.

Reply to every `ask` and `agent` id within about a minute; the app forgets a
request after 180 seconds.

## Detach

When the meeting ends, or the user says to stop, stop the `tail` process. Do
not leave it running past the meeting.

## Gotchas

- The tail dies when the MidMeeting app restarts. If replies stop landing,
  rearm by starting `tail` again.
- Attach one agent per meeting. The socket accepts several watchers and sends
  every line to all of them, so two attached agents both answer every ask.
- The tail cadence (updated within a second of a pause, at least every 5
  seconds while someone is talking) is a floor, not a promise of faster
  updates. Do not treat a delayed line as a dropped connection.
