---
name: cold-start
description: Write a cold-start handoff document for a project, feature, or initiative. Creates a standalone briefing that allows any agent or human with zero prior context to understand the full picture and continue the work. Also invocable as /handoff.
---

# Cold-Start Handoff

Write a document complete enough that an agent or human with **zero prior context** can orient, understand the full picture, and start contributing immediately. No "check the prior conversation" hand-waving. No assumed knowledge. Everything needed is in the document or explicitly linked.

This format is a **temporal handoff artifact** -- a bridge between two contexts. It is neither a standing doc (like ARCHITECTURE.md) nor a historical record (like an ADR). It is written by one agent or human for the next, at a moment when context is about to be lost.

## Prior Art Incorporated

This format draws from established standards:

| Source | What we adopt |
|--------|---------------|
| **BLUF** (military) | Conclusion/state/action-needed in the first paragraph |
| **OPORD** (military) | Situation, Mission, Execution, Resources, Comms structure |
| **ADR/MADR** | Decisions with reasoning and tradeoffs (compressed, not full ADRs) |
| **ARCHITECTURE.md** (matklad) | Stable code map with module descriptions |
| **llms.txt** (Answer.AI) | Two-tier model: overview for quick load, links for depth |
| **Diataxis** | Reference + explanation for handoffs, not tutorials |
| **PARA** | Actionability hierarchy: active now / always true / archived |
| **Intelligence briefs** | Confidence marking: confirmed / assessed / experimental / broken |

## What This Format Adds

1. **Temporal state** -- "Here is where things stand RIGHT NOW." Work-in-progress, momentum, next actions.
2. **Confidence marking** -- Each section of current state is tagged: working (confirmed), in-progress (assessed), not-started (planned), broken (known issue).
3. **Agent-substrate portability** -- Works regardless of which LLM or framework picks it up. No vendor-specific assumptions.
4. **Decision compression** -- Key choices and constraints in a few lines each, with links to full rationale.
5. **Handoff-as-artifact** -- Explicitly temporal: "I am writing this because context is about to be lost."

## When to Use

- Handing off a project to another agent, team member, or contractor
- Capturing the state of a complex initiative at a milestone
- Creating onboarding material for a codebase or feature area
- Archiving a decision-rich session so future instances can pick up cleanly
- Sharing work across trust boundaries (personal to work, team to team)

## Structure

Follow this order. The order matters -- it moves from orientation to action, with BLUF at the top.

### 0. BLUF (Bottom Line Up Front)

3-5 sentences maximum. Answer: What is this? What state is it in? What needs to happen next? A reader who stops here should know whether this document is relevant to them.

### 1. What Is This

State what the project/feature/system IS in plain language. Not what it does -- what it IS. A reader should be able to explain it to someone else after reading just this section. Define all project-specific terms on first use.

### 2. Why It Exists

The problem it solves. The motivation. What is wrong with the world without it. Keep it concrete -- no marketing language. If there is a thesis document, link to it.

### 3. Key Decisions (with reasoning)

Compressed decision digest. Each entry:
```
**Decision:** What was decided
**Why:** The reasoning (1-2 sentences)
**Tradeoff:** What we gave up
**Link:** Full ADR or discussion (if it exists)
```

These are the things a new person would otherwise re-derive or second-guess. Include enough reasoning that a reader can judge whether the decision still holds given changed circumstances.

### 4. The Architecture / Design

How the pieces fit together. Use ASCII diagrams, tables, or structured lists. This should be scannable -- someone should be able to find "where does X happen" quickly.

For layered systems, show the stack. For distributed systems, show the topology. For monoliths, show the module map. Match the diagram to the architecture.

### 5. Repository / File Map

Annotated directory tree with one-line descriptions. A new agent spends most of its early time figuring out what is where -- front-load this. Use the ARCHITECTURE.md "code map" convention: stable structural overview, not implementation detail.

### 6. Current State

**This is the section no existing standard handles well.** Be ruthlessly honest. Use confidence markers:

- **Working** (confirmed): compiles, tests pass, deployed, relied upon
- **In progress** (assessed): partially built, may compile, incomplete
- **Planned** (designed): architecture exists, code does not
- **Broken** (known issue): exists but does not work, with reason

A reader who acts on a false "this works" wastes time. A reader who knows something is broken can either fix it or route around it.

### 7. How to Build / Run / Test

Concrete commands. Copy-paste ready. Include prerequisites. If there are multiple environments or configurations, show each. If something requires manual steps (API keys, tokens, signing), say so explicitly.

### 8. What to Build Next (dependency-ordered)

Prioritized by dependency, not wishful thinking. Each item:
```
**What:** Brief description
**Why:** What it unblocks
**Depends on:** What must be done first (or "nothing")
**Estimated scope:** Small / Medium / Large
```

### 9. Constraints

Hard constraints the reader must respect. Platform requirements, subscription limitations, tool restrictions, organizational boundaries, trust scope boundaries. Things that are not obvious from the code.

### 10. Key Files to Read (ordered)

A reading list. 5-10 files, in the order they should be read, with one-line explanations of what each contributes. This is the guided tour. A reader who follows this list in order builds a correct mental model.

## Principles

- **BLUF always.** Lead with the state and the ask. Details follow.
- **Assume zero.** The reader has never seen this codebase, never talked to you, and does not know your abbreviations.
- **Orient before instruct.** What, why, how, where, what next.
- **Be honest about state.** Confidence markers are not optional.
- **Link, don't inline.** The handoff is a map, not an encyclopedia. Point to full documents.
- **Include the reasoning.** Decisions without reasoning are indistinguishable from arbitrary choices.
- **Date it.** Cold-start documents decay. The reader needs to know how fresh the information is.
- **Make it portable.** No vendor-specific assumptions. Works for any agent, any LLM, any human.

## Quality Check

Before finalizing, verify:
- [ ] Could someone with zero context read only this document and know what to do next?
- [ ] Does the BLUF accurately capture the current state in under 5 sentences?
- [ ] Are all decisions explained with reasoning?
- [ ] Is every piece of current state tagged with a confidence marker?
- [ ] Are build/run commands copy-paste ready?
- [ ] Is every abbreviation or project-specific term defined on first use?
- [ ] Are file paths absolute or clearly relative to a stated root?
- [ ] Is the document dated?
- [ ] Could this be shared across a trust boundary without leaking private context?

## Output

Write the handoff document as a markdown file. Naming conventions:
- For a whole project: `docs/{project}-cold-start.md`
- For a feature area: `docs/{feature}-cold-start.md` or alongside the code
- For sharing across trust boundaries: ensure the document is self-contained with no references to private memory, personal workspace state, or session history

## Anti-Patterns

- **"See the conversation from March 28th"** -- If it is not in the document or a linked file, it does not exist for the reader.
- **Assuming tool familiarity** -- Do not say "use the CLI" without explaining what it is and where it lives.
- **Wishful state reporting** -- "The server is almost done" is meaningless. What compiles? What passes tests? What is behind a build tag?
- **Priority without dependency** -- "Build the UI" is useless if it depends on three unbuilt backends.
- **Vendor lock-in** -- "Run /slash-command" assumes a specific agent platform. Describe the action, not the invocation.
- **Implicit context** -- "As discussed" or "the usual approach" assumes shared history that does not exist.
