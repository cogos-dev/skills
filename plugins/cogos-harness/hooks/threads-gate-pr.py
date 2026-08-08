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
  - Only inspects Bash tool calls whose command tokenizes to an actual `gh
    pr create` INVOCATION -- some top-level segment's argv starts with
    `gh`, `pr`, `create`, in that order -- not merely a command string
    that contains those three words somewhere (e.g. as a quoted argument
    to `git commit -m` or `grep`). See `_looks_like_gh_pr_create()` and
    `_split_commands()` below for exactly what is and isn't caught (F2 in
    the 2026-08-07 independent review: a bare substring match flagged
    `git commit -m "docs: ... gh pr create ..."` and `grep -rn "gh pr
    create" .` as if they were the real thing).
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
import shlex
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))


def _split_commands(command: str) -> list[str]:
    """Best-effort split of a shell command line into simple-command
    segments, breaking on TOP-LEVEL (outside single/double quotes)
    occurrences of `;`, `&&`, `||`, `|`, `$(`, and newline. This is NOT a
    real shell parser -- it exists only to tell "gh pr create" appearing
    as an actual invoked command apart from it appearing merely as a
    quoted string argument to some other command. Splitting on `$(` means
    the text of a command substitution is checked like any other segment
    (so `FOO=$(gh pr create ...)` is still caught), even though nesting
    and closing-paren handling inside the substitution aren't modeled
    precisely -- good enough for a warn-tier gate that only needs to spot
    the invocation, not fully parse arbitrary shell.

    Known, accepted limit, documented rather than silently pretended
    away: variable-substitution evasion (`C=create; gh pr $C`, `$X pr
    create`) is NOT caught. Catching that would require actually
    expanding shell variables, i.e. running a shell -- exactly the kind
    of side effect a PreToolUse gate must never have. This gate only ever
    denies a LITERAL `gh pr create` invocation; anyone motivated enough to
    obfuscate past a warn-tier gate on their own machine can already do
    so, same as any other client-side check."""
    segments: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    i = 0
    n = len(command)
    while i < n:
        ch = command[i]
        if quote:
            buf.append(ch)
            if ch == quote and command[i - 1] != "\\":
                quote = None
            i += 1
            continue
        if ch in ("'", '"'):
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if command.startswith("$(", i):
            segments.append("".join(buf))
            buf = []
            i += 2
            continue
        if command.startswith("&&", i) or command.startswith("||", i):
            segments.append("".join(buf))
            buf = []
            i += 2
            continue
        if ch in (";", "|", "\n"):
            segments.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    segments.append("".join(buf))
    return segments


def _looks_like_gh_pr_create(command: str) -> bool:
    """True iff some top-level segment of `command` is an actual
    invocation whose argv starts with `gh pr create` (flags interleaved
    anywhere after that are irrelevant -- this only needs to detect that
    the invocation exists at all; the registry check downstream is what
    decides allow/deny). See `_split_commands()` for the documented
    limits, most notably: no variable-substitution evasion detection."""
    for segment in _split_commands(command):
        try:
            argv = shlex.split(segment, posix=True)
        except ValueError:
            # Unbalanced quotes etc. in this segment -- skip it rather
            # than raising; other segments are still checked, and any
            # exception that does escape this function still lands in
            # main()'s fail-open catch-all.
            continue
        if argv[:3] == ["gh", "pr", "create"]:
            return True
    return False


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
        if not _looks_like_gh_pr_create(command):
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
