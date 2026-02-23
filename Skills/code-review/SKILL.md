---
name: code-review
description: Use this skill after completing multiple, complex software development tasks before informing the user that work is complete.
---

# Guidelines For Performing Code Reviews After Completing Multiple Complex Software Development Tasks

1. Spawn parallel sub-agents with tasks to perform a critical self-review of the changes you've made.
2. Compile findings into a concise numbered list with severity (critical/medium/low)
3. Verify each finding against actual code (no false positives)
4. Implement all fixes and run the appropriate lint/test/build pipeline

If you get stuck on any especially complex or recurring issue consider using the systematic debugging skill to investigate further and unblock yourself.

## Sub Agent Guidelines

- Instruct sub-agents to keep outputs concise, token-efficient, relevant and actionable focused on your changes and not to nitpick on minor style issues.
- Provide concise relevant context to the sub-agents to help them understand the context of the changes they are reviewing but avoid wasting lots of tokens on context they can infer from the code itself.
- Appropriately scope the review to your changes with clear boundaries.
