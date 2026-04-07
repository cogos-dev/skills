---
name: execute-plan
description: Execute a phased plan produced by plan-phases. Transforms dependency-wired task graphs into running work with parallel subagents per wave, verification gates between waves, and persistent progress tracking. Use after plan-phases produces a plan and the user approves it.
---

# Execute Plan

Execute a phased plan produced by `plan-phases`. Transform the plan's dependency-wired task graph into running work -- parallel subagents per wave, verification gates between waves, persistent progress state.

## When to Use

- After `plan-phases` produces a plan and the user approves it
- When the user says "wire it up", "start executing", "run the plan", "go", etc.
- When resuming a partially-executed plan from a previous session
- When `/execute-plan` is invoked directly

## Prerequisites

A plan must exist either:
1. **In conversation context** -- the plan-phases output from this session
2. **In a state file** -- persisted from a prior session (e.g., `active-plan.md` in the project)

The plan must include: task inventory (track-prefixed IDs), wave assignments, role assignments, dependency graph, and verification gates.

## Execution Protocol

Seven steps. Execute in order. Steps 3-7 form a loop that repeats per wave.

### Step 1: Parse the Plan

Extract from the plan-phases output:

| Element | Example | Where to find |
|---------|---------|---------------|
| Tasks | `A1: Define API types` | Task inventory / ASCII diagram |
| Waves | `Wave 0`, `Wave 1` | Wave assignment section |
| Dependencies | `A2 depends on A1` | Dependency analysis / `blockedBy` |
| Roles | `architect`, `expert`, `researcher` | Role assignment column |
| Gates | `npm run build`, `pytest` | Verification gates section |
| Tracks | A (core), B (impl), C (ops), D (docs), E (convergence) | Track identification |

Build a mental model of the full graph before proceeding.

### Step 2: Persist Plan State

Write the plan state to a markdown file so it survives context compaction:

```markdown
---
title: "Active Plan: {plan title}"
status: executing
created: "{date}"
total_tasks: {N}
total_waves: {N}
---

# Active Plan: {title}

## Status
Current wave: 0
Tasks completed: 0/{total}
Last updated: {timestamp}

## Task Registry
| ID | Track | Wave | Role | Status | Description |
|----|-------|------|------|--------|-------------|
| A1 | A | 0 | architect | pending | Define API types |
| D1 | D | 0 | researcher | Process architecture doc |
...

## Wave Progress
### Wave 0
- [ ] A1: Define API types
- [ ] D1: Process architecture doc
...

### Wave 1
- [ ] A2: Implement API types
...

## Verification Gates
- Wave 0 -> 1: `npm run build`
- Wave 1 -> 2: `npm run build && npm test`
...

## Decisions and Notes
{Append decisions made during execution here}
```

### Step 3: Wire TodoWrite

Create TodoWrite entries for the current wave's tasks plus the gate. Do not wire all waves at once -- the list becomes unwieldy and buries the active work.

**Format each task as:**
- `content`: `"{ID}: {description}"` -- e.g., `"A1: Define API types"`
- `activeForm`: `"Executing {ID}: {present participle}"` -- e.g., `"Executing A1: Defining API types"`
- `status`: `"pending"` for current wave tasks

**Include a gate entry at the end:**
- `content`: `"Gate {N}->{N+1}: {verification command}"`
- `activeForm`: `"Running wave {N} verification gate"`

### Step 4: Launch Wave

For each wave, launch all unblocked tasks as parallel subagents in a **single message** with multiple Agent tool calls.

**Role to subagent mapping:**

| Plan Role | `subagent_type` | Capabilities | Notes |
|-----------|----------------|--------------|-------|
| `researcher` | `Explore` | Read-only codebase exploration | Cannot write files |
| `architect` | `Plan` | Design without code | Returns designs, not implementations |
| `expert` | `general-purpose` | Full read/write | Core implementation work |
| `implementer` | `general-purpose` | Full read/write | Focused execution tasks |
| `reviewer` | `general-purpose` | Full read/write test files | Validation and testing |
| `domain-manager` | `general-purpose` | Full read/write | Cross-track coordination |

**Foreground vs background decision:**
- **Foreground** (default): When the next wave depends on this task's output, or when only 1-2 tasks in the wave
- **Background** (`run_in_background: true`): When 3+ tasks run in parallel and there is independent work to do while waiting

**When to use worktree isolation:**
- Tasks that write code in the same directory as other parallel tasks: `isolation: "worktree"`
- Design/doc tasks or tasks in separate directories: no isolation needed
- Research tasks (Explore agents): never need isolation (read-only)

