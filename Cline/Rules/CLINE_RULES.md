# Important Guidelines and Rules

## LANGUAGE & COMMUNICATION

<SPELLING_AND_LOCALISATION note="IMPORTANT">
  <IMPORTANT note="This is VERY important">**CRITICAL: YOU MUST ALWAYS USE INTERNATIONAL / AUSTRALIAN ENGLISH SPELLING FOR ALL RESPONSES, DOCUMENTATION, COMMENTS, DEFINITIONS AND FUNCTION NAMES. DO NOT USE AMERICAN SPELLING.**</IMPORTANT>
  <AUSTRALIAN_ENGLISH_RULES>
    - ALWAYS ensure consistent use of Australian English in all your interactions, ***AUSTRALIAN ENGLISH SPELLING MUST BE USED IN ALL WRITING!***
    - Look out for Z's when there should be S's
    - Using American spelling makes users sad, confused, frustrated and disappointed in your performance
    <KEY_PATTERNS>
        You must follow these Australian English spelling and usage rules during all your task, e.g:
        1. Use -our instead of -or (colour, favour, behaviour)
        2. Use -ise/-yse instead of -ize/-yze (organise, analyse, optimise)
        3. Use -re instead of -er (centre, metre, theatre)
        4. Use -ogue instead of -og (catalogue, dialogue, analogue)
        5. Use -ae/-oe instead of -e (anaemia, oesophagus)
        6. Use -ll- instead of -l- (travelled, cancelled, modelling)
        7. Use -t instead of -ed for certain past tense (learnt, dreamt, spelt)
        8. Use -ence instead of -ense for nouns (defence, licence, offence)
        9. Use British vocabulary (mum, aeroplane, autumn, lift, boot)
    </KEY_PATTERNS>
  </AUSTRALIAN_ENGLISH_RULES>
  <FINAL_CHECK>
    Before completing a task, verify: Did I use Australian English spellings?
  </FINAL_CHECK>
</SPELLING_AND_LOCALISATION>

<WRITING_STYLE note="IMPORTANT">
  <AVOID_AI_CLICHES>
    - **You must NEVER use overused AI phrases especially those that are not quantifiable or measurable such as: comprehensive , robust , best-in-class , feature-rich , production-ready , enterprise-grade**
    - NEVER write with smart quotes or em dashes
    - Avoid excessive bullet points with bolded headers
    - No transition phrases between every paragraph
    - No unnecessary summary paragraphs
    - Do not write content that could be interpreted as marketing or hype and do not use overly enthusiastic or self-congratulatory language
  </AVOID_AI_CLICHES>

  <WRITE_NATURALLY>
    - Write as if you're a knowledgeable engineer explaining to a colleague, do not write someone selling a product
    - Be direct, concise and specific, not vague and grandiose
    - Use active voice and concrete examples
    - If a sentence adds no value, delete it!
  </WRITE_NATURALLY>

  <FINAL_CHECK>
    When writing documentation does it sound like a real person explaining something they know, or Wikipedia crossed with a press release? Natural writing is messier, more varied, more specific than AI defaults.
  </FINAL_CHECK>
</WRITING_STYLE>

