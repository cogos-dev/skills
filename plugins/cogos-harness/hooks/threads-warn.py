#!/usr/bin/env python3
"""threads-warn.py — UserPromptSubmit warn-tier for the threads registry.

Fires on every turn of every session (see the plugin-wide hard gate in
README.md). That means this file's failure modes are load-bearing, not
incidental:

  - Any exception, missing file, malformed state, or unavailable dependency
    -> emit NOTHING and exit 0. Never raise past main(). Never print a
    traceback -- the operator's daily driver must never see one from here.
  - Bounded work only: predicates run with a hard per-predicate timeout
    (THREADS_PREDICATE_TIMEOUT) AND the whole hook is bounded by an overall
    wall-clock budget (THREADS_TOTAL_BUDGET) -- once the budget is spent,
    remaining threads are silently skipped for this turn rather than
    pushing the hook past its latency budget. No network calls originate
    from this file itself (see derive_status()'s docstring in
    lib/threads_core.py for why owner-liveness checking is deferred rather
    than added here).
  - SILENT BY DEFAULT. This hook speaks only when at least one open thread
    is orphaned (unresolved AND past its expected_by). A healthy registry,
    an empty registry, or a registry this hook couldn't even read all
    produce identical silence -- absence of a block is not evidence
    everything is fine, only that nothing here demanded attention.

Corrupt/missing state file: silent, on purpose. `threads list`/`threads
check`, run by a human or an agent that actually wants to know, report
corruption loudly (see bin/threads's _load_or_die). This hook is not that
surface -- surfacing a corrupt-file warning on every single turn is exactly
the wallpaper failure mode the gate warns about, and the CLI already
reports it whenever someone actually looks.
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "lib"))

THREADS_PREDICATE_TIMEOUT = float(os.environ.get("COGOS_THREADS_PREDICATE_TIMEOUT", "3"))
THREADS_TOTAL_BUDGET = float(os.environ.get("COGOS_THREADS_TOTAL_BUDGET", "4"))
MAX_LINES = 5  # cap how many orphan lines render; rest collapse to a count


def _read_event_name() -> str:
    try:
        raw = sys.stdin.read()
        if raw.strip():
            return json.loads(raw).get("hook_event_name") or "UserPromptSubmit"
    except Exception:
        pass
    return "UserPromptSubmit"


def _emit(evt: str, block: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": evt,
            "additionalContext": block,
        }
    }))


def _line_for(core, status) -> str:
    t = status.thread
    reasons = ",".join(status.orphan_reasons) or "?"
    exp = core.iso(status.expected_by_ts) if status.expected_by_ts else "?"
    note = f" [{status.predicate_note}]" if status.predicate_note else ""
    what = (t.get("what") or "")[:70]
    return (
        f'⚠ {t.get("id")} ({reasons}): "{what}" — age {core.human_age(status.age)}, '
        f'expected_by {exp}, owner={t.get("owner","?")}{note}'
    )


def main() -> None:
    evt = _read_event_name()
    try:
        import threads_core as core
    except Exception:
        return  # can't even import the library -> fully silent, per contract

    try:
        data = core.load_state()
    except Exception:
        # Missing, corrupt, or otherwise unreadable state: silent by design
        # on this hook -- see module docstring. `threads list` is where
        # corruption gets reported loudly.
        return

    try:
        open_threads = core.open_threads(data)
    except Exception:
        return
    if not open_threads:
        return

    deadline = time.monotonic() + THREADS_TOTAL_BUDGET
    orphan_lines: list[str] = []
    skipped_for_budget = 0

    for t in open_threads:
        if time.monotonic() >= deadline:
            skipped_for_budget += 1
            continue
        try:
            per_thread_timeout = min(THREADS_PREDICATE_TIMEOUT, max(0.1, deadline - time.monotonic()))
            # skip_predicate_if_not_due=True: this hook only ever emits for
            # orphaned (overdue-and-unresolved) threads, so for any thread
            # not yet past its expected_by the predicate's exit code cannot
            # change this hook's output -- skip running it (no subprocess,
            # no possible network call) rather than paying full predicate
            # latency/budget every turn for a deadline that hasn't arrived.
            status = core.derive_status(t, timeout=per_thread_timeout, skip_predicate_if_not_due=True)
        except Exception:
            # A single bad thread entry (or a predicate that errors in some
            # exotic way derive_status didn't already catch) must never
            # take down the check for every other thread.
            continue
        if status.orphaned:
            try:
                orphan_lines.append(_line_for(core, status))
            except Exception:
                continue

    if not orphan_lines:
        return  # silent: no orphans this turn, budget skips notwithstanding

    shown = orphan_lines[:MAX_LINES]
    extra = len(orphan_lines) - len(shown)
    body = "\n".join(shown)
    if extra:
        body += f"\n… +{extra} more orphaned thread(s) (`threads list`, `threads check`)"
    if skipped_for_budget:
        body += f"\n({skipped_for_budget} open thread(s) not checked this turn — over budget)"

    block = (
        f'<threads_warn count="{len(orphan_lines)}">\n{body}\n'
        f"(`threads check <id>` for detail, `threads close <id>` to close)\n"
        f"</threads_warn>"
    )
    _emit(evt, block)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
