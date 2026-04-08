# OpenCode Adapter — OpenCode CLI

Backend adapter for `dispatch-agent` protocol. Maps abstract operations to the OpenCode CLI.

> **Status: Experimental / Provisional**
>
> OpenCode is a newer entrant with a rapidly evolving CLI. This adapter covers the known interface as of early 2026. Expect breaking changes. Verify commands against `opencode --help` before relying on them in automation.

---

## Overview

OpenCode is an open-source terminal-based AI coding assistant that supports multiple LLM providers (Anthropic, OpenAI, Google, AWS Bedrock, local models). Its primary advantage is provider flexibility — you can dispatch to whatever model you have API keys for.

**Best used when:**
- You need a specific provider not covered by Codex or Claude Code
- You want to use local models (Ollama, etc.)
- The user explicitly requests OpenCode

**Avoid when:**
- Task reliability is critical (prefer Codex or Claude Code for production workflows)
- You need session resume (not supported)
- You need structured output (freeform text only)

---

## Availability Check

```bash
which opencode
```

If not installed, OpenCode can be installed via:
```bash
# Go install
go install github.com/opencode-ai/opencode@latest

# Or from source
git clone https://github.com/opencode-ai/opencode && cd opencode && go install .
```

---

## CLI Syntax

### Basic Invocation

```bash
opencode "prompt"
```

OpenCode's CLI is simpler than Codex or Claude Code — the primary interface is the interactive TUI. Non-interactive dispatch is more limited.

### Non-Interactive Mode

```bash
echo "prompt" | opencode
```

Or, if the CLI supports a direct prompt flag (check `opencode --help` for current syntax):
```bash
opencode --prompt "prompt"
```

### Working Directory

Run from the target directory:
```bash
cd /path/to/workspace && opencode "prompt"
```

Or if `--cwd` is supported:
```bash
opencode --cwd /path/to/workspace "prompt"
```

---

## Provider Configuration

OpenCode reads provider config from its configuration file (typically `~/.opencode/config.yaml` or environment variables).

### Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Anthropic provider |
| `OPENAI_API_KEY` | OpenAI provider |
| `GOOGLE_API_KEY` | Google provider |
| `OPENCODE_MODEL` | Default model override |

### Selecting a Provider/Model

```bash
OPENCODE_MODEL="claude-sonnet-4-20250514" opencode "prompt"
```

Or via config file — consult OpenCode documentation for current syntax.

---

## Permission Mapping

| Abstract Level | OpenCode Approach | Notes |
|----------------|-------------------|-------|
| read-only | Default behavior | OpenCode asks before writing |
| workspace-write | Auto-approve mode (if available) | Check CLI flags for auto-accept |
| full-access | Auto-approve + environment access | Requires explicit configuration |

**Note:** OpenCode's permission model is evolving. Check current documentation for the exact flags to control auto-approval of file writes and command execution.

---

## Complexity Tier → Model Mapping

Since OpenCode supports multiple providers, the model mapping depends on which provider is configured:

### Anthropic Provider

| Tier | Model | Notes |
|------|-------|-------|
| low | `claude-haiku-4-20250414` | Fast, cheap |
| medium | `claude-sonnet-4-20250514` | General purpose |
| high | `claude-opus-4-20250514` | Full reasoning |

### OpenAI Provider

| Tier | Model | Notes |
|------|-------|-------|
| low | `gpt-4o-mini` | Fast, cheap |
| medium | `gpt-4o` | General purpose |
| high | `o1` | Full reasoning |

### Google Provider

| Tier | Model | Notes |
|------|-------|-------|
| low | `gemini-2.0-flash` | Fast, cheap |
| medium | `gemini-2.5-pro` | General purpose |
| high | `gemini-2.5-pro` | Same (no higher tier currently) |

### Local Models (Ollama)

| Tier | Model | Notes |
|------|-------|-------|
| low | Provider default | Limited capability |
| medium | Provider default | Limited capability |
| high | Not recommended | Use a cloud provider for high-tier tasks |

**Default behavior:** If no tier-specific model selection is available via CLI flags, use the provider's default model and note the limitation.

---

## Operations Mapping

### spawn

```bash
cd /path/to/workspace && opencode "Your briefing here" 2>/dev/null
```

Or for background:
```bash
cd /path/to/workspace && opencode "prompt" 2>/dev/null &
AGENT_PID=$!
```

### status

```bash
kill -0 $AGENT_PID 2>/dev/null && echo "running" || echo "completed"
```

No native status API.

### resume

**Not supported.** Each OpenCode invocation is independent. Include relevant prior context in the new prompt.

### collect

Read stdout from the process. OpenCode's output format may include TUI artifacts in non-interactive mode — filter accordingly.

### cancel

```bash
kill $AGENT_PID
sleep 5
kill -9 $AGENT_PID 2>/dev/null
```

---

## Known Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| Immature non-interactive mode | CLI dispatch may not work cleanly | Test with current version before relying on it |
| No session resume | Can't continue previous conversations | Include context in new prompts |
| No structured output | Freeform text only | Include format instructions in prompt |
| TUI artifacts in output | Stdout may contain escape codes | Filter with `sed` or pipe through `cat -v` |
| Provider-dependent behavior | Same prompt, different results per provider | Test with your configured provider |
| Rapidly evolving CLI | Flags and syntax may change between versions | Check `opencode --help` before automation |
| No sandbox model | Permission control is limited | Use worktree isolation for safety |

---

## Error Handling

| Error | Cause | Action |
|-------|-------|--------|
| `opencode: command not found` | Not installed | `go install github.com/opencode-ai/opencode@latest` |
| API key errors | Provider not configured | Set the appropriate environment variable |
| Model not found | Invalid model name for provider | Check provider's available models |
| TUI initialization errors | Terminal environment issues in non-interactive mode | Try piping input via stdin instead |
| Timeout | Task too complex | Escalate to a more capable provider/model |

---

## Example Dispatch

### Basic analysis

```bash
cd /Users/me/project && opencode "List all exported functions in src/utils.ts with their type signatures." 2>/dev/null
```

### With specific provider

```bash
OPENCODE_MODEL="claude-sonnet-4-20250514" \
  cd /Users/me/project && opencode "TASK: Review src/parser.py for potential bugs.
CONTEXT: This module handles untrusted YAML input.
DONE-WHEN: List of issues with severity ratings and suggested fixes." 2>/dev/null
```

---

## When to Use OpenCode vs Other Backends

| Scenario | Recommendation |
|----------|---------------|
| Need Anthropic models | Prefer Claude Code (native integration) |
| Need OpenAI models | Prefer Codex (native integration) |
| Need Google models | OpenCode is a good choice |
| Need local models | OpenCode is the only option |
| Need reliability | Prefer Codex or Claude Code |
| Need provider flexibility | OpenCode shines here |
| User explicitly requests it | Use OpenCode |
