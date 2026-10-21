"""requirement_changes copies OpenSpec's requirement matching; this catches it drifting.

Runs only where a real `openspec` with `show --diff` is installed, and skips otherwise.
"""

import json
import shutil
import subprocess
import unittest

from helpers import make_repo, write
from openspeccer.reqdiff import requirement_changes

DELTAS = {
    "auth": (
        "## RENAMED Requirements\n\n"
        "- FROM: `### Requirement: Lockout`\n"
        "- TO: `### Requirement: Account lockout`\n"
        "- FROM: `### Requirement: Account lockout`\n"
        "- TO: `### Requirement: Lockout policy`\n\n"
        "## MODIFIED Requirements\n\n"
        "### Requirement: password  LOGIN\nThe system SHALL accept a passphrase.\n\n"
        "#### Scenario: Passphrase\n- **WHEN** a passphrase is entered\n- **THEN** sign-in succeeds\n\n"
        "### Requirement: Lockout policy ###\nAccounts MUST lock after three failures.\n\n"
        "#### Scenario: Locked\n- **WHEN** three attempts fail\n- **THEN** the account locks\n\n"
        "### Requirement: Ghost\nThe system SHALL haunt.\n\n"
        "#### Scenario: Boo\n- **WHEN** it is dark\n- **THEN** boo\n"
    ),
    "notes": (
        "﻿## Modified requirements\n\n"
        "### Requirement: Kept\nKept text, revised.\n\n"
        "### Stray heading\nabsorbed line\n\n"
        "#### Scenario: K\n- **WHEN** x\n- **THEN** y\n\n"
        "### Requirement: Outside\nNow inside.\n\n"
        "#### Scenario: O\n- **WHEN** x\n- **THEN** y\n"
    ),
    "billing/invoices": (
        "## MODIFIED Requirements\n\n"
        "### Requirement: Totals\nTotals MUST add up to the cent.\n\n"
        "#### Scenario: Sum\n- **WHEN** an invoice is issued\n- **THEN** lines sum to the total\n"
    ),
}


def _changed(lines: list[str]) -> list[str]:
    """Added and removed lines, sorted: difflib and jsdiff can align equal blank lines differently."""
    return sorted(x for x in lines if x[:1] in "+-")


def _cli_changed(diff: str) -> list[str]:
    lines = diff.splitlines()
    start = next((i for i, x in enumerate(lines) if x.startswith("@@")), len(lines))
    return _changed(lines[start:])


class CliParityTest(unittest.TestCase):
    def setUp(self) -> None:
        self.cli = shutil.which("openspec")
        if not self.cli:
            self.skipTest("openspec CLI not installed")
        self.tmp, self.root = make_repo(with_git=False)
        write(
            self.root,
            "openspec/specs/notes/spec.md",
            "# Notes\n\n## Purpose\n\nEdge cases.\n\n## Requirements\n\n"
            "### Requirement: Kept\nKept text.\n\n#### Scenario: K\n- **WHEN** x\n- **THEN** y\n\n"
            "```\n### Requirement: Fenced\n```\n\n"
            "## Notes\n\n### Requirement: Outside\nNot a requirement section.\n",
        )
        for topic, text in DELTAS.items():
            write(self.root, f"openspec/changes/review-me/specs/{topic}/spec.md", text)
        write(
            self.root,
            "openspec/changes/review-me/proposal.md",
            "## Why\n\nParity.\n\n## What Changes\n\n- Rework auth and billing requirements.\n",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_matches_openspec_show_diff(self) -> None:
        cli = self.cli
        assert cli

        def run(*args: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run([cli, *args], cwd=self.root, capture_output=True, text=True, timeout=30)

        if "--diff" not in run("show", "--help").stdout:
            self.skipTest("installed openspec has no `show --diff`")
        out = run("show", "review-me", "--json", "--diff")
        self.assertEqual(out.returncode, 0, out.stdout[:300] + out.stderr[:300])
        theirs = {
            (d["spec"], d["requirement"]["name"]): (_cli_changed(d.get("diff") or ""), bool(d.get("warning")))
            for d in json.loads(out.stdout)["deltas"]
            if d["operation"] == "MODIFIED"
        }
        ours = {}
        for topic, text in DELTAS.items():
            main = (self.root / "openspec" / "specs" / topic / "spec.md").read_text()
            for r in requirement_changes(text, main):
                body = _changed([x["t"] + x["text"] for x in r["lines"]])
                ours[(topic, r["name"])] = (body, not (r["found"] and r["exact"]))
        self.assertEqual(len(theirs), 6)
        self.assertEqual(ours, theirs)


if __name__ == "__main__":
    unittest.main()
