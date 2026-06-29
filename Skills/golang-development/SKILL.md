---
name: golang-development
description: You MUST activate this skill when working on Go projects
---

# Go

- Use latest Go version (verify, don't assume). Build with `-ldflags="-s -w"`
- Check modernity: `go run golang.org/x/tools/gopls/internal/analysis/modernize/cmd/modernize@latest -fix -test ./...`
- Copy golangci config: `$HOME/git/sammcj/mcp-devtools/.golangci.yml`
- Idiomatic Go: explicit error handling, early returns, small interfaces, composition, defer for cleanup, table-driven tests

## Go Testing

- When working with tests in Go, read in `references/go-testing.md` for actionable testing guidelines.
