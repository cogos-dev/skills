# Refs Vocabulary

Canonical `rel:` values for `refs:` entries in CogOS ADRs, RFCs, and cogdocs.

Source: `cogos-architecture-docs` skill (§ Relationship vocabulary), ratified by ADR-087. This file is a condensed quick-reference for the `corpus-cross-reference` skill; the authoritative version with derivation detail lives in the cogos-architecture-docs SKILL.md.

## Canonical inverse-pair table

Every forward rel has a canonical inverse. Asymmetric refs are lint-rule R1 errors.

| Forward | Inverse | Semantic |
|---------|---------|---------|
| `supersedes` | `superseded-by` | History edge — new replaces old |
| `extends` | `extended-by` | New builds on old without replacing |
| `absorbs` | `absorbed-by` | New unifies old into a broader frame |
| `unifies` | `unified-by` | New folds multiple prior decisions into one coherent frame without formally superseding any |
| `subsumes` | `subsumed-by` | New covers old's concern domain |
| `composes-with` | `composes-with` | **Self-inverse.** Peer decisions that interlock at runtime or architecture |
| `depends-on` | `depended-on-by` | Structural dependency |
| `builds-on` | `built-on-by` | Weaker than `depends-on`; uses old's primitives |
| `grounds` | `grounded-by` | Evidentiary support — A grounds B's claim |
| `implements` | `implemented-by` | Code-to-decision edge |
| `decides` | `decided-by` | ADR → RFC edge at acceptance |
| `cites` | `cited-by` | General citation (cogdoc → ADR, etc.) |
| `informs` | `informed-by` | Softer than `grounds` — A shapes B's thinking |
| `supplements` | `supplemented-by` | A adds to B without replacing |
| `clarifies` | `clarified-by` | Meta-edge — new explains old |
| `amends` | `amended-by` | In-place edit that changes meaning |
| `uses` | `used-by` | Runtime / operational dependency |
| `applies` | `applied-by` | A principle applies in B's domain |
| `evolves` / `evolves-into` | `evolved-from` | Soft supersede (history line) |
| `companion` | `companion` | **Self-inverse.** Paired docs, neither primary |
| `related` | `related` | **Self-inverse.** Catch-all when no sharper rel fits |
| `context` | `contextualized-by` | A provides reading context for B |
| `provenance` | `provenance-of` | Origin citation |
| `indexed-by` | `indexes` | Navigational — A is listed in B's index / README |

## Rel categories (for sorting a new ref)

| Category | Rels |
|----------|------|
| Structural | `depends-on`, `builds-on`, `uses`, `extends`, `subsumes`, `composes-with` |
| Historical | `supersedes`, `amends`, `evolves`, `absorbs`, `unifies` |
| Evidentiary | `grounds`, `cites`, `provenance`, `informs` |
| Implementation | `implements`, `decides` |
| Navigational | `companion`, `related`, `context`, `supplements`, `clarifies`, `indexed-by` |

## Selecting a rel for the cross-reference review

When the corpus-cross-reference skill suggests a missing `refs:` entry, it picks from this vocabulary. Selection heuristics:

- The proposal uses a mechanism **defined** by the cited artifact → `builds-on`
- The proposal **narrows** or **specializes** the cited artifact's scope → `extends`
- The proposal **replaces** the cited artifact's decision → `supersedes` (only after the proposal is accepted)
- The proposal and cited artifact are **peers that must coexist** → `composes-with`
- The cited artifact is a **founding claim** the proposal assumes → `grounds` (from cited → proposal) / `grounded-by` (from proposal → cited)
- The cited artifact is a **vocabulary ADR** the proposal references → `builds-on` or `cites`
- The cited artifact is **adjacent, loosely related** → `related`

If no rel fits precisely, use `related` and note the intended relationship in `description:`. Do not invent new rel verbs; growth requires an amendment ADR (R9 enforces the whitelist).

## Growth discipline

To add a new rel:
1. File an amendment or small supersede-ADR adding the rel + canonical inverse.
2. Do not use ad hoc verbs mid-write.
3. Non-canonical rels in the existing pre-standard corpus are tolerated on read (R9 surfaces them as warn, not error).
