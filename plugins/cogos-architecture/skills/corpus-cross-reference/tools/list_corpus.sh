#!/usr/bin/env bash
# list_corpus.sh
# Enumerate the four RFC/ADR corpora and emit a structured index.
#
# Usage:
#   ./list_corpus.sh                  # all four corpora
#   ./list_corpus.sh --corpus=cog     # cog workspace only
#   ./list_corpus.sh --corpus=cogos   # cogos repo only
#   ./list_corpus.sh --format=json    # JSON output (default: table)
#
# Output columns: corpus | type | number | slug | status | title | tags
#
# Depends on: bash, grep, find, awk, sed (standard POSIX tools)
# Optionally: yq (for reliable YAML parsing) — falls back to grep-based extraction

set -euo pipefail

COG_WORKSPACE="${COGOS_WORKSPACE:-$HOME/workspaces/cog}"
MYRGIC_ROOT="${MYRGIC_REPOS_ROOT:-$HOME/workspaces/myrgic}"

CORPUS="both"
FORMAT="table"

# Parse args
for arg in "$@"; do
  case "$arg" in
    --corpus=*) CORPUS="${arg#--corpus=}" ;;
    --format=*) FORMAT="${arg#--format=}" ;;
    *) echo "Unknown argument: $arg" >&2; exit 1 ;;
  esac
done

# Extract frontmatter field from a file using grep (yq-free fallback)
extract_field() {
  local file="$1"
  local field="$2"
  # Handles: field: value AND field: "quoted value"
  grep -m1 "^${field}:" "$file" 2>/dev/null \
    | sed 's/^[^:]*: *//' \
    | sed 's/^"\(.*\)"$/\1/' \
    | tr -d '\r' \
    || true
}

extract_nested_field() {
  local file="$1"
  local field="$2"
  # For nested cog: blocks — look for the field indented by 2 spaces
  grep -m1 "^  ${field}:" "$file" 2>/dev/null \
    | sed 's/^  [^:]*: *//' \
    | sed 's/^"\(.*\)"$/\1/' \
    | tr -d '\r' \
    || true
}

extract_tags() {
  local file="$1"
  grep -m1 "^tags:" "$file" 2>/dev/null \
    | sed 's/^tags: *//' \
    | tr -d '[]' \
    | tr ',' ' ' \
    | tr -s ' ' \
    || true
}

print_header() {
  if [[ "$FORMAT" == "table" ]]; then
    printf "%-8s %-4s %-6s %-55s %-12s %s\n" "corpus" "type" "num" "title" "status" "tags"
    printf "%s\n" "$(printf '%0.s-' {1..120})"
  fi
}

process_file() {
  local corpus_name="$1"
  local file="$2"
  local doc_type="$3"  # adr or rfc

  local number status title tags

  if [[ "$doc_type" == "rfc" ]]; then
    # RFC frontmatter may use nested cog: block
    local nested_rfc
    nested_rfc=$(extract_nested_field "$file" "rfc")
    if [[ -n "$nested_rfc" ]]; then
      number="$nested_rfc"
    else
      number=$(extract_field "$file" "rfc")
    fi
  else
    number=$(extract_field "$file" "adr")
  fi

  status=$(extract_field "$file" "status")
  title=$(extract_field "$file" "title")
  tags=$(extract_tags "$file")

  # Pad number
  local num_padded
  if [[ "$corpus_name" == cogos* ]]; then
    num_padded=$(printf "%04d" "${number:-0}" 2>/dev/null || echo "${number:-?}")
  else
    num_padded=$(printf "%03d" "${number:-0}" 2>/dev/null || echo "${number:-?}")
  fi

  if [[ "$FORMAT" == "json" ]]; then
    printf '{"corpus":"%s","type":"%s","number":"%s","file":"%s","status":"%s","title":"%s","tags":"%s"}\n' \
      "$corpus_name" "$doc_type" "$num_padded" "$file" "${status:-unknown}" "${title:-unknown}" "$tags"
  else
    # Truncate title to fit
    local short_title="${title:0:53}"
    printf "%-8s %-4s %-6s %-55s %-12s %s\n" \
      "$corpus_name" "$doc_type" "$num_padded" "$short_title" "${status:-?}" "$tags"
  fi
}

# --- Main ---

print_header

if [[ "$CORPUS" == "cog" || "$CORPUS" == "both" ]]; then
  # cog workspace ADRs
  adr_dir="${COG_WORKSPACE}/.cog/adr"
  if [[ -d "$adr_dir" ]]; then
    while IFS= read -r f; do
      process_file "cog" "$f" "adr"
    done < <(find "$adr_dir" -maxdepth 1 -name '[0-9]*.cog.md' | sort)
  fi

  # cog workspace RFCs
  rfc_dir="${COG_WORKSPACE}/.cog/conf/spec/rfc"
  if [[ -d "$rfc_dir" ]]; then
    while IFS= read -r f; do
      process_file "cog" "$f" "rfc"
    done < <(find "$rfc_dir" -maxdepth 1 -name 'RFC-[0-9]*.cog.md' | sort)
  fi
fi

if [[ "$CORPUS" == "cogos" || "$CORPUS" == "both" ]]; then
  # cogos repo ADRs
  cogos_adr_dir="${MYRGIC_ROOT}/cogos/docs/adr"
  if [[ -d "$cogos_adr_dir" ]]; then
    while IFS= read -r f; do
      process_file "cogos" "$f" "adr"
    done < <(find "$cogos_adr_dir" -maxdepth 1 -name '[0-9]*.md' | sort)
  fi

  # cogos repo RFCs
  cogos_rfc_dir="${MYRGIC_ROOT}/cogos/docs/rfcs"
  if [[ -d "$cogos_rfc_dir" ]]; then
    while IFS= read -r f; do
      process_file "cogos" "$f" "rfc"
    done < <(find "$cogos_rfc_dir" -maxdepth 1 -name '[0-9]*.md' | sort)
  fi
fi
