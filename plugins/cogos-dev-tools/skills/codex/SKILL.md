---
name: codex
description: Use when the user asks to run Codex CLI (codex exec, codex resume) or references OpenAI Codex for code analysis, refactoring, or automated editing
version: 1.0.0
author: myrgic
tags: [codex, cli-tools, cross-model, automation]
canonical_source: "~/workspaces/cog/.claude/skills/codex/SKILL.md"
projection_note: >
  This is the public marketplace projection. Content is unchanged from the
  canonical source — the skill has no operator-specific material to strip.
  Update canonical first; project here after.
---

# Codex Skill Guide

## Resolving the codex Binary

**Scope: macOS only.** On Linux and Windows, only the `command -v codex` / Homebrew checks apply; the editor-bundled fallbacks are macOS-specific binary layouts.

Before step 1 of "Running a Task," ensure codex is resolvable. If `command -v codex` succeeds *and* `codex --version` actually runs, proceed. Otherwise (npm global cleared during housekeeping, dangling symlink from cleaned `node_modules`, fresh machine, different editor with a bundled binary), walk common fallback locations and fix PATH for the session — don't abandon the skill.

### Fallback order

Tried in this order; first candidate whose binary actually runs `--version` wins:

1. **PATH-visible** — must pass both `command -v` and `--version`
2. **Codex.app desktop bundle** — `/Applications/Codex.app/Contents/Resources/codex`
3. **Per-user app install** — `~/Applications/Codex.app/Contents/Resources/codex`
4. **VSCode extension** — `~/.vscode/extensions/openai.chatgpt-*/bin/*/codex`
5. **VSCode Insiders extension** — `~/.vscode-insiders/extensions/openai.chatgpt-*/bin/*/codex`
6. **Cursor extension** — `~/.cursor/extensions/openai.chatgpt-*/bin/*/codex`
7. **Homebrew (Apple Silicon)** — `/opt/homebrew/bin/codex`
8. **Homebrew / legacy system** — `/usr/local/bin/codex`
9. **nvm-managed npm install** — `~/.nvm/versions/node/*/bin/codex`

Editor-bundle paths use `bin/*/codex` instead of `bin/macos-aarch64/codex` to cover both Apple Silicon (`macos-aarch64`) and Intel Macs (`macos-x86_64`). When multiple versioned extension directories exist, the glob picks whichever expands first lexicographically — that's fine for "any working candidate," but if a specific version is required, resolve it manually.

### Shell snippet (run once at the start of a Codex session)

```bash
# Resolve codex binary for this session. Safe under set -e / set -u.
# Handles: missing PATH entry, dangling symlinks, multiple fallback locations.
resolve_codex() {
  # Short-circuit if already usable (not just present — actually executable).
  if command -v codex >/dev/null 2>&1 && codex --version >/dev/null 2>&1; then
    return 0
  fi

  local candidate
  for candidate in \
    "/Applications/Codex.app/Contents/Resources/codex" \
    "$HOME/Applications/Codex.app/Contents/Resources/codex" \
    "$HOME"/.vscode/extensions/openai.chatgpt-*/bin/*/codex \
    "$HOME"/.vscode-insiders/extensions/openai.chatgpt-*/bin/*/codex \
    "$HOME"/.cursor/extensions/openai.chatgpt-*/bin/*/codex \
    "/opt/homebrew/bin/codex" \
    "/usr/local/bin/codex" \
    "$HOME"/.nvm/versions/node/*/bin/codex
  do
    [ -x "$candidate" ] || continue
    "$candidate" --version >/dev/null 2>&1 || continue
    export PATH="$(dirname "$candidate"):$PATH"
    hash -r 2>/dev/null || true
    return 0
  done

  echo "codex not installed. Run: npm install -g @openai/codex" >&2
  return 1
}

resolve_codex || return 1 2>/dev/null || exit 1
codex --version
```

After the snippet runs, all subsequent `codex exec` invocations in the skill work unchanged.

Key behaviors of this resolver:
- **`--version` gate per candidate** catches dangling symlinks (exists + executable bit set, but target gone). `[ -x ]` alone would not.
- **Single flat loop with `continue`** avoids nested-loop `break 2` cross-scope semantics and unquoted-glob word-splitting traps that bite under `set -u` in zsh (where unmatched globs raise `nomatch` by default).
- **`hash -r`** clears the shell's cached command lookup after PATH mutation so `codex` resolves to the new location without reopening the shell.
- **`return 1 2>/dev/null || exit 1`** is safe whether the snippet is sourced (`return`) or executed as a script (`exit`).

### If no binary is found anywhere

