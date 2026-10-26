package main

// Denied-host guard: denies a tool call whose input mentions a host listed in
// a WebFetch(domain:...) deny rule or sandbox.network.deniedDomains, when that
// call can reach the network without the sandbox proxy.
//
// The proxy already refuses those hosts for sandboxed Bash and Monitor, so
// their commands are only scanned when they bypass it (sandbox off,
// dangerouslyDisableSandbox, or a part matching sandbox.excludedCommands such
// as docker). That keeps `rg aliyuncs.com ~/logs` and commit messages working.
// WebFetch and MCP tools (context-mode's ctx_execute fetches outside the
// sandbox) are always scanned. Matching is on text, so an encoded or assembled
// URL gets through; the sandbox and the auto mode classifier stay primary.

import (
	"encoding/json"
	"regexp"
	"strings"
)

var webFetchDomain = regexp.MustCompile(`^WebFetch\(domain:([^)]+)\)$`)

// Host characters on either side mean a different name (notaliyuncs.com,
// aliyun.com.au). A single trailing dot is a fully qualified name.
const (
	hostLeft  = `(?:^|[^a-z0-9_-])`
	hostRight = `\.?(?:[^a-z0-9_.-]|$)`
)

type hostGuard struct {
	hosts     *regexp.Regexp
	excluded  []*regexp.Regexp
	sandboxed bool
}

func newHostGuard(s Settings) hostGuard {
	var entries []string
	for _, rule := range s.Permissions.Deny {
		if m := webFetchDomain.FindStringSubmatch(rule); m != nil {
			entries = append(entries, m[1])
		}
	}
	entries = append(entries, s.Sandbox.Network.DeniedDomains...)
	// (?s) lets a quoted newline inside `docker run ... sh -c "..."` still
	// match `docker *`; allow rules stay newline-blind because that is the
	// safe direction for approvals.
	var excluded []*regexp.Regexp
	for _, re := range compileAll(s.Sandbox.ExcludedCommands) {
		excluded = append(excluded, regexp.MustCompile("(?s)"+re.String()))
	}
	return hostGuard{
		hosts:     compileDeniedHosts(entries),
		excluded:  excluded,
		sandboxed: s.Sandbox.Enabled != nil && *s.Sandbox.Enabled,
	}
}

var envPrefix = regexp.MustCompile(`^(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)+`)

// compileDeniedHosts builds one case-insensitive regexp from host entries, or
// nil when there is nothing to match.
func compileDeniedHosts(entries []string) *regexp.Regexp {
	var alts []string
	for _, e := range entries {
		if alt := hostPattern(strings.ToLower(strings.TrimSpace(e))); alt != "" {
			alts = append(alts, alt)
		}
	}
	if len(alts) == 0 {
		return nil
	}
	re, err := regexp.Compile(`(?i)(?:` + strings.Join(alts, "|") + `)`)
	if err != nil {
		return nil
	}
	return re
}

func hostPattern(h string) string {
	h = strings.TrimPrefix(h, "*.")
	if h == "" || h == "*" {
		// A deny-everything rule is Claude Code's job; matching it here would
		// deny every tool call.
		return ""
	}
	if strings.HasPrefix(h, "[") {
		// Bracketed IPv6, optionally with a port: [fd00:ec2::254]:80
		if end := strings.Index(h, "]"); end > 0 {
			h = h[1:end]
		}
	} else if i := strings.LastIndex(h, ":"); i > 0 && strings.Count(h, ":") == 1 {
		h = h[:i]
	}
	esc := strings.ReplaceAll(regexp.QuoteMeta(h), `\*`, `[a-z0-9-]*`)
	if strings.ContainsAny(h, ".:") {
		return hostLeft + esc + hostRight
	}
	// Bare TLD entries (*.cn, *.ru) need host context so file names like
	// config.ru/ or a path segment like translations/zh.cn/ don't trip the
	// guard: a // or user@ before the host, or at least two labels before the
	// TLD outside a path. A schemeless single-label host (evil.cn/x) is missed.
	const start = `(?:^|[^a-z0-9_/.-])`
	label := `[a-z0-9-]+`
	return `//(?:[^/\s"'@]*@)?[a-z0-9.-]*\.` + esc + hostRight +
		`|@` + label + `(?:\.` + label + `)*\.` + esc + hostRight +
		`|` + start + label + `(?:\.` + label + `)+\.` + esc + `(?::\d+)?(?:[/\s"'?#]|$)`
}

// deniedHost returns the first denied host reference in the tool input, or "".
func (g hostGuard) deniedHost(toolName string, raw json.RawMessage) string {
	if g.hosts == nil || len(raw) == 0 {
		return ""
	}
	var input any
	if json.Unmarshal(raw, &input) != nil {
		return ""
	}
	if toolName == "Bash" || toolName == "Monitor" {
		fields, _ := input.(map[string]any)
		if !g.bypassesSandbox(fields) {
			return ""
		}
		delete(fields, "description")
	}
	var b strings.Builder
	joinStrings(input, &b)
	return strings.Trim(g.hosts.FindString(b.String()), " \t\n\"'()<>[],;=/:.@")
}

// bypassesSandbox reports whether a shell command runs outside the sandbox
// proxy. Over-reporting is safe: it only means the command gets scanned.
func (g hostGuard) bypassesSandbox(fields map[string]any) bool {
	if !g.sandboxed {
		return true
	}
	if off, _ := fields["dangerouslyDisableSandbox"].(bool); off {
		return true
	}
	cmd, _ := fields["command"].(string)
	for _, part := range splitCommand(cmd) {
		bare := stripWrappers(envPrefix.ReplaceAllString(part, ""))
		if matchesAny(part, g.excluded) || matchesAny(bare, g.excluded) {
			return true
		}
	}
	return false
}

// joinStrings writes every string value in v, so JSON escapes such as a
// unicode-escaped dot are already decoded when matched.
func joinStrings(v any, b *strings.Builder) {
	switch t := v.(type) {
	case string:
		b.WriteString(t)
		b.WriteByte('\n')
	case []any:
		for _, x := range t {
			joinStrings(x, b)
		}
	case map[string]any:
		for _, x := range t {
			joinStrings(x, b)
		}
	}
}

func denyOutput(host string) string {
	out, _ := json.Marshal(map[string]any{
		"hookSpecificOutput": map[string]string{
			"hookEventName":            "PreToolUse",
			"permissionDecision":       "deny",
			"permissionDecisionReason": "Tool input references a denied host (" + host + "); see WebFetch(domain:...) deny rules and sandbox.network.deniedDomains",
		},
	})
	return string(out)
}
