#!/usr/bin/env python3
"""
User-scope UserPromptSubmit hook — minimal proprioception stub.

Injects a one-line status tag on every prompt when Claude Code is invoked
outside the cog workspace (non-cog sessions). Provides branch + timestamp
spatial awareness without requiring the full cog substrate.

When invoked FROM inside the cog workspace, skips entirely — the workspace-
scope foveated-context + dispatch hooks (if any) already provide richer
proprioception.

Output when active:
  <cogos_proprioception>
    branch=main | 2026-05-13T19:48Z | cwd=/path/to/dir
    local=2026-05-13 15:48 EDT (afternoon) | session_elapsed=2h13m | model=Sonnet 4.6
    cogos 0.16.27 ok · 0err 0anom · up 3-12:04:11 | PRs 2
  </cogos_proprioception>

If cwd is not a git repo, branch field is omitted or shows "no-git".

Temporal binding: the second line anchors the agent to LOCAL wall-clock,
day-phase, and elapsed session time. Rationale: agents advance an internal
narrative clock by work density (training prior) rather than by the actual
clock — several hours of dense work reads as "late evening." The binding
makes the real clock ambient. Session start times are tracked per
session_id in a small JSON state file.

Model binding: the second line also surfaces the model the LAST completed
assistant turn actually ran on, read straight from the session transcript
JSONL — the harness can silently route a session onto a different model
than the one requested, and this makes that ambient rather than invisible.
This is a ONE-TURN-LAGGED read: UserPromptSubmit fires before the upcoming
turn generates, so the header shows the previous turn's model. For sticky
context-driven routing changes that is exactly right — the moment after a
flip, the header marks it. Last-seen model is tracked per session_id
alongside the elapsed-time state.

Third line (when available): the kernel-vitals segment, a pre-formatted
one-liner written by kernel-vitals-probe.py (fired detached, below, when its
cache goes stale) — kernel health, error/anomaly counts, release/PR status.
This hook itself never makes a network call to PRODUCE that line — it only
reads the probe's cache.

Session heartbeat (#17): when that cache already shows the kernel
reachable (a round-trip some prior probe cycle already completed, read
here for free), this hook also POSTs the session heartbeat — the REST
counterpart of cog_heartbeat_session — so a seat's LastSeen advances
without needing its own dedicated poller. This is the one network call
this hook makes, and it is conditional: zero extra probes are ever fired
against an absent/unreachable kernel, and it fires at most once per
UserPromptSubmit turn (this hook runs once per turn by construction).

Safety contract: never raises, always exits 0. Short-circuit on any error.
Performance target: <200ms (git rev-parse cached by OS; the vitals read is
a local cache read, not a network call — only the conditional heartbeat
POST above touches the network, and its timeout is deliberately tight
(HEARTBEAT_TIMEOUT) so that even a kernel that accepts connections and
then hangs cannot push this hook meaningfully past its budget).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Where this plugin's own state/cache files live. CLAUDE_PLUGIN_DATA is the
# persistent per-plugin directory Claude Code provides (survives plugin
# updates); fall back to the historical ~/.claude/hooks location so this
# script also works unchanged when run standalone (not installed as a
# plugin), e.g. during local development.
_DATA_DIR = Path(os.environ.get("CLAUDE_PLUGIN_DATA") or (Path.home() / ".claude" / "hooks"))
# Where this plugin's own sibling scripts live (the detached probe this hook
# fires). Falls back to the same directory as this file for standalone use.
_PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or str(Path(__file__).resolve().parent.parent))

# COGOS_KERNEL_URL takes precedence when set; COGOS_KERNEL_PORT is a
# localhost-only convenience default. Same precedence as
# seat-identity-heal.py / kernel-vitals-probe.py so every hook resolves to
# the same kernel. Only used by the conditional heartbeat POST (#17) --
# this hook otherwise stays network-free, per its original contract.
KERNEL_URL = os.environ.get("COGOS_KERNEL_URL") or \
    f"http://127.0.0.1:{os.environ.get('COGOS_KERNEL_PORT', '6931')}"
# Deliberately far below the other hooks' 1.0-1.5s: this one call sits on
# the UserPromptSubmit critical path, so its timeout is the per-turn tax
# whenever the kernel accepts a connection but stops answering (a hang, not
# a refusal -- a refusal returns in ~0.1s). The vitals cache can keep
# reporting "reachable" for up to _KERNEL_VITALS_TTL after such a hang, so
# that tax would otherwise be paid on every turn for a minute and a half.
# A localhost heartbeat completes in ~20ms; 0.25s is 10x headroom, and a
# missed heartbeat is free -- the next turn sends another.
HEARTBEAT_TIMEOUT = 0.25


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


def _cwd_is_inside_cog(cog_ws: Path, cwd: Path) -> bool:
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


def _git_branch(cwd: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, timeout=2, cwd=str(cwd),
        )
        if result.returncode == 0:
            branch = result.stdout.strip()
            return branch if branch else "no-git"
    except Exception:
        pass
    return "no-git"


_SESSIONS_STATE = _DATA_DIR / ".proprioception-sessions.json"
_MODELS_STATE = _DATA_DIR / ".proprioception-models.json"

# Friendly display names for known model IDs. Unknown IDs fall through to a
# generic prettifier (strip "claude-" prefix + trailing date, title-case family).
_MODEL_PRETTY = {
    "claude-opus-4-8": "Opus 4.8",
    "claude-opus-4-7": "Opus 4.7",
    "claude-opus-4-6": "Opus 4.6",
    "claude-sonnet-4-6": "Sonnet 4.6",
    "claude-sonnet-4-5": "Sonnet 4.5",
    "claude-haiku-4-5": "Haiku 4.5",
}

_DAY_PHASES = [
    (0, "late-night"), (5, "early-morning"), (8, "morning"), (12, "midday"),
    (14, "afternoon"), (17, "evening"), (21, "night"),
]


def _day_phase(hour: int) -> str:
    phase = "late-night"
    for start, name in _DAY_PHASES:
        if hour >= start:
            phase = name
    return phase


def _session_elapsed(session_id: str, now_utc: datetime) -> str:
    """Elapsed wall time since this session_id was first seen. Never raises."""
    if not session_id:
        return ""
    try:
        state = {}
        if _SESSIONS_STATE.exists():
            state = json.loads(_SESSIONS_STATE.read_text() or "{}")
        now_iso = now_utc.isoformat()
        # Prune entries older than 48h to bound file growth.
        cutoff = now_utc.timestamp() - 48 * 3600
        state = {
            sid: ts for sid, ts in state.items()
            if datetime.fromisoformat(ts).timestamp() > cutoff
        }
        first = state.get(session_id)
        if first is None:
            state[session_id] = now_iso
            _SESSIONS_STATE.parent.mkdir(parents=True, exist_ok=True)
            _SESSIONS_STATE.write_text(json.dumps(state))
            return "session_elapsed=0m (first prompt this session)"
        _SESSIONS_STATE.write_text(json.dumps(state))
        secs = int(now_utc.timestamp() - datetime.fromisoformat(first).timestamp())
        h, m = divmod(secs // 60, 60)
        return f"session_elapsed={h}h{m:02d}m" if h else f"session_elapsed={m}m"
    except Exception:
        return ""


def _temporal_line(session_id: str) -> str:
    """LOCAL wall-clock + day-phase + session elapsed. Never raises."""
    try:
        now_utc = datetime.now(timezone.utc)
        local = now_utc.astimezone()  # system tz
        tzname = local.tzname() or "local"
        phase = _day_phase(local.hour)
        parts = [f"local={local.strftime('%Y-%m-%d %H:%M')} {tzname} ({phase})"]
        elapsed = _session_elapsed(session_id, now_utc)
        if elapsed:
            parts.append(elapsed)
        return " | ".join(parts)
    except Exception:
        return ""


def _pretty_model(mid: str | None) -> str:
    """Map a model ID to a short display name. Never raises."""
    if not mid:
        return "?"
    known = _MODEL_PRETTY.get(mid)
    if known:
        return known
    try:
        s = mid[len("claude-"):] if mid.startswith("claude-") else mid
        segs = s.split("-")
        # Drop a trailing 8-digit date suffix (e.g. -20251001).
        if segs and segs[-1].isdigit() and len(segs[-1]) == 8:
            segs = segs[:-1]
        if not segs:
            return mid
        family = segs[0].capitalize()
        ver = ".".join(segs[1:])
        return f"{family} {ver}".strip()
    except Exception:
        return mid


def _find_transcript(session_id: str, transcript_path: str | None) -> str | None:
    """Resolve the session transcript JSONL. Prefer the hook-provided path;
    fall back to globbing ~/.claude/projects/*/<session_id>.jsonl. Never raises."""
    if transcript_path:
        return transcript_path
    if not session_id:
        return None
    try:
        base = Path.home() / ".claude" / "projects"
        hits = list(base.glob(f"*/{session_id}.jsonl"))
        return str(hits[0]) if hits else None
    except Exception:
        return None


