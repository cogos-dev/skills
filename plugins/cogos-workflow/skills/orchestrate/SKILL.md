---
name: orchestrate
description: Dispatch a Sonnet master orchestrator that fans out N parallel Sonnet/Haiku workers, synthesizes their work, and returns to the Tier 1 parent. Use when ≥3 parallel bounded items need parallel execution + synthesis. Triggers on /orchestrate, "orchestrate this", "dispatch in parallel", "have agents work on this in parallel", "knock these out in parallel", "fan out workers".
version: 1.0.0
allowed-tools: Agent, Bash, Read, Write, Edit, Grep, TodoWrite
canonical_source: cog://workspaces/cog/.claude/skills/orchestrate/SKILL.md
projection_note: This file is a marketplace projection. Canonical source lives in the cog workspace at the path above. Update canonical first; project here after.
---

# Orchestrate: Master-Orchestrator Pattern

Dispatch a single Sonnet master orchestrator that decomposes a broad operator directive into N bounded worker tasks, fans them out in parallel, synthesizes their outputs, and returns one concise report. The Tier 1 parent (Opus) pays only two dispatch-tokens round-trips: one to dispatch the master, one to receive the synthesis.

## When to use

**Trigger conditions — all three should hold:**
- **≥3 parallel bounded items**: the work decomposes into independent chunks with clear ground states
- **Synthesis needed**: the Tier 1 context shouldn't absorb N independent worker reports directly
- **Operator has delegated broadly**: "knock these out," "push forward," "work through these in parallel"

**Do NOT use when:**
- 1–2 items: overhead exceeds benefit — use `dispatch-agent` directly
- Items are sequential or tightly dependent: use `execute-plan` against a planned phase
- Cross-model deliberation is the goal: use `council` (perspectives, not parallel execution)
- The items require operator decision between them: use sequential `dispatch-agent` calls instead

Related skills: `dispatch-agent` (single dispatch), `council` (multi-perspective deliberation), `plan-phases` + `execute-plan` (when a full dependency plan already exists).

---

## The three-tier shape

```
Tier 1: parent (Opus, running in conversation)
  └── dispatch → Master Orchestrator (Sonnet)
       ├── Worker 1 (Sonnet) ─── pull-context ─── reports
       ├── Worker 2 (Sonnet) ─── pull-context ─── reports
       ├── Worker 3 (Haiku, mechanical leaf) ─── reports
       └── Worker N ─── ...
       ↓ all complete
       Master synthesizes ─── concise report ──→ Tier 1
```

**Why three tiers:**
- Master absorbs N worker outputs so Tier 1 context stays clean
- Workers use pull-context dispatch (no pre-summarization — see `pull-context-dispatch` skill)
- Mechanical leaves use Haiku; substantive implementation and research uses Sonnet
- Opus remains at the conversation and synthesis layer only
- Tier 1 → Tier 2 → Tier 3 is the practical depth ceiling; beyond three tiers, reasoning accountability degrades

**Note on Tier 1 in Hermes:** In Hermes gateway sessions (Telegram, Discord, CLI), Tier 1 is typically Sonnet (the main model by default). The tier model still applies — dispatch Tier 2 workers with a lower-cost profile. The semantic is preserved; the model assignment is controlled by profile config. "Tier 1 is the calling context, whatever model is running there."

---

## Platform binding

Both platforms support the orchestrate pattern. Use the syntax native to your environment.

**Claude Code — dispatch the master:**
```python
Agent(
    subagent_type="general-purpose",
    model="claude-sonnet-4-6",           # MUST be explicit — Tier 2
    description="Master orchestrator: <one-line task>",
    prompt=MASTER_BRIEF,
    run_in_background=True
)
```

**Hermes — dispatch the master:**
```python
result = delegate_task(
    goal=MASTER_BRIEF,
    context="substrate pointers only",
    role="orchestrator",   # enables nested dispatch
    toolsets=["terminal", "file", "web"],
)

# For durable multi-step work that must survive session boundaries:
# hermes kanban create 'task title' --profile sonnet --goal --goal-max-turns 20
```

**Tier → profile/model mapping:**

