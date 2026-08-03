---
name: consolidate
description: "Reflect on the current session's arc when context pressure or operator signals indicate an inflection point. Map settled vs heating-up distinctions, surface at-risk-of-being-lost items, capture any new operational framing as feedback memory, write a consolidation cogdoc + continuation brief. Use when context approaches ~60% saturation, when the operator signals stepping away, when a long arc has settled and needs durable capture, or when an explicit `/consolidate` is invoked. Distinct from `handoff`, which is transactional (one session emits, another claims) — consolidate is reflective (distill the session's distinctions into durable form)."
version: 1.0.0
author: myrgic
tags: [cogos, session-management, memory, continuity]
canonical_source: "~/.claude/skills/session-consolidate/SKILL.md"
projection_note: >
  This is the public marketplace projection of a locally-authored skill.
  Update canonical first; project here after.
---

# Skill: consolidate

The reflective complement to `handoff`. Where handoff moves *work* between sessions, consolidate moves *understanding* into durable storage so it outlives any individual session.

A CogOS workspace's persistent-organism shape requires this. Without consolidation, every session's recognitions evaporate at context-end. With it, the session itself becomes reconciled into durable form.

<invocation>
MUST identify three categories: SETTLED distinctions (already durably captured somewhere), HEATING-UP distinctions (load-bearing for continued attention), and AT-RISK distinctions (named once, not captured anywhere).
MUST preserve the structure of distinctions made; don't compress into a single narrative summary.
MUST capture any NEW operational framing or reusable pattern as a `feedback_*.md` memory entry — these are the most load-bearing outputs because they change how future sessions evaluate work.
MUST write outputs to durable locations (cog workspace memory + Claude Code memory + memory index update), not to ephemeral job dirs alone.
MUST NOT skip the at-risk section. That's the most important category — items there are what would otherwise drop out of the operational picture.
</invocation>

## When to invoke

### Context-pressure trigger
- Session context usage approaches ~60% (the natural inflection where consolidation cost is amortized cleanly across remaining session work)
- A long arc of substantive work has stabilized; further work would benefit from a refreshed working set

### Operator-signaled trigger
- "Let's consolidate", "make sure nothing's getting lost", "I'm stepping away"
- A specific recognition lands (a framing crystallizes) and the operator wants it captured before drift

### Idle / cycle-boundary trigger (future-state)
- Operator has been inactive > N minutes mid-session
- Session about to be backgrounded or auto-compacted

### Composition with handoff
- Consolidate BEFORE handoff when there's substantive recognition to preserve beyond the work itself
- Handoff alone is sufficient if the recognition is task-bound and the successor session has all it needs from the bootstrap prompt

## What it does

