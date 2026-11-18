#!/usr/bin/env bash
# Usage: encode.sh <outDir>  - turns frames.ffconcat + scenes.json into demo.mp4 (no audio), timings.tsv and stills/ (a frame per scene, plus a contact sheet for each scene over 4s).
# Env: OUT_HEIGHT sets the output height (default 1620, i.e. 3K); "native" keeps the capture size (2160 at scale 2).
set -euo pipefail

case "${1:-}" in -h | --help) sed -n '2,3s/^# //p' "$0"; exit 0 ;; esac
out="${1:?usage: encode.sh <outDir>}"
lead=0.3 # seconds kept before the first scene so the video doesn't open mid-motion

# scene<TAB>start<TAB>end<TAB>duration, relative to the trimmed video; the first row carries the trim offset.
node -e '
  const { scenes, leadFrom = 0 } = JSON.parse(require("fs").readFileSync(process.argv[1] + "/scenes.json", "utf8"));
  // leadFrom is when the page of the first scene had painted; starting earlier would open the video on a blank frame.
  const trim = Math.min(scenes[0].start, Math.max(0, scenes[0].start - Number(process.argv[2]), leadFrom));
  if (scenes.length < 2) throw new Error("no scenes in scenes.json; call h.scene() in the demo");
  console.log("trim\t" + trim.toFixed(2) + "\t" + (scenes.at(-1).start - trim).toFixed(2));
  for (let i = 0; i < scenes.length - 1; i++) {
    const s = scenes[i].start - trim, e = scenes[i + 1].start - trim;
    console.log([scenes[i].name, s.toFixed(1), e.toFixed(1), (e - s).toFixed(1)].join("\t"));
  }
' "$out" "$lead" > "$out/timings.raw"

trim=$(awk -F'\t' 'NR==1 {print $2}' "$out/timings.raw")
length=$(awk -F'\t' 'NR==1 {print $3}' "$out/timings.raw") # up to the "end" scene mark
{ printf 'scene\tstart\tend\tseconds\n'; tail -n +2 "$out/timings.raw"; } > "$out/timings.tsv"
rm "$out/timings.raw"

filters="fps=60"
# Scale before fps so lanczos runs once per captured frame, not on every duplicate fps=60 adds.
# 3K from a 2x capture: downscaling supersamples the text, which a 1.5x capture would render softer.
out_height="${OUT_HEIGHT:-1620}"
[ "$out_height" != native ] && filters="scale=-2:${out_height}:flags=lanczos,$filters"

# 60fps keeps cursor moves smooth. CRF 12 holds small UI text sharp; mostly-static screens keep the file small.
# yuv420p, High profile and faststart play everywhere, including QuickTime and browsers.
ffmpeg -nostdin -loglevel error -y -f concat -safe 0 -i "$out/frames.ffconcat" -ss "$trim" -t "$length" -an \
  -vf "$filters" -c:v libx264 -preset slow -crf 12 -profile:v high -pix_fmt yuv420p -movflags +faststart \
  "$out/demo.mp4"

mkdir -p "$out/stills"
rm -f "$out"/stills/*.png
n=0
tail -n +2 "$out/timings.tsv" | while IFS=$'\t' read -r name start _end secs; do
  n=$((n + 1))
  at=$(awk -v s="$start" -v d="$secs" 'BEGIN { print s + (d < 3 ? d / 2 : 1.5) }') # short scenes still get their own still
  still="$out/stills/$(printf %02d "$n")-$name"
  ffmpeg -nostdin -loglevel error -y -ss "$at" -i "$out/demo.mp4" -frames:v 1 "$still.png"
  # One frame cannot show a missed click later in a long scene. A frame every 2s, stretched so 12 tiles span the scene.
  if awk -v d="$secs" 'BEGIN { exit !(d > 4) }'; then
    every=$(awk -v d="$secs" 'BEGIN { e = d / 12; printf "%.2f", (e > 2 ? e : 2) }')
    ffmpeg -nostdin -loglevel error -y -ss "$start" -t "$secs" -i "$out/demo.mp4" \
      -vf "fps=1/$every,scale=960:-2,tile=4x3" -frames:v 1 "$still.sheet.png"
  fi
done

size=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "$out/demo.mp4")
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$out/demo.mp4")
printf 'demo.mp4 %s %.1fs %s\n' "$size" "$dur" "$(du -h "$out/demo.mp4" | cut -f1)"
column -t -s $'\t' "$out/timings.tsv"
