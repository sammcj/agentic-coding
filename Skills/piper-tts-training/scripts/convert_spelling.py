#!/usr/bin/env python3
"""
Convert American English spelling to Australian/UK English.

Usage:
    python convert_spelling.py input.txt output.txt
    python convert_spelling.py metadata.csv metadata_uk.csv

Processes text files or LJSpeech metadata.csv files.
"""

import json
import re
import sys
from pathlib import Path

# Load mappings from JSON file
SCRIPT_DIR = Path(__file__).parent
MAPPINGS_FILE = SCRIPT_DIR.parent / "references" / "american_spellings.json"

WORD_REPLACEMENTS: dict[str, str] = {}
if MAPPINGS_FILE.exists():
    with open(MAPPINGS_FILE, encoding="utf-8") as f:
        WORD_REPLACEMENTS = json.load(f)

# Words to preserve (don't convert via pattern matching)
PRESERVE_WORDS = {
    "size", "sized", "sizes", "sizing",
    "prize", "prized", "prizes",
    "seize", "seized", "seizes", "seizing",
    "capsize", "capsized",
}


def convert_text(text: str) -> str:
    """Convert American spelling to UK/AU spelling."""
    result = text

    # Apply word replacements (case-insensitive with case preservation)
    for us, uk in WORD_REPLACEMENTS.items():
        pattern = re.compile(r"\b" + re.escape(us) + r"\b", re.IGNORECASE)

        def replace_preserve_case(match, uk_word=uk):
            matched = match.group(0)
            if matched.isupper():
                return uk_word.upper()
            elif matched[0].isupper():
                return uk_word.capitalize()
            return uk_word

        result = pattern.sub(replace_preserve_case, result)

    return result


def process_file(input_path: Path, output_path: Path) -> tuple[int, int]:
    """Process a file and return (lines_processed, lines_changed)."""
    lines_processed = 0
    lines_changed = 0

    with open(input_path, encoding="utf-8") as f:
        lines = f.readlines()

    converted_lines = []
    for line in lines:
        lines_processed += 1
        converted = convert_text(line)
        if converted != line:
            lines_changed += 1
        converted_lines.append(converted)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(converted_lines)

    return lines_processed, lines_changed


def main():
    if len(sys.argv) != 3:
        print("Usage: convert_spelling.py <input_file> <output_file>")
        print("\nConverts American English to Australian/UK English spelling.")
        print("Works with plain text files or LJSpeech metadata.csv files.")
        print(f"\nLoaded {len(WORD_REPLACEMENTS)} spelling mappings.")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        sys.exit(1)

    lines_processed, lines_changed = process_file(input_path, output_path)

    print(f"Processed {lines_processed} lines ({len(WORD_REPLACEMENTS)} mappings)")
    print(f"Modified {lines_changed} lines")
    print(f"Output written to: {output_path}")


if __name__ == "__main__":
    main()
