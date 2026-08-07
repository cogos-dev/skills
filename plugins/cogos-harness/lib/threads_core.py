#!/usr/bin/env python3
"""threads_core.py — shared primitives for the threads registry.

The registry exists to answer one question truthfully at any later point,
with no memory of who asked it to be true: **is the thing this thread is
waiting on actually resolved?** That's why a thread's identity is a
RESOLUTION PREDICATE (a bounded shell command whose exit code answers
"resolved?"), not a completion signal (did some process exit). The
distinguishing failure this fixes: watching a CI *run* answers "did it
finish", not "is the verdict in" — a run can finish long before the thing
being waited on (e.g. a review decision) has actually landed. See
skills/threads/SKILL.md for the worked example and the write-a-good-
predicate guidance.

Schema — DECLARED fields (the only ones a caller ever writes):
  id            str  — short, unique, human-chosen or auto-slugged
  what          str  — one line: what is being waited on
  why           str  — one line: why it matters
  predicate     str  — a bounded shell command; exit 0 == resolved
  opened_at     str  — ISO8601, stamped by `threads add`
  expected_by   str  — ISO8601 timestamp OR a duration ("2h","1d","45m","30s")
                        relative to opened_at
  owner         str  — session/seat id that registered the thread
  closed_at     str | None — set only by `threads close` (an explicit,
                        declared action — closing is not the same thing as
                        the predicate resolving; a resolved thread still
                        needs an operator/agent to look at it and close it)
  closed_reason str | None

Everything else — resolved, orphaned, overdue, age — is DERIVED: computed
fresh by RUNNING the predicate and comparing timestamps, never read back out
of a stored field. A registry that could self-report "all clear" from a
hand-written flag is exactly the failure this replaces (see the module
docstring's node_count:0-since-January reference in the build brief this
shipped from). derive_status() is the single place that computation happens;
nothing else in this module or its callers may set those fields by hand.

Storage: a single JSON file, {"version": 1, "threads": [...]}. Atomic
writes (write-to-tempfile + os.replace) so a hook reading mid-write never
sees a torn file. A corrupt or unreadable-but-present file is reported via
CorruptStateError, NEVER silently replaced with a fresh empty state — losing
someone's registered threads because the reader panicked and reset the file
would be worse than the bug this registry exists to catch.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_STATE_PATH = Path.home() / ".cog" / "status" / "threads.json"
STATE_PATH = Path(os.environ.get("COGOS_THREADS_STATE", str(DEFAULT_STATE_PATH)))

DEFAULT_CONFIG_PATH = Path.home() / ".cog" / "status" / "threads-config.json"
CONFIG_PATH = Path(os.environ.get("COGOS_THREADS_CONFIG", str(DEFAULT_CONFIG_PATH)))

SCHEMA_VERSION = 1
DECLARED_FIELDS = (
    "id", "what", "why", "predicate", "opened_at", "expected_by", "owner",
    "closed_at", "closed_reason",
)

DURATION_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*([smhdw])\s*$", re.IGNORECASE)
_DURATION_SECONDS = {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}


class CorruptStateError(Exception):
    """Raised when the state file exists but does not parse as the expected
    shape. Callers MUST surface this, never swallow it into a fresh reset —
    see module docstring."""


class ThreadNotFoundError(Exception):
    pass


# --------------------------------------------------------------------- time --

def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_ts(raw: str | None) -> datetime | None:
    """Best-effort ISO8601 -> tz-aware UTC datetime. None on any failure —
    absence of a parseable timestamp is a signal callers must handle, never
    an exception that takes the whole hook down with it."""
    if not raw or not isinstance(raw, str):
        return None
    t = raw.strip().replace("Z", "+00:00")
    for cand in (t, re.sub(r"\.\d+", "", t)):
        try:
            dt = datetime.fromisoformat(cand)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue
    return None


def parse_expected_by(raw: str | None, opened_at: datetime | None) -> datetime | None:
    """expected_by is either an absolute ISO8601 timestamp, or a duration
    ("2h", "45m", "1d", "30s", "1w") measured from opened_at. Returns None
    if it parses as neither — callers must treat that as "no deadline
    known", not as an error (a thread with an unparsable expected_by is
    still a valid open thread; it just never triggers the overdue path)."""
    if not raw:
        return None
    m = DURATION_RE.match(raw)
    if m and opened_at is not None:
        qty, unit = m.groups()
        return opened_at + timedelta(seconds=float(qty) * _DURATION_SECONDS[unit.lower()])
    return parse_ts(raw)


def human_age(delta: timedelta) -> str:
    secs = int(delta.total_seconds())
    if secs < 0:
        return "0s"
    if secs < 60:
        return f"{secs}s"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m"
    hrs = mins // 60
    if hrs < 48:
        return f"{hrs}h{mins % 60:02d}m"
    days = hrs // 24
    return f"{days}d{hrs % 24:02d}h"


# -------------------------------------------------------------------- state --

def _default_state() -> dict:
    return {"version": SCHEMA_VERSION, "threads": []}


def load_state(path: Path = STATE_PATH) -> dict:
    """Missing file -> fresh empty state (the common, harmless case: nobody
    has registered a thread yet). Present-but-unreadable/malformed file ->
    CorruptStateError, always -- never silently reset. Empty-but-present
    file is treated as corrupt too (a 0-byte file is not a valid empty
    state; our own atomic writer never produces one, so its presence means
    something wrote outside this module's contract)."""
    if not path.exists():
        return _default_state()
    try:
        raw = path.read_text(encoding="utf-8")
    except Exception as e:
        raise CorruptStateError(f"{path}: unreadable ({e})") from e
    if not raw.strip():
        raise CorruptStateError(f"{path}: present but empty (0 bytes) — not a valid state file")
    try:
        data = json.loads(raw)
    except Exception as e:
        raise CorruptStateError(f"{path}: invalid JSON ({e})") from e
    if not isinstance(data, dict) or not isinstance(data.get("threads"), list):
        raise CorruptStateError(
            f"{path}: unexpected shape (expected an object with a 'threads' list)"
        )
    for t in data["threads"]:
        if not isinstance(t, dict) or not t.get("id"):
            raise CorruptStateError(f"{path}: a thread entry is malformed (missing 'id')")
    return data


def atomic_write(data: dict, path: Path = STATE_PATH) -> None:
    """Write-to-tempfile-then-os.replace so a concurrent reader (the warn
    hook, firing on every turn) never observes a torn/partial file. Same
    filesystem as the target by construction (tempfile lives alongside it),
    so os.replace is atomic on every platform this plugin targets (macOS)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{uuid.uuid4().hex[:8]}")
    tmp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def find_thread(data: dict, thread_id: str) -> dict:
    for t in data.get("threads", []):
        if t.get("id") == thread_id:
            return t
    raise ThreadNotFoundError(thread_id)


def open_threads(data: dict) -> list[dict]:
    """Threads not yet explicitly closed. `closed_at` is the only gate —
    resolved-but-not-yet-closed threads still show up here on purpose:
    resolution and closing are different declared moments (see module
    docstring)."""
    return [t for t in data.get("threads", []) if not t.get("closed_at")]


def slugify(text: str, maxlen: int = 40) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s[:maxlen].rstrip("-")) or "thread"


def new_id(what: str, existing_ids: set[str]) -> str:
    base = slugify(what)
    ts = str(int(time.time()))[-5:]
    cand = f"{base}-{ts}"
    if cand not in existing_ids:
        return cand
    return f"{base}-{ts}-{uuid.uuid4().hex[:4]}"


# ---------------------------------------------------------------- predicate --

@dataclass
class PredicateResult:
    resolved: bool
    note: str = ""          # "" on a clean run; "timeout" / "error: ..." otherwise
    duration_s: float = 0.0


def run_predicate(cmd: str, timeout: float) -> PredicateResult:
    """Runs `cmd` via `/bin/sh -c`, hard-bounded by `timeout`. Contract:
    exit code 0 == resolved; any nonzero exit == not resolved (no special
    meaning attached to particular nonzero codes — a predicate author who
    wants nuance reduces it to exit-0/nonzero themselves, e.g. via `test` or
    `[[ ... ]]`, same convention as the shell `until` idiom this environment
    already uses elsewhere). Never raises: a hung, missing, or erroring
    predicate is reported as unresolved with a note, not an exception —
    callers (in particular the per-turn hook) must be able to treat every
    predicate outcome uniformly."""
    start = time.monotonic()
    try:
        r = subprocess.run(
            ["/bin/sh", "-c", cmd],
            capture_output=True,
            timeout=timeout,
            text=True,
        )
        return PredicateResult(resolved=(r.returncode == 0), duration_s=time.monotonic() - start)
    except subprocess.TimeoutExpired:
        return PredicateResult(resolved=False, note="timeout", duration_s=time.monotonic() - start)
    except Exception as e:
        return PredicateResult(resolved=False, note=f"error: {e}", duration_s=time.monotonic() - start)


# -------------------------------------------------------------------- derive --

@dataclass
class ThreadStatus:
    thread: dict
    resolved: bool
    predicate_note: str
    age: timedelta
    expected_by_ts: datetime | None
    overdue: bool
    orphaned: bool
    orphan_reasons: list[str] = field(default_factory=list)


def derive_status(thread: dict, timeout: float, now: datetime | None = None) -> ThreadStatus:
    """The one place resolved/overdue/orphaned/age get computed. Always
    RUNS the predicate — never trusts a cached/prior value — because a
    registry that reports staleness from its own stale cache can't be
    trusted to report staleness at all."""
    now = now or now_utc()
    opened = parse_ts(thread.get("opened_at")) or now
    expected = parse_expected_by(thread.get("expected_by"), opened)
    pred = run_predicate(thread.get("predicate", ""), timeout)
    age = now - opened
    overdue = bool(expected and now > expected and not pred.resolved)
    reasons = []
    if overdue:
        reasons.append("overdue")
    # Owner-liveness ("the registering session is gone") is intentionally
    # NOT checked here: it would require a network call to the kernel, and
    # this function is called from the per-turn warn hook, which the
    # operating gate forbids from making network calls. `threads check`
    # (the interactive CLI, not a per-turn hook) may add a liveness check
    # later without changing this schema or this function's contract.
    orphaned = bool(reasons) and not pred.resolved
    return ThreadStatus(
        thread=thread,
        resolved=pred.resolved,
        predicate_note=pred.note,
        age=age,
        expected_by_ts=expected,
        overdue=overdue,
        orphaned=orphaned,
        orphan_reasons=reasons,
    )


# -------------------------------------------------------------------- config --

def load_config(path: Path = CONFIG_PATH) -> dict:
    """Best-effort config read for the (disabled-by-default) enforcement
    tier. Missing/corrupt file -> {} -> every key reads as its documented
    default. Never raises."""
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}
