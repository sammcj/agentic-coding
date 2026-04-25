#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# ///

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path


def find_project_root(start: Path) -> Path:
    current = start.resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    print("Error: could not find .git directory in any parent", file=sys.stderr)
    sys.exit(1)


def git_commit_count(root: Path) -> int:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=root,
        )
        return int(result.stdout.strip())
    except subprocess.CalledProcessError as e:
        print(f"Error: git rev-list failed: {e.stderr.strip()}", file=sys.stderr)
        sys.exit(1)


def compute_calver(root: Path) -> str:
    today = date.today()
    commits = git_commit_count(root)
    return f"{today.year}.{today.month}.{commits}"


def discover_config_files(root: Path) -> list[Path]:
    candidates = [
        root / "package.json",
        root / "Cargo.toml",
        root / "pyproject.toml",
        root / "tauri.conf.json",
        root / "src-tauri" / "tauri.conf.json",
        root / "VERSION",
    ]
    return [p for p in candidates if p.is_file()]


def _detect_json_indent(text: str) -> int:
    for line in text.splitlines()[1:]:
        stripped = line.lstrip()
        if stripped:
            return len(line) - len(stripped)
    return 2


def stamp_json_file(path: Path, version: str, dry_run: bool) -> str | None:
    with open(path, encoding="utf-8") as f:
        raw = f.read()

    data = json.loads(raw)

    if "version" not in data:
        return None

    old_version = data["version"]
    if old_version == version:
        return None

    if not dry_run:
        indent = _detect_json_indent(raw)
        data["version"] = version
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
            f.write("\n")

    return old_version


def stamp_toml_file(path: Path, version: str, dry_run: bool) -> str | None:
    with open(path, encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r'^(version\s*=\s*)"([^"]*)"', re.MULTILINE)
    match = pattern.search(content)
    if not match:
        return None

    old_version = match.group(2)
    if old_version == version:
        return None

    if not dry_run:
        new_content = pattern.sub(rf'\g<1>"{version}"', content, count=1)
        with open(path, "w", encoding="utf-8") as f:
            f.write(new_content)

    return old_version


def stamp_version_file(path: Path, version: str, dry_run: bool) -> str | None:
    with open(path, encoding="utf-8") as f:
        content = f.read().strip()

    # Only stamp if existing content looks like a version. This avoids
    # rewriting files named VERSION that hold something else (build numbers,
    # tag-prefixed strings, multi-line metadata).
    if not re.match(r"^\d+\.\d+\.\d+", content):
        return None

    if content == version:
        return None

    if not dry_run:
        with open(path, "w", encoding="utf-8") as f:
            f.write(version + "\n")

    return content


def stamp_config_file(path: Path, version: str, dry_run: bool) -> str | None:
    if path.suffix == ".json":
        return stamp_json_file(path, version, dry_run)
    elif path.suffix == ".toml":
        return stamp_toml_file(path, version, dry_run)
    elif path.name == "VERSION":
        return stamp_version_file(path, version, dry_run)
    return None


