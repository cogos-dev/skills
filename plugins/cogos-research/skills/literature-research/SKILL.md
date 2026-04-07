---
name: literature-research
description: Structured literature review and source synthesis. Guides systematic search, source evaluation, claim extraction, and cross-reference analysis. Use when researching a technical topic, evaluating prior art, or building a knowledge base from published sources.
---

# Literature Research Skill

Protocols for navigating and curating academic and technical literature.

## The Literature Search Process

### 1. Establish Entry Points

Before deep diving:

1. Find a recent **review paper** (saves months)
2. Identify the **foundational papers** (the ones everyone cites)
3. Note the **key authors** (who's doing the best work)
4. Map the **subfields** (different communities, different terminology)

### 2. Trace Citations

Two directions:

- **Backward** (who did they cite?) - Find foundations
- **Forward** (who cited them?) - Find developments

### 3. Build a Reading Map

Don't just collect papers. Map them:

```markdown
## Literature Map: {topic}

### Foundational (must read)
1. {Author, Year} - {title} - {why it matters}
2. {Author, Year} - {title} - {why it matters}

### Review Papers
1. {Author, Year} - {coverage scope}

### Active Research Fronts
- {Front 1}: {key papers}
- {Front 2}: {key papers}

### Different Names for Same Concept
- In {field 1}: "{term 1}"
- In {field 2}: "{term 2}"

### Key Authors
- {Name}: Known for {contribution}
- {Name}: Known for {contribution}

### Reading Order
1. Start with: {paper} (accessible introduction)
2. Then: {paper} (core theory)
3. Then: {paper} (modern treatment)
```

## Finding Papers

### Search Strategies

| Source | Best For | Limitations |
|--------|----------|-------------|
| Google Scholar | Broad search, citation counts | Noisy, includes low-quality |
| Semantic Scholar | AI-organized, related papers | Smaller corpus |
| arXiv | Preprints, cutting edge | No peer review |
| DBLP | CS specifically | Limited to CS |
| PubMed | Bio/medical | Domain-specific |

### Search Tips

1. **Use author names** - Once you find good work, find more by same author
2. **Check "cited by"** - Forward citation is gold
3. **Check references** - Backward citation for foundations
4. **Look for surveys** - "{topic} survey" or "{topic} review"
5. **Try different terms** - Same idea, different names in different fields

## Evaluating Papers

### Quality Signals

| Signal | What It Tells You |
|--------|-------------------|
| Venue | Conference/journal reputation |
| Citations | Impact (with lag) |
| Author track record | Reliability |
| Methodology clarity | Reproducibility |
| Engagement with prior work | Scholarship |

### Warning Signs

| Red Flag | Possible Issue |
|----------|----------------|
| No related work section | Doesn't know the field |
| Claims novelty without checking | Reinvention |
| Cites only own work | Isolation |
| Methodology vague | Not reproducible |
| Overclaims results | Hype |

### Quick Evaluation Checklist

- [ ] Read abstract: Is the claim clear?
- [ ] Scan figures/tables: What's actually shown?
- [ ] Check related work: Do they know the field?
- [ ] Look at methodology: Could you reproduce this?
- [ ] Find the limitations: Are they honest?

## Reading Strategies

### Triage Reading (5 minutes)

1. Title and abstract
2. Figures and tables
3. Conclusion
4. Decision: Read fully? Skim? Skip?

### Skimming (20 minutes)

1. Introduction (motivation, claims)
2. Method (high level)
3. Results (key findings)
4. Discussion (interpretation)

### Deep Reading (2+ hours)

1. Full text, taking notes
2. Check key equations/proofs
3. Think about assumptions
4. Connect to other work
5. Identify questions

## Reference Management

### What to Track

For each paper:

```markdown
## {Author, Year} - {Short title}

**Full citation:** {full bibliographic info}
**URL/DOI:** {link}
**Read status:** {unread / skimmed / read / studied}

### Summary
{One paragraph: what they did, what they found}

### Key contributions
- {contribution 1}
- {contribution 2}

### Methodology
{Brief description of approach}

### Relevance to current work
{Why this matters for the task at hand}

### Key quotes
> "{quote}" (p. {X})

### Connections
- Related to: {other papers}
- Builds on: {prior work}
- Extended by: {subsequent work}

### Notes
{Personal thoughts, questions, critiques}
```

## Building Reading Lists

### For Entering a New Field

```markdown
## Reading List: Entering {Field}

### Background (if needed)
- {prerequisite 1}
- {prerequisite 2}

### Orientation (week 1)
1. {Survey paper} - Get the lay of the land
2. {Textbook chapter} - Core concepts

### Foundations (weeks 2-3)
1. {Seminal paper 1} - {why it's foundational}
2. {Seminal paper 2} - {why it's foundational}
3. {Seminal paper 3} - {why it's foundational}

### Modern Developments (week 4+)
1. {Recent influential paper}
2. {Recent influential paper}

### Optional Deep Dives
- If interested in {subtopic}: {papers}
- If interested in {subtopic}: {papers}
```

### For Specific Questions

```markdown
## Reading List: {Question}

### The question
{What I'm trying to understand}

### Papers that address this
1. {Paper} - {how it helps}
2. {Paper} - {how it helps}

### Background needed
- {Concept}: See {paper}

### After reading these, I should understand:
- {outcome 1}
- {outcome 2}
```

## Citation Archaeology

### Tracing an Idea's History

1. Find the earliest clear statement
2. Trace back through their references
3. Note when the terminology changed
4. Map the genealogy

### Template

```markdown
## Genealogy: {Concept}

### Modern Name
{What we call it now}

### Origin
{Author, Year} - First clear statement

### Key Developments
- {Year}: {Author} - {contribution}
- {Year}: {Author} - {contribution}
- {Year}: {Author} - {contribution}

### Terminology Evolution
- Originally: "{term}" ({Author, Year})
- Then: "{term}" ({Author, Year})
- Now: "{term}"

### In Other Fields
- {Field}: called "{term}"
- {Field}: called "{term}"
```

## Anti-Patterns

### What to Avoid

1. **Reading only recent papers** - Miss foundations
2. **Citing without reading** - Academic dishonesty
3. **Ignoring other fields** - Miss connections
4. **Reading everything** - Diminishing returns
5. **Never finishing papers** - Need some deep reads
6. **No note-taking** - Will forget
