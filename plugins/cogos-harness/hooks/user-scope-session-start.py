#!/usr/bin/env python3
"""
User-scope SessionStart hook — presence.started dispatcher.

Runs from ANY cwd. It locates the cog workspace, checks whether the current
cwd is already inside it (in which case the workspace-scope hooks already
fired and we skip to avoid double-emit), then delegates to the canonical
51-presence-started.py handler under the workspace's own .cog/hooks tree.

Safety contract:
  - NEVER raises. All errors are caught and exit 0 is returned.
  - cog workspace not found -> silent no-op.
  - Already inside cog workspace -> skip (workspace hooks handle it).
  - Handler not found -> silent no-op.

Workspace location (in priority order):
  1. COGOS_WORKSPACE env var
  2. $HOME/workspaces/cog

Worktree awareness: a cwd that is a git worktree under the cog workspace
is considered "inside the cog workspace" and skips to avoid double-fire
from workspace hooks.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def _find_cog_workspace() -> Path | None:
    """Return the cog workspace root if it exists and has .cog/."""
    candidates = []
    env = os.environ.get("COGOS_WORKSPACE")
    if env:
        candidates.append(Path(env))
    candidates.append(Path.home() / "workspaces" / "cog")

    for c in candidates:
        try:
            if (c / ".cog").is_dir():
                return c.resolve()
        except OSError:
            continue
    return None


def _cwd_is_inside_cog(cog_ws: Path) -> bool:
    """
    Return True if the current working directory lives inside the cog
    workspace tree (direct or via a git worktree).

    Covers:
      - cwd == cog_ws
      - cwd is a subdirectory of cog_ws
      - cwd is a git worktree whose common gitdir is cog_ws/.git
    """
    cwd = Path.cwd().resolve()

    # Direct containment (including the workspace root itself).
    try:
        cwd.relative_to(cog_ws)
        return True
    except ValueError:
        pass

    # Worktree check: ask git for the common dir.
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, timeout=2, cwd=str(cwd),
        )
        if result.returncode == 0:
            common_dir = Path(result.stdout.strip()).resolve()
            # Common dir for a worktree is the main repo's .git directory.
            if common_dir == (cog_ws / ".git").resolve():
                return True
    except Exception:
        pass

    return False


def _read_stdin_bytes() -> bytes:
    """Read stdin safely, returning b'{}' on error."""
    try:
        return sys.stdin.buffer.read()
    except Exception:
        return b"{}"


def main() -> int:
    cog_ws = _find_cog_workspace()
    if cog_ws is None:
        # No cog workspace found — graceful no-op.
        return 0

    if _cwd_is_inside_cog(cog_ws):
        # Workspace-scope hooks already handle presence for this session.
        # Skip to prevent double-emit.
        return 0

    handler = cog_ws / ".cog" / "hooks" / "session-start.d" / "51-presence-started.py"
    if not handler.exists():
        return 0

    # Delegate: re-exec the canonical handler with the same stdin.
    stdin_data = _read_stdin_bytes()
    try:
        subprocess.run(
            [sys.executable, str(handler)],
            input=stdin_data,
            capture_output=False,  # pass stdout/stderr through unchanged
            timeout=4,
        )
        return 0  # always exit 0 regardless of handler result
    except subprocess.TimeoutExpired:
        sys.stderr.write("[user-scope-session-start] presence handler timed out\n")
        return 0
    except Exception as e:
        sys.stderr.write(f"[user-scope-session-start] handler exec failed: {e}\n")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"[user-scope-session-start] unexpected error: {e}\n")
        sys.exit(0)
