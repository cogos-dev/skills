#!/usr/bin/env python3
"""
User-scope SessionEnd hook — presence.ended dispatcher.

Companion to user-scope-session-start.py. Same cwd-detection and
skip-if-inside-cog-workspace logic. Delegates to the canonical
51-presence-ended.py handler under the workspace's own .cog/hooks tree.

Presence is kernel-gated, not workspace-gated (#17), mirroring the
session-start fallback: when the delegated workspace handler was NOT
invoked, this hook POSTs /v1/sessions/{id}/end directly -- the REST
counterpart of cog_end_session -- gated on a short kernel probe, same as
the start-side fallback, so a seat registered by that fallback also gets
cleanly ended by this one.

Safety contract: never raises, always exits 0.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# Same env precedence as user-scope-session-start.py / seat-identity-heal.py.
KERNEL_URL = os.environ.get("COGOS_KERNEL_URL") or \
    f"http://127.0.0.1:{os.environ.get('COGOS_KERNEL_PORT', '6931')}"
PROBE_TIMEOUT = 1.0
END_TIMEOUT = 1.5


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


def _parse_hook_data(stdin_data: bytes) -> dict:
    try:
        data = json.loads(stdin_data.decode("utf-8", "ignore") or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _kernel_probe_ok() -> bool:
    """Short-timeout GET /health. Same contract as the start-side probe."""
    try:
        with urllib.request.urlopen(f"{KERNEL_URL}/health", timeout=PROBE_TIMEOUT) as r:
            return r.status == 200
    except Exception:
        return False


def _end_direct(session_id: str) -> None:
    """POST /v1/sessions/{id}/end -- the REST counterpart of
    cog_end_session. Fire-and-forget, fail-open on any error (unknown
    session -> 404, already-ended -> 409, kernel down -> connection error
    -- all silently ignored, matching the rest of this hook's contract)."""
    req = urllib.request.Request(
        f"{KERNEL_URL}/v1/sessions/{urllib.parse.quote(session_id, safe='')}/end",
        data=json.dumps({"reason": "plugin-shutdown"}).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=END_TIMEOUT) as r:
            r.read()
    except (urllib.error.URLError, OSError, ValueError):
        pass


def _maybe_end_direct(hook_data: dict) -> None:
    """The #17 fallback: only reached when the delegated workspace handler
    was NOT invoked. Fires only when a session_id is available AND the
    short kernel probe succeeds. Never raises."""
    try:
        session_id = str(hook_data.get("session_id") or "")
        if not session_id:
            return
        if not _kernel_probe_ok():
            return
        _end_direct(session_id)
    except Exception:
        pass


def main() -> int:
    stdin_data = _read_stdin_bytes()
    cog_ws = _find_cog_workspace()

    workspace_handles_presence = False
    handler_invoked = False

    if cog_ws is not None:
        if _cwd_is_inside_cog(cog_ws):
            workspace_handles_presence = True
        else:
            handler = cog_ws / ".cog" / "hooks" / "session-end.d" / "51-presence-ended.py"
            if handler.exists():
                handler_invoked = True
                try:
                    subprocess.run(
                        [sys.executable, str(handler)],
                        input=stdin_data,
                        capture_output=False,
                        timeout=4,
                    )
                except subprocess.TimeoutExpired:
                    sys.stderr.write("[user-scope-session-end] presence handler timed out\n")
                except Exception as e:
                    sys.stderr.write(f"[user-scope-session-end] handler exec failed: {e}\n")

    if not workspace_handles_presence and not handler_invoked:
        _maybe_end_direct(_parse_hook_data(stdin_data))

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"[user-scope-session-end] unexpected error: {e}\n")
        sys.exit(0)
