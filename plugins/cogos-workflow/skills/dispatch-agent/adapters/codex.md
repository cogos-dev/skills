# Codex Adapter — OpenAI Codex CLI

Backend adapter for `dispatch-agent` protocol. Maps abstract operations to the Codex CLI.

---

## CLI Syntax

### Basic Invocation

```bash
codex exec -m MODEL --sandbox MODE --full-auto --skip-git-repo-check -C DIR "prompt" 2>/dev/null
```

**Required flags:**
- `--skip-git-repo-check` — always include, prevents git safety checks that block automation
- `--full-auto` — required for non-interactive dispatch (no confirmation prompts)
- `2>/dev/null` — always append to suppress thinking tokens on stderr

### Resume

```bash
echo "prompt" | codex exec --skip-git-repo-check resume --last 2>/dev/null
```

**Resume rules:**
- All flags go between `exec` and `resume`
- The resumed session inherits the original model, sandbox, and reasoning effort
- Don't re-specify config flags unless explicitly requested
- Pipe the new prompt via stdin

### Flag Reference

| Flag | Purpose | Values |
|------|---------|--------|
| `-m, --model` | Model selection | See tier mapping below |
| `--sandbox` | Permission level | `read-only`, `workspace-write`, `danger-full-access` |
| `--full-auto` | Non-interactive mode | (flag, no value) |
| `--skip-git-repo-check` | Skip git safety checks | (flag, no value) |
| `-C, --cd` | Working directory | Absolute path |
| `--config` | Runtime config | `model_reasoning_effort="high"` etc. |

---

## Permission Mapping

| Abstract Level | Codex Flag | Notes |
|----------------|-----------|-------|
| read-only | `--sandbox read-only` | Agent can only read files, output goes to stdout |
| workspace-write | `--sandbox workspace-write` | Agent can edit files within the working directory |
| full-access | `--sandbox danger-full-access` | Network, system commands, everything — **requires user approval** |

### Sandbox Selection Guide

| Task Type | Sandbox | File Output Method |
|-----------|---------|-------------------|
| Research, analysis, design docs | `read-only` | You write from stdout |
| Code review, explanation | `read-only` | No file needed |
| Edit existing code / config | `workspace-write` | Codex writes directly |
| Create multiple interdependent files | `workspace-write` | Codex writes directly |
| Network access (git clone, API calls) | `danger-full-access` | Codex writes directly |

---

## Complexity Tier → Model Mapping

| Tier | Model | Reasoning Effort | Timeout | Notes |
|------|-------|-----------------|---------|-------|
| **low** | `gpt-5.3-codex-spark` | medium | 120s | Fast, cheap. Good for mechanical transforms. |
| **medium** | `gpt-5.3-codex` | high | 300s | Strong general-purpose. Handles most tasks. |
| **high** | `gpt-5.4` | xhigh | 600s | Full capability. Novel design, complex reasoning. |

### Model Selection Notes

- **Spark (low)** — optimized for speed. Struggles with existing codebases — works best on greenfield or clearly-scoped mechanical tasks. If spark fails, escalate to medium, don't retry at same tier.
- **Codex (medium)** — reliable workhorse. Handles templated implementations, test writing, module-level edits. Can't do cross-module reasoning well — if the task requires understanding distant code, escalate to high.
- **GPT-5.4 (high)** — full reasoning capability. Use for architecture decisions, security-sensitive code, novel algorithms, and tasks requiring understanding of the whole codebase. Slower and more expensive, but significantly more reliable on complex work.

### Reasoning Effort

Control reasoning depth independently of model:

| Effort | When to use |
|--------|-------------|
| `low` | Trivial tasks, formatting |
| `medium` | Standard implementation |
| `high` | Complex logic, careful edits |
| `xhigh` | Architecture, safety-critical |

Set via: `--config model_reasoning_effort="high"`

---

## Operations Mapping

### spawn

```bash
codex exec \
  -m "gpt-5.3-codex" \
  --sandbox workspace-write \
  --full-auto \
  --skip-git-repo-check \
  -C /path/to/workspace \
  "Your briefing here" \
  2>/dev/null
```

For background execution, append `&` and capture PID:
```bash
codex exec -m "gpt-5.3-codex" --sandbox read-only --full-auto \
  --skip-git-repo-check -C /path/to/workspace \
  "prompt" 2>/dev/null &
AGENT_PID=$!
```

### status

```bash
# Check if process is still running
kill -0 $AGENT_PID 2>/dev/null && echo "running" || echo "completed"
```

No native status API — track by PID.

### resume

```bash
echo "Follow-up instructions here" | codex exec --skip-git-repo-check resume --last 2>/dev/null
```

Codex supports native session resume. The `--last` flag reconnects to the most recent session. This is one of Codex's strongest features — prior context is fully preserved.

### collect

Read stdout from the foreground process, or the captured output file for background runs. Strip any thinking token artifacts that leaked through stderr suppression.

### cancel

```bash
kill $AGENT_PID        # SIGTERM
sleep 5
kill -9 $AGENT_PID    # SIGKILL if still running
```

