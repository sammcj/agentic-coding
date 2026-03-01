#!/usr/bin/env bash
set -euo pipefail

# Sends OS notifications on macOS and Linux
# Usage: TITLE="Done" MESSAGE="Task complete" PLAY_SOUND=true DIR="~/output" TTL_SECONDS=10 ./send_notification.sh

title="${TITLE:-Notification}"
message="${MESSAGE:-}"
play_sound="${PLAY_SOUND:-false}"
sound="${SOUND:-default}"
dir="${DIR:-}"
ttl="${TTL_SECONDS:-}"

# Expand ~ in directory path
if [[ -n "$dir" ]]; then
    dir="${dir/#\~/$HOME}"
fi

detect_os() {
    case "$(uname -s)" in
        Darwin) echo "macos" ;;
        Linux)  echo "linux" ;;
        *)      echo "unsupported" ;;
    esac
}

notify_macos() {
    # Prefer terminal-notifier for click-to-open support
    if command -v terminal-notifier &>/dev/null; then
        local args=(-title "$title")
        [[ -n "$message" ]] && args+=(-message "$message")
        [[ -n "$dir" ]] && args+=(-open "file://$dir")
        [[ "$play_sound" == "true" ]] && args+=(-sound "$sound")
        terminal-notifier "${args[@]}" 2>/dev/null || {
            # terminal-notifier may fail in sandboxed environments - fall back to osascript
            local script="display notification \"$message\" with title \"$title\""
            [[ "$play_sound" == "true" ]] && script="$script sound name \"$sound\""
            osascript -e "$script" 2>/dev/null || true
            [[ -n "$dir" ]] && open "$dir" 2>/dev/null &
        }
    else
        # Fallback to osascript (no click-to-open support)
        echo "terminal-notifier not found, consider installing it with brew install terminal-notifier; falling back to basic osascript notification." >&2
        local script="display notification \"$message\" with title \"$title\""
        [[ "$play_sound" == "true" ]] && script="$script sound name \"$sound\""
        osascript -e "$script" 2>/dev/null || true

        # Open directory separately if specified
        [[ -n "$dir" ]] && open "$dir" 2>/dev/null &
    fi
}

notify_linux() {
    local args=()

    # Timeout in milliseconds
    if [[ -n "$ttl" ]]; then
        args+=(-t "$((ttl * 1000))")
    fi

    # Add action to open directory (works on some DEs)
    if [[ -n "$dir" ]]; then
        args+=(-A "open=Open folder")
    fi

    local result
    result=$(notify-send "${args[@]}" "$title" "$message" 2>/dev/null) || true

    # Handle action response
    if [[ "$result" == "open" && -n "$dir" ]]; then
        xdg-open "$dir" &>/dev/null &
    fi

    # Play sound
    if [[ "$play_sound" == "true" ]]; then
        if command -v paplay &>/dev/null; then
            local sound_file="/usr/share/sounds/freedesktop/stereo/complete.oga"
            [[ -f "$sound_file" ]] && paplay "$sound_file" &>/dev/null &
        elif command -v aplay &>/dev/null; then
            local sound_file="/usr/share/sounds/sound-icons/prompt.wav"
            [[ -f "$sound_file" ]] && aplay -q "$sound_file" &>/dev/null &
        fi
    fi
}

main() {
    local os
    os=$(detect_os)

    case "$os" in
        macos)
            notify_macos
            ;;
        linux)
            if ! command -v notify-send &>/dev/null; then
                echo "Error: notify-send not found. Install libnotify-bin." >&2
                exit 1
            fi
            notify_linux
            ;;
        *)
            echo "Error: Unsupported OS" >&2
            exit 1
            ;;
    esac
}

main