def stamp_changelog(root: Path, version: str, dry_run: bool) -> bool:
    changelog = root / "CHANGELOG.md"
    if not changelog.is_file():
        print("Warning: CHANGELOG.md not found, skipping", file=sys.stderr)
        return False

    with open(changelog, encoding="utf-8") as f:
        lines = f.readlines()

    unreleased_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^## \[Unreleased\]", line):
            unreleased_idx = i
            break

    if unreleased_idx is None:
        print(
            "Warning: no '## [Unreleased]' heading found in CHANGELOG.md, skipping",
            file=sys.stderr,
        )
        return False

    next_heading_idx = None
    for i in range(unreleased_idx + 1, len(lines)):
        if re.match(r"^## ", lines[i]):
            next_heading_idx = i
            break

    content_end = next_heading_idx if next_heading_idx is not None else len(lines)
    section_lines = lines[unreleased_idx + 1 : content_end]
    has_content = any(line.strip() for line in section_lines)

    if not has_content:
        print(
            "Warning: Unreleased section is empty, skipping changelog stamp",
            file=sys.stderr,
        )
        return False

    today_str = date.today().isoformat()
    version_heading = f"## [{version}] - {today_str}\n"

    lines[unreleased_idx] = version_heading

    fresh_unreleased = "## [Unreleased]\n\n"

    known_bugs_idx = None
    for i, line in enumerate(lines):
        if re.match(r"^## Known Bugs", line):
            known_bugs_idx = i
            break

    ai_comment_idx = None
    changelog_heading_idx = None
    for i, line in enumerate(lines):
        if ai_comment_idx is None and re.match(r"^<!-- AI agents:", line):
            ai_comment_idx = i
        if changelog_heading_idx is None and re.match(r"^# Changelog", line):
            changelog_heading_idx = i

    stamped_heading_idx = None
    for i, line in enumerate(lines):
        if line == version_heading:
            stamped_heading_idx = i
            break

    if known_bugs_idx is not None and stamped_heading_idx is not None and known_bugs_idx < stamped_heading_idx:
        kb_content_end = stamped_heading_idx
        while kb_content_end > known_bugs_idx + 1 and not lines[kb_content_end - 1].strip():
            kb_content_end -= 1
        lines = lines[:kb_content_end] + ["\n"] + [fresh_unreleased] + lines[stamped_heading_idx:]
    elif ai_comment_idx is not None:
        insert_at = ai_comment_idx + 1
        lines.insert(insert_at, "\n")
        lines.insert(insert_at + 1, fresh_unreleased)
    elif changelog_heading_idx is not None:
        insert_at = changelog_heading_idx + 1
        lines.insert(insert_at, "\n")
        lines.insert(insert_at + 1, fresh_unreleased)
    else:
        lines.insert(0, fresh_unreleased)

    if not dry_run:
        with open(changelog, "w", encoding="utf-8") as f:
            f.writelines(lines)

    return True


def cmd_version(_args: argparse.Namespace) -> None:
    root = find_project_root(Path(__file__).parent)
    version = compute_calver(root)
    print(version)


def cmd_stamp(args: argparse.Namespace) -> None:
    root = find_project_root(Path(__file__).parent)
    version = args.version if args.version else compute_calver(root)
    dry_run = args.dry_run

    prefix = "Dry run for" if dry_run else "Stamping"
    print(f"{prefix} version {version}...", file=sys.stderr)

    changes_made = False

    if not args.no_changelog:
        changed = stamp_changelog(root, version, dry_run)
        if changed:
            today_str = date.today().isoformat()
            suffix = " (would change)" if dry_run else ""
            print(
                f"  CHANGELOG.md: [Unreleased] -> [{version}] - {today_str}{suffix}",
                file=sys.stderr,
            )
            changes_made = True

    if not args.changelog_only:
        for config_path in discover_config_files(root):
            old_version = stamp_config_file(config_path, version, dry_run)
            if old_version is not None:
                rel = config_path.relative_to(root)
                suffix = " (would change)" if dry_run else ""
                print(f"  {rel}: {old_version} -> {version}{suffix}", file=sys.stderr)
                changes_made = True

    if dry_run:
        print("No files modified (dry run).", file=sys.stderr)
    elif changes_made:
        print("Done.", file=sys.stderr)
    else:
        print("No files needed updating.", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="CalVer versioning and changelog stamping")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version", help="Compute and print the CalVer version")

    stamp_parser = subparsers.add_parser("stamp", help="Stamp version into changelog and config files")
    stamp_parser.add_argument("--version", help="Manual version override")
    stamp_parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")
    stamp_parser.add_argument("--changelog-only", action="store_true", help="Only stamp CHANGELOG.md")
    stamp_parser.add_argument("--no-changelog", action="store_true", help="Skip CHANGELOG.md stamping")

    args = parser.parse_args()

    if args.command == "version":
        cmd_version(args)
    elif args.command == "stamp":
        cmd_stamp(args)


if __name__ == "__main__":
    main()
