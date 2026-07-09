---
name: tmux-cli
description: CLI utility to help when running ongoing interactive CLI sessions or using tmux to communicate with other CLI Agents; use when you are asked to connect to remote machines via ssh or need to use interactive CLI tools that require ongoing input.
---

# tmux-cli

## Instructions

- Use the `tmux-cli` command to communicate with other CLI Agents or Scripts in other tmux panes. Do `tmux-cli --help` to see how to use it!
  - This command depends on installing the `claude-code-tools`. If you get an error indicating that the command is not available, ask the user to install it using: `uv tool install claude-code-tools`.
  - When using tmux-cli to connect to remote machines you must run it outside the sandbox (the tmux socket is outside the sandbox's allowed paths, and the pane's `ssh` needs the environment's SSH auth). A sandboxed `capture` returns empty. Allow-list `tmux-cli` once to avoid repeated approval prompts.
- When you are finished with all tasks that you need tmux-cli for clean up the session.

## Remote SSH hosts (default pattern)

When you need to run more than one command on a remote host over SSH, do NOT issue repeated one-off `ssh host 'cmd'` calls - each re-authenticates and needs its own approval. Open ONE persistent session and drive it. This is the default for any multi-command remote work.

1. Reuse an existing session rather than spawning a new one each task (windows accumulate otherwise): check `tmux-cli status` / `tmux-cli list_panes`, reuse its pane if healthy, and only `tmux-cli launch "zsh"` if none exists. Note the returned pane id.
2. Arm auto-cleanup on the pane BEFORE connecting, so nothing lingers if the task is abandoned:
   - Idle timeout: `export TMOUT=1800` in the launched zsh (self-exits after 30 min idle at a prompt).
   - Hard cap watchdog (zsh): `( sleep 5400 && tmux kill-session -t remote-cli-session ) &!` - kills the whole session after 90 min regardless of activity. tmux-cli's remote session is named `remote-cli-session` on the default socket, so raw `tmux` can target it. `&!` backgrounds and disowns so it survives the shell exiting.
3. Connect with keepalive so a dropped link tears itself down: `ssh -o ServerAliveInterval=60 -o ServerAliveCountMax=3 -o StrictHostKeyChecking=no user@host`.
4. After connecting, set the same idle timeout on the remote shell (busybox `ash` and `bash` both honour it): `export TMOUT=1800`.
5. Run work with `send` + `wait_idle` + `capture`. Only the pane's `ssh` uses the network / SSH auth; tmux-cli itself only talks to the local tmux socket.
6. Tear it down explicitly when done: `tmux-cli cleanup` kills the managed session; `tmux-cli kill --pane=<id>` kills a single pane. Do not leave idle sessions behind - the timeouts above are a backstop, not a substitute for cleanup.

## Key Commands

### Execute with Exit Code Detection

Use `tmux-cli execute` when you need to know if a shell command succeeded or failed:

```bash
tmux-cli execute "make test" --pane=2
# Returns JSON: {"output": "...", "exit_code": 0}

tmux-cli execute "npm install" --pane=ops:1.3 --timeout=60
# Returns exit_code=0 on success, non-zero on failure, -1 on timeout
```

This is useful for:

- Running builds and knowing if they passed
- Running tests and detecting pass/fail
- Multi-step automation that should abort on failure

**Note**: `execute` is for shell commands only, not for agent-to-agent chat.

## Tips

- For communicating with another Claude Code instance, use `send` + `wait_idle` + `capture` instead.
- To wait for a condition, use Monitor with an until-loop (e.g. `until <check>; do sleep 2; done`), to wait for a command you started, use `run_in_background: true`.

