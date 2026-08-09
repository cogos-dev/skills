---
name: memory-janitor
description: "Check-and-repair loop for the memory-janitor Stop hook: dispatch a bounded background Haiku lane to compact an over-threshold project MEMORY.md against the standing directive, grade its output deterministically with check.py, and repair on defects — up to 2 rounds — without ever compacting inline. Use when the memory-janitor Stop hook blocks a turn with a size-threshold reason, or when explicitly asked to run or check the memory janitor."
version: 1.0.0
author: myrgic
tags: [cogos, session-management, memory, hooks]
provenance: "promoted from an operator-local seat, 2026-08-08"
---

# Skill: memory-janitor

The check-and-repair loop for the `memory-janitor.py` Stop hook. The hook only detects and blocks once; this skill is what the pilot follows when it fires — dispatch a bounded Haiku lane to compact the project's `MEMORY.md`, grade its output deterministically, and repair on defects, all without compacting inline.

<invocation>
MUST dispatch the compaction work to a background subagent using the Agent tool with `run_in_background: true` and `model: "haiku"` (or any equivalent background-subagent dispatch your harness provides) — never compact MEMORY.md inline in the pilot's own turn.
MUST pass the subagent the `directive` path and the `target file` path exactly as printed in the triggering hook's block reason — never `${CLAUDE_PLUGIN_ROOT}`. That token only expands inside `hooks.json`'s own JSON args; it is not a shell variable and is not set in a Bash-tool subprocess or a subagent's environment.
MUST also pass the subagent the three numbers from the block reason (`trigger`, `target`, `floor`) — `directive.md` hardcodes none of them; it operates on whatever numbers its dispatcher hands it.
MUST run the checker (`check.py`, path also taken from the block reason) only after the subagent's completion notification arrives, never before.
MUST NOT arm a wait or monitor for the subagent's completion from within this skill — the pilot's own turn-loop owns that notification; the janitor lane completes and exits.
MUST stop after 2 repair rounds, pass or fail, and relay the final checker line to the operator either way.
</invocation>

## When this fires

The `memory-janitor.py` Stop hook blocks the turn once when the current project's `MEMORY.md` crosses a size threshold, and re-arms after a 6-hour cooldown or once the file drops back under threshold. Its `reason` text is this skill's primary input — read it before doing anything else. The hook self-locates its own plugin root and resolves everything below at block time, as absolute paths and live numbers, so nothing here needs to be re-derived:

```
<memory-janitor> MEMORY.md is <size> bytes (trigger <T>, target <Ta>, floor <F>). ...
checker: /path/to/cogos-harness/skills/memory-janitor/check.py
directive: /path/to/cogos-harness/skills/memory-janitor/directive.md
target file: /path/to/.claude/projects/<sanitized-cwd>/memory/MEMORY.md
project dir: <the raw project directory the hook resolved>
numbers: trigger=<T> target=<Ta> floor=<F>
```

Use these five values verbatim throughout the procedure below. No `${CLAUDE_PLUGIN_ROOT}` appears anywhere in this skill: that token only expands inside `hooks.json`'s own JSON args, never in a shell command or a subagent's prompt — the hook already resolved its own path once (the same `Path(__file__).resolve()` trick `check.py` already used, which is exactly why the hook now owns it and hands the result down) and this skill just relays what it printed.

## Procedure

### Round 1

1. **Dispatch.** Start ONE background subagent via the Agent tool, `run_in_background: true`, `model: "haiku"` (or any equivalent background-subagent dispatch your harness provides). Its prompt is a pointer, not a summary:
   - the `directive` path from the block reason
   - the `target file` path from the block reason
   - the three numbers from the block reason, stated plainly (e.g. "trigger=<T> target=<Ta> floor=<F>") — `directive.md` reads its SKIP condition and compaction target from these, not a built-in default

   Do not quote the directive's rules into the dispatch prompt — the subagent reads the file itself. Do not summarize the target file's contents either; the subagent reads that too. Pointers only.

2. **Wait for completion.** This skill does not poll or monitor. End your turn, or continue other work, and let the harness's own background-task notification tell you when the subagent finishes. Picking that notification back up is the pilot's job, not this skill's — see the note in `<invocation>`.

3. **Check.** On the completion notification, run the checker at the `checker` path from the block reason, passing the `project dir` and the three numbers so the checker grades against exactly what the lane was dispatched with:
   ```bash
   python3 "<checker path>" --round 1 --project-dir "<project dir>" \
     --trigger <T> --target <Ta> --floor <F>
   ```
   Its first line always echoes what it resolved and is grading — `grading <current> vs <baseline>` — so you can confirm it's looking at the right files before reading the verdict. The verdict line follows: `PASS <before> -> <after> B, <n> links, round 1`, or `DEFECTS ...` followed by a repair-pointer list.

