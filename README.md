# CogOS Skills

Portable skill definitions for Claude Code and compatible AI agents.

Each skill is a `SKILL.md` file — a structured prompt that gives an agent specialized knowledge for a specific domain. There is no code to install; you copy the SKILL.md into your project's `.claude/skills/` directory.

## Usage

To use a skill, copy its `SKILL.md` file into your project:

```bash
# Example: add the plan-phases skill
mkdir -p .claude/skills/plan-phases
cp plugins/cogos-workflow/skills/plan-phases/SKILL.md .claude/skills/plan-phases/SKILL.md
```

Claude Code automatically loads skills from `.claude/skills/*/SKILL.md` when they match the conversation context.

## Available Skills

| Category | Skills | Description |
|----------|--------|-------------|
| **Workflow** | plan-phases, execute-plan, critical-review, dispatch-agent, council, cold-start, retrospective | Phased planning, parallel execution, deliberation |
| **Research** | literature-research, experiment-design, interdisciplinary-research, physics-validation, lab-engineering, inference-cascade | Structured research methodology |
| **Voice** | voice | Voice modality via Mod3 on Apple Silicon |
| **Dev Tools** | git-forensics, technical-writing, code-quality, systems-architecture | Developer tooling and code quality |

**Total: 18 skills across 4 categories.**

## Format

Each skill follows the [Agent Skills](https://agentskills.io) open standard. The `SKILL.md` format works in Claude Code, Cursor, VS Code Copilot, Gemini CLI, and other compatible agents.

## Structure

```
plugins/
├── cogos-workflow/skills/       # Planning + execution + review
├── cogos-voice/skills/          # Voice modality (Mod3)
├── cogos-research/skills/       # Research methodology
└── cogos-dev-tools/skills/      # Developer tooling
```

## License

MIT
