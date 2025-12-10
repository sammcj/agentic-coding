#!/usr/bin/env bash
set -euo pipefail

# Read JSON from stdin
input=$(cat)
command=$(echo "$input" | jq -r '.tool_input.command // empty')

# Patterns to auto-approve: cd with chained commands, or subshell with cd
# Adjust these patterns to your needs
if [[ "$command" =~ ^cd[[:space:]].*\&\& ]] || \
   [[ "$command" =~ ^\([[:space:]]*cd[[:space:]] ]]; then
  echo '{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"Auto-approved cd compound command"}}'
  exit 0
fi

# Otherwise, let normal permission flow handle it
echo '{}'
exit 0
