# Worker Brief Template

Each worker brief is pull-context-dispatch-shaped. Do NOT pre-summarize what's in the substrate pointers — pass paths and let the worker observe. One brief per worker.

---

## Full template

```
WORKER [ID]: [one-line role — e.g., "harness routing patcher" or "vllm cache architecture researcher"]

Identity:
You are a [role descriptor]. Your responsibility in this batch is [what this worker owns,
isolated from what other workers own]. You are a Sonnet agent dispatched by a master
orchestrator. [One to two sentences. Role-defining, not task-describing.]

Directive:
[The concrete, bounded deliverable — one or two sentences.]
[One-sentence "done when": "Done when [specific acceptance criterion]."]
["Do NOT [scope boundary 1]." "Do NOT [scope boundary 2]."]

Tool access:
[List only the tools this worker needs:]
- Read
- Bash (for: git, grep, gh)
- Edit
- Write
[Omit tools not needed. Reduces hallucination surface.]

Substrate pointers:
[Pass paths/URIs/IDs — NOT quoted content. The worker reads these itself.]
- [absolute/path/to/file.go]
- [cog://mem/semantic/insights/topic.cog.md]
- [~/workspaces/myrgic/cogos/internal/harness/provider.go]
[3–7 pointers is typical. More than 10 suggests the directive is too broad.]

Working directory: [absolute path]
[For worktree workers: the worktree path, not the main repo path]
[For read-only workers: the main repo or any stable path]

Git instructions (if applicable):
- Branch: [name — e.g., "wave-c-harness-routing"]
- Commit each logical change with a clean message (no Co-Authored-By trailers)
- Do NOT push — master orchestrator handles coordination

Authorization:
[Exactly one of:]
- Auto-merge if CI green
- Open PR, title "[title]", leave for operator review
- No commits — report findings only
- Apply changes in place; no PR needed

Done when:
[One sentence. Should be independently verifiable by the master orchestrator.]
Examples:
  - "harness_routing.go updated, existing tests pass, new test covers provider-lookup path, committed"
  - "cogdoc at /path/to/file written with sections: [list]"
  - "PR #NNN open with description matching [spec]"
  - "feasibility report includes: current constraints, blockers, WAIT/GO verdict"
```

---

## Examples

### Read-only research worker

```
WORKER W1: vllm block-cache architecture researcher

Identity: You are a code dive researcher. Your task in this batch is to map the KV-cache
architecture in the vllm codebase — specifically the PagedAttention block management layer.
You are read-only; you produce a cogdoc, not code changes.

Directive: Read the vllm source at ~/workspaces/myrgic/vllm/ and produce a cogdoc that maps
the block-cache design: how blocks are allocated, how the block manager decides evictions,
what the content-address primitive looks like in code. Done when the cogdoc exists with
sections: Block Primitive, BlockManager, Eviction Policy, Content-Address Analog.

Tool access: Read, Bash (grep only)

Substrate pointers:
- ~/workspaces/myrgic/vllm/vllm/core/block/
- ~/workspaces/myrgic/vllm/vllm/core/scheduler.py
- ~/workspaces/cog/.cog/mem/semantic/architecture/vllm-block-cache-architecture.cog.md

Working directory: ~/workspaces/myrgic/vllm/

Authorization: No commits — write cogdoc to the pointer path above, report done.

Done when: cogdoc written with all four sections, each ≥100 words.
```

### Implementation + PR worker

```
WORKER W2: harness routing patcher

Identity: You are an implementation agent. Your responsibility is to patch the harness
routing function to consult the kernel's current provider registry rather than hardcoding
Ollama as the dispatch target. You work in an isolated worktree.

Directive: Patch process_state_routing in ~/workspaces/myrgic/cogos-worktrees/wave-c-w2/
internal/harness/provider.go to call cogos.GetCurrentProvider() before routing. Run
existing tests; add a test for the new provider-lookup path. Commit and open a PR.

Tool access: Read, Edit, Bash (go, git, gh)

Substrate pointers:
- ~/workspaces/myrgic/cogos/internal/harness/provider.go
- ~/workspaces/myrgic/cogos/internal/kernel/providers.go
- ~/workspaces/cog/.cog/mem/2026-05-13-mlx-gemma-routing-verification.cog.md

Working directory: ~/workspaces/myrgic/cogos-worktrees/wave-c-w2/

Git instructions:
- Branch: wave-c-harness-routing
- Commit each logical change (no Co-Authored-By trailers)
- Do NOT push until PR is opened via gh

Authorization: Open PR, title "fix(harness): consult provider registry in routing", leave for operator review.

Done when: tests pass, PR open, commit history on branch shows the patch and test.
```
