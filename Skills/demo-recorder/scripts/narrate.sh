#!/usr/bin/env bash
# Renders one Cloney text-to-speech clip per numbered script section; skips cleanly when Cloney is absent.
# Kept bash 3.2 compatible (macOS /bin/bash): no mapfile or associative arrays; empty arrays expand via ${a[@]+...}.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: narrate.sh <script.md> <audioDir> [timings.tsv]
       narrate.sh --list

Writes <audioDir>/N.wav for every "## N. Title" section of script.md, ready for dub.sh.
A section's text is every line after its heading except blank lines and _italic_ stage notes.
With timings.tsv (from encode.sh) each clip is fitted to scene N: the shortest of TAKES renders
is kept, then sped up by at most MAX_TEMPO if it still runs past the scene.

Raw renders are cached in <audioDir>/.narrate/ and redone only when a clip's text or voice
settings change; fitting to new timings re-runs from the cache. An N.wav that differs from what
narrate.sh last wrote (a hand-recorded take) is never overwritten unless FORCE=1. Clips of
removed sections are deleted. Exits 1 if any clip failed, so make demo stops before dubbing.
Delete <audioDir>/.narrate/N.* to re-render one clip; FORCE=1 re-renders them all.

Environment:
  VOICE        Cloney character name or UUID (default Attenborough)
  ENGINE       qwen3 | moss | dots | breeze | auk (default breeze, i.e. Breeze-TTS-2)
  REFERENCE    character reference name or 1-based index (default: the character's first)
  SEED         RNG seed; take k uses SEED+k (default: random)
  TAKES        renders per clip, shortest kept (default 1)
  MAX_TEMPO    speed-up ceiling for an overrunning clip, 1 disables (default 1.1)
  CLONEY_ARGS  extra flags for "cloney synth", e.g. "--breeze-direction 'Speak briskly.'"
  CLONEY_BIN   cloney executable (default: cloney on PATH, then the one inside Cloney.app)
  CLONEY_HOME  character library, for --list (default ~/Cloney)
  FORCE=1      re-render every clip, including hand-recorded ones

--list prints each character with its stored engine.
EOF
}

case "${1:-}" in -h | --help) usage; exit 0 ;; esac

cloney="${CLONEY_BIN:-$(command -v cloney || echo /Applications/Cloney.app/Contents/Helpers/cloney)}"
cloney=$(command -v "$cloney" || true) # resolves a bare name on PATH; empty unless executable

