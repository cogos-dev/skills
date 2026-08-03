# Zsh Startup File Loading Order (macOS)

## Load Order

Zsh reads config files in this exact order. Files only load if they exist.

### All shell invocations (scripts, commands, interactive)
1. `/etc/zshenv` (system)
2. `~/.zshenv` (user)

### Login shells only (first terminal open, ssh)
3. `/etc/zprofile` (system — macOS runs `path_helper` here)
4. `~/.zprofile` (user)

### Interactive shells only (shells you type commands in)
5. `/etc/zshrc` (system)
6. `~/.zshrc` (user — where Oh My Zsh, plugins, aliases live)

### Login shells only (after .zshrc)
7. `/etc/zlogin` (system)
8. `~/.zlogin` (user)

### On exit
9. `~/.zlogout`
10. `/etc/zlogout`

## What Goes Where

| File | Scope | What belongs here |
|------|-------|-------------------|
| `~/.zshenv` | ALL invocations (scripts too) | Minimal. Only env vars needed by non-interactive scripts. Cargo env. |
| `~/.zprofile` | Login shells only | `brew shellenv`, system PATH setup. Runs once per login session. |
| `~/.zshrc` | Interactive shells | Oh My Zsh, plugins, aliases, prompts, completions, tool inits (nvm, pyenv). |
| `~/.zlogin` | Login shells (after .zshrc) | Rarely used. Login messages or one-time setup. |
| `~/.profile` | Legacy sh/bash compat | Zsh does NOT read this. Only useful if running bash or sh. |

## macOS Specifics

### path_helper
macOS `/etc/zprofile` runs `/usr/libexec/path_helper -s` which:
- Reads `/etc/paths` (system default paths)
- Reads `/etc/paths.d/*` (per-tool path additions)
- **Moves existing PATH entries** — can reorder your PATH unexpectedly

This is why Homebrew PATH set in `.zprofile` sometimes gets reordered. `path_helper` runs first in `/etc/zprofile`, then user's `~/.zprofile` runs after.

### Terminal.app and iTerm2
macOS terminal apps open **login interactive** shells by default, meaning ALL config files load (`.zshenv` → `.zprofile` → `.zshrc`).

### VS Code Integrated Terminal
VS Code opens **interactive** shells (not login by default). This means:
- `.zshenv` loads (always)
- `.zprofile` does NOT load (not a login shell)
- `.zshrc` loads (interactive)

This is a common source of "works in terminal but not in VS Code" issues. Fix: set `"terminal.integrated.defaultProfile.osx": "zsh"` and optionally `"terminal.integrated.profiles.osx": { "zsh": { "path": "/bin/zsh", "args": ["-l"] } }` to force login shell.

### Subshells
When you type `zsh` from within zsh, you get an **interactive non-login** shell:
- `.zshenv` loads
- `.zshrc` loads
- `.zprofile` does NOT load

## Decision Tree for Placing Config

```
Need this in non-interactive scripts/cron?
  YES → ~/.zshenv
  NO  → Is this a PATH addition for system tools (homebrew, etc.)?
          YES → ~/.zprofile
          NO  → ~/.zshrc (default for most things)
```
