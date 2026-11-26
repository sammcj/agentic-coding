#!/usr/bin/env bash
# Render an HTML file to PNG with a headless Chromium-family browser.
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: render.sh --html FILE --out FILE [--width PX] [--height PX] [--scale N] [--crop X,Y,W,H]
  --html    HTML file to render
  --out     PNG to write
  --width   viewport width in CSS px (default 1400)
  --height  viewport height in CSS px; the PNG is cut at this height (default 2400)
  --scale   device scale factor; 2 shows 16 px icons and menu bar glyphs as they look on Retina (default 1)
  --crop    keep only this region, in CSS px from the page's top left (scaled for you); needs magick or sips
Set BROWSER to a browser binary to override the search.
EOF
}

html="" out="" width=1400 height=2400 scale=1 crop=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --html) html="$2"; shift 2 ;;
    --out) out="$2"; shift 2 ;;
    --width) width="$2"; shift 2 ;;
    --height) height="$2"; shift 2 ;;
    --scale) scale="$2"; shift 2 ;;
    --crop) crop="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
[[ -n "$html" && -n "$out" ]] || { usage >&2; exit 2; }
[[ -f "$html" ]] || { echo "No such file: $html" >&2; exit 1; }

find_browser() {
  if [[ -n "${BROWSER:-}" ]]; then echo "$BROWSER"; return; fi
  local candidates=(
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    "/Applications/Chromium.app/Contents/MacOS/Chromium"
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
  )
  for c in "${candidates[@]}"; do [[ -x "$c" ]] && { echo "$c"; return; }; done
  for c in google-chrome chromium chromium-browser brave-browser microsoft-edge; do
    command -v "$c" >/dev/null && { command -v "$c"; return; }
  done
  # Playwright's cached build, when no browser is installed.
  local pw=""
  for c in "$HOME"/Library/Caches/ms-playwright/chromium-*/chrome-mac*/*.app/Contents/MacOS/* \
    "$HOME"/.cache/ms-playwright/chromium-*/chrome-linux*/chrome; do
    [[ -x "$c" ]] && pw="$c"
  done
  [[ -n "$pw" ]] && { echo "$pw"; return; }
  return 1
}

browser=$(find_browser) || { echo "No Chromium-family browser found. Set BROWSER." >&2; exit 1; }
abs_html="$(cd "$(dirname "$html")" && pwd)/$(basename "$html")"
mkdir -p "$(dirname "$out")"
abs_out="$(cd "$(dirname "$out")" && pwd)/$(basename "$out")"
rm -f "$abs_out"

# GPU and display-link errors on stderr are normal in headless mode, so success is judged by the file.
"$browser" --headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor="$scale" \
  --window-size="$width,$height" --screenshot="$abs_out" "file://$abs_html" >/dev/null 2>&1 || true
[[ -s "$abs_out" ]] || { echo "Render failed: $browser wrote no PNG" >&2; exit 1; }

if [[ -n "$crop" ]]; then
  IFS=, read -r cx cy cw ch <<<"$crop"
  # The PNG is in device pixels, so CSS px are multiplied by the scale factor.
  px() { awk -v v="$1" -v s="$scale" 'BEGIN { printf "%d", v * s }'; }
  x=$(px "$cx") y=$(px "$cy") w=$(px "$cw") h=$(px "$ch")
  if command -v magick >/dev/null; then
    magick "$abs_out" -crop "${w}x${h}+${x}+${y}" +repage "$abs_out"
  elif command -v sips >/dev/null; then
    sips -c "$h" "$w" --cropOffset "$y" "$x" "$abs_out" >/dev/null
  else
    echo "Rendered, but --crop needs magick or sips: $abs_out" >&2; exit 1
  fi
fi
echo "$abs_out"
