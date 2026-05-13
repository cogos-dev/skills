---
name: local-review
description: Review a pull request using a local model (Ollama/vLLM) via pull-context dispatch. The model navigates the actual diff, reads relevant files, and produces a verdict grounded in real code — not in a flat summary blob. Use when you want a peer review from a local model without paying cloud inference tokens, or when you need a review before committing to a PR submission.
allowed-tools: Bash(gh:*) Bash(git:*)
---

# Local Review

Peer review a pull request or diff using a local model via the cogos kernel's tool-use endpoint, following the pull-context-dispatch pattern. The model reads files, runs grep, and navigates the repo rather than receiving a flat-prompt summary.

## Why this exists

Flat-prompt review (paste diff + write summary into request) fails at scale: the model pattern-matches on the summary rather than reading code, producing hallucinated concerns with no file:line citation. The fix is not a larger model — it is giving the model the tools to look at the actual code.

This skill wires the local model into the kernel's `/v1/chat/completions` tool-use loop with `read_file`, `grep`, and `git_show` tools so it can navigate the PR like a human reviewer would.

## Invocation

```
/local-review <PR-number>
/local-review <base>..<head>
/local-review <file>:<line-range>
```

## Procedure

### 1. Resolve the target

```bash
# For a PR number:
gh pr view <PR-number> --repo <owner>/<repo> --json number,headRefName,baseRefName,changedFiles,body

# For a branch range:
git diff --stat <base>..<head>

# Get the list of changed files and their ranges:
gh pr diff <PR-number> --repo <owner>/<repo> --name-only
```

Store: `PR_NUMBER`, `BASE_REF`, `HEAD_REF`, `CHANGED_FILES` (list of paths), `PR_BODY`.

### 2. Construct the pull-context dispatch envelope

The dispatch envelope has four fields only. Do NOT paste diff content or file excerpts into the prompt.

**Identity:**
```
You are a senior Go/Python/TypeScript reviewer (match language to repo) focused on:
- Correctness and edge cases
- Race conditions and concurrency safety
- Test coverage adequacy
- API surface changes
- Obvious logic errors
```

**Directive:**
```
Review PR #<PR_NUMBER> (<BASE_REF>..<HEAD_REF>).

Changed files:
<CHANGED_FILES — one path per line>

PR description:
<PR_BODY — first 300 chars if long>

For each concern you raise, cite the specific file and line number from your tool reads.
Do not raise concerns you cannot verify against the code.

Return verdict in this format:
---
Verdict: APPROVE | REQUEST_CHANGES | COMMENT
Blockers: <list, empty if none>
Concerns: <list with file:line citations>
What looks good: <2-3 observations>
---
```

**Tool access:**

Dispatch with these tools available via the kernel's tool-use loop:
- `read_file(path, start_line, end_line)` — read a file range
- `grep(pattern, path_glob)` — find patterns
- `git_show(ref:path)` — read a file at a specific commit
- `list_dir(path)` — list directory contents

**Substrate pointers:**
- Workspace root: `<WORKSPACE_ROOT>`
- Changed files: `<CHANGED_FILES>`
- Base commit: `<BASE_REF>`
- Head commit: `<HEAD_REF>`

### 3. Dispatch to local model via kernel endpoint

```bash
curl -s -X POST http://localhost:${COGOS_PORT:-8765}/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "local",
    "messages": [
      {"role": "system", "content": "<IDENTITY>"},
      {"role": "user", "content": "<DIRECTIVE>"}
    ],
    "tools": [
      {
        "type": "function",
        "function": {
          "name": "read_file",
          "description": "Read a range of lines from a file",
          "parameters": {
            "type": "object",
            "properties": {
              "path": {"type": "string"},
              "start_line": {"type": "integer"},
              "end_line": {"type": "integer"}
            },
            "required": ["path"]
          }
        }
      },
      {
        "type": "function",
        "function": {
          "name": "grep",
          "description": "Search for a pattern across files",
          "parameters": {
            "type": "object",
            "properties": {
              "pattern": {"type": "string"},
              "path_glob": {"type": "string"}
            },
            "required": ["pattern"]
          }
        }
      },
      {
        "type": "function",
        "function": {
          "name": "git_show",
          "description": "Read a file at a specific git ref",
          "parameters": {
            "type": "object",
            "properties": {
              "ref": {"type": "string"},
              "path": {"type": "string"}
            },
            "required": ["ref", "path"]
          }
        }
      }
    ],
    "stream": false
  }'
```

Run the tool-use loop: execute each tool call the model requests, return results, repeat until the model produces its verdict without a tool call.

### 4. Execute tool calls

For each tool call the model makes:

**read_file:**
```bash
sed -n "${start_line},${end_line}p" <path>
# Or full file if no range:
cat <path>
```

**grep:**
```bash
grep -rn "<pattern>" <path_glob>
```

**git_show:**
```bash
git show <ref>:<path>
```

Return tool results as `{"role": "tool", "tool_call_id": "<id>", "content": "<output>"}` in the next request.

### 5. Post the verdict

When the model returns a message with no tool calls, extract the verdict block and post as a PR comment:

```bash
gh pr comment <PR-number> --repo <owner>/<repo> --body "$(cat <<'EOF'
**Local model review** (via cogos local-review skill)

<VERDICT_BLOCK>
EOF
)"
```

Do NOT post as an official `gh pr review` approval/rejection. Comment-only by default; let the human decide on the official verdict.

### 6. Report

Print to stdout:
- Verdict
- Number of tool calls made by the model
- Whether any concern was cited without a file:line (flag as ungrounded if so)
- PR comment URL

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--model` | `local` | Override the model alias (passed to `/v1/chat/completions`) |
| `--no-comment` | false | Print verdict to stdout only; do not post PR comment |
| `--repo` | inferred from `git remote` | Target repo for gh commands |
| `--port` | `$COGOS_PORT` or `8765` | Kernel port |

## Acceptance criteria (from issue #85)

- A `local-review <PR#>` invocation runs end-to-end against a local provider via `/v1/chat/completions`.
- The dispatched agent has tool access to `read_file`, `grep`, `git_show` -- verified by inspecting tool-call traces.
- Any concern raised cites a specific file:line verifiable against the code (not a hallucination from the diff summary).
- Worked example: see Episodes section after first production run.

## Related

- `pull-context-dispatch` skill -- the pattern this skill operationalizes for PR review
- `cogos-workflow/dispatch-agent` skill -- general agent dispatch; this skill is the PR-review specialization
- `myrgic/cogos` issue #85 -- origin of this skill
- `myrgic/cogos` issue #107 -- concurrent Ollama requests; local-review dispatches one request at a time so this is safe
- `myrgic/cogos` kernel endpoint `/v1/chat/completions` with `model: local` -- the inference path

## Episodes

<!-- Add production run examples here after first use. Format:
### YYYY-MM-DD — PR #N
Command: `/local-review N`
Tool calls: N (read_file x N, grep x N)
Verdict: APPROVE/REQUEST_CHANGES/COMMENT
Ungrounded concerns: 0
Notes: ...
-->

## Learnings

- Flat-prompt review on PR #83 (myrgic/cogos) produced 3 REQUEST_CHANGES items, all hallucinations grounded in summary pattern-matching with no file:line citation. This skill was created to fix that failure mode.
- Local model (gemma4:e4b via Ollama) was the victim, but the failure mode applies equally to larger models receiving flat diffs.
