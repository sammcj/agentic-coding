#!/usr/bin/env python3
"""Print one tab-separated row per slide that still needs a sub-agent.

Each row is `slide_number<TAB>manifest_path<TAB>output_path`. Slides whose
output markdown already exists are skipped, so reruns only target missing
work. Pipe into a parallel dispatch loop, or read into the orchestrator to
batch sub-agent calls.

Usage:
    python dispatch_list.py WORKSPACE_DIR [--all]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", type=Path, help="workspace directory produced by prepare.py")
    ap.add_argument("--all", action="store_true", help="emit all slides, not just missing ones")
    args = ap.parse_args()

    index_path = args.workspace / "deck_index.json"
    if not index_path.exists():
        sys.exit(f"error: {index_path} not found - run prepare.py first")
    index = json.loads(index_path.read_text())

    extracted = index.get("extracted") or index.get("visible") or []
    manifests = args.workspace / "manifests"
    slides = args.workspace / "slides"

    for sn in extracted:
        out = slides / f"slide{sn:02d}.md"
        if out.exists() and not args.all:
            continue
        m = manifests / f"slide{sn:02d}.json"
        print(f"{sn}\t{m}\t{out}")


if __name__ == "__main__":
    main()
