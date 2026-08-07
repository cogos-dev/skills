#!/usr/bin/env python3
"""Self-tests for the threads registry: the CLI (bin/threads), the shared
library (lib/threads_core.py), and the warn hook (hooks/threads-warn.py).

Run directly: `python3 tests/test_threads.py -v`
No third-party dependencies -- stdlib unittest only, per this plugin's
"python3 on PATH" requirement.

Every state-file fixture in this file lives under a per-test tempdir via
COGOS_THREADS_STATE -- these tests never touch the operator's real
~/.cog/status/threads.json.

The hook-silence tests are the load-bearing ones: they assert BYTE-EXACT
empty stdout for every failure mode the build's hard gate calls out
(missing file, corrupt file, predicate timeout, predicate error) plus the
two "nothing wrong" cases (no threads registered, one healthy thread) --
because the gate this hook exists under is "silent unless something is
wrong", and the only way to trust that is to check it directly, per input,
rather than infer it from the code.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
LIB_DIR = PLUGIN_ROOT / "lib"
BIN_THREADS = PLUGIN_ROOT / "bin" / "threads"
HOOK_WARN = PLUGIN_ROOT / "hooks" / "threads-warn.py"

sys.path.insert(0, str(LIB_DIR))
import threads_core as core  # noqa: E402


def run_cli(*args, env_extra=None, input_text=None):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(BIN_THREADS), *args],
        capture_output=True, text=True, timeout=15, env=env, input=input_text,
    )


def run_hook(env_extra=None, event="UserPromptSubmit"):
    env = dict(os.environ)
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, str(HOOK_WARN)],
        capture_output=True, text=True, timeout=15, env=env,
        input=json.dumps({"hook_event_name": event}),
    )


class TempState(unittest.TestCase):
    """Base: gives every test its own throwaway state file path, never the
    operator's real one."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.state_path = Path(self._tmp.name) / "threads.json"
        self.env = {"COGOS_THREADS_STATE": str(self.state_path)}

    def tearDown(self):
        self._tmp.cleanup()


# --------------------------------------------------------------- CLI tests --

