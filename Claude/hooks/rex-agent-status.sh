#!/bin/sh
# Report Claude Code's state to Rex tabs with OSC 7501 (Rex's program status protocol).
# Claude Code's terminalSequence output only allows OSC 0/1/2/9/99/777, and hooks have no
# controlling terminal, so write to the tty of the nearest ancestor that has one (claude).
[ -n "${REX_BLOCK:-}" ] || exit 0
# Hook stdout can reach the model as context; this hook never adds any.
exec >/dev/null 2>&1
command -v jq >/dev/null || exit 0

# "|" rather than tab: read collapses runs of whitespace IFS, dropping empty fields.
fields=$(jq -r '[.hook_event_name, .agent_id, .notification_type, .tool_name] | map(. // "") | join("|")') || exit 0
IFS="|" read -r event agent ntype tool <<EOF
$fields
EOF

# Known gaps the hook events can't close: Esc fires no event, so "working" stays until the
# next prompt; a parallel tool's PostToolUse can overwrite "blocked" while a prompt is open.
case "$event" in
  # Subagent working/done events would revive "working" after the main turn has stopped.
  UserPromptSubmit | PostToolUse | PostToolUseFailure) [ -z "$agent" ] && report="state=working" ;;
  # allow-skills-edit.sh auto-approves many edits; the permission_prompt notification
  # still covers edits that really wait on the user.
  PermissionRequest)
    case "$tool" in Edit | Write) ;; *) report="state=blocked:kind=permission" ;; esac ;;
  PreToolUse) [ "$tool" = AskUserQuestion ] && report="state=blocked:kind=question" ;;
  Notification)
    case "$ntype" in
      permission_prompt) report="state=blocked:kind=permission" ;;
      elicitation_dialog | elicitation_url_dialog) report="state=blocked:kind=question" ;;
    esac ;;
  Stop) [ -z "$agent" ] && report="state=done" ;;
  StopFailure) report="state=error" ;;
  SessionEnd) report="state=clear" ;;
esac
[ -n "${report:-}" ] || exit 0

pid=$PPID
while [ "${pid:-1}" -gt 1 ]; do
  tty=$(ps -o tty= -p "$pid" | tr -d ' ')
  case "$tty" in '' | '??') ;; *) break ;; esac
  pid=$(ps -o ppid= -p "$pid" | tr -d ' ')
done
case "${tty:-??}" in '??') exit 0 ;; esac

printf '\033]7501;%s:app=claude-code\033\134' "$report" >"/dev/$tty"
exit 0
