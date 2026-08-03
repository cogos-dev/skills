#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="$HOME/.config/zsh-backups"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
MAX_BACKUPS=20

CONFIG_FILES=(
    "$HOME/.zshrc"
    "$HOME/.zshenv"
    "$HOME/.zprofile"
    "$HOME/.profile"
    "$HOME/.zlogin"
)

mkdir -p "$BACKUP_DIR"

backed_up=0
for src in "${CONFIG_FILES[@]}"; do
    if [[ -f "$src" ]]; then
        basename="$(basename "$src" | sed 's/^\.//')"
        dest="$BACKUP_DIR/${basename}.${TIMESTAMP}"
        cp "$src" "$dest"
        echo "  Backed up: $src -> $dest"
        ((backed_up++))
    fi
done

if [[ $backed_up -eq 0 ]]; then
    echo "No config files found to back up."
    exit 0
fi

echo ""
echo "Backed up $backed_up file(s) to $BACKUP_DIR/"

# Prune old backups per config file
pruned=0
for src in "${CONFIG_FILES[@]}"; do
    basename="$(basename "$src" | sed 's/^\.//')"
    files=("$BACKUP_DIR/${basename}."*)
    [[ ! -e "${files[0]}" ]] && continue
    count=${#files[@]}
    if [[ "$count" -gt "$MAX_BACKUPS" ]]; then
        to_remove=$((count - MAX_BACKUPS))
        # Sort oldest first, remove extras
        printf '%s\n' "${files[@]}" | sort | head -n "$to_remove" | while read -r old; do
            rm -f "$old"
            ((pruned++)) || true
        done
    fi
done

if [[ $pruned -gt 0 ]]; then
    echo "Pruned $pruned old backup(s) (keeping last $MAX_BACKUPS per file)."
fi

total=$(find "$BACKUP_DIR" -maxdepth 1 -type f | wc -l | tr -d ' ')
echo "Total backups: $total"
echo ""
echo "Restore with: cp $BACKUP_DIR/zshrc.$TIMESTAMP ~/.zshrc"
