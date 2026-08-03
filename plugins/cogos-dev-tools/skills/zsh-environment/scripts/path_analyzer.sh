#!/usr/bin/env zsh
set -uo pipefail

HOME_DIR="$HOME"
RED='\033[0;31m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

section() { echo -e "\n${BOLD}${CYAN}=== $1 ===${NC}"; }

# ── Get current PATH ──
CURRENT_PATH=$(zsh -l -i -c 'echo $PATH' 2>/dev/null || echo "$PATH")

path_entries=("${(@s/:/)CURRENT_PATH}")

# ── Numbered PATH listing ──
section "PATH Entries (${#path_entries[@]} total)"
typeset -A seen_paths
typeset -A seen_resolved
duplicates=0
dead=0
idx=1

for entry in "${path_entries[@]}"; do
    [[ -z "$entry" ]] && continue
    flags=()

    # Resolve ~ and symlinks for comparison
    expanded="${entry/#\~/$HOME_DIR}"
    resolved=$(cd "$expanded" 2>/dev/null && pwd -P 2>/dev/null || echo "$expanded")

    # Check duplicate (exact)
    if [[ -n "${seen_paths[$entry]:-}" ]]; then
        flags+=("${YELLOW}DUPLICATE${NC}")
        ((duplicates++))
    fi
    seen_paths[$entry]=1

    # Check duplicate (resolved path differs but same dir)
    if [[ -n "${seen_resolved[$resolved]:-}" && "$entry" != "${seen_resolved[$resolved]}" ]]; then
        flags+=("${YELLOW}ALIAS-DUP of ${seen_resolved[$resolved]}${NC}")
        ((duplicates++))
    fi
    seen_resolved[$resolved]="${entry}"

    # Check existence
    if [[ ! -d "$expanded" ]]; then
        if [[ "$expanded" == /Volumes/* ]]; then
            flags+=("${YELLOW}UNMOUNTED${NC}")
        else
            flags+=("${RED}MISSING${NC}")
        fi
        ((dead++))
    fi

    flag_str=""
    if [[ ${#flags[@]} -gt 0 ]]; then
        flag_str=" [$(echo -e "${(j:, :)flags}")]"
    fi

    printf "  %2d. %s%b\n" "$idx" "$entry" "$flag_str"
    ((idx++))
done

# ── Origin tracing ──
section "PATH Origin Tracing"
config_files=("$HOME_DIR/.zshenv" "$HOME_DIR/.zprofile" "$HOME_DIR/.zshrc" "$HOME_DIR/.profile")

for entry in "${path_entries[@]}"; do
    [[ -z "$entry" ]] && continue
    # Normalize for grep: replace $HOME with patterns
    search_term="$entry"
    search_term_home="${entry/#$HOME_DIR/\$HOME}"
    search_term_tilde="${entry/#$HOME_DIR/\~}"

    sources=()
    for cfg in "${config_files[@]}"; do
        [[ ! -f "$cfg" ]] && continue
        cfg_name="$(basename "$cfg")"
        if grep -qF "$search_term" "$cfg" 2>/dev/null || \
           grep -qF "$search_term_home" "$cfg" 2>/dev/null || \
           grep -qF "$search_term_tilde" "$cfg" 2>/dev/null; then
            lineno=$(grep -nF "$search_term" "$cfg" 2>/dev/null | head -1 | cut -d: -f1)
            [[ -z "$lineno" ]] && lineno=$(grep -nF "$search_term_home" "$cfg" 2>/dev/null | head -1 | cut -d: -f1)
            [[ -z "$lineno" ]] && lineno=$(grep -nF "$search_term_tilde" "$cfg" 2>/dev/null | head -1 | cut -d: -f1)
            sources+=("$cfg_name:${lineno:-?}")
        fi
    done

    if [[ ${#sources[@]} -gt 0 ]]; then
        printf "  %-50s <- %s\n" "$entry" "${sources[*]}"
    elif [[ "$entry" == /usr/local/bin || "$entry" == /usr/bin || "$entry" == /bin || \
            "$entry" == /usr/sbin || "$entry" == /sbin || "$entry" == /opt/homebrew/* || \
            "$entry" == *cryptex* ]]; then
        printf "  %-50s <- %s\n" "$entry" "system (/etc/paths or brew shellenv)"
    else
        printf "  %-50s <- %b\n" "$entry" "${YELLOW}unknown origin${NC}"
    fi
done

# ── Shadowed commands check ──
section "Command Shadowing"
common_cmds=(python python3 node npm git ruby perl)
for cmd in "${common_cmds[@]}"; do
    locations=$(zsh -l -i -c "whence -a $cmd" 2>/dev/null || true)
    count=$(echo "$locations" | grep -c '/' 2>/dev/null || echo 0)
    if [[ "$count" -gt 1 ]]; then
        first=$(echo "$locations" | head -1)
        echo -e "  ${YELLOW}$cmd${NC} has $count locations (active: $first)"
        echo "$locations" | tail -n +2 | while read -r loc; do
            echo "    shadowed: $loc"
        done
    fi
done

# ── Summary ──
section "Summary"
echo "  Total entries: ${#path_entries[@]}"
echo "  Duplicates: $duplicates"
echo "  Dead/missing: $dead"
unique_count=${#seen_resolved[@]}
echo "  Unique directories: $unique_count"
