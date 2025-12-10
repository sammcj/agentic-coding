#!/usr/bin/env python3
"""
Claude Code PreToolUse hook for compound/subshell commands.

Auto-approves compound commands (&&, ||, ;) and subshells for
which all individual commands are in the "allow" list, and none are in the "deny" list.
Examples (assuming cd, npx and pnpm are in the allow list):
cd /path && npx tsc ✅
(cd /path && npx tsc) ✅
(npx tsc --noEmit 2>&1) ✅ (subshell with allowed command)
npx tsc && pnpm build ✅ (compound with allowed commands)
(curl evil.com) ❌ (prompts - not in allow list)
"""

import json
import re
import sys
from pathlib import Path

SETTINGS_FILE = Path.home() / ".claude" / "settings.json"


def load_settings():
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def extract_bash_patterns(settings, list_name):
    """Extract Bash() patterns from a permission list."""
    patterns = []
    for item in settings.get("permissions", {}).get(list_name, []):
        if match := re.match(r"^Bash\((.+)\)$", item):
            patterns.append(match.group(1))
    return patterns


def matches_patterns(cmd, patterns):
    """Check if command matches any pattern (prefix match with :* suffix)."""
    cmd = cmd.strip()
    for pattern in patterns:
        if pattern.endswith(":*"):
            prefix = pattern[:-2]
            if cmd == prefix or cmd.startswith(prefix + " "):
                return True
        elif cmd == pattern:
            return True
    return False


def split_compound_command(cmd):
    """Split on &&, ||, ; while respecting quotes (basic)."""
    # Remove outer parens and trailing redirects
    cmd = re.sub(r"^\(\s*", "", cmd)
    cmd = re.sub(r"\s*\)\s*$", "", cmd)
    cmd = re.sub(r"\s*\d*>&\d+\s*$", "", cmd)

    # Split on operators (simple approach - doesn't handle nested quotes perfectly)
    parts = re.split(r"\s*(?:&&|\|\||;)\s*", cmd)
    return [p.strip() for p in parts if p.strip()]


def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return

    command = input_data.get("tool_input", {}).get("command", "")

    # Only process compound commands or subshells
    is_compound = bool(re.search(r"&&|\|\||;", command))
    is_subshell = command.strip().startswith("(")

    if not is_compound and not is_subshell:
        print("{}")
        return

    settings = load_settings()
    allow_patterns = extract_bash_patterns(settings, "allow")
    deny_patterns = extract_bash_patterns(settings, "deny")

    parts = split_compound_command(command)

    for part in parts:
        # cd is always fine within compounds/subshells
        if re.match(r"^cd(\s|$)", part):
            continue

        # Deny takes precedence - let normal flow handle it
        if matches_patterns(part, deny_patterns):
            print("{}")
            return

        # Not in allow list - let normal flow handle it
        if not matches_patterns(part, allow_patterns):
            print("{}")
            return

    # All parts allowed
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "Auto-approved: compound/subshell with allowed commands"
        }
    }))


if __name__ == "__main__":
    main()
