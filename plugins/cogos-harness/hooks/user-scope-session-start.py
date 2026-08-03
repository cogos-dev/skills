#!/usr/bin/env python3
"""
User-scope SessionStart hook — presence.started dispatcher.

Runs from ANY cwd. It locates the cog workspace, checks whether the current
cwd is already inside it (in which case the workspace-scope hooks already
fired and we skip to avoid double-emit), then delegates to the canonical
51-presence-started.py handler under the workspace's own .cog/hooks tree.

Presence is kernel-gated, not workspace-gated (#17). When neither of the
above applies — no cog workspace, or a cog workspace with no
51-presence-started.py handler — this hook no longer just no-ops: it
probes the kernel directly (short timeout) and, if it answers, registers
this seat itself via POST /v1/sessions/register, the exact REST
counterpart of cog_register_session. Workspace info still ENRICHES a
registration when available (delegation is preferred and tried first);
its absence no longer VETOES presence.

Safety contract:
  - NEVER raises. All errors are caught and exit 0 is returned.
  - Delegation path (workspace handler) is tried first, unchanged from
    before #17.
  - The direct-registration fallback fires ONLY when the delegated
    handler was not invoked (no cog workspace, or workspace found but no
    handler) AND a short kernel probe succeeds. Both the probe and the
    registration POST use bounded, short timeouts and fail open silently.

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
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

# COGOS_KERNEL_URL takes precedence when set; COGOS_KERNEL_PORT is a
# localhost-only convenience default. Same precedence as
# seat-identity-heal.py / kernel-vitals-probe.py so all hooks resolve to
# the same kernel.
KERNEL_URL = os.environ.get("COGOS_KERNEL_URL") or \
    f"http://127.0.0.1:{os.environ.get('COGOS_KERNEL_PORT', '6931')}"
PROBE_TIMEOUT = 1.0  # short, bounded probe -- never block the hook budget
REGISTER_TIMEOUT = 1.5


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


def _parse_hook_data(stdin_data: bytes) -> dict:
    """Best-effort parse of the hook stdin JSON. Never raises; returns {}
    on any problem so callers can treat missing fields uniformly."""
    try:
        data = json.loads(stdin_data.decode("utf-8", "ignore") or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _kernel_probe_ok() -> bool:
    """Short-timeout GET /health. True only on a clean 200. Any failure
    (kernel down, timeout, DNS, refused connection) returns False -- this
    is the gate that keeps the fallback from ever blocking on a dead
    kernel or firing a noisy registration attempt against nothing."""
    try:
        with urllib.request.urlopen(f"{KERNEL_URL}/health", timeout=PROBE_TIMEOUT) as r:
            return r.status == 200
    except Exception:
        return False


def _register_direct(session_id: str, workspace: str) -> None:
    """POST /v1/sessions/register -- the exact REST counterpart of the
    cog_register_session MCP tool, same endpoint/env conventions as
    seat-identity-heal.py's _register(). Fire-and-forget: the response is
    read (to let the connection close cleanly) but never inspected --
    presence registration is best-effort by design, per #17."""
    body = {
        "session_id": session_id,
        "workspace": workspace,
        "role": os.environ.get("COGOS_SEAT_ROLE", "claude-code"),
        "hostname": socket.gethostname(),
        "extras": {"source": "plugin-startup"},
    }
    req = urllib.request.Request(
        f"{KERNEL_URL}/v1/sessions/register",
        data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=REGISTER_TIMEOUT) as r:
            r.read()
    except (urllib.error.URLError, OSError, ValueError):
        pass


def _maybe_register_direct(hook_data: dict) -> None:
    """The #17 fallback: kernel-gated, not workspace-gated. Only reached
    when the delegated workspace handler was NOT invoked. Fires the
    registration only when a session_id is available AND the short kernel
    probe succeeds -- zero registration attempts against an absent or
    unreachable kernel. Never raises."""
    try:
        session_id = str(hook_data.get("session_id") or "")
        if not session_id:
            return
        if not _kernel_probe_ok():
            return
        workspace = str(hook_data.get("cwd") or os.getcwd())
        _register_direct(session_id, workspace)
    except Exception:
        pass


def main() -> int:
    stdin_data = _read_stdin_bytes()
    cog_ws = _find_cog_workspace()

    # workspace_handles_presence: cwd is inside the cog workspace tree, so
    # the WORKSPACE's own session-start hooks (a separate mechanism from
    # this delegator) already fire for this session. handler_invoked: this
    # script itself re-exec'd the canonical 51-presence-started.py handler.
    # Either condition means presence is already someone else's job for
    # this turn; the #17 fallback below is for the remaining case: neither
    # happened.
    workspace_handles_presence = False
    handler_invoked = False

    if cog_ws is not None:
        if _cwd_is_inside_cog(cog_ws):
            # Workspace-scope hooks already handle presence for this
            # session. Skip delegation to prevent double-emit.
            workspace_handles_presence = True
        else:
            handler = cog_ws / ".cog" / "hooks" / "session-start.d" / "51-presence-started.py"
            if handler.exists():
                handler_invoked = True
                # Delegate: re-exec the canonical handler with the same stdin.
                try:
                    subprocess.run(
                        [sys.executable, str(handler)],
                        input=stdin_data,
                        capture_output=False,  # pass stdout/stderr through unchanged
                        timeout=4,
                    )
                except subprocess.TimeoutExpired:
                    sys.stderr.write("[user-scope-session-start] presence handler timed out\n")
                except Exception as e:
                    sys.stderr.write(f"[user-scope-session-start] handler exec failed: {e}\n")

    if not workspace_handles_presence and not handler_invoked:
        _maybe_register_direct(_parse_hook_data(stdin_data))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"[user-scope-session-start] unexpected error: {e}\n")
        sys.exit(0)
