---
name: retrospective
description: Re-examine earlier work through the lens of a new result, milestone, or discovery. Launches parallel analyst agents per domain, producing standardized retrospective reports that track what changed, what was validated, and what new questions opened.
---

# Retrospective Analysis

Re-examine earlier documents and decisions through the lens of a new result (theorem, proof, milestone, gap closure, or significant discovery). Produces standardized retrospective reports.

## When to Use

- A major result has been established and you want to trace its implications through earlier work
- A milestone occurred and you need to reassess claims that depended on it
- A gap closure happened and previously speculative claims may now be provable or falsifiable
- The user says "run retrospective agents" or "re-examine early work through X lens"

## How to Invoke

Launch one subagent per domain using the Task tool or dispatch-agent skill with `run_in_background: true`. Run them in parallel.

### Prompt Template

```
You are a retrospective analyst.

**New Result:** {statement of the new result}
**Date:** {date}
**Reference:** {path to proof/document}

Re-examine the following documents through this lens:
1. {path1}
2. {path2}
...

For each document, assess:
- What was claimed and at what confidence level?
- Does the new result change the status of any claims?
- Which claims are now provable or falsifiable that were not before?
- Are there early intuitions that turned out to be correct?

**Write your report to:**
  {output_directory}/{date}-{domain-slug}-retrospective.md

Use the standard report format below.
```

## Output Location

Place reports in a designated retrospective directory:
`{output_directory}/{date}-{domain-slug}-retrospective.md`

- `{date}` = ISO date of triggering result (e.g., `2026-03-11`)
- `{domain-slug}` = kebab-case domain name (e.g., `backend-api`, `auth-system`, `data-pipeline`)

## Report Format

### Frontmatter

```yaml
---
created: "{date}"
type: retrospective
trigger: "{name of triggering result}"
scope: "{comma-separated keywords}"
documents_reviewed:
  - {relative path to each document}
---
```

### Body Structure

```markdown
# Retrospective: {Domain Title}

## The Shift
One paragraph: the single biggest change the new result introduces for this domain.

## Document-by-Document

### 1. {Document Title} ({Date})
**Claimed:** What was the original claim?
**Then:** What confidence level at the time?
**Now:** What changes with the new result?
**Verdict:** Promoted / Corrected / Unchanged -- then explanation.

(repeat for each document)

## Cross-Cutting Findings

### Promoted (speculation -> confirmed)
| Claim | Before | After | Mechanism |
|-------|--------|-------|-----------|

### Corrected (right intuition, wrong mechanism)
List of claims where the conclusion was right but the route was wrong.

### Unchanged
Claims unaffected by the new result.

### Early Intuitions Validated
Numbered list of insights that turned out correct before justification existed.

## Open Problems
Numbered list of concrete, testable questions opened or sharpened by the new result.
```

## Guidelines

1. **Be honest about confidence levels.** Use a consistent scale. Do not inflate.
2. **Distinguish mechanism from conclusion.** Right conclusion via wrong mechanism -- note both.
3. **Quote early documents directly** when claims are now validated or corrected.
4. **Separate coincidences from structural identities.** The new result may promote some and demote others.
5. **Flag cross-domain connections** prominently when the same pattern appears in multiple areas.
6. **The new result is the lens, not the conclusion.** Re-evaluate OLD work; do not extend the new result.

## Example Invocation

After completing a major refactor or proving a key result, launch domain-specific retrospective agents:

```
Task(description="Retrospective: API layer",       domain="api-layer")
Task(description="Retrospective: Auth system",      domain="auth-system")
Task(description="Retrospective: Data pipeline",    domain="data-pipeline")
Task(description="Retrospective: Client SDK",       domain="client-sdk")
```

Each produces a report at `{output_directory}/{date}-{domain}-retrospective.md`.

## Confidence Scale

Use a consistent scale for before/after assessments:

| Level | Meaning |
|-------|---------|
| **Confirmed** | Proven, tested, relied upon |
| **Assessed** | Strong evidence, high confidence |
| **Experimental** | Partial evidence, moderate confidence |
| **Speculative** | Hypothesis, low confidence |
| **Broken** | Known to be wrong or outdated |

## Anti-Patterns

- **Retroactive rationalization** -- Do not rewrite history to make past decisions look better. Report what was actually claimed and believed.
- **Scope inflation** -- The retrospective is about re-evaluating old work, not extending the new result into new territory.
- **Missing the tensions** -- Disagreements between old claims and new results are the most valuable findings. Do not smooth them over.
- **Skipping open problems** -- Every good retrospective should surface new questions, not just validate old answers.
