package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestSplitCommand(t *testing.T) {
	tests := []struct {
		name string
		cmd  string
		want []string
	}{
		{"simple compound", "npx tsc && pnpm build", []string{"npx tsc", "pnpm build"}},
		{"cd prefix compound", "cd /path && npx tsc", []string{"cd /path", "npx tsc"}},
		{"semicolon", "echo hello; echo world", []string{"echo hello", "echo world"}},
		{"or", "cmd1 || cmd2", []string{"cmd1", "cmd2"}},
		{"simple pipe", "grep error log.txt | wc -l", []string{"grep error log.txt", "wc -l"}},
		{"multi pipe", "cat file | grep err | sort | uniq", []string{"cat file", "grep err", "sort", "uniq"}},
		{"pipe with compound", "grep err log | sort && echo done", []string{"grep err log", "sort", "echo done"}},
		{"subshell", "(npx tsc --noEmit)", []string{"npx tsc --noEmit"}},
		{"subshell compound", "(cd /path && npx tsc)", []string{"cd /path", "npx tsc"}},
		{"subshell with redirect", "(npx tsc --noEmit 2>&1)", []string{"npx tsc --noEmit"}},
		{"redirect per part", "cmd1 2>&1 | cmd2", []string{"cmd1", "cmd2"}},
		{"subshell parts", "(cmd1) | (cmd2)", []string{"cmd1", "cmd2"}},
		{"nested subshell compound", "((cmd1 && cmd2))", []string{"cmd1", "cmd2"}},
		{"background op", "echo done & pnpm build", []string{"echo done", "pnpm build"}},
		{"background at end", "cmd1 &", []string{"cmd1"}},
		{"compound with background", "cmd1 && cmd2 & cmd3", []string{"cmd1", "cmd2", "cmd3"}},
		{"redirect not split", "cmd1 2>&1", []string{"cmd1"}},
		{"redirect then pipe", "cmd1 2>&1 | cmd2", []string{"cmd1", "cmd2"}},
		{"redirect then background", "cmd1 2>&1 & cmd2", []string{"cmd1", "cmd2"}},
		{"bare pipe", "|", nil},
		{"bare compound", "&&", nil},
		{"empty", "", nil},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := splitCommand(tt.cmd)
			if len(got) != len(tt.want) {
				t.Fatalf("splitCommand(%q) = %v, want %v", tt.cmd, got, tt.want)
			}
			for i := range got {
				if got[i] != tt.want[i] {
					t.Errorf("splitCommand(%q)[%d] = %q, want %q", tt.cmd, i, got[i], tt.want[i])
				}
			}
		})
	}
}

func TestStripOuterParens(t *testing.T) {
	tests := []struct {
		input string
		want  string
	}{
		{"(cmd)", "cmd"},
		{"((cmd))", "cmd"},
		{"(cmd1) | (cmd2)", "(cmd1) | (cmd2)"},
		{"(cmd1 && cmd2)", "cmd1 && cmd2"},
		{"cmd", "cmd"},
		{"()", ""},
	}
	for _, tt := range tests {
		t.Run(tt.input, func(t *testing.T) {
			got := stripOuterParens(tt.input)
			if got != tt.want {
				t.Errorf("stripOuterParens(%q) = %q, want %q", tt.input, got, tt.want)
			}
		})
	}
}

