# PATH Management Reference

## PATH Ordering

- **Prepend** (`PATH="/new:$PATH"`) — Higher priority. The new entry is checked first.
- **Append** (`PATH="$PATH:/new"`) — Lower priority, fallback.

First match wins: if `python` exists in both `/opt/homebrew/bin` and `/usr/bin`, the one earlier in PATH is used.

## Idempotent PATH Patterns

### Case guard (preferred — used by pnpm, bun)
```bash
case ":$PATH:" in
  *":/path/to/dir:"*) ;;
  *) export PATH="/path/to/dir:$PATH" ;;
esac
```

### Directory existence guard
```bash
[[ -d "$PYENV_ROOT/bin" ]] && export PATH="$PYENV_ROOT/bin:$PATH"
```

### Simple export (no guard — can duplicate)
```bash
export PATH="/path/to/dir:$PATH"
```

When adding new PATH entries, prefer the case guard pattern for consistency.

## Common Tool Paths on macOS

| Tool | PATH Entry | Install Method |
|------|-----------|----------------|
| Homebrew (Apple Silicon) | `/opt/homebrew/bin`, `/opt/homebrew/sbin` | `brew shellenv` in .zprofile |
| Homebrew (Intel) | `/usr/local/bin` | `brew shellenv` in .zprofile |
| Cargo/Rust | `~/.cargo/bin` | `. "$HOME/.cargo/env"` in .zshenv |
| pyenv | `~/.pyenv/bin` + shims via `eval` | .zshrc |
| nvm | Dynamic: `~/.nvm/versions/node/vXX/bin` | OMZ plugin or manual source |
| Go | `~/go/bin` | .zshrc |
| Bun | `~/.bun/bin` | .zshrc |
| pnpm | `~/Library/pnpm` | .zshrc |
| pip (user) | `~/.local/bin` | .zshrc |
| Claude Code | `~/.local/bin` (via npm global) | .zshrc |
| LM Studio | `~/.lmstudio/bin` | .zshrc |

## PATH from System Sources

macOS sets base PATH via:
1. `/etc/paths` — `/usr/local/bin`, `/usr/bin`, `/bin`, `/usr/sbin`, `/sbin`
2. `/etc/paths.d/*` — Per-tool additions (Cryptex, etc.)
3. `/usr/libexec/path_helper` — Assembles the above into PATH (runs in `/etc/zprofile`)

## Diagnosing PATH Issues

### Command not found
```bash
# Check all locations
whence -a COMMAND
type -a COMMAND

# Check if binary exists somewhere
find ~/.local/bin ~/go/bin ~/.cargo/bin -name COMMAND 2>/dev/null
```

### Wrong version being used
```bash
# See which one is active
which python3
# See ALL in PATH order
whence -a python3
```

### PATH too long / slow
Long PATH can slow command resolution. Keep under ~30 entries. Remove entries for tools you no longer use.
