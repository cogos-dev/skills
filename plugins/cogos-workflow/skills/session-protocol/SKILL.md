---
name: session-protocol
description: Protocols for starting and ending work sessions - initialization, checkpointing, handoffs, and continuity. Use when beginning or ending a session, or creating handoff documentation.
version: 1.0.0
author: myrgic
tags: [session-management, checkpointing, handoff, continuity]
canonical_source: "~/workspaces/cog/.claude/skills/session-protocol/SKILL.md"
projection_note: >
  This is the public marketplace projection. Content is unchanged from the
  canonical source — the skill has no operator-specific material to strip.
  Update canonical first; project here after.
---

# Session Protocol Skill

Protocols for managing work session boundaries and continuity.

## Session Start Protocol

### 1. Orient

Understand current state before proceeding:

```markdown
## Session Orientation

**Date:** {YYYY-MM-DD}
**Context:** {brief description of what we're working on}

### What I Know
- {Key context from previous session}
- {Active tasks or goals}

### What I Need to Check
- [ ] Current state of {X}
- [ ] Status of {Y}
- [ ] Any blockers or changes
```

### 2. Verify

Check environment and dependencies:

- [ ] Required tools available
- [ ] Dependencies installed
- [ ] Access to needed resources
- [ ] No blocking issues

### 3. Resume or Start Fresh

If continuing previous work:
- Review last session's notes
- Check any pending items
- Verify state matches expectations

If starting new work:
- Document objectives clearly
- Create initial structure
- Note any assumptions

## During Session

### Progress Markers

Create checkpoints at natural boundaries:

```markdown
## Checkpoint: {description}
**Time:** {HH:MM}
**Status:** {in_progress | completed | blocked}

### Completed
- {item 1}
- {item 2}

### In Progress
- {current task}

### Blocked On
- {blocker, if any}
```

### Decision Recording

When making significant decisions:

```markdown
## Decision: {title}

**Context:** Why this came up
**Options Considered:**
1. {option 1} - {pros/cons}
2. {option 2} - {pros/cons}

**Decision:** {what we chose}
**Rationale:** {why}
```

## Session End Protocol

### 1. Checkpoint State

Save all work in progress:

- [ ] All files saved
- [ ] Work committed (if using version control)
- [ ] Intermediate results preserved

### 2. Document Status

Create session summary:

```markdown
## Session Summary: {YYYY-MM-DD}

### Accomplished
- {completed item 1}
- {completed item 2}

### In Progress
- {task} - {current state}

### Blocked / Needs Attention
- {issue} - {what's needed}

### Next Steps
1. {priority 1}
2. {priority 2}
```

### 3. Create Handoff

If someone else will continue:

```markdown
## Handoff Document

### Context
{What we're working on and why}

### Current State
{Where things stand right now}

### Key Files / Locations
- `{path}` - {description}
- `{path}` - {description}

### What's Working
- {item}

### Known Issues
- {issue}

### Recommended Next Steps
1. {step 1}
2. {step 2}

### Questions / Decisions Needed
- {question 1}
- {question 2}
```

## Session Continuity Patterns

### The "5 Minute Rule"

If you can't explain current state in 5 minutes, documentation is insufficient.

### Context Recovery

When resuming after a break:

1. Read previous session summary
2. Check for any changes (git status, file dates)
3. Run a small verification task
4. Update orientation before proceeding

### Handoff Quality Checklist

- [ ] New person can understand context without asking questions
- [ ] All relevant files/locations listed
- [ ] Current state is accurate and verifiable
- [ ] Next steps are actionable
- [ ] Known issues are documented with workarounds if any

## Session Artifacts

Each session should produce:

| Artifact | Purpose | When |
|----------|---------|------|
| Orientation | Start context | Session start |
| Checkpoints | Progress markers | During |
| Decisions | Rationale record | As needed |
| Summary | What happened | Session end |
| Handoff | Continuity | If needed |

## Templates

### Quick Start Template

```markdown
# Session: {YYYY-MM-DD}

## Goal
{What we're trying to accomplish}

## Notes
{Running log of what happens}

## Summary
{Fill in at end}
```

### Full Session Template

```markdown
# Session: {YYYY-MM-DD}

## Orientation
**Context:** {continuing from / starting fresh}
**Goal:** {session objective}
**Time Budget:** {expected duration}

## Environment Check
- [ ] Tools ready
- [ ] Dependencies met
- [ ] Resources available

## Session Log

### {HH:MM} - Start
{Initial notes}

### {HH:MM} - {Activity}
{What happened, what was learned}

## Decisions Made
{Link to decision records if any}

## Summary

### Completed
- {items}

### Next Session
- {priorities}

### Notes for Future
- {anything worth remembering}
```
