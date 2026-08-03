#!/usr/bin/env bash
# storage_report.sh — Non-interactive macOS storage analysis for Claude
# Produces a concise text report of disk usage, caches, and cleanup opportunities.
# Requires: dust (brew install dust)
# Optional: mole (brew install mole), kondo (brew install kondo)
set -euo pipefail

echo "=== macOS Storage Report ==="
echo "Generated: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# --- Disk overview ---
echo "## Disk Overview"
df -h / /System/Volumes/Data 2>/dev/null | tail -2
echo ""

# --- Top directories by actual disk usage (dust handles sparse files correctly) ---
echo "## Top Directories (actual disk usage, depth 2)"
if command -v dust &>/dev/null; then
    dust -n 20 -d 2 ~ 2>/dev/null || echo "(dust scan failed)"
else
    du -sh ~/Library ~/Documents ~/Downloads ~/Workspaces ~/Desktop ~/Parallels ~/*.pvm 2>/dev/null | sort -rh | head -20
fi
echo ""

# --- Caches ---
echo "## Cache Sizes"
for d in \
    "$HOME/Library/Caches" \
    "$HOME/.cache" \
    "$HOME/.bun/install/cache" \
    "$HOME/.yarn/berry/cache" \
    "$HOME/.npm/_cacache" \
    "$HOME/go/pkg/mod/cache" \
    "$HOME/.cargo/registry" \
    "$HOME/Library/Caches/Homebrew" \
    "$HOME/.cache/huggingface"; do
    if [ -d "$d" ]; then
        size=$(du -sh "$d" 2>/dev/null | cut -f1)
        echo "  $size  $d"
    fi
done
echo ""

# --- Dev artifacts (node_modules, target/, .venv, __pycache__) ---
echo "## Dev Artifact Directories"
echo "### node_modules"
if command -v dust &>/dev/null; then
    # Find top 10 node_modules by size. Adjust this list of root directories
    # to match wherever the user actually keeps their projects.
    find ~/Workspaces ~/Projects ~/dev ~/code 2>/dev/null -name node_modules -type d -maxdepth 5 -not -path '*/node_modules/*/node_modules' | while read -r d; do
        du -sh "$d" 2>/dev/null
    done | sort -rh | head -10
else
    find ~ -name node_modules -type d -maxdepth 5 -not -path '*/node_modules/*/node_modules' 2>/dev/null | head -10 | while read -r d; do
        du -sh "$d" 2>/dev/null
    done | sort -rh
fi
echo ""

echo "### Rust target/"
find ~ -name target -type d -maxdepth 6 2>/dev/null | while read -r d; do
    if [ -f "$d/../Cargo.toml" ] || [ -f "$d/../Cargo.lock" ]; then
        du -sh "$d" 2>/dev/null
    fi
done | sort -rh | head -10
echo ""

echo "### Python virtualenvs"
find ~ -maxdepth 5 \( -name .venv -o -name venv \) -type d 2>/dev/null | while read -r d; do
    if [ -d "$d/lib" ] || [ -d "$d/bin" ]; then
        du -sh "$d" 2>/dev/null
    fi
done | sort -rh | head -10
echo ""

# --- Docker ---
echo "## Docker"
docker_raw="$HOME/Library/Containers/com.docker.docker/Data/vms/0/data/Docker.raw"
if [ -f "$docker_raw" ]; then
    logical=$(ls -lh "$docker_raw" 2>/dev/null | awk '{print $5}')
    actual=$(du -sh "$docker_raw" 2>/dev/null | cut -f1)
    echo "  Docker.raw: $actual actual / $logical logical (sparse file)"
    if command -v docker &>/dev/null && docker info &>/dev/null 2>&1; then
        echo "  Docker system df:"
        docker system df 2>/dev/null | sed 's/^/    /'
    fi
else
    echo "  Docker not found or not installed"
fi
echo ""

# --- Mole dry-run summary (if available) ---
echo "## Mole Cleanup Preview"
if command -v mo &>/dev/null; then
    mo clean 2>&1 | grep -E '(✓|◎|➤|Total|Freed|GB|MB)' | head -30
else
    echo "  (mole not installed — brew install mole)"
fi
echo ""

# --- Large files ---
echo "## Largest Files (top 15)"
find ~ -type f -not -path '*/Library/CloudStorage/*' -not -path '*/.Trash/*' 2>/dev/null -size +100M | while read -r f; do
    du -sh "$f" 2>/dev/null
done | sort -rh | head -15
echo ""

echo "=== End Report ==="
