---
name: pr-triage
description: Enumerate, classify, and summarize open pull requests across the cogos-dev GitHub org. Use when asked to triage PRs, check what needs review, audit open work, or surface stale or blocked PRs across repos.
---

# Skill: pr-triage

Produce a classified, grouped summary of open pull requests across the cogos-dev GitHub org. This skill is read-only. It does not merge, close, approve, or edit any PR.

## Active Repos

Query these repos. Skip archived repos (desktop, openclaw-plugin) unless the request explicitly names them.

| Repo | Notes |
|------|-------|
| cogos-dev/cogos | kernel |
| cogos-dev/constellation | |
| cogos-dev/mod3 | |
| cogos-dev/charts | |
| cogos-dev/skills | |
| cogos-dev/research | |
| cogos-dev/cogops | private |
| cogos-dev/docs | private |
| cogos-dev/cog-sandbox-mcp | |
| cogos-dev/.github | org governance |

## Step 1: Enumerate

Run one of the following. Both produce equivalent data; pick based on context:

**Per-repo (precise, handles private repos):**
```
gh pr list \
  --repo cogos-dev/<repo> \
  --state open \
  --json number,title,author,createdAt,isDraft,mergeable,reviewDecision,labels,comments,updatedAt
```
Repeat for each repo in the active list above.

**Flat view (fast, public repos only):**
```
gh search prs --owner cogos-dev --state open \
  --json number,title,author,createdAt,isDraft,repository
```
Follow up with per-repo queries for cogops and docs, which are private and not returned by `gh search prs`.

Collect the full result set before classifying.

## Step 2: Classify

Assign each PR exactly one classification. Apply the first rule that matches.

| Classification | Criteria |
|----------------|----------|
| **ready-to-merge** | Not draft; `mergeable == MERGEABLE`; `reviewDecision == APPROVED`; no label matching `blocked`, `needs-discussion`, or `do-not-merge`. |
| **needs-review** | Not draft; no review decision yet (reviewDecision is null or `REVIEW_REQUIRED`); no requested changes. |
| **needs-author-action** | `reviewDecision == CHANGES_REQUESTED`; OR `mergeable == CONFLICTING`; OR CI is failing (check with `gh pr checks <number> --repo <repo>` if reviewDecision alone is ambiguous). |
| **needs-discussion** | Has a label matching `needs-discussion` or `blocked`; OR has unresolved review threads (check with `gh pr view <number> --repo <repo> --json reviewThreads`). |
| **stale-or-abandoned** | No activity (comments, commits, review) in 30+ days; no clear path forward. Apply this only after checking `updatedAt`; a recent commit resets the clock. |

When a PR matches more than one rule (for example, approved but also has a `blocked` label), prefer the classification that requires more human attention: needs-discussion beats ready-to-merge; needs-author-action beats needs-review.

## Step 3: Format Each Entry

One line per PR:

```
<repo>#<number> [<classification>] <title> (by @<author>, <age>)
```

Age is expressed as days: compute from `createdAt` to the session date.

## Step 4: Group and Sort

Output sections in this order:

1. Notable items (see Step 5)
2. ready-to-merge
3. needs-review
4. needs-author-action
5. needs-discussion
6. stale-or-abandoned

Within each section: sort by repo name (alphabetical), then by age (oldest first within the same repo).

## Step 5: Surface Notable Items

Before the grouped sections, produce a "Notable" block listing PRs that match any of the following conditions. A PR may appear in both Notable and its classification section.

- **Age > 14 days**: any open PR not yet in stale-or-abandoned but older than 14 days.
- **Draft marked ready**: draft PRs whose title or body contains "ready for review", "ready to merge", or similar phrasing.
- **Governance-sensitive**: PRs touching `.github/profile/`, `docs/`, or any file that directly controls the org's public identity or published documentation. Flag these for extra care before merging.
- **First-time contributor**: PR author has no other merged or open PR across any cogos-dev repo (check with `gh search prs --owner cogos-dev --author <author> --state all`). Label the entry `[first-time contributor]`.

If Notable is empty, omit the section entirely.

## Step 6: Summary Line

End the output with one line:

```
Summary: <N> open PRs across <R> repos -- ready-to-merge: <n>, needs-review: <n>, needs-author-action: <n>, needs-discussion: <n>, stale-or-abandoned: <n>. Flags: <list or "none">.
```

## Step 7: Recommend Actions

After the summary, add a short "Recommended Actions" section. One bullet per actionable item. Recommend only; do not execute.

Recommendation patterns by classification:

| Classification | Recommended action |
|----------------|--------------------|
| ready-to-merge | "Verify CI on cogos#N, then merge." |
| needs-review | "Request review from a team member on constellation#N." Name a specific reviewer if context makes one obvious. |
| needs-author-action | "Nudge @author on repo#N: resolve conflicts before re-review." |
| needs-discussion | "Resolve the blocking question on repo#N before proceeding." |
| stale-or-abandoned | "Comment on repo#N asking whether work will continue, or close as stale." Do not close unilaterally. |

Limit to the top 5 highest-priority items if the total would exceed 10.

## Example Output (Illustrative)

```
### Notable

cogos#38 [needs-review] Refactor event loop dispatcher (by @alice, 18d) -- age > 14d
cogos#42 [ready-to-merge] Add reconciler health endpoint (by @carol, 4d) -- governance-sensitive (.github/profile touched)

### ready-to-merge

cogos#42 [ready-to-merge] Add reconciler health endpoint (by @carol, 4d)

### needs-review

cogos#38 [needs-review] Refactor event loop dispatcher (by @alice, 18d)
constellation#7 [needs-review] Update identity manifest schema (by @bob, 6d)

### stale-or-abandoned

charts#3 [stale-or-abandoned] Bump cert-manager to v1.14 (by @dave, 51d)

Summary: 4 open PRs across 3 repos -- ready-to-merge: 1, needs-review: 2, needs-author-action: 0, needs-discussion: 0, stale-or-abandoned: 1. Flags: 1 governance-sensitive, 1 age > 14d.

### Recommended Actions

- Verify CI on cogos#42, then merge (governance-sensitive: confirm .github change is intentional).
- Assign a reviewer to cogos#38; it has been open 18 days.
- Request review assignment on constellation#7.
- Comment on charts#3 asking @dave whether the bump is still needed, or close as stale.
```

## Constraints

- **Read-only.** Do not run `gh pr merge`, `gh pr close`, `gh pr review`, `gh pr edit`, or any write operation against a PR.
- **Skip archived repos** (desktop, openclaw-plugin) unless the user explicitly names them.
- **Date claims** are relative to the session date. Compute age from `createdAt`.
- **Private repos** (cogops, docs): query with per-repo `gh pr list`; `gh search prs` will not return them.