class TestCliRoundTrip(TempState):
    def test_add_list_check_close(self):
        r = run_cli("add", "--what", "PR verdict", "--why", "blocks merge",
                     "--predicate", "true", "--expected-by", "2h",
                     "--id", "t1", env_extra=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("registered thread 't1'", r.stdout)

        r = run_cli("list", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("t1", r.stdout)
        self.assertIn("[open", r.stdout)

        r = run_cli("check", "t1", env_extra=self.env)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn("RESOLVED", r.stdout)

        r = run_cli("close", "t1", "--reason", "done", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("closed 't1'", r.stdout)

        r = run_cli("list", env_extra=self.env)
        self.assertIn("(no open threads)", r.stdout)
        r = run_cli("list", "--all", env_extra=self.env)
        self.assertIn("t1", r.stdout)
        self.assertIn("[closed", r.stdout)

    def test_add_rejects_unparsable_expected_by(self):
        r = run_cli("add", "--what", "x", "--why", "y", "--predicate", "true",
                     "--expected-by", "not-a-time-or-duration", env_extra=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("neither an ISO8601", r.stderr)

    def test_add_rejects_duplicate_id(self):
        run_cli("add", "--what", "x", "--why", "y", "--predicate", "true",
                 "--expected-by", "1h", "--id", "dup", env_extra=self.env)
        r = run_cli("add", "--what", "x2", "--why", "y", "--predicate", "true",
                     "--expected-by", "1h", "--id", "dup", env_extra=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("already exists", r.stderr)

    def test_check_orphan_sets_nonzero_exit(self):
        run_cli("add", "--what", "x", "--why", "y", "--predicate", "false",
                 "--expected-by", "1s", "--id", "will-orphan", env_extra=self.env)
        import time
        time.sleep(1.2)
        r = run_cli("check", env_extra=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertIn("ORPHAN", r.stdout)

    def test_close_unknown_id_fails(self):
        r = run_cli("close", "nope", env_extra=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no such thread", r.stderr)

    def test_list_missing_file_is_empty_not_error(self):
        r = run_cli("list", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("(no open threads)", r.stdout)

    def test_cli_refuses_corrupt_file_never_resets_it(self):
        self.state_path.write_text("{not valid json", encoding="utf-8")
        before = self.state_path.read_text(encoding="utf-8")
        r = run_cli("list", env_extra=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("corrupt", r.stderr)
        self.assertIn("Never auto-reset", r.stderr)
        after = self.state_path.read_text(encoding="utf-8")
        self.assertEqual(before, after, "corrupt file must be left untouched")


# ------------------------------------------------------------- library tests --

class TestLibrary(unittest.TestCase):
    def test_load_state_missing_file_is_empty_default(self):
        p = Path(tempfile.mkdtemp()) / "nope.json"
        data = core.load_state(p)
        self.assertEqual(data, {"version": 1, "threads": []})

    def test_load_state_empty_file_is_corrupt(self):
        p = Path(tempfile.mkdtemp()) / "threads.json"
        p.write_text("", encoding="utf-8")
        with self.assertRaises(core.CorruptStateError):
            core.load_state(p)

    def test_load_state_bad_json_is_corrupt(self):
        p = Path(tempfile.mkdtemp()) / "threads.json"
        p.write_text("{oops", encoding="utf-8")
        with self.assertRaises(core.CorruptStateError):
            core.load_state(p)

    def test_load_state_wrong_shape_is_corrupt(self):
        p = Path(tempfile.mkdtemp()) / "threads.json"
        p.write_text(json.dumps({"threads": "not-a-list"}), encoding="utf-8")
        with self.assertRaises(core.CorruptStateError):
            core.load_state(p)

    def test_atomic_write_survives_a_reader_mid_write(self):
        # Not a true concurrency test (that needs real threads/processes),
        # but proves the write path never leaves a partial target: the
        # target file is either the old complete content or the new
        # complete content, never a torn write, because atomic_write always
        # goes through a tempfile + os.replace.
        p = Path(tempfile.mkdtemp()) / "threads.json"
        core.atomic_write({"version": 1, "threads": []}, p)
        core.atomic_write({"version": 1, "threads": [{"id": "a"}]}, p)
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertEqual([t["id"] for t in data["threads"]], ["a"])
        # no leftover tempfiles
        leftovers = [f for f in p.parent.iterdir() if f.name.startswith(".threads.json.tmp-")]
        self.assertEqual(leftovers, [])

    def test_parse_expected_by_duration_and_timestamp(self):
        opened = core.now_utc()
        d = core.parse_expected_by("2h", opened)
        self.assertIsNotNone(d)
        self.assertAlmostEqual((d - opened).total_seconds(), 7200, delta=1)

        ts = core.iso(opened)
        d2 = core.parse_expected_by(ts, opened)
        self.assertIsNotNone(d2)

        self.assertIsNone(core.parse_expected_by("garbage", opened))

    def test_run_predicate_resolved_on_exit_zero(self):
        r = core.run_predicate("true", timeout=2)
        self.assertTrue(r.resolved)
        self.assertEqual(r.note, "")

    def test_run_predicate_unresolved_on_nonzero_exit(self):
        r = core.run_predicate("false", timeout=2)
        self.assertFalse(r.resolved)

    def test_run_predicate_times_out_never_raises(self):
        r = core.run_predicate("sleep 5", timeout=0.3)
        self.assertFalse(r.resolved)
        self.assertEqual(r.note, "timeout")

    def test_run_predicate_swallows_exceptions(self):
        # Force an internal error path (not a shell nonzero-exit, an actual
        # exception in subprocess.run) by pointing at a timeout value that
        # is invalid for the underlying API, and confirm run_predicate still
        # returns a PredicateResult rather than propagating.
        r = core.run_predicate("true", timeout=-1)
        self.assertFalse(r.resolved)
        self.assertTrue(r.note == "timeout" or r.note.startswith("error"))

    def test_derive_status_orphan_requires_unresolved_and_overdue(self):
        opened = core.now_utc() - core.timedelta(seconds=5)
        thread = {
            "id": "x", "predicate": "false",
            "opened_at": core.iso(opened), "expected_by": "1s",
        }
        st = core.derive_status(thread, timeout=2)
        self.assertFalse(st.resolved)
        self.assertTrue(st.overdue)
        self.assertTrue(st.orphaned)

    def test_derive_status_resolved_thread_is_never_orphaned_even_if_overdue(self):
        opened = core.now_utc() - core.timedelta(seconds=5)
        thread = {
            "id": "x", "predicate": "true",
            "opened_at": core.iso(opened), "expected_by": "1s",
        }
        st = core.derive_status(thread, timeout=2)
        self.assertTrue(st.resolved)
        self.assertFalse(st.orphaned)

    def test_derive_status_unresolved_but_not_overdue_is_not_orphaned(self):
        opened = core.now_utc()
        thread = {
            "id": "x", "predicate": "false",
            "opened_at": core.iso(opened), "expected_by": "1h",
        }
        st = core.derive_status(thread, timeout=2)
        self.assertFalse(st.resolved)
        self.assertFalse(st.overdue)
        self.assertFalse(st.orphaned)


# ------------------------------------------------------------ hook tests --

class TestWarnHookSilence(TempState):
    """Every scenario the build's hard gate calls out for the hook,
    checked directly against the hook's actual stdout."""

    def test_nothing_registered_is_silent(self):
        r = run_hook(env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_missing_state_file_is_silent(self):
        self.assertFalse(self.state_path.exists())
        r = run_hook(env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_corrupt_state_file_is_silent(self):
        self.state_path.write_text("{not json at all", encoding="utf-8")
        r = run_hook(env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_empty_state_file_is_silent(self):
        self.state_path.write_text("", encoding="utf-8")
        r = run_hook(env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_one_healthy_thread_is_silent(self):
        run_cli("add", "--what", "healthy thing", "--why", "y",
                 "--predicate", "true", "--expected-by", "2h", "--id", "healthy",
                 env_extra=self.env)
        r = run_hook(env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_unresolved_but_not_overdue_is_silent(self):
        run_cli("add", "--what", "still waiting", "--why", "y",
                 "--predicate", "false", "--expected-by", "1h", "--id", "waiting",
                 env_extra=self.env)
        r = run_hook(env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_predicate_timeout_but_not_overdue_is_silent(self):
        run_cli("add", "--what", "slow but not due", "--why", "y",
                 "--predicate", "sleep 5", "--expected-by", "1h", "--id", "slow-ok",
                 env_extra=self.env)
        env = dict(self.env, COGOS_THREADS_PREDICATE_TIMEOUT="0.3")
        r = run_hook(env_extra=env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_predicate_error_but_not_overdue_is_silent(self):
        run_cli("add", "--what", "bad cmd not due", "--why", "y",
                 "--predicate", "nonexistent_command_xyz", "--expected-by", "1h",
                 "--id", "err-ok", env_extra=self.env)
        r = run_hook(env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")

    def test_closed_orphan_stays_silent(self):
        run_cli("add", "--what", "was orphaned", "--why", "y", "--predicate", "false",
                 "--expected-by", "1s", "--id", "closed-orphan", env_extra=self.env)
        import time
        time.sleep(1.2)
        run_cli("close", "closed-orphan", env_extra=self.env)
        r = run_hook(env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")


class TestWarnHookSpeaksWhenWarranted(TempState):
    def test_one_orphan_produces_a_block(self):
        run_cli("add", "--what", "PR 118 review verdict", "--why", "blocks merge",
                 "--predicate", "false", "--expected-by", "1s", "--id", "pr118",
                 env_extra=self.env)
        import time
        time.sleep(1.2)
        r = run_hook(env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertNotEqual(r.stdout.strip(), "")
        payload = json.loads(r.stdout)
        block = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("pr118", block)
        self.assertIn("threads_warn", block)
        self.assertEqual(payload["hookSpecificOutput"]["hookEventName"], "UserPromptSubmit")

    def test_orphan_via_timeout_produces_a_block(self):
        run_cli("add", "--what", "hangs", "--why", "y", "--predicate", "sleep 5",
                 "--expected-by", "1s", "--id", "hangs", env_extra=self.env)
        import time
        time.sleep(1.2)
        env = dict(self.env, COGOS_THREADS_PREDICATE_TIMEOUT="0.3")
        r = run_hook(env_extra=env)
        self.assertEqual(r.returncode, 0)
        self.assertNotEqual(r.stdout.strip(), "")
        self.assertIn("hangs", r.stdout)
        self.assertIn("timeout", r.stdout)

    def test_healthy_and_orphan_mixed_reports_only_the_orphan(self):
        run_cli("add", "--what", "fine", "--why", "y", "--predicate", "true",
                 "--expected-by", "2h", "--id", "fine", env_extra=self.env)
        run_cli("add", "--what", "stuck", "--why", "y", "--predicate", "false",
                 "--expected-by", "1s", "--id", "stuck", env_extra=self.env)
        import time
        time.sleep(1.2)
        r = run_hook(env_extra=self.env)
        payload = json.loads(r.stdout)
        block = payload["hookSpecificOutput"]["additionalContext"]
        self.assertIn("stuck", block)
        self.assertNotIn("fine", block)


class TestGatePrScaffoldDisabledByDefault(TempState):
    """The enforcement-tier hook itself, per the build's requirement that
    it's present but inert unless explicitly armed."""

    def _run_gate(self, command, env_extra=None):
        env = dict(os.environ)
        if env_extra:
            env.update(env_extra)
        gate = PLUGIN_ROOT / "hooks" / "threads-gate-pr.py"
        payload = {"tool_name": "Bash", "tool_input": {"command": command}}
        return subprocess.run(
            [sys.executable, str(gate)], capture_output=True, text=True,
            timeout=10, env=env, input=json.dumps(payload),
        )

    def test_default_off_allows_even_with_no_open_threads(self):
        r = self._run_gate("gh pr create --title x --body y", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        self.assertEqual(json.loads(r.stdout), {})

    def test_non_matching_command_always_allowed(self):
        r = self._run_gate("ls -la", env_extra=self.env)
        self.assertEqual(json.loads(r.stdout), {})

    def test_armed_and_no_open_threads_denies(self):
        cfg_dir = Path(tempfile.mkdtemp())
        cfg_path = cfg_dir / "threads-config.json"
        cfg_path.write_text(json.dumps({"enforce_pr_create_thread": True}), encoding="utf-8")
        env = dict(self.env, COGOS_THREADS_CONFIG=str(cfg_path))
        r = self._run_gate("gh pr create --title x --body y", env_extra=env)
        resp = json.loads(r.stdout)
        self.assertEqual(resp["hookSpecificOutput"]["permissionDecision"], "deny")

    def test_armed_and_open_thread_present_allows(self):
        run_cli("add", "--what", "x", "--why", "y", "--predicate", "true",
                 "--expected-by", "1h", "--id", "t1", env_extra=self.env)
        cfg_dir = Path(tempfile.mkdtemp())
        cfg_path = cfg_dir / "threads-config.json"
        cfg_path.write_text(json.dumps({"enforce_pr_create_thread": True}), encoding="utf-8")
        env = dict(self.env, COGOS_THREADS_CONFIG=str(cfg_path))
        r = self._run_gate("gh pr create --title x --body y", env_extra=env)
        self.assertEqual(json.loads(r.stdout), {})

    def test_armed_but_corrupt_registry_fails_open(self):
        self.state_path.write_text("{not json", encoding="utf-8")
        cfg_dir = Path(tempfile.mkdtemp())
        cfg_path = cfg_dir / "threads-config.json"
        cfg_path.write_text(json.dumps({"enforce_pr_create_thread": True}), encoding="utf-8")
        env = dict(self.env, COGOS_THREADS_CONFIG=str(cfg_path))
        r = self._run_gate("gh pr create --title x --body y", env_extra=env)
        self.assertEqual(json.loads(r.stdout), {})


if __name__ == "__main__":
    unittest.main(verbosity=2)
