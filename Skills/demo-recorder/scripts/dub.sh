#!/usr/bin/env bash
# Lays numbered narration clips over demo.mp4: N.wav (or .mp3/.m4a/.aiff) goes on the Nth scene of timings.tsv.
# Each clip starts at its scene's start, or just after the previous clip ends if that one runs long.
# Kept bash 3.2 compatible (macOS /bin/bash): no mapfile or associative arrays.
set -euo pipefail

usage="usage: dub.sh <outDir> <audioDir> [output.mp4]  (default output <outDir>/demo-dubbed.mp4)"
case "${1:-}" in -h | --help) echo "$usage"; exit 0 ;; esac
out="${1:?$usage}"
audio="${2:?$usage}"
dest="${3:-$out/demo-dubbed.mp4}"
gap=0.3 # seconds of silence kept between clips when one is pushed back

# Exit 0 without clips so make demo still ends cleanly when there is no narration.
[ -d "$audio" ] || { echo "dub: no $audio; nothing to dub" >&2; exit 0; }
clips=()
while IFS= read -r f; do
  [[ $(basename "$f") =~ ^[0-9]+\.(wav|mp3|m4a|aiff)$ ]] && clips+=("$f")
done < <(find "$audio" -maxdepth 1 -type f | sort -V)
for f in demo.mp4 timings.tsv; do
  [ -f "$out/$f" ] || { echo "dub: no $out/$f; run encode.sh first" >&2; exit 1; }
done
scenes=()
while IFS= read -r line; do scenes+=("$line"); done < <(tail -n +2 "$out/timings.tsv")
[ "${#clips[@]}" -gt 0 ] || { echo "dub: no numbered clips in $audio; nothing to dub" >&2; exit 0; }

inputs=(-i "$out/demo.mp4")
filters=""
labels=""
prev_end=0
printf '%-10s %6s %6s %6s %6s  %s\n' scene start clip ends sceneEnd note
dubbed=() # indexed by clip number
for i in "${!clips[@]}"; do
  n=$((10#$(basename "${clips[$i]%.*}"))) # 01.wav is clip 1
  [ "$n" -ge 1 ] && [ "$n" -le "${#scenes[@]}" ] || { echo "dub: ${clips[$i]} but only ${#scenes[@]} scenes" >&2; exit 1; }
  [ -z "${dubbed[$n]:-}" ] || { echo "dub: two clips numbered $n" >&2; exit 1; }
  dubbed[n]=1
  IFS=$'\t' read -r name s_start s_end _ <<< "${scenes[$((n - 1))]}"
  len=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "${clips[$i]}")
  at=$(awk -v s="$s_start" -v p="$prev_end" -v g="$gap" 'BEGIN { a = (p > 0 && p + g > s) ? p + g : s; printf "%.3f", a }')
  end=$(awk -v a="$at" -v l="$len" 'BEGIN { printf "%.3f", a + l }')
  note=""
  awk -v a="$at" -v s="$s_start" 'BEGIN { exit !(a > s) }' && note="pushed back"
  awk -v e="$end" -v se="$s_end" 'BEGIN { exit !(e > se) }' && note="${note:+$note, }runs past scene"
  printf '%-10s %6.1f %6.1f %6.1f %6.1f  %s\n' "$name" "$at" "$len" "$end" "$s_end" "$note"
  inputs+=(-i "${clips[$i]}")
  ms=$(awk -v a="$at" 'BEGIN { printf "%d", a * 1000 }')
  filters+="[$((i + 1)):a]aresample=48000,aformat=channel_layouts=stereo,adelay=${ms}|${ms}[a$i];"
  labels+="[a$i]"
  prev_end=$end
done
for i in "${!scenes[@]}"; do
  [ -n "${dubbed[$((i + 1))]:-}" ] || printf '%-10s  (no clip)\n' "$(cut -f1 <<< "${scenes[$i]}")"
done

# normalize=0 keeps each clip at its recorded level; amix would otherwise scale by the input count.
# apad + -shortest runs the silence out to the video's end instead of cutting the video at the last clip.
filters+="${labels}amix=inputs=${#clips[@]}:normalize=0:duration=longest,apad[aout]"
ffmpeg -nostdin -loglevel error -y "${inputs[@]}" -filter_complex "$filters" \
  -map 0:v -map "[aout]" -c:v copy -c:a aac -b:a 192k -shortest -movflags +faststart "$dest"
echo "wrote $dest"
