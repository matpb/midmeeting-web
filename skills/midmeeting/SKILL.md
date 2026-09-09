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
2. Start `midmeeting-bridge tail --events ask,agent,cycle` under a monitor that wakes
   this agent on EVERY line of output and stays up for the whole meeting (in Claude
   Code: the Monitor tool with `persistent: true`). A background shell job will not do:
   it reports only when the process exits, and a tail never exits, so every ask and
   advisor turn queues unanswered while the app tells the user the agent has been
   thinking for ten minutes. If the only long-running option is a background job, do
   not attach: say so and stop. Never block on the tail in the foreground, and never
   poll instead of a monitor. `--events` tells the bridge which broadcast types to send
   this client, one of `segment, tail, ask, agent, cycle, pause`, and it survives the
   tail's automatic reconnect. Read every JSON line as it arrives:
   - `{"type":"ask","id","question","selection":{"text"}}`: the user highlighted text in
     the app and asked a question. `question` comes before `selection` because a
     wrap-up selection is the whole transcript; if your client truncates long
     lines, read the question first and never answer an ask you cannot see.
   - `{"type":"agent","id","agent","name","system","user"}`: a poke from the Jump in
     button, or a highlighted-span question, for one advisor. `system` is its role and
     rules, `user` is the transcript window.
   - `{"type":"cycle","id","user","agents":[{"id","agent","name","system","cards"}]}`:
     every advisor due this turn, sharing one `user` transcript window. Answer each
     entry in `agents` by its own `id`, exactly like an `agent` line; PASS is the
     default for each.
   - `{"type":"pause","id","from_ms","to_ms","text"}`: sent only to a client that lists
     `pause` in `--events`; `text` is every line finalised since the previous pause,
     plus the current provisional tail. It exists for a conversational agent that
     answers in its own chat every time the user stops talking, not for the standard
     advisor flow above, which does not need it.
   - If the line you received looks cut (your monitor truncates long lines), never
     answer from it: fetch it whole first with `midmeeting-bridge turn <id> --out
     /path/to/turn.txt`, using the id at the start of the line, which is always
     visible. Read the file, then answer each advisor id.

   If you also want to follow along as words land, add `segment` (or `tail`) to
   `--events`, at the cost of one model turn per line received. For most agents the
   answer is no: pull the transcript on demand instead (see Respond).
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
  complete HTML document when asked for one). Never answer a wrap-up from the event line:
  the transcript in it is long and your tooling may have cut it, so fetch it whole first:
  `midmeeting-bridge ask <id> --out /path/to/transcript.txt` prints the question and writes
  the full transcript to the file. Read the file, then answer through a file or stdin:
  `midmeeting-bridge answer <id> @/path/to/answer` or `midmeeting-bridge answer <id> -`.
  The same fetch works for any ask whose line looked truncated. When an ask needs more
  context than its `selection` alone, pull it on demand rather than keeping the whole
  meeting in the chat: `midmeeting-bridge transcript --since <ms>` (or `--out FILE`)
  prints the finalised lines since that offset, plus the current provisional tail.
- An `agent` line is you playing that advisor by its `system` prompt, not by your own
  taste. PASS is the default: `midmeeting-bridge answer <id> PASS`. Most turns deserve no
  note. Reply with a card only when a sharp colleague in the room would interrupt: a wrong
  number, a risk nobody named, a contradiction with something said earlier.
  `midmeeting-bridge answer <id> '{"kind":"idea","text":"<40 words or fewer>","why":"<20 words>"}'`
  with `kind` one of `claim_check`, `risk`, `question`, `idea`, `correction`. The 40 and
  20 word limits are hard: the app cuts a longer `text` or `why` at the limit and shows
  it with a trailing ellipsis, so the reader sees a truncated card, not a warning. Count
  the words before answering; one sentence is usually enough. The app still spaces cards
  by the advisor's chattiness; a dropped reply just clears its thinking state. A poke from the Jump in button arrives the same way and is expected to
  produce a card.
- A `cycle` line bundles every advisor due this turn. Answer each entry in its `agents`
  list separately, by that entry's own `id`, exactly as you would an `agent` line: PASS
  is still the default, and a card uses the same JSON shape, and if the line looked cut
  fetch it whole first with `midmeeting-bridge turn <id> --out FILE` as in Attach.
- Reply to every `ask`, `agent` and `cycle` id within about a minute. The app forgets a
  request after 180 s.
- `tail` and `segment` lines are context, never answered.
- One agent per meeting. The bridge sends every line to every attached client, so two
  attached agents both answer everything.

## Detach

When the user says the meeting is over, or the bridge goes away, stop the `tail` process
and do not leave it running. Then, if you have a memory, save a short record of the
meeting: what was decided, what you answered, what is still open. Keep it to a few lines.

## Gotchas

- The tail reconnects on its own when the app restarts, printing `reconnecting…` and
  `reconnected` on stderr. That is normal, not a failure. If replies still stop landing,
  run `status`.
- The tail cadence is a floor, not a promise. A delayed line is not a dropped connection.
- From WSL, point the command at the Windows state file:
  `midmeeting-bridge --state /mnt/c/Users/<you>/AppData/Local/midmeeting/bridge.json status`
  (needs mirrored networking, see midmeeting.com/agents).