def _current_model(transcript_path: str | None) -> str | None:
    """Model the LAST completed main-chain assistant turn ran on. Bounded
    tail-read of the transcript JSONL (last 256KB) — no full parse. Never raises."""
    try:
        if not transcript_path:
            return None
        p = Path(transcript_path)
        if not p.exists():
            return None
        size = p.stat().st_size
        with open(p, "rb") as f:
            f.seek(max(0, size - 262144))  # last 256KB is ample for one turn
            chunk = f.read()
        text = chunk.decode("utf-8", "ignore")
        for line in reversed(text.splitlines()):
            line = line.strip()
            if not line or line[0] != "{":
                continue  # skip blanks and the partial first line of the tail
            try:
                d = json.loads(line)
            except Exception:
                continue
            if d.get("type") != "assistant" or d.get("isSidechain"):
                continue  # main-chain assistant turns only (not sub-agents)
            msg = d.get("message")
            if isinstance(msg, dict):
                m = msg.get("model")
                if m and not str(m).startswith("<"):  # skip "<synthetic>"
                    return m
        return None
    except Exception:
        return None


def _model_segment(session_id: str, transcript_path: str | None) -> str:
    """`model=<name>` for the last turn, with a `(⚠ changed from X)` flag the
    turn the model changes within a session. Tracks last-seen per session_id.
    Never raises — returns "" on any failure so the header degrades silently."""
    cur = _current_model(transcript_path)
    if not cur:
        return ""
    pretty = _pretty_model(cur)
    flag = ""
    try:
        state = {}
        if _MODELS_STATE.exists():
            state = json.loads(_MODELS_STATE.read_text() or "{}")
        prev = state.get(session_id) if session_id else None
        if prev and prev != cur:
            flag = f" (⚠ changed from {_pretty_model(prev)})"
        if session_id and prev != cur:
            state[session_id] = cur
            # Bound file growth: keep the most-recent ~300 sessions (dicts are
            # insertion-ordered; the current session was just re-inserted last).
            if len(state) > 300:
                state = dict(list(state.items())[-300:])
            _MODELS_STATE.parent.mkdir(parents=True, exist_ok=True)
            _MODELS_STATE.write_text(json.dumps(state))
    except Exception:
        pass
    return f"model={pretty}{flag}"


