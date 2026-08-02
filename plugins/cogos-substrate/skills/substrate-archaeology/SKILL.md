---
name: substrate-archaeology
description: "Surface, integrate, and map prior work in the CogOS substrate — find existing research, prior cartography, theoretical lineages, and connect them to current work before building new things."
version: 1.0.0
author: myrgic
tags: [cogos, substrate, research, archaeology, cartography, theoretical-corpus, integration]
canonical_source: "~/.hermes/skills/domain/substrate-archaeology/SKILL.md"
projection_note: >
  This is the public marketplace projection. The canonical source at
  ~/.hermes/skills/domain/substrate-archaeology/SKILL.md contains additional
  private research corpus content. Update canonical first; project here after.
related_skills: [parallel-research-digest]
---

# Substrate Archaeology

Load this skill when asked to explore what's already in the substrate, find prior work relevant to a new direction, or connect theoretical threads to engineering work. The substrate almost always has more than the current conversation has surfaced.

## When to Use

- User says "there's probably more in there", "dig around", "find what's relevant", "what do we already have on X"
- Before designing a new system: check what theory and prior design work already constrains the design
- Before dispatching research agents: find existing maps so agents get pointers, not blank canvas
- When surfacing apparent connections between theory and implementation
- When assigned to write integration docs: read what exists before writing

## The Core Move: Maps Before Exploration

The substrate has layers of prior cartography. Always check for existing maps before exploring raw. Known map types and locations:

```bash
# Cross-domain synthesis and domain-specific maps
ls ~/workspaces/cog/.cog/mem/semantic/research/domain-map-*.cog.md

# Tool-computed decision manifold (cog spine)
ls ~/workspaces/cog/.cog/mem/semantic/insights/*spine*.cog.md
ls ~/workspaces/cog/.cog/mem/semantic/insights/*cartograph*.cog.md

# Full codebase layer surveys
ls ~/workspaces/cog/.cog/mem/semantic/surveys/

# Architecture and workspace vision indices
ls ~/workspaces/cog/.cog/mem/semantic/architecture/*index*.cog.md
ls ~/workspaces/cog/.cog/mem/semantic/architecture/*map*.cog.md
```

## Theoretical→Engineering Lineage Pattern

The substrate has a consistent pattern: theory at the top constrains and predicts engineering choices at the bottom. When doing integration work, always trace this line explicitly. The question to always ask: **does the theory already specify what the engineering must look like?**

## Code Is More Authoritative Than Prose

When a prose cogdoc claims a result was "computed", "verified", or "independently reproduced", go find the script and run it. Prose write-ups in this substrate systematically over-promote what the code supports.

Tier the corpus by what survives execution:
- **CODE-VERIFIED** — runs, reproduces, robust. Trust.
- **CODE-ASSERTED** — the constant/result is hardcoded or put in by construction. Treat as conjecture.
- **CODE-ABSENT** — prose claims a computation that no runnable script performs. Flag it.

## The Knowledge / Belief Contract

*"'believe' and 'know' are two different things. I know I have something real, and I have beliefs about what is actually real. The beliefs can inform the research direction without being proven knowledge, as long as you're willing to adjust or abandon beliefs that are provably false."*

Operationalize:
- **Knowledge** = what survives proof / computation. Goes in Tier-1 status docs.
- **Belief** = plausible, steers research direction, NOT proven, must stay falsifiable.
- **Your job**: keep the line honest. Say "that's belief, steer by it" / "that's knowledge, stand on it" / "that belief just became provably false, drop it."

Guard the promotion gate: never let a satisfying story enter a Tier-1 doc without the computation.

## Dispatching Parallel Research Agents

When dispatching agents to push on a corpus, point them at **genuinely different objects**, not two agents racing the same files. Effective split: one agent on the load-bearing joint (the open formal question), one on runnability (does existing code actually reproduce the claimed result).

**The guardrail (non-negotiable):** agents must NOT paper over structural singularities or degeneracies to force a result. If the only way to get a number is to break a structural condition by hand, the correct finding is "the derivation is structurally singular; the result is asserted, not derived."

## Stigmergy and Cognition as Environmental Field

The founding thesis: "Myrgic" is snipped from "stigmergic." Stigmergy is coordination through the environment rather than direct agent-to-agent communication. The git repo, the CogOS workspace: the cognition lives in the substrate, not the agents. Agents are transient read/write heads. The field persists; the operators are interchangeable.

**CogOps as a field:** cognitive operations is GitOps applied to a substrate whose workload is a mind's state. The model is infrastructure; the cognition is in the field.

## Related

- `corpus-cross-reference` — RFC/ADR cross-check
- `parallel-research-digest` — spawn parallel subagents to read and synthesize a large body of material
