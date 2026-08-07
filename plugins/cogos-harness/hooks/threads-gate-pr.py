#!/usr/bin/env python3
"""threads-gate-pr.py — PreToolUse (Bash) enforcement tier for the threads
registry. SCAFFOLDED BUT DISABLED BY DEFAULT.

Idea: `gh pr create` is exactly the kind of action that opens a thread the
operator will need resolved later (a review verdict). This gate can require
that at least one open (unclosed) thread already exists before a `gh pr
create` is allowed to run -- forcing the predicate to be registered at the
moment the wait begins, not reconstructed from memory afterward.

DEFAULT: OFF. This file is wired into hooks.json's PreToolUse matcher (so it
runs, cheaply, on every Bash call) but its own first action is to read a
config key and return an ALLOW no-op unless that key is explicitly true.
Nothing in this plugin, this PR, or its installation flips that key --
per the build's hard gate, only the operator does that, by hand, later:

    ~/.cog/status/threads-config.json
    { "enforce_pr_create_thread": true }

Contract when armed:
  - Only inspects Bash tool calls whose command matches `gh pr create`.
  - DENIES (permissionDecision "deny") when zero open threads exist in the
    registry at call time.
  - FAILS OPEN on any internal error, missing state file, unreadable
    config, or unavailable dependency -- a broken gate must never wedge a
    legitimate `gh pr create`. Same fail-open discipline as the rest of
    this plugin's hooks, and the same PreToolUse response shape already
    used by this operator's attribution_gate.py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

_PR_CREATE_RE = re.compile(r"\bgh\s+pr\s+create\b", re.IGNORECASE)


def _allow() -> None:
    print("{}")


def _deny(reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))


def main() -> None:
    try:
        inp = json.load(sys.stdin)
    except Exception:
        _allow()
        return

    try:
        if inp.get("tool_name") != "Bash":
            _allow()
            return
        command = (inp.get("tool_input") or {}).get("command", "") or ""
        if not _PR_CREATE_RE.search(command):
            _allow()
            return

        import threads_core as core

        cfg = core.load_config()
        if not cfg.get("enforce_pr_create_thread", False):
            _allow()
            return

        try:
            data = core.load_state()
        except core.CorruptStateError:
            # Armed, but the registry itself is unreadable: fail OPEN, not
            # closed -- a corrupt registry must never be able to wedge
            # every future `gh pr create` in the harness.
            _allow()
            return

        if core.open_threads(data):
            _allow()
            return

        _deny(
            "BLOCKED by threads-gate-pr (enforce_pr_create_thread=true): no "
            "open thread is registered. `gh pr create` starts a wait on a "
            "review verdict -- register the predicate for it first: "
            "`threads add --what '...' --why '...' "
            "--predicate '[ \"$(gh pr view <n> --json reviewDecision --jq .reviewDecision)\" = \"APPROVED\" ]' "
            "--expected-by 1d`. See skills/threads/SKILL.md."
        )
    except Exception:
        # Fail open -- never wedge a legitimate gh call on a hook bug.
        _allow()


if __name__ == "__main__":
    main()