| Tier | Role | Claude Code | Hermes |
|------|------|-------------|--------|
| Tier 1 | Calling context | Opus (claude-opus-4-8) | Main session model (default: Sonnet) |
| Tier 2 | Master orchestrator / substantive workers | Sonnet (claude-sonnet-4-6) | profile=sonnet (or equivalent named profile) |
| Tier 3 | Mechanical leaf tasks | Haiku (claude-haiku-4-5-20251001) | profile=haiku (or equivalent named profile) |

These defaults are configurable. The tier abstraction survives the platform split.

---

## Procedure for Tier 1

### 1. Decompose

Identify the N workers and the ground state for each. For each worker, specify:
- What "done" looks like (one sentence)
- Which files, repos, or substrate pointers the worker needs
- Whether it will write to git (requires worktree isolation)

### 2. Pre-flight

If any worker touches git in a shared repo, pre-create one worktree per worker **before dispatch**. Never share a working tree across concurrent agent dispatches — the failure mode (branches silently cross-merge) is quiet and destructive.

```bash
# Pre-create worktrees for workers that write to git
REPO=/path/to/repo
for w in worker-1 worker-2 worker-3; do
  git -C "$REPO" worktree add "$REPO/../agent-worktrees/$w" -b "wave/<date>/$w"
done
```

Read-only workers (research, code dive, documentation) do not need worktrees.

### 3. Write the master brief

Fill the master brief template (see `resources/master-brief-template.md`). The brief must include:
- **Identity**: one paragraph naming the master's responsibility
- **Directive**: the operator's intent, with explicit success criterion
- **Worker briefs**: N pull-context-dispatch-shaped worker descriptions
- **Pre-flight setup**: any worktree-creation commands if not done by Tier 1
- **Constraints**: model tiering, commit requirement, no Co-Authored-By, authorization limits
- **Synthesis return shape**: what format and fields the master returns

### 4. Dispatch

**Claude Code:**
```python
Agent(
    subagent_type="general-purpose",
    model="sonnet",           # MUST be explicit — Tier 1 is Opus; children inherit without override
    description="Master orchestrator: <one-line task>",
    prompt=MASTER_BRIEF,
    run_in_background=True    # unless Tier 1 has nothing to do while waiting
)
```

**Hermes:**
```python
result = delegate_task(
    goal=MASTER_BRIEF,
    context="substrate pointers only",
    role="orchestrator",
    toolsets=["terminal", "file", "web"],
)
```

### 5. Verify on return

Trust but verify. When the master returns:
- Spot-check the most impactful worker claims against the substrate (read one or two files)
- Check `git log` if commits were expected
- For PRs: confirm they opened with `gh pr list`
- Surface the synthesis to the operator with any caveats from verification

---

## Master brief template

See `resources/master-brief-template.md` for the full copy-paste template. The essential shape:

```
IDENTITY:
You are a master orchestrator. Your responsibility is [scope of this batch].
You are running as a Tier 2 agent dispatched by the Tier 1 calling context.
(In Claude Code sessions: dispatched by an Opus parent. In Hermes sessions: dispatched by the main gateway session.)

DIRECTIVE:
[Operator's intent verbatim + explicit success criterion]

PRE-FLIGHT (if applicable):
[Worktree creation commands or "pre-flight completed by parent"]

WORKERS:
Dispatch all workers in parallel (single message, multiple Agent calls).
Worker model: use "haiku" for mechanical work, "sonnet" for code/research judgment.

[W1: pull-context-dispatch-shaped brief for worker 1]
[W2: pull-context-dispatch-shaped brief for worker 2]
...

CONSTRAINTS:
- No Co-Authored-By trailers in commits
- Every implementation worker must include "commit each logical change" in its brief
- [Authorization limits: what workers can auto-merge vs surface]
- Do not spawn sub-orchestrators (no Tier 3+) without explicit authorization

SYNTHESIS RETURN:
When all workers complete, return a single structured report to me:
- Worker outcomes (one line each: ID, result, any issues)
- Decisions made (anything architectural or irreversible)
- Files changed (paths, commit SHAs if applicable)
- Open items (anything surfaced but not acted on)
- Verification performed
Under [N] words total.
```

---

## Worker brief template

Each worker brief is pull-context-dispatch-shaped. Do not pre-summarize the substrate for the worker — pass pointers and let the worker observe.