<DOCUMENTATION_STANDARDS>
  <TECHNICAL_DOCS>
    - Start with what it does, not why it's amazing
    - Configuration and examples over feature lists
    - "Setup" not "🚀 Getting Started"
    - "Exports to PDF" not "Seamlessly transforms content"
    - Include concrete examples for every major feature
    - Document the "why" only for non-obvious decisions
    - Aim to keep README files under 500 lines
    - **You must **NOT** create new markdown documentation files (implementation notes, usage guides, troubleshooting docs, changelogs, etc. other than a development plan document if you're working from one) unless explicitly requested - update existing README.md instead (if you need to) or keep notes in conversation.**
  </TECHNICAL_DOCS>

  <CODE_COMMENTS>
    - Only comment complex logic that cannot be inferred
    - Never add process comments ("improved", "fixed", "enhanced")
    - Explain "why" not "what" for business logic
    - Use function/variable names that eliminate need for comments
  </CODE_COMMENTS>
</DOCUMENTATION_STANDARDS>

---

## ARCHITECTURE & DESIGN

<CORE_DESIGN_PRINCIPLES>
  <SIMPLICITY_FIRST>
    - **CRITICAL**: Favour elegance through simplicity - "less is more"
    - Start with working MVP, iterate improvements
    - Avoid premature optimisation and over-engineering
    - Use abstraction only when pattern repeats 3+ times
    - Each iteration should be functional and tested
  </SIMPLICITY_FIRST>

  <SOLID_PRINCIPLES>
    - Single Responsibility: One reason to change
    - Open/Closed: Extend without modifying
    - Liskov Substitution: Subtypes must be substitutable
    - Interface Segregation: Many specific interfaces
    - Dependency Inversion: Depend on abstractions
  </SOLID_PRINCIPLES>

  <DESIGN_PATTERNS>
    - Repository pattern for data access
    - Dependency injection for testability
    - Circuit breaker for external services
    - Strategy pattern for swappable algorithms
    - Observer pattern for event systems
    - Factory pattern for complex object creation
    - When creating a project greenfields provide a single Makefile entrypoint to lint, test, version, build and run the application
  </DESIGN_PATTERNS>
</CORE_DESIGN_PRINCIPLES>

<CODE_QUALITY_METRICS>
- Functions: Max 50 lines (split if larger)
- Files: Max 700 lines (split if larger)
- Cyclomatic complexity: Under 10
- Test execution: Test run quickly (a few seconds ideally) and do not rely on external services
- Build time: Optimise if over 1 minute
- Code coverage: 80% minimum for new code
</CODE_QUALITY_METRICS>

<CONFIGURATION_MANAGEMENT>
- ALWAYS use .env or config files as single source of truth
- Never commit .env files (use .gitignore)
- Provide .env.example with all required variables
- Validate environment variables on startup
- Use structured config objects, not scattered process.env
- Group related configuration together
- Use sensible defaults where appropriate
</CONFIGURATION_MANAGEMENT>

---

## TESTING & QUALITY ASSURANCE

<SOFTWARE_TESTING_PRACTICES>
  <TESTING_WORKFLOW>
    1. Write failing test for bugs (test-first)
    2. Fix the bug
    3. Verify test passes
    4. Run test suite
    5. Check no other tests broken
    6. Only then declare fixed
  </TESTING_WORKFLOW>

  <TEST_STANDARDS>
    - Descriptive test names explaining what and why
    - Arrange-Act-Assert pattern
    - One assertion per test where practical
    - Use table-driven tests for multiple cases
    - Mock external dependencies where appropriate
    - Test edge cases and error paths
    - Group all tests in a common location (e.g. `test/` or `tests/`)
  </TEST_STANDARDS>
</SOFTWARE_TESTING_PRACTICES>

<VERIFICATION_CHECKLIST>
Before declaring any task complete:
- [ ] Code builds without warnings
- [ ] Linting passes with no warnings or errors
- [ ] All tests pass (new and existing)
- [ ] No debug statements or console.log remain
- [ ] Error cases and logging handled appropriately
- [ ] Documentation updated if needed
- [ ] Performance impact considered
- [ ] Security implications reviewed
</VERIFICATION_CHECKLIST>

---

## SECURITY & ERROR HANDLING

<SECURITY_STANDARDS>
  <CRITICAL_SECURITY>
    - NEVER hardcode credentials, tokens, or secrets
    - NEVER commit sensitive data
    - NEVER trust user input - always validate
    - NEVER use string concatenation for SQL
    - NEVER expose internal errors to users
  </CRITICAL_SECURITY>

  <SECURITY_PRACTICES>
    - Validate and sanitise all inputs
    - Use parameterised queries/prepared statements
    - Implement rate limiting for APIs
    - Follow principle of least privilege
    - Hash passwords with bcrypt/scrypt/argon2
    - Use HTTPS/TLS for data transmission
    - Keep dependencies updated
    - Scan for known vulnerabilities
  </SECURITY_PRACTICES>
</SECURITY_STANDARDS>

<ERROR_HANDLING>
  <ERROR_STRATEGY>
    - Return meaningful errors for developers
    - Return safe errors for end users
    - Log errors with context and stack traces
    - Make use of error boundaries where applicable
    - Implement retry logic with exponential backoff
    - Graceful degradation over complete failure
    - Never expose system internals in errors
  </ERROR_STRATEGY>

  <LOGGING_STANDARDS>
    - Use structured logging (JSON)
    - Include correlation IDs for tracing
    - Log levels: ERROR, WARN, INFO, DEBUG
    - Never log sensitive data (passwords, tokens)
    - Include timestamp, service, and context
    - Avoid excessive logging in production
  </LOGGING_STANDARDS>
</ERROR_HANDLING>

---

## LANGUAGE-SPECIFIC RULES

<GOLANG>
  <GO_STANDARDS>
    - Use latest Go version (verify, don't assume)
    - Use os and io packages (not deprecated ioutil)
    - Always handle errors explicitly
    - Use context for cancellation and timeouts
    - Build with -ldflags="-s -w" for smaller binaries
    - Check go code modernity with `go run golang.org/x/tools/gopls/internal/analysis/modernize/cmd/modernize@latest -fix -test ./...`
    - When configuring golangci copy $HOME/git/sammcj/mcp-devtools/.golangci.yml to the project
    - Use table-driven tests
    - Follow standard project layout
    - Use go mod for dependencies
  </GO_STANDARDS>

  <GO_PATTERNS>
    - Return early for error conditions
    - Prefer composition over inheritance
    - Use interfaces for abstraction
    - Keep interfaces small
    - Use defer for cleanup
  </GO_PATTERNS>
</GOLANG>

<JAVASCRIPT_TYPESCRIPT>
  <TS_STANDARDS>
    - Prefer TypeScript over JavaScript
    - Use strict mode always
    - Prefer type inference where obvious
    - Use discriminated unions over enums
    - Avoid `any`, use `unknown` for truly unknown
    - Use `readonly` for immutable properties
    - Leverage utility types (Partial, Pick, Omit)
  </TS_STANDARDS>

  <JS_TS_PRACTICES>
    - Use const by default, let when needed, never var
    - Destructuring over property access
    - Template literals over string concatenation
    - Arrow functions for callbacks
    - Async/await over promises chains
    - Optional chaining (?.) and nullish coalescing (??)
    - Never hardcode styles - use theme/config
  </JS_TS_PRACTICES>
</JAVASCRIPT_TYPESCRIPT>

<PYTHON>
  <PYTHON_STANDARDS>
    - Use Python 3.10+ features
    - Type hints for all functions
    - Use dataclasses for data structures
    - Follow PEP 8 style guide
    - Use pathlib over os.path
    - Use f-strings for formatting
    - Virtual environments for dependencies
  </PYTHON_STANDARDS>
</PYTHON>

<BASH>
  <SHELL_STANDARDS>
    - Use `#!/usr/bin/env bash` shebang
    - Set strict mode: `set -euo pipefail`
    - Define variables separately from assignment
    - Quote all variable expansions
    - Use `[[ ]]` over `[ ]` for conditionals
    - Handle errors with trap
    - Use functions for repeated code
  </SHELL_STANDARDS>
</BASH>

---

## Tool Usage

<TOOL_PRIORITIES note="**IMPORTANT**">
- Use purpose-built tools over manual approaches.
- Prioritise using specific tools is often a better approach than searching the web (e.g. using get_library_docs for library documentation)
- Use tools to reduce token usage
- Search documentation before making assumptions
- If you stuck don't just keep making things up - use the tools available to you to lookup package documentation or search the web
- When asked to do math that's more than adding one or two items, use the calculator tool to ensure accuracy
- If you're exploring a large codebase or potentially very large files, use of the 'code_skim' tool (if you have it) to quickly understand the structure of the file(s) without all the implementation details
- Remember can delegate tasks to a sub-agents with instructions to use specific tools and provide you with only the key information you're looking for to reduce token usage and optionally speed up the process further by doing this in parallel where it makes sense to do so
</TOOL_PRIORITIES>



---

## Diagramming Rules

<MERMAID_RULES>
    -  IMPORTANT: You MUST NOT use round brackets ( ) within item labels or descriptions
    -  Use <br> instead of \n for line breaks
    -  Apply standard colour theme unless specified otherwise
    -  Mermaid does not support unordered lists within item labels
  <STANDARD_THEME>
    classDef inputOutput fill:#F5F5F5,stroke:#9E9E9E,color:#616161
    classDef llm fill:#E8EAF6,stroke:#7986CB,color:#3F51B5
    classDef components fill:#F3E5F5,stroke:#BA68C8,color:#8E24AA
    classDef process fill:#E0F2F1,stroke:#4DB6AC,color:#00897B
    classDef stop fill:#FFEBEE,stroke:#E57373,color:#D32F2F
    classDef data fill:#E3F2FD,stroke:#64B5F6,color:#1976D2
    classDef decision fill:#FFF3E0,stroke:#FFB74D,color:#F57C00
    classDef storage fill:#F1F8E9,stroke:#9CCC65,color:#689F38
    classDef api fill:#FFF9C4,stroke:#FDD835,color:#F9A825
    classDef error fill:#FFCDD2,stroke:#EF5350,color:#C62828
  </STANDARD_THEME>
</MERMAID_RULES>

---

## Contributing Style

<CONTRIBUTING_TO_OPEN_SOURCE when="If the user states they are contributing to an open source project">
- You MUST align to the style of the existing code and you MUST follow the project's contribution guidelines and coding standards, start by reading CONTRIBUTING.md or similar files in the repository
- Be precise in your changes and match existing conventions
- **IMPORTANT: You MUST NOT add placeholder comments or code!**
</CONTRIBUTING_TO_OPEN_SOURCE>

---

## General Rules & Guidelines

<NEVER_DO_THESE note="**IMPORTANT**">
- NEVER perform git add/commit/push operations
- NEVER hardcode credentials, unique identifiers or localhost URLs
- NEVER attempt to estimate time required for tasks (e.g. do not add "this will take about 2 hours", "Phase 3: Weeks 2-3" etc...)
- NEVER add comments pertaining only to development process (e.g. "improved function", "optimised version", "# FIX:", "enhanced function" etc...)
- NEVER claim an issue is resolved until user verification - This is very important, you *MUST* confirm an issue truly is fixed before stating it is fixed!
- NEVER implement placeholder or mocked functionality unless explicitly instructed - don't be lazy!
- NEVER build or develop for Windows - we do not ever need or want Windows support
</NEVER_DO_THESE>

<VERBOSE_THINKING_CONCISE_OUTPUT>
- Be verbose when you are thinking to help explore the problem space but be succinct and concise (don't waste tokens) in your general communication and code changes
- Combine multiple, file edits to the same file where possible
</VERBOSE_THINKING_CONCISE_OUTPUT>

<REMINDER note="**IMPORTANT** you must follow these reminders for all tasks unless directly instructed otherwise by the user">
- IMPORTANT: Edit only what's necessary! Make minimal changes to existing structures unless instructed
- **You MUST NOT EVER state something is fixed unless you have confirmed it is by means of testing or measuring output and building the application**
- Run make lint/format/test/build if available after completing tasks
- If working from a dev plan or checklist - you **MUST** check off tasks as they are completed to 100%, if you cannot be sure they are truly complete - do not state they are complete!
- If you are stuck on a persistent problem that you and the user have tried to fix several times use the performing-systematic-debugging-for-stubborn-problems skill if you have it available (if you don't: perform a fagan inspection to systematically identify and resolve the root cause of the problem)
- Create a todo lists when working on complex tasks to track progress and remain on track
- You **MUST** fix all failing tests before marking task complete
- If the user asks you to ensure the code builds you **MUST** ensure you run a build or any other related commands before stating you've completed the work.
</REMINDER>
