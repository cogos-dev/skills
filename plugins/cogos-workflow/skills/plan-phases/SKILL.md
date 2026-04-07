---
name: plan-phases
description: Produce a phased execution plan for multi-step implementations. Decomposes complex tasks into dependency-wired task graphs with wave assignments, role mappings, verification gates, and parallel execution schedules. Use when a task has 5+ discrete steps or requires coordinating work across multiple files or domains.
---

# Skill: plan-phases

Produce a phased execution plan for a multi-step implementation. The plan includes dependency analysis, parallel tracks, role assignments, and verification gates so that every phase is executable, not just a human-readable outline.

## When to Use

- Any implementation with 5+ discrete tasks
- When decomposing a large feature, refactor, or infrastructure change
- When coordinating work across multiple roles or agents
- After exiting plan mode, before starting implementation
- When reviewing an existing plan for parallelization opportunities

## The Method

Eight steps. Do them in order. The output is a dependency-wired task graph with role assignments, coordination primitives, and verification gates.

### Step 1: Inventory

List every discrete unit of work. Each task should be:
- **Independently testable** -- you can verify it works without other tasks
- **Single-responsibility** -- one clear deliverable (a file, an interface, a test suite)
- **Named with a track prefix** -- `A1`, `B2`, `C3` for visual grouping

**Granularity rule:** If a task touches more than 3 files or exceeds ~200 lines, split it. If it's fewer than ~20 lines, merge it with its neighbor.

### Step 2: Dependency Analysis

For each task, ask: **"What must exist before I can start this?"**

Only hard dependencies -- what literally cannot compile, run, or make sense without a predecessor:
- **Type dependencies** -- "I implement an interface defined in task X"
- **Data dependencies** -- "I read output produced by task X"
- **Semantic dependencies** -- "My design requires a decision made in task X"

**Minimize aggressively.** If a task only needs the *types* from another task (not the full implementation), it depends on the types task, not the implementation.

### Step 3: Track Identification

Group tasks into **independent tracks** -- streams of work that share no dependencies until a convergence point.

Naming convention:
- **Track A** -- Core/framework (interfaces, types, plumbing)
- **Track B** -- First concrete implementation (proves the framework)
- **Track C** -- Operational concerns (monitoring, hooks, lifecycle)
- **Track D** -- Design/spec work (documents, schemas, no code)
- **Track E** -- Integration/convergence (needs multiple tracks complete)

Tracks A-D should be startable independently or with minimal wait. Track E converges.

### Step 4: Wave Assignment

Assign each task to a **wave** -- the earliest point it can begin:

- **Wave 0** -- No dependencies. Start immediately. **Maximize tasks here.**
- **Wave 1** -- Depends only on Wave 0 outputs.
- **Wave 2** -- Depends on Wave 1 outputs.
- **Wave N** -- Depends on Wave N-1 outputs.

**Goal:** Minimize total waves (depth) while maximizing tasks per wave (breadth).

### Step 5: Role Assignment

Assign each task a **role** that clarifies the execution posture:

| Role | Capabilities | Typical tasks |
|------|-------------|---------------|
| `coordinator` | Multi-domain orchestration, strategic planning | Phase oversight, cross-track dependencies |
| `domain-manager` | Expert coordination, task decomposition, synthesis | Track ownership, checkpoint coordination |
| `researcher` | Literature review, discovery, codebase exploration | Codebase analysis, prior art, design research |
| `expert` | Deep analysis, specialized domain knowledge | Core implementation, complex algorithms |
| `reviewer` | Falsification, edge cases, adversarial testing | Test suites, code review, validation |
| `architect` | Infrastructure design, failure mode analysis | Interface design, schema definition |
| `implementer` | Code quality, focused execution | Straightforward implementation tasks |