### Step 5: Construct Subagent Prompts

This is the most important step. A subagent has zero context from this conversation. Brief it completely.

**Every prompt must include:**

1. **What to build** -- the specific deliverable (file, interface, document, test)
2. **Why it matters** -- one sentence on how this fits the larger plan
3. **Where to work** -- exact file paths, line numbers, directory
4. **What already exists** -- relevant code, interfaces, or decisions that constrain the work
5. **Acceptance criteria** -- how to know the task is done
6. **What NOT to do** -- scope boundaries, things to avoid

**Do NOT:**
- Say "based on your findings, implement X" -- that pushes synthesis onto the subagent
- Leave file paths vague ("somewhere in the project") -- give exact paths
- Include the entire plan -- give only what is relevant to this task
- Assume the subagent knows what was discussed -- it does not

### Step 6: Collect Results and Update State

As each subagent completes:

1. **Read the result** -- check what was produced, any issues flagged
2. **Verify the deliverable** -- does it match acceptance criteria?
3. **Mark TodoWrite completed** -- update the task status immediately
4. **Update state file** -- mark the task done in the active plan markdown file
5. **Note decisions** -- if the subagent made design choices, record them in the Decisions section

**Failure triage:**

```
Failure?
+-- Build/compilation error
|   '-- Fix in-place, re-run verification, mark complete
+-- Wrong approach / misunderstood requirements
|   '-- Re-prompt with clearer constraints, launch as new agent
+-- Blocked by missing dependency
|   '-- Check if dependency task actually completed. If not, defer to next wave
'-- Scope too large
    '-- Split into subtasks, add to current wave
```

Never silently skip a failed task. Report to the user with the failure reason and proposed resolution.

### Step 7: Verification Gate

After all tasks in a wave complete, run the wave's verification gate:

```bash
# Typical gates (language-dependent):
go build ./...                    # Go compilation gate
npm run build && npm test         # Node build + test gate
cargo check && cargo test         # Rust check + test gate
python -m pytest                  # Python test gate
```

**Gate pass:** Update state file, wire next wave's tasks into TodoWrite, return to Step 4.

**Gate fail:** Diagnose the failure. Common causes:
- Type mismatch between parallel tasks: fix and re-gate
- Test regression from a task that skipped existing tests: fix and re-gate
- Build error from incompatible changes: reconcile and re-gate

Report gate results to the user before proceeding to the next wave.

## Cross-Session Continuity

If a session ends mid-plan (context compaction, user ends session):

1. The state file (e.g., `active-plan.md`) persists in the project
2. On the next session, read the state file to see where execution stopped
3. Check which tasks are marked complete vs pending
4. Resume from the current wave -- re-check gate status before launching new tasks
5. Verify completed tasks still hold (files exist, tests pass) before assuming they are done

**To resume:** Read the state file, check `git log` for commits since last update, verify the codebase matches expected state, then continue the wave loop.

## Progress Reporting

At each wave boundary, report to the user:

```
Wave {N} complete ({M}/{total} tasks done)
|-- Completed: {list of task IDs and one-line summaries}
|-- Gate: {pass/fail + command output summary}
|-- Decisions made: {any design choices subagents made}
'-- Next: Wave {N+1} -- {count} tasks: {ID list}
```

Keep it concise. The user can read diffs and state files for detail.

## Plan Modification During Execution

Plans are not immutable. During execution:

- **Add tasks** -- a subagent discovers work not in the original plan. Add to the appropriate wave/track.
- **Split tasks** -- a task is too large. Split and re-assign within the same wave if no new dependencies.
- **Re-sequence** -- a dependency assumption was wrong. Move the task to a later wave.
- **Drop tasks** -- a task is no longer needed. Remove from TodoWrite and state file.

Always update the state file and inform the user when modifying the plan.

## Principles

**One wave at a time.** Complete verification before moving on. Catching integration issues early is cheaper than debugging them at convergence.

**Prompts are the product.** Subagent output quality is directly proportional to prompt quality. Include file paths, type definitions, constraints. Never delegate understanding.

**State file is source of truth.** TodoWrite is for in-session visibility. The state file is for cross-session continuity. Keep both in sync but trust the state file when they diverge.

**Report failures fast.** A failed task in Wave 1 may invalidate Waves 2-N. Surface it immediately.

**No speculative execution.** Do not start Wave N+1 tasks while Wave N's gate is pending, even if they seem independent. The gate exists for a reason.
