---
name: issue-triage
description: Enumerate, classify, and surface actionable open issues across cogos-dev repos. Use when the issue backlog needs review, before sprint planning, or when onboarding contributors.
---

# Issue Triage

Read-only audit of open issues across active cogos-dev repositories. Produces a classified inventory, flags untouched and contributor-ready items, and ends with a summary and label recommendations. No write operations are performed.

## Scope

**Active repos:** cogos, constellation, mod3, charts, skills, research, docs, .github, cog-sandbox-mcp

**Skip (archived):** desktop, openclaw-plugin

---

## Procedure

### Step 1: Enumerate open issues

For each active repo, run:

```bash
gh issue list \
  --repo cogos-dev/<repo> \
  --state open \
  --json number,title,author,createdAt,labels,comments,assignees \
  --limit 200
```

Alternatively, enumerate across the org in one pass:

```bash
gh search issues \
  --owner cogos-dev \
  --state open \
  --json number,repository,title,author,createdAt,labels,comments,assignees \
  --limit 500
```

Compute age in days from `createdAt` to today's date (2026-05-01 as of this version).

### Step 2: Classify each issue

Assign exactly one classification per issue:

| Classification | Criteria |
|---|---|
| `bug` | Identifiable defect; reproducible (see reproducibility heuristic below) |
| `bug (needs-info)` | Looks like a defect but lacks sufficient reproduction detail |
| `feature-request` | Enhancement or new capability |
| `question` | Support or clarification request; often belongs in Discussions, not Issues |
| `duplicate` | Same underlying problem as another open or recently-closed issue |
| `stale` | No activity in 60+ days; no clear path forward |
| `needs-info` | Insufficient detail for any classification; author follow-up required |
| `good-first-issue` | Scoped, has clear acceptance criteria, suitable for a new contributor |

**Reproducibility heuristic for bugs.** Check whether the issue body contains these four elements:

1. Steps to reproduce
2. Expected vs. actual behavior
3. Environment or version info
4. Logs or error messages

If 3 or 4 are present: classify as `bug`. If fewer than 3: classify as `bug (needs-info)`.

**good-first-issue** overrides other classifications when the issue carries that label or meets all three conditions: scope is bounded, acceptance criteria are explicit, and no deep repo knowledge is required.

### Step 3: Format each issue

One line per issue:

```
<repo>#<number> [<classification>] <title> (by @<author>, <age>d, <comment-count> comments)
```

Example:

```
cogos#142 [bug] Kernel exits on SIGPIPE with no log output (by @jsmith, 12d, 3 comments)
constellation#88 [feature-request] Add mTLS support for peer connections (by @alice, 45d, 0 comments)
mod3#31 [question] How do I configure a custom voice model? (by @bob, 7d, 1 comment)
```

### Step 4: Group and sort

Output the full list grouped in this order:

1. `bug` / `bug (needs-info)` (highest priority)
2. `feature-request`
3. `good-first-issue`
4. `needs-info`
5. `question`
6. `duplicate`
7. `stale`

Within each group, sort by repo name, then by age (oldest first).

### Step 5: Surface notable items

After the grouped list, produce four focused sub-lists:

**Untouched (no comments, no labels, 7+ days old):**
Issues that have received no engagement since filing. These need a first response or label.

**Contributor-ready:**
Issues labeled `good first issue` or `help wanted`, or classified `good-first-issue` by this triage. Include a one-line summary of the acceptance criteria if present in the body.

**Possible duplicates (flag for human verification only):**
For each open issue, check for title or body keyword overlap with other open issues and with issues closed in the past 90 days:

```bash
gh search issues --owner cogos-dev "<keyword from title>"
```

Extract 2–4 keywords from each title. If a match appears, list both issues and note the overlap. Do NOT auto-classify as duplicate; flag only.

Example:

```
POSSIBLE DUPLICATE: cogos#142 and cogos#98 (closed 2026-02-10)
  Shared terms: "SIGPIPE", "kernel exit"
  Verify: are these the same root cause?
```

**Should be discussions:**
Issues classified as `question` with no code reproduction or actionable defect. Suggest converting to a GitHub Discussion.

### Step 6: Summary table

| Metric | Count |
|---|---|
| Total open issues | N |
| bug / bug (needs-info) | N |
| feature-request | N |
| good-first-issue | N |
| needs-info | N |
| question | N |
| duplicate | N |
| stale | N |
| Untouched (no comments, no labels, 7+ days) | N |
| Contributor-ready | N |
| Possible duplicates flagged | N |

### Step 7: Recommendations

For each issue, append one read-only recommendation (do not execute):

| Recommendation | When to use |
|---|---|
| `SUGGEST LABEL: <label>` | Issue lacks a label matching its classification |
| `SUGGEST ASSIGN: @<maintainer>` | Clearly scoped to one repo's owner, unassigned |
| `SUGGEST CLOSE: duplicate of #<N>` | High-confidence duplicate |
| `SUGGEST CONVERT TO DISCUSSION` | Pure question, no reproducible defect |
| `NO ACTION` | Already labeled, assigned, and active |

Do not run `gh issue edit`, `gh issue close`, `gh issue comment`, or `gh label add`.

---

## Constraints

- **Read-only.** No write operations against any repo.
- Skip archived repos (desktop, openclaw-plugin).
- Age calculations are relative to the run date; note the run date at the top of output.
- If a repo returns a 404 or permission error, note it and continue.
- Duplicate detection is fuzzy and keyword-based. Always frame as "possible duplicate, verify manually."

---

## Example output fragment

```
Run date: 2026-05-01

## bug / bug (needs-info)

cogos#142    [bug]              Kernel exits on SIGPIPE with no log output  (by @jsmith, 12d, 3 comments)
cogos#137    [bug (needs-info)] Intermittent panic on startup               (by @alice, 19d, 0 comments)

## question

mod3#31      [question]  How do I configure a custom voice model?  (by @bob, 7d, 1 comment)

## Notable: Untouched

cogos#137    [bug (needs-info)]  Intermittent panic on startup  (19d, no comments, no labels)

## Notable: Possible duplicates (verify manually)

POSSIBLE DUPLICATE: cogos#142 and cogos#98 (closed 2026-02-10)
  Shared terms: "SIGPIPE", "kernel exit"

## Summary

| Metric | Count |
|---|---|
| Total open issues | 3 |
| bug / bug (needs-info) | 2 |
| question | 1 |
| Untouched | 1 |
| Contributor-ready | 0 |

## Recommendations

cogos#137    SUGGEST LABEL: needs-info
mod3#31      SUGGEST CONVERT TO DISCUSSION
```
