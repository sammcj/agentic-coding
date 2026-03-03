#!/usr/bin/env bash
set -euo pipefail

# Format markdown files using prettier.
# Auto-detects bunx or npx. Suppresses output on success.
#
# Usage: bash scripts/format.sh <file> [file2 ...]
#        bash scripts/format.sh --check <file>

if [[ $# -eq 0 ]]; then
    echo "Usage: $0 [--check] <file> [file2 ...]" >&2
    exit 1
fi

# Avoid OpenSSL sandbox errors in npm/bun cache operations.
export OPENSSL_CONF=/dev/null

mode="--write"
if [[ "$1" == "--check" ]]; then
    mode="--check"
    shift
    if [[ $# -eq 0 ]]; then
        echo "Usage: $0 [--check] <file> [file2 ...]" >&2
        exit 1
    fi
fi

# Detect runner: prefer bunx, fall back to npx.
if command -v bunx &>/dev/null; then
    runner="bunx"
elif command -v npx &>/dev/null; then
    runner="npx -y"
else
    echo "Error: Neither bunx nor npx found. Install bun or node." >&2
    exit 1
fi

# Run prettier, capture output. Only print on failure.
output=$($runner prettier "$mode" "$@" 2>&1) || {
    rc=$?
    echo "prettier failed (exit $rc):" >&2
    echo "$output" >&2
    exit $rc
}
