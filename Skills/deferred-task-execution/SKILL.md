---
name: deferred-task-execution
description: Delays execution of a task until a specified time or after a duration. Use when the user asks to run something later, in X minutes/hours, at a specific time, schedule a command, or defer work to a future point.
allowed-tools: [Bash, Read, TaskStop]
---

# Deferred Task Execution

Delays agent work until a user-specified time using a background timer script, then proceeds with the deferred task.

## Script Location

`~/.claude/skills/deferred-task-execution/scripts/wait-until.sh`

## Supported Input Formats

The script accepts one argument in either format:

**Duration** - relative delay from now:
- `30s`, `5m`, `1h`, `90m`, `2h30m`, `1h15m30s`

**Clock time** - specific time of day:
- `14:30`, `9:00`, `3pm`, `3:30pm`
- If the time has already passed today, it waits until that time tomorrow

## Workflow

### Step 1: Confirm the user's intent

Confirm what task to perform and when. Parse their natural language into a wait-until argument:

| User says | Argument |
|-----------|----------|
| "in 30 minutes" | `30m` |
| "in an hour" | `1h` |
| "in 2 and a half hours" | `2h30m` |
| "at 3pm" | `3pm` |
| "at 14:30" | `14:30` |
| "at half past 9" | `9:30am` |

The script self-handles timezone via the `USER_TZ` variable defined at the top of `wait-until.sh` (defaults to `Australia/Melbourne`). Clock-time arguments are interpreted in that zone regardless of host TZ. Don't ask the user about timezones unless they mention travelling.

Tell the user exactly what will happen and when the timer will fire. Ask them to confirm before starting.

### Step 2: Launch the timer in background

Run the wait script using Bash with `run_in_background: true`:

```
~/.claude/skills/deferred-task-execution/scripts/wait-until.sh <argument>
```

Note the task ID from the response -- you need it to cancel.

### Step 3: Wait for the timer

Background Bash notifies you when the script exits. Wait for that notification; don't poll.

### Step 4: Execute the deferred task

Once the output contains "Timer complete. Proceed with deferred task.", carry out whatever work the user requested.

## Important Notes

- The agent session must remain open for the timer to work. If the user closes the session, the deferred task will not execute. Warn the user about this.
- For very long waits (multiple hours), remind the user that the session needs to stay active.
- If the user asks to cancel, use `TaskStop` with the background task ID.
- Always tell the user the calculated wake time so they know when to expect the action.
