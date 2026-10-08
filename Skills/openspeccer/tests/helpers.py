"""Builds throwaway OpenSpec repositories for tests."""

from __future__ import annotations

import os
import subprocess
import tempfile
from pathlib import Path

# Hermetic: never reach a real OpenSpec install. Schemas resolve from the fixture's own
# openspec/schemas/, which is the CLI-unavailable path.
os.environ["OPENSPECCER_OPENSPEC_BIN"] = "openspeccer-test-no-such-cli"

LOOP_SCHEMA = """name: loop
description: Custom loop
artifacts:
  - id: intake
    generates: loop/intake.md
    requires: []
  - id: checks
    generates: loop/checks.md
    requires: [intake]
apply:
  requires: [checks]
  tracks: loop/checks.md
"""

SPEC = """# Auth

## Purpose

Users sign in.

## Requirements

### Requirement: Password login
The system SHALL accept a password.

#### Scenario: Correct password
- **WHEN** the user enters the right password
- **THEN** they are signed in

#### Scenario: Wrong password
- **WHEN** the password is wrong
- **THEN** sign-in fails

### Requirement: Lockout
Accounts MUST lock after five failures.
"""

DELTA = """## ADDED Requirements

### Requirement: Passkeys
The system SHALL accept passkeys.

#### Scenario: Passkey login
- **WHEN** a passkey is presented
- **THEN** the user is signed in
"""


def write(root: Path, rel: str, text: str) -> Path:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return p


def git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-c", "user.email=t@example.com", "-c", "user.name=t", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout


def make_repo(with_git: bool = True) -> tuple[tempfile.TemporaryDirectory, Path]:
    tmp = tempfile.TemporaryDirectory()
    root = Path(tmp.name).resolve() / "repo"
    root.mkdir()
    write(root, "openspec/config.yaml", "schema: spec-driven\n")
    write(root, "openspec/specs/auth/spec.md", SPEC)
    write(
        root,
        "openspec/specs/billing/invoices/spec.md",
        "# Invoices\n\n## Requirements\n\n### Requirement: Totals\nTotals MUST add up.\n",
    )
    # Active: in progress, with a delta for auth.
    write(root, "openspec/changes/add-passkeys/.openspec.yaml", "schema: spec-driven\ncreated: 2026-09-01\n")
    write(root, "openspec/changes/add-passkeys/proposal.md", "## Why\n\nPasskeys are safer.\n")
    write(
        root,
        "openspec/changes/add-passkeys/tasks.md",
        "## 1. Build\n\n- [x] 1.1 Add model\n- [ ] 1.2 Add endpoint\n",
    )
    write(root, "openspec/changes/add-passkeys/specs/auth/spec.md", DELTA)
    # Active: proposal only.
    write(root, "openspec/changes/idea-sso/proposal.md", "## Why\n\nSSO.\n")
    # Archived, complete.
    write(
        root,
        "openspec/changes/archive/2026-08-01-init-auth/.openspec.yaml",
        "schema: spec-driven\ncreated: 2026-07-20\n",
    )
    write(root, "openspec/changes/archive/2026-08-01-init-auth/tasks.md", "- [x] done\n")
    write(root, "openspec/changes/archive/2026-08-01-init-auth/specs/auth/spec.md", DELTA)
    # Active, on a project schema that tracks a non-default file.
    write(root, "openspec/schemas/loop/schema.yaml", LOOP_SCHEMA)
    write(root, "openspec/changes/loop-work/.openspec.yaml", "schema: loop\ncreated: 2026-09-10\n")
    write(root, "openspec/changes/loop-work/loop/intake.md", "# Intake\n")
    write(root, "openspec/changes/loop-work/loop/checks.md", "- [x] a\n- [x] b\n")
    # Agent setup.
    write(root, ".claude/skills/openspec-apply-change/SKILL.md", "---\nname: x\n---\n")
    write(root, ".claude/commands/opsx/apply.md", "apply\n")
    write(root, ".claude/commands/other.md", "not openspec\n")
    if with_git:
        git(root, "init", "-q", "-b", "main")
        git(root, "add", "-A")
        git(root, "commit", "-qm", "init")
    return tmp, root
