#!/usr/bin/env bash
set -euo pipefail

# YouTube Transcript Downloader
# Downloads only transcripts/subtitles from YouTube videos (no video file)
# Organises files by video ID in the Wisdom directory
# Auto-detects macOS or Linux and uses appropriate paths
# Falls back to no-cookie download if browser cookies unavailable

# Resolve the script's real location for environment detection.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"

# Detect environment and set appropriate base directory.
# Claw-based environments are detected automatically from the script path:
#   ~/.openclaw/workspace/...  ->  openclaw
#   ~/.zeroclaw/workspace/...  ->  zeroclaw
#   ~/.anyclaw/workspace/...   ->  anyclaw   (no code changes needed)
# On Linux, set <UPPERNAME>_WISDOM_DIR to override the output directory.
detect_environment_and_set_paths() {
    local base_dir=""
    local detected_env=""
    local ws_dir=""

    # Detect from script path: ~/.{name}/workspace/...
    if [[ "$SCRIPT_DIR" =~ ^"${HOME}"/\.([^/]+)/workspace(/|$) ]]; then
        detected_env="${BASH_REMATCH[1]}"
        ws_dir="${HOME}/.${detected_env}/workspace"
    elif [[ "$SCRIPT_DIR" =~ ^"${HOME}"/\.claude(/|$) ]]; then
        detected_env="claude-code"
    fi

    if [[ -n "$detected_env" && "$detected_env" != "claude-code" ]]; then
        # Claw-based environment
        if [[ "$OSTYPE" == "darwin"* ]]; then
            base_dir="${ws_dir}/wisdom"
        else
            # Convention: <UPPERNAME>_WISDOM_DIR overrides output on Linux
            local wisdom_env
            wisdom_env="$(printf '%s' "$detected_env" | tr '[:lower:]' '[:upper:]')_WISDOM_DIR"
            if [[ -n "${!wisdom_env:-}" ]]; then
                base_dir="${!wisdom_env}"
            else
                base_dir="${ws_dir}/wisdom"
            fi
        fi
    elif [[ "$detected_env" == "claude-code" ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            if [[ -d "${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Documents" ]]; then
                base_dir="${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Documents/Wisdom"
            else
                base_dir="${HOME}/Wisdom"
            fi
        else
            base_dir="${HOME}/.claude/wisdom"
        fi
    else
        # Unknown environment -- sensible defaults
        if [[ "$OSTYPE" == "darwin"* ]]; then
            if [[ -d "${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Documents" ]]; then
                base_dir="${HOME}/Library/Mobile Documents/com~apple~CloudDocs/Documents/Wisdom"
            else
                base_dir="${HOME}/Wisdom"
            fi
        else
            base_dir="${HOME}/Wisdom"
        fi
    fi

    export DETECTED_ENV="$detected_env"
    echo "$base_dir"
}

# Download transcript with optional cookie support
download_transcript() {
    local video_url="$1"
    local video_dir="$2"
    local use_cookies="${3:-false}"

    local args=(
        yt-dlp
        --skip-download
        --write-subs
        --write-auto-subs
        --sub-format json3
        --sub-lang en
        --restrict-filenames
        -o "${video_dir}/%(title)s.%(ext)s"
    )

    if [[ "$use_cookies" == "true" ]]; then
        local browser=""
        for b in firefox chrome chromium safari edge brave; do
            if command -v "$b" &>/dev/null || [[ -d "${HOME}/.config/$b" ]] || [[ -d "${HOME}/.var/app/com.google.Chrome" ]]; then
                browser="$b"
                break
            fi
        done

        if [[ -n "$browser" ]]; then
            args+=(--cookies-from-browser "$browser")
            echo "Using browser cookies from: $browser"
        else
            echo "No supported browser found for cookies, proceeding without..."
        fi
    fi

    "${args[@]}" "$video_url" 2>&1 || return 1
}

extract_video_id() {
    local url="$1"
    local video_id=""

    # Extract video ID using yt-dlp's own parsing
    video_id=$(yt-dlp --get-id "$url" 2>/dev/null || echo "")

    if [[ -z "$video_id" ]]; then
        echo "Error: Could not extract video ID from URL" >&2
        exit 1
    fi

    echo "$video_id"
}

main() {
    local video_url="${1:-}"
    local video_id
    local video_dir
    local base_videos_dir
    local converted_count=0
    local download_success=false

    # Validate input
    if [[ -z "$video_url" ]]; then
        echo "Error: No video URL provided"
        echo "Usage: $0 <youtube-url>"
        echo ""
        echo "Environment variables (Linux only - override output directory):"
        echo "  <UPPERNAME>_WISDOM_DIR  e.g. OPENCLAW_WISDOM_DIR, ZEROCLAW_WISDOM_DIR"
        exit 1
    fi

    # Detect environment and set base directory
    base_videos_dir=$(detect_environment_and_set_paths)
    echo "Using output directory: $base_videos_dir"

    # Extract video ID
    echo "Extracting video ID from URL..."
    video_id=$(extract_video_id "$video_url")
    echo "Video ID: $video_id"

    # Create directory structure
    video_dir="${base_videos_dir}/${video_id}"
    mkdir -p "$video_dir"
    echo "Created directory: $video_dir"

    # Download ONLY transcripts/subtitles (skip video download)
    # First try with cookies, then fallback to without
    echo "Downloading transcripts from: $video_url"
    echo "Attempting download with browser cookies..."
    
    if download_transcript "$video_url" "$video_dir" "true"; then
        download_success=true
        echo "Download successful with cookies"
    else
        echo "Cookie-based download failed, trying without cookies..."
        if download_transcript "$video_url" "$video_dir" "false"; then
            download_success=true
            echo "Download successful without cookies"
        fi
    fi

    # Check if we actually got any subtitle files
    if [[ "$download_success" != "true" ]] || [[ -z "$(find "$video_dir" -maxdepth 1 -name "*.json3" -print -quit 2>/dev/null || true)" ]]; then
        echo "Error: No subtitle files were downloaded"
        echo "Check: $video_dir"
        echo ""
        echo "This may be due to:"
        echo "  - Age-restricted video requiring login"
        echo "  - Video has no available subtitles"
        echo "  - Video is private or unlisted"
        echo "  - Rate limiting from YouTube"
        exit 1
    fi

    # Convert JSON3 subtitle files to clean text with proper naming
    while IFS= read -r -d '' file; do
        local base_name="${file%.json3}"
        # Remove language code suffix (e.g., .en, .es, .fr, etc.)
        base_name="${base_name%.*}"
        local output_file="${base_name} - transcript.txt"

        echo "Converting: ${file##*/}"

        # Extract and clean subtitle text
        if jq -r '[.events[].segs[]?.utf8] | join("") | gsub("[\\n ]+"; " ")' "$file" > "$output_file" 2>/dev/null; then
            rm -f "$file"
            echo "Created: ${output_file##*/}"
            converted_count=$((converted_count + 1))
        else
            echo "Error: Failed to convert ${file##*/}"
        fi
    done < <(find "$video_dir" -maxdepth 1 -name "*.json3" -print0 2>/dev/null || true)

    # Clean up any stray .txt files without the - transcript suffix or with language codes
    while IFS= read -r -d '' old_file; do
        echo "Removing unwanted file: ${old_file##*/}"
        rm -f "$old_file"
    done < <(find "$video_dir" -maxdepth 1 -type f -name "*.txt" ! -name "*- transcript.txt" -print0 2>/dev/null || true)

    # Report results
    if [[ $converted_count -eq 0 ]]; then
        echo "Error: No subtitles found or downloaded for this video"
        echo "Check: $video_dir"
        exit 1
    fi
    
    # Find the transcript file path
    local transcript_file
    transcript_file=$(find "$video_dir" -maxdepth 1 -name "*- transcript.txt" -print -quit 2>/dev/null || true)
    
    if [[ -z "$transcript_file" ]]; then
        echo "Error: Transcript file not found after conversion"
        exit 1
    fi
    
    # Output compact format for the agent
    echo ""
    echo "TRANSCRIPT_PATH: $transcript_file"
    echo "OUTPUT_DIR: $video_dir"
    echo "NEXT_STEP: mv $video_dir ${base_videos_dir}/$(date +%Y-%m-%d)-<description>"
    
    exit 0
}

main "$@"