def _latest_ctx_tokens(transcript_path: str | None) -> int | None:
    """Effective context tokens from the transcript's last usage block (input +
    both cache reads/writes — the real window occupancy). Bounded tail-read.
    Never raises."""
    try:
        if not transcript_path:
            return None
        p = Path(transcript_path)
        if not p.exists():
            return None
        size = p.stat().st_size
        with open(p, "rb") as f:
            f.seek(max(0, size - 262144))
            text = f.read().decode("utf-8", "ignore")
        for line in reversed(text.splitlines()):
            line = line.strip()
            if '"usage"' not in line or line[:1] != "{":
                continue
            try:
                d = json.loads(line)
            except Exception:
                continue
            u = (d.get("message") or {}).get("usage") or d.get("usage")
            if isinstance(u, dict):
                return (int(u.get("input_tokens") or 0)
                        + int(u.get("cache_read_input_tokens") or 0)
                        + int(u.get("cache_creation_input_tokens") or 0))
        return None
    except Exception:
        return None


def _context_pct_value(data: dict, transcript_path: str | None) -> float | None:
    """Raw context-window-used percentage (0-100), shared by the display
    segment and the heartbeat payload's context_usage field. Prefers the
    harness-provided percentage; falls back to transcript usage / window.
    Never raises; None on any failure or missing data."""
    try:
        cw = data.get("context_window") or {}
        pct = cw.get("used_percentage")
        if pct is None:
            size = int(cw.get("context_window_size") or 1000000)
            tok = cw.get("current_usage")
            if tok is None:
                tok = _latest_ctx_tokens(transcript_path)
            if not tok or size <= 0:
                return None
            pct = int(tok) * 100 / size
        return round(float(pct), 1)
    except Exception:
        return None


def _context_pct_seg(pct: float | None) -> str:
    """`ctx N%` of the context window — so the budget pressure is ambient every
    turn. Prefixes ⚠ when filling up (>=75%). One-turn-lagged like the model
    read. Never raises."""
    try:
        if pct is None:
            return ""
        p = round(pct)
        return f"{'⚠' if p >= 75 else ''}ctx {p}%"
    except Exception:
        return ""


_KERNEL_VITALS = _DATA_DIR / ".kernel-vitals.json"
_KERNEL_VITALS_PROBE = _PLUGIN_ROOT / "hooks" / "kernel-vitals-probe.py"
_KERNEL_VITALS_TTL = 90  # refresh the out-of-band vitals probe at most this often


