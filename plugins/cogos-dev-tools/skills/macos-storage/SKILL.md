---
name: macos-storage
description: Analyze and manage disk storage on macOS. This skill should be used when the user asks about disk space, wants to free up storage, needs to find large files, clean caches, or manage developer build artifacts. Handles macOS-specific concerns like sparse files (Docker.raw), cloud storage placeholders (Google Drive streaming), and developer tool caches. Triggers on requests like "what's using my disk space", "free up storage", "clean caches", "find large files", "how much space do node_modules use".
version: 1.0.0
author: myrgic
tags: [macos, disk-storage, cleanup, dev-tools]
canonical_source: "~/.claude/skills/macos-storage/SKILL.md"
projection_note: >
  This is the public marketplace projection. The canonical source additionally
  integrates with a private local file-catalogue database (a personal SQLite
  index of the operator's files) — that integration section is dropped here
  since the tool it queries isn't part of this repo. One hardcoded workspace
  path in the bundled report script was also genericized. Update canonical
  first; project here after.
---

# macOS Storage Management

Analyze, report on, and clean up disk storage on macOS using a combination of CLI tools and direct commands.

## Prerequisites

The following tools should be installed via Homebrew. If missing, install them before proceeding.

```bash
brew install dust mole kondo
```

- **dust** — Fast disk usage analyzer (Rust). Handles sparse files correctly via `st_blocks`. Non-interactive, ideal for scripted analysis.
- **mole** (`mo`) — macOS-specific cleanup tool. Cleans caches, logs, browser data, dev artifacts. Runs non-interactively without a TTY.
- **kondo** — Dev project artifact cleaner. Finds node_modules, target/, .venv across 20+ project types. Requires TTY for interactive mode.

## Workflow

### 1. Quick Assessment

For a fast overview of what's consuming space, run:

```bash
df -h /System/Volumes/Data  # Check free space
dust -n 20 -d 2 ~           # Top 20 dirs, 2 levels deep (uses actual disk blocks)
```

`dust` correctly handles sparse files (Docker.raw, VM disks) and cloud storage placeholders (Google Drive streaming), reporting actual on-disk usage rather than logical size.

### 2. Full Storage Report

Run the bundled analysis script for a comprehensive report:

```bash
bash scripts/storage_report.sh
```

This produces a structured report covering: disk overview, top directories, cache sizes, dev artifacts (node_modules, Rust target/, Python virtualenvs), Docker status, large files, and mole cleanup preview.

### 3. Targeted Analysis

For specific categories, use these commands directly:

**Caches:**
```bash
du -sh ~/Library/Caches ~/.cache ~/Library/Caches/Homebrew 2>/dev/null | sort -rh
```

**Dev artifacts:**
```bash
# node_modules
find ~ -name node_modules -type d -maxdepth 5 -not -path '*/node_modules/*/node_modules' 2>/dev/null -exec du -sh {} \; | sort -rh | head -15

# Rust target/
find ~ -name target -type d -maxdepth 6 2>/dev/null | while read d; do [ -f "$d/../Cargo.toml" ] && du -sh "$d"; done | sort -rh

# Python virtualenvs
find ~ -maxdepth 5 \( -name .venv -o -name venv \) -type d 2>/dev/null -exec du -sh {} \; | sort -rh
```

**Docker:**
```bash
# Actual vs logical size of Docker.raw (sparse file)
ls -ls ~/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw 2>/dev/null
docker system df 2>/dev/null
```

**Large files (excluding cloud placeholders):**
```bash
find ~ -type f -not -path '*/Library/CloudStorage/*' -not -path '*/.Trash/*' -size +200M 2>/dev/null -exec du -sh {} \; | sort -rh | head -20
```

### 4. Cleanup Actions

Always confirm with the user before executing destructive cleanup commands. Present findings first, then propose specific actions.

**System caches (via mole):**
```bash
mo clean              # Interactive when TTY available; non-interactive otherwise
mo clean --dry-run    # Preview only (interactive mode)
```

In non-interactive mode (no TTY), `mo clean` automatically proceeds with user-level cleanup only (skips sudo-required system cleanup). It will report what it found and cleaned.

**Dev project artifacts (via kondo):**
Kondo requires a TTY for interactive mode. When running without a TTY, instruct the user to run kondo directly in their terminal:
```
# User should run interactively:
kondo ~/Workspaces
kondo --older 3M ~/Workspaces  # Only projects untouched for 3+ months
```

For non-interactive batch cleanup of specific known directories, use direct `rm -rf` on confirmed targets:
```bash
# Only after user confirmation
rm -rf /path/to/project/node_modules
rm -rf /path/to/project/target
cargo clean --manifest-path /path/to/project/Cargo.toml
```

**Package manager caches:**
```bash
brew cleanup && brew autoremove       # Homebrew
npm cache clean --force               # npm
pnpm store prune                      # pnpm
pip cache purge                       # pip
go clean -modcache                    # Go modules
```

**Docker:**
```bash
docker system prune -a    # Remove unused images, containers, networks
docker builder prune       # Clear build cache
# Restart Docker Desktop after pruning to reclaim Docker.raw space
```

**node_modules (via npkill — zero install):**
Instruct user to run in their terminal for interactive cleanup:
```
npx npkill
```

## Important macOS Caveats

Consult `references/macos_storage_knowledge.md` for detailed information on these topics:

1. **Sparse files**: Docker.raw and VM disks report inflated logical sizes. Always use `du -sh` (actual blocks) not `ls -lh` (logical size). `dust` handles this correctly.

2. **Cloud storage placeholders**: Google Drive streaming and iCloud files appear with full `st_size` but occupy near-zero disk space (`st_blocks = 0`). Exclude `~/Library/CloudStorage/` from disk usage calculations. Quick check: `du -sh ~/Library/CloudStorage/` — if it reports KB, streaming mode is active.

3. **TTY requirement**: `mo analyze`, `mo clean --dry-run`, and `kondo` (interactive mode) require a real terminal. When running from an agent harness (no TTY), either use non-interactive alternatives or instruct the user to run the command directly.

4. **Protected locations**: Never auto-clean `~/Library/Keychains/`, `~/Library/Preferences/`, or `~/Library/CloudStorage/`. The mole whitelist protects critical caches by default.

5. **Sandboxed app data**: `~/Library/Containers/` contains sandboxed app data. Deleting folders here can break apps. Only clean known-safe paths (like Docker's vms/data).

## Resources

- `scripts/storage_report.sh` — bundled non-interactive analysis script producing the full structured report described in "Full Storage Report" above
- `references/macos_storage_knowledge.md` — extended detail on sparse files, cloud placeholders, and other macOS-specific storage caveats
