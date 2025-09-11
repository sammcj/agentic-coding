---
title: 'Perform A Full "Fagan Inspection" (Systematic Debugging) When Stuck'
read_only: true
type: 'command'
---

# Perform A Full "Fagan Inspection" (Systematic Debugging) When Stuck

This applies a modified Fagan Inspection methodology for systematic problem resolution, this is useful when facing complex problems or troubleshooting failures.

## Process

1. **Initial Overview**:

   - Explain the problem/bug in plain language
   - Clearly state the expected behaviour
   - Clearly state the actual behaviour
   - Identify any error messages or symptoms observed

2. **Systematic Inspection** (Fagan-style):

   - Perform a line-by-line walkthrough as the "Reader" role
   - Identify defects without attempting to fix them yet (pure inspection phase)
   - Check against common defect categories:
     - Logic errors (incorrect conditional logic, loop conditions)
     - Boundary conditions (off-by-one errors, edge cases)
     - Error handling (unhandled exceptions, missing validations)
     - Data flow issues (variable scope, data transformation problems)
     - Integration points (API calls, database interactions, external dependencies)

3. **Root Cause Analysis**:

   - After identifying issues, trace back to find the fundamental cause
   - Focus on the root cause, not just symptoms
   - Ask "why" (aloud, to yourself) repeatedly to get to the underlying issue
   - Consider environmental factors (configuration, dependencies, timing)
   - State any assumptions explicitly

4. **Solution & Verification**:

   - Propose specific fixes for each identified issue
   - Explicitly verify each proposed solution would resolve the identified problems
   - Consider potential side effects or unintended consequences
   - Plan verification steps or tests to confirm the fix works

## Important Guidelines

- **Think aloud** through each phase
- **State assumptions explicitly** rather than making implicit ones
- **Flag unclear aspects** rather than guessing
- **Focus on systematic analysis** over quick fixes
- **Don't skip phases** - complete each step thoroughly before moving to the next
- **Validate any flagged aspects** - after the final step, revisit any unclear points and use ultrathink to clarify them if required

Once complete: Summarise the findings, proposed solutions, and next steps clearly. Unless the user has indicated they do not want you to take action on the findings you may then proceed to implement the proposed solutions if appropriate.
