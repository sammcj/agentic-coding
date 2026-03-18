#!/usr/bin/env bash
set -euo pipefail

# Scans a skill for security issues using Snyk Agent Scan.
# Usage:
#   scan_skill.sh <github-repo-url>          # scan a full repo
#   scan_skill.sh <raw-file-url>             # scan a single SKILL.md
#   scan_skill.sh --dir <local-directory>     # scan a local directory

usage() {
  echo "Usage: $0 <github-repo-url|raw-file-url>"
  echo "       $0 --dir <local-directory>"
  echo ""
  echo "Scans a skill for security issues using Snyk Agent Scan (uvx)."
  echo "Requires: uv"
  exit 1
}

if [[ $# -lt 1 ]]; then
  usage
fi

# Check uv is available
if ! command -v uv &>/dev/null; then
  echo "Error: uv is not installed. Install it from https://docs.astral.sh/uv/" >&2
  echo ""
  echo "Alternatively, scan manually at: https://labs.snyk.io/experiments/skill-scan/"
  exit 1
fi

SCAN_DIR=""
CLEANUP=false

cleanup() {
  if [[ "$CLEANUP" == "true" && -n "$SCAN_DIR" ]]; then
    rm -rf "$SCAN_DIR"
  fi
}
trap cleanup EXIT

if [[ "$1" == "--dir" ]]; then
  # Local directory mode
  if [[ $# -lt 2 ]]; then
    usage
  fi
  TARGET="$2"
  if [[ ! -d "$TARGET" ]]; then
    echo "Error: '$TARGET' is not a directory" >&2
    exit 1
  fi
  echo "Scanning local directory: $TARGET"
  uvx snyk-agent-scan@latest --skills "$TARGET" --json 2>/dev/null
elif [[ "$1" == *.md ]]; then
  # Single file mode (raw URL to a SKILL.md or similar)
  SCAN_DIR=$(mktemp -d)
  CLEANUP=true
  echo "Downloading skill file..."
  if ! curl -fsSL "$1" -o "$SCAN_DIR/SKILL.md"; then
    echo "Error: Failed to download '$1'" >&2
    exit 1
  fi
  echo "Scanning single skill file..."
  uvx snyk-agent-scan@latest --skills "$SCAN_DIR/SKILL.md" --json 2>/dev/null
else
  # Full repo mode
  SCAN_DIR=$(mktemp -d)
  CLEANUP=true
  echo "Cloning repository..."
  if ! git clone --depth 1 "$1" "$SCAN_DIR/skill-under-review" 2>/dev/null; then
    echo "Error: Failed to clone '$1'" >&2
    exit 1
  fi
  echo "Scanning skill repository..."
  uvx snyk-agent-scan@latest --skills "$SCAN_DIR/skill-under-review" --json 2>/dev/null
fi
