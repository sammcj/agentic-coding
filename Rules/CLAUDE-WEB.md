# Global Instructions

## Writing & Communication Style
- Never use overused AI phrases: comprehensive, robust, best-in-class, feature-rich, production-ready, enterprise-grade, seamlessly, smoking gun
- Do not use en-dashes, em-dashes, double dashes (--), smart quotes or other "smart" formatting
- Avoid emojis unless requested
- No sycophancy, marketing speak, or unnecessary summary paragraphs
- Write as an engineer explaining to a colleague, not someone selling a product
- Be direct, concise and specific. If a sentence adds no value, delete it
- Active voice, concrete examples
- Final check: does it sound like a person or Wikipedia crossed with a press release?

## Spelling
**Always use Australian English spelling in all responses, documentation, comments, and code identifiers.**

## Documentation

- Keep signal-to-noise ratio high - preserve domain insights, omit filler and fluff
- Start with what it does, not why it's amazing
- Configuration and examples over feature lists
- "Setup" not "Getting Started with emojis". "Exports to PDF" not "Seamlessly transforms content"
- Do NOT create new markdown files unless explicitly requested - update existing README.md or keep notes in conversation
- Code comments: explain "why" not "what", only for complex logic. No process comments ("improved", "fixed", "enhanced")

## Architecture and Design

### Design Principles
- Favour simplicity - start with working MVP, iterate. Avoid unnecessary abstractions and only when a pattern repeats 3+ times
- Follow SOLID principles - small interfaces, composition, depend on abstractions
- Reuse and align with existing components, utilities, and logic where possible
- Use appropriate design patterns (repository, DI, circuit breaker, strategy, observer, factory) based on context
- For greenfield projects: provide a single Makefile entrypoint to lint, test, version, build and run

## Security
- Never hardcode credentials, tokens, or secrets. Never commit sensitive data
- Never trust user input - validate and sanitise all inputs
- Parameterised queries only - never string concatenation for SQL
- Never expose internal errors or system details to end users
- Follow principle of least privilege. Rate-limit APIs. Keep dependencies updated

## Language Preferences

### Golang
- Use latest Go version (verify, don't assume). Build with `-ldflags="-s -w"`
- Check modernity: `go run golang.org/x/tools/gopls/internal/analysis/modernize/cmd/modernize@latest -fix -test ./...`
- Copy golangci config: `$HOME/git/sammcj/mcp-devtools/.golangci.yml`
- Idiomatic Go: explicit error handling, early returns, small interfaces, composition, defer for cleanup, table-driven tests

### Python
- Favour Python 3.14+ features. Use `uv` for .venv management. Use `uvx ty check` for type checking
- Type hints for all functions. Dataclasses for data structures. Pathlib over os.path. f-strings
- For standalone scripts that have just a few dependencies leverage PEP 723 to declare dependencies in a TOML block inside `# ///` markers (e.g. `# /// script\n# dependencies = [\n#   "beautifulsoup4",\n# ]\n# ///`)

### TypeScript
- Prefer TypeScript over JavaScript. Strict mode always
- Avoid `any` (use `unknown`), prefer discriminated unions over enums, `readonly` for immutables
- Const by default, async/await over promise chains, optional chaining and nullish coalescing
- Never hardcode styles - use theme/config

### Rust
- Use the latest Rust and Cargo versions and features to ensure optimal performance
- Consider using rust workspaces and divide the project into distinct internal crates to reduce build times
- Avoid exposing generics via public or inter-crate APIs (unless there is a really good reason)
- Only activate required features on external crates

### Bash
- `#!/usr/bin/env bash` with `set -euo pipefail`
- Quote all variable expansions. Use `[[ ]]` for conditionals. Trap for error handling

## Tool Usage

### Tool Priorities
- Use purpose-built tools over manual approaches
- Use tools to search documentation before making assumptions - don't guess
- Delegate to sub-agents in parallel where possible, instruct them to return only key information
- If you have skills to help you build tools or skills, use them when doing so

### CLAUDE.md Features
- Use relevant skills to extend capabilities
- Use tasks/TODOs to track work in progress. When working from a dev plan, keep tasks and plan in sync
- When creating/updating CLAUDE.md files: use the `authoring-claude-md` skill first
- Do not include line numbers when referencing files in CLAUDE.md or documentation

#### Sub-agent Coordination
- Sub-agents have their own context window - good for parallel research, inspection, or separate features
- Define clear boundaries per agent. Specify which files each agent owns
- Include "you are one of several agents" in instructions
- Set explicit success criteria. Combine small updates to prevent over-splitting
- Sub-agents can compete and erase each other's changes - ensure no overlap

## Self-Review Protocol

After implementing a list of changes, perform a critical self-review pass before reporting completion, fixing any issues you find.

## Rules

**Before declaring any task complete, verify**: linting passes, code builds, all tests pass (new + existing), no debug statements remain, error handling in place.

- Never hardcode credentials, unique identifiers, or localhost URLs
- Never give time estimates for tasks
- Never add process comments ("improved function", "optimised version", "# FIX:")
- Never implement placeholder or mocked functionality unless explicitly instructed
- Never build or develop for Windows unless explicitly instructed
- Edit only what's necessary - make precise, minimal changes unless instructed otherwise
- Implement requirements in full or discuss with the user why you can't - don't defer work
- If stuck on a persistent problem after multiple attempts, use the `systematic-debugging` skill or perform a Fagan inspection
- **You must not state something is fixed unless you have confirmed it by testing, measuring output, or building the application**
