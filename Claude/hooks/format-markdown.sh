#!/usr/bin/env bash
set -euo pipefail

# Claude Code PostToolUse hook: format markdown files after edit/write.
#
# Path control (sources combined):
#   1. ALLOWED_PATHS array below - edit directly in this script
#   2. CLAUDE_HOOK_MD_LINT_PATHS env var - colon-separated paths
#   Blocklist: .nomdformat - place in any project root to disable formatting there
#
# If any allowed paths are defined (either source), ONLY files under those paths are formatted.
# If no allowed paths are defined, all markdown files are formatted (minus .nomdformat opt-outs).
#
# All output suppressed to avoid bloating Claude's context.

# --- Edit this array to add permanent allowed paths ---
ALLOWED_PATHS=(
  "$HOME/git/sammcj"
  "$HOME/Downloads"
)

# Extract file_path from hook JSON via jq (no code execution surface, unlike python3)
file_path="$(jq -r '.tool_input.file_path // .file_path // empty' 2>/dev/null)" || exit 0
[[ -z "$file_path" ]] && exit 0

# Only process markdown files
case "$file_path" in
*.md | *.markdown | *.mdx) ;;
*) exit 0 ;;
esac

[[ -f "$file_path" ]] || exit 0

# Resolve symlinks and verify the real path still has a markdown extension
resolved_path="$(realpath "$file_path" 2>/dev/null)" || exit 0
case "$resolved_path" in
*.md | *.markdown | *.mdx) ;;
*) exit 0 ;;
esac

# Merge env var paths (colon-separated) into the allowed list
if [[ -n "${CLAUDE_HOOK_MD_LINT_PATHS:-}" ]]; then
  IFS=':' read -ra env_paths <<<"$CLAUDE_HOOK_MD_LINT_PATHS"
  for p in "${env_paths[@]}"; do
    [[ -n "$p" ]] && ALLOWED_PATHS+=("${p/#\~/$HOME}")
  done
fi

# Allowlist check: resolved path must be under an allowed directory
if [[ ${#ALLOWED_PATHS[@]} -gt 0 ]]; then
  allowed=false
  for path_entry in "${ALLOWED_PATHS[@]}"; do
    [[ "$path_entry" != */ ]] && path_entry="$path_entry/"
    if [[ "$resolved_path" == "$path_entry"* ]]; then
      allowed=true
      break
    fi
  done
  [[ "$allowed" == false ]] && exit 0
fi

# Blocklist check: .nomdformat marker in project root
dir="$(dirname "$file_path")"
while [[ "$dir" != "/" ]]; do
  if [[ -f "$dir/.nomdformat" ]]; then
    exit 0
  fi
  if [[ -f "$dir/.git/HEAD" || -d "$dir/.git" ]]; then
    break
  fi
  dir="$(dirname "$dir")"
done
[[ -f "$dir/.nomdformat" ]] && exit 0

# Run prettier on the resolved (real) path with 2s timeout - all output suppressed
timeout 2 /Users/samm/Library/pnpm/prettier --write --parser markdown "$resolved_path" >/dev/null 2>&1 || true

exit 0
