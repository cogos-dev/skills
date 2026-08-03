# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Commit-message convention: [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
(`feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:`, `ci:`).

## [Unreleased]

### Added

- New `cogos-architecture` plugin with the `corpus-cross-reference` skill — automatically cross-checks a proposed RFC or ADR against the existing substrate corpus (composition gaps, conflicts, prior art, frontmatter validation, numbering). Handles both corpus numbering schemes (cog workspace 3-digit, cogos repo 4-digit). Includes `resources/canonical-frontmatter-shapes.md`, `resources/refs-vocabulary.md`, `resources/cross-check-heuristics.md`, and `tools/list_corpus.sh`.
- New `cogos-harness` plugin — the first plugin in this marketplace of the hooks/MCP-server kind rather than skills-only. Bundles `SessionStart`/`SessionEnd` presence hooks, a compaction bypass path, ambient kernel-vitals + context-window proprioception on `UserPromptSubmit`, the `cogos-kernel` MCP server, and the `btw`/`consolidate`/`handoff` skills. Every hook degrades to a silent no-op wherever the kernel or a cog workspace is absent.
- `cogos-architecture`'s `.claude-plugin/plugin.json` — the package was declared in `marketplace.json` but shipped no manifest of its own, so installing it specifically would misbehave.

### Changed

- `marketplace.json`: `name` corrected from `cogos-skills` to `plugins`, matching the repository name (the convention this marketplace and other Claude Code marketplaces already follow — e.g. `oscine`'s marketplace is named `oscine`). Added the missing `$schema` key.

### Fixed

<!--
Release template — copy this block, bump the version, date it, and move
Unreleased entries into the new release section:

## [X.Y.Z] - YYYY-MM-DD

### Added
- ...

### Changed
- ...

### Fixed
- ...

### Removed
- ...

### Security
- ...
-->
