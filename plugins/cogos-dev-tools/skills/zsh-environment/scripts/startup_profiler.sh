#!/usr/bin/env bash
set -euo pipefail

CYAN='\033[0;36m'
YELLOW='\033[0;33m'
GREEN='\033[0;32m'
RED='\033[0;31m'
BOLD='\033[1m'
NC='\033[0m'

section() { echo -e "\n${BOLD}${CYAN}=== $1 ===${NC}"; }
RUNS=3

time_shell() {
    local flags="$1"
    local total=0
    for ((i = 0; i < RUNS; i++)); do
        t=$( { time zsh $flags -c 'exit' ; } 2>&1 )
        real=$(echo "$t" | grep real | awk '{print $2}')
        # Parse time formats: 0m0.123s or 0.123
        if [[ "$real" == *m*s ]]; then
            mins="${real%%m*}"
            secs="${real##*m}"
            secs="${secs%s}"
            ms=$(echo "$mins $secs" | awk '{printf "%.0f", ($1*60 + $2)*1000}')
        else
            ms=$(echo "$real" | awk '{printf "%.0f", $1*1000}')
        fi
        total=$((total + ms))
    done
    echo $((total / RUNS))
}

section "Shell Startup Timing (average of $RUNS runs)"

echo -n "  Bare shell (--no-rcs)... "
bare_ms=$(time_shell "--no-rcs -i")
echo "${bare_ms}ms"

echo -n "  Interactive login shell... "
full_ms=$(time_shell "-l -i")
echo "${full_ms}ms"

overhead=$((full_ms - bare_ms))
echo ""
echo -e "  Bare:     ${GREEN}${bare_ms}ms${NC}"
echo -e "  Full:     ${full_ms}ms"
echo -e "  Overhead: ${BOLD}${overhead}ms${NC} (from config files + plugins)"

if [[ $full_ms -lt 200 ]]; then
    echo -e "  Rating:   ${GREEN}Fast${NC}"
elif [[ $full_ms -lt 500 ]]; then
    echo -e "  Rating:   ${YELLOW}Moderate${NC}"
else
    echo -e "  Rating:   ${RED}Slow${NC}"
fi

# ── Trace analysis ──
section "Startup Trace (slow operations)"
echo "  Tracing shell startup with zsh -x (this may take a moment)..."
echo ""

trace_file=$(mktemp)
trap "rm -f '$trace_file'" EXIT

# Capture trace output, time each section
{ time zsh -x -l -i -c 'exit' ; } 2>"$trace_file" || true

# Find slow patterns in trace
slow_patterns=(
    "nvm"
    "pyenv"
    "brew shellenv"
    "compinit"
    "compaudit"
    "oh-my-zsh"
    "source.*plugin"
    "eval"
)

echo "  Known slow operations found in trace:"
for pattern in "${slow_patterns[@]}"; do
    count=$(grep -c "$pattern" "$trace_file" 2>/dev/null || echo 0)
    if [[ "$count" -gt 0 ]]; then
        echo -e "    ${YELLOW}$pattern${NC}: $count trace lines"
    fi
done

# Count total trace lines
total_lines=$(wc -l < "$trace_file" | tr -d ' ')
echo ""
echo "  Total trace lines: $total_lines"

# ── Recommendations ──
section "Recommendations"
if [[ $full_ms -gt 300 ]]; then
    echo "  Startup is over 300ms. Consider:"

    if grep -q 'nvm.sh' "$HOME/.zshrc" 2>/dev/null; then
        echo -e "  ${YELLOW}*${NC} nvm: Use the oh-my-zsh nvm plugin's lazy loading instead of"
        echo "    sourcing nvm.sh directly. Remove the manual [ -s \"\$NVM_DIR/nvm.sh\" ] lines."
    fi

    if grep -q 'pyenv init' "$HOME/.zshrc" 2>/dev/null; then
        echo -e "  ${YELLOW}*${NC} pyenv: Consider lazy-loading pyenv init or using pyenv's"
        echo "    shell integration with --path only (faster)."
    fi

    if grep -q 'compinit' "$trace_file" 2>/dev/null; then
        count=$(grep -c 'compinit' "$trace_file" 2>/dev/null || echo 0)
        if [[ "$count" -gt 1 ]]; then
            echo -e "  ${YELLOW}*${NC} compinit: Called $count times. Should only be called once."
        fi
    fi
else
    echo -e "  ${GREEN}Startup time looks good. No immediate action needed.${NC}"
fi