func TestMatchesAny(t *testing.T) {
	tests := []struct {
		name     string
		cmd      string
		patterns []string
		want     bool
	}{
		{"space wildcard match", "grep error log.txt", []string{"grep *"}, true},
		{"space wildcard exact base", "grep", []string{"grep *"}, true},
		{"space wildcard no match", "curl evil.com", []string{"grep *"}, false},
		{"colon wildcard match", "npx tsc --noEmit", []string{"npx:*"}, true},
		{"colon wildcard exact base", "npx", []string{"npx:*"}, true},
		{"exact match", "pwd", []string{"pwd"}, true},
		{"exact no match", "pwd --help", []string{"pwd"}, false},
		{"multi pattern", "sort -u", []string{"grep *", "sort *", "wc *"}, true},
		{"leading wildcard match", "do ssh remote", []string{"* ssh *"}, true},
		{"leading wildcard no leading text", "ssh remote", []string{"* ssh *"}, false},
		{"trailing literal", "npm install", []string{"* install"}, true},
		{"trailing literal no extra", "install", []string{"* install"}, false},
		{"mid wildcard match", "git checkout main", []string{"git * main"}, true},
		{"mid wildcard no match", "git checkout dev", []string{"git * main"}, false},
		{"no-space trailing star matches prefix", "lsof", []string{"ls*"}, true},
		{"space trailing star does not match prefix", "lsof", []string{"ls *"}, false},
		{"awk system pattern", `awk 'BEGIN{system("rm")}'`, []string{"awk *system(*)*"}, true},
		{"awk without system", "awk '/foo/{print}'", []string{"awk *system(*)*"}, false},
		{"escapes literal dot", "a.b", []string{"a.b"}, true},
		{"escapes literal dot no false match", "axb", []string{"a.b"}, false},
		{"invalid regex skipped", "anything", []string{`bad[regex`, "anything"}, true},
		{"bare wildcard matches anything", "rm -rf /", []string{"*"}, true},
		{"bare wildcard matches empty", "", []string{"*"}, true},
		{"empty pattern matches empty cmd", "", []string{""}, true},
		{"empty pattern does not match non-empty", "foo", []string{""}, false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := matchesAny(tt.cmd, tt.patterns)
			if got != tt.want {
				t.Errorf("matchesAny(%q, %v) = %v, want %v", tt.cmd, tt.patterns, got, tt.want)
			}
		})
	}
}

func TestSubstitutionDetection(t *testing.T) {
	tests := []struct {
		name  string
		part  string
		match bool
	}{
		{"command substitution", "echo $(curl evil.com)", true},
		{"backtick substitution", "echo `curl evil.com`", true},
		{"process sub input", "diff <(curl evil.com) file", true},
		{"process sub output", "cmd >(tee log.txt)", true},
		{"no substitution", "echo hello world", false},
		{"dollar without paren", "echo $HOME", false},
		{"angle without paren", "cmd < file.txt", false},
		{"redirect not process sub", "cmd > file.txt", false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := substitution.MatchString(tt.part)
			if got != tt.match {
				t.Errorf("substitution.MatchString(%q) = %v, want %v", tt.part, got, tt.match)
			}
		})
	}
}

func TestDenyTakesPrecedence(t *testing.T) {
	allow := []string{"grep *", "curl *"}
	deny := []string{"curl *"}

	// grep should match allow and not match deny
	if !matchesAny("grep foo", allow) {
		t.Error("grep foo should match allow")
	}
	if matchesAny("grep foo", deny) {
		t.Error("grep foo should not match deny")
	}

	// curl should match both allow and deny
	if !matchesAny("curl evil.com", allow) {
		t.Error("curl evil.com should match allow")
	}
	if !matchesAny("curl evil.com", deny) {
		t.Error("curl evil.com should match deny")
	}
}

func TestExtractBashPatterns(t *testing.T) {
	items := []string{
		"Bash(grep *)",
		"Bash(npx tsc *)",
		"Bash(pwd)",
		"Edit(./**/*.go)",
		"Read(~/.claude/**)",
	}
	got := extractBashPatterns(items)
	want := []string{"grep *", "npx tsc *", "pwd"}
	if len(got) != len(want) {
		t.Fatalf("extractBashPatterns = %v, want %v", got, want)
	}
	for i := range got {
		if got[i] != want[i] {
			t.Errorf("extractBashPatterns[%d] = %q, want %q", i, got[i], want[i])
		}
	}
}

