#!/usr/bin/env python3
"""Memory-index janitor trigger — Stop hook.

Portable port of a hook promoted from an operator-local seat, 2026-08-08:
the pilot must not be steered into inline memory maintenance mid-turn.
Instead this hook fires deterministically at end-of-turn; when a project's
MEMORY.md crosses the size threshold it blocks the stop ONCE with a nod
request — the pilot invokes the `memory-janitor` skill (this plugin),
which owns the dispatch/check/repair loop. Guards below keep the block
rare and non-looping.

Portability: every path is derived from the CURRENT project, never
hardcoded to one machine or one operator. A project with no auto-memory
(no MEMORY.md under its own `~/.claude/projects/<sanitized-cwd>/memory/`)
never sees this hook fire at all — see the early-exit below.

This hook also self-locates its own plugin root (`Path(__file__).resolve()
.parent.parent`, since this file lives at `<plugin>/hooks/memory-janitor.py`)
and embeds the ABSOLUTE resolved checker path, directive path, target
MEMORY.md path, project dir, and the live trigger/target/floor numbers
directly in the block reason. The `memory-janitor` skill's primary flow
reads all of that back out of the reason instead of re-deriving any of it
(and instead of depending on `${CLAUDE_PLUGIN_ROOT}`, which is a
hooks.json/MCP-config substitution token, not something that expands in a
shell command or a subagent's own environment).

Env overrides (testing / non-default layouts): COG_JANITOR_FILE,
COG_JANITOR_TRIGGER, COG_JANITOR_TARGET, COG_JANITOR_FLOOR,
COG_JANITOR_STATE_DIR. A malformed *_TRIGGER/_TARGET/_FLOOR value degrades
to its default with a stderr warning rather than raising — this hook must
never crash or block a turn on a typo'd env var.
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

COOLDOWN_S = 6 * 3600


def _cwd_from_stdin() -> str | None:
    """Best-effort drain of the hook's stdin JSON payload, returning its
    "cwd" key if present. Never blocks: a tty (someone running this by
    hand with nothing piped in) short-circuits to None instead of waiting
    on input that isn't coming. Draining stdin is also just hook hygiene —
    Claude Code always pipes a payload in for a real Stop event."""
    if sys.stdin.isatty():
        return None
    try:
        raw = sys.stdin.read()
    except Exception:
        return None
    try:
        data = json.loads(raw) if raw.strip() else {}
        cwd = data.get("cwd") if isinstance(data, dict) else None
        return cwd if isinstance(cwd, str) and cwd else None
    except Exception:
        return None


def _resolve_cwd(stdin_cwd: str | None) -> str:
    """cwd resolution order: hook stdin JSON "cwd" -> $CLAUDE_PROJECT_DIR ->
    os.getcwd(). Returns the raw (unsanitized) cwd — callers sanitize it
    themselves via `_sanitize`, and it is also what's handed to `check.py`
    as `--project-dir` so the checker rederives the identical path."""
    return stdin_cwd or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _sanitize(cwd: str) -> str:
    """Sanitized the same way Claude Code itself names a project's
    `~/.claude/projects/<sanitized>` directory, so this hook lands on the
    exact auto-memory tree the session is already using."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def _env_int(name: str, default: int) -> int:
    """Read an integer env override, degrading to `default` with a stderr
    warning on anything malformed. This hook must stay fail-open: a typo'd
    COG_JANITOR_TRIGGER should never turn into an import-time traceback on
    every single Stop event."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return int(raw)
    except ValueError:
        print(f"<memory-janitor> warning: {name}={raw!r} is not an integer; using default {default}", file=sys.stderr)
        return default


def main() -> int:
    trigger = _env_int("COG_JANITOR_TRIGGER", 18800)
    target = _env_int("COG_JANITOR_TARGET", 16500)
    floor = _env_int("COG_JANITOR_FLOOR", 15500)

    cwd = _resolve_cwd(_cwd_from_stdin())
    sanitized = _sanitize(cwd)
    projects_dir = Path.home() / ".claude" / "projects" / sanitized

    mem = Path(os.environ.get("COG_JANITOR_FILE") or str(projects_dir / "memory" / "MEMORY.md"))
    if not mem.exists():
        return 0  # no auto-memory for this project: the janitor never fires

    state_dir = Path(os.environ.get("COG_JANITOR_STATE_DIR") or str(projects_dir / "janitor"))
    pending = state_dir / "pending"
    baseline = state_dir / "baseline"
    # Fallback pending-marker location. If state_dir itself is unwritable
    # (permissions, a read-only mount, ...) the primary `pending` marker
    # above can never be written, so the cooldown dedupe below has nothing
    # to read back and every single over-threshold Stop event re-blocks
    # with no dedupe -- a session-wrecking loop, not just a missed
    # optimization. The system temp dir is a second, unrelated filesystem;
    # if EITHER write succeeds, the cooldown check below honors it. Only
    # if BOTH locations fail does the per-turn re-block resume.
    pending_fallback = Path(tempfile.gettempdir()) / f"cogos-janitor-{sanitized}.pending"

    size = mem.stat().st_size

    if size <= trigger:
        # Healthy. Clear any resolved pending marker (both locations) so
        # the next crossing fires cleanly.
        if pending.exists():
            pending.unlink(missing_ok=True)
        if pending_fallback.exists():
            pending_fallback.unlink(missing_ok=True)
        return 0

    # Over threshold: only request the nod once per cooldown window, so a
    # dispatched-but-slow (or failed) janitor doesn't cause a block loop.
    # Honor whichever pending marker exists -- primary or fallback.
    for p in (pending, pending_fallback):
        if p.exists() and (time.time() - p.stat().st_mtime) < COOLDOWN_S:
            return 0

    # Validate the same floor < target <= trigger invariant check.py
    # enforces, BEFORE arming -- a misconfigured trio must never turn into
    # a block the checker then refuses to grade (CHECKER-ERROR, exit 2),
    # looping the turn forever on a config problem the pilot can't fix
    # in-band. Fail open: warn to stderr, skip the block, touch no state.
    # Same env-resolved numbers read above, so this can never disagree
    # with what check.py would see given the same environment.
    if not (floor < target <= trigger):
        print(
            f"<memory-janitor> warning: invalid thresholds floor={floor} target={target} "
            f"trigger={trigger} (require floor < target <= trigger); skipping block",
            file=sys.stderr,
        )
        return 0

    plugin_root = Path(__file__).resolve().parent.parent
    checker_path = plugin_root / "skills" / "memory-janitor" / "check.py"
    directive_path = plugin_root / "skills" / "memory-janitor" / "directive.md"

    # Build the reason first — this is the only thing that MUST reach the
    # pilot. Everything from here down (state dir, baseline snapshot,
    # pending marker) is best-effort bookkeeping: a failure in any of it
    # is appended to `reason` as a warning, never allowed to cost the
    # block itself — the print() at the bottom always runs.
    reason = (
        f"<memory-janitor> MEMORY.md is {size} bytes "
        f"(trigger {trigger}, target {target}, floor {floor}). "
        f"Invoke the memory-janitor skill (cogos-harness plugin) and follow "
        f"it exactly; do not compact inline.\n"
        f"checker: {checker_path}\n"
        f"directive: {directive_path}\n"
        f"target file: {mem}\n"
        f"project dir: {cwd}\n"
        f"numbers: trigger={trigger} target={target} floor={floor}"
    )

    warnings: list[str] = []
    try:
        state_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        warnings.append(f"state dir create failed: {e}")

    # Never shutil.copy2 INTO a stale directory left at the baseline path —
    # that silently "succeeds" by copying mem inside it, and check.py then
    # dies on IsADirectoryError. Remove it explicitly first, or skip the
    # snapshot and say so.
    if baseline.is_dir():
        try:
            shutil.rmtree(baseline)
        except Exception as e:
            warnings.append(f"baseline path is a stale directory and could not be removed: {e}")

    if not baseline.is_dir():
        try:
            shutil.copy2(mem, baseline)  # checker's pre-state; taken at trigger time, in code
        except Exception as e:
            warnings.append(f"baseline snapshot failed: {e}")

    try:
        pending.write_text(f"{int(time.time())} size={size}\n")
    except Exception as e:
        warnings.append(f"pending marker write failed: {e}")
        try:
            pending_fallback.write_text(f"{int(time.time())} size={size}\n")
        except Exception as e2:
            warnings.append(f"pending fallback marker write failed too: {e2}")

    if warnings:
        reason += "\nWARNING: " + "; ".join(warnings)

    print(json.dumps({"decision": "block", "reason": reason}))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
