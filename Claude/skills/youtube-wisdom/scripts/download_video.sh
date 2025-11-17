#!/usr/bin/env bash
set -euo pipefail

# YouTube Transcript Downloader
# Downloads only transcripts/subtitles from YouTube videos (no video file)
# Organises files by video ID in ~/Downloads/videos/<video-id>/

extract_video_id() {
    local url="$1"
    local video_id=""

    # Extract video ID using yt-dlp's own parsing
    video_id=$(yt-dlp --get-id "$url" 2>/dev/null || echo "")

    if [[ -z "$video_id" ]]; then
        echo "Error: Could not extract video ID from URL"
        exit 1
    fi

    echo "$video_id"
}

main() {
    local video_url="$1"
    local video_id
    local video_dir
    local base_videos_dir="${HOME}/Downloads/videos"
    local converted_count=0

    # Validate input
    if [[ -z "$video_url" ]]; then
        echo "Error: No video URL provided"
        echo "Usage: $0 <youtube-url>"
        exit 1
    fi

    # Extract video ID
    echo "Extracting video ID from URL..."
    video_id=$(extract_video_id "$video_url")
    echo "Video ID: $video_id"

    # Create directory structure
    video_dir="${base_videos_dir}/${video_id}"
    mkdir -p "$video_dir"
    echo "Created directory: $video_dir"

    # Download ONLY transcripts/subtitles (skip video download)
    echo "Downloading transcripts from: $video_url"
    if ! yt-dlp \
        --skip-download \
        --write-subs \
        --write-auto-subs \
        --sub-format json3 \
        --sub-lang en \
        --cookies-from-browser firefox \
        -o "$video_dir/%(title)s.%(ext)s" \
        "$video_url"; then
        echo "Error: yt-dlp failed to download transcripts"
        exit 1
    fi

    # Convert JSON3 subtitle files to clean text
    for file in "$video_dir"/*.json3; do
        [[ -e "$file" ]] || continue

        local base_name="${file%.json3}"
        local output_file="${base_name}.txt"

        echo "Converting $file to $output_file"

        # Extract and clean subtitle text
        if jq -r '[.events[].segs[]?.utf8] | join("") | gsub("[\n ]+"; " ")' "$file" > "$output_file"; then
            rm "$file"
            echo "Cleaned up $file"
            ((converted_count++))
        else
            echo "Error: Failed to convert $file"
        fi
    done

    # Report results
    if [[ $converted_count -eq 0 ]]; then
        echo "Warning: No subtitles found or downloaded for this video"
        echo "Check: $video_dir"
        exit 1
    else
        echo "Success: Downloaded and extracted $converted_count transcript(s)"
        echo "Location: $video_dir"
    fi
}

main "$@"
