#!/usr/bin/env bash
set -euo pipefail

SETTINGS_FILE="$HOME/.claude/settings.json"
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Check if this is a compound command (&&, ||, ;) or subshell
is_compound=false
is_subshell=false

[[ "$command" =~ \&\&|\|\||\; ]] && is_compound=true
[[ "$command" =~ ^\([[:space:]]* ]] && is_subshell=true

# If neither compound nor subshell, let native permissions handle it
if ! $is_compound && ! $is_subshell; then
  echo '{}'
  exit 0
fi

# Extract Bash patterns from settings.json
get_patterns() {
  local list_name="$1"
  jq -r ".permissions.${list_name}[]? // empty" "$SETTINGS_FILE" 2>/dev/null | \
    grep -E '^Bash\(' | \
    sed -E 's/^Bash\(([^)]+)\)$/\1/'
}

# Check if a command matches any pattern in a list
matches_pattern_list() {
  local cmd="$1"
  local list_name="$2"

  while IFS= read -r pattern; do
    [[ -z "$pattern" ]] && continue

    # Handle :* suffix (prefix match)
    if [[ "$pattern" == *":*" ]]; then
      local prefix="${pattern%:\*}"
      if [[ "$cmd" == "$prefix" ]] || [[ "$cmd" == "$prefix "* ]]; then
        return 0
      fi
    else
      # Exact match
      if [[ "$cmd" == "$pattern" ]]; then
        return 0
      fi
    fi
  done < <(get_patterns "$list_name")

  return 1
}

# Strip outer parentheses and trailing redirects for parsing
clean_cmd="$command"
clean_cmd="${clean_cmd#\(}"
clean_cmd="${clean_cmd%\)}"
# Remove trailing redirects like 2>&1
clean_cmd=$(echo "$clean_cmd" | sed -E 's/[[:space:]]*[0-9]*>&[0-9]+[[:space:]]*$//')

# Split compound command into parts (handles &&, ||, ;)
IFS=$'\n' read -r -d '' -a cmd_parts < <(
  echo "$clean_cmd" | sed -E 's/[[:space:]]*(&&|\|\||;)[[:space:]]*/\n/g' && printf '\0'
) || true

# Check each part
all_allowed=true
for part in "${cmd_parts[@]}"; do
  # Trim whitespace
  part="${part#"${part%%[![:space:]]*}"}"
  part="${part%"${part##*[![:space:]]}"}"

  [[ -z "$part" ]] && continue

  # cd is always fine within compounds/subshells
  [[ "$part" =~ ^cd([[:space:]]|$) ]] && continue

  # Check deny list first - if matched, let normal flow handle it
  if matches_pattern_list "$part" "deny"; then
    echo '{}'
    exit 0
  fi

  # Check allow list
  if ! matches_pattern_list "$part" "allow"; then
    all_allowed=false
  fi
done

if $all_allowed; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"Auto-approved: compound/subshell with allowed commands"}}'
else
  echo '{}'
fi
