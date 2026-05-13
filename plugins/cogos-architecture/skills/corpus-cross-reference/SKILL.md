---
name: corpus-cross-reference
description: Cross-check a proposed RFC or ADR against the existing substrate corpus. Surfaces composition gaps, conflicts, prior art, frontmatter validation, and numbering issues. Runs at proposal time — invoke manually today; auto-fires on RFC/ADR PR-open via a future GitHub Actions hook. Triggers on /corpus-cross-reference, "cross-reference the corpus", "check this RFC against existing", "what does the corpus already say about", or when opening an RFC/ADR PR and wanting a composition review.
version: 0.1.0
allowed-tools: Read, Bash(find:*) Bash(grep:*) Bash(git:*) Bash(gh:*)
---

# Corpus Cross-Reference

Automated cross-check for a proposed RFC or ADR. Runs at proposal time and produces a structured review comment suitable for posting on the PR. The review is informational, not blocking — it helps the proposer catch composition gaps and prior art before a human reviewer reads the document.

Ratified by ADR-087 (`cog://adr/087`). This skill extends the `cogos-architecture-docs` domain with a focused proposal-time cross-check procedure.

## When to use

- A new RFC or ADR has been opened or is about to be opened for review.
- You want to confirm the proposal cites all relevant prior art.
- You want to confirm the assigned number has not been used elsewhere.
- You want a quick conflict scan against accepted decisions.

Do NOT run this skill on every PR. Only RFC/ADR PRs in the architecture-docs sectors of the cog workspace or cogos repo warrant a cross-reference review.

## Corpus layout

Two distinct corpora with different numbering schemes — the skill handles both.

| Corpus | Location | Number format | Example |
|--------|----------|---------------|---------|
| cog workspace — ADRs | `${COGOS_WORKSPACE:-$HOME/workspaces/cog}/.cog/adr/` | 3-digit `NNN-slug.cog.md` | `087-architecture-documentation-lifecycle-skill.cog.md` |
| cog workspace — RFCs | `${COGOS_WORKSPACE:-$HOME/workspaces/cog}/.cog/conf/spec/rfc/` | `RFC-NNN-slug.cog.md` | `RFC-033-cognitive-primitives-substrate-runtime-workspace-node-agent.cog.md` |
| cogos repo — ADRs | `${MYRGIC_REPOS_ROOT:-$HOME/workspaces/myrgic}/cogos/docs/adr/` | 4-digit `NNNN-slug.md` | `0007-dispatch-provider-override.md` |
| cogos repo — RFCs | `${MYRGIC_REPOS_ROOT:-$HOME/workspaces/myrgic}/cogos/docs/rfcs/` | 4-digit `NNNN-slug.md` | `0005-cog-fork-session.md` |
| Memory cogdocs | `${COGOS_WORKSPACE:-$HOME/workspaces/cog}/.cog/mem/semantic/` | slug | `insights/pull-context-agent-dispatch.cog.md` |

When an RFC or ADR lives in the cog workspace, also scan the cogos repo corpus for cross-corpus composition — they are sibling artifacts that should be aware of each other. The inverse applies.

## Procedure

### 1. Identify the proposed artifact

```bash
# From a PR number (most common invocation):
gh pr view <PR-number> --json headRefName,files,body,title

# Get the actual file path from the PR's changed files:
gh pr diff <PR-number> --name-only | grep -E '\.(cog\.md|\.md)$' | head -5
```

Read the file. Parse its frontmatter — extract:
- `type` (adr / rfc)
- numeric id / `adr:` / `cog.rfc:` field
- `status`
- `tags`
- `refs` list (existing citations)
- `title`

Determine which corpus it belongs to from its file path.

### 2. Build the corpus index

```bash
# cog workspace ADRs:
find "${COGOS_WORKSPACE:-$HOME/workspaces/cog}/.cog/adr" \
  -name '*.cog.md' -not -name 'README.md' -not -name 'TEMPLATE*' | sort

# cog workspace RFCs:
find "${COGOS_WORKSPACE:-$HOME/workspaces/cog}/.cog/conf/spec/rfc" \
  -name '*.cog.md' -not -name 'TEMPLATE*' | sort

# cogos repo ADRs:
find "${MYRGIC_REPOS_ROOT:-$HOME/workspaces/myrgic}/cogos/docs/adr" \
  -name '*.md' | sort 2>/dev/null

# cogos repo RFCs:
find "${MYRGIC_REPOS_ROOT:-$HOME/workspaces/myrgic}/cogos/docs/rfcs" \
  -name '*.md' | sort 2>/dev/null
```

For each file, read just the frontmatter block (first ~40 lines). Build a quick index:
`number → title → tags → status → refs-list`.

### 3. Run the cross-checks

Run all six checks. Each emits findings in a structured list. Tolerate noise rather than missing real connections — the reviewer filters; the skill surfaces.

#### 3a. Composition check

Extract the key concepts from the proposal's title, tags, and body headings. Search the corpus for documents that share 2+ concepts with the proposal but are absent from `refs:`.

