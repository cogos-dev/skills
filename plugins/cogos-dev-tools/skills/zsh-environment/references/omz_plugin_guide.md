# Oh My Zsh Plugin Guide

## Plugin Locations

| Type | Location | Example |
|------|----------|---------|
| Bundled | `~/.oh-my-zsh/plugins/<name>/` | git, docker, npm |
| Custom/Third-party | `~/.oh-my-zsh/custom/plugins/<name>/` | zsh-autosuggestions |

## The plugins Array

In `~/.zshrc`:
```zsh
plugins=(
    git
    docker
    zsh-autosuggestions
    zsh-syntax-highlighting  # MUST be last
)
```

- **Space-separated** (not comma-separated)
- Order matters: `zsh-syntax-highlighting` must be last or near-last
- Each entry must have a matching directory in either `plugins/` or `custom/plugins/`

## Installing Plugins

### Bundled plugins (already included with OMZ)
Just add the name to the `plugins=()` array. List available: `ls ~/.oh-my-zsh/plugins/`

### Third-party plugins
```bash
# Clone to custom plugins directory
git clone https://github.com/author/plugin-name.git \
    ~/.oh-my-zsh/custom/plugins/plugin-name

# Then add to plugins array in .zshrc
```

### Creating a custom plugin
Directory structure:
```
~/.oh-my-zsh/custom/plugins/my-plugin/
├── my-plugin.plugin.zsh    # REQUIRED: must match directory name
└── README.md               # Optional
```

The `.plugin.zsh` file is sourced by OMZ during startup. It can:
- Define functions and aliases
- Add to PATH
- Set up completions
- Register hook functions (chpwd, precmd, preexec)

## Plugin Ordering Rules

1. **zsh-syntax-highlighting** — Must be the last plugin (or second-to-last before zsh-history-substring-search). It wraps ZLE widgets, so any plugin loaded after it won't get syntax highlighting on its keybinds.
2. **zsh-autosuggestions** — Should be near the end, but before syntax-highlighting.
3. **nvm** — The OMZ nvm plugin provides lazy loading. If using it, remove manual `[ -s "$NVM_DIR/nvm.sh" ]` lines from `.zshrc` to avoid double-loading.

## Useful Plugins Not Commonly Known

| Plugin | Type | Purpose |
|--------|------|---------|
| `fzf` | bundled | Fuzzy finder key bindings and completion |
| `z` | bundled | Frecent directory jumping (like autojump) |
| `zoxide` | third-party | Modern replacement for z/autojump |
| `fast-syntax-highlighting` | third-party | Faster alternative to zsh-syntax-highlighting |
| `you-should-use` | third-party | Reminds you of existing aliases |
| `zsh-completions` | third-party | Additional completion definitions |
| `auto-notify` | third-party | Notifications when long commands finish |

## Troubleshooting

### Plugin not loading
1. Check name matches directory: `ls ~/.oh-my-zsh/custom/plugins/PLUGIN_NAME/`
2. Check `.plugin.zsh` file exists and matches dir name
3. Check for typos in the `plugins=()` array
4. Check `source $ZSH/oh-my-zsh.sh` comes after the `plugins=()` line

### Plugin slowing startup
Identify with: `time zsh -i -c exit` before/after removing the plugin from the array. Common slow plugins: nvm (if using manual sourcing), pyenv, rbenv, kubectl (completion generation).
