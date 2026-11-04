#!/usr/bin/env bash
# Add or revoke a private beta tester's update token in the update service KV.
# Usage: beta-token.sh [--dry-run] add <label> | revoke <label>
#
# add prints the token once, to send to the tester. KV keeps only its SHA-256, with the label in the key's metadata
# so revoke can find it. --dry-run prints the wrangler commands instead of running them. Needs `wrangler login`.
set -euo pipefail

USAGE="usage: beta-token.sh [--dry-run] add <label> | revoke <label>"
WRANGLER=(npx --yes wrangler@4)
WORKER_DIR="$(cd "$(dirname "$0")/../updates-worker" && pwd)"
DRY=0
if [[ "${1:-}" == --dry-run ]]; then DRY=1; shift; fi
ACTION="${1:?$USAGE}"
LABEL="${2:?$USAGE}"
# The label goes into JSON metadata unescaped, so it is kept to characters that need no escaping.
[[ "$LABEL" =~ ^[A-Za-z0-9._@+-]+$ ]] || { echo "ERROR: label may contain only letters, digits and . _ @ + -" >&2; exit 1; }

run() {
    if (( DRY )); then printf '%q ' "$@"; echo; else (cd "$WORKER_DIR" && "$@"); fi
}

case "$ACTION" in
    add)
        # 32 random bytes as base64url without padding: the 43 characters the Worker accepts.
        token=$(openssl rand 32 | base64 | tr '+/' '-_' | tr -d '=\n')
        hash=$(printf '%s' "$token" | shasum -a 256 | cut -d' ' -f1)
        run "${WRANGLER[@]}" kv key put --binding BETA_TOKENS --remote --metadata "{\"label\":\"$LABEL\"}" "$hash" "$LABEL"
        (( DRY )) || printf 'Token for %s (shown once, not stored anywhere):\n%s\n' "$LABEL" "$token"
        ;;
    revoke)
        if (( DRY )); then
            run "${WRANGLER[@]}" kv key list --binding BETA_TOKENS --remote
            echo "then, for each key whose metadata label is $LABEL:"
            run "${WRANGLER[@]}" kv key delete --binding BETA_TOKENS --remote "<sha256>"
            exit 0
        fi
        # wrangler may print a banner before the JSON list.
        hashes=$(run "${WRANGLER[@]}" kv key list --binding BETA_TOKENS --remote \
            | sed -n '/^\[/,$p' | jq -r --arg label "$LABEL" '.[] | select(.metadata.label == $label) | .name')
        [[ -n "$hashes" ]] || { echo "ERROR: no token labelled $LABEL" >&2; exit 1; }
        while read -r hash; do
            run "${WRANGLER[@]}" kv key delete --binding BETA_TOKENS --remote "$hash"
        done <<< "$hashes"
        echo "Revoked $(wc -l <<< "$hashes" | tr -d ' ') token(s) labelled $LABEL"
        ;;
    *) echo "$USAGE" >&2; exit 1 ;;
esac