```bash
# Extract tags from proposal and grep corpus for matching content:
grep -r "<tag1>\|<tag2>\|<concept>" \
  "${COGOS_WORKSPACE:-$HOME/workspaces/cog}/.cog/adr/" \
  "${COGOS_WORKSPACE:-$HOME/workspaces/cog}/.cog/conf/spec/rfc/" \
  --include='*.cog.md' -l
```

For each candidate file not already in `refs:`, read its title and tags. Rank by concept overlap (most matches first). Surface the top 5 candidates.

See `resources/cross-check-heuristics.md` for keyword extraction and overlap scoring heuristics.

#### 3b. Conflict check

Search for contradictions with accepted decisions. Focus on ADRs with `status: accepted` that touch the same tag or concept space.

For each candidate accepted ADR or RFC in the overlapping set, scan for decision invariants that could contradict the proposal's Decision or Proposal section. Quote the specific conflicting invariant.

A conflict is: "Proposal says X; ADR-NNN (accepted) says not-X." Surface only genuine logical contradictions, not merely related topics.

#### 3c. Prior-art check

Find near-duplicates: documents that already partially articulate the same idea, mechanism, or design. The canonical example (recorded in the skill's design rationale): RFC-033 from 12 days before a hypothetical RFC-034 had already drawn the substrate-vs-kernel cut without naming the separability implication — a cross-reference skill should surface that automatically.

Look for:
- Same mechanism described in different terms
- Same problem statement with a different proposed solution
- Predecessor RFCs the proposal effectively supersedes without saying so

#### 3d. Numbering check

Confirm the proposed number is unused in the relevant corpus AND has no collision in the sibling corpus.

```bash
# For a cog-workspace ADR proposing number NNN:
find "${COGOS_WORKSPACE:-$HOME/workspaces/cog}/.cog/adr" -name 'NNN-*.cog.md'

# Also check cogos repo for collision with 4-digit scheme:
# (4-digit NNN = 00NN format in cogos repo — check for NNNN match)
find "${MYRGIC_REPOS_ROOT:-$HOME/workspaces/myrgic}/cogos/docs/adr" -name "00${NNN}-*.md"
```

Flag collisions. Also warn if the proposed number skips more than 2 from the current highest number (possible parallel drafts in flight).

#### 3e. Frontmatter check

Validate the proposal's frontmatter against the canonical shape per `cogos-architecture-docs` skill (§ Frontmatter contract).

Required fields for ADRs: `type`, `adr`, `id`, `title`, `status`, `created`.
Required fields for RFCs: nested `cog:` block with `type`, `rfc`, `id`; `title`, `status`, `created`, `author`.

See `resources/canonical-frontmatter-shapes.md` for the exact shapes and examples for both corpus schemes.

Report each missing required field as an error. Report each missing recommended field (`authors`, `tags`, `refs`) as a warning.

#### 3f. Status-graph check

For each artifact in the proposal's `refs:` list:
- Confirm it exists in the corpus (no dangling `cog://` URIs)
- Confirm it is not `status: superseded` or `status: deprecated` — if so, flag with the successor's ID

Stale refs (citing superseded documents without also citing the successor) compromise the composition graph.

#### 3g. Gap check

Review the proposal's `## Open Questions` and `## Alternatives` sections (RFCs) or `## Consequences` section (ADRs) for implicit assumptions that have already been addressed by prior decisions.

Flag items where the proposal marks something as "out of scope" or "to be decided later" when a ratified ADR or accepted RFC already decided it.

### 4. Compose the structured review

Assemble the review in markdown. Emit to stdout; optionally post as a PR comment.

```markdown
## Substrate cross-reference review (auto)

*Generated by the `corpus-cross-reference` skill. Informational — not a blocker.*

### Compositions you may have missed

| Artifact | Title | Relationship | Why it matters |
|---------|-------|-------------|---------------|
| cog://adr/NNN | ADR-NNN: ... | extends / composes-with / builds-on | one-line reason |

*(empty if none found above the relevance threshold)*

### Prior art

> Quote of the relevant invariant from the prior artifact

**ADR-NNN / RFC-NNN** already articulates [mechanism/decision]. If your proposal extends or supersedes this, add a `refs:` entry with the appropriate `rel:`.

*(empty if no near-duplicates found)*

### Potential conflicts

| Ratified decision | Conflict with proposal |
|------------------|----------------------|
| cog://adr/NNN: "invariant text" | Your proposal says X which contradicts this |

*(or: "No conflicts detected with accepted decisions.")*

### Status notes

- **Numbering:** NNN is unused in both corpora. ✓
- **Frontmatter:** required fields present. ✓ / Missing: `field1`, `field2`
- **Stale refs:** none / `cog://adr/NNN` is superseded by ADR-MMM — update ref.

### Suggested amendments

*(non-blocking, prioritized)*

1. Add `refs:` entry for ADR-NNN with `rel: builds-on` — it defines the primitive this proposal uses.
2. Frontmatter: add `authors:` field.
3. Consider narrowing scope: the Open Questions section raises X, but ADR-NNN already resolved it.

### Composition graph (excerpt)

```
RFC-NNN (proposed)
  └── extends → ADR-NNN (accepted) "Title"
  └── composes-with → RFC-MMM (draft) "Title"
  └── [missing] builds-on → ADR-PPP (accepted) "Title"  ← suggested addition
```
```

### 5. Output and post

Print the review to stdout. To post as a PR comment:

```bash
gh pr comment <PR-number> --repo <owner>/<repo> --body "$(cat <<'REVIEW'
<review content here>
REVIEW
)"
```

Post as a comment, not as an official `gh pr review` verdict. The review is advisory.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| PR number or file path | required | What to review — PR number (resolves via `gh`) or absolute file path |
| `--no-comment` | false | Print to stdout only; do not post PR comment |
| `--repo` | inferred from `git remote` | Target repo for `gh` commands |
| `--corpus` | both | Which corpus to search: `cog`, `cogos`, or `both` |
| `--depth` | standard | `quick` (numbering + frontmatter only) or `deep` (full semantic scan) |

## Anti-patterns

- **Over-citing.** Only surface artifacts with a genuine compositional relationship. A passing mention of a concept is not a `refs:` relationship. Prefer surfacing 2–5 relevant artifacts over dumping 20 marginal ones.
- **Restructuring the proposal.** This skill flags composition gaps and conflicts. It does not suggest rewriting sections, splitting the proposal, or changing the design direction. Out of scope.
- **Being a quality gatekeeper.** The review is informational. The skill does not approve or block. That is the human reviewer's role.
- **Fabricating connections.** Only cite what genuinely composes. If a keyword match does not survive a one-sentence "why it matters" test, drop it.
- **Running on every PR.** Only RFC/ADR PRs in architecture-docs sectors warrant a cross-reference review. Code-only PRs, dependency bumps, and documentation fixes do not.
- **Normalizing pre-standard artifacts.** Lenient-read on the existing corpus (per `cogos-architecture-docs`). Old ADRs ≤ 045 may lack canonical frontmatter — surface that as info, not error.

## Composition with RFC-034 (Reconcilable Binding Pattern)

This skill is a natural instantiation of the Reconcilable Binding Pattern (cog://rfc/034) at the corpus-curation layer. The binding primitives map as follows:

| Binding-pattern primitive | This skill's instantiation |
|---|---|
| Class | `CorpusReviewClass` — declares the review policy for any RFC/ADR PR |
| Claim | Each new RFC/ADR PR is a `CorpusReviewClaim` asserting "this proposal composes correctly with the existing corpus" |
| PhysicalInstantiation | The actual review comment posted on the PR + an optional cogdoc record |
| Reconciler | This skill — observes the corpus, detects drift from expected composition, emits findings |

This composition is noted even though RFC-034 has not merged yet. The skill is designed to work with or without RFC-034's ratification; the binding-pattern framing explains *why* a recurring reconciler is the right architectural shape for corpus hygiene rather than a one-off review checklist.

## Resources

- `resources/canonical-frontmatter-shapes.md` — valid frontmatter examples for all four corpus × document-type combinations
- `resources/refs-vocabulary.md` — canonical `rel:` values with semantics and canonical inverses (sourced from `cogos-architecture-docs`)
- `resources/cross-check-heuristics.md` — concrete heuristics for composition, conflict, and prior-art checks
- `tools/list_corpus.sh` — enumerate all four corpora and emit a structured index

## Related

- `cogos-architecture-docs` skill — canonical lifecycle reference this skill extends (`.claude/skills/cogos-architecture-docs/SKILL.md`); ratified by ADR-087
- ADR-087 (`cog://adr/087`) — declares architecture-documentation hygiene as skill-governed; this skill operates within that policy
- RFC-033 (`cog://rfc/033`) — prior-art example: articulated substrate/runtime distinction before RFC-034 named it; the canonical case for why a cross-reference skill is needed
- `cogos-workflow/local-review` skill — PR review via local model; a companion at the code-review layer
- `cogos-workflow/critical-review` skill — rigorous argument evaluation; use alongside this skill for deeper proposal assessment

## Episodes

<!-- Add production run examples here after first use. Format:
### YYYY-MM-DD — RFC/ADR NNN
Command: `/corpus-cross-reference <PR-number>`
Artifacts in corpus at time of run: NNN ADRs, MMM RFCs
Compositions surfaced: N
Conflicts detected: N
Time to review: Xs
Notes: ...
-->

## Learnings

- The RFC-033/RFC-034 gap (substrate/kernel distinction partially articulated 12 days before the proposal that named it) is the founding motivating case for this skill. A running cross-reference check at PR-open time closes this class of gap automatically.
- Keyword-only matching generates noise. The composition check uses keyword + tag overlap + concept co-occurrence; the prior-art check requires a "why it matters" rationale for each surfaced artifact. See `resources/cross-check-heuristics.md` for the calibration.
- Two numbering schemes coexist (cog workspace 3-digit; cogos repo 4-digit). Numbering check must resolve both to avoid false-negative collision reports.
