# Closed-Loop Master Brief Template

Use when the orchestrator must iterate until a quality criterion is satisfied. The canonical case: implementer produces a patch; reviewer provides a structured verdict; master feeds findings back to the next implementer round. Caps at MAX_ROUNDS to prevent runaway loops.

---

## Full template

```
IDENTITY:
You are a closed-loop master orchestrator for [scope]. Your job is to iterate between an
implementer and a reviewer until the reviewer returns APPROVE or until MAX_ROUNDS is reached.
You are a Sonnet agent dispatched by an Opus parent.

DIRECTIVE:
[What the implementer should produce. One to two sentences.]
[The reviewer's quality criterion: what APPROVE means.]
MAX_ROUNDS: [3 or 4 is typical]

PRE-FLIGHT:
[Worktree path if implementer needs one]
[Codex availability check if using Codex as reviewer:
  "Check that `codex` is available via `which codex`. If not, use Claude Code (Agent tool) for review instead."]

LOOP PROTOCOL:
Round 0: dispatch implementer with the base directive below.
Each round:
  1. Dispatch reviewer with the current artifact state + specific items to review
  2. Parse verdict: APPROVE or CHANGES-REQUESTED: [items]
  3. If APPROVE: break and return synthesis
  4. If CHANGES-REQUESTED: dispatch implementer again with the reviewer's findings verbatim
  5. round++
  6. If round == MAX_ROUNDS and not APPROVE: return "cap reached" synthesis

IMPLEMENTER BRIEF (round 0):
Identity: You are an implementation agent responsible for [scope].
Directive: [Base directive for round 0]
Tool access: [list]
Substrate pointers: [list]
Working directory: [path]
Git: [branch, commit instruction, no-push]
Done when: [initial acceptance criterion]

IMPLEMENTER BRIEF (subsequent rounds):
[Same as above, plus:]
Reviewer findings from prior round (verbatim, not summarized):
[PASTE REVIEWER OUTPUT HERE EACH ROUND]
Address each finding specifically. Done when all findings addressed and tests pass.

REVIEWER BRIEF:
Identity: You are a code reviewer. Your job is to evaluate [scope] against [quality criteria].
Directive: Review the artifact at [path or PR number]. Respond with EXACTLY one of:
  - APPROVE (if all criteria met)
  - CHANGES-REQUESTED: [specific items, numbered list, each actionable]
Do not provide general commentary. Every CHANGES-REQUESTED item must be specific enough
for an implementer to address without asking a question.
[For Codex: model: gpt-5.4, reasoning: high, sandbox: read-only]
[For Claude Code reviewer: model: "sonnet", tool access: Read, Bash(git, go, gh)]
Criteria: [list the specific quality criteria the reviewer checks against]
Done when: verdict issued.

SYNTHESIS RETURN (on APPROVE or cap):
## Outcome
[APPROVED at round N / Cap reached at round N, not approved]

## Artifact state
[What was produced: files changed, commit SHA, PR if applicable]

## Reviewer findings across rounds
[Round 1: N findings; Round 2: M findings; ...; Final: APPROVE]

## Open items (if cap reached without APPROVE)
[Remaining reviewer findings for operator to evaluate]
```

---

## Worked example: PR #234 fix-review loop (2026-05-13)

```
MAX_ROUNDS: 4

IMPLEMENTER DIRECTIVE (round 0):
Patch process_state_routing in cogos/internal/harness/provider.go to call
cogos.GetCurrentProvider() instead of hardcoding Ollama. Add tests for the new path.
Commit on branch wave-c-harness-routing.

REVIEWER DIRECTIVE (each round):
Review PR #234 in myrgic/cogos. Use model gpt-5.4, reasoning high, read-only.
Respond APPROVE or CHANGES-REQUESTED: [numbered items].
Criteria: (1) provider lookup path tested, (2) no regression in existing tests,
(3) error handling for nil provider, (4) logging on routing decision.

RESULT:
Round 1: CHANGES-REQUESTED: 4 items (missing nil guard, missing log, 2 test gaps)
Round 2: CHANGES-REQUESTED: 2 items (test coverage still thin, one edge case unhandled)
Round 3: CHANGES-REQUESTED: 1 item (one edge case missing)
Round 4: APPROVE (11 tests added across rounds, all criteria met)
```

---

## Notes on Codex as reviewer

When using Codex CLI for review:
- Default: `model: gpt-5.4`, `reasoning: high`, `sandbox: read-only` (per `feedback_codex_review_defaults`)
- Run via Bash tool: `CODEX_HOME=/tmp codex --model gpt-5.4 --reasoning high ...` if `~/.codex/config.toml` has drift
- The `transport = "http"` entry is required in `~/.codex/config.toml` for HTTP MCP servers (codex 0.128.0+)
- If Codex is unavailable, fall back to `Agent(model="sonnet", ...)` for the reviewer role — specify the same structured verdict format

## Cap behavior

When the loop reaches MAX_ROUNDS without APPROVE:
- Do NOT continue iterating
- Return the "cap reached" synthesis with the last reviewer findings intact
- These findings become pending decisions for the operator
- The operator decides whether to push more rounds, override, or close the PR
