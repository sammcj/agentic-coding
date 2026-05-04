#!/usr/bin/env python3
"""Concatenate per-slide markdown into a single deck.md.

Reads deck_index.json from a workspace produced by prepare.py, then stitches
the per-slide markdown files in source-slide order with a brief header that
notes which hidden slides were excluded.

Usage:
    python concatenate.py WORKSPACE_DIR [--out deck.md] [--title "Deck title"]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", type=Path, help="workspace directory produced by prepare.py")
    ap.add_argument("--out", type=Path, default=None, help="output path (default: WORKSPACE/deck.md)")
    ap.add_argument("--title", type=str, default=None, help="optional deck title for the header")
    args = ap.parse_args()

    ws = args.workspace
    index_path = ws / "deck_index.json"
    if not index_path.exists():
        sys.exit(f"error: {index_path} not found - run prepare.py first")
    index = json.loads(index_path.read_text())

    slides_dir = ws / "slides"
    extracted = index.get("extracted") or index.get("visible") or []
    hidden = index.get("hidden") or []

    missing = [sn for sn in extracted if not (slides_dir / f"slide{sn:02d}.md").exists()]
    if missing:
        sys.exit(
            f"error: missing slide markdown for: {missing}. "
            "Dispatch sub-agents for these slides before concatenating."
        )

    out = args.out or (ws / "deck.md")
    title = args.title or "Deck"
    header_lines = [f"# {title}", ""]
    if hidden:
        header_lines += [
            "Hidden slides excluded: " + ", ".join(str(h) for h in hidden) + ".",
            "",
        ]
    header_lines += ["---", "", ""]
    parts = ["\n".join(header_lines)]

    for sn in extracted:
        body = (slides_dir / f"slide{sn:02d}.md").read_text().rstrip()
        parts.append(body + "\n\n---\n\n")

    out.write_text("".join(parts))
    print(f"wrote {out} ({len(extracted)} slides, hidden: {hidden if hidden else 'none'})")


if __name__ == "__main__":
    main()