```
WORKER [ID]: [one-line role]
Identity: You are [role-defining paragraph — what this worker is responsible for].
Directive: [concrete bounded task — what exactly to deliver]
Tool access: [explicit list: Read, Bash, Edit, Write, Grep, etc.]
Substrate pointers:
  - [path/URI/ID 1]
  - [path/URI/ID 2]
Constraints:
  - Working directory: [path — absolute, or worktree path if applicable]
  - [git: commit each logical change on branch <name>; do not push]
  - [authorization: auto-merge OK / leave for operator / read-only]
Done when: [acceptance criterion — one sentence]
```

See `resources/worker-brief-template.md` for the full template with examples.

---

## Closed-loop variant

Use when the orchestrator's purpose is iterate-until-criterion-met rather than single-pass fan-out. The canonical example is the PR #234 fix-review loop (2026-05-13): one implementer worker patched the harness routing gap; a Codex reviewer (gpt-5.4, high effort, read-only) produced a structured verdict; the master parsed the verdict, checked the round cap, and either re-dispatched the implementer with the reviewer's findings or returned APPROVE.

**When to use the closed-loop variant:**
- A quality criterion must be satisfied before proceeding (reviewer must APPROVE)
- The criterion is machine-parseable (structured verdict: APPROVE / CHANGES-REQUESTED)
- You have a concrete cap on iterations (prevent runaway loops)

**Closed-loop structure:**
```
Master:
  round = 0
  while round < MAX_ROUNDS:
    dispatch implementer (Sonnet) → produces artifact
    dispatch reviewer (Sonnet or Codex) → structured verdict
    if verdict == APPROVE: break
    feed reviewer findings back to implementer brief
    round++
  if round == MAX_ROUNDS and not approved:
    return "cap reached, last state: <summary>"
  return "APPROVED at round N, <summary>"
```

