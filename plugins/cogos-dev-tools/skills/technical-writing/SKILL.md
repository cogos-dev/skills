---
name: technical-writing
description: Protocols for effective technical documentation - structure, clarity, specification, and executor-oriented writing. Use when writing specifications, reports, proposals, or documentation.
---

# Technical Writing Skill

Protocols for documents that survive contact with readers and executors.

## Core Principles

### 1. Executor-Oriented

Every document has a reader who needs to **do** something with it. Write for them.

Questions to answer:
- Who reads this?
- What do they need to do?
- What do they need to know to do it?

### 2. Clarity Over Elegance

Ambiguity is a bug. If two readers could interpret a sentence differently, rewrite it.

### 3. Structured for Scanning

Most readers won't read linearly. Use:
- Headers for navigation
- Tables for structured data
- Lists for enumerated items
- Front-loaded key information

## Document Structure

### Standard Elements

| Element | Purpose | Position |
|---------|---------|----------|
| Title | What is this | Top |
| Summary | Key points upfront | After title |
| Context | Why this exists | Early |
| Body | Main content | Middle |
| Limitations | What this isn't | Near end |
| Next steps | What to do | End |

### Revision Control

Every document should track changes:

```markdown
## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 0.2 | YYYY-MM-DD | Name | Added failure modes section |
| 0.1 | YYYY-MM-DD | Name | Initial draft |
```

## Scoping Claims

### Be Precise

| Vague | Precise |
|-------|---------|
| "It should work" | "Success if latency < 100ms for 99% of requests" |
| "Large improvement" | "30% reduction in error rate" |
| "We expect" | "Hypothesis: X > Y under condition Z" |
| "Good performance" | "Throughput > 1000 req/s on standard hardware" |

### Scope Statements

Always include:

```markdown
## Scope

### In Scope
- {What this covers}
- {What this covers}

### Out of Scope
- {What this does NOT cover}
- {What this does NOT cover}
```

## Success Criteria

### Make Them Measurable

```markdown
## Success Criteria

| Criterion | Metric | Target | Measurement |
|-----------|--------|--------|-------------|
| Accuracy | F1 score | > 0.85 | Held-out test set |
| Speed | Latency p99 | < 200ms | Load test results |
| Reliability | Uptime | > 99.9% | Monitoring |
```

### Null Hypothesis

For research documents:

```markdown
## Hypothesis
{What we believe to be true}

## Null Hypothesis
{What we'd expect if there's no effect}

## Success Criterion
We reject the null if: {specific criterion}
```

## Failure Modes

### Document What Can Go Wrong

```markdown
## Failure Modes

| Failure | Detection | Impact | Response |
|---------|-----------|--------|----------|
| Database timeout | Health check fails | Service degraded | Fallback to cache |
| Invalid input | Validation error | Request rejected | Return 400 with message |
| Memory exhaustion | OOM killer | Process restart | Auto-restart, alert |
```

## Writing Guidelines

### Sentences

- Lead with the point
- One idea per sentence
- Active voice over passive
- Concrete over abstract

```
# Passive (weak)
It was found that the system was slow.

# Active (strong)
The system took 3 seconds to respond.
```

### Paragraphs

- One topic per paragraph
- Topic sentence first
- Supporting details follow
- Transition to next topic

### Technical Terms

- Define on first use
- Be consistent (same term for same concept)
- Don't use synonyms for "variety"

## Tables vs Prose

### Use Tables For

- Parameters and their values
- Comparisons across items
- Success criteria
- Failure modes
- Status tracking

### Use Prose For

- Motivation and context
- Sequential narrative
- Arguments and reasoning
- Interpretation of results

## Document Templates

### Specification

```markdown
# {Feature/System} Specification

## Summary
{One paragraph: what this is and why}

## Context
{Background needed to understand}

## Requirements

### Functional
- [ ] {Requirement 1}
- [ ] {Requirement 2}

### Non-Functional
| Requirement | Target |
|-------------|--------|
| Latency | < X ms |
| Throughput | > Y req/s |

## Design

### Overview
{High-level description}

### Components
{Detailed breakdown}

## Success Criteria
{How we know we succeeded}

## Failure Modes
{What can go wrong and how we handle it}

## Open Questions
- {Question 1}
- {Question 2}

## Revision History
| Version | Date | Changes |
```

### Proposal

```markdown
# Proposal: {Title}

## Summary
{What we propose and why}

## Problem
{What problem this solves}

## Proposed Solution
{What we want to do}

## Alternatives Considered
| Alternative | Pros | Cons |
|-------------|------|------|

## Implementation Plan
1. {Step 1}
2. {Step 2}

## Risks
| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|

## Success Criteria
{How we measure success}

## Timeline
{Expected schedule}

## Resources Needed
{What this requires}
```

### Report

```markdown
# {Title} Report

## Executive Summary
{Key findings in one paragraph}

## Context
{Why this work was done}

## Methodology
{How the work was done}

## Results
{What was found}

## Analysis
{What the results mean}

## Limitations
{What this doesn't tell us}

## Conclusions
{What we conclude}

## Recommendations
{What to do next}

## Appendix
{Supporting data}
```

## Review Checklist

Before finalizing:

### Clarity
- [ ] Could someone unfamiliar understand this?
- [ ] Are all terms defined?
- [ ] Is the structure logical?

### Completeness
- [ ] Are all claims scoped?
- [ ] Are success criteria measurable?
- [ ] Are limitations acknowledged?
- [ ] Is there a next steps section?

### Accuracy
- [ ] Are facts verified?
- [ ] Are numbers correct?
- [ ] Are references accurate?

### Usability
- [ ] Can a reader find what they need?
- [ ] Are tables/lists used appropriately?
- [ ] Is it scannable?
