# cogos-harness

The first versioned slice of a CogOS node's Claude Code membrane: the
session-lifecycle hooks, ambient kernel-vitals proprioception, and the
`cogos-kernel` MCP server, packaged as one installable plugin instead of
hand-copied files under `~/.claude/hooks/`.

This is a deliberately small first cut. It ships the portion of the
membrane that is (a) already generic across any CogOS node and (b) safe to
publish. See "What's excluded" below for the rest.

## What ships

**MCP server** (`.mcp.json`): `cogos-kernel`, an HTTP connection to a
locally-running CogOS kernel at `http://127.0.0.1:6931/mcp`. If no kernel
is running, the server simply has nothing to answer — Claude Code surfaces
that as an unavailable tool, not an error. The port is not currently
env-parameterized in the MCP config (Claude Code plugin `.mcp.json` doesn't
support arbitrary `${ENV_VAR}` substitution in server URLs, only the
`CLAUDE_PLUGIN_*`/`CLAUDE_PROJECT_DIR` trio); if your kernel runs on a
different port, edit the installed plugin's `.mcp.json` or register a
second `cogos-kernel` entry in your own `.mcp.json` — see "Known
limitation" below.

**Hooks** (`hooks/hooks.json`), all Python 3, all fail-open (never block a
turn, never raise past their own `main()`, degrade to silence on any
missing dependency):

