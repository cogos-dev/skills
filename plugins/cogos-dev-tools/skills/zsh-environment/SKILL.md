---
name: zsh-environment
description: >
  Manage and troubleshoot the zsh shell environment on macOS with Oh My Zsh.
  Use this skill when the user asks about PATH problems, missing commands, shell
  configuration, oh-my-zsh plugins, shell startup performance, environment variables,
  exposed secrets in dotfiles, terminal application settings (VS Code, iTerm2, Ghostty),
  or any zsh/shell troubleshooting. Triggers on requests like "fix my PATH", "why is
  my shell slow", "add a plugin", "audit my shell config", "check for secrets",
  "configure my terminal", "what's in my PATH", "command not found".
allowed-tools: Read, Grep, Glob, Bash, Write, Edit
version: 1.0.0
author: myrgic
tags: [zsh, shell, macos, oh-my-zsh, dotfiles, troubleshooting]
canonical_source: "~/.claude/skills/zsh-environment/SKILL.md"
projection_note: >
  This is the public marketplace projection. The canonical source additionally
  documents one operator's exact dotfile contents (a line-numbered list of
  specific config issues, including a real exposed secret variable name and a
  private external-volume name). That section is replaced here with a
  generalized checklist of the same issue *categories*, since the categories
  generalize and the specific findings don't. Update canonical first; project
  here after.
---

# Zsh Environment Manager

Manage a zsh shell environment on macOS running Oh My Zsh.

## Assumptions

This skill assumes a common macOS setup, but always verify against the actual files before proposing changes — don't assume:

- **Shell**: zsh (default macOS shell)
- **Framework**: Oh My Zsh at `~/.oh-my-zsh/`
- **Config chain**: `~/.zshenv` → `~/.zprofile` → `~/.zshrc`

### Config File Roles
- `~/.zshenv`: Runs for ALL shell invocations (interactive, non-interactive, scripts, cron). Keep it minimal — anything here pays a cost on every subprocess.
- `~/.zprofile`: Login shells only. Typical contents: `brew shellenv`, other one-time PATH setup.
- `~/.zshrc`: Everything else — Oh My Zsh, plugins, PATH, tool inits, aliases. Most user-facing changes land here.
- `~/.profile`: Legacy; zsh ignores this file by default. If it still exists and has content, check for stale duplicate exports also present in `~/.zshrc`/`~/.zshenv`.

## Safety Protocol

**MANDATORY for ALL modifications to shell config files.**

### Before editing:
1. Run: `bash scripts/config_backup.sh`
2. Confirm the intended change and target file with the user before applying
3. Show the user the exact edit (old → new) before applying

### After editing:
1. Syntax check: `zsh -n ~/.zshrc` (or whichever file was edited)
2. Load test: `zsh -c 'source ~/.zshrc && echo "Config loads OK"'`
3. Tell the user the backup location and restore command

### If something breaks:
Tell the user: `cp ~/.config/zsh-backups/zshrc.TIMESTAMP ~/.zshrc` (use the actual timestamp from the backup step).

## Mode 1: Diagnose

Use when the user has a shell problem (missing command, wrong version, broken config, etc.).

### Steps:
1. Read the relevant config files (`~/.zshenv`, `~/.zprofile`, `~/.zshrc`)
2. Run diagnostic scripts as needed:
   - General issues: `bash scripts/shell_audit.sh`
   - PATH issues: `zsh scripts/path_analyzer.sh`
   - Slow startup: `bash scripts/startup_profiler.sh`
3. Consult reference docs for details:
   - File placement: `references/zsh_startup_order.md`
   - PATH specifics: `references/path_management.md`
   - Plugin issues: `references/omz_plugin_guide.md`
   - Terminal issues: `references/terminal_apps.md`
4. Present findings as a numbered list with severity: `[ERR]`, `[WARN]`, `[INFO]`
5. Propose specific fixes with before/after code blocks
6. If a fix is approved, follow the Safety Protocol

## Mode 2: Modify

Use when the user wants to change their shell config.

### Choosing the right file

```
Need this in non-interactive scripts/cron?  →  ~/.zshenv
PATH for Homebrew/system tools?             →  ~/.zprofile
Everything else (default)?                  →  ~/.zshrc
```

See `references/zsh_startup_order.md` for details.

### Adding a PATH entry

1. Check the directory exists
2. Check it's not already in PATH (grep the config files)
3. Use the idempotent case pattern:
```bash
# tool-name
case ":$PATH:" in
  *":/path/to/dir:"*) ;;
  *) export PATH="/path/to/dir:$PATH" ;;
esac
# tool-name end
```
4. Place near related entries in `.zshrc`
5. Follow Safety Protocol

### Removing a PATH entry

1. Find the block (look for comment markers like `# tool-name` / `# tool-name end`)
2. Remove the entire block including comments
3. Verify the command still resolves: `zsh -c 'source ~/.zshrc && which COMMAND'`
4. Follow Safety Protocol

### Adding an oh-my-zsh plugin

See `references/omz_plugin_guide.md` for full details.

1. **Bundled**: Just add to the `plugins=()` array
2. **Third-party**: `git clone` to `~/.oh-my-zsh/custom/plugins/<name>/`, then add to array
3. **Custom**: Scaffold `~/.oh-my-zsh/custom/plugins/<name>/<name>.plugin.zsh`, then add to array
4. **Ordering**: `zsh-syntax-highlighting` must remain last in the array
5. Follow Safety Protocol