if [ "${1:-}" = "--list" ]; then
  for f in "${CLONEY_HOME:-$HOME/Cloney}"/*/character.json; do
    [ -f "$f" ] || { echo "narrate: no characters in ${CLONEY_HOME:-$HOME/Cloney}" >&2; exit 1; }
    # shellcheck disable=SC2016 # JS template literal, not shell
    node -e 'const c = require(process.argv[1]); console.log(`${c.name}\t${c.engine ?? "qwen3"}`)' "$f"
  done | sort -f | column -t -s $'\t'
  exit 0
fi

[ $# -ge 2 ] || { usage >&2; exit 1; }
script="$1"
audio="$2"
timings="${3:-}"
voice="${VOICE:-Attenborough}"
engine="${ENGINE:-breeze}"
takes="${TAKES:-1}"
max_tempo="${MAX_TEMPO:-1.1}"
gap=0.3 # dub.sh's gap between clips; a clip this much shorter than its scene never pushes the next one back
silent_db=-50 # max_volume below this is a silent render (Cloney exits 0 with a silent stub when weights are missing)

if [ -z "$cloney" ]; then
  echo "narrate: cloney not found (set CLONEY_BIN); skipping text-to-speech" >&2
  exit 0
fi

extra=()
eval "extra=(${CLONEY_ARGS:-})" # eval keeps a quoted value such as --breeze-direction 'Speak briskly.' as one argument
mkdir -p "$audio"
cache="$audio/.narrate" # raw renders and their keys; dub.sh only reads the top level
mkdir -p "$cache"
work=$(mktemp -d "$cache/work.XXXXXX") # beside the cache so finished takes move in without a copy
trap 'rm -rf "$work"' EXIT

# One file per section: N.txt holds the spoken text joined onto one line.
awk -v dir="$work" '
  /^## [0-9]+\.([[:space:]]|$)/ {
    n = $2 + 0
    if (n in seen) { print "narrate: two sections numbered " n > "/dev/stderr"; exit 1 }
    seen[n] = 0; out = dir "/" n ".txt"; printf "" > out; next
  }
  /^## [0-9]/ { print "narrate: section heading needs \"## N. Title\": " $0 > "/dev/stderr"; exit 1 }
  /^## / { out = ""; next }
  !out || /^[[:space:]]*$/ || /^_.*_[[:space:]]*$/ { next }
  { printf "%s%s", (seen[n]++ ? " " : ""), $0 >> out }
' "$script"
sections=()
while IFS= read -r s; do sections+=("$s"); done < <(find "$work" -name '*.txt' -exec basename {} .txt \; | sort -n)
[ "${#sections[@]}" -gt 0 ] || { echo "narrate: no '## N.' sections in $script" >&2; exit 1; }
if [ -n "$timings" ]; then
  if [ ! -f "$timings" ]; then
    echo "narrate: no $timings; clips will not be fitted to scenes" >&2
  elif [ "$(($(wc -l < "$timings") - 1))" != "${#sections[@]}" ]; then
    echo "narrate: ${#sections[@]} sections but $(($(wc -l < "$timings") - 1)) scenes in $timings" >&2
  fi
fi

scene_seconds() { # row N of timings.tsv, matching dub.sh's clip-to-scene order
  [ -n "$timings" ] && [ -f "$timings" ] && awk -F'\t' -v n="$1" 'NR == n + 1 { print $4 }' "$timings"
}
duration() { ffprobe -v error -show_entries format=duration -of csv=p=0 "$1"; }
peak_db() { ffmpeg -nostdin -hide_banner -i "$1" -af volumedetect -f null - 2>&1 | awk '/max_volume/ { print $5 }'; }
row() { printf '%-4s %6s %6s  %s\n' "$@"; }
hash() { shasum -a 256 "$1" | cut -c1-16; }
# N.wav is ours only while it still matches what we last wrote; anything else is a hand-recorded take.
ours() { [ -f "$audio/$1.wav" ] && [ -f "$cache/$1.out" ] &&[ "$(hash "$audio/$1.wav")" = "$(cat "$cache/$1.out")" ]; }

render() { # render <n> <txt> <raw>: keeps the shortest audible take
  local n=$1 txt=$2 raw=$3 best="" best_len="" t take len peak
  for ((t = 0; t < takes; t++)); do
    take="$work/$n-$t.wav"
    args=(synth --character "$voice" --engine "$engine" --text-file "$txt" -o "$take")
    [ -n "${REFERENCE:-}" ] && args+=(--reference "$REFERENCE")
    [ -n "${SEED:-}" ] && args+=(--seed "$((SEED + t))")
    if ! "$cloney" "${args[@]}" ${extra[@]+"${extra[@]}"} > "$work/$n-$t.log" 2>&1; then
      echo "narrate: clip $n take $((t + 1)) failed:" >&2
      tail -n 5 "$work/$n-$t.log" >&2
      continue
    fi
    peak=$(peak_db "$take")
    if awk -v p="$peak" -v s="$silent_db" 'BEGIN { exit !(p == "" || p + 0 < s) }'; then
      echo "narrate: clip $n take $((t + 1)) is silent (peak ${peak:-?} dB); check the engine's model is installed" >&2
      continue
    fi
    len=$(duration "$take")
    if [ -z "$best" ] || awk -v a="$len" -v b="$best_len" 'BEGIN { exit !(a < b) }'; then
      best=$take best_len=$len
    fi
  done
  [ -n "$best" ] && mv "$best" "$raw"
}

failed=0
row clip scene length note
for n in "${sections[@]}"; do
  txt="$work/$n.txt"
  wav="$audio/$n.wav"
  raw="$cache/$n.wav"
  scene=$(scene_seconds "$n" || true)
  if [ "${FORCE:-}" != 1 ]; then
    hand=""
    for f in "$audio/$n".{wav,mp3,m4a,aiff}; do # dub.sh takes any of these
      [ -f "$f" ] && { [ "$f" != "$wav" ] || ! ours "$n"; } && hand=$f
    done
    if [ -n "$hand" ]; then
      row "$n" "${scene:--}" "$(printf %.1f "$(duration "$hand")")" "kept (hand-recorded $(basename "$hand"))"
      continue
    fi
  fi
  if [ ! -s "$txt" ]; then
    row "$n" "${scene:--}" - "FAILED (no spoken text)"
    failed=1
    continue
  fi

  # Timing stays out of the key: fitting is cheap and re-runs every time, a render is not.
  key=$(printf '%s\n' "$(cat "$txt")" "$voice" "$engine" "${REFERENCE:-}" "${SEED:-}" "$takes" "${extra[*]:-}" |
    shasum -a 256 | cut -c1-16)
  if [ -f "$raw" ] && [ "$(cat "$cache/$n.key" 2>/dev/null)" = "$key" ] && [ "${FORCE:-}" != 1 ]; then
    note="unchanged"
  elif render "$n" "$txt" "$raw"; then
    echo "$key" > "$cache/$n.key"
    note="rendered"
  else
    row "$n" "${scene:--}" - "FAILED"
    failed=1
    continue
  fi

  tempo=1.000
  if [ -n "$scene" ]; then
    # atempo changes speed without shifting pitch; past ~1.1 the voice starts to sound hurried.
    # Rounded up so a fitted clip never lands a millisecond over and makes dub.sh push the next one back.
    tempo=$(awk -v l="$(duration "$raw")" -v s="$scene" -v g="$gap" -v m="$max_tempo" \
      'BEGIN { t = (s > g) ? l / (s - g) : m; t = int(t * 1000 + 0.999) / 1000; if (t > m) t = m
               printf "%.3f", (t > 1 ? t : 1) }')
  fi
  fit="$work/$n.fit.wav"
  if [ "$tempo" = "1.000" ]; then
    cp "$raw" "$fit"
  else
    ffmpeg -nostdin -loglevel error -y -i "$raw" -af "atempo=$tempo" "$fit"
    note="$note, sped up x$tempo"
  fi
  if [ -n "$scene" ] && awk -v l="$(duration "$fit")" -v s="$scene" 'BEGIN { exit !(l > s) }'; then
    note="$note, runs past scene"
  fi
  # Hash first, then an atomic mv: an interrupted write must not leave N.wav looking hand-recorded.
  hash "$fit" > "$cache/$n.out"
  mv "$fit" "$wav"
  row "$n" "${scene:--}" "$(printf %.1f "$(duration "$wav")")" "$note"
done

# A section removed or renumbered leaves its clip behind, and dub.sh would lay it over a scene.
for key in "$cache"/*.key; do
  [ -f "$key" ] || continue
  n=$(basename "$key" .key)
  [ -f "$work/$n.txt" ] && continue
  if ours "$n"; then
    rm -f "$audio/$n.wav"
    row "$n" - - "removed (no section $n)"
  elif [ -f "$audio/$n.wav" ]; then
    row "$n" - - "kept (hand-recorded), but no section $n: delete it or dub.sh will use it"
  fi
  rm -f "$cache/$n".*
done

# A failed clip would leave a gap for that scene; stop so make demo doesn't dub around it.
exit "$failed"
