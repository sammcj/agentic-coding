Let's approach this systematically using a modified Fagan Inspection methodology:

1. **Initial Overview**: First, explain the problem/bug in plain language and what the expected vs actual behaviour is.

2. **Systematic Inspection** (Fagan-style):
   - Line-by-line walkthrough as the "Reader" role
   - Identify defects without fixing yet (pure inspection phase)
   - Check against common defect categories: logic errors, boundary conditions, error handling, data flow issues

3. **Root Cause Analysis**: After identifying issues, trace back to find the fundamental cause, not just symptoms.

4. **Solution & Verification**: Propose fixes and explicitly verify each one would resolve the identified issues.

Think aloud through each phase. If you spot assumptions, state them explicitly. If something seems unclear, flag it rather than guessing.
