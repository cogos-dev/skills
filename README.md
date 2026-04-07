# CogOS Skills

> Part of the [CogOS ecosystem](https://github.com/cogos-dev) — what it **CAN DO**

A Claude Code plugin marketplace and Agent Skills collection for CogOS development workflows.

## Installation

Add this marketplace to Claude Code:

```shell
/plugin marketplace add cogos-dev/skills
```

Then install individual plugins:

```shell
/plugin install cogos-workflow@cogos-skills
/plugin install cogos-voice@cogos-skills
/plugin install cogos-research@cogos-skills
```

## Plugins

| Plugin | What it does | Skills |
|--------|-------------|--------|
| **cogos-workflow** | Phased planning and execution for complex tasks | plan-phases, execute-plan, critical-review |
| **cogos-voice** | Voice modality via Mod³ on Apple Silicon | voice |
| **cogos-research** | Structured research and experiment design | literature-research, experiment-design |

## Agent Skills Compatibility

All skills in this marketplace follow the [Agent Skills](https://agentskills.io) open standard. The `SKILL.md` files work in any compatible agent product (Claude Code, Cursor, VS Code Copilot, Gemini CLI, and others). The Claude Code plugin wrapper adds hooks, MCP server configs, and agents on top.

## Structure

```
skills/
├── .claude-plugin/
│   └── marketplace.json      # Plugin registry
└── plugins/
    ├── cogos-workflow/        # Planning + execution + review
    ├── cogos-voice/           # Voice modality (Mod³)
    └── cogos-research/        # Research methodology
```

Each plugin follows the standard structure:

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json           # Plugin metadata
├── skills/
│   └── skill-name/
│       └── SKILL.md          # Agent Skills format
└── ...                       # Optional: agents/, hooks/, .mcp.json
```

## Creating Skills

See the [Agent Skills specification](https://agentskills.io/specification) for the SKILL.md format, or use the [template](https://github.com/anthropics/skills/tree/main/template) as a starting point.

## License

MIT
