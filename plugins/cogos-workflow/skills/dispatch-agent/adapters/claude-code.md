# Claude Code Adapter — Claude Code CLI

Backend adapter for `dispatch-agent` protocol. Maps abstract operations to the Claude Code CLI and the native Agent tool.

---

## Two Dispatch Modes

Claude Code supports two dispatch mechanisms. Choose based on context:

| Mode | When to use | Advantages |
|------|-------------|-----------|
| **Agent tool** (preferred) | Running inside Claude Code | Shared context, tools, permissions. No serialization overhead. Native subagent. |
| **CLI dispatch** | Cross-backend isolation, background execution, running from outside Claude Code | Full process isolation, independent timeout, concurrent execution. |

**Rule of thumb:** If you're already inside Claude Code, use the Agent tool. If you need isolation or are orchestrating from another context, use the CLI.

---

## Agent Tool Dispatch (Preferred)

When running inside Claude Code, the Agent tool spawns a subagent natively:

```
Agent tool call:
  prompt: "Your briefing here"
```

### Advantages

- **Shared context** — subagent inherits the conversation's file access and tool permissions
- **No CLI overhead** — no process spawning, stderr noise, or output parsing
- **Native tool access** — subagent can use Read, Write, Edit, Grep, Glob, Bash
- **Structured results** — output is returned as text, not raw stdout
- **No permission flags needed** — inherits the parent session's permission model

### Limitations

