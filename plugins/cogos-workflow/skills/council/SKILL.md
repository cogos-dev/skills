---
name: council
description: Convene parallel deliberation agents that reason independently then synthesize. Use when you need multi-perspective analysis of a design decision, architectural choice, or complex problem. Spawns background agents with different lenses, coordinates via shared workspace artifacts, and produces a unified synthesis.
---

# Council: Parallel Deliberation Protocol

Spawn multiple agents with different analytical lenses to deliberate on a topic in parallel, coordinating through shared workspace artifacts and converging on a synthesis.

## When To Use

- **Architectural decisions** needing multiple stakeholder perspectives
- **Design reviews** requiring diverse lenses (stability, simplicity, theory)
- **Complex problems** where single-perspective analysis is insufficient
- **Validation** of claims (convergence across lenses proves coherence)
- Any time you would benefit from reasoning about a problem from multiple angles simultaneously

## The Pattern

```
┌─────────────────────────────────────────────────────────────┐
│                 OBSERVER/SYNTHESIZER (you)                   │
│                                                               │
│  You remain present while the agents think.                  │
│                                                               │
│  1. Define topic and lenses                                  │
│  2. Spawn agents in parallel (one per lens)                  │
│  3. Wait for all agents to complete                          │
│  4. Read deliberation artifacts                              │
│  5. Synthesize perspectives into coherent whole              │
│  6. Return synthesis to user                                 │
└─────────────────────────────────────────────────────────────┘
         │
         │ spawn (parallel, each with a focused lens)
         ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  Lens: Meta  │ │  Lens: Arch  │ │  Lens: Code  │ │  Lens: User  │
│  (theory/    │ │  (structure/ │ │  (implement-  │ │  (interface/  │
│   coherence) │ │   design)    │ │   ation)      │ │   experience) │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │                │
       │ write          │ write          │ write          │ write
       ▼                ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│           councils/{session}/ (shared workspace)                     │
│                                                                       │
│  ├── manifest.json         (council metadata, status)               │
│  ├── topic.md              (the question under deliberation)        │
│  ├── notes/                (independent perspectives)                │
│  │   ├── meta.md           (philosophical/theoretical analysis)      │
│  │   ├── arch.md           (architectural view)                      │
│  │   ├── code.md           (implementation review)                   │
│  │   └── user.md           (interface/experience vision)             │
│  └── synthesis.md          (final weaving — written by Observer)     │
└─────────────────────────────────────────────────────────────────────┘
```

## Invocation

When user says "convene a council" or "deliberate on X":

### Step 1: Define the Council

Choose 3-6 lenses appropriate to the topic.

**General-Purpose Lenses:**

| Lens | Focus |
|------|-------|
| `meta` | Philosophical coherence, conceptual integrity, foundations |
| `arch` | Technical architecture, layers, boundaries, patterns |
| `code` | Implementation fidelity, practical building, tooling |
| `interface` | User experience, perception, ergonomics |
| `stability` | Failure modes, reliability, operational concerns |
| `simplicity` | Minimum viable approach, what can be removed, essence |
| `future` | Evolution, technical debt, what we will wish we had done |
| `skeptic` | Hidden assumptions, what could go wrong, falsification |

**Choosing Lenses:**
- 4-5 lenses is ideal
- Always include a synthesis role (you, the observer)
- Match lenses to the nature of the question

### Step 2: Create Council Workspace

```bash
SESSION_ID=$(date +%s)
mkdir -p councils/$SESSION_ID/notes
```

Write `manifest.json`:
```json
{
  "id": "{session_id}",
  "topic": "Brief topic description",
  "lenses": ["stability", "simplicity", "skeptic"],
  "status": "deliberating",
  "created": "ISO timestamp"
}
```

Write `topic.md` with the full context of what is being deliberated.

### Step 3: Spawn Agents in Parallel

Use the dispatch-agent skill or the Task tool to spawn one agent per lens in background:

```
For each lens, spawn a background agent with prompt:

"You are a deliberation agent with lens: {LENS}

Your focus: {LENS_DESCRIPTION}

Topic under deliberation:
{TOPIC_CONTENT}

Instructions:
1. Read the topic carefully
2. Think deeply from your lens's perspective
3. Write your analysis to: councils/{SESSION}/notes/{LENS}.md
4. Your output should be 200-500 words of focused insight
5. End with 2-3 concrete recommendations from your perspective

Write your deliberation now."
```

### Step 4: Wait for Completion

After spawning all agents, block on their completion:

```
# Spawn returns agent IDs
# Then block waiting for each:
TaskOutput(task_id: a1, block: true, timeout: 120000)
TaskOutput(task_id: a2, block: true, timeout: 120000)
# ... etc
```

Never use sleep to guess when agents are done. Block on actual completion.

### Step 5: Synthesize

Read all notes. Write `synthesis.md` that:
- Acknowledges each perspective
- Identifies **convergent insights** (where lenses agree)
- Identifies **tensions** (where lenses conflict)
- Recommends a path forward that addresses key concerns

Update `manifest.json` status to `"complete"`.

### Step 6: Return

Present the synthesis to the user. The full deliberation artifacts remain in the council workspace for reference.

## Council Types

**Exploratory Council** - Understanding a complex system
- Goal: Map the territory, identify gaps, surface questions
- Synthesis: Comprehensive view with open questions

**Decision Council** - Choosing between approaches
- Goal: Evaluate options from multiple stakeholder perspectives
- Synthesis: Recommendation with trade-offs acknowledged

**Validation Council** - Testing architectural coherence
- Goal: Check if implementation matches intent, find drift
- Synthesis: Validation report with remediation priorities

**Reflection Council** - Self-examination
- Goal: The project reflecting on itself
- Synthesis: Insights about the current state and direction

Choose the council type based on what you need. The protocol adapts.

## Coordination Signals

For more complex councils that need mid-deliberation coordination, agents can write signal files:

```bash
# Create council signal
echo '{"council_id": "123", "status": "deliberating"}' > councils/123/signal.json

# Agents check signal for adjournment
# When done, convener updates signal
echo '{"council_id": "123", "status": "adjourned"}' > councils/123/signal.json
```

## Key Principles

1. **Parallel, not sequential** - Agents run simultaneously, not in turns
2. **Artifact-based coordination** - Use files, not message passing
3. **Artifacts persist** - The deliberation is captured, not ephemeral
4. **Synthesis is required** - Raw perspectives without synthesis is not useful
5. **Lenses are focused** - Each agent has ONE perspective, not a general review
6. **Observer remains present** - You (the synthesizer) watch while agents work
7. **Convergence validates coherence** - When agents agree on fundamentals, the design is sound

## Convergence as Validation

- When council agents **agree on fundamentals**, it validates the underlying coherence of the design
- When agents **disagree on details**, it shows richness (different lenses reveal different facets)
- When agents **fail to converge**, it suggests the question or the design itself may be incoherent

Convergence is not forced - it emerges naturally from multiple perspectives analyzing the same system. Genuine agreement across lenses is a strong signal.

## Anti-Patterns

- **Too many lenses** - More than 6 adds noise without clarity
- **Overlapping lenses** - Each lens must have a distinct focus
- **Skipping synthesis** - Raw notes without integration wastes the council
- **Forcing agreement** - Tensions between lenses are valuable findings
- **Single-lens councils** - Use a regular agent call instead
