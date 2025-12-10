package main

// Claude Code PreToolUse hook for compound/subshell commands.

// Auto-approves compound commands (&&, ||, ;) and subshells for
// which all individual commands are in the "allow" list, and none are in the "deny" list.
// Examples (assuming cd, npx and pnpm are in the allow list):
// cd /path && npx tsc ✅
// (cd /path && npx tsc) ✅
// (npx tsc --noEmit 2>&1) ✅ (subshell with allowed command)
// npx tsc && pnpm build ✅ (compound with allowed commands)
// (curl evil.com) ❌ (prompts - not in allow list)

// Build with: go build -ldflags="-s -w" ./approve-compound-commands.go

// Configure in ~/.claude/settings.json like so:
// "hooks": {
// 	"PreToolUse": [
// 		{
// 			"matcher": "Bash",
// 			"hooks": [
// 				{
// 					"type": "command",
// 					"command": "~/.claude/hooks/approve-compound-commands"
// 				}
// 			]
// 		}
// 	]
// }

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

type Settings struct {
	Permissions struct {
		Allow []string `json:"allow"`
		Deny  []string `json:"deny"`
	} `json:"permissions"`
}

type HookInput struct {
	ToolInput struct {
		Command string `json:"command"`
	} `json:"tool_input"`
}

var (
	bashPattern    = regexp.MustCompile(`^Bash\((.+)\)$`)
	compoundOps    = regexp.MustCompile(`\s*(&&|\|\||;)\s*`)
	cdPrefix       = regexp.MustCompile(`^cd(\s|$)`)
	trailingRedir  = regexp.MustCompile(`\s*\d*>&\d+\s*$`)
)

func main() {
	var input HookInput
	if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil {
		fmt.Println("{}")
		return
	}

	cmd := input.ToolInput.Command
	isCompound := strings.Contains(cmd, "&&") || strings.Contains(cmd, "||") || strings.Contains(cmd, ";")
	isSubshell := strings.HasPrefix(strings.TrimSpace(cmd), "(")

	if !isCompound && !isSubshell {
		fmt.Println("{}")
		return
	}

	settings := loadSettings()
	allowPatterns := extractBashPatterns(settings.Permissions.Allow)
	denyPatterns := extractBashPatterns(settings.Permissions.Deny)

	for _, part := range splitCommand(cmd) {
		if cdPrefix.MatchString(part) {
			continue
		}
		if matchesAny(part, denyPatterns) || !matchesAny(part, allowPatterns) {
			fmt.Println("{}")
			return
		}
	}

	fmt.Println(`{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"Auto-approved compound/subshell"}}`)
}

func loadSettings() Settings {
	home, _ := os.UserHomeDir()
	data, err := os.ReadFile(filepath.Join(home, ".claude", "settings.json"))
	if err != nil {
		return Settings{}
	}
	var s Settings
	json.Unmarshal(data, &s)
	return s
}

func extractBashPatterns(items []string) []string {
	var patterns []string
	for _, item := range items {
		if m := bashPattern.FindStringSubmatch(item); m != nil {
			patterns = append(patterns, m[1])
		}
	}
	return patterns
}

func splitCommand(cmd string) []string {
	cmd = strings.TrimPrefix(strings.TrimSpace(cmd), "(")
	cmd = strings.TrimSuffix(strings.TrimSpace(cmd), ")")
	cmd = trailingRedir.ReplaceAllString(cmd, "")
	parts := compoundOps.Split(cmd, -1)
	var result []string
	for _, p := range parts {
		if p = strings.TrimSpace(p); p != "" {
			result = append(result, p)
		}
	}
	return result
}

func matchesAny(cmd string, patterns []string) bool {
	cmd = strings.TrimSpace(cmd)
	for _, pattern := range patterns {
		if strings.HasSuffix(pattern, ":*") {
			prefix := strings.TrimSuffix(pattern, ":*")
			if cmd == prefix || strings.HasPrefix(cmd, prefix+" ") {
				return true
			}
		} else if cmd == pattern {
			return true
		}
	}
	return false
}
