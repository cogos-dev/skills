# Contributing to CogOS Skills

Thanks for your interest. This repo is a collection of portable skill definitions (`SKILL.md` files) for Claude Code and compatible AI agents. There is no code to compile — contributions are prose.

## Development setup

```sh
git clone https://github.com/cogos-dev/skills.git
cd skills
```

No language runtime is required. A markdown-aware editor is the whole toolchain.

## Skill structure

Each skill lives under `plugins/<plugin>/skills/<skill-name>/SKILL.md`. The file is a structured prompt — see any existing skill for the shape.

Minimum fields:

- Frontmatter block (`---` wrapped)
  - `name:` — kebab-case skill name
  - `description:` — single-sentence trigger hint for Claude to load it
  - `version:` — semver (start at `0.1.0`)
- Body with sections: **When to use**, **What this does**, procedural steps

## Proposing a new skill

1. Fork the repo and create a branch from `main`
2. Drop the skill under `plugins/<relevant-plugin>/skills/<your-skill>/SKILL.md`
3. Verify the frontmatter is valid YAML
4. Smoke-test in your own Claude Code session: does the `description` field cause Claude to load it at the right moment?
5. Open a pull request using the org PR template

## Editing an existing skill

Keep the change scoped. If you're rewriting a major section, bump the `version` in the frontmatter.

## Skill-design pointers

- Skills should be *procedural* (how to do a thing), not *encyclopedic* (all facts about a thing).
- The `description` field is what Claude sees when deciding whether to load the skill. It must be an accurate triggering hint, not marketing copy.
- If a skill loads but doesn't help, the description is wrong — fix it.

## Reporting issues

Use the org-level [Bug Report](https://github.com/cogos-dev/skills/issues/new?template=bug.yml) or [Feature Request](https://github.com/cogos-dev/skills/issues/new?template=feature.yml) forms.

## License

By contributing, you agree that your contributions will be licensed under the [MIT License](LICENSE).
