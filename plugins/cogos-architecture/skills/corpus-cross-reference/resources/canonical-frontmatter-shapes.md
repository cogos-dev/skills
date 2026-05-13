# Canonical Frontmatter Shapes

Reference for the `corpus-cross-reference` skill. All four combinations of corpus × document type.

Source of truth: `cogos-architecture-docs` skill (`.claude/skills/cogos-architecture-docs/SKILL.md`, § Frontmatter contract), ratified by ADR-087.

## 1. cog workspace — ADR (3-digit numbering)

```yaml
---
type: adr
adr: 87
id: "087"
title: "ADR-087: Architecture Documentation Lifecycle Skill"
status: accepted
created: 2026-04-23
authors: [slowbro, cog]
tags: [architecture, documentation, lifecycle, adr, rfc, skill, governance, hygiene]
refs:
  - uri: cog://adr/027
    rel: extends
    description: "RFC Process Adoption — establishes RFC/ADR lifecycle this skill formalizes"
supersedes: []
---
```

**Required fields:** `type`, `adr`, `id`, `title`, `status`, `created`
**Recommended:** `authors`, `tags`, `refs`
**File path:** `.cog/adr/NNN-kebab-slug.cog.md`
**Number format:** 3-digit decimal, zero-padded, permanent

Status vocabulary: `proposed` | `accepted` | `rejected` | `deprecated` | `superseded` | `withdrawn` | `in-review` (not-yet-canonical)

## 2. cog workspace — RFC (3-digit numbering)

```yaml
---
cog:
  type: rfc
  rfc: 33
  id: "033"
  version: 1
title: "RFC-033: Cognitive Primitives — Substrate, Runtime, Workspace, Node, Agent"
status: draft
created: 2026-04-24
author: slowbro
tags: [substrate, runtime, workspace, node, agent, primitives]
refs:
  - uri: cog://adr/027
    rel: extended-by
    description: "RFC Process Adoption — this RFC uses the process ADR-027 establishes"
---
```

**Required fields:** nested `cog:` block with `type`, `rfc`, `id`; plus `title`, `status`, `created`, `author`
**Note:** singular `author:` (not `authors:`), nested `cog:` block — intentional per ADR-087; do not normalize to ADR shape
**File path:** `.cog/conf/spec/rfc/RFC-NNN-kebab-slug.cog.md`
**Number format:** `RFC-NNN-` prefix, 3-digit, permanent

Status vocabulary: `draft` | `review` | `accepted` | `implemented` | `withdrawn`

## 3. cogos repo — ADR (4-digit numbering)

```yaml
---
type: adr
adr: 7
id: "0007"
title: "ADR-0007: Dispatch Provider Override"
status: accepted
created: 2026-05-01
authors: [slowbro]
tags: [dispatch, provider, override, routing]
refs:
  - uri: cog://adr/0006
    rel: extends
    description: "vLLM PagedAttention provider — dispatch override builds on provider abstraction"
supersedes: []
---
```

**Required fields:** same as cog workspace ADR
**File path:** `docs/adr/NNNN-kebab-slug.md` (no `.cog` extension)
**Number format:** 4-digit decimal, zero-padded
**Note:** `cog://adr/` URIs use the 4-digit id within the cogos corpus; resolve ambiguity by corpus path context

## 4. cogos repo — RFC (4-digit numbering)

```yaml
---
cog:
  type: rfc
  rfc: 5
  id: "0005"
  version: 1
title: "RFC-0005: cog fork-session"
status: draft
created: 2026-05-02
author: slowbro
tags: [session, fork, context]
refs: []
---
```

**File path:** `docs/rfcs/NNNN-kebab-slug.md`
**Number format:** 4-digit, same pattern as cogos ADRs

## Numbering collision check

When proposing a new ADR or RFC, confirm:
1. The number is unused in the primary corpus (the one you're writing into)
2. No conceptual collision with the sibling corpus at the same number

The two corpora are independent sequences. `ADR-007` in the cog workspace and `ADR-0007` in the cogos repo are different artifacts. The `cog://adr/007` URI is local to the cog workspace; cogos repo refs use relative paths or their own `cog://` scope (TBD per org-level substrate RFC).

## Memory cogdoc shape (for reference)

```yaml
---
name: Brief noun-phrase title
description: 1-3 sentence summary of contents and when a reader would load it.
type: semantic
refs:
  - uri: cog://adr/021
    rel: grounds
---
```

Memory cogdocs live under `.cog/mem/semantic/` (or `episodic/`, `procedural/`, `reflective/`). No lifecycle status.