1. **Source assembly.** Reads:
   - Current session's conversation JSONL at `~/.claude/projects/<project>/<session_id>.jsonl`
   - Job-dir artifacts, if the harness uses them, at `~/.claude/jobs/<job_id>/`
   - Recent memory entries written this session (files modified today under the session's memory directory)
   - Cogdocs created/touched this session, if the workspace has a cog memory tree
   - PRs landed today (`gh pr list --search "merged:<today>"`)
   - Current task list state (TaskList tool, if available)

2. **Arc mapping.** Builds a chronological topic map of the session. Names the arcs — don't recapitulate every turn.

3. **Distinction sorting.** Each substantive recognition from the session sorts into:
   - **Settled**: durably captured in memory file / cogdoc / ADR / merged PR. Confirm where each one lives.
   - **Heating-up**: discussed but not yet captured; load-bearing for continued attention. Name what's load-bearing about each.
   - **At-risk**: surfaced once, didn't get captured anywhere durable. Most important section — these would otherwise drop out.

4. **New-framing capture.** If the session produced any new operational/pattern framing not yet in memory, write a fresh `feedback_*.md` memory entry capturing it. Include cross-links to related memories via `[[name]]` notation where the memory system supports it. Update the memory index.

5. **Continuation brief.** Write a handoff-shaped brief that a future session (this one after refresh, or a fresh one) can load to pick up cleanly. Includes: where things stopped, what's actively decision-blocked, what's dispatch-ready, what conversation-arcs are mid-flight.

6. **Durable consolidation record.** If the workspace has a `.cog/mem` tree (`COGOS_WORKSPACE`, default `~/workspaces/cog`), write the consolidation artifact to `${COGOS_WORKSPACE:-~/workspaces/cog}/.cog/mem/episodic/sessions/<date>-consolidation.cog.md`, sectioned by: Arc Map, Settled, Heating-Up, At-Risk, Operational State, Continuation Brief. If there's no cog memory tree, write the equivalent to the harness's own memory location instead.

## How to dispatch

Spawn a sub-agent (Sonnet-tier is sufficient) with:
- Identity: "conversation-consolidation agent"
- Pointers: session JSONL path, job dir path (if any), memory directory, cog memory directory (if any)
- Tool access: Bash, Read, Write, Edit
- Output spec: the 6 outputs above
- Discipline: don't paraphrase the session; preserve distinction structure; be honest about at-risk items

Where a local-inference or scheduled-dispatch path exists, this is a natural candidate to run on a trigger (context-pressure or idle-time) rather than only on explicit invocation — the skill's shape doesn't change, only who/what invokes it.

## Output locations

Each output goes to a durable place:

| Output | Path | Lifespan |
|---|---|---|
| Consolidation cogdoc (if the workspace has one) | `${COGOS_WORKSPACE:-~/workspaces/cog}/.cog/mem/episodic/sessions/<date>-consolidation.cog.md` | Permanent; indexed by the workspace's own memory search |
| New feedback memory (if framing crystallized) | `~/.claude/projects/<project>/memory/feedback_<name>.md` | Permanent; auto-loaded as user-level memory in future sessions |
| Memory index update | the harness's memory index file | Permanent; loaded at session start |
| Continuation brief | `${COGOS_WORKSPACE:-~/workspaces/cog}/.cog/mem/episodic/handoffs/<date>-<session>-brief.md` OR job dir if ephemeral | Permanent OR session-bound; pick based on whether the work is task-bound |

## Composition with other primitives

- **`handoff`**: consolidate first if there's recognition to preserve; handoff for the task continuity
- **`pull-context-dispatch`**: consolidate's outputs are exactly the kind of pointer-shaped artifacts a pull-context dispatch agent reads from
- **A conversations-observatory feature, if the substrate has one**: the workspace can already see its own conversation history; consolidation produces the curated index on top

## At-risk-of-being-lost section discipline

This is the load-bearing section. Items that came up once in the session and were never captured. Examples that recur:
- A side comment by the operator that named a future direction but didn't get filed
- A trade-off that was articulated but not resolved
- A question the operator asked that drifted before being answered
- An insight the agent had mid-dispatch that didn't make it back to the main thread

**Don't soften.** If something is at-risk, say so concretely with a one-sentence note about what would re-surface it. The point of the section is so the operator (or a future session) can decide whether to act on each item before it drops.

## Anti-patterns

- **Don't summarize the session.** A summary loses the structure of distinctions. The point is to surface what's settled vs heating-up vs at-risk; that's a *sort*, not a *summary*.
- **Don't omit the at-risk section.** If there's nothing at-risk, name that explicitly — but the default assumption is that the agent should look for at-risk items hard, because they're the most-likely-to-be-lost.
- **Don't write the consolidation into the job dir only.** The job dir is ephemeral; the consolidation is durable. Always write at least the cogdoc (or equivalent) + memory entries to durable paths.
- **Don't treat this as the same as handoff.** Handoff moves a task; consolidate captures recognition. A session can need one, both, or neither.

## Substrate framing

The session itself can be treated as a reconciled artifact: its spec is "what we said today" (the conversation), its live state is "what's actually durable" (memory entries, cogdocs, merged code), and consolidation is the reconcile step that computes the gap and applies the plan.

## Related

- A `handoff` skill, if installed alongside this one, covers the architectural framing this skill composes with — consolidate is the reflective-mode primitive; handoff is the transactional one.
