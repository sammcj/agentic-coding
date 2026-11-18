#!/usr/bin/env python3
"""Tests for scripts/list_descriptions.py. Stdlib unittest; run: python3 -m unittest discover -s tests -v"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import list_descriptions as ld  # noqa: E402  # pyright: ignore[reportMissingImports]


def run(skills: list[tuple[str, str, str]]) -> tuple[int, str]:
    """Write (directory, name, description) skills under one root and return (exit code, stdout)."""
    with tempfile.TemporaryDirectory() as tmp:
        for directory, name, description in skills:
            skill_dir = Path(tmp) / directory
            skill_dir.mkdir()
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: {description}\n---\n\n# T\n", encoding="utf-8"
            )
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = ld.main([tmp])
        return code, out.getvalue()


class SummaryTests(unittest.TestCase):
    def test_the_total_counts_description_characters_across_skills(self):
        code, out = run([("a", "a", "x" * 30), ("b", "b", "y" * 12)])
        self.assertEqual(code, 0)
        self.assertIn("2 skill(s), 42 description characters", out)

    def test_a_set_within_the_list_budget_draws_no_note(self):
        _, out = run([("a", "a", "x" * 30)])
        self.assertNotIn("Over", out)

    def test_a_set_over_the_list_budget_is_noted_without_failing(self):
        half = "x" * (ld.LIST_BUDGET_CHARS // 2 + 1)
        code, out = run([("a", "a", half), ("b", "b", half)])
        self.assertEqual(code, 0)
        self.assertIn(f"Over {ld.LIST_BUDGET_CHARS:,} characters", out)
        self.assertIn("Claude Code", out)

    def test_more_skills_than_copilot_describes_in_full_is_noted(self):
        skills = [(f"s{i}", f"s{i}", "x") for i in range(ld.COPILOT_FULL_DESCRIPTIONS + 1)]
        self.assertIn("GitHub Copilot", run(skills)[1])
        self.assertNotIn("GitHub Copilot", run(skills[:-1])[1])

    def test_two_directories_sharing_a_name_are_reported_together(self):
        _, out = run([("one", "same", "x"), ("two", "same", "y"), ("three", "other", "z")])
        self.assertIn("Duplicate name 'same': one, two", out)
        self.assertNotIn("'other'", out)


if __name__ == "__main__":
    unittest.main()
