# plugins

Portable skill definitions, and Claude Code harness plugins, for CogOS.

Most packages here are pure skill collections: each skill is a `SKILL.md` file — a structured prompt that gives an agent specialized knowledge for a specific domain. The format follows the [Agent Skills](https://agentskills.io) open standard and works across Claude Code, Cursor, VS Code Copilot, Gemini CLI, Hermes, and other compatible agents.

One package, **cogos-harness**, is a different kind: it bundles hooks and an MCP server alongside its skills — the Claude Code plugin system's harness-integration surface, not just prompt content. It's Claude-Code-specific (hooks and MCP servers aren't portable to Hermes's skill-tap mechanism the way `SKILL.md` files are) and is documented separately in its own [README](plugins/cogos-harness/README.md).

## Setup

### Claude Code (plugin marketplace)

Install the whole collection as a marketplace tap:

```bash
claude plugin add myrgic/plugins
```

Or install a specific plugin package:

```bash
claude plugin add myrgic/plugins/cogos-workflow
claude plugin add myrgic/plugins/cogos-substrate
claude plugin add myrgic/plugins/cogos-research
claude plugin add myrgic/plugins/cogos-harness
```

`cogos-harness` additionally registers an MCP server (`cogos-kernel`) and a
set of hooks — see its [own README](plugins/cogos-harness/README.md) for
what it does and what it needs running to be useful.

Skills are then available in any Claude Code session. Claude invokes them automatically when the conversation context matches, or you can trigger them explicitly (e.g. `/plan-phases`, `/orchestrate`).

To install a single skill manually without the plugin system:

```bash
mkdir -p .claude/skills/plan-phases
cp plugins/cogos-workflow/skills/plan-phases/SKILL.md .claude/skills/plan-phases/SKILL.md
```

### Hermes (skills tap)

Add the repo as a Hermes skill tap:

```bash
hermes skills tap add myrgic/plugins
```

Then install individual skills:

```bash
hermes skills install plan-phases
hermes skills install orchestrate
hermes skills install pull-context-dispatch
```

Or search across all taps:

```bash
hermes skills search orchestration
hermes skills search substrate
```

Skills installed via tap are available in all Hermes sessions and appear in the `skills_list()` tool output. The same `SKILL.md` files work in both agents — the format is identical.

## Available Skills

| Plugin | Skills | Description |
|--------|--------|-------------|
| **cogos-workflow** | plan-phases, execute-plan, critical-review, dispatch-agent, council, cold-start, retrospective, local-review, orchestrate, kanban-closed-loop-supervisor, pull-context-dispatch, suggest, session-protocol | Phased planning, parallel execution, deliberation, closed-loop orchestration, pointer-based dispatch, session continuity |
| **cogos-substrate** | substrate-archaeology | Finding and trusting prior work in a CogOS/Myrgic substrate |
| **cogos-research** | literature-research, experiment-design, interdisciplinary-research, physics-validation, lab-engineering, inference-cascade | Structured research methodology |
| **cogos-voice** | voice | Voice modality via Mod³ on Apple Silicon |
| **cogos-dev-tools** | git-forensics, technical-writing, code-quality, systems-architecture, zsh-environment, macos-storage, codex, openclaw-expert | Developer tooling, code quality, shell/storage management, cross-model CLI operation |
| **cogos-architecture** | corpus-cross-reference | CogOS architecture corpus hygiene — cross-check proposed RFCs/ADRs against the substrate corpus |
| **myrgic-org** | pr-triage, issue-triage | Org-management skills for the myrgic GitHub org |
| **cogos-harness** | btw, consolidate, handoff | Session-lifecycle hooks, kernel-vitals proprioception, and the `cogos-kernel` MCP server, plus the three skills that lean on them. Claude-Code-only — see its own README. |

**Total: 35 skills across 8 plugin packages** (one of which, cogos-harness, also ships hooks and an MCP server).

## Cross-Compatibility

Skills in this repo are written to work in both Claude Code and Hermes without modification:

- **Claude Code** loads skills from `.claude/skills/*/SKILL.md` automatically, or via the plugin marketplace (`claude plugin add`).
- **Hermes** loads skills from `~/.hermes/skills/` and from tap-registered GitHub repos (`hermes skills tap add`).
- **Other agents** (Cursor, VS Code Copilot, Gemini CLI) load skills from `.claude/skills/` following the same Agent Skills standard.

The `SKILL.md` frontmatter is the same format for all agents. Agent-specific metadata (Hermes toolset requirements, Claude Code `allowed-tools`) lives under `metadata.hermes` or as standard frontmatter fields and is ignored by agents that don't understand it.

Some skills include a `canonical_source` frontmatter field pointing to the authoritative copy in a running Hermes or cog workspace instance. In those cases the marketplace copy is a projection — update the canonical source first, then project here.

## Skill Bundles (Hermes)

Hermes supports composing multiple skills into a named bundle that loads them together with a shared instruction:

```yaml
# ~/.hermes/skill-bundles/cogos-operator.yaml
name: cogos-operator
description: Full CogOS operator context: substrate archaeology, architecture hygiene, pointer-based dispatch
skills:
  - substrate-archaeology
  - corpus-cross-reference
  - pull-context-dispatch
instruction: |
  You are operating in the Myrgic/CogOS substrate. Read existing maps and prior work before
  designing or writing. Update canonical sources first; project to marketplace after.
```

Activate with `/cogos-operator` in any Hermes session.

## Structure

```
plugins/
├── cogos-workflow/skills/       # Planning + execution + review + orchestration
├── cogos-substrate/skills/      # Prior-work archaeology
├── cogos-research/skills/       # Research methodology
├── cogos-voice/skills/          # Voice modality (Mod³)
├── cogos-dev-tools/skills/      # Developer tooling
├── cogos-architecture/skills/   # Architecture corpus hygiene
├── myrgic-org/skills/           # Org management
└── cogos-harness/               # Claude Code hooks + MCP server + skills (not skills-only)
    ├── hooks/
    ├── skills/
    └── .mcp.json
```

## Format

Each skill follows the [Agent Skills](https://agentskills.io) open standard:

```yaml
---
name: skill-name
description: "One-line description — what the skill does and when to load it."
version: 1.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [tag1, tag2]
    related_skills: [other-skill]
---

# Skill Name

Body: when to use, method, steps, examples.
```

## Contributing

Skills follow the same PR workflow as the rest of the myrgic org — branch on the upstream repo, squash-merge to main. See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

If a skill has a canonical source in a running workspace (indicated by `canonical_source` in frontmatter), update that first, then project here. Don't edit the marketplace copy directly.

## License

MIT
