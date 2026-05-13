# Cross-Check Heuristics

Concrete heuristics for the composition, conflict, and prior-art checks in the `corpus-cross-reference` skill.

These heuristics are calibrated against the cog workspace corpus (89 ADRs + 33 RFCs as of 2026-05-13). Adjust thresholds as the corpus grows.

## Composition check (§ 3a)

Goal: surface artifacts that should plausibly be in `refs:` but are not.

### Step 1: Extract candidate concepts from the proposal

From the proposal's frontmatter + body:
1. All `tags:` values (exact)
2. Words in the `title:` with length > 4 that are not stop-words
3. Section headings in the body (## and ###)
4. Defined terms introduced in the first paragraph of each major section

Example: RFC proposing "session registration via context assembly" yields concepts:
`session`, `registration`, `context`, `assembly`, `identity`, `kernel`, `workspace`

### Step 2: Score corpus artifacts

For each artifact in the corpus index:
- Score = (proposal concepts present in artifact's tags) + 0.5 × (proposal concepts present in artifact's title)
- Threshold: Score ≥ 1.5 to enter candidate set
- Hard floor: at least 1 matching tag (title-only matches are weak)

### Step 3: Filter already-cited

Remove any artifact already in the proposal's `refs:` list.

### Step 4: Rank and cap

Sort candidates by score descending. Surface the top 5.
If more than 10 candidates pass the threshold, note "corpus has N related artifacts" and surface only top 5.

### Step 5: One-sentence "why it matters" test

For each candidate, write one sentence connecting it to the proposal. If you cannot write this sentence in under 20 words, drop the candidate — it is keyword noise, not a genuine composition.

**Signal/noise calibration:**
- ADRs and RFCs sharing 3+ tags with the proposal: very high confidence — surface always
- ADRs and RFCs sharing 2 tags: moderate confidence — surface with "why it matters"
- ADRs and RFCs sharing 1 tag + concept-in-body overlap: low confidence — surface as "also consider" at the end
- Memory cogdocs: surface only if they define a term or framework the proposal builds on

## Conflict check (§ 3b)

Goal: find ratified decisions that contradict the proposal.

### What counts as a conflict

A conflict requires all three of:
1. The cited artifact is `status: accepted` (or `implemented`)
2. The cited artifact contains a decision invariant ("we use X", "all components must Y", "the contract is Z")
3. The proposal's Decision or Proposal section states the inverse or an incompatible variant

**Not a conflict:**
- Two artifacts address the same topic from different angles
- An ADR establishes a mechanism the proposal extends (that is `extends`, not a conflict)
- An RFC in `draft` or `review` status (non-ratified, subject to change)

### How to scan for conflicts

For each candidate accepted ADR/RFC from the composition-check candidate set:
1. Read the Decision section
2. Extract invariants (sentences with "must", "always", "never", "is the only", "canonical", "required")
3. Compare each invariant to the proposal's Decision/Proposal section
4. Flag if a clear logical negation or incompatible claim exists

### Conflict output format

```
CONFLICT: ADR-NNN says "[verbatim invariant]" (accepted).
Your proposal says "[verbatim conflicting claim]".
Suggestion: either cite ADR-NNN with `rel: supersedes` (if intentionally replacing it)
or narrow your proposal to avoid the overlap.
```

Never flag a conflict without quoting both invariants verbatim. Paraphrase leads to false positives.

## Prior-art check (§ 3c)

Goal: find documents that already articulate the same mechanism or design direction.

### Near-duplicate signals

A document is prior art when any of these hold:
- Title overlap: 3+ significant words shared with the proposal title (after stop-word removal)
- Same mechanism: both documents describe the same state machine, protocol step, data flow, or interface boundary
- Same problem statement: the Background / Motivation sections address the same observed gap
- Implicit supersede: the proposal's design would make the prior document's Decision invalid without saying so

### Scan approach

For high-probability candidates (score ≥ 2 from composition check):
1. Read the full Summary (first 20 lines of body)
2. Compare problem statement with proposal's Background / Motivation
3. Compare solution mechanism with proposal's Decision / Proposal
4. Flag if overlap score > 70% subjective (same design with different names, or partial overlap)

### Prior-art output format

```
PRIOR ART: RFC-NNN "Title" (12 days ago, status: draft) already articulates
[one-sentence description of the overlap].
If your proposal extends this, add `refs: {uri: cog://rfc/NNN, rel: extends}`.
If it supersedes it, add `rel: supersedes` once accepted.
Key quote: "[verbatim relevant sentence from prior artifact]"
```

The RFC-033/RFC-034 case is the canonical example: RFC-033 described the substrate/runtime/workspace/node/agent distinction in detail; a hypothetical RFC-034 (Reconcilable Binding Pattern) relies on the substrate/kernel separation that RFC-033 established. Without a cross-reference check, RFC-034's author might not realize RFC-033 had drawn the relevant distinction 12 days earlier.

## Numbering check (§ 3d)

### cog workspace ADR numbering

1. List all files under `.cog/adr/` matching `NNN-*.cog.md`
2. Extract highest existing number N
3. Flag if proposed number:
   - Already used (collision)
   - More than 2 above N (potential parallel draft)
   - Less than N (definitely parallel-draft collision)

### cog workspace RFC numbering

1. List all files under `.cog/conf/spec/rfc/` matching `RFC-NNN-*.cog.md`
2. Same checks as above

### Cross-corpus collision check

The two corpora use independent sequences but share the same `cog://adr/` URI scheme in their respective contexts. When a cog-workspace ADR has number NNN, check if the cogos repo has `NNNN-*.md` (zero-padded to 4 digits). These are different artifacts in different namespaces, but the overlap is worth noting in the review to prevent future confusion.

## Status-graph check (§ 3f)

### Dangling URIs

For each `cog://` URI in `refs:`:
1. Map to a filesystem path:
   - `cog://adr/NNN` → `.cog/adr/NNN-*.cog.md`
   - `cog://rfc/NNN` → `.cog/conf/spec/rfc/RFC-NNN-*.cog.md`
   - `cog://mem/<sector>/<path>` → `.cog/mem/<sector>/<path>`
2. Check file exists
3. If not found, flag as dangling URI

### Stale refs

For each artifact in `refs:` that exists in the corpus:
1. Read its `status:` field
2. Flag if `status: superseded` — include the `superseded_by:` value
3. Flag if `status: deprecated` — note it is aging out
4. Warn if `status: withdrawn` or `status: rejected` — citing a rejected/withdrawn proposal in `related:` is fine, but citing it in `builds-on:` or `extends:` is a flag

## Frontmatter check (§ 3e)

### Required field matrix

| Field | ADR (cog) | RFC (cog) | ADR (cogos) | RFC (cogos) | Severity if missing |
|-------|-----------|-----------|-------------|-------------|---------------------|
| `type` | required | (in nested `cog:`) | required | (in nested `cog:`) | error |
| `adr:` / `cog.rfc:` | required | required | required | required | error |
| `id:` | required | required | required | required | error |
| `title:` | required | required | required | required | error |
| `status:` | required | required | required | required | error |
| `created:` | required | required | required | required | error |
| `authors:` / `author:` | recommended | required | recommended | required | warn (ADR), error (RFC) |
| `tags:` | recommended | recommended | recommended | recommended | warn |
| `refs:` | recommended | recommended | recommended | recommended | info (new proposals with no refs are suspicious but not invalid) |

### Status vocabulary check

Validate `status:` against the canonical vocabulary per corpus:
- ADR: `proposed` | `accepted` | `rejected` | `deprecated` | `superseded` | `withdrawn`
- RFC: `draft` | `review` | `accepted` | `implemented` | `withdrawn`

Non-canonical status values are errors (strict-write: R3 equivalent for this check).

### Title format check

ADR title format: `"ADR-NNN: Short Noun Phrase"`
RFC title format (cog workspace): `"RFC-NNN: Short Noun Phrase"`
cogos repo format: `"ADR-NNNN: Short Noun Phrase"` / `"RFC-NNNN: Short Noun Phrase"`

Mismatch between title prefix and `id:` field is an error.
