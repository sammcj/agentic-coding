#!/usr/bin/env bash
set -euo pipefail

# Waits for a specified duration or until a target clock time, then exits.
# Used by the deferred-task-execution skill to delay agent actions.
#
# Usage:
#   wait-until.sh <duration|time>
#
# Duration formats:
#   30s, 5m, 1h, 2h30m, 90m, 1h15m30s
#
# Clock time formats:
#   14:30, 3pm, 3:30pm, 15:00
#   If the time has already passed today, waits until that time tomorrow.

die() {
  echo "Error: ${1}" >&2
  exit 1
}

[[ $# -ge 1 ]] || die "Usage: wait-until.sh <duration|time>"

input="${1}"

parse_duration_to_seconds() {
  local input="${1}"
  local total=0
  local remaining="${input}"

  # Match patterns like 2h30m15s, 5m, 1h, 30s, 90m
  while [[ -n "${remaining}" ]]; do
    if [[ "${remaining}" =~ ^([0-9]+)h(.*)$ ]]; then
      local val="${BASH_REMATCH[1]}"
      total=$(( total + val * 3600 ))
      remaining="${BASH_REMATCH[2]}"
    elif [[ "${remaining}" =~ ^([0-9]+)m(.*)$ ]]; then
      local val="${BASH_REMATCH[1]}"
      total=$(( total + val * 60 ))
      remaining="${BASH_REMATCH[2]}"
    elif [[ "${remaining}" =~ ^([0-9]+)s(.*)$ ]]; then
      local val="${BASH_REMATCH[1]}"
      total=$(( total + val ))
      remaining="${BASH_REMATCH[2]}"
    else
      return 1
    fi
  done

  (( total > 0 )) || return 1
  echo "${total}"
}

parse_clock_time_to_seconds() {
  local input="${1}"
  local hour minute ampm

  # Match 3pm, 3:30pm, 3:30PM, 3PM
  if [[ "${input}" =~ ^([0-9]{1,2})(:([0-9]{2}))?([aApP][mM])$ ]]; then
    hour="${BASH_REMATCH[1]}"
    minute="${BASH_REMATCH[3]:-0}"
    ampm="${BASH_REMATCH[4],,}"  # lowercase

    if [[ "${ampm}" == "pm" && "${hour}" -ne 12 ]]; then
      hour=$(( hour + 12 ))
    elif [[ "${ampm}" == "am" && "${hour}" -eq 12 ]]; then
      hour=0
    fi
  # Match 14:30, 9:00, 09:00
  elif [[ "${input}" =~ ^([0-9]{1,2}):([0-9]{2})$ ]]; then
    hour="${BASH_REMATCH[1]}"
    minute="${BASH_REMATCH[2]}"
  else
    return 1
  fi

  (( hour >= 0 && hour <= 23 )) || return 1
  (( minute >= 0 && minute <= 59 )) || return 1

  local now_epoch
  now_epoch=$(date +%s)

  # Calculate target epoch for today
  local target_epoch
  target_epoch=$(date -j -f "%H:%M:%S" "$(printf '%02d:%02d:00' "${hour}" "${minute}")" +%s 2>/dev/null) || \
    target_epoch=$(date -d "today ${hour}:${minute}:00" +%s 2>/dev/null) || \
    die "Could not parse target time. Ensure date command supports required format."

  local delta=$(( target_epoch - now_epoch ))

  # If the time has passed today, schedule for tomorrow
  if (( delta <= 0 )); then
    delta=$(( delta + 86400 ))
  fi

  echo "${delta}"
}

# Try parsing as duration first, then as clock time
seconds=""
if seconds=$(parse_duration_to_seconds "${input}" 2>/dev/null); then
  target_desc="after ${input}"
elif seconds=$(parse_clock_time_to_seconds "${input}" 2>/dev/null); then
  target_desc="at ${input}"
else
  die "Could not parse '${input}'. Use a duration (e.g. 30m, 1h, 2h30m) or clock time (e.g. 14:30, 3pm)."
fi

# Display wait info
if (( seconds >= 3600 )); then
  human_duration="$(( seconds / 3600 ))h$(( (seconds % 3600) / 60 ))m"
elif (( seconds >= 60 )); then
  human_duration="$(( seconds / 60 ))m$(( seconds % 60 ))s"
else
  human_duration="${seconds}s"
fi

wake_time=$(date -v+"${seconds}"S '+%H:%M:%S' 2>/dev/null) || \
  wake_time=$(date -d "+${seconds} seconds" '+%H:%M:%S' 2>/dev/null) || \
  wake_time="unknown"

echo "WAITING: ${human_duration} (${seconds}s) - ${target_desc}"
echo "WAKE_TIME: ${wake_time}"
echo "STARTED: $(date '+%Y-%m-%d %H:%M:%S')"

sleep "${seconds}"

echo "READY: $(date '+%Y-%m-%d %H:%M:%S')"
echo "Timer complete. Proceed with deferred task."