Surface the install command: `npm install -g @openai/codex` (or point to https://github.com/openai/codex). **Do not** silently fail or recommend `OPENAI_API_KEY` workarounds — most users pay via a ChatGPT subscription and expect the OAuth path.

## Running a Task
0. Ensure `codex --version` succeeds. If not, run the resolver snippet from "Resolving the codex Binary" above. Do this once per session, before any `codex exec` call.
1. Ask the user which model to run (`gpt-5.4`, `gpt-5.3-codex-spark`, or `gpt-5.3-codex`) AND which reasoning effort to use (`xhigh`, `high`, `medium`, or `low`) in a single prompt with two questions.
2. Select the sandbox mode required for the task; default to `--sandbox read-only` unless edits or network access are necessary.
3. Assemble the command with the appropriate options:
   - `-m, --model <MODEL>`
   - `--config model_reasoning_effort="<xhigh|high|medium|low>"`
   - `--sandbox <read-only|workspace-write|danger-full-access>`
   - `--full-auto`
   - `-C, --cd <DIR>`
   - `--skip-git-repo-check`
   - `"your prompt here"` (as final positional argument)
3. Always use --skip-git-repo-check.
4. When continuing a previous session, use `codex exec --skip-git-repo-check resume --last` via stdin. When resuming don't use any configuration flags unless explicitly requested by the user e.g. if a specific model or reasoning effort is requested when resuming a session. Resume syntax: `echo "your prompt here" | codex exec --skip-git-repo-check resume --last 2>/dev/null`. All flags have to be inserted between exec and resume.
5. **IMPORTANT**: By default, append `2>/dev/null` to all `codex exec` commands to suppress thinking tokens (stderr). Only show stderr if the user explicitly requests to see thinking tokens or if debugging is needed.
6. Run the command, capture stdout/stderr (filtered as appropriate), and summarize the outcome for the user.
7. **After Codex completes**, inform the user they can resume this Codex session at any time by saying "codex resume" or asking to continue with additional analysis or changes.

### Quick Reference
| Use case | Sandbox mode | Key flags |
| --- | --- | --- |
| Read-only review or analysis | `read-only` | `--sandbox read-only 2>/dev/null` |
| Apply local edits | `workspace-write` | `--sandbox workspace-write --full-auto 2>/dev/null` |
| Permit network or broad access | `danger-full-access` | `--sandbox danger-full-access --full-auto 2>/dev/null` |
| Resume recent session | Inherited from original | `echo "prompt" \| codex exec --skip-git-repo-check resume --last 2>/dev/null` (no flags allowed) |
| Run from another directory | Match task needs | `-C <DIR>` plus other flags `2>/dev/null` |

## Following Up
- After every `codex` command, confirm next steps, collect clarifications, or decide whether to resume with `codex exec resume --last`.
- When resuming, pipe the new prompt via stdin: `echo "new prompt" | codex exec resume --last 2>/dev/null`. The resumed session automatically uses the same model, reasoning effort, and sandbox mode from the original session.
- Restate the chosen model, reasoning effort, and sandbox mode when proposing follow-up actions.

## Critical Evaluation of Codex Output

Codex is powered by OpenAI models with their own knowledge cutoffs and limitations. Treat Codex as a **colleague, not an authority**.

### Guidelines
- **Trust your own knowledge** when confident. If Codex claims something you know is incorrect, push back directly.
- **Research disagreements** using web search or documentation before accepting Codex's claims. Share findings with Codex via resume if needed.
- **Remember knowledge cutoffs** - Codex may not know about recent releases, APIs, or changes that occurred after its training data.
- **Don't defer blindly** - Codex can be wrong. Evaluate its suggestions critically, especially regarding:
  - Model names and capabilities
  - Recent library versions or API changes
  - Best practices that may have evolved

### When Codex is Wrong
1. State your disagreement clearly to the user
2. Provide evidence (your own knowledge, web search, docs)
3. Optionally resume the Codex session to discuss the disagreement. **Identify yourself as the calling agent** so Codex knows it's a peer AI discussion. Use your actual model name instead of a hardcoded one:
   ```bash
   echo "This is <agent> (<your current model name>) following up. I disagree with [X] because [evidence]. What's your take on this?" | codex exec --skip-git-repo-check resume --last 2>/dev/null
   ```
4. Frame disagreements as discussions, not corrections - either AI could be wrong
5. Let the user decide how to proceed if there's genuine ambiguity

## File Output Pattern (Read-Only Agent + Deterministic Write)

**Default pattern for research, analysis, and design tasks:**

Codex agents run in `read-only` sandbox for safety. The skill handles file
output deterministically after the agent completes.

### Flow

1. **Assemble the prompt** with an explicit output instruction:
   ```
   "Produce your output as a single markdown document. Start with --- frontmatter
   and end with the document. Print ONLY the document content to stdout, no
   commentary before or after."
   ```

2. **Run Codex in read-only mode:**
   ```bash
   codex exec -m "gpt-5.4" --sandbox read-only --full-auto \
     --skip-git-repo-check -C /path/to/workspace \
     "your prompt here" 2>/dev/null
   ```

3. **Capture stdout** — this is the document content.

4. **Write the file** yourself using your own write tool to the specified path.

5. **Report to user** with: file path, line count, section summary.

### Why Read-Only + External Write

- **Safety**: Codex can't accidentally modify code or config files
- **Determinism**: File path, frontmatter, and format are controlled by the calling agent
- **Auditability**: Content is reviewed before writing
- **Reliability**: No "file not written" failures from sandbox permission errors

### When to Use workspace-write Instead

Only use `workspace-write` for tasks where Codex needs to **edit existing files**
(e.g., applying a patch, creating multiple interdependent files, running build
commands). For single-document output, always prefer read-only + external write.

### Sandbox Selection Guide

| Task type | Sandbox | File output |
|-----------|---------|-------------|
| Research, analysis, design docs | `read-only` | Calling agent writes from stdout |
| Code review, explain | `read-only` | No file needed |
| Edit existing code / config | `workspace-write` | Codex writes directly |
| Create multiple interdependent files | `workspace-write` | Codex writes directly |
| Network access (git clone, API) | `danger-full-access` | Codex writes directly |

## Error Handling
- Stop and report failures whenever `codex --version` or a `codex exec` command exits non-zero; request direction before retrying.
- Before you use high-impact flags (`--full-auto`, `--sandbox danger-full-access`, `--skip-git-repo-check`) ask the user for permission unless it was already given.
- When output includes warnings or partial results, summarize them and ask how to adjust.
