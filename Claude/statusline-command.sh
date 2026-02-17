#!/usr/bin/env bash
set -euo pipefail

input=$(cat)

used_pct=0 cwd="" model_name="unknown" session_id="default"
eval "$(jq -r '@sh "used_pct=\(.context_window.used_percentage // 0) cwd=\(.workspace.current_dir // "") model_name=\(.model.display_name // .model.id // "unknown") session_id=\(.session_id // "default")"' <<< "$input")"

# Fetch 5-hour usage from Anthropic OAuth API (cached for n seconds)
CACHE_FILE="/tmp/claude_usage_cache.json"
CACHE_MAX_AGE=60 # seconds
session_pct=0

fetch_usage() {
    local creds token response
    creds=$(security find-generic-password -s "Claude Code-credentials" -w 2>/dev/null) || return 1
    token=$(jq -r '.claudeAiOauth.accessToken // empty' <<< "$creds" 2>/dev/null) || return 1
    [ -z "$token" ] && return 1

    response=$(curl -s --max-time 5 \
        -H "Authorization: Bearer $token" \
        -H "anthropic-beta: oauth-2025-04-20" \
        -H "User-Agent: claude-code-statusline/1.0" \
        "https://api.anthropic.com/api/oauth/usage" 2>/dev/null) || return 1

    echo "$response" > "$CACHE_FILE"
}

# Use cache if fresh, otherwise fetch in background
read_cache=false
if [ -f "$CACHE_FILE" ]; then
    cache_age=$(( $(date +%s) - $(stat -f %m "$CACHE_FILE") ))
    if [ "$cache_age" -gt "$CACHE_MAX_AGE" ]; then
        fetch_usage &>/dev/null &
    fi
    read_cache=true
else
    # First run - fetch synchronously
    fetch_usage
    read_cache=true
fi

# Single jq call to read both values from cache
resets_at=""
diff=0
if [ "$read_cache" = true ] && [ -f "$CACHE_FILE" ]; then
    eval "$(jq -r '@sh "session_pct=\(.five_hour.utilization // 0) resets_iso=\(.five_hour.resets_at // "")"' "$CACHE_FILE" 2>/dev/null)"
    session_pct=${session_pct%.*}  # truncate to int
    [ -z "$session_pct" ] && session_pct=0

    if [ -n "$resets_iso" ]; then
        clean_ts=$(sed -E 's/\.[0-9]+//; s/:([0-9]{2})$/\1/' <<< "$resets_iso")
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

# --- Model usage tracking per session ---
MODEL_TRACK_DIR="/tmp/claude_model_tracking"
mkdir -p "$MODEL_TRACK_DIR"
MODEL_TRACK_FILE="${MODEL_TRACK_DIR}/${session_id}"

# Clean up stale session files older than 24 hours
find "$MODEL_TRACK_DIR" -type f -mtime +1 -delete 2>/dev/null || true

# Increment count for current model
if [ -f "$MODEL_TRACK_FILE" ]; then
    current_count=$(jq -r --arg m "$model_name" '.[$m] // 0' "$MODEL_TRACK_FILE" 2>/dev/null) || current_count=0
else
    current_count=0
fi
new_count=$((current_count + 1))
if [ -f "$MODEL_TRACK_FILE" ]; then
    jq --arg m "$model_name" --argjson c "$new_count" '.[$m] = $c' "$MODEL_TRACK_FILE" > "${MODEL_TRACK_FILE}.tmp" 2>/dev/null && \
        mv "${MODEL_TRACK_FILE}.tmp" "$MODEL_TRACK_FILE"
else
    printf '{\"%s\":%d}' "$model_name" "$new_count" > "$MODEL_TRACK_FILE"
fi

# Colour map for known models (short display names)
model_colour() {
    case "$1" in
        *Opus*)   printf "\033[35m" ;;  # magenta
        *Sonnet*) printf "\033[34m" ;;  # blue
        *Haiku*)  printf "\033[32m" ;;  # green
        *)        printf "\033[37m" ;;  # white fallback
    esac
}

# Build segmented model bar from tracking data
model_bar_width=10
model_bar=""
model_legend=""
if [ -f "$MODEL_TRACK_FILE" ]; then
    total_ticks=$(jq '[.[]] | add // 0' "$MODEL_TRACK_FILE" 2>/dev/null) || total_ticks=0
    if [ "$total_ticks" -gt 0 ]; then
        # Read model names and counts, sorted by count descending
        filled_so_far=0
        model_count=$(jq 'length' "$MODEL_TRACK_FILE" 2>/dev/null) || model_count=0
        model_idx=0

        while IFS='=' read -r m_name m_ticks; do
            model_idx=$((model_idx + 1))
            colour=$(model_colour "$m_name")
            if [ "$model_idx" -eq "$model_count" ]; then
                # Last model gets remaining blocks to avoid rounding gaps
                blocks=$((model_bar_width - filled_so_far))
            else
                blocks=$((m_ticks * model_bar_width / total_ticks))
                [ "$blocks" -lt 1 ] && blocks=1
            fi
            filled_so_far=$((filled_so_far + blocks))

            segment=""
            for ((i=0; i<blocks; i++)); do segment="${segment}█"; done
            model_bar="${model_bar}${colour}${segment}\033[0m"

            # Capture active model's percentage for the legend
            if [ "$m_name" = "$model_name" ]; then
                active_pct=$((m_ticks * 100 / total_ticks))
            fi
        done < <(jq -r 'to_entries | sort_by(-.value) | .[] | "\(.key)=\(.value)"' "$MODEL_TRACK_FILE" 2>/dev/null)

        active_colour=$(model_colour "$model_name")
        model_legend="${active_colour}${model_name} ${active_pct:-0}%\033[0m"
    fi
fi

# Fallback if no tracking data yet
if [ -z "$model_bar" ]; then
    colour=$(model_colour "$model_name")
    model_bar="${colour}"
    for ((i=0; i<model_bar_width; i++)); do model_bar="${model_bar}█"; done
    model_bar="${model_bar}\033[0m"
    model_legend="${colour}${model_name} 100%\033[0m"
fi

reset_str=""
if [ -n "$resets_at" ]; then
    if [ "$diff" -lt 1800 ]; then
        # Light blue when under 30 minutes
        reset_str=$' \033[94m'"${resets_at}"$'\033[0m'
    else
        # Bright white
        reset_str=$' \033[97m'"${resets_at}"$'\033[0m'
    fi
fi

printf "[%s] 🧠%s%s\033[0m %s%% | 📶%s%s\033[0m%s%%%s | 🧑‍💻%b %b" \
    "$dir_name" "$context_colour" "$context_bar" "$used_pct" \
    "$session_colour" "$session_bar" "$session_pct" "$reset_str" \
    "$model_bar" "$model_legend"
