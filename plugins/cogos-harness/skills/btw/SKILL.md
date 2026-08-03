---
name: btw
description: Fork the current session into a parenthetical aside using cog_fork_session. The aside runs in a child session with role "btw-aside" so it has its own context and does not pollute the parent thread. On completion, the parent session resumes. Use when the user types /btw or says "by the way" and wants to pursue a tangent without losing the main thread.
version: 1.0.0
author: myrgic
tags: [session-management, cogos, cog-fork-session]
canonical_source: "~/.claude/skills/btw/SKILL.md"
projection_note: >
  This is the public marketplace projection of a locally-authored skill.
  Update canonical first; project here after.
---

# Skill: /btw — Substrate-Native Session Aside

Consumer for the `cog_fork_session` CogOS kernel primitive. Forks the current session into a child, runs a parenthetical tangent in the child, then returns control to the parent.

<invocation>
Trigger: user types `/btw` or "by the way, ..." or explicitly asks to fork the current session for an aside.

MUST call `cog_fork_session` with:
- `parent_session_id` = current session ID
- `overlay.role.role` = "btw-aside"
- `overlay.context.clear_parent_context` = false (child inherits parent context at fork point)

MUST NOT start the aside until the fork is confirmed (child_session_id returned).
MUST surface any fork error verbatim — do not silently proceed without a fork.
</invocation>

## When to use

- User types `/btw` mid-conversation
- User says "by the way, ..." and the aside is substantive enough to be worth tracking separately
- User asks to "fork this" or "spin off" a tangent
- User wants to explore a counterfactual without losing the main thread

## When NOT to use

- One-sentence questions — just answer inline, no fork needed
- When `cog_fork_session` is unavailable (kernel not running, MCP not wired) — fall through to answering inline and note the limitation
- When the user explicitly wants to stay in the same thread

## Preconditions

Check whether `cog_fork_session` is directly in your tool surface. Depending on kernel version it may be deferred plumbing rather than eagerly exposed. Before falling back inline, check for `cog_tool_search` + `cog_tool_invoke` (the porcelain pair): if present, use `cog_tool_search` to confirm `cog_fork_session` exists in the deferred catalog, then invoke it via `cog_tool_invoke(name="cog_fork_session", args={...})` with the same arguments documented below. Only fall through to answering inline if neither `cog_fork_session` nor the `cog_tool_search`/`cog_tool_invoke` pair is available.

## Procedure

### Step 1 — Identify the current session ID

The current session ID should be known from the session registration at session start (the `session_id` set when `cog_register_session` was called). If not known, use `cog_list_sessions` to find the most recently-heartbeated session.

### Step 2 — Fork the session

Call `cog_fork_session` with these args, either directly (if it's in the eager surface) or via `cog_tool_invoke(name="cog_fork_session", args={...})` (if only the deferred porcelain pair is present):

```json
{
  "parent_session_id": "<current-session-id>",
  "overlay": {
    "role": {
      "role": "btw-aside"
    },
    "context": {
      "clear_parent_context": false
    }
  }
}
```

This produces a `child_session_id`. The child inherits the parent's context at the fork point and runs with role `btw-aside`.

### Step 3 — Complete the aside

Address the user's /btw question or tangent. The aside is logically bounded to the child context. Keep responses focused on the aside topic.

When the aside is complete, say something like: "Aside complete. Returning to the main thread." This signals the return to parent context.

### Step 4 — Mark the child session ended (optional)

If the kernel session lifecycle matters, call `cog_end_session` with `session_id` = the `child_session_id` to mark it ended cleanly.

### Step 5 — Resume the parent session

Return to the parent thread by continuing the prior conversation where it left off. The parent's context was preserved at the fork point.

## Merge-back pattern (optional)

If the aside produced information worth carrying back to the parent thread:

1. Summarize the aside findings in one paragraph.
2. Ingest the summary via `cog_ingest` (if the kernel supports it) so it appears in the parent's foveal context.
3. Reference the aside's `child_session_id` in the summary for lineage traceability.

## Error handling

| Error | Action |
|-------|--------|
| `cog_fork_session` not in tool surface AND `cog_tool_search`/`cog_tool_invoke` unavailable | Answer inline; note that /btw requires the cogos-kernel MCP server |
| `cog_fork_session` absent from eager surface but `cog_tool_search`/`cog_tool_invoke` present | Route through `cog_tool_invoke(name="cog_fork_session", args={...})` (see Step 2) |
| Parent session not found (404) | Use `cog_register_session` to register the current session first, then retry |
| Cross-workspace fork (501) | Not supported on all kernel versions; answer inline |
| Fork succeeds but child registration fails | Proceed with aside anyway; note the registry miss in the response |

## Example invocation

User: `/btw — how does the fork primitive interact with session identity?`

1. Fork with `overlay.role.role = "btw-aside"`.
2. Answer the question in the child context.
3. Say "Aside complete. Returning to the main thread."
4. Resume the parent thread.

## Kernel dependencies

- `cog_fork_session` — the fork primitive
- `cog_list_sessions` — for session ID discovery
- `cog_end_session` (optional) — for clean child lifecycle

## Notes

- The fork primitive also underlies parallel exploration tracks, agent spawning, and time-travel via self-fork — `/btw` is the simplest application.
- Lineage queries beyond a direct parent/child relationship require direct registry inspection via `cog_list_sessions` + event reads, on kernel versions where dedicated ancestor/descendant lookup tools aren't shipped.
