---
name: dispatch-agent
description: Spawn, manage, and collect results from external coding agents. Abstracts over backend-specific CLIs (Codex, Claude Code, OpenCode) with a unified dispatch protocol for background inference, lifecycle management, and result verification. Use when delegating work to external agents or orchestrating multi-agent workflows.
allowed-tools: Bash(codex:*) Bash(claude:*) Bash(opencode:*)
---

# Dispatch Agent Protocol

Unified interface for spawning, managing, and collecting results from external coding agents. This protocol is backend-agnostic — all CLI-specific knowledge lives in adapter files loaded on demand.

**Adapters:** `adapters/codex.md` | `adapters/claude-code.md` | `adapters/opencode.md`

Load the appropriate adapter after selecting a backend. If no adapter exists for the chosen backend, the protocol still applies — just translate the abstract operations to the backend's native CLI.

---

## 1. Core Operations

### spawn(backend, prompt, config)

Launch an external agent to perform a task.

**Parameters:**
- `backend` — which CLI to use (codex, claude-code, opencode)
- `prompt` — the briefing (see Section 3)
- `config` — backend-specific options:
  - `model` — model tier or specific model name
  - `sandbox` — permission level (read-only, workspace-write, full-access)
  - `cwd` — working directory
  - `timeout` — max runtime in seconds (default: 300)
  - `background` — run asynchronously (default: false)
  - `output_file` — path to capture structured output

**Returns:** `agent_id` (use for status/collect/cancel)

**Flow:**
1. Validate backend is installed (see Section 2)
2. Construct the briefing prompt (see Section 3)
3. Determine sandbox level (see Section 4)
4. Translate to backend-native CLI via adapter
5. Launch and record agent_id with timestamp

### status(agent_id)

Check current state of a dispatched agent.

**States:**
- `running` — process still active
- `completed` — exited 0, output available
- `failed` — exited non-zero, stderr available
- `timeout` — exceeded configured timeout
- `cancelled` — stopped via cancel()

### resume(agent_id, prompt)

Continue a previous agent session with additional context or instructions.

**Notes:**
- Not all backends support resume (check adapter)
- The resumed session inherits the original config (model, sandbox, cwd)
- Pass new instructions only — don't repeat the original briefing

### collect(agent_id)

Retrieve and verify results from a completed agent.

**Flow:**
1. Confirm status is `completed`
2. Read stdout/output file
3. Run acceptance criteria checks (see Section 6)
4. Return structured result: `{ output, files_changed, tests_passed, summary }`

### cancel(agent_id)

Terminate a running agent.

**Flow:**
1. Send SIGTERM to process
2. Wait 5s for graceful shutdown
3. SIGKILL if still running
4. Record cancellation reason

---

## 2. Backend Selection

### Availability Check

Before dispatching, verify the backend is installed:

| Backend | Check command |
|---------|--------------|
| codex | `which codex` |
| claude-code | `which claude` |
| opencode | `which opencode` |

If the requested backend is unavailable, report to the user and suggest alternatives.

### Selection Heuristic

When the user doesn't specify a backend, select based on this priority:

1. **User preference** — if previously stated, honor it
2. **Task fit** — match task requirements to backend strengths:
   - Codex: best for code generation, refactoring, file editing (strong sandbox model)
   - Claude Code: best for analysis, architecture, multi-file reasoning (native context sharing)
   - OpenCode: experimental, use only if explicitly requested
3. **Availability** — use what's installed

### When Running Inside Claude Code

If this skill is invoked from within a Claude Code session, prefer the **Agent tool** (subagent spawning) over CLI dispatch for claude-code tasks. The Agent tool shares context, tools, and permissions natively — no serialization overhead.

Use CLI dispatch for:
- Cross-backend calls (dispatching to Codex from Claude Code)
- Isolation requirements (agent must not see current context)
- Background execution needs

---

## 3. Prompt Construction — The Briefing Pattern

Every dispatch prompt MUST include all six elements. Incomplete briefings produce unreliable results.

