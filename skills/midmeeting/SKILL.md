---
name: midmeeting
description: Use on "/midmeeting", "listen to my meeting", "join the meeting", "watch MidMeeting", "attach to the bridge": attaches this session to the MidMeeting desktop app's agent bridge, streams the live transcript in, answers questions asked in the app, and plays the advisors the user armed. Not for summarising a finished transcript and not for transcribing a file.
---

# MidMeeting agent bridge

MidMeeting is a local meeting recorder with a live transcript. When its copilot is set to
Agent bridge, the app hands the transcript to an agent running on the same computer instead
of a cloud key. This skill makes this session that agent. It works the same on Windows,
macOS and Linux through one command, `midmeeting-bridge`, which the app installs.

## The one rule that matters: silence

Everything you write in this chat becomes a notification on the user's screen while they
are in a call. So:

- A `tail` or `segment` line with nothing to act on produces no visible output at all. No
  "no action needed", no "still listening", no summary of what was just said, no emoji,
  no one-word acknowledgement.
- Answers to asks and agent turns go through `midmeeting-bridge`, never mirrored into the
  chat. The app shows them.
- Write in the chat only when the user speaks to you here, when the meeting ends, or when
  the bridge itself breaks and the app cannot say so.
- When in doubt, say nothing. A quiet agent is doing its job.

## Attach

1. `midmeeting-bridge status`. Exit 0 prints `connected <endpoint>`. Anything else means
   MidMeeting is not running with Agent bridge selected: say so once, then stop. If the
   command is missing, the path is shown in the app under Settings, Copilot, Agent bridge,
   and midmeeting.com/agents explains the install.
2. Start `midmeeting-bridge tail` as a persistent background process with whatever this
   agent uses for long-running monitors. Never block on it in the foreground. Read every
   JSON line as it arrives:
   - `{"type":"tail","lines":[{"track","text","from_ms","to_ms"}]}`: the provisional
     current line, replaced on every push, within a second of a pause and at least every
     5 s while someone talks. It repeats earlier words of the same line.
   - `{"type":"segment","track","text","from_ms","to_ms"}`: a finalised line, sent once,
     about 25 s after it was spoken.
   - `{"type":"ask","id","selection":{"text"},"question"}`: the user highlighted text in
     the app and asked a question.
   - `{"type":"agent","id","agent","name","system","user"}`: one armed advisor's turn.
     `system` is its role and rules, `user` is the transcript window.
3. Say "Listening" once, then apply the silence rule.

Track labels: `you` is the user's microphone, `them` is the computer's audio, normally the
other side of the call. Several people sharing the user's room all land on `you`, so a
track is a side of the call, not a person.

## Respond

- An `ask` is always answered, quickly, grounded in the transcript seen so far. Verify a
  factual claim with your tools first when you can.
  `midmeeting-bridge answer <id> "<answer>"`
  A question starting with `Over the whole meeting:` is a wrap-up preset: `selection.text`
  is the full transcript, and the answer may run long (a summary, action items, or a
  complete HTML document when asked for one). Long answers go through a file or stdin:
  `midmeeting-bridge answer <id> @/path/to/file` or `midmeeting-bridge answer <id> -`.
- An `agent` line is you playing that advisor by its `system` prompt, not by your own
  taste. PASS is the default: `midmeeting-bridge answer <id> PASS`. Most turns deserve no
  note. Reply with a card only when a sharp colleague in the room would interrupt: a wrong
  number, a risk nobody named, a contradiction with something said earlier.
  `midmeeting-bridge answer <id> '{"kind":"idea","text":"<40 words or fewer>","why":"<20 words>"}'`
  with `kind` one of `claim_check`, `risk`, `question`, `idea`, `correction`. The app
  still spaces cards by the advisor's chattiness; a dropped reply just clears its
  thinking state. A poke from the Jump in button arrives the same way and is expected to
  produce a card.
- Reply to every `ask` and `agent` id within about a minute. The app forgets a request
  after 180 s.
- `tail` and `segment` lines are context, never answered.
- One agent per meeting. The bridge sends every line to every attached client, so two
  attached agents both answer everything.

## Detach

When the user says the meeting is over, or the bridge goes away, stop the `tail` process
and do not leave it running. Then, if you have a memory, save a short record of the
meeting: what was decided, what you answered, what is still open. Keep it to a few lines.

## Gotchas

- The tail dies silently when the app restarts. If replies stop landing, run `status` and
  start `tail` again.
- The tail cadence is a floor, not a promise. A delayed line is not a dropped connection.
- Each line you receive costs a model turn. Do not filter for more lines, and do not poll.
- From WSL, point the command at the Windows state file:
  `midmeeting-bridge --state /mnt/c/Users/<you>/AppData/Local/midmeeting/bridge.json status`
  (needs mirrored networking, see midmeeting.com/agents).