---

## File Output Pattern (Read-Only + External Write)

The preferred pattern for single-document output tasks:

1. **Instruct Codex to produce content to stdout:**
   ```
   "Produce your output as a single markdown document. Start with --- frontmatter
   and end with the document. Print ONLY the document content to stdout, no
   commentary before or after."
   ```

2. **Run in read-only sandbox:**
   ```bash
   codex exec -m "gpt-5.4" --sandbox read-only --full-auto \
     --skip-git-repo-check -C /path/to/workspace \
     "your prompt here" 2>/dev/null
   ```

3. **Capture stdout** — this is the document content.

4. **Write the file yourself** using the Write tool.

5. **Report to user** with: file path, line count, section summary.

### Why Read-Only + External Write

- **Safety**: Codex can't accidentally modify code or config files
- **Determinism**: File path, frontmatter, and format are controlled by the orchestrator
- **Auditability**: Content is reviewed before writing
- **Reliability**: No "file not written" failures from sandbox permission errors

---

## Critical Evaluation

Codex is a colleague, not an authority. Its output requires critical evaluation.

### Guidelines

- **Trust your own knowledge** when confident. If Codex produces something you know is incorrect, don't accept it.
- **Research disagreements** using documentation or web search before accepting Codex claims.
- **Remember knowledge cutoffs** — Codex may not know about recent releases, APIs, or changes.
- **Don't defer blindly** — evaluate suggestions critically, especially regarding:
  - Model names and capabilities
  - Recent library versions or API changes
  - Best practices that may have evolved

### When Codex is Wrong

1. State the disagreement clearly
2. Provide evidence (your knowledge, web search, docs)
3. Optionally resume to discuss: identify yourself so Codex knows it's a peer AI discussion
4. Frame disagreements as discussions — either AI could be wrong
5. Let the user decide if there's genuine ambiguity

---

## Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Spark fails on existing code | Can't reason about existing patterns, produces non-idiomatic code | Use medium tier for anything touching existing files |
| Medium can't do cross-module reasoning | Misses dependencies between distant files | Use high tier or split into per-file tasks |
| No streaming output in full-auto | Can't monitor progress during execution | Use timeout + PID check |
| Stderr noise from thinking tokens | Output pollution if 2>/dev/null omitted | Always append 2>/dev/null |
| Resume is last-session only | Can't resume arbitrary past sessions | Track session boundaries yourself |
| No structured output format | Stdout is freeform text | Include format instructions in prompt |

---

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| `codex: command not found` | Not installed | `npm install -g @openai/codex` or suggest alternative backend |
| Non-zero exit, no output | Prompt too vague or model confusion | Re-prompt with clearer briefing |
| Non-zero exit, error in output | Build failure, syntax error | Parse error, fix in-place or re-dispatch |
| Timeout | Task too complex for tier | Escalate tier or split task |
| `--sandbox` permission denied | Task needs higher sandbox level | Escalate sandbox (with user approval) |
| Garbled output | Thinking tokens leaked | Ensure 2>/dev/null is present |

---

## Example Dispatch

### Low-tier mechanical task

```bash
codex exec \
  -m "gpt-5.3-codex-spark" \
  --sandbox read-only \
  --full-auto \
  --skip-git-repo-check \
  -C /Users/me/project \
  "List all exported functions in src/utils.ts. Output as a markdown table with columns: function name, parameters, return type." \
  2>/dev/null
```

### Medium-tier implementation

```bash
codex exec \
  -m "gpt-5.3-codex" \
  --sandbox workspace-write \
  --full-auto \
  --skip-git-repo-check \
  -C /Users/me/project \
  "TASK: Add a parse_frontmatter() function to src/parser.py
CONTEXT: The memory system needs to index documents by YAML metadata.
FILES: Edit src/parser.py, add tests to tests/test_parser.py
EXISTING: parser.py has parse_body(). Uses pyyaml (in requirements.txt).
DONE-WHEN: Function returns dict. Handles missing/malformed YAML. Tests cover all cases. Existing tests pass.
SCOPE: Do NOT modify parse_body(). Do NOT add dependencies. Do NOT restructure the module." \
  2>/dev/null
```

### High-tier architecture task

```bash
codex exec \
  -m "gpt-5.4" \
  --config model_reasoning_effort="xhigh" \
  --sandbox workspace-write \
  --full-auto \
  --skip-git-repo-check \
  -C /Users/me/project \
  "TASK: Refactor the event system from callback-based to an async event bus with typed channels.
CONTEXT: Current callback spaghetti causes race conditions in concurrent handlers.
FILES: src/events/bus.ts (new), src/events/types.ts (new), src/handlers/*.ts (migrate all), src/index.ts (update imports)
EXISTING: 12 handlers in src/handlers/, each exports a register() function. Tests in tests/events/.
DONE-WHEN: All handlers use typed channels. No callback registration remains. All tests pass. New bus supports concurrent dispatch without races.
SCOPE: Do NOT change handler business logic. Do NOT modify the API layer. Do NOT add new dependencies." \
  2>/dev/null
```