### The Six Elements

```
1. WHAT TO BUILD
   Specific deliverable. One sentence, concrete noun.
   ✓ "Create a Python function that parses YAML frontmatter from markdown files"
   ✗ "Work on the parser"

2. WHY IT MATTERS
   One sentence of context so the agent can make judgment calls.
   ✓ "This is used by the memory system to index documents by metadata"
   ✗ (omitted — agent guesses wrong about edge cases)

3. WHERE TO WORK
   Exact file paths. Absolute, not relative.
   ✓ "Edit /Users/me/project/src/parser.py, add tests to /Users/me/project/tests/test_parser.py"
   ✗ "In the parser module"

4. WHAT ALREADY EXISTS
   Constraints the agent must respect.
   ✓ "parser.py already has a `parse_body()` function — add `parse_frontmatter()` alongside it.
       Uses the `pyyaml` library already in requirements.txt."
   ✗ (omitted — agent rewrites the whole file or picks a different library)

5. ACCEPTANCE CRITERIA
   How to verify the work is done correctly.
   ✓ "Function returns a dict. Handles missing frontmatter (returns empty dict).
       All existing tests still pass. New test covers: valid YAML, missing frontmatter, malformed YAML."
   ✗ "Make sure it works"

6. WHAT NOT TO DO
   Explicit scope boundaries to prevent drift.
   ✓ "Do NOT modify parse_body(). Do NOT add new dependencies. Do NOT restructure the module."
   ✗ (omitted — agent helpfully refactors half the codebase)
```

### Briefing Template

```
<briefing>
TASK: {one-sentence deliverable}
CONTEXT: {why this matters}
FILES: {exact paths to read/write}
EXISTING: {constraints and conventions}
DONE-WHEN: {acceptance criteria}
SCOPE: Do NOT {boundaries}
</briefing>
```

### Anti-Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| "Based on your findings, implement X" | Pushes synthesis to agent | Do the synthesis yourself, dispatch concrete work |
| Vague file paths | Agent searches and guesses wrong | Provide absolute paths |
| Dumping the entire plan | Agent loses focus, cherry-picks | One task per dispatch |
| "Be creative with the approach" | Unpredictable output | Specify the approach |
| "Fix the tests" | Which tests? What's broken? | Name the test file, describe the failure |
| Embedding context in code comments | Agent may ignore comments | Put context in the prompt directly |

---

## 4. Sandbox / Permission Model

### Abstract Permission Levels

| Level | Allows | Default for |
|-------|--------|-------------|
| **read-only** | Read files, analyze code, produce output to stdout | Analysis, review, research |
| **workspace-write** | Read + write files within the working directory | Code edits, file creation |
| **full-access** | Read + write + network + system commands | Package install, git operations, API calls |

### Rules

1. **Default to read-only** unless the task requires writes
2. **Escalate to workspace-write** only when the agent needs to create or modify files
3. **Never use full-access** without explicit user approval — ask first
4. **Use read-only + external write** for single-file output tasks:
   - Agent produces content to stdout in read-only mode
   - You write the file yourself using the Write tool
   - Safer and more auditable than letting the agent write

### Permission Mapping

Each adapter maps these abstract levels to backend-specific flags. See the appropriate adapter file for translation.

---

## 5. Lifecycle Management

### Foreground vs Background Decision

| Condition | Mode | Rationale |
|-----------|------|-----------|
| Task < 30 seconds expected | Foreground | User waits for immediate result |
| Task > 30 seconds expected | Background | Don't block the conversation |
| User explicitly requests | As requested | Honor user preference |
| Multi-agent parallel dispatch | Background | All agents run concurrently |
| Interactive/conversational task | Foreground | Need to relay output live |

### Background Agent Tracking

When running agents in the background, maintain a tracking record:

```
agent_id: {unique identifier}
backend: {codex|claude-code|opencode}
model: {specific model used}
task: {one-line summary}
cwd: {working directory}
started: {timestamp}
timeout: {seconds}
status: {running|completed|failed|timeout|cancelled}
pid: {process ID for cancel}
```