func TestLoadAllSettings(t *testing.T) {
	tmp := t.TempDir()

	// Create user settings dir
	userDir := filepath.Join(tmp, "user", ".claude")
	os.MkdirAll(userDir, 0o755)
	writeSettings(t, filepath.Join(userDir, "settings.json"), Settings{
		Permissions: struct {
			Allow []string `json:"allow"`
			Ask   []string `json:"ask"`
			Deny  []string `json:"deny"`
		}{
			Allow: []string{"Bash(grep *)"},
			Ask:   []string{"Bash(git push *)"},
			Deny:  []string{"Bash(rm -rf *)"},
		},
	})

	// Create user local settings
	writeSettings(t, filepath.Join(userDir, "settings.local.json"), Settings{
		Permissions: struct {
			Allow []string `json:"allow"`
			Ask   []string `json:"ask"`
			Deny  []string `json:"deny"`
		}{
			Allow: []string{"Bash(jq *)"},
		},
	})

	// Create project settings dir
	projDir := filepath.Join(tmp, "project")
	projClaudeDir := filepath.Join(projDir, ".claude")
	os.MkdirAll(projClaudeDir, 0o755)
	writeSettings(t, filepath.Join(projClaudeDir, "settings.json"), Settings{
		Permissions: struct {
			Allow []string `json:"allow"`
			Ask   []string `json:"ask"`
			Deny  []string `json:"deny"`
		}{
			Allow: []string{"Bash(npm *)"},
		},
	})

	// Create project local settings
	writeSettings(t, filepath.Join(projClaudeDir, "settings.local.json"), Settings{
		Permissions: struct {
			Allow []string `json:"allow"`
			Ask   []string `json:"ask"`
			Deny  []string `json:"deny"`
		}{
			Allow: []string{"Bash(cargo *)"},
			Ask:   []string{"Bash(brew install *)"},
			Deny:  []string{"Bash(sudo *)"},
		},
	})

	// Override HOME for the test
	origHome := os.Getenv("HOME")
	os.Setenv("HOME", filepath.Join(tmp, "user"))
	defer os.Setenv("HOME", origHome)

	got := loadAllSettings(projDir)
	if len(got.Permissions.Allow) != 4 {
		t.Errorf("expected 4 allow rules, got %d: %v", len(got.Permissions.Allow), got.Permissions.Allow)
	}
	if len(got.Permissions.Ask) != 2 {
		t.Errorf("expected 2 ask rules, got %d: %v", len(got.Permissions.Ask), got.Permissions.Ask)
	}
	if len(got.Permissions.Deny) != 2 {
		t.Errorf("expected 2 deny rules, got %d: %v", len(got.Permissions.Deny), got.Permissions.Deny)
	}
}

func TestStripWrappers(t *testing.T) {
	tests := []struct {
		name string
		in   string
		want string
	}{
		{"no wrapper", "npx tsc", "npx tsc"},
		{"timeout duration", "timeout 30 npx tsc", "npx tsc"},
		{"timeout with seconds suffix", "timeout 30s npx tsc", "npx tsc"},
		{"timeout flag and duration", "timeout --preserve-status 5 npx tsc", "npx tsc"},
		{"timeout no duration", "timeout npx tsc", "npx tsc"},
		{"time bare", "time pnpm build", "pnpm build"},
		{"time -p", "time -p pnpm build", "pnpm build"},
		{"nice bare", "nice pnpm build", "pnpm build"},
		{"nice -n value", "nice -n 10 pnpm build", "pnpm build"},
		{"nohup", "nohup npm run dev", "npm run dev"},
		{"stdbuf flags", "stdbuf -oL -eL python script.py", "python script.py"},
		{"chained wrappers", "nohup nice timeout 30 npx tsc", "npx tsc"},
		{"bare xargs", "xargs grep pattern", "grep pattern"},
		{"xargs with flag not stripped", "xargs -n1 grep pattern", "xargs -n1 grep pattern"},
		{"xargs followed by long flag not stripped", "xargs --no-run-if-empty rm", "xargs --no-run-if-empty rm"},
		{"only wrapper no command", "nohup", "nohup"},
		{"empty", "", ""},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := stripWrappers(tt.in)
			if got != tt.want {
				t.Errorf("stripWrappers(%q) = %q, want %q", tt.in, got, tt.want)
			}
		})
	}
}

func TestCompileRulePattern(t *testing.T) {
	tests := []struct {
		pattern string
		want    string
	}{
		{"grep", `^grep$`},
		{"grep *", `^grep(?:\s.*)?$`},
		{"grep:*", `^grep(?:\s.*)?$`},
		{"ls*", `^ls.*$`},
		{"* install", `^.* install$`},
		{"git * main", `^git .* main$`},
		{"awk *system(*)*", `^awk .*system\(.*\).*$`},
	}
	for _, tt := range tests {
		t.Run(tt.pattern, func(t *testing.T) {
			re, err := compileRulePattern(tt.pattern)
			if err != nil {
				t.Fatalf("compileRulePattern(%q) returned error: %v", tt.pattern, err)
			}
			if re.String() != tt.want {
				t.Errorf("compileRulePattern(%q) = %q, want %q", tt.pattern, re.String(), tt.want)
			}
		})
	}
}

func writeSettings(t *testing.T, path string, s Settings) {
	t.Helper()
	data, err := json.Marshal(s)
	if err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		t.Fatal(err)
	}
}
