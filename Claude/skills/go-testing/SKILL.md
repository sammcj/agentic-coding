---
name: writing-go-tests
description: Applies current Go testing best practices. Use when writing or modifying Go test files or advising on Go testing strategies.
# model: inherit
---

# Go Testing Best Practices

This skill provides actionable testing guidelines. For detailed implementation patterns, code examples, rationale, and production system references, consult `go-testing-best-practices.md`.

## When Working with Go Tests

**Always apply these current best practices:**

### 1. Test Organisation
- Place test files alongside source code using `*_test.go` naming
- Use internal tests (same package) for unit testing unexported functions
- Use external tests (`package foo_test`) for integration testing and examples
- Split test files by functionality when they exceed 500-800 lines (e.g., `handler_auth_test.go`, `handler_validation_test.go`)

### 2. Table-Driven Testing
- **Prefer map-based tables over slice-based** for automatic unique test names
- Use descriptive test case names that appear in failure output
- See detailed guide for complete pattern and examples

### 3. Concurrent Testing
- **Use `testing/synctest` for deterministic concurrent testing** (Go 1.24+)
- This eliminates flaky time-based tests and runs in microseconds instead of seconds
- For traditional parallel tests, always call `t.Parallel()` first in test functions

### 4. Assertions and Comparisons
- Use `cmp.Diff()` from `google/go-cmp` for complex comparisons
- Standard library is sufficient for simple tests
- Testify is the dominant third-party framework when richer assertions are needed

### 5. Mocking and Test Doubles
- **Favour integration testing with real dependencies** over heavy mocking
- Use Testcontainers for database/service integration tests
- When mocking is necessary, prefer simple function-based test doubles over code generation
- Use interface-based design ("accept interfaces, return structs")

### 6. Coverage Targets
- Aim for **70-80% coverage as a practical target**
- Focus on meaningful tests over percentage metrics
- Use `go test -cover` and `go tool cover -html` for analysis

### 7. Test Fixtures
- Use `testdata` directory for test fixtures (automatically ignored by Go toolchain)
- Implement golden file testing for validating complex output
- Use functional builder patterns for complex test data

### 8. Helpers and Cleanup
- **Always mark helper functions with `t.Helper()`** for accurate error reporting
- Use `t.Cleanup()` for resource cleanup (superior to defer in tests)

### 9. Benchmarking (Go 1.24+)
- **Use `B.Loop()` method** as the preferred pattern (prevents compiler optimisations)
- Combine with `benchstat` for statistical analysis
- Use `-benchmem` for memory profiling

### 10. Naming Conventions
- Test functions: `Test*`, `Benchmark*`, `Fuzz*`, `Example*` (capital letter after prefix)
- Use `got` and `want` for actual vs expected values
- Use descriptive test case names in table-driven tests

## Integration vs Unit Testing

- **Separate tests by environment variable** (preferred over build tags)
- See detailed guide for implementation pattern

## Additional Reference Material

**Load `go-testing-best-practices.md` when you need:**
- Complete code examples for table-driven tests, mocking patterns, golden files, helpers, or benchmarks
- Detailed explanation of testing/synctest concurrent testing patterns
- Rationale behind why specific patterns are preferred over alternatives
- Production system examples and statistics (Kubernetes, Docker, Uber, Netflix, ByteDance)
- Context on testing framework choices (Testify, GoMock, Testcontainers)
- Comprehensive coverage strategies and tooling details
- Integration testing patterns with containerisation

**The detailed guide contains full context, examples with explanations, and production-proven patterns. This SKILL.md provides the actionable rules to apply.**

## Key Principle

**Focus on meaningful tests that validate behaviour rather than implementation.** Pragmatic excellence over theoretical perfection.
