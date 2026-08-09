#!/usr/bin/env python3
"""Memory-janitor output checker — the deterministic filter half of the loop.

Portable port of a script promoted from an operator-local seat, 2026-08-08:
the dispatched Haiku lane does the compaction; this script grades it. PASS
settles the round. DEFECTS emits repair pointers the pilot re-dispatches
with (pull-context: pointers, not re-explanation). Every round appends to
a ledger — that's training data (directive version + outcome).

Path resolution, in order of precedence:
  1. --current / --baseline, if passed explicitly.
  2. --project-dir PATH — the raw (unsanitized) project directory, sanitized
     the same way Claude Code names a project's `~/.claude/projects/<...>`
     tree, then MEMORY.md / janitor/ derived under it exactly as the
     trigger hook derives its own. This is what the `memory-janitor`
     skill's canonical command passes — the "project dir" value the
     trigger hook already resolved and printed in its block reason — and
     is reliable regardless of the invoking shell's own cwd.
  3. Hook-shaped stdin JSON "cwd" -> $CLAUDE_PROJECT_DIR -> os.getcwd().
     This mirrors the trigger hook's own resolution chain, kept for parity
     and for direct hook-shaped piping, but it is a fallback, not the
     common case: run via the Bash tool, stdin carries no hook payload
     (reads as empty) and CLAUDE_PROJECT_DIR is typically unset, so in
     practice only bare os.getcwd() is ever live here — and the Bash
     tool's cwd persists silently across calls, so an earlier `cd`
     retargets this without warning. Pass --project-dir explicitly rather
     than relying on this chain.

With --project-dir (or with neither --project-dir nor --baseline/--current,
i.e. the plain fallback case), the ledger is that project's own
janitor/ledger.jsonl. If --baseline/--current are given explicitly WITHOUT
--project-dir, the run is a one-off/fixture invocation: its ledger row is
written next to whichever of the two was given explicitly (--current if
given, else --baseline -- so a lone --baseline can never fall through to
the cwd-derived project's real ledger), tagged "fixture": true, unless
that anchor file's own parent directory is literally named "memory"
(content-scanned as auto-memory), in which case the ledger steps up one
level so a fixture row can never land inside a memory/ directory either.

Exit 0 = PASS, 1 = DEFECTS, 2 = checker error (cannot grade — malformed
invocation, inconsistent thresholds, missing/unreadable files, or any
other uncaught fault). These three mean exactly that and nothing else.

Usage: check.py [--baseline PATH] [--current PATH] [--project-dir PATH]
                 [--target N] [--floor N] [--trigger N] [--round N]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

LINK_RE = re.compile(r"\]\(([^)]+)\)")
# Sentinel prefix for keys derived from a linkless bullet's own text, so
# they can never collide with a real markdown link target.
LINKLESS_KEY_PREFIX = "\x00linkless:"


def _cwd_from_stdin() -> str | None:
    """Best-effort drain of a hook-shaped JSON payload's "cwd" key, if one
    happens to be piped in. Never blocks on an interactive terminal —
    check.py is normally invoked directly with no stdin at all, so this is
    a rarely-exercised fallback, kept only so the trigger hook and this
    checker share one derivation rule instead of two that could drift."""
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


def _sanitize(cwd: str) -> str:
    """Same normalization Claude Code uses for a project's
    `~/.claude/projects/<sanitized>` directory name. Matches memory-janitor.py."""
    return re.sub(r"[^A-Za-z0-9]", "-", cwd)


def _resolve_cwd() -> str:
    """cwd resolution order: hook stdin JSON "cwd" -> $CLAUDE_PROJECT_DIR ->
    os.getcwd(); see the module docstring for why only the last of these
    is ever actually live in a Bash-tool invocation."""
    return _cwd_from_stdin() or os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def _paths_for_project_dir(project_dir: str) -> tuple[Path, Path, Path]:
    """(current, baseline, ledger) derived under a given raw project dir,
    honoring the same COG_JANITOR_FILE / COG_JANITOR_STATE_DIR overrides as
    the trigger hook."""
    projects_dir = Path.home() / ".claude" / "projects" / _sanitize(project_dir)
    current = Path(os.environ.get("COG_JANITOR_FILE") or str(projects_dir / "memory" / "MEMORY.md"))
    state_dir = Path(os.environ.get("COG_JANITOR_STATE_DIR") or str(projects_dir / "janitor"))
    return current, state_dir / "baseline", state_dir / "ledger.jsonl"


def _default_paths() -> tuple[Path, Path, Path]:
    """Fallback derivation when no --project-dir is given: see precedence
    tier 3 in the module docstring."""
    return _paths_for_project_dir(_resolve_cwd())


def entry_key(line: str) -> str:
    """Stable dict key for a `- ` bullet line: its first markdown link
    target if it has one, else its text up to the first ':' (else the
    first 30 chars, whitespace-normalized) — so linkless bullets are still
    tracked for deletion, under a sentinel-prefixed key that can never
    collide with a real link target."""
    m = LINK_RE.search(line)
    if m:
        return m.group(1)
    body = line[2:]  # strip the leading "- "
    colon = body.find(":")
    key_text = body[:colon] if colon != -1 else body[:30]
    return LINKLESS_KEY_PREFIX + " ".join(key_text.split())


def _display_key(key: str) -> str:
    if key.startswith(LINKLESS_KEY_PREFIX):
        text = key[len(LINKLESS_KEY_PREFIX):]
        return f"\"{text}\" (linkless bullet deleted)"
    return key


def entry_lines(text: str) -> dict[str, list[str]]:
    """Map key -> every full line sharing that key, in order. Every line
    starting with '- ' is inventoried, linked or not; duplicate-keyed
    bullets are kept as repeated list entries (Counter semantics
    downstream), never collapsed to a single sighting."""
    out: dict[str, list[str]] = {}
    for line in text.splitlines():
        if line.startswith("- "):
            out.setdefault(entry_key(line), []).append(line)
    return out


def stripped_len(line: str) -> int:
    """Length of the line minus link-target syntax (display text + tails remain)."""
    return len(LINK_RE.sub("]", line))


def clauses(line: str) -> int:
    return line.count(";") + 1


def _env_int(name: str, default: int) -> int:
    """Read an integer env override. Unlike the trigger hook, a malformed
    value here is NOT silently defaulted: it propagates (caught by the
    outer CHECKER-ERROR handler in __main__) because grading with a
    silently-guessed threshold could produce a misleading verdict — a
    checker that can't confirm its own configuration should refuse to
    grade, not guess quietly."""
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    return int(raw)


def main() -> int:
    directive = Path(__file__).resolve().parent / "directive.md"

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--baseline", type=Path, default=None,
                     help="Path to the pre-compaction snapshot. Defaults per the "
                          "precedence chain in the module docstring.")
    ap.add_argument("--current", type=Path, default=None,
                     help="Path to the post-compaction file to grade. Defaults per "
                          "the precedence chain in the module docstring.")
    ap.add_argument(
        "--project-dir", type=str, default=None,
        help="Raw (unsanitized) project directory — e.g. the 'project dir' "
             "line from the trigger hook's block reason. Derives "
             "--current/--baseline/the ledger path the same way the hook "
             "derives its own MEMORY.md/janitor/ paths. Explicit --baseline "
             "/ --current still win per-path if also given.",
    )
    ap.add_argument("--target", type=int, default=None,
                     help="Byte-size ceiling to grade against. Defaults to "
                          "$COG_JANITOR_TARGET or 16500.")
    ap.add_argument("--floor", type=int, default=None,
                     help="Byte-size overtrim floor to grade against. Defaults to "
                          "$COG_JANITOR_FLOOR or 15500.")
    ap.add_argument("--trigger", type=int, default=None,
                     help="Byte-size the trigger hook blocked at, for the "
                          "floor<target<=trigger sanity check. Defaults to "
                          "$COG_JANITOR_TRIGGER or 18800.")
    ap.add_argument("--round", type=int, default=1, dest="round_n",
                     help="Repair-round number, echoed in the verdict line and "
                          "the ledger row. 1 for the first check, 2 for the repair check.")
    args = ap.parse_args()

    if args.project_dir:
        proj_current, proj_baseline, proj_ledger = _paths_for_project_dir(args.project_dir)
        is_fixture = False
    else:
        proj_current, proj_baseline, proj_ledger = _default_paths()
        is_fixture = args.baseline is not None or args.current is not None

    current = args.current if args.current is not None else proj_current
    baseline = args.baseline if args.baseline is not None else proj_baseline

    if is_fixture:
        # Anchor next to whichever explicit file was actually passed --
        # --current if given, else --baseline -- never the cwd-derived
        # project ledger, and never inside a directory literally named
        # "memory" (content-scanned as auto-memory) even if the anchor
        # file itself happens to live there.
        anchor = args.current if args.current is not None else args.baseline
        anchor_dir = anchor.parent
        if anchor_dir.name == "memory":
            anchor_dir = anchor_dir.parent
        ledger = anchor_dir / "ledger.jsonl"
    else:
        ledger = proj_ledger

    # Always the first line: what this run actually resolved to grade,
    # before anything below can fail.
    print(f"grading {current} vs {baseline}")

    target = args.target if args.target is not None else _env_int("COG_JANITOR_TARGET", 16500)
    floor = args.floor if args.floor is not None else _env_int("COG_JANITOR_FLOOR", 15500)
    trigger = args.trigger if args.trigger is not None else _env_int("COG_JANITOR_TRIGGER", 18800)

    if not (floor < target <= trigger):
        print(f"CHECKER-ERROR invalid thresholds: floor={floor} target={target} trigger={trigger} — require floor < target <= trigger")
        return 2

    if baseline.is_dir() or current.is_dir():
        which = "baseline" if baseline.is_dir() else "current"
        print(f"CHECKER-ERROR {which} path is a directory, not a file: {baseline if which == 'baseline' else current}")
        return 2

    if not baseline.exists() or not current.exists():
        print(f"CHECKER-ERROR missing file: baseline={baseline} current={current}")
        return 2

    base = baseline.read_text()
    cur = current.read_text()
    size_before, size_after = len(base.encode()), len(cur.encode())
    defects = []

    if size_after > target:
        defects.append(f"size: {size_after} B still over target {target} — trim further (longest tails first)")
    if size_after < floor:
        defects.append(
            f"overtrim: {size_after} B is {floor - size_after} B below floor {floor} — "
            f"trimmed past the target; restore clauses from the flagged entries below"
        )

    base_links = Counter(LINK_RE.findall(base))
    cur_links = Counter(LINK_RE.findall(cur))
    if base_links != cur_links:
        missing = sorted(k for k in base_links if k not in cur_links)
        added = sorted(k for k in cur_links if k not in base_links)
        changed = sorted(k for k in (base_links.keys() & cur_links.keys()) if base_links[k] != cur_links[k])
        if missing:
            defects.append(f"links: {len(missing)} target(s) LOST: {', '.join(missing[:8])} — restore them verbatim")
        if added:
            defects.append(f"links: {len(added)} target(s) invented: {', '.join(added[:8])} — remove them")
        if changed:
            deltas = ", ".join(f"{k} {base_links[k]}->{cur_links[k]}" for k in changed[:8])
            defects.append(f"links: {len(changed)} target(s) changed occurrence count: {deltas} — restore the missing occurrence(s)")

    base_entries = entry_lines(base)
    cur_entries = entry_lines(cur)
    base_counts = Counter({k: len(v) for k, v in base_entries.items()})
    cur_counts = Counter({k: len(v) for k, v in cur_entries.items()})
    lost_counter = base_counts - cur_counts
    if lost_counter:
        total_lost = sum(lost_counter.values())
        parts = [
            (f"{_display_key(k)} x{lost_counter[k]}" if lost_counter[k] > 1 else _display_key(k))
            for k in sorted(lost_counter)
        ]
        defects.append(f"entries: {total_lost} bullet(s) deleted (keyed {', '.join(parts[:5])}) — restore each as a line")

    base_heads = [l for l in base.splitlines() if l.startswith("#")]
    cur_heads = [l for l in cur.splitlines() if l.startswith("#")]
    if base_heads != cur_heads:
        defects.append("headers: section header set/order changed — restore the baseline headers exactly")

    # Clause-retention scan: flag entries whose annotation lost too much.
    # Linkless bullets are exempt — the entries check above already covers
    # their presence/absence; their tails remain freely trimmable.
    for key, blines in base_entries.items():
        if key.startswith(LINKLESS_KEY_PREFIX):
            continue
        clines = cur_entries.get(key)
        if not clines:
            continue
        for bline, cline in zip(blines, clines):
            blen, clen = stripped_len(bline), stripped_len(cline)
            clause_drop = clauses(bline) - clauses(cline)
            char_loss = 1 - (clen / blen) if blen else 0
            if clause_drop >= 2 or (char_loss > 0.5 and (blen - clen) > 60):
                defects.append(
                    f"clause-loss [{key}]: lost {clause_drop} clause(s), {int(char_loss * 100)}% of annotation. "
                    f"Baseline line was: {bline}"
                )

    verdict = "PASS" if not defects else "DEFECTS"
    directive_sha = hashlib.sha256(directive.read_bytes()).hexdigest()[:12] if directive.exists() else None
    total_cur_links = sum(cur_links.values())

    # Verdict and pointers print BEFORE the ledger is touched: a
    # ledger-write failure must never cost an already-computed verdict or
    # flip the exit code (same "bookkeeping never costs the result" rule
    # the trigger hook already follows for its own state writes).
    print(f"{verdict} {size_before} -> {size_after} B, {total_cur_links} links, round {args.round_n}")
    if defects:
        print("\nRepair pointers (re-dispatch the janitor with EXACTLY this list + baseline/current paths):")
        for d in defects:
            print(f"  - {d}")

    try:
        ledger.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger, "a") as f:
            f.write(json.dumps({
                "ts": int(time.time()),
                "round": args.round_n,
                "directive_sha": directive_sha,
                "baseline": str(baseline),
                "current": str(current),
                "size_before": size_before,
                "size_after": size_after,
                "verdict": verdict,
                "defects": defects,
                "fixture": is_fixture,
            }) + "\n")
    except Exception as e:
        print(f"<memory-janitor> warning: ledger append failed: {type(e).__name__}: {e}", file=sys.stderr)

    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"CHECKER-ERROR {type(e).__name__}: {e}")
        sys.exit(2)
