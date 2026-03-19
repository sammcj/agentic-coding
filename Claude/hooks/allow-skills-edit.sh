#!/usr/bin/env bash
set -euo pipefail

# Auto-approve Edit/Write operations on files within ~/.claude/skills/ and ~/.claude/agents/
# This bypasses the built-in self-edit protection for these directories.

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')
HOOK_EVENT=$(echo "$INPUT" | jq -r '.hook_event_name // empty')

if [ -z "$FILE_PATH" ]; then
  exit 0
fi

# Resolve ~ and normalise the path
RESOLVED=$(cd "$(dirname "$FILE_PATH" 2>/dev/null)" 2>/dev/null && echo "$(pwd -P)/$(basename "$FILE_PATH")" || echo "$FILE_PATH")
SKILLS_DIR="$HOME/.claude/skills"
AGENTS_DIR="$HOME/.claude/agents"

if [[ "$RESOLVED" == "$SKILLS_DIR"/* ]] || [[ "$RESOLVED" == "$AGENTS_DIR"/* ]]; then
  if [[ "$HOOK_EVENT" == "PermissionRequest" ]]; then
    jq -n '{
      hookSpecificOutput: {
        hookEventName: "PermissionRequest",
        decision: {
          behavior: "allow"
        }
      }
    }'
  else
    jq -n '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "allow",
        permissionDecisionReason: "Auto-approved: file is in skills/agents directory"
      }
    }'
  fi
  exit 0
fi

exit 0
