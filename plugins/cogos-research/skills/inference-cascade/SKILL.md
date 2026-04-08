---
name: inference-cascade
description: Design and run supervised multi-agent inference cascades using idle local GPU capacity. Spawns parallel agents with read-wide write-narrow sandboxing, collects observations as append-only hash-chained deltas, and triangulates findings from model agreement and disagreement. Use when running autonomous research loops, evaluating model performance against a live corpus, or exploring a problem space with multiple models in parallel.
allowed-tools: Bash(ollama:*) Read Write
---

# Inference Cascade

Run supervised multi-agent inference cascades — a supervisor model designs experiments, spawns parallel observer agents, collects their observations, and updates hypotheses based on agreement and disagreement patterns.

## When to Use

- Autonomous research where multiple perspectives improve coverage
- Live evaluation of fine-tuned models against base models
- Exploring a problem space with different model sizes or architectures
- Continuous workspace validation during idle periods
- Any task where disagreement between observers is informative

## The Pattern

```
Supervisor (you)
  │
  ├── Design: formulate prompt + select models
  ├── Spawn: N parallel agents, same prompt, different models
  ├── Collect: read all chain files after agents resolve
  ├── Analyze: agreement = signal, disagreement = investigate
  └── Iterate: update hypotheses, design next cascade
```

## Cascade Structure

### 1. Supervisor Turn

Before spawning agents, the supervisor:

1. Reviews previous cycle's hypotheses (if any)
2. Reads any existing chain files from prior cascades
3. Designs the experiment: what question to investigate, what prompt to give agents
4. Selects models to run (mix of sizes, architectures, or fine-tuned variants)

### 2. Agent Spawning

Each agent gets:
- **The same prompt** (or controlled variations for ablation)
- **Read-wide access**: full visibility into workspace, codebase, documents
- **Write-narrow constraint**: can ONLY append to its assigned chain file
- **No execution**: no shell, no tools beyond read + append

Spawn agents in parallel. Each runs independently and records observations.

### 3. Chain File Format

Each agent appends observations to a JSONL chain file. Entries are hash-linked:

```jsonl
{"seq": 1, "prior_hash": "", "model": "gemma4:26b", "observation": "...", "confidence": 0.8, "sources": ["file.go:42"], "hash": "abc123"}
{"seq": 2, "prior_hash": "abc123", "model": "gemma4:26b", "observation": "...", "confidence": 0.6, "sources": ["doc.md"], "hash": "def456"}
```

Fields:
- `seq`: monotonic sequence number
- `prior_hash`: hash of previous entry (empty for first)
- `model`: which model produced this observation
- `observation`: the finding (one observation per entry, specific and testable)
- `confidence`: agent's self-assessed confidence (0.0-1.0)
- `sources`: file paths or references that support the observation
- `hash`: SHA-256 of the canonical JSON entry (tamper-evident)

### 4. Analysis Patterns

After all agents resolve, read the chains and look for:

| Pattern | Meaning | Action |
|---------|---------|--------|
| **N/N agree** | High-confidence signal | Record as finding |
| **Most agree, one diverges** | Either hallucination or novel insight | Investigate in next cycle |
| **All diverge** | Ambiguous question or model-dependent | Refine prompt and retry |
| **Fine-tuned diverges from base** | Training effect | Evaluate which is correct |
| **Small model finds what large model misses** | Interesting attention pattern | Compare approaches |

### 5. Hypothesis Updates

After analysis, update the running hypotheses:

```markdown
## Hypotheses after Cycle N

### Confirmed
- [Observation] — agreed by N/N models across M cycles

### Active (investigating)
- [Observation] — first seen cycle N, single model, needs verification

### Refuted
- [Observation] — contradicted by evidence in cycle N

### New this cycle
- [Observation] — just discovered, queue for verification
```

## Read-Wide Write-Narrow Sandbox

The safety model for cascade agents:

```
READ:   Entire workspace, all source code, all documentation
WRITE:  ONLY append to assigned chain file (one file per agent)
EXEC:   NONE — no shell, no network, no side effects
```

This is maximally safe:
- Agents cannot modify workspace files
- Agents cannot execute commands
- Agents cannot communicate with each other (only via chains, read by supervisor)
- All output is append-only and hash-chained

## Model Selection

| Use Case | Models to Compare |
|----------|------------------|
| General exploration | Large (26B) + Medium (4B) + Small (0.8B) |
| LoRO evaluation | Base model + Fine-tuned model (same size) |
| Architecture comparison | Transformer + SSM on same task |
| Confidence calibration | Same model, different temperatures |

## Practical Execution

### Using the dispatch-agent skill

Reference the [dispatch-agent](../dispatch-agent/SKILL.md) skill for spawning agents. Each Ralph agent is dispatched with:

```
Backend: ollama (direct) or cogos (with foveated context)
Sandbox: read-only
Prompt: the cascade experiment prompt
Output: append to chain file
```

### Using Claude Code with CogOS backend

```bash
# Supervisor: real Claude (synthesis quality)
claude --bare -p "Read chains/*.jsonl and analyze the observations..."

# Agents: local models via CogOS
ANTHROPIC_BASE_URL=http://localhost:6931 ANTHROPIC_API_KEY=local \
claude --model gemma4:26b --bare --print \
  "Read the workspace and answer: [experiment prompt]. Record your observation."
```

### Using the Python sandbox agent

```bash
python3 scripts/sandbox-agent.py \
  --model gemma4:26b \
  --sandbox read-only \
  "Read the workspace and answer: [experiment prompt]"
```

## Clock-Time Moderation

Local models run exploration (free). Remote models run synthesis (budgeted).

| Phase | Model | Cost | Duration |
|-------|-------|------|----------|
| Agent runs (N=3) | Local (Ollama) | Free | ~15s parallel |
| Supervisor analysis | Local or Remote | Free or budgeted | ~10s |
| Reconciliation | Local | Free | ~5s |
| **Total per cycle** | | **~60s GPU** | |

24 cycles/day = autonomous research generating ~67K tokens of observations.

## Reconciliation

When cascades discover novel information:

1. **Novel + high agreement**: Multiple models found it → update workspace immediately
2. **Novel + single model**: Only one model found it → queue for next cycle
3. **Known + confirmed**: Models agree with existing docs → no action
4. **Known + contradicted**: Models disagree with existing docs → flag for review

Reconciliation propagates changes through affected documents until the workspace is internally consistent with the new observation.

## Anti-Patterns

- **Running without hypotheses**: Every cascade should test something specific. "Look at the workspace" is too vague.
- **Ignoring disagreements**: Divergence between models is the most valuable signal. Don't average it away.
- **Over-trusting any single model**: The cascade exists because individual models are unreliable. Trust the ensemble signal.
- **Skipping the chain format**: The hash-linked JSONL is what makes observations auditable and reproducible. Don't use free-form text files.
- **Running agents with write access**: Read-wide write-narrow is the safety boundary. Never give cascade agents write access to the workspace.