### Timeout Handling

- Default timeout: 300 seconds (5 minutes)
- For complex tasks: extend to 600s (10 min) with user acknowledgment
- On timeout: cancel the agent, report partial results if any, suggest splitting the task
- Codex spark model: 120s timeout (it's fast or it's stuck)

### Output Monitoring

For background agents, check status by:
1. Process existence (`kill -0 $PID`)
2. Output file growth (if output_file configured)
3. Backend-specific status commands (see adapter)

---

## 6. Result Collection & Verification

### Collection Flow

```
1. Confirm agent status == completed
2. Read stdout / output file
3. Parse output (strip thinking tokens, extract content)
4. Check acceptance criteria:
   a. Do specified files exist?
   b. Do tests pass? (if applicable)
   c. Does output match expected format?
   d. Are scope boundaries respected? (no unexpected changes)
5. Summarize for user:
   - What was delivered
   - Files created/modified (with paths)
   - Test results
   - Any warnings or deviations
```

### Failure Triage

When an agent fails or produces unsatisfactory results:

| Failure Type | Symptoms | Action |
|--------------|----------|--------|
| **Build error** | Non-zero exit, error in stderr | Read error, fix in-place or re-dispatch with fix |
| **Wrong approach** | Output doesn't match intent | Re-prompt with clearer briefing, more constraints |
| **Blocked** | Agent asks questions, can't proceed | Answer the question via resume, or handle yourself |
| **Too large** | Timeout, partial output, confused reasoning | Split into smaller tasks, dispatch sequentially |
| **Model mismatch** | Correct approach but poor execution | Escalate to higher model tier |
| **Sandbox too restrictive** | Permission denied errors | Escalate sandbox level (with user approval) |

### Quality Gate

Before reporting results to the user:
- [ ] Output is non-empty and coherent
- [ ] Files mentioned in acceptance criteria exist
- [ ] No unintended file modifications (check git diff if applicable)
- [ ] Output doesn't contain thinking tokens or debug artifacts
- [ ] Agent didn't hallucinate file paths or function names

---

## 7. Complexity Tier Mapping

Assess task complexity before selecting a model. The tier determines which model the adapter selects.

| Tier | Criteria | Examples |
|------|----------|---------|
| **low** | ≤2 files, ≤50 lines changed, mechanical transformation | Rename variable, add type hints, format code, simple boilerplate |
| **medium** | 2–4 files, ≤200 lines, follows existing patterns | Implement function from spec, add tests, create module from template |
| **high** | 3+ files, novel design, cross-module reasoning, safety-critical | Architecture changes, new abstractions, security-sensitive code, complex refactors |

### Tier → Model Mapping

Each adapter defines its own model mapping. The abstract protocol only specifies the tier.

| Tier | Codex | Claude Code | OpenCode |
|------|-------|-------------|----------|
| low | See `adapters/codex.md` | See `adapters/claude-code.md` | See `adapters/opencode.md` |
| medium | See `adapters/codex.md` | See `adapters/claude-code.md` | See `adapters/opencode.md` |
| high | See `adapters/codex.md` | See `adapters/claude-code.md` | See `adapters/opencode.md` |

### Tier Selection Rules

1. **Start low, escalate if needed** — cheaper and faster models are preferred
2. **Mechanical tasks are always low** — even if they touch many files (e.g., rename across codebase)
3. **Novel design is always high** — even if it's a small change (e.g., new algorithm)
4. **When in doubt, use medium** — the middle tier handles most tasks well
5. **User can override** — explicit model/tier requests always win

---

## 8. Multi-Agent Coordination

### Parallel Dispatch

Launch multiple agents when tasks are independent:

