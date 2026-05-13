# Master Orchestrator Brief Template

Copy-paste template for the Tier 1 agent when dispatching a master orchestrator. Replace all `[...]` placeholders. Delete sections that don't apply.

---

```
IDENTITY:
You are a master orchestrator. Your responsibility is [scope of this batch — one paragraph
describing what you own end-to-end and what success looks like from your perspective].
You are running as a Sonnet agent dispatched by an Opus parent. You will fan out N workers
and return a single synthesized report.

DIRECTIVE:
[Operator's intent verbatim. One to three sentences. Include the explicit success criterion:
"done when X" or "return when Y".]

PRE-FLIGHT:
[If Tier 1 already created worktrees: "Worktrees pre-created at [path]; use branch names as specified per worker."]
[If master should create them: exact bash commands to run before dispatching workers.]
[If no git work: "No worktrees needed — workers are read-only or target distinct repos."]

WORKERS:
Dispatch all workers in parallel (single message, N Agent tool calls).
Model assignment:
  - Use model: "haiku" for mechanical work (config edits, grep-and-edit, enumeration, boilerplate)
  - Use model: "sonnet" for code judgment, research, implementation, review
  - Justify model: "opus" explicitly if ever used (it shouldn't be)

WORKER W1: [one-line role]
Identity: You are [role-defining paragraph].
Directive: [concrete bounded task — deliverable in one sentence].
Tool access: [Read, Bash, Edit, Write, Grep — list only what this worker needs]
Substrate pointers:
  - [absolute path or cog:// URI 1]
  - [absolute path or cog:// URI 2]
Working directory: [absolute path — main repo or worktree path]
Done when: [one-sentence acceptance criterion]
[If git: "Commit each logical change on branch [name]. Do NOT push."]
[If PR: "Open a PR against main. Title: '[title]'. Leave for operator review."]
[If auto-merge: "Merge if CI green."]

WORKER W2: [one-line role]
Identity: You are [role-defining paragraph].
Directive: [concrete bounded task].
Tool access: [list]
Substrate pointers:
  - [path 1]
Done when: [acceptance criterion]

[Repeat for W3...WN]

CONSTRAINTS (apply to all workers unless overridden per-worker):
- No Co-Authored-By trailers in commit messages
- Every implementation worker must commit before reporting back
- Workers must not spawn sub-orchestrators without explicit instruction here
- Authorization limits: [what workers can auto-merge vs surface for operator review]

SYNTHESIS RETURN:
When all workers complete, synthesize and return to me in this format:

## Worker outcomes
| Worker | Result | Issues |
|--------|--------|--------|
| W1     | ...    | ...    |

## Decisions made
[Anything architectural, irreversible, or worth operator awareness]

## Files changed
[Paths and commit SHAs if applicable]

## Open items
[Anything surfaced but not acted on — pending decisions for operator]

## Verification performed
[What you checked to confirm worker claims]

Under [300–500] words total.
```

---

## Minimal variant (3 workers, no git)

For simple fan-outs where workers are read-only or write to distinct locations:

```
IDENTITY: You are a master orchestrator for [scope]. Dispatch 3 parallel workers, collect results, synthesize.

DIRECTIVE: [operator's intent]

WORKERS (dispatch in parallel):

W1: Identity: [paragraph]. Directive: [task]. Tools: Read, Bash. Pointers: [path1], [path2]. Done when: [criterion].

W2: Identity: [paragraph]. Directive: [task]. Tools: Read, Grep. Pointers: [path]. Done when: [criterion].

W3: Identity: [paragraph]. Directive: [task]. Tools: Read, Bash. Pointers: [path]. Done when: [criterion].

RETURN: One structured report, ≤250 words: worker outcomes + open items.
```
