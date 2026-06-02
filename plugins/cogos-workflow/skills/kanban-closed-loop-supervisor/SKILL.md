---
name: kanban-closed-loop-supervisor
description: >
  Closed-loop orchestration over Hermes delegate_task + Kanban.
  Use when >=3 parallel bounded items need parallel execution + synthesis
  AND a quality criterion must be satisfied before proceeding (reviewer must GO).
  Binds the harness-agnostic orchestrate pattern to Hermes dispatch machinery.
  Extends kanban-orchestrator; does NOT replace it.
version: 1.0.0
platforms: [linux, macos, windows]
canonical_source: /Users/slowbro/.hermes/hermes-agent/skills/devops/kanban-closed-loop-supervisor/SKILL.md
projection_note: >
  This file is a marketplace projection. Canonical source lives in the Hermes
  agent repo at the path above (canonical_source). Update canonical first;
  project here after. Mirror the pattern from orchestrate/SKILL.md line 7.
metadata:
  hermes:
    tags: [orchestration, delegate_task, kanban, closed-loop, worktrees]
    related_skills: [kanban-orchestrator, kanban-worker, orchestrate]
---

# Kanban Closed-Loop Supervisor (projection)

This is a projection. See canonical_source above for the authoritative text.

Hermes binding of the harness-agnostic `orchestrate` pattern. The pattern
(tier discipline, pull-context dispatch, structured-verdict parse, dynamic
round cap, operator-decisions break the loop) is the invariant. This skill
binds it to delegate_task + Kanban + webhook-wake.

This skill is a THIN OVERLAY over delegate_task's orchestrator role.
It does NOT rebuild the dispatch mechanism. It encodes the doctrine.

Load the `kanban-orchestrator` skill too -- this skill extends it.

---

## When to use

All three conditions should hold:

1. >=3 parallel bounded items with clear ground states.
2. Synthesis needed.
3. A quality criterion must be satisfied (seam reviewer must emit GO).

Do NOT use when:
- 1-2 items: use delegate_task directly.
- Items sequential: use execute-plan.
- No quality gate: use kanban-orchestrator.

---

## The three-tier model

```
Tier 1: you (in conversation)
  |
  +-- dispatch --> Tier 2: Orchestrator (role='orchestrator' in delegate_task)
                    |
                    +-- Worker 1 (leaf)
                    +-- Worker 2 (leaf)
                    +-- Worker N (leaf)
                    v
                   Reviewer -> OVERALL: GO / NO-GO <seams>
                    |
                    +-- GO: synthesize -> return to Tier 1
                    +-- NO-GO: re-dispatch (up to MAX_ROUNDS, then escalate)
```

---

## Hermes binding

Enable nested orchestration in config.yaml:

```yaml
delegation:
  max_spawn_depth: 2
  max_concurrent_children: 5
  orchestrator_enabled: true
```

Dispatch:

```python
result = delegate_task(
    goal="[orchestrator brief]",
    context="[substrate pointers only]",
    role="orchestrator",   # REQUIRED
    toolsets=["terminal", "file", "web"],
)
```

---

## Verdict contract

Reviewer final line must be exactly:

  OVERALL: GO

  or

  OVERALL: NO-GO <seam-ids>

Parse with scripts/verdict-parser.sh (in canonical location):

  verdict=$(bash /path/to/verdict-parser.sh "$REVIEWER_OUTPUT")

---

## Dynamic round cap

The supervisory agent IS the cap. Escalate to Tier 1 on:
  (a) Same-seam NO-GO twice (spec ambiguity)
  (b) Irreversible action needed (merge/push/publish -- always surface)
  (c) Iteration redefines intent rather than executes it

Default MAX_ROUNDS=2. Raise with operator when stakes are high.

---

## Gate-decision topology

Merge/push/publish always surfaces to Tier 1.
NO-GO the loop cannot resolve surfaces to Tier 1.
Everything else: the orchestrator drives.

---

## Full doctrine

See canonical_source for the complete skill including:
- Pull-context brief format
- Worktree isolation procedure
- Closed-loop variant (implementer -> reviewer loop)
- Authorization patterns table
- Anti-patterns
- Synthesis return shape
- Worked references