**Assignment rules:**
- Design/spec tasks (Track D) -> `architect` or `researcher`
- Interface/types tasks (Track A, Wave 0) -> `architect`
- Implementation tasks -> `expert` or `implementer`
- Test tasks -> `reviewer`
- Convergence tasks (Track E) -> `domain-manager` or `coordinator`
- Tasks requiring codebase exploration before design -> `researcher`

In single-agent execution (e.g., one Claude Code session), roles are advisory -- they clarify the *posture* for each task. In multi-agent execution (fleets, delegation), roles map to concrete agent assignments.

### Step 5b: Complexity Tier Assignment

Assign each task an **execution complexity tier** that determines which model/agent to dispatch it to. This is evaluated once during planning so dispatch doesn't require re-analyzing the task.

| Tier | Criteria |
|------|----------|
| `low` | Mechanical changes: config edits, flag additions, simple CRUD, template work. Touches <=2 files, <=50 lines changed. |
| `medium` | Templated implementation: adapters following existing patterns, test writing for known interfaces, routine refactors. Touches 2-4 files, <=200 lines. |
| `high` | Safety-critical logic, multi-file architectural changes, complex algorithms, novel implementations without a template. Touches 3+ files or requires cross-module reasoning. |

**Assignment heuristics:**
- If the task is "do X like we did Y" -> `low` or `medium`
- If the task involves security, correctness invariants, or distributed state -> `high`
- If the task is a test suite for already-implemented code -> `low`
- If the task creates a new subsystem or interface -> `medium` (design) or `high` (implementation)
- When in doubt, prefer one tier lower -- cheaper models fail fast and can be escalated

**Include in task tables:** Add a `Tier` column alongside Role and Wave so dispatch is mechanical:

```
| ID | Track | Task | Wave | Role | Tier |
```

### Step 6: Coordination and Verification Gates

Insert verification gates between waves:

**Between waves:**
- Build/compile gate -- `go build ./...`, `npm run build`, `cargo check`, etc.
- Test gate -- `go test ./...`, `npm test`, `pytest`, etc.
- Lint/format gate -- `eslint .`, `ruff check`, etc.

**Between tracks at convergence:**
- Integration test gate -- verify cross-track interfaces work together
- Type-check gate -- ensure shared types are consistent

**At plan boundaries:**
- Full test suite -- all tests pass
- Build verification -- clean build from scratch

### Step 7: Task Registration

Register the current wave's tasks via `TodoWrite`. Each task entry needs:
- **content** -- Track prefix + title: `"A1: Define Reconcilable interface"`
- **activeForm** -- Present continuous: `"Defining reconciliation interface"`
- **status** -- `"pending"` for unstarted tasks

Include a gate entry at the end of each wave:
- **content** -- `"Gate 0->1: build && test"`
- **activeForm** -- `"Running wave 0 verification gate"`

Dependencies are tracked by wave membership, not per-task wiring -- all tasks in Wave N must complete before Wave N+1 begins. Note dependencies in each task's content string (e.g., `"A2: Implement extensions (depends on A1)"`) for human readability.

### Step 8: Visualization and Summary

Render the dependency graph as ASCII art:

```
WAVE 0 (immediate -- no dependencies, run in parallel):
+--------------------------+  +--------------------------+  +--------------------------+
| #1  A1: Short name       |  | #5  C1: Short name       |  | #7  D1: Short name       |
|     Role: architect      |  |     Role: expert         |  |     Role: researcher     |
+------------+-------------+  +------------+-------------+  +--------------------------+
             |                            |
      -- build + test gate --
             |                            |
WAVE 1 (unblocked by Wave 0):
+------------v-----------+  +------------v-----------+  +------------v-----------+
| #2  A2: Name           |  | #3  A3: Name           |  | #6  B1: Name           |
|     Role: expert       |  |     Role: expert       |  |     Role: impl         |
+------------+-----------+  +------------+-----------+  +------------+-----------+
```

