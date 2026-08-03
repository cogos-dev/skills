---
name: suggest
description: Pause and produce a numbered decision menu — invariants, context, and 3-5 options the user can pick by number or override with a custom message. Use when the user types /suggest mid-conversation.
version: 1.0.0
author: myrgic
tags: [decision-menu, ux-pattern, interrupt, session-technique]
canonical_source: "~/.claude/skills/suggest/SKILL.md"
projection_note: >
  This is the public marketplace projection. Content is unchanged from the
  canonical source — the skill has no operator-specific material to strip.
  Update canonical first; project here after.
---

# Skill: suggest

A fast decision-aid pattern. The user types `/suggest`; you pause whatever you're doing, simulate the user's perspective on your own most recent output, and produce a structured menu they can respond to with a single number (or a custom message).

The friction this resolves: you're mid-output proposing or implying choices; the user is reading and wants to direct the next step *quickly*, without typing a long response. The numbered-option pattern gives them keyboard speed; the invariants and context give them confidence the options are sane.

<invocation>
MUST produce: three sections — Invariants, Context, Options — followed by a one-line response prompt.
MUST NOT produce: continued execution, new tool calls, or open-ended prose. The skill is a pause, not a continuation.
Input: the user's typed `/suggest` (no other args needed; you read your own preceding output).
Output: structured menu matching the `<output_contract>` below.
Success: the user can respond with a single number, get the action they want, and continue.
</invocation>

<do_not>
MUST NOT continue the work you were doing — `/suggest` is an interrupt that produces a menu, not a continuation that produces both a menu and more work.
MUST NOT generate options that are obviously redundant ("option 2: same as option 1 but slower"). If you can't produce 3 distinct options, produce 2 plus a clearly-orthogonal third (e.g., "stop and tell me more").
MUST NOT include implementation detail in option labels. The label is the *choice*; the body is the consequence.
MUST NOT make the recommended option the default by ordering — mark it explicitly with `(Recommended)` if you have a preference, otherwise rank by likelihood-of-fit.
MUST NOT exceed 5 options or 5 bullets per section. Cognitive budget for fast-decision is small; keep the menu scannable.
</do_not>

## When to use

The user types `/suggest`. That's the only trigger. The user is asking for a fast menu *now* about whatever you most recently produced or are about to do.

You may also internally invoke this pattern (without the user typing `/suggest`) when you notice you're about to ask a multi-clause open-ended question — collapsing the question into a numbered menu is usually a better experience.

## What to do

1. **Stop your current work.** Do not continue editing, dispatching, or analyzing. The skill is a pause.
2. **Re-read your own most recent output** (and the user's most recent message it responded to) with the user's perspective in mind:
   - What choices does that output expect or imply?
   - What's at stake — what changes between options?
   - What context is the user holding that you should reflect back so they don't have to load it themselves?
3. **Produce the menu** in the format below.
4. **Stop.** Do not continue acting until the user responds.

## Output contract

```
**Invariants** (constraints that must hold regardless of what you choose):
- <up to 5 short bullets — things that won't change between options>

**Context** (situation-shaping facts to hold while choosing):
- <up to 5 short bullets — things that distinguish the options or constrain the timing>

**Options**:
1. **<short label, ≤8 words>** — <1-2 lines: what it does + main tradeoff>
2. **<short label>** — <1-2 lines>
3. **<short label> (Recommended)** — <1-2 lines: marked when you have a clear preference>
4. **<optional, if there's a meaningfully distinct fourth option>**
5. **<optional, if a fifth genuinely earns its slot>**

Reply with a number, or a custom message that overrides, combines, or forks these.
```

If you have no clear preference, omit `(Recommended)`. Don't fake it.

## Examples

<example>
**Conversation state**: Claude has just finished a research pass and is about to dispatch implementation work. Output ended with "I'll dispatch three agents in parallel for the refactor." User types `/suggest`.

**Skill output**:

**Invariants**:
- The refactor must preserve existing public API
- Tests must pass on darwin-arm64 and linux-amd64 before any PR
- No push without explicit approval

**Context**:
- The three subdirectories are independent — agents won't conflict
- One of them touches the build path; cost of regression is high
- Currently on `main` synced with upstream; clean working tree

**Options**:
1. **Dispatch all three in parallel** — fastest; relies on tests catching cross-module issues
2. **Dispatch the high-cost one alone first; other two after it lands (Recommended)** — sequential safety on the high-cost path; a bit slower wall-clock
3. **Pause and let me sketch the API contract first** — adds upfront review; reduces rework risk if interfaces drift
4. **Stop and tell me more about the regression risk** — useful if you want deeper analysis before committing to dispatch

Reply with a number, or a custom message that overrides, combines, or forks these.
</example>

## Discipline

- **Simulate the user's perspective.** You're producing the menu they would build for themselves if they had time. That means: their constraints (invariants), their working memory (context), their plausible next steps (options).
- **One option should refuse the framing.** When you can, include an option that exits the menu's frame — "stop and tell me more," "drop this branch entirely," "pause until I clarify X." Real choice spaces include the option to step out.
- **Recommend honestly.** Mark `(Recommended)` only when you actually prefer one option. If three are roughly equal, say so by omitting the marker.
- **The user's response is authoritative.** If they reply `2`, do option 2 without re-questioning. If they reply with a custom message, treat that as the new directive — don't re-litigate against the menu.

## Reference

The pattern operationalizes a general instinct worth carrying into any agent's default behavior: for exploratory questions, respond briefly with a recommendation and the main tradeoff, presented as something the user can redirect rather than a decided plan. `/suggest` turns that into a typed menu when the user wants speed.
