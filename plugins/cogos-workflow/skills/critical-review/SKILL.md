---
name: critical-review
description: Rigorous evaluation of arguments, theories, claims, and architectural decisions. Includes steel-manning, assumption hunting, scope validation, falsification analysis, and alternative explanations. Use when reviewing designs, proposals, or technical claims before committing to them.
---

# Critical Review Skill

Protocols for rigorous evaluation of arguments, theories, and claims.

## The Review Process

### 1. Understand Before Critiquing

Never critique a strawman. First:

1. State the claim in your own words
2. Identify the strongest version of the argument
3. Ask clarifying questions if anything is unclear
4. Confirm understanding before proceeding

### 2. Steel-Man First

> "I think you're saying X, where X is the strongest version I can construct. Is that right?"

If you can't state the argument in a way the author would accept, you don't understand it yet.

## Assumption Hunting

### Every Argument Has Hidden Premises

Look for:

1. **Definitional assumptions** - How are key terms defined?
2. **Empirical assumptions** - What facts are taken as given?
3. **Methodological assumptions** - Why is this approach valid?
4. **Value assumptions** - What's being optimized for?

### Template

```markdown
## Assumption Analysis: {claim}

### Stated Premises
1. {explicit premise 1}
2. {explicit premise 2}

### Hidden Premises
1. {assumption} - Is this justified? {yes/no/unclear}
2. {assumption} - Is this justified? {yes/no/unclear}

### Depends On
- {external claim that must be true}
- {condition that must hold}

### If These Fail
- Without {assumption 1}: {consequence}
- Without {assumption 2}: {consequence}
```

## Scope Validation

### Claims vs Evidence

For every claim, ask:
- What exactly is being claimed?
- What evidence supports it?
- Does the evidence actually support this claim, or a weaker one?

### Scope Creep Indicators

| Red Flag | Example |
|----------|---------|
| "This shows that..." | Does it show, or suggest? |
| "Obviously..." | If obvious, why argue it? |
| "All X are Y" | Every single one? |
| "This proves..." | Proof or strong evidence? |
| "The data clearly..." | Clear to whom? What alternative interpretations? |

### Scope Clarification Template

```markdown
## Scope Analysis: {claim}

### Claimed Scope
{What the argument says it shows}

### Actual Scope
{What the evidence actually supports}

### Gap
{Difference between claimed and actual}

### To Close Gap Would Require
{What additional evidence/argument is needed}
```

## Falsification

### What Would Make This Wrong?

Every good theory specifies what would falsify it.

Questions to ask:
- What evidence would change your mind?
- What would have to be true for this to fail?
- Is this claim falsifiable at all?

### Template

```markdown
## Falsification Analysis: {claim}

### The Claim Would Be False If:
1. {condition 1}
2. {condition 2}

### Have These Been Checked?
- {condition 1}: {checked/not checked/cannot be checked}
- {condition 2}: {checked/not checked/cannot be checked}

### Falsifiability Assessment
{Highly falsifiable / Somewhat falsifiable / Unfalsifiable}

### If Unfalsifiable
{Why this is or isn't a problem for this type of claim}
```

## Alternative Explanations

### What Else Could Explain This?

For any observation, consider:
- What other hypotheses are consistent with this data?
- Has the argument ruled these out?
- Are there simpler explanations?

### Template

```markdown
## Alternative Explanations: {observation}

### Proposed Explanation
{The claim being made}

### Alternative 1: {name}
- Explanation: {how this accounts for the observation}
- Evidence for: {what supports this alternative}
- Evidence against: {what weakens this alternative}
- Ruled out by: {why we can/can't dismiss this}

### Alternative 2: {name}
...

### Comparative Assessment
{Which explanation is best supported and why}
```

## Logical Structure

### Argument Mapping

Break arguments into:
1. Premises (claimed facts)
2. Inferences (logical steps)
3. Conclusions (what follows)

### Common Fallacies

| Fallacy | Pattern | Example |
|---------|---------|---------|
| Affirming consequent | If A then B; B; therefore A | Wet streets -> rain; streets wet; must be rain |
| Denying antecedent | If A then B; not A; therefore not B | Rain -> wet streets; no rain; streets dry |
| False dichotomy | Either A or B; not A; therefore B | Ignores options C, D, ... |
| Equivocation | X (meaning 1); therefore X (meaning 2) | Word means different things |
| Begging question | Assuming what you're proving | Circular reasoning |

### Logical Check Template

```markdown
## Logical Analysis: {argument}

### Structure
Premise 1: {P1}
Premise 2: {P2}
...
Inference: {from P1, P2 we get...}
Conclusion: {C}

### Validity
{Does conclusion follow from premises? Yes/No}
If no: {what's the logical gap}

### Soundness
{Are the premises true?}
- P1: {true/false/uncertain}
- P2: {true/false/uncertain}
```

## The Review Document

### Full Review Template

```markdown
# Critical Review: {title/claim}

## Summary
{Brief restatement of what's being claimed}

## Steel-Man Version
{Strongest form of the argument}

## Strengths
- {what the argument does well}
- {what's compelling}

## Concerns

### 1. {concern title}
**Issue:** {description}
**Impact:** {how serious}
**Suggestion:** {how to address}

### 2. {concern title}
...

## Questions
- {clarifying question 1}
- {clarifying question 2}

## Verdict
{Overall assessment: Strong / Promising but needs work / Significant problems / Fundamental issues}

## Recommendations
1. {priority action 1}
2. {priority action 2}
```

## Reviewer Calibration

### Be Tough, Not Mean

- Attack arguments, not people
- Explain why something is a problem, not just that it is
- Suggest solutions when possible
- Acknowledge when you might be wrong

### Useful Framing

Instead of:
- "This is wrong" -> "This seems to assume X, which may not hold because..."
- "You forgot Y" -> "How does this account for Y?"
- "This doesn't work" -> "I'm having trouble seeing how A leads to B here"

### Your Job

You're helping make the work better, not proving you're smart. The goal is work that survives peer review, not work that survives you.
