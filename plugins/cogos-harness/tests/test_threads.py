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

    def test_add_rejects_empty_predicate(self):
        r = run_cli("add", "--what", "x", "--why", "y", "--predicate", "",
                     "--expected-by", "1h", "--id", "emptypred", env_extra=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("must not be empty", r.stderr)
        # and it must not have been written to state at all
        r = run_cli("list", "--all", env_extra=self.env)
        self.assertNotIn("emptypred", r.stdout)

    def test_add_rejects_whitespace_only_predicate(self):
        r = run_cli("add", "--what", "x", "--why", "y", "--predicate", "   ",
                     "--expected-by", "1h", "--id", "wspred", env_extra=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("must not be empty", r.stderr)

    def test_concurrent_add_does_not_lose_registrations(self):
        # Reproduces the lost-write race: N concurrent `threads add`
        # invocations against a fresh registry must all survive. Before the
        # locked_state() fix this reliably dropped entries (last-writer-wins
        # on the unguarded read-modify-write) while every process still
        # printed "registered" and exited 0.
        import concurrent.futures
        n = 8
        ids = [f"r{i}" for i in range(n)]

        def add_one(tid):
            return run_cli("add", "--what", f"concurrent {tid}", "--why", "y",
                            "--predicate", "true", "--expected-by", "1h",
                            "--id", tid, env_extra=self.env)

        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as pool:
            results = list(pool.map(add_one, ids))

        for r in results:
            self.assertEqual(r.returncode, 0, r.stderr)

        r = run_cli("list", "--all", "--json", env_extra=self.env)
        self.assertEqual(r.returncode, 0)
        registered = {t["id"] for t in json.loads(r.stdout)}
        self.assertEqual(registered, set(ids),
                          f"lost registrations: expected {sorted(ids)}, got {sorted(registered)}")


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

    def test_run_predicate_unbounded_output_is_cheap_and_bounded(self):
        # A predicate that floods stdout must not blow the timeout or buffer
        # gigabytes into this process -- output is DEVNULL'd, never
        # captured, since nothing reads it. `cat /dev/zero` never exits on
        # its own, so this also exercises the timeout path with a predicate
        # that produces unbounded bytes until it's killed.
        start = core.time.monotonic()
        r = core.run_predicate("cat /dev/zero", timeout=0.5)
        elapsed = core.time.monotonic() - start
        self.assertFalse(r.resolved)
        self.assertEqual(r.note, "timeout")
        # generous ceiling -- was 9+ seconds when output was captured
        self.assertLess(elapsed, 3.0, f"took {elapsed:.2f}s; output capture likely regressed")

    def test_run_predicate_non_utf8_output_is_not_misreported(self):
        # A predicate that exits 0 but emits non-UTF-8 bytes must still be
        # reported resolved -- output is never decoded, only the exit code
        # is read.
        r = core.run_predicate("head -c 64 /dev/urandom >/dev/null; exit 0", timeout=2)
        self.assertTrue(r.resolved)
        self.assertEqual(r.note, "")

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

    def test_derive_status_empty_predicate_is_never_resolved(self):
        # A thread that lost its predicate (hand-edit, partial write, future
        # schema drift) must never self-report "all clear" -- `/bin/sh -c
        # ''` exits 0, which would make it resolved if run at all. It must
        # be reported as an explicit unresolved result, and it must be
        # capable of going orphaned once overdue (unlike a healthy silence).
        opened = core.now_utc() - core.timedelta(seconds=5)
        thread = {"id": "x", "predicate": "", "opened_at": core.iso(opened), "expected_by": "1s"}
        st = core.derive_status(thread, timeout=2)
        self.assertFalse(st.resolved)
        self.assertTrue(st.overdue)
        self.assertTrue(st.orphaned)
        self.assertIn("predicate", st.predicate_note)

    def test_derive_status_missing_predicate_key_is_never_resolved(self):
        opened = core.now_utc() - core.timedelta(seconds=5)
        thread = {"id": "x", "opened_at": core.iso(opened), "expected_by": "1s"}
        st = core.derive_status(thread, timeout=2)
        self.assertFalse(st.resolved)
        self.assertTrue(st.orphaned)

    def test_derive_status_skips_predicate_when_not_due(self):
        # skip_predicate_if_not_due=True (the per-turn hook's mode): a
        # thread nowhere near its deadline must never actually invoke the
        # predicate, since the exit code can't change orphaned/overdue
        # either way. Use a predicate that would time out if it ran at all,
        # with a timeout far shorter than that predicate needs, and confirm
        # it still comes back near-instantly and non-orphaned.
        opened = core.now_utc()
        thread = {
            "id": "x", "predicate": "sleep 30",
            "opened_at": core.iso(opened), "expected_by": "1h",
        }
        start = core.time.monotonic()
        st = core.derive_status(thread, timeout=5, skip_predicate_if_not_due=True)
        elapsed = core.time.monotonic() - start
        self.assertLess(elapsed, 1.0, "predicate should never have been invoked")
        self.assertFalse(st.overdue)
        self.assertFalse(st.orphaned)
        self.assertIn("skipped", st.predicate_note)

    def test_derive_status_still_runs_predicate_when_overdue_even_in_skip_mode(self):
        # skip_predicate_if_not_due must not suppress the predicate once a
        # thread actually is past its deadline -- that's the one case its
        # exit code still matters.
        opened = core.now_utc() - core.timedelta(seconds=5)
        thread = {
            "id": "x", "predicate": "true",
            "opened_at": core.iso(opened), "expected_by": "1s",
        }
        st = core.derive_status(thread, timeout=2, skip_predicate_if_not_due=True)
        self.assertTrue(st.resolved)
        self.assertFalse(st.orphaned)  # resolved, so never orphaned even though overdue

    def test_derive_status_skip_mode_does_not_change_check_command_behavior(self):
        # threads check never passes skip_predicate_if_not_due, so its
        # resolved/orphaned reporting for a not-yet-due thread must still
        # reflect an actually-executed predicate (default False == old
        # behavior, unchanged).
        opened = core.now_utc()
        thread = {
            "id": "x", "predicate": "false",
            "opened_at": core.iso(opened), "expected_by": "1h",
        }
        st = core.derive_status(thread, timeout=2)
        self.assertEqual(st.predicate_note, "")
        self.assertFalse(st.resolved)


    # ---------------------------------------------------------- F6 --
    # opened_at unparseable + expected_by a *duration* would otherwise
    # recompute `now + duration` fresh on every call -- a deadline that
    # recedes forever and can never be reached, making the thread
    # permanently invisible to the warn hook. Defense-in-depth mirrors the
    # blank-predicate case: treat it as already overdue-eligible.

    def test_derive_status_unparseable_opened_at_with_duration_expected_by_is_overdue(self):
        thread = {
            "id": "x", "predicate": "false",
            "opened_at": "not-a-timestamp", "expected_by": "1d",
        }
        st = core.derive_status(thread, timeout=2)
        self.assertTrue(st.overdue)
        self.assertTrue(st.orphaned)

    def test_derive_status_missing_opened_at_with_duration_expected_by_is_overdue(self):
        thread = {"id": "x", "predicate": "false", "expected_by": "1h"}
        st = core.derive_status(thread, timeout=2)
        self.assertTrue(st.overdue)
        self.assertTrue(st.orphaned)

    def test_derive_status_resolved_thread_with_unparseable_opened_at_still_never_orphaned(self):
        # The overdue-eligible override must not itself force orphaned --
        # a resolved predicate is still never orphaned, same invariant as
        # test_derive_status_resolved_thread_is_never_orphaned_even_if_overdue.
        thread = {
            "id": "x", "predicate": "true",
            "opened_at": "garbage", "expected_by": "1h",
        }
        st = core.derive_status(thread, timeout=2)
        self.assertTrue(st.resolved)
        self.assertFalse(st.orphaned)

    def test_derive_status_unparseable_opened_at_with_absolute_expected_by_is_unaffected(self):
        # The F6 defense-in-depth is scoped to DURATION expected_by only
        # -- an absolute ISO8601 expected_by is computed independently of
        # opened_at and does not recede regardless, so a corrupt
        # opened_at paired with a not-yet-due absolute deadline must
        # behave exactly as before: not overdue.
        future = core.iso(core.now_utc() + core.timedelta(hours=1))
        thread = {"id": "x", "predicate": "false", "opened_at": "garbage", "expected_by": future}
        st = core.derive_status(thread, timeout=2)
        self.assertFalse(st.overdue)
        self.assertFalse(st.orphaned)

    def test_derive_status_parseable_opened_at_with_duration_expected_by_is_unaffected(self):
        # Sanity check that the F6 override only fires when opened_at
        # itself fails to parse -- a normal, healthy thread with a
        # parseable opened_at and a duration expected_by must behave
        # exactly as before (not yet overdue, since it was just opened).
        opened = core.now_utc()
        thread = {
            "id": "x", "predicate": "false",
            "opened_at": core.iso(opened), "expected_by": "1h",
        }
        st = core.derive_status(thread, timeout=2)
        self.assertFalse(st.overdue)
        self.assertFalse(st.orphaned)



    # ---------------------------------------------------------- F7 --
    # SCHEMA_VERSION was written on every save but never read back on
    # load -- a future schema bump would parse silently under old-schema
    # assumptions instead of failing loudly.

    def test_load_state_future_schema_version_is_corrupt(self):
        p = Path(tempfile.mkdtemp()) / "threads.json"
        p.write_text(json.dumps({"version": core.SCHEMA_VERSION + 1, "threads": []}), encoding="utf-8")
        with self.assertRaises(core.CorruptStateError):
            core.load_state(p)

    def test_load_state_current_schema_version_loads_fine(self):
        p = Path(tempfile.mkdtemp()) / "threads.json"
        p.write_text(json.dumps({"version": core.SCHEMA_VERSION, "threads": []}), encoding="utf-8")
        data = core.load_state(p)
        self.assertEqual(data["version"], core.SCHEMA_VERSION)

    def test_load_state_missing_version_key_loads_fine(self):
        # A version key is only enforced when PRESENT -- a state file
        # that predates this field entirely (or one some other tool wrote
        # without it) must not be rejected on that basis alone.
        p = Path(tempfile.mkdtemp()) / "threads.json"
        p.write_text(json.dumps({"threads": []}), encoding="utf-8")
        data = core.load_state(p)
        self.assertEqual(data["threads"], [])



    # ---------------------------------------------------------- F8 --
    # A predicate that backgrounds or forks a grandchild the shell
    # doesn't wait on used to survive the timeout kill (only the direct
    # /bin/sh child was signaled) -- one leaked, reparented process per
    # turn per overdue slow/hanging thread. run_predicate now runs the
    # predicate in its own process group (start_new_session=True) and
    # kills the WHOLE group via os.killpg on timeout.

    def test_run_predicate_timeout_kills_backgrounded_descendant(self):
        marker = f"threads_core_leak_test_{os.getpid()}_{int(core.time.time() * 1000)}"
        # The outer predicate backgrounds a long-sleeping python3 process
        # (identifiable via the marker in its argv) that the shell does
        # NOT wait on, then itself blocks past the timeout -- reproducing
        # exactly the "grandchild the shell doesn't wait on" leak F8
        # describes.
        cmd = f"python3 -c 'import time; time.sleep(30)' {marker} & sleep 30"
        try:
            r = core.run_predicate(cmd, timeout=0.3)
            self.assertFalse(r.resolved)
            self.assertEqual(r.note, "timeout")

            deadline = core.time.monotonic() + 3.0
            leaked = True
            while core.time.monotonic() < deadline:
                check = subprocess.run(
                    ["pgrep", "-f", marker], capture_output=True, text=True
                )
                if check.returncode != 0:  # pgrep: no matching process
                    leaked = False
                    break
                core.time.sleep(0.2)
            self.assertFalse(
                leaked,
                f"backgrounded descendant matching {marker!r} survived the "
                f"predicate timeout -- process group was not fully killed",
            )
        finally:
            # Best-effort cleanup regardless of assertion outcome -- never
            # leave a real sleep-30 process behind because a test failed.
            subprocess.run(["pkill", "-9", "-f", marker], capture_output=True)




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

    def test_not_due_thread_never_pays_predicate_latency(self):
        # The cost-side counterpart to the silence test above: a thread with
        # a deadline nowhere near due must not just stay silent, it must
        # come back fast -- its predicate's exit code cannot affect
        # `orphaned` (which requires overdue), so the hook must skip
        # running it (skip_predicate_if_not_due) rather than paying the
        # full per-predicate timeout every single turn for the thread's
        # entire lifetime. Uses a predicate timeout the hook would have to
        # wait out if it actually ran the predicate, to make a regression
        # here fail loudly rather than by a hair.
        run_cli("add", "--what", "distant deadline", "--why", "y",
                 "--predicate", "sleep 30", "--expected-by", "1w", "--id", "distant",
                 env_extra=self.env)
        env = dict(self.env, COGOS_THREADS_PREDICATE_TIMEOUT="3")
        import time
        start = time.monotonic()
        r = run_hook(env_extra=env)
        elapsed = time.monotonic() - start
        self.assertEqual(r.returncode, 0)
        self.assertEqual(r.stdout, "")
        self.assertLess(elapsed, 2.0, f"hook took {elapsed:.2f}s; predicate was likely run unnecessarily")

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
