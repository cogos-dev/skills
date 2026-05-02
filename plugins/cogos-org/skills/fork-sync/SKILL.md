---
name: fork-sync
description: Check and report origin-to-upstream divergence across the cogos-dev workspace repos. Use when asked to audit fork drift, check which repos need rebasing, surface blocked work without open PRs, or get an org-wide sync status before a release or merge window.
---

# Skill: fork-sync

Produce a structured divergence report for every active repo in the cogos-dev workspace. Each repo uses a fork pattern: `origin` points at the user's personal fork (`chazmaniandinkle/<repo>`) where development happens; `upstream` points at the org canonical (`cogos-dev/<repo>`) where PRs land. This skill is read-only. It does not pull, push, merge, rebase, or open PRs.

## Active Repos

Iterate these directories under `/Users/slowbro/workspaces/cogos-dev/`. Skip archived repos.

| Directory | Upstream Repo |
|-----------|---------------|
| `cogos/` | cogos-dev/cogos |
| `constellation/` | cogos-dev/constellation |
| `mod3/` | cogos-dev/mod3 |
| `charts/` | cogos-dev/charts |
| `skills/` | cogos-dev/skills |
| `research/` | cogos-dev/research |
| `cogops/` | cogos-dev/cogops (private) |
| `docs/` | cogos-dev/docs (private) |
| `.github/` | cogos-dev/.github |
| `gog-mcp/` | cogos-dev/cog-sandbox-mcp |

**Skip:** `desktop/`, `openclaw-plugin/` (archived). Skip the workspace root itself (not a git repo).

## Step 1: Verify Fork Pattern

```
git -C /Users/slowbro/workspaces/cogos-dev/<repo> remote -v
```

Parse for both `origin` and `upstream` entries. If neither is present, or if the directory is not a git repo, note it as **skipped (no fork pattern)** and move on. If only one remote exists, note which is missing and continue with what is available.

## Step 2: Fetch Latest

```
git -C /Users/slowbro/workspaces/cogos-dev/<repo> fetch origin --quiet
git -C /Users/slowbro/workspaces/cogos-dev/<repo> fetch upstream --quiet
```

These are read-only network operations. If a fetch fails, note the failure and continue. Do not abort the run for a single repo failure.

## Step 3: Identify Main Branch

```
git -C /Users/slowbro/workspaces/cogos-dev/<repo> symbolic-ref --short HEAD
git -C /Users/slowbro/workspaces/cogos-dev/<repo> rev-parse --abbrev-ref upstream/HEAD 2>/dev/null
```

Use the upstream default branch for all comparisons. If `upstream/HEAD` is not resolvable, fall back to `upstream/main`, then `upstream/master`.

## Step 4: Compute Divergence

Run three checks using `--left-right --count`. Each produces two numbers: commits unique to the left ref and commits unique to the right ref.

```
git -C /Users/slowbro/workspaces/cogos-dev/<repo> rev-list --left-right --count HEAD...upstream/main
git -C /Users/slowbro/workspaces/cogos-dev/<repo> rev-list --left-right --count origin/main...upstream/main
git -C /Users/slowbro/workspaces/cogos-dev/<repo> rev-list --left-right --count HEAD...origin/main
```

Substitute the correct branch name from Step 3. Record `N/A` for any comparison where a ref does not exist.

## Step 5: Detect Uncommitted State

```
git -C /Users/slowbro/workspaces/cogos-dev/<repo> status --porcelain
```

Empty output means the working tree is clean. Non-empty output: count the lines. Staged, unstaged, and untracked files all count.

## Step 6: Surface Open PRs from Origin

```
gh pr list \
  --repo cogos-dev/<repo> \
  --head chazmaniandinkle:<branch> \
  --state open \
  --json number,title,headRefName
```

Run for the current branch. List PR numbers and titles if any exist; otherwise record "none." For private repos (cogops, docs), note any auth or access failures.

## Step 7: Per-Repo Report Row

```
<repo> (branch: <current>)
  local <-> upstream/main:       ahead <N>, behind <M>
  origin/main <-> upstream/main: ahead <X>, behind <Y>
  local <-> origin/main:         ahead <A>, behind <B>
  working tree: clean | dirty (<Z> files)
  open PRs from origin: <#number: title> | none
  status: <label>
```

## Step 8: Assign Status Label

Assign exactly one label per repo. Apply the first matching rule.

| Label | Criteria |
|-------|----------|
| **clean** | All divergence counts are zero; working tree clean. |
| **dirty** | Working tree has uncommitted changes. |
| **blocked** | Local is ahead of upstream by 1+ commits with no open PR from that branch. |
| **drift-high** | Local or origin/main is behind upstream by 10 or more commits. |
| **drift-low** | Local or origin/main is behind upstream by 1-9 commits. |
| **unrelated** | Current branch is not main/master; or histories cannot be compared cleanly. |

Priority when multiple rules match: dirty > blocked > drift-high > drift-low > clean.

## Step 9: Org-Wide Summary

After per-repo rows, emit a summary table and a status count line, followed by per-repo recommendations for any repo that is not clean.

```
| Repo          | Branch | Behind Upstream | Ahead Upstream | Working Tree | Open PRs | Status     |
|---------------|--------|-----------------|----------------|--------------|----------|------------|
| cogos         | main   | 4               | 2              | clean        | none     | blocked    |
| constellation | main   | 0               | 0              | clean        | none     | clean      |
| charts        | main   | 11              | 0              | clean        | none     | drift-high |
| mod3          | main   | 0               | 0              | dirty (2)    | none     | dirty      |

Status counts: clean: 1, dirty: 1, blocked: 1, drift-high: 1, drift-low: 0, unrelated: 0, skipped: 0

Recommendations:
- cogos: 2 commits ahead of upstream with no open PR. Open a PR from chazmaniandinkle:main to cogos-dev:main.
- charts: 11 commits behind upstream. Rebase local main on upstream/main before adding new work.
- mod3: Uncommitted changes present. Stash or commit before fetching upstream.
```

Recommendations are advisory only. The human decides whether and when to act.

## Constraints

- **Read-only.** Do not run `git pull`, `git merge`, `git rebase`, `git push`, `gh pr create`, or any write operation.
- **Skip archived repos** (desktop, openclaw-plugin) unless the user explicitly names them.
- **Fetch before comparing.** Divergence counts against stale remote refs are misleading.
- **Recommendations are advisory.** This skill reports; the human acts.