### Removing an oh-my-zsh plugin

1. Remove from `plugins=()` array
2. Ask if user also wants to delete the plugin directory (for custom/third-party)
3. Check for plugin-specific config below the `source $ZSH/oh-my-zsh.sh` line
4. Follow Safety Protocol

### Adding/modifying environment variables

1. Check for existing definitions across all config files: `grep -n 'VARNAME' ~/.zshrc ~/.zshenv ~/.zprofile`
2. Avoid creating duplicates
3. Place in the correct file based on scope (see decision tree above)
4. For secrets: recommend `~/.config/secrets/env` pattern (see `references/secret_patterns.md`)
5. Follow Safety Protocol

## Mode 3: Audit

Use when the user wants a comprehensive health check.

### Steps:
1. Run all diagnostic scripts:
   ```
   bash scripts/shell_audit.sh
   zsh scripts/path_analyzer.sh
   bash scripts/startup_profiler.sh
   ```
2. Check for exposed secrets (see `references/secret_patterns.md`)
3. Report findings in these sections:
   - **Secrets**: Any exposed API keys, tokens, passwords
   - **PATH Health**: Duplicates, dead entries, unmounted volumes
   - **Config Duplicates**: Duplicate exports, PATH additions
   - **Plugin Health**: Missing plugins, orphaned custom plugins
   - **Performance**: Startup time, slow operations
   - **Terminal Apps**: VS Code, iTerm2, Ghostty config status
4. Prioritize findings: errors first, then warnings, then info

### Common Audit Findings (patterns to check for)

Independent of any specific user's config, these are the issue categories that show up most often:

1. Secrets committed in plain text (API keys, tokens, passwords) in `.zshrc`/`.zshenv`
2. The same PATH directory added twice via different code paths (e.g. `~/bin` and `$HOME/bin` both resolving to the same place)
3. The same environment variable or tool init sourced from more than one config file — redundant work on every shell start
4. Manual sourcing of a tool's init script (nvm, pyenv, rbenv, etc.) that duplicates what an Oh My Zsh plugin already does for the same tool
5. `eval`-based init blocks (`pyenv init -`, `rbenv init -`, etc.) running on every shell open — measure with `startup_profiler.sh` before assuming a given block is the culprit
6. PATH entries pointing at removable or network volumes that go dead when unmounted, silently swallowing `command not found` diagnosis time

## Terminal App Configuration

See `references/terminal_apps.md` for full details.

### VS Code (most common issue)
Settings at: `~/Library/Application Support/Code/User/settings.json`

Ensure these are set:
```json
"terminal.integrated.defaultProfile.osx": "zsh"
```

For Cursor: `~/Library/Application Support/Cursor/User/settings.json`
For Windsurf: `~/Library/Application Support/Windsurf/User/settings.json`

### iTerm2
Check profile shell settings: `defaults read com.googlecode.iterm2 "New Bookmarks" | grep -A2 "Custom Command"`

### Ghostty
Config at `~/.config/ghostty/config`. Create if it doesn't exist.

## Common Recipes

### Make shell startup faster
1. Remove manual nvm sourcing if the OMZ nvm plugin is active (it lazy-loads)
2. Use `pyenv init --path` instead of `pyenv init -` for PATH-only setup
3. Check for duplicate `compinit` calls (OMZ already calls it)
4. Run `startup_profiler.sh` to measure impact

### Add a new tool to PATH
Use the idempotent case pattern (see Mode 2: Adding a PATH entry).

### Create a custom oh-my-zsh plugin
```bash
mkdir -p ~/.oh-my-zsh/custom/plugins/my-plugin
cat > ~/.oh-my-zsh/custom/plugins/my-plugin/my-plugin.plugin.zsh << 'EOF'
# my-plugin: description
# Add functions, aliases, hooks here
EOF
```
Then add `my-plugin` to the `plugins=()` array in `.zshrc`.

### Move secrets out of dotfiles
See `references/secret_patterns.md` for the `~/.config/secrets/env` pattern and macOS Keychain approach.

### Fix PATH ordering
Prepend = higher priority. Append = fallback. See `references/path_management.md`.

### Preview an Oh My Zsh theme without switching
`bash scripts/theme_preview.sh` renders a sample prompt for a candidate theme so the user can compare before committing to a `ZSH_THEME` change.

## Resources

- `scripts/shell_audit.sh` — general config health scan (secrets, PATH, duplicates, plugins)
- `scripts/path_analyzer.sh` — PATH-specific analysis (duplicates, dead entries, ordering)
- `scripts/startup_profiler.sh` — measures shell startup time and flags slow blocks
- `scripts/config_backup.sh` — timestamped backup of dotfiles before an edit
- `scripts/theme_preview.sh` — render a sample prompt for a candidate Oh My Zsh theme
- `references/zsh_startup_order.md` — which file loads when, and why it matters
- `references/path_management.md` — PATH ordering and idempotent-append patterns
- `references/omz_plugin_guide.md` — adding/removing bundled, third-party, and custom plugins
- `references/terminal_apps.md` — terminal-specific shell profile configuration
- `references/secret_patterns.md` — detecting and relocating secrets out of dotfiles
