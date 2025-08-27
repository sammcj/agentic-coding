## Go Modernisation Rules for AI Coding Agents

CRITICAL: Follow these rules when writing Go code to avoid outdated patterns that `modernize` would flag:

### Types and Interfaces
- Use `any` instead of `interface{}`
- Use `comparable` for type constraints when appropriate

### String Operations
- Use `strings.CutPrefix(s, prefix)` instead of `if strings.HasPrefix(s, prefix) { s = strings.TrimPrefix(s, prefix) }`
- Use `strings.SplitSeq()` and `strings.FieldsSeq()` in range loops instead of `strings.Split()` and `strings.Fields()`

### Loops and Control Flow
- Use `for range n` instead of `for i := 0; i < n; i++` when index isn't used
- Use `min(a, b)` and `max(a, b)` instead of if/else conditionals

### Slices and Maps
- Use `slices.Contains(slice, element)` instead of manual loops for searching
- Use `slices.Sort(s)` instead of `sort.Slice(s, func(i, j int) bool { return s[i] < s[j] })`
- Use `maps.Copy(dst, src)` instead of manual `for k, v := range src { dst[k] = v }` loops

### Testing
- Use `t.Context()` instead of `context.WithCancel()` in tests

### Formatting
- Use `fmt.Appendf(nil, format, args...)` instead of `[]byte(fmt.Sprintf(format, args...))`

### Build without debug symbols
- Use `go build -ldflags="-s -w"` to reduce binary size