**Constraints for closed-loop:**
- Set MAX_ROUNDS before starting (3–4 is typical; PR #234 capped at 4, approved at round 4)
- Reviewer brief must specify the verdict format: `APPROVE` or `CHANGES-REQUESTED: <specific items>`
- Implementer brief each round must include the reviewer's specific findings from the prior round — not a summary, the actual findings verbatim
- Cap the loop at MAX_ROUNDS even if not approved; surface to operator rather than looping indefinitely

See `resources/closed-loop-template.md` for the full template.

---

## Authorization patterns

Workers have different authorization levels depending on what they touch. Encode these in the master brief explicitly — do not leave them implicit.

| Work type | Authorization |
|---|---|
| Substrate-only changes (cogdocs, config, skills) | Auto-merge OK if CI green |
| Documentation, gitignore, repo hygiene | Auto-merge OK if CI green |
| Skill file PRs (plugins repo) | Auto-merge OK if CI green |
| Kernel feature PRs | Leave open for operator review — never auto-merge |
| Architectural RFCs / ADRs | Open PR + leave open; operator decides |
| Operational hygiene (storage, launchd, observers) | Auto-merge OK |
| Anything touching concurrency, auth, or dispatch routing | Leave for operator review |

---

## Anti-patterns

**Pre-summarizing context for workers** — defeats pull-context. If you write a summary of what's in a cogdoc, you're paying generation cost in the master brief AND biasing the worker's perception. Pass the pointer; let the worker read it.

**Shared worktrees across parallel git work** — silent cross-merge failure mode. Both agents report success; one branch contains the other's changes. Always pre-create one worktree per concurrent writer.

**Vague ground state per worker** — "work on the routing" is not a ground state. "Patch `process_state_routing` in `harness/provider.go` to consult `cogos.GetCurrentProvider()` instead of hardcoding Ollama; confirm existing tests pass; commit on branch `wave-c-harness-routing`" is a ground state.

**Auto-merging kernel concurrency changes** — any change to provider dispatch, session management, or mutex logic in the kernel is operator-review territory regardless of CI.

**Letting workers spawn unbounded sub-dispatches** — set the sub-agent budget in the master brief. Workers should not fan out further without explicit authorization. "Dispatch one worker for X, not a fleet of sub-workers" is a valid constraint.

**Recursing orchestrators past Tier 3** — Tier 1 (calling context) dispatches Tier 2 (Sonnet master), which dispatches Tier 3 (Sonnet/Haiku workers). Tier 4+ exists but becomes hard to reason about. Flag if you find yourself writing a "dispatch an orchestrator to orchestrate orchestrators" prompt.

**Omitting the commit instruction from implementation worker briefs** — agents leave work uncommitted unless explicitly told to commit. Always include "commit each logical change with a clean message" in any implementation worker's directive.

---

## Worked examples

The examples below are accurate records from Claude Code sessions (Tier 1 = Opus). The pattern applies identically in Hermes — substitute `delegate_task(role='orchestrator')` for the `Agent(...)` calls and Hermes profiles for model names.

### Wave A — 7-worker storage and infrastructure sweep (2026-05-13)

**Setup:** The substrate had accumulated storage drift (HF cache scattered, old Ollama store occupying 42 GB, mlx-lm fork uncloned, launchd plists missing). Seven independent items with zero cross-dependencies.

**Structure:** Master dispatched 7 parallel Sonnet workers: storage hygiene (SSD HF cache trim), launchd plist audit and repair, vllm clone into `~/workspaces/myrgic/`, mlx-lm fork setup, autonomic cycle verification, issue observatory scaffold, and skill migration audit. Workers were read-write for their own scopes and read-only everywhere else. No worktrees needed — each worker's target was a distinct location.

**What was novel:** The scope decomposition itself was the hard part. The master's brief included a coverage matrix ("each worker owns exactly one concern; no worker should discover it needs to touch another worker's target"). The post-synthesis verification ran `df -h` to confirm storage claims matched reported worker output.

---

### Wave B — 6-worker mixed research and targeted writes (2026-05-13)

**Setup:** The mlx-lm runtime was running but its KV cache architecture was unknown, vllm's block-cache design needed mapping for the upcoming mlx fork, and the harness routing had a suspected Ollama-hardcoding gap.

**Structure:** Master dispatched 6 workers: vllm code dive (read-only Sonnet, produced cogdoc), mlx-lm cache architecture dive (read-only Sonnet, produced cogdoc), live routing verification (Bash-enabled, produced diagnostic), substrate health diagnostic (read-only, produced component-warnings cogdoc), inventory anomaly triage (read-only, produced recommendations cogdoc), RFC-0008 amendment (write, produced PR). The B3 routing verification worker surfaced the specific gap in `process_state_routing` that motivated PR #234.

**What was novel:** The mixed read-only / write worker set within a single master dispatch. Workers were explicitly told their authorization level in their briefs; the write worker (RFC-0008 amendment) was told to open a PR and leave it for operator review.

---

### Wave C — 4-worker config and research (2026-05-13)

**Setup:** Discord wiring was broken (config.hcl missing), the harness routing gap from Wave B needed a fix PR, provider names were misaligned with machine names (mlx-gemma should be mlx-lm), and vLLM feasibility on Eclipse needed a spike.

**Structure:** 4 parallel workers: Discord wiring fix (write, applied config.hcl, auto-merge authorized), harness routing PR (write to worktree, opened PR #234, leave for review), provider rename (write to providers.local.yaml), vLLM-on-Eclipse feasibility spike (read-only research + cogdoc). The Eclipse spike returned WAIT because the worker discovered Eclipse runs Windows, making ROCm irrelevant.

**What was novel:** The vLLM spike worker was dispatched into a cloud-provider feasibility question but independently discovered the OS constraint and returned a WAIT verdict with the reasoning. That's the pattern working correctly — workers with clear ground states and read access to substrate can self-terminate on relevant findings.

---

### Council variant — 5-seat RFC evaluation (2026-05-12)

**Setup:** Three new RFCs (RFC-0004, RFC-0005, RFC-0006) needed multi-perspective evaluation before ratification.

**Structure:** This was council-shaped (perspectives, not execution), so it used the `council` skill pattern rather than `orchestrate`. Five seats with distinct lenses (formalist, convergence, cogsci, refuser, pragmatist). Each seat wrote to a dedicated worktree branch. Calling layer synthesized into a ratification recommendation.

**When to prefer council over orchestrate:** When you need genuinely independent perspectives on the same artifact (convergence-without-coordination is the signal). When you need cross-model verification (council supports it; orchestrate is typically single-model). When the goal is a deliberation record, not a task-completion record.

See the `council` skill for the full protocol.

---

### Closed-loop fix-review — PR #234 (2026-05-13)

**Setup:** PR #234 had a harness routing gap confirmed by Wave B. The change needed implementation and a quality review before merge.

**Structure:** Master orchestrator (Sonnet) ran a closed-loop with MAX_ROUNDS=4: Sonnet implementer patched `process_state_routing` in the harness to consult `cogos.GetCurrentProvider()` instead of the Ollama hardcode; Codex reviewer (gpt-5.4, high, read-only) reviewed the PR diff and produced a structured verdict. Round 1–3 returned CHANGES-REQUESTED with specific items; the implementer integrated each finding. Round 4 returned APPROVE after the implementer added 11 tests covering the new routing paths. Master returned APPROVED at round 4 to Tier 1.

**What was novel:** The Codex reviewer ran via CLI with `CODEX_HOME=/tmp` workaround (there was a config drift issue with `transport = "http"` in `~/.codex/config.toml`). The master brief included a fallback path for the Codex invocation and a note that the workaround was temporary. Tier 1 logged the config drift as a pending decision for the next session. The loop pattern itself worked as designed — reviewer findings flowed verbatim into the next implementer brief each round.

---

## Composes with

- **`pull-context-dispatch`** — each worker is pull-context-dispatch-shaped. The orchestrate skill IS the multi-worker peer to a single pull-context dispatch. Never pre-summarize worker context; pass substrate pointers.

- **`dispatch-agent`** — single-agent variant. Use `dispatch-agent` when ≤2 items. `/orchestrate` is its multi-agent peer when ≥3 items need synthesis.

- **`council`** — cross-model or multi-perspective deliberation variant. Council is the right shape when you want orthogonal lenses and convergence-without-coordination. Orchestrate is the right shape when you want parallel execution and synthesis of bounded tasks.

- **`plan-phases` + `execute-plan`** — when a full dependency-wired plan already exists, `execute-plan` runs each wave. The `/orchestrate` pattern applies naturally to individual waves: each wave is a master dispatch with N workers per the wave's task set.

- **RFC-034 binding pattern** — the orchestrate pattern maps cleanly onto the Reconcilable binding primitives:

  | RFC-034 primitive | Orchestrate instantiation |
  |---|---|
  | Class | `OrchestrateClass` — the pattern itself; declares how N-item parallel work should be structured |
  | Claim | Each operator invocation — "these N items should be worked in parallel with synthesis" |
  | PhysicalInstantiation | The actual master orchestrator agent + its N worker agents running in the substrate |
  | Reconciler | The master orchestrator — observes worker outputs, detects drift from target state (items incomplete, quality gates unmet), synthesizes resolution |

---

## Episodes

### 2026-05-13 — 7-wave multi-agent session (Waves A, B, C)
Command: `/orchestrate` invoked implicitly (Tier 1 Opus dispatched masters as the session's primary work pattern)
Workers dispatched: 17 across Waves A, B, C
PRs produced: #234 (harness routing), #6 (cogos-architecture plugin), #5 (local-review skill), and multiple merged PRs across cogos main
Closed-loop run: PR #234 fix-review loop, APPROVED at round 4, 11 tests added
Notes: First session to use the three-tier shape consistently. The vLLM-on-Eclipse spike (Wave C W4) demonstrated autonomous WAIT-verdict from a worker based on substrate observation. The PR #234 closed-loop is the founding reference for the closed-loop variant.

---

## Learnings

- Ground state per worker is the most important investment at decomposition time. Vague ground states produce workers that keep going past intent or return partial results that can't be synthesized cleanly.
- Mixed authorization within a single dispatch is fine — encode it explicitly per worker. Auto-merge OK for hygiene, leave-for-operator for kernel changes, no-op for research.
- The closed-loop variant requires verbatim reviewer findings in the next implementer brief — not a summary of findings. Summarizing compounds the "telephone" problem across rounds.
- Codex CLI config drift (missing `transport = "http"`) blocks the review path silently. The closed-loop template now includes a Codex availability pre-flight check.
- Children inherit the parent's model when `model` is not specified. Tier 2 master and Tier 3 workers must have explicit `model: "sonnet"` or `"haiku"` — never rely on inheritance from an Opus parent.