```
dispatch A: "Write the parser" → codex, workspace-write
dispatch B: "Write the tests" → codex, read-only (output to stdout)
dispatch C: "Write the docs"  → claude-code, read-only

wait_all(A, B, C)
collect(A) → verify parser exists
collect(B) → write test file, run tests
collect(C) → write docs file
```

### Worktree Isolation

When multiple agents need to write to the same repository concurrently:

1. Create git worktrees for each agent:
   ```
   git worktree add /tmp/agent-A-work -b agent-A
   git worktree add /tmp/agent-B-work -b agent-B
   ```
2. Dispatch each agent to its own worktree directory
3. After collection, merge results:
   ```
   git merge agent-A agent-B
   ```
4. Clean up worktrees:
   ```
   git worktree remove /tmp/agent-A-work
   git worktree remove /tmp/agent-B-work
   ```

### Sequential Chaining

When output of one agent feeds the next:

```
result_A = dispatch("Analyze the codebase structure") → collect
result_B = dispatch("Based on this structure: {result_A.summary}, implement X") → collect
result_C = dispatch("Write tests for: {result_B.files_changed}") → collect
```

**Rules for chaining:**
- Never pass raw stdout between agents — summarize and extract the relevant parts
- Each agent gets a fresh briefing with all six elements
- Don't chain more than 3 agents deep — complexity compounds errors
- Verify intermediate results before chaining to the next agent

### Coordination Patterns

| Pattern | When to use | Notes |
|---------|-------------|-------|
| **Fan-out** | Independent tasks | Fastest, no ordering constraints |
| **Pipeline** | Sequential dependencies | Each step waits for the previous |
| **Fan-out → merge** | Independent work on same codebase | Requires worktree isolation |
| **Supervisor** | Complex multi-step workflow | You (the orchestrator) verify each step |

### Conflict Resolution

When parallel agents produce conflicting changes:
1. Collect all results before merging
2. Identify conflicts (git merge will flag them)
3. Resolve by choosing the agent with the most relevant context
4. If ambiguous, ask the user
5. Never auto-resolve conflicts in safety-critical code

---

## 9. Error Handling

### Pre-Dispatch Errors

| Error | Handling |
|-------|----------|
| Backend not installed | Report, suggest alternatives |
| Invalid model for backend | Fall back to default model for tier |
| Working directory doesn't exist | Report, ask user to confirm path |
| Prompt empty or too short | Warn user, suggest adding briefing elements |

### Runtime Errors

| Error | Handling |
|-------|----------|
| Non-zero exit code | Read stderr, classify failure, triage per Section 6 |
| Timeout | Cancel, report partial results, suggest task splitting |
| Process killed externally | Record as cancelled, check for partial output |
| Disk full / resource exhaustion | Report system issue, defer task |

### Post-Collection Errors

| Error | Handling |
|-------|----------|
| Output contains only errors | Parse error message, re-dispatch with fix or escalate |
| Files not created as expected | Check if agent wrote to wrong path, retry with explicit paths |
| Tests fail after agent edit | Read failures, dispatch fix or handle in-place |
| Unexpected files modified | Review with git diff, revert unintended changes, re-dispatch |

---

## 10. Quick Reference

### Dispatch Checklist

Before every dispatch:
- [ ] Backend selected and installed
- [ ] Complexity tier assessed
- [ ] Briefing has all 6 elements
- [ ] Sandbox level appropriate (default: read-only)
- [ ] Timeout set (default: 300s)
- [ ] Foreground/background decision made
- [ ] Acceptance criteria are verifiable

### Common Workflows

**Single task, simple:**
```
assess tier → select backend → build briefing → spawn → wait → collect → report
```

**Research then implement:**
```
spawn(read-only, "analyze X") → collect → synthesize → spawn(workspace-write, "implement Y based on analysis") → collect → verify → report
```

**Parallel implementation:**
```
create worktrees → fan-out spawns → wait_all → collect all → merge → verify → clean up → report
```

**Iterative refinement:**
```
spawn → collect → verify → [fail?] → resume/re-dispatch with feedback → collect → verify → [pass?] → report
```
