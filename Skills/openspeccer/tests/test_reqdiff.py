import unittest

from helpers import DELTA, SPEC
from openspeccer.reqdiff import line_diff, requirement_changes


def changed(lines: list[dict]) -> list[str]:
    return [f"{x['t']}{x['text']}" for x in lines if x["t"] in "+-"]


def modified(name: str, body: str) -> str:
    return f"## MODIFIED Requirements\n\n### Requirement: {name}\n{body}\n"


class RequirementChangesTest(unittest.TestCase):
    def test_modified_diffs_against_main_block_including_scenarios(self) -> None:
        [r] = requirement_changes(modified("Lockout", "Accounts MUST lock after three failures."), SPEC)
        self.assertEqual(
            (r["name"], r["base_name"], r["found"], r["exact"]), ("Lockout", "Lockout", True, True)
        )
        self.assertEqual(
            changed(r["lines"]),
            ["-Accounts MUST lock after five failures.", "+Accounts MUST lock after three failures."],
        )
        self.assertEqual((r["added"], r["removed"]), (1, 1))

    def test_main_block_ends_at_next_requirement_and_keeps_its_scenarios(self) -> None:
        [r] = requirement_changes(modified("Password login", "The system SHALL accept a password."), SPEC)
        removed = changed(r["lines"])
        self.assertIn("-#### Scenario: Wrong password", removed)
        self.assertNotIn("-### Requirement: Lockout", removed)
        self.assertTrue(all(line.startswith("-") for line in removed))

    def test_only_modified_requirements_are_diffed(self) -> None:
        self.assertEqual(requirement_changes(DELTA, SPEC), [])

    def test_case_or_spacing_mismatch_is_flagged_inexact(self) -> None:
        [r] = requirement_changes(modified("password  LOGIN", "Changed."), SPEC)
        self.assertEqual((r["found"], r["exact"], r["base_name"]), (True, False, "Password login"))

    def test_missing_requirement_or_main_spec_is_not_found(self) -> None:
        for main in (SPEC, None):
            [r] = requirement_changes(modified("Ghost", "Boo."), main)
            self.assertEqual((r["found"], r["lines"]), (False, []))

    def test_renamed_and_modified_looks_up_old_name(self) -> None:
        delta = (
            "## RENAMED Requirements\n\n"
            "- FROM: `### Requirement: Lockout`\n"
            "- TO: `### Requirement: Account lockout`\n\n"
            + modified("Account lockout ###", "Accounts MUST lock after five failures.")
        )
        [r] = requirement_changes(delta, SPEC)
        self.assertEqual((r["name"], r["base_name"], r["found"]), ("Account lockout", "Lockout", True))
        self.assertEqual(
            changed(r["lines"]), ["-### Requirement: Lockout", "+### Requirement: Account lockout ###"]
        )

    def test_rename_chain_resolves_to_original_name(self) -> None:
        delta = (
            "## RENAMED Requirements\n\n"
            "- FROM: `### Requirement: Lockout`\n- TO: `### Requirement: Lock2`\n"
            "- FROM: `### Requirement: Lock2`\n- TO: `### Requirement: Lock3`\n\n" + modified("Lock3", "New.")
        )
        [r] = requirement_changes(delta, SPEC)
        self.assertEqual((r["found"], r["base_name"]), (True, "Lockout"))

    def test_main_requirements_only_count_under_requirements_section(self) -> None:
        main = "## Requirements\n\n### Requirement: A\nOld.\n\n## Notes\n\n### Requirement: B\nOld.\n"
        [r] = requirement_changes(modified("B", "New."), main)
        self.assertFalse(r["found"])

    def test_block_runs_to_next_requirement_or_section_whatever_its_headings(self) -> None:
        main = "## Requirements\n\n### Requirement: A\nOld.\n"
        [r] = requirement_changes(modified("A", "Old.\n\n### Stray\nextra line"), main)
        self.assertEqual(changed(r["lines"]), ["+", "+### Stray", "+extra line"])

    def test_section_titles_match_whole_and_ignore_case(self) -> None:
        main = "## Requirements\n\n### Requirement: A\nOld.\n"
        [r] = requirement_changes("## Modified requirements\n\n### Requirement: A\nNew.\n", main)
        self.assertTrue(r["found"])
        self.assertEqual(requirement_changes("## MODIFIED stuff\n\n### Requirement: A\nNew.\n", main), [])

    def test_requirement_header_in_fence_is_ignored(self) -> None:
        main = "## Requirements\n\n### Requirement: A\nOld.\n```\n### Requirement: B\n```\n"
        [r] = requirement_changes(modified("B", "New."), main)
        self.assertFalse(r["found"])

    def test_longer_fence_is_not_closed_by_shorter_one(self) -> None:
        main = "## Requirements\n\n### Requirement: A\n````md\n```\n### Requirement: B\n```\n````\n"
        [r] = requirement_changes(modified("B", "New."), main)
        self.assertFalse(r["found"])

    def test_leading_bom_and_unspaced_header(self) -> None:
        [r] = requirement_changes("﻿## MODIFIED Requirements\n\n###Requirement: Lockout\nNew.\n", SPEC)
        self.assertTrue(r["found"])

    def test_line_diff_keeps_content_lines_that_look_like_headers(self) -> None:
        d = line_diff("a\n---\nb\n", "a\nb\n+++\n")
        self.assertEqual((d["removed"], d["added"]), (1, 1))


if __name__ == "__main__":
    unittest.main()