def _maybe_refresh_kernel_vitals() -> None:
    """Fire the substrate-vitals probe detached if its cache is stale. Keeps the
    in-path hook network-free; the spawn returns immediately. Never raises.
    No-ops cleanly when the probe script isn't present (e.g. a partial
    install)."""
    try:
        stale = True
        if _KERNEL_VITALS.exists():
            stale = (datetime.now(timezone.utc).timestamp()
                     - _KERNEL_VITALS.stat().st_mtime) > _KERNEL_VITALS_TTL
        if stale and _KERNEL_VITALS_PROBE.exists():
            subprocess.Popen(
                ["python3", str(_KERNEL_VITALS_PROBE)],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL, start_new_session=True,
            )
    except Exception:
        pass


def _read_kernel_vitals() -> dict:
    """Read the probe's cached vitals dict whole (not just the formatted
    line) so callers can also inspect kernel.reachable for the heartbeat
    gate below. The probe (kernel-vitals-probe.py) is the single writer;
    this is just a read. No network. Never raises."""
    try:
        if not _KERNEL_VITALS.exists():
            return {}
        d = json.loads(_KERNEL_VITALS.read_text() or "{}")
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _kernel_vitals_seg(vit: dict) -> str:
    """The pre-formatted vitals line from the probe cache. No network,
    no re-formatting -- kernel-vitals-probe.py is the single formatter.
    Never raises."""
    try:
        return vit.get("line", "")
    except Exception:
        return ""


def _maybe_heartbeat(vit: dict, session_id: str, context_pct: float | None) -> None:
    """Session heartbeat fallback (#17): POST /v1/sessions/{id}/heartbeat,
    the REST counterpart of cog_heartbeat_session, but ONLY when the
    vitals cache we just read already shows the kernel reachable -- i.e.
    a round-trip some probe cycle already completed. This adds zero new
    probes: if the cache says unreachable (or doesn't exist yet), this
    is a no-op, full stop. Fires at most once per call (this hook runs
    once per UserPromptSubmit turn, so that bounds it to once per turn).
    Never raises; the response is read and discarded."""
    try:
        if not session_id:
            return
        if not vit.get("kernel", {}).get("reachable"):
            return
        body: dict = {"status": "active"}
        if context_pct is not None:
            body["context_usage"] = context_pct
        req = urllib.request.Request(
            f"{KERNEL_URL}/v1/sessions/{urllib.parse.quote(session_id, safe='')}/heartbeat",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=HEARTBEAT_TIMEOUT) as r:
            r.read()
    except (urllib.error.URLError, OSError, ValueError):
        pass
    except Exception:
        pass


def _emit_no_op(event_name: str) -> None:
    """Emit an empty context block (no-op for the agent)."""
    out = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": "",
        }
    }
    json.dump(out, sys.stdout)


def main() -> int:
    # Read hook input.
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    event_name = data.get("hook_event_name", "UserPromptSubmit")
    cwd_str = data.get("cwd", os.getcwd())
    try:
        cwd = Path(cwd_str).resolve()
    except Exception:
        cwd = Path.cwd().resolve()

    # Locate cog workspace.
    cog_ws = _find_cog_workspace()

    # If inside cog workspace, skip — workspace hooks already inject context.
    if cog_ws is not None and _cwd_is_inside_cog(cog_ws, cwd):
        sys.exit(0)

    # If no cog workspace found at all, still emit something lightweight.
    # (The stub is useful even in fully non-cog contexts.)

    branch = _git_branch(cwd)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%MZ")

    session_id = data.get("session_id", "")
    transcript_path = _find_transcript(session_id, data.get("transcript_path"))

    lines = ["<cogos_proprioception>"]
    if branch != "no-git":
        lines.append(f"  branch={branch} | {ts} | cwd={cwd}")
    else:
        lines.append(f"  {ts} | cwd={cwd} | no-git-repo")
    _maybe_refresh_kernel_vitals()
    temporal = _temporal_line(session_id)
    model_seg = _model_segment(session_id, transcript_path)
    context_pct = _context_pct_value(data, transcript_path)
    ctx_seg = _context_pct_seg(context_pct)
    second_parts = [p for p in (temporal, model_seg, ctx_seg) if p]
    if second_parts:
        lines.append("  " + " | ".join(second_parts))
    vit = _read_kernel_vitals()
    vitals_seg = _kernel_vitals_seg(vit)
    if vitals_seg:
        lines.append("  " + vitals_seg)
    _maybe_heartbeat(vit, session_id, context_pct)
    lines.append("</cogos_proprioception>")

    context = "\n".join(lines)
    out = {
        "hookSpecificOutput": {
            "hookEventName": event_name,
            "additionalContext": context,
        },
    }
    json.dump(out, sys.stdout)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        sys.stderr.write(f"[user-scope-proprioception] unexpected error: {e}\n")
        # Emit empty no-op to satisfy hook contract.
        try:
            out = {"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": ""}}
            json.dump(out, sys.stdout)
        except Exception:
            pass
        sys.exit(0)