Then state:
1. **Maximum parallelism** -- most tasks running simultaneously at any wave
2. **Critical path** -- longest sequential dependency chain (minimum calendar time)
3. **Parallelism ratio** -- total tasks / wave count
4. **Independent starting points** -- what begins immediately with zero context
5. **Verification gates** -- what runs between waves
6. **Role distribution** -- count of tasks per role

## Execution Model

Plans are executed through Claude Code's `TodoWrite` (progress tracking) and `Agent` (subagent spawning) tools. Use `/execute-plan` to run the full execution protocol, or follow the loop manually.

### Task Tracking (TodoWrite)

The **progress dashboard**. Register the current wave's tasks via `TodoWrite`:

- `content` -- Task ID + description: `"A1: Define Reconcilable interface"`
- `activeForm` -- Present continuous: `"Defining reconciliation interface"`
- `status` -- `"pending"` -> `"in_progress"` -> `"completed"`

Wire one wave at a time. When a wave completes, replace the TodoWrite list with the next wave's tasks.

**Dependencies** are tracked by wave membership -- all Wave N tasks must complete before Wave N+1 begins. TodoWrite does not support per-task dependency wiring; wave boundaries are the synchronization primitive.

### Subagent Execution (Agent tool)

The **work engine**. Within each wave, launch unblocked tasks as parallel subagents:

```
# Wave 0 -- launch all three in parallel (single message, multiple Agent calls):
Agent(subagent_type="general-purpose", description="A1: Define types", prompt="...")
Agent(subagent_type="Explore", description="D1: Research spec", prompt="...")
Agent(subagent_type="general-purpose", description="C1: Hook events", prompt="...")
```

**Subagent selection by role:**
| Role | Subagent type | Notes |
|------|--------------|-------|
| `researcher` | `Explore` | Read-only codebase exploration |
| `architect` | `Plan` | Design without writing code |
| `expert` | `general-purpose` | Full read/write capability |
| `implementer` | `general-purpose` | Full read/write capability |
| `reviewer` | `general-purpose` | Can read, run tests, write test files |

Use `run_in_background: true` for tasks that don't block the current message. Read the output file path returned by the Agent tool to check results.

### Wave Execution Loop

For each wave:

1. **Wire tasks** -- register the wave's tasks in `TodoWrite` as `pending`
2. **Launch parallel** -- spawn subagents for all tasks via `Agent` in a single message
3. **Collect results** -- wait for subagents or read background output files
4. **Mark completed** -- update each finished task in `TodoWrite` to `completed`
5. **Run verification gate** -- build, test, lint as appropriate
6. **Next wave** -- replace TodoWrite with next wave's tasks, repeat

## Output Format

Every plan must include:

1. **Task list** -- each task with ID, description, wave, role, and dependency annotations
2. **Wave grouping** -- tasks grouped by wave with dependencies noted in descriptions
3. **ASCII wave diagram** -- showing parallel structure, roles, and gates
4. **Execution schedule** -- which subagent types to use, which tasks run in background
5. **Summary stats** -- parallelism, critical path, roles, starting points, gates

## Principles

**Maximize Wave 0.** Every task without hard dependencies starts here. This determines initial velocity.

**Minimize critical path depth.** If the critical path equals total tasks, you have a sequential plan wearing a parallel costume.

**Design separate from implementation.** Schema, spec, and interface tasks are almost always Wave 0 -- they have no code dependencies and unblock everything.

**Tests are their own tasks.** Don't bundle "implement + test." Implementation is done when code compiles. Test task depends on it and validates correctness.

**Convergence track (E) should be small.** If Track E has many tasks, the independent tracks aren't independent enough.

**Roles clarify posture, not identity.** A researcher approaches a task differently than an implementer -- even if the same agent executes both. Role assignment shapes how the task is executed, not just who does it.

**Track dependencies in wave grouping.** Wave membership is the synchronization boundary. Note per-task dependencies in the task description for human readability, but enforce ordering through waves.

**Gates are real commands.** Verification gates between waves are actual build/test commands that run and must pass, not aspirational notes.
