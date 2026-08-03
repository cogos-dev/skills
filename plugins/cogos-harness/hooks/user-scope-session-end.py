#!/usr/bin/env python3
"""
User-scope SessionEnd hook — presence.ended dispatcher.

Companion to user-scope-session-start.py. Same cwd-detection and
skip-if-inside-cog-workspace logic. Delegates to the canonical
51-presence-ended.py handler under the workspace's own .cog/hooks tree.

Safety contract: never raises, always exits 0.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def _find_cog_workspace() -> Path | None:
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
    cwd = Path.cwd().resolve()

    try:
        cwd.relative_to(cog_ws)
        return True
    except ValueError:
        pass

    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, timeout=2, cwd=str(cwd),
        )
        if result.returncode == 0:
            common_dir = Path(result.stdout.strip()).resolve()
            if common_dir == (cog_ws / ".git").resolve():
                return True
    except Exception:
        pass

    return False


def _read_stdin_bytes() -> bytes:
    try:
        return sys.stdin.buffer.read()
    except Exception:
        return b"{}"


def main() -> int:
    cog_ws = _find_cog_workspace()
    if cog_ws is None:
        return 0

    if _cwd_is_inside_cog(cog_ws):
        return 0

    handler = cog_ws / ".cog" / "hooks" / "session-end.d" / "51-presence-ended.py"
    if not handler.exists():
        return 0

    stdin_data = _read_stdin_bytes()
    try:
        subprocess.run(
            [sys.executable, str(handler)],
            input=stdin_data,
            capture_output=False,
            timeout=4,
        )
        return 0
    except subprocess.TimeoutExpired:
        sys.stderr.write("[user-scope-session-end] presence handler timed out\n")
        return 0
    except Exception as e:
        sys.stderr.write(f"[user-scope-session-end] handler exec failed: {e}\n")
        return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"[user-scope-session-end] unexpected error: {e}\n")
        sys.exit(0)
