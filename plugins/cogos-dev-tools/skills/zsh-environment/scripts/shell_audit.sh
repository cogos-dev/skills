#!/usr/bin/env bash
set -euo pipefail

HOME_DIR="$HOME"
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

section() { echo -e "\n${BOLD}${CYAN}=== $1 ===${NC}"; }
ok()      { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn()    { echo -e "  ${YELLOW}[WARN]${NC} $1"; }
err()     { echo -e "  ${RED}[ERR]${NC} $1"; }
info()    { echo -e "  $1"; }

errors=0
warnings=0

# ── Shell Version ──
section "Shell & Framework"
if command -v zsh &>/dev/null; then
    ok "zsh $(zsh --version 2>/dev/null | head -1)"
else
    err "zsh not found"; ((errors++))
fi

if [[ -d "$HOME_DIR/.oh-my-zsh" ]]; then
    omz_ver=""
    if [[ -f "$HOME_DIR/.oh-my-zsh/.git/HEAD" ]]; then
        omz_ver=" ($(cd "$HOME_DIR/.oh-my-zsh" && git log -1 --format='%h %ci' 2>/dev/null | cut -d' ' -f1-2))"
    fi
    ok "Oh My Zsh installed${omz_ver}"
else
    info "Oh My Zsh not installed"
fi

info "Default shell: $(dscl . -read "$HOME_DIR" UserShell 2>/dev/null | awk '{print $2}' || echo 'unknown')"
info "SHELL env: ${SHELL:-unset}"

# ── Config File Inventory ──
section "Config Files"
config_files=(.zshenv .zprofile .zshrc .zlogin .profile .bash_profile .bashrc)
for f in "${config_files[@]}"; do
    path="$HOME_DIR/$f"
    if [[ -f "$path" ]]; then
        size=$(wc -c < "$path" | tr -d ' ')
        lines=$(wc -l < "$path" | tr -d ' ')
        modified=$(stat -f '%Sm' -t '%Y-%m-%d %H:%M' "$path" 2>/dev/null || stat --format='%y' "$path" 2>/dev/null | cut -d. -f1)
        info "$f: ${lines} lines, ${size} bytes, modified ${modified}"
    fi
done

# ── Syntax Check ──
section "Syntax Check"
for f in .zshenv .zprofile .zshrc; do
    path="$HOME_DIR/$f"
    if [[ -f "$path" ]]; then
        if zsh -n "$path" 2>/dev/null; then
            ok "$f syntax OK"
        else
            err "$f has syntax errors"; ((errors++))
        fi
    fi
done

# ── Oh My Zsh Plugins ──
section "Oh My Zsh Plugins"
if [[ -f "$HOME_DIR/.zshrc" ]]; then
    # Extract plugins array from .zshrc
    declared_plugins=()
    in_plugins=0
    while IFS= read -r line; do
        if [[ "$line" =~ ^[[:space:]]*plugins=\( ]]; then
            in_plugins=1
            # Handle single-line: plugins=(a b c)
            inner="${line#*\(}"
            inner="${inner%%\)*}"
            for p in $inner; do
                [[ -n "$p" ]] && declared_plugins+=("$p")
            done
            [[ "$line" == *")"* ]] && in_plugins=0
            continue
        fi
        if [[ $in_plugins -eq 1 ]]; then
            [[ "$line" == *")"* ]] && in_plugins=0
            clean="${line%%\)*}"
            for p in $clean; do
                p="${p%%#*}"
                [[ -n "$p" && "$p" != "#"* ]] && declared_plugins+=("$p")
            done
        fi
    done < "$HOME_DIR/.zshrc"

    info "Declared plugins (${#declared_plugins[@]}): ${declared_plugins[*]}"
    echo ""

    for p in "${declared_plugins[@]}"; do
        if [[ -d "$HOME_DIR/.oh-my-zsh/custom/plugins/$p" ]]; then
            ok "$p (custom)"
        elif [[ -d "$HOME_DIR/.oh-my-zsh/plugins/$p" ]]; then
            ok "$p (bundled)"
        else
            err "Plugin '$p' declared but not found"; ((errors++))
        fi
    done

    # Check for orphaned custom plugins
    if [[ -d "$HOME_DIR/.oh-my-zsh/custom/plugins" ]]; then
        for dir in "$HOME_DIR/.oh-my-zsh/custom/plugins"/*/; do
            [[ ! -d "$dir" ]] && continue
            pname="$(basename "$dir")"
            [[ "$pname" == "example" ]] && continue
            found=0
            for dp in "${declared_plugins[@]}"; do
                [[ "$dp" == "$pname" ]] && found=1 && break
            done
            if [[ $found -eq 0 ]]; then
                warn "Custom plugin '$pname' exists but is not in plugins array"; ((warnings++))
            fi
        done
    fi
fi

# ── Duplicate Detection ──
section "Duplicate Detection"
if [[ -f "$HOME_DIR/.zshrc" ]]; then
    # Duplicate PATH additions
    path_adds=$(grep -n 'export PATH=' "$HOME_DIR/.zshrc" 2>/dev/null || true)
    path_count=$(echo "$path_adds" | grep -c 'PATH' 2>/dev/null || echo 0)
    if [[ "$path_count" -gt 5 ]]; then
        warn "$path_count PATH export lines in .zshrc (may have duplicates)"
        ((warnings++))
    fi

    # Duplicate export lines (exact matches)
    dupes=$(grep '^export ' "$HOME_DIR/.zshrc" 2>/dev/null | sort | uniq -d)
    if [[ -n "$dupes" ]]; then
        warn "Duplicate export lines found:"
        echo "$dupes" | while read -r line; do
            info "  $line"
        done
        ((warnings++))
    else
        ok "No duplicate export lines"
    fi
fi

# ── Secret Exposure Scan ──
section "Secret Scan"
secret_patterns=(
    'sk-[a-zA-Z0-9_\-]{20,}'
    'AKIA[A-Z0-9]{16}'
    'gh[pousr]_[A-Za-z0-9_]{36,}'
    '(api[_-]?key|apikey|api_secret|access_token|auth_token|password|secret)[[:space:]]*=[[:space:]]*["'"'"']?[A-Za-z0-9_\-]{16,}'
)
secrets_found=0
for f in .zshenv .zprofile .zshrc .profile; do
    path="$HOME_DIR/$f"
    [[ ! -f "$path" ]] && continue
    for pattern in "${secret_patterns[@]}"; do
        matches=$(grep -inE "$pattern" "$path" 2>/dev/null || true)
        if [[ -n "$matches" ]]; then
            while IFS= read -r match; do
                err "Possible secret in $f: $match"
                ((secrets_found++))
            done <<< "$matches"
        fi
    done
done
if [[ $secrets_found -eq 0 ]]; then
    ok "No obvious secrets detected"
else
    ((errors += secrets_found))
fi

# ── Environment Summary ──
section "Environment Summary"
env_count=$(zsh -l -c 'env | wc -l' 2>/dev/null | tr -d ' ' || echo 'unknown')
alias_count=$(zsh -i -c 'alias | wc -l' 2>/dev/null | tr -d ' ' || echo 'unknown')
func_count=$(zsh -i -c 'print -l ${(ok)functions} | wc -l' 2>/dev/null | tr -d ' ' || echo 'unknown')
info "Environment variables: $env_count"
info "Aliases: $alias_count"
info "Functions: $func_count"

# ── Summary ──
section "Summary"
if [[ $errors -gt 0 ]]; then
    err "$errors error(s) found"
fi
if [[ $warnings -gt 0 ]]; then
    warn "$warnings warning(s) found"
fi
if [[ $errors -eq 0 && $warnings -eq 0 ]]; then
    ok "Shell environment looks healthy"
fi

exit $((errors > 0 ? 2 : warnings > 0 ? 1 : 0))
