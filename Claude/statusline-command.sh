#!/usr/bin/env bash
set -euo pipefail

input=$(cat)

used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // 0')
cwd=$(echo "$input" | jq -r '.workspace.current_dir // ""')

# Fetch 5-hour usage from Anthropic OAuth API (cached for n seconds)
CACHE_FILE="/tmp/claude_usage_cache.json"
CACHE_MAX_AGE=90 # seconds
session_pct=0

fetch_usage() {
    local creds token response
    creds=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null) || return 1
    token=$(echo "$creds" | jq -r '.claudeAiOauth.accessToken // empty' 2>/dev/null) || return 1
    [ -z "$token" ] && return 1

    response=$(curl -s --max-time 5 \
        -H "Authorization: Bearer $token" \
        -H "anthropic-beta: oauth-2025-04-20" \
        -H "User-Agent: claude-code-statusline/1.0" \
        "https://api.anthropic.com/api/oauth/usage" 2>/dev/null) || return 1

    echo "$response" > "$CACHE_FILE"
}

# Use cache if fresh, otherwise fetch in background
if [ -f "$CACHE_FILE" ]; then
    cache_age=$(( $(date +%s) - $(stat -f %m "$CACHE_FILE") ))
    if [ "$cache_age" -gt "$CACHE_MAX_AGE" ]; then
        fetch_usage &>/dev/null &
    fi
    session_pct=$(jq -r '.five_hour.utilization // 0' "$CACHE_FILE" 2>/dev/null | awk '{printf "%d", $1}')
else
    # First run - fetch synchronously
    fetch_usage
    session_pct=$(jq -r '.five_hour.utilization // 0' "$CACHE_FILE" 2>/dev/null | awk '{printf "%d", $1}')
fi

[ -z "$session_pct" ] && session_pct=0

# Parse reset time from cached data
resets_at=""
if [ -f "$CACHE_FILE" ]; then
    resets_iso=$(jq -r '.five_hour.resets_at // empty' "$CACHE_FILE" 2>/dev/null)
    if [ -n "$resets_iso" ]; then
        # Strip fractional seconds and colon from tz offset for macOS date
        clean_ts=$(echo "$resets_iso" | sed -E 's/\.[0-9]+//; s/:([0-9]{2})$/\1/')
        reset_epoch=$(date -j -f "%Y-%m-%dT%H:%M:%S%z" "$clean_ts" +%s 2>/dev/null) || reset_epoch=0
        now=$(date +%s)
        diff=$((reset_epoch - now))
        if [ "$diff" -gt 0 ]; then
            hrs=$((diff / 3600))
            mins=$(( (diff % 3600) / 60 ))
            if [ "$hrs" -gt 0 ]; then
                resets_at="${hrs}h${mins}m"
            else
                resets_at="${mins}m"
            fi
        fi
    fi
fi

progress_bar() {
    local percentage=$1
    local width=10
    local filled=$((percentage * width / 100))
    local empty=$((width - filled))

    local bar=""
    for ((i=0; i<filled; i++)); do bar="${bar}█"; done
    for ((i=0; i<empty; i++)); do bar="${bar}░"; done

    printf "%s" "$bar"
}

get_colour() {
    local pct=$1
    if [ "$pct" -lt 50 ]; then
        printf "\033[32m"
    elif [ "$pct" -lt 75 ]; then
        printf "\033[33m"
    else
        printf "\033[31m"
    fi
}

context_bar=$(progress_bar "$used_pct")
session_bar=$(progress_bar "$session_pct")
context_colour=$(get_colour "$used_pct")
session_colour=$(get_colour "$session_pct")
dir_name=$(basename "$cwd")

reset_str=""
if [ -n "$resets_at" ]; then
    if [ "$diff" -lt 1800 ]; then
        # Light blue when under 30 minutes
        reset_str=$' \033[94mResets: '"${resets_at}"$'\033[0m'
    else
        # Bright white
        reset_str=$' Resets:\033[97m '"${resets_at}"$'\033[0m'
    fi
fi

printf "Context: %s%s\033[0m %s%% | 5hr limit: %s%s\033[0m %s%%%s | Project: %s" \
    "$context_colour" "$context_bar" "$used_pct" \
    "$session_colour" "$session_bar" "$session_pct" "$reset_str" \
    "$dir_name"
