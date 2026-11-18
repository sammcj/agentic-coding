#!/usr/bin/env bash
# Joins finished cuts end to end without re-encoding.
set -euo pipefail

usage="usage: join.sh <output.mp4> <part.mp4>...
Parts must come from this skill's encode.sh or dub.sh, which share one codec and frame size, and must
all be silent or all be dubbed: the concat demuxer copies streams and cannot add a missing audio track."
case "${1:-}" in -h | --help) echo "$usage"; exit 0 ;; esac
[ $# -ge 2 ] || { echo "$usage" >&2; exit 1; }
dest=$1
shift

list=$(mktemp "${TMPDIR:-/tmp}/join.XXXXXX")
trap 'rm -f "$list"' EXIT
audio=""
for part in "$@"; do
  [ -f "$part" ] || { echo "join: no $part" >&2; exit 1; }
  has=$(ffprobe -v error -select_streams a -show_entries stream=codec_type -of csv=p=0 "$part" | head -1)
  [ -z "$audio" ] && audio="${has:-none}"
  [ "${has:-none}" = "$audio" ] || { echo "join: $part and $1 differ in having audio; dub every part or none" >&2; exit 1; }
  # The demuxer reads paths relative to the list file, so they go in absolute; ' is the list's quote character.
  abs="$(cd "$(dirname "$part")" && pwd)/$(basename "$part")"
  printf "file '%s'\n" "${abs//\'/\'\\\'\'}" >> "$list"
done

mkdir -p "$(dirname "$dest")"
ffmpeg -nostdin -loglevel error -y -f concat -safe 0 -i "$list" -c copy -movflags +faststart "$dest"
printf '%s %.1fs %s\n' "$dest" "$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$dest")" "$(du -h "$dest" | cut -f1)"
