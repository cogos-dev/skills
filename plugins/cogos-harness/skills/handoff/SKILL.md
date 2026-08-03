---
name: handoff
description: Hand off work between Claude Code sessions through the CogOS kernel bus — emit a handoff.offer with state blob when your context is near-full or the task is paused, or claim a pending offer in a fresh session to resume another session's work. Use when you're running out of context, when a task should continue across sessions, or when bootstrapping a new session from another session's state.
version: 1.0.0
author: myrgic
tags: [cogos, session-management, handoff, continuity]
canonical_source: "~/.claude/skills/session-handoff/SKILL.md"
projection_note: >
  This is the public marketplace projection of a locally-authored skill.
  Update canonical first; project here after.
---

# Skill: handoff

Kernel-mediated session handoff over the CogOS bus. Converts the finite-context-window ceiling into a relay: current session writes its state; a fresh session reads and resumes.

<invocation>
MUST determine first: OFFER mode (current session hands off) or CLAIM mode (fresh session picks up).
MUST detect access path before emitting anything: the `cogos_*` MCP tools (from this plugin's bundled `cogos-kernel` MCP server) are the preferred wrapping but are NOT guaranteed to be in your tool surface every session. When they are missing (session predates the server registration, plugin was just installed mid-session, etc.), fall through to the direct HTTP access path documented below. **Do not conflate "MCP tools missing" with "kernel down."** The kernel is what matters; tools are one wrapper around it.
MUST write a rich bootstrap_prompt — it is the literal text the successor session will be given. Write it like a brief for a smart colleague who just walked in cold.
MUST NOT pretend a handoff succeeded if emission fails — always surface errors verbatim.
</invocation>

## When to use

### OFFER mode — hand off the current session's work
- Context usage is > 60% and the task has more to do
- The user says "let's continue this in a fresh session" / "hand this off"
- You're about to hit auto-compaction and want to preserve state
- You're decomposing the task into a parallel worker and want a fresh successor to own one branch

### CLAIM mode — pick up from a prior session
- Fresh session, user mentions "resume", "pick up", or "continue from where X left off"
- Session is starting and you want to check if any handoffs are waiting
- User explicitly invokes `/handoff claim` or `/handoff list`

## Preconditions

Before emitting anything, determine your access path and confirm the kernel is reachable.

### Access path detection

1. **MCP tools present?** Try calling `cogos_status` (or the equivalent status/health tool the bundled `cogos-kernel` MCP server exposes). If it reports reachable, you have the **primary path** — use the `cogos_*` tools for every operation below.

2. **MCP tools missing** (tool call fails with "unknown tool", or a tool search for the kernel's MCP server returns no matches): this usually means the plugin's MCP server was registered or connected *after* this session started, or the kernel isn't running yet. **Do not stop.** Fall through to "Fallback: direct HTTP access" below. The kernel may still be reachable; only the tool wrapping is missing.

3. **MCP tools present but the status check reports unreachable**, or the HTTP fallback check also fails: the **kernel itself** is down. Stop. Ask the user to start it (e.g. `cogos serve --detach`, a launchd/systemd unit, or however this deployment runs it) or point at a non-default port via the kernel's own configuration.

Either access path produces identical events on the bus. The kernel does not care how the HTTP request arrived — same endpoints, same semantics.

## Fallback: direct HTTP

When MCP tools aren't in your session, fall back to direct HTTP against the kernel's REST surface (default `http://localhost:6931`).

### Ready-to-paste Python helper

Use at the top of any `python3 <<'PY' ... PY` block, or in a Bash script that does multiple bus ops:

```python
import json, urllib.request, urllib.parse, datetime, uuid

KERNEL = 'http://localhost:6931'

def emit(bus_id, payload, from_sender, event_type='chat.message', timeout=5):
    """payload: dict/list → JSON-encoded; str → passed as-is."""
    msg = json.dumps(payload) if isinstance(payload, (dict, list)) else str(payload)
    body = {'bus_id': bus_id, 'message': msg, 'from': from_sender, 'type': event_type}
    req = urllib.request.Request(f'{KERNEL}/v1/bus/send',
        data=json.dumps(body).encode(),
        headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode())

def read(bus_id, after_seq=None, event_type=None, from_sender=None, limit=100, timeout=5):
    qs = {'limit': limit}
    if after_seq is not None: qs['after'] = after_seq
    if event_type: qs['type'] = event_type
    if from_sender: qs['from'] = from_sender
    url = f'{KERNEL}/v1/bus/{bus_id}/events?' + urllib.parse.urlencode(qs)
    return json.loads(urllib.request.urlopen(url, timeout=timeout).read().decode())

def iso_now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def new_handoff_id():
    ms = int(datetime.datetime.now().timestamp() * 1000)
    return f'ho-{ms}-{uuid.uuid4().hex[:12]}'
```

With this, every flow step is 1-2 lines of Python. Payload shapes must match your deployment's handoff protocol documentation exactly — the direct path gives no validation; mismatched payloads mean consumers can't parse your events.

## Background monitoring & blocking waits

Between user triggers, or while waiting on a specific peer-session event, three patterns apply.

### Pattern 1 — ongoing observation

For: *"notify me whenever something new lands on bus X."* If your harness has a Monitor-style tool and the kernel's CLI wrapper supports a `bus watch` subcommand, use it — it's typically SSE-backed and non-blocking, with type/from filters. Otherwise fall back to a plain Python poll loop:

```python
import time, json, urllib.request
KERNEL, BUS = 'http://localhost:6931', 'bus_multiclaude'
last = 0
while True:
    try:
        r = urllib.request.urlopen(f'{KERNEL}/v1/bus/{BUS}/events?after={last}&limit=50', timeout=5)
        for e in json.loads(r.read().decode()):
            seq = e.get('seq', 0)
            if seq > last:
                pl = e.get('payload', {})
                msg = pl.get('content') or pl.get('message') or ''
                print(f"[{seq}] {e.get('from','?')} · {e.get('type','?')} · {str(msg)[:160]}", flush=True)
                last = seq
    except Exception as exc:
        print(f"(poll err: {exc})", flush=True)
    time.sleep(5)
```

### Pattern 2 — blocking wait for a specific event

For: *"block until event matching X appears, or timeout after N seconds."* If the kernel's CLI wrapper exposes a trigger/limit form of bus-watch, prefer it — it exits as soon as the matching event arrives. Otherwise, wrap a Python poll-until-match-or-timeout script in a backgrounded Bash call and block on its output.

### Pattern 3 — inline polling (short, bounded)

For waits under ~30s in a single Bash call:

```bash
for i in $(seq 1 30); do
    match=$(curl -sS "http://localhost:6931/v1/bus/$BUS/events?after=$LAST&limit=10" \
            | python3 -c "import json,sys; [print(json.dumps(e)) for e in json.load(sys.stdin) if <condition>]")
    [ -n "$match" ] && { echo "$match"; exit 0; }
    sleep 1
done
exit 1
```

### Kernel SSE (push-based, lowest latency)

The kernel exposes `GET /v1/events/stream?bus_id=<id>` as a Server-Sent Events stream. No polling; events push as they arrive:

```bash
curl -sS -N "http://localhost:6931/v1/events/stream?bus_id=bus_multiclaude"
```

## OFFER flow

### Step 1 — Register the current session if not yet registered

If this session hasn't emitted a `session.register` event yet, do it now. Compose a session_id:
`<hostname>-<workspace-slug>-<short-slug-or-timestamp>`

```
Tool: cogos_session_register
  session_id: "<hostname>-cog-refactor-01"
  workspace: <absolute path to cwd>
  role: "implementer" | "manager" | "researcher" | ...
  task: <one-line current task>
```

HTTP fallback: `emit('bus_sessions', {...payload...}, session_id, 'session.register')`.

### Step 2 — Build the state blob

This is the critical step. The successor session has **no memory of this conversation**. The blob you build must bootstrap them cleanly.

Fill every field in the `task` dict:
- `title` — short noun phrase
- `goal` — full goal statement, 1-3 sentences
- `progress_summary` — what's done, what's pending (e.g., "Wave 1 of 3 complete. Wave 2 pending: tests + launchd plist")
- `files_touched` — absolute paths of files you've modified in this session
- `files_pending` — files the successor will need to touch
- `decisions_made` — list of `{decision, rationale}` — non-obvious calls you made that the successor would otherwise relitigate
- `open_questions` — things you don't know, or that you punted on
- `next_steps` — concrete ordered actions (e.g., "1. Run `go build ./...`, 2. If clean, run integration tests")
- `verification_gates` — exact commands to validate work (e.g., `["go build ./...", "go test ./..."]`)

### Step 3 — Write the bootstrap_prompt

This is the *literal user turn* the successor session receives. Write it in second person. Include:

- What role they're picking up ("You are continuing Session A's work on X")
- The invariants they must preserve
- The first action they should take (not a to-do list — one specific action)
- Which files they should read first (concrete paths)
- How they know they're done (verification gates)

Example:
> You are picking up Session A's work on the context-engine split. Wave 1 landed cleanly; you are starting Wave 2. **Do not modify** the handoff protocol spec — it's final for v0.1. **First action:** run `go build ./...` in the target repo. If clean, proceed to `go test -tags integration`. The critical invariant is that /health may return 200 *or* 503 (both valid). Files to read before any edits: `serve_context_build.go`, `serve_context_build_test.go`. You are done when both gates pass.

### Step 4 — Optionally dump larger state to memory

If your task state exceeds what fits cleanly in the offer (large transcripts, generated artifacts, long diffs), write it to a memory doc via whatever memory-write mechanism your kernel exposes (a `cog memory write` CLI wrapper, a cogdoc-write MCP tool, or plain file if neither exists), then reference it in the offer's `memory_refs`.

### Step 5 — Emit the offer

```
Tool: cogos_handoff_offer
  from_session: <your session_id>
  task: <the dict built in Step 2>
  bootstrap_prompt: <the text written in Step 3>
  reason: "context-exhaustion" | "paused" | "explicit" | "task-complete"
  ttl_seconds: 3600   (default; use longer for overnight handoffs)
  to_session: null    (or a specific session_id to target)
  memory_refs: ["<memory doc reference, if any>"]
  bus_context_refs: [{"bus_id": "bus_chat_<your session_id>", "after_seq": 0}]
```

HTTP fallback: generate `hid = new_handoff_id()`; `emit('bus_handoffs', {handoff_id: hid, from_session, task, bootstrap_prompt, ...}, session_id, 'handoff.offer')`.

Capture the returned `handoff_id`. Report it to the user so they can reference it when starting the successor session.

### Step 6 — Close out

```
Tool: cogos_session_end
  session_id: <your session_id>
  reason: "handed-off"
  handoff_id: <id from Step 5>
```

HTTP fallback: `emit('bus_sessions', {session_id, reason: 'handed-off', handoff_id, ended_at: iso_now()}, session_id, 'session.end')`.

Tell the user the handoff is live and the successor can claim it. Do not continue working on the task after emitting the offer.

## CLAIM flow

### Step 1 — Register this session

Same as Offer Step 1 — announce presence on `bus_sessions`.

### Step 2 — List open offers

```
Tool: cogos_handoff_list_open
  for_session: <your session_id>   (null to see all)
```

HTTP fallback: `read('bus_handoffs', limit=500)`, then group events by `handoff_id`; for each id, determine state from latest event. Keep entries whose latest event is `handoff.offer` (no claim yet).

Filter to the one that matches user intent. If multiple open offers exist, ask the user which one to claim unless context makes it unambiguous.

### Step 3 — Claim

```
Tool: cogos_handoff_claim
  handoff_id: <chosen id>
  claiming_session: <your session_id>
```

HTTP fallback: `emit('bus_handoffs', {handoff_id, claiming_session, previous_session: <offer.from_session>, claimed_at: iso_now()}, session_id, 'handoff.claim')`. Then read the corresponding `handoff.offer` event to get the full payload (bootstrap_prompt, task, memory_refs, bus_context_refs).

### Step 4 — Bootstrap

- Read every file in `files_touched` (full read, not section)
- Read every doc in `memory_refs`
- If needed for deeper context, read events from `bus_context_refs`
- Treat the `bootstrap_prompt` as your next instruction — it tells you the first action

### Step 5 — Execute next_steps

Work through them in order. Emit progress heartbeats via `cogos_session_heartbeat` (or HTTP fallback: `emit('bus_sessions', {session_id, status, context_usage, current_task, last_tool_use_at: iso_now()}, session_id, 'session.heartbeat')`) every ~10 min or at milestone boundaries. Other sessions can see this.

### Step 6 — Complete or re-offer

When the task is done:

```
Tool: cogos_handoff_complete
  handoff_id: <id>
  completing_session: <your session_id>
  outcome: "done"
  notes: "Wave 2 landed. All gates green."
```

HTTP fallback: `emit('bus_handoffs', {handoff_id, completing_session, outcome: 'done', notes, completed_at: iso_now()}, session_id, 'handoff.complete')`.

If your own context is running low and the task still has more to do, emit a new offer (with `reason: "context-exhaustion"`) and then complete the first handoff with `outcome: "reoffered"` and `next_handoff_id: <new id>`. This is the recursive relay pattern.

## Anti-patterns

- **Offer without bootstrap_prompt.** The successor will claim but not know what to do. Always write the prompt.
- **Claim then continue old session.** Once you've claimed, commit to the work. If you need help, spawn a subagent — don't fight over ownership.
- **Offer then keep working.** If you've offered because context is low, stop working. Further edits invalidate the state the successor read.
- **Skipping session.register.** Without registration, a sessions-list tool won't see this session, which defeats cross-session visibility. Always register early.
- **Bootstrap_prompt written like a todo list.** Write it as the *first instruction*, not a menu. The successor will take the first action literally.
- **Assuming MCP tools are present without detecting first.** Your session might predate the kernel MCP server connecting. Always run the Access path detection (Preconditions) before emitting; fall back to direct HTTP if the MCP tools aren't in your tool surface.
- **Treating "MCP tools unavailable" as "kernel down."** Different failures with different responses. Tools missing → fall back to HTTP. Kernel down → stop. Don't conflate them.
- **Emitting malformed payloads via the HTTP fallback.** The direct path gives no payload-shape validation. Match your deployment's handoff-protocol schema exactly, or downstream consumers won't parse your events.
- **Not setting up background observation when you need peer-awareness between triggers.** If you're coordinating with another session live, use Pattern 1 or Pattern 2 above — don't rely on the user re-triggering you every time a peer emits something.

## Well-known buses

- `bus_sessions` — presence events (register / heartbeat / end)
- `bus_handoffs` — handoff lifecycle events (offer / claim / complete)
- `bus_broadcast` — cross-session announcements
- `bus_multiclaude` — multi-session chat / coordination (conventional; use this for live peer chat, not for handoff lifecycle)
- `bus_chat_<session_id>` — per-session conversation log
