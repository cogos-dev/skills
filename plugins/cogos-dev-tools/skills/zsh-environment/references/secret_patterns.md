# Secret Detection Patterns

## Regex Patterns for Common Secrets

### API Keys
| Provider | Pattern |
|----------|---------|
| OpenAI / OpenRouter | `sk-[a-zA-Z0-9_\-]{20,}` |
| Anthropic | `sk-ant-[a-zA-Z0-9_\-]{20,}` |
| AWS Access Key | `AKIA[A-Z0-9]{16}` |
| AWS Temp Key | `ASIA[A-Z0-9]{16}` |
| GitHub PAT | `ghp_[A-Za-z0-9_]{36,}` |
| GitHub OAuth | `gho_[A-Za-z0-9_]{36,}` |
| GitHub User-to-Server | `ghu_[A-Za-z0-9_]{36,}` |
| GitHub Server-to-Server | `ghs_[A-Za-z0-9_]{36,}` |
| GitHub Refresh | `ghr_[A-Za-z0-9_]{36,}` |
| Slack Bot Token | `xoxb-[0-9]{10,}-[a-zA-Z0-9-]+` |
| Slack User Token | `xoxp-[0-9]{10,}-[a-zA-Z0-9-]+` |
| Stripe | `sk_live_[a-zA-Z0-9]{24,}` |
| Google API | `AIza[A-Za-z0-9_\\-]{35}` |

### Generic patterns
```
(api[_-]?key|apikey|api_secret|access_token|auth_token)\s*=\s*["']?[A-Za-z0-9_\-]{16,}
(password|passwd|secret)\s*=\s*["'][^"']+["']
(private[_-]?key|ssh[_-]?key)\s*=\s*["']
```

## Files to Scan

Shell config files:
- `~/.zshrc`
- `~/.zshenv`
- `~/.zprofile`
- `~/.profile`
- `~/.bash_profile`
- `~/.bashrc`

Other common locations:
- `~/.env`
- `~/.netrc`
- `~/.npmrc` (may contain auth tokens)
- `~/.config/gh/hosts.yml` (GitHub CLI tokens)

## Remediation

### Move to separate sourced file
```bash
# Create secrets file (NOT tracked by any dotfiles repo)
mkdir -p ~/.config/secrets
touch ~/.config/secrets/env
chmod 600 ~/.config/secrets/env

# Add secrets there
echo 'export OPENROUTER_API_KEY="sk-or-v1-..."' >> ~/.config/secrets/env

# Source from .zshrc
echo '[ -f ~/.config/secrets/env ] && source ~/.config/secrets/env' >> ~/.zshrc

# Remove from .zshrc
# (manually edit to remove the hardcoded export line)
```

### Use macOS Keychain
```bash
# Store
security add-generic-password -a "$USER" -s "openrouter-api-key" -w "sk-or-v1-..."

# Retrieve in .zshrc
export OPENROUTER_API_KEY=$(security find-generic-password -a "$USER" -s "openrouter-api-key" -w 2>/dev/null)
```

### Use direnv (project-specific)
The `dotenv` oh-my-zsh plugin auto-loads `.env` files in directories. Combine with `.gitignore` to keep secrets out of repos.

```bash
# .env in project root (gitignored)
OPENROUTER_API_KEY=sk-or-v1-...
```
