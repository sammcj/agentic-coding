# Self-Improving Cline Reflection

**Objective:** Offer opportunities to continuously improve `.clinerules` based on user interactions and feedback.

**Trigger:** Before using the `attempt_completion` tool for any task that involved user feedback provided at any point during the conversation, or involved multiple non-trivial steps (e.g., multiple file edits, complex logic generation).

For clarity, 'multiple non-trivial steps' could include (but is not limited to) scenarios such as:

- Creating a new code file containing a new class or multiple functions (e.g., >30 lines of new logic).
- Modifying 2 or more existing distinct code files (i.e., not just memory bank or configuration file updates).
- Implementing a new API endpoint or a significant new feature within an existing one.
- Making substantial content changes (beyond simple status updates like ticking a checkbox) to 3 or more memory bank files as part of the task's primary work. \* Successfully executing a sequence of 3 or more distinct tool uses (e.g., `read_file` -> `write_to_file` -> `execute_command`) to achieve a task objective.

**Process:**

1. **Offer Reflection:** Ask the user: "Before I complete the task, would you like me to reflect on our interaction and suggest potential improvements to the active `.clinerules`?"
2. **Await User Confirmation:** Proceed to `attempt_completion` immediately if the user declines or doesn't respond affirmatively.
3. **If User Confirms:**
    a. **Review Interaction:** Synthesize all feedback provided by the user throughout the entire conversation history for the task. Analyze how this feedback relates to the active `.clinerules` and identify areas where modified instructions could have improved the outcome or better aligned with user preferences.
    b. **Identify Active Rules:** List the specific global and workspace `.clinerules` files active during the task.
    c. **Formulate & Propose Improvements:** Generate specific, actionable suggestions for improving the _content_ of the relevant active rule files. Prioritize suggestions directly addressing user feedback. Use `replace_in_file` diff blocks when practical, otherwise describe changes clearly.
    d. **Await User Action on Suggestions:** Ask the user if they agree with the proposed improvements and if they'd like me to apply them _now_ using the appropriate tool (`replace_in_file` or `write_to_file`). Apply changes if approved, then proceed to `attempt_completion`.

**Constraint:** Do not offer reflection if:

- No `.clinerules` were active.
- The task was very simple and involved no feedback.