- Cannot select a specific model (uses the current session's model)
- Cannot run truly in the background (blocks the current turn)
- Cannot isolate from current context (shares everything)
- No resume capability (each Agent call is independent)

### When to Use CLI Instead

- You need a specific model tier (haiku for cheap analysis, opus for complex reasoning)
- You need true background execution
- You need process isolation (agent should not see or modify current conversation state)
- You're orchestrating from a non-Claude-Code environment

---

## CLI Syntax

### Non-Interactive One-Shot

```bash
claude -p "prompt" 2>/dev/null
```

The `-p` flag (or `--print`) runs Claude Code in non-interactive print mode — sends the prompt, outputs the response, and exits. No conversation UI.

### Read-Only Analysis

```bash
claude --print "prompt" 2>/dev/null
```

`--print` is the long form of `-p`. Identical behavior. Use for analysis tasks where no files should be modified.

### With Model Selection

```bash
claude -p --model opus "prompt" 2>/dev/null
```

### With Working Directory

```bash
claude -p --cwd /path/to/workspace "prompt" 2>/dev/null
```

### Full-Auto (Skip Permissions)

```bash
claude -p --dangerously-skip-permissions "prompt" 2>/dev/null
```

**Warning:** This bypasses Claude Code's permission system entirely. The agent can read, write, execute, and access the network without confirmation. Only use when:
- The task requires writes and you trust the prompt
- You've already set up the workspace safely (e.g., worktree isolation)
- The user has explicitly approved full-access

### Structured Output

```bash
claude -p --output-format json "prompt" 2>/dev/null
```

Returns a JSON object with structured response data instead of plain text. Useful for programmatic collection.

### Flag Reference

| Flag | Purpose | Notes |
|------|---------|-------|
| `-p, --print` | Non-interactive one-shot mode | Required for dispatch |
| `--model` | Select model | `haiku`, `sonnet`, `opus` |
| `--cwd` | Working directory | Absolute path |
| `--dangerously-skip-permissions` | Skip all permission prompts | Requires user approval |
| `--output-format` | Output format | `text` (default), `json` |
| `2>/dev/null` | Suppress stderr noise | Always include |

---

## Permission Mapping

| Abstract Level | CLI Approach | Notes |
|----------------|-------------|-------|
| read-only | `claude --print "prompt"` | Default mode, no write tools invoked |
| workspace-write | `claude -p --dangerously-skip-permissions "prompt"` | Needed for file edits |
| full-access | `claude -p --dangerously-skip-permissions "prompt"` | Same flag — Claude Code doesn't distinguish write from full-access at the CLI level |

### Agent Tool Permission Mapping

| Abstract Level | Approach | Notes |
|----------------|----------|-------|
| read-only | Agent prompt instructs "analyze only, do not modify files" | Relies on prompt compliance |
| workspace-write | Agent prompt with no restrictions | Inherits parent permissions |
| full-access | Agent prompt with no restrictions | Inherits parent permissions |

**Note:** The Agent tool inherits the parent session's permission model. If the parent has write access, the subagent does too. Scope control is done via prompt instructions.

---

## Complexity Tier → Model Mapping

| Tier | Model | Timeout | Notes |
|------|-------|---------|-------|
| **low** | `haiku` | 120s | Fast, cheap. Good for simple analysis, formatting, boilerplate. |
| **medium** | `sonnet` | 300s | Strong general-purpose. Handles most implementation tasks. |
| **high** | `opus` | 600s | Full reasoning capability. Architecture, novel design, complex analysis. |

### Model Selection Notes

- **Haiku (low)** — extremely fast, good at following clear instructions. Struggles with ambiguous tasks or tasks requiring deep codebase understanding. Best for: summarization, formatting, simple code generation from clear specs.
- **Sonnet (medium)** — excellent balance of speed and capability. Handles multi-file edits, test writing, and pattern-following implementations well. The default choice when unsure.
- **Opus (high)** — strongest reasoning. Use for tasks requiring deep analysis, novel solutions, or cross-codebase understanding. Slower but significantly more reliable on hard problems.

### Agent Tool Model Note

The Agent tool uses the current session's model — you cannot select a different tier. If you need a specific model, use CLI dispatch.

---

## Operations Mapping

### spawn (Agent tool)

```
Use the Agent tool with a briefing prompt.
The subagent executes and returns results in the same turn.
```

### spawn (CLI)

```bash
claude -p --model sonnet --cwd /path/to/workspace \
  --dangerously-skip-permissions \
  "Your briefing here" \
  2>/dev/null
```

For background execution:
```bash
claude -p --model sonnet --cwd /path/to/workspace \
  "prompt" 2>/dev/null &
AGENT_PID=$!
```

### status

```bash
# CLI dispatch only — check if process is running
kill -0 $AGENT_PID 2>/dev/null && echo "running" || echo "completed"
```

Agent tool dispatch: status is implicit — the tool call completes when the agent finishes.

### resume

**Not supported.** Claude Code CLI sessions are one-shot — each invocation is independent with no session continuity.

**Workarounds:**
- For CLI: include relevant context from the previous run in the new prompt
- For Agent tool: the subagent has access to the parent conversation context, so prior results are naturally available
- For Codex-style resume workflows: use the Codex backend instead

### collect

- **Agent tool:** Read the tool's return value directly
- **CLI text mode:** Read stdout from the process
- **CLI JSON mode:** Parse the JSON output with `--output-format json`

### cancel

```bash
kill $AGENT_PID        # SIGTERM
sleep 5
kill -9 $AGENT_PID    # SIGKILL if still running
```

Agent tool dispatch cannot be cancelled mid-execution.

---

## Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| No session resume | Can't continue a previous conversation | Include prior context in new prompt |
| Agent tool blocks current turn | Can't do other work while subagent runs | Use CLI for true background execution |
| Agent tool inherits model | Can't select cheaper model for subagent | Use CLI when model tier matters |
| `--dangerously-skip-permissions` is all-or-nothing | No workspace-write without full-access | Use Agent tool for scoped permissions |
| No native structured output from Agent tool | Must parse text response | Include format instructions in prompt |
| CLI has no progress indication | Can't monitor execution | Use timeout + PID check |

---

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| `claude: command not found` | Not installed | Install Claude Code CLI or use Agent tool |
| Non-zero exit, no output | Prompt too vague or permission issue | Re-prompt with clearer briefing |
| Permission denied errors | Missing `--dangerously-skip-permissions` | Add the flag (with user approval) |
| Timeout | Task too complex for tier | Escalate model tier or split task |
| JSON parse error | `--output-format json` with malformed response | Fall back to text mode, parse manually |
| Agent tool returns error | Subagent hit a tool error | Read the error, fix the issue, re-dispatch |

---

## Example Dispatch

### Low-tier analysis (Agent tool)

```
Agent tool:
  prompt: "Read /Users/me/project/src/parser.py and list all public functions
           with their signatures. Output as a markdown table."
```

### Low-tier analysis (CLI)

```bash
claude -p --model haiku --cwd /Users/me/project \
  "Read src/parser.py and list all public functions with their signatures. Output as a markdown table." \
  2>/dev/null
```

### Medium-tier implementation (CLI)

```bash
claude -p --model sonnet --cwd /Users/me/project \
  --dangerously-skip-permissions \
  "TASK: Add a parse_frontmatter() function to src/parser.py
CONTEXT: The memory system needs to index documents by YAML metadata.
FILES: Edit src/parser.py, add tests to tests/test_parser.py
EXISTING: parser.py has parse_body(). Uses pyyaml (in requirements.txt).
DONE-WHEN: Function returns dict. Handles missing/malformed YAML. Tests cover all cases. Existing tests pass.
SCOPE: Do NOT modify parse_body(). Do NOT add dependencies. Do NOT restructure the module." \
  2>/dev/null
```

### High-tier architecture (Agent tool)

```
Agent tool:
  prompt: "TASK: Design the event bus interface for the new async event system.
           CONTEXT: Replacing callback spaghetti with typed channels to prevent race conditions.
           FILES: Create src/events/bus.ts (interface only) and src/events/types.ts (channel type definitions).
           EXISTING: 12 handlers in src/handlers/, each exports register(). See src/handlers/auth.ts for the pattern.
           DONE-WHEN: Interface supports typed channels, concurrent dispatch, and handler registration. Types are exported. No implementation yet — interface only.
           SCOPE: Do NOT implement the bus. Do NOT modify existing handlers. Interface design only."
```

### Structured output collection (CLI)

```bash
RESULT=$(claude -p --model sonnet --output-format json --cwd /Users/me/project \
  "Analyze the test coverage for src/parser.py. Return a JSON object with: covered_functions (array), uncovered_functions (array), coverage_percentage (number)." \
  2>/dev/null)

echo "$RESULT" | jq '.result'
```