| Hook | Event | What it does |
|---|---|---|
| `user-scope-session-start.py` | `SessionStart` (`*`) | Locates a cog workspace (via `COGOS_WORKSPACE` or `~/workspaces/cog`) and delegates to its `session-start.d` presence handler, if one exists. **Presence is kernel-gated, not workspace-gated**: when no workspace handler ran (no workspace found, or one found with no handler), this hook falls back to registering the seat itself — a short `/health` probe against the kernel, then `POST /v1/sessions/register` (session_id from the hook's stdin, workspace=cwd, role=`$COGOS_SEAT_ROLE` or `claude-code`, hostname, `extras.source=plugin-startup`) — the exact REST counterpart of `cog_register_session`. No-ops entirely when the kernel is unreachable too. |
| `seat-identity-heal.py` | `SessionStart` (`*`) | Re-asserts a durable session role against the kernel if `~/.cog/status/seat-identity.json` exists. No-ops with no identity file. |
| `compaction-handoff.py` | `SessionStart` (`compact`) | Re-injects operator-verbatim messages, in-flight background task state, and uncommitted-repo status after compaction — a bypass path around what the compaction summary flattens. |
| `user-scope-session-end.py` | `SessionEnd` (`*`) | Presence-ended counterpart to the session-start hook: delegates to the workspace's `session-end.d` handler when one ran for this session, otherwise falls back to `POST /v1/sessions/{id}/end` directly (same kernel probe gate, same fail-open contract) — the REST counterpart of `cog_end_session`. Cleanly ends a seat that the session-start fallback registered. |
| `user-scope-proprioception.py` | `UserPromptSubmit` (`*`) | Emits a one-line `<cogos_proprioception>` block outside a cog workspace: branch, local wall-clock + day-phase, session-elapsed time, last-turn model, context-window usage, and (via the detached probe below) kernel health. When that cached vitals read already shows the kernel reachable, also `POST`s a session heartbeat (`/v1/sessions/{id}/heartbeat`, the REST counterpart of `cog_heartbeat_session`) — no extra network probe, at most once per turn, silently skipped whenever the kernel is absent. |
| `kernel-vitals-probe.py` | fired detached by the proprioception hook | Off-the-critical-path collector: kernel `/health`, error/anomaly counts from the kernel log, process uptime, release/PR status via `gh`. Writes a cache the proprioception hook reads; never called synchronously. |

All three lifecycle hooks resolve the kernel the same way: `COGOS_KERNEL_URL`
wins when set, else `http://127.0.0.1:${COGOS_KERNEL_PORT:-6931}` — the same
precedence as `seat-identity-heal.py` and `kernel-vitals-probe.py`, so a
non-default kernel location only needs to be set once.

**Skills** (`skills/`): `btw` (fork the session into a parenthetical aside
via `cog_fork_session`), `consolidate` (reflective session-arc capture:
settled / heating-up / at-risk distinctions), `handoff` (transactional
session handoff over the kernel's event bus). `pull-context-dispatch` is
**not** duplicated here — it already ships in this marketplace's
`cogos-workflow` package; install that alongside this plugin if you want
it too.

## What's excluded, and why

- **`dispatch-model-probe.py`** — audited as a "by-reference companion" to
  the proprioception hook, but its only call site in that hook has been
  commented out since before this plugin existed (a dead code path, kept
  only for easy revival). It also reads the local Claude Code OAuth
  credentials file directly and makes live calls to
  `api.anthropic.com` with them — appropriate for a single operator's own
  incident-response tooling, not for default behavior in a plugin anyone
  installs. Excluded outright rather than ported.
- **Plan-usage tracking** (the `use S24%·W18%` style segment some
  proprioception hooks carry) — depends on a statusline side-channel cache
  that isn't part of this plugin and isn't itself portable membrane;
  dropped rather than partially ported. The context-window (`ctx N%`)
  segment, which is self-contained, is kept.
- **Book/reading-surface sync** — the source `kernel-vitals-probe.py` this
  was cut from also read a specific private repo's comment ledger to
  surface an unrelated personal writing project's review queue. That
  entire code path (repo constant, thread-state diffing, the `book ✎N`
  segment) is removed from the shipped version, not just disabled.
- **Everything else the membrane audit classified as machine-literal,
  project-specific, or operator-personal** — `hermes-ops`-style
  machine-named triggers, family/book-project references, hardcoded
  `/Volumes/...` paths, personal usernames in example payloads — is out of
  scope for this plugin by construction; none of it was in the source
  files this plugin was built from.

## What stays outside this plugin (user scope, not plugin scope)

Deliberately not shipped, and not something a future version of this
plugin should absorb without a separate decision:

- **`CLAUDE.md` principles** — how you want an agent to operate is
  identity, not mechanism. A plugin can offer hooks and tools; it
  shouldn't write your operating philosophy for you.
- **The memory corpus** — durable knowledge, feedback files, and any
  cogdoc/memory tree are per-operator content, not plugin payload.
- **`settings.json` risk-posture flags** — `defaultMode`, permission
  allow-lists, `skipDangerousModePermissionPrompt` and siblings are
  operator risk decisions. This plugin's hooks are all read-only or
  fail-open by design and don't need any of these flags to work; it never
  writes them.
- **The default-agent / model-tiering setting** — a per-operator choice
  about which model handles what, orthogonal to the membrane.
- **Node bootstrap** (installing the `cogos` binary itself, scaffolding a
  workspace, starting the kernel) — this plugin *configures* a client
  against an already-running kernel; it does not install or start one. See
  the kernel repo's own install docs for that step.

## Requirements

- `python3` on `PATH`
- Optional, degrades cleanly if absent: a running CogOS kernel at
  `127.0.0.1:6931`, a `~/workspaces/cog` (or `$COGOS_WORKSPACE`) workspace,
  `gh` authenticated against the kernel repo, `launchctl` (macOS) if the
  kernel runs as a launchd service

## Path/env conventions

- `COGOS_WORKSPACE` — the active CogOS workspace; falls back to
  `~/workspaces/cog`
- `MYRGIC_REPOS_ROOT` — local checkouts of myrgic-org repos; falls back to
  `~/workspaces/myrgic`
- `COGOS_KERNEL_PORT` — kernel HTTP port on `127.0.0.1`, read by the vitals
  probe, `seat-identity-heal.py`, the three session-lifecycle hooks
  (`user-scope-session-start.py`, `user-scope-session-end.py`,
  `user-scope-proprioception.py`'s heartbeat), and the bundled `.mcp.json`
  (via `${COGOS_KERNEL_PORT:-6931}`); falls back to `6931`
- `COGOS_KERNEL_URL` — full kernel base URL, for a kernel that isn't on
  `127.0.0.1`; takes precedence over `COGOS_KERNEL_PORT` everywhere above
  except the bundled `.mcp.json` (which only resolves `COGOS_KERNEL_PORT`,
  so a non-default host still needs a hand-edited or project-level
  `.mcp.json` override); falls back to `http://127.0.0.1:6931`
- `COGOS_KERNEL_REPO` — `owner/repo` for the kernel release/PR checks in
  the vitals probe; falls back to `myrgic/cogos`
- `COGOS_SEAT_ROLE` — the `role` field the session-start fallback
  registers with when it fires (no cog workspace, or a workspace with no
  presence handler); falls back to `claude-code`

## Dogfood plan

Not part of this PR: tapping `myrgic/plugins` and installing
`cogos-harness@plugins` in a real seat, and confirming the installed copy
serves the hooks in place of the hand-wired `~/.claude/hooks/` files it
was cut from. That's the natural next step once this lands, and is
tracked as follow-up work rather than bundled into this change.
