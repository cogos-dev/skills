# Terminal Application Configuration

## VS Code

### Settings file
`~/Library/Application Support/Code/User/settings.json`

### Key terminal settings
```json
{
    "terminal.integrated.defaultProfile.osx": "zsh",
    "terminal.integrated.profiles.osx": {
        "zsh": {
            "path": "/bin/zsh",
            "args": ["-l"]
        }
    },
    "terminal.integrated.env.osx": {
        "SOME_VAR": "value"
    },
    "terminal.integrated.fontFamily": "MesloLGS NF",
    "terminal.integrated.scrollback": 10000
}
```

### Common issue: Not using zsh
If `terminal.integrated.defaultProfile.osx` is not set, VS Code auto-detects and may pick bash. Always set it explicitly to `"zsh"`.

### Login shell vs interactive
By default VS Code opens interactive (not login) shells. To get login shell behavior (which loads `.zprofile`), add `"args": ["-l"]` to the profile.

### Cursor, Windsurf
Same settings format as VS Code. Settings locations:
- Cursor: `~/Library/Application Support/Cursor/User/settings.json`
- Windsurf: `~/Library/Application Support/Windsurf/User/settings.json`

## iTerm2

### Config location
Binary plist: `~/Library/Preferences/com.googlecode.iterm2.plist`

### Shell settings (per-profile)
- **Profiles → General → Command**: Set to "Login Shell" (default) or custom command
- **Custom Command = No**: Uses system login shell (`/bin/zsh`)
- **Custom Command = Yes**: Uses the Command field value

### Reading settings
```bash
defaults read com.googlecode.iterm2 "New Bookmarks" | grep -A2 "Custom Command"
```

### Shell integration
```bash
curl -L https://iterm2.com/shell_integration/zsh -o ~/.iterm2_shell_integration.zsh
# Add to .zshrc: source ~/.iterm2_shell_integration.zsh
```

## Ghostty

### Config location
`~/.config/ghostty/config` (plain text, key = value)

### Key settings
```
font-family = MesloLGS NF
font-size = 14
theme = catppuccin-mocha
shell-integration = zsh
command = /bin/zsh -l
```

### Creating config
```bash
mkdir -p ~/.config/ghostty
touch ~/.config/ghostty/config
```

## Terminal.app (macOS built-in)

### Settings
Preferences → Profiles → Shell tab:
- "Default login shell" (recommended)
- Or specify custom command

### Reading settings
```bash
defaults read com.apple.Terminal "Default Window Settings"
```

## Warp

### Config location
`~/Library/Preferences/dev.warp.Warp-Stable.plist`

### Shell detection
Warp auto-detects the login shell. No configuration usually needed.

## Cross-Terminal Detection

Use `$TERM_PROGRAM` in `.zshrc` for terminal-specific config:
```zsh
case "$TERM_PROGRAM" in
    vscode)    ;; # VS Code terminal
    iTerm.app) ;; # iTerm2
    ghostty)   ;; # Ghostty
    Apple_Terminal) ;; # Terminal.app
    WarpTerminal)   ;; # Warp
esac
```