4. **PASS → done.** Relay the checker's verdict line to the operator. Stop here.

### Repair rounds (max 2 total)

5. **On DEFECTS**, re-dispatch a fresh background Haiku subagent. The prompt is again pointers only:
   - the `directive` path (same as round 1)
   - the `target file` path (same as round 1)
   - the three numbers (same as round 1)
   - the checker's own repair-pointer list, verbatim (the `size:` / `links:` / `entries:` / `headers:` / `clause-loss [...]:` lines from its output)
   - the baseline path — read it off the checker's own first line, `grading <current> vs <baseline>`: it's the exact path after ` vs ` (there is no `baseline=` token on this line — that form only appears on a CHECKER-ERROR missing-file line, not here); don't guess it or re-derive it

   Do not re-explain what the pointers mean and do not restate the directive — the subagent already has both.

6. **Check again**, incrementing the round (same flags as step 3, `--round 2`):
   ```bash
   python3 "<checker path>" --round 2 --project-dir "<project dir>" \
     --trigger <T> --target <Ta> --floor <F>
   ```

7. **Stop at 2 rounds regardless of verdict.** Whether round 2 is PASS or still DEFECTS, relay the final checker line to the operator and stop — do not dispatch a third round. Persistent DEFECTS after 2 rounds is itself a signal worth surfacing verbatim (which checks kept failing), not something to keep hammering at.

## Manual invocation (no block reason to read from)

If you're asked to run or check the janitor directly — not off a fresh Stop-hook block — there's no `reason` text to pull paths from. Locate the checker first:
```bash
find ~/.claude -path '*/memory-janitor/check.py' 2>/dev/null
```
`directive.md` is its sibling in the same directory. Pass `--project-dir` explicitly — either the operator-named project's root, or `"$(pwd)"` for the current one — and supply `--trigger`/`--target`/`--floor` explicitly too (see `check.py --help`, or the `COG_JANITOR_TRIGGER` / `COG_JANITOR_TARGET` / `COG_JANITOR_FLOOR` env vars documented in the plugin README for the defaults). Everything else in the procedure above is unchanged.

## Coexistence with the hook's own dedupe

The Stop hook already prevents re-blocking mid-cooldown (a `pending` marker in the project's `janitor/` state dir, cleared once the file drops back under threshold). If this skill ends up invoked more than once for what's functionally the same trigger — e.g. two turns in a row both hit the block before round 1 finished — that's harmless: round 1's dispatch and check are idempotent against the same baseline, and a second invocation simply continues the same loop against whatever the current state is. Nothing here needs its own additional dedupe logic; the hook already carries it.

## Known limitation

The baseline the checker grades against is a snapshot taken at Stop-hook trigger time, not at dispatch time — and auto-memory can keep writing `MEMORY.md` during the session (other turns, other tabs, other seats sharing the same project). If a checker run flags a loss the dispatched lane plainly didn't make, that is the signature of a concurrent write racing the snapshot, not a bad compaction. Re-snapshot (overwrite the `baseline` state file with the current `MEMORY.md`) and treat that round as void rather than repair-dispatching the lane against a defect it didn't cause.

## Anti-patterns

- **Compacting MEMORY.md inline.** The entire point of this skill existing separately from the hook is that the pilot never does the trim itself, mid-turn, without the checker's grading. If you catch yourself editing the target file directly, stop.
- **Summarizing the directive or target file into the dispatch prompt.** Pointers only — pull-context dispatch. The subagent has file access; use it.
- **Re-deriving the checker/directive path instead of using the block reason's.** The hook already resolved and printed absolute paths; inventing your own risks disagreeing with them.
- **Arming a wait/monitor for the subagent.** This skill's dispatch step ends the moment the subagent is started. The notification arrives on its own; don't block a turn polling for it.
- **A third repair round.** Two is the ceiling regardless of verdict. Relay and stop.
- **Treating a DEFECTS verdict as a failure to hide.** Relay it verbatim, including which checks failed — that's training signal for the directive, not an embarrassment to paper over.

## Related

- The `memory-janitor.py` Stop hook (`hooks/hooks.json`) is what triggers this skill; it never runs the compaction itself, only the block + baseline capture + path/number resolution.
- `directive.md` (this skill's own directory) is the standing procedure the dispatched Haiku lane follows.
- `check.py` (this skill's own directory) is the deterministic grader; its checks are documented in its own module docstring.
- Composes the way `handoff` and `consolidate` do without being either: this skill is narrowly transactional (one file, one size target), where `consolidate` is reflective session-arc capture. Don't reach for `consolidate` as a substitute here — different job.
