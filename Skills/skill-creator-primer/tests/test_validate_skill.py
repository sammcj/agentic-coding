#!/usr/bin/env python3
"""Tests for scripts/validate_skill.py.

Stdlib unittest, no third-party runner, so this works wherever the validator's
own --report-only path works. PyYAML-dependent paths (lint) are skipped when
PyYAML is absent rather than failing.

Run: python3 -m unittest discover -s tests -v
"""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_skill as vs  # noqa: E402  # pyright: ignore[reportMissingImports]

# Long enough to clear the 30-word description floor the linter enforces, so
# fixtures exercise the token/structure paths rather than tripping that check.
FIXTURE_DESCRIPTION = (
    "Use this skill when exercising the validator against a synthetic fixture "
    "whose body shape is known in advance, covering the token budget bands, the "
    "structure percentage, and the blob and code fence listings end to end."
)


def build_skill(root: Path, body: str, name: str = "fixture", metadata: str = "") -> Path:
    """Write a minimal valid skill and return its directory."""
    skill_dir = root / name
    (skill_dir / "references").mkdir(parents=True, exist_ok=True)
    frontmatter = f"---\nname: {name}\ndescription: {FIXTURE_DESCRIPTION}\n{metadata}---\n\n"
    (skill_dir / "SKILL.md").write_text(frontmatter + body, encoding="utf-8")
    return skill_dir


def words(count: int) -> str:
    return "word " * count


class ProsePercentageTests(unittest.TestCase):
    """The percentage exists to surface walls of prose, so it must stay quiet on
    tight one-line directives and loud on a genuine paragraph."""

    def pct(self, body: str) -> int | None:
        with tempfile.TemporaryDirectory() as tmp:
            return vs._structure(build_skill(Path(tmp), body))[0]

    def test_one_line_directives_are_not_prose(self):
        body = "# T\n\nRun the build before committing.\n\nCheck the logs when a test fails.\n"
        self.assertEqual(self.pct(body), 0)

    def test_single_long_paragraph_is_prose(self):
        pct = self.pct(f"# T\n\n{words(120)}\n")
        self.assertIsNotNone(pct)
        assert pct is not None
        self.assertGreater(pct, 90)

    def test_wrapped_list_continuation_is_not_prose(self):
        body = f"# T\n\n- a list item that wraps\n  {words(60)}\n"
        self.assertEqual(self.pct(body), 0)

    def test_paragraph_just_under_threshold_is_structure(self):
        self.assertEqual(self.pct(f"# T\n\n{words(vs.PROSE_UNIT_MIN - 1)}\n"), 0)

    def test_table_and_quote_rows_are_structure(self):
        body = f"# T\n\n| a | b |\n| - | - |\n> {words(60)}\n"
        self.assertEqual(self.pct(body), 0)

    def test_fenced_code_is_excluded_from_the_body(self):
        body = f"# T\n\n```\n{words(200)}\n```\n\nOne short directive here.\n"
        self.assertEqual(self.pct(body), 0)


class BlobDetectionTests(unittest.TestCase):
    def blobs(self, body: str):
        with tempfile.TemporaryDirectory() as tmp:
            _, skill_blobs, ref_blobs, long_code = vs._structure(build_skill(Path(tmp), body))
            return skill_blobs, ref_blobs, long_code

    def test_paragraph_over_threshold_is_a_blob(self):
        skill_blobs, _, _ = self.blobs(f"# T\n\n{words(vs.BLOB_WORDS + 5)}\n")
        self.assertEqual(len(skill_blobs), 1)

    def test_oversized_list_item_is_a_blob(self):
        """Form-invariant per unit: a bullet is not an exempt container."""
        skill_blobs, _, _ = self.blobs(f"# T\n\n- {words(vs.BLOB_WORDS + 5)}\n")
        self.assertEqual(len(skill_blobs), 1)

    def test_unit_under_threshold_is_not_a_blob(self):
        skill_blobs, _, _ = self.blobs(f"# T\n\n{words(vs.BLOB_WORDS - 10)}\n")
        self.assertEqual(skill_blobs, [])

    def test_long_code_fence_is_reported(self):
        fence = "\n".join(f"line {n}" for n in range(vs.CODE_FENCE_LINES + 5))
        _, _, long_code = self.blobs(f"# T\n\n```\n{fence}\n```\n")
        self.assertEqual(len(long_code), 1)

    def test_unterminated_fence_still_reported(self):
        fence = "\n".join(f"line {n}" for n in range(vs.CODE_FENCE_LINES + 5))
        _, _, long_code = self.blobs(f"# T\n\n```\n{fence}\n")
        self.assertEqual(len(long_code), 1)


class ListingTests(unittest.TestCase):
    def test_listing_truncates_past_the_cap(self):
        group = [(100, "SKILL.md", n, "opening words here") for n in range(vs.BLOB_LIST_MAX + 3)]
        out = vs._listing(group, "w")
        self.assertEqual(len(out), vs.BLOB_LIST_MAX + 1)
        self.assertIn("+3 more", out[-1])

    def test_listing_shows_every_finding_within_the_cap(self):
        group = [(100, "SKILL.md", n, "opening words here") for n in range(vs.BLOB_LIST_MAX)]
        self.assertEqual(len(vs._listing(group, "w")), vs.BLOB_LIST_MAX)


class DescriptionLengthTests(unittest.TestCase):
    """The bounds are ceilings. A message naming a target range reads as a quota
    and gets padded up to, so no finding may state a length to aim for."""

    def test_over_cap_is_an_error(self):
        errors, warnings = vs.description_findings(words(vs.DESCRIPTION_WORDS_FAIL + 1))
        self.assertEqual(len(errors), 1)
        self.assertEqual(warnings, [])

    def test_over_ceiling_is_a_warning(self):
        errors, warnings = vs.description_findings(words(vs.DESCRIPTION_WORDS_WARN + 1))
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)

    def test_a_short_two_sentence_description_is_clean(self):
        # 20 words is a realistic tight description; warning here would be an
        # instruction to pad, which is what the floor was lowered to stop.
        self.assertEqual(vs.description_findings(words(20)), ([], []))

    def test_no_finding_names_a_length_to_aim_for(self):
        for count in (5, vs.DESCRIPTION_WORDS_WARN + 1, vs.DESCRIPTION_WORDS_FAIL + 1):
            errors, warnings = vs.description_findings(words(count))
            for message in errors + warnings:
                self.assertNotIn("aim for", message.lower())
                self.assertNotRegex(message, r"\d+\s*-\s*\d+ words|\d+-\d+\b(?! words)")


class DeclaredBudgetTests(unittest.TestCase):
    def test_budget_with_justifying_comment_is_read(self):
        text = "---\nname: x\nmetadata:\n  token-budget: 11000 # branchy by design\n---\n"
        self.assertEqual(vs.declared_token_budget(text), (11000, True))

    def test_budget_without_comment_is_unjustified(self):
        text = "---\nname: x\nmetadata:\n  token-budget: 11000\n---\n"
        self.assertEqual(vs.declared_token_budget(text), (11000, False))

    def test_empty_comment_does_not_justify(self):
        text = "---\nname: x\nmetadata:\n  token-budget: 11000 #\n---\n"
        self.assertEqual(vs.declared_token_budget(text), (11000, False))

    def test_absent_budget(self):
        self.assertEqual(vs.declared_token_budget("---\nname: x\n---\n"), (None, False))

    def test_no_frontmatter(self):
        self.assertEqual(vs.declared_token_budget("# just a body\n"), (None, False))


class BudgetReportTests(unittest.TestCase):
    """End-to-end over _budget: the rating bands, where the cure line is routed,
    and the effect of a declared budget."""

    def report(self, tokens: int, metadata: str = "", ref_tokens: int = 0):
        with tempfile.TemporaryDirectory() as tmp:
            body = f"# T\n\n{words(tokens)}\n"
            if ref_tokens:
                body += "\nSee `references/big.md` for detail.\n"
            skill_dir = build_skill(Path(tmp), body, metadata=metadata)
            if ref_tokens:
                (skill_dir / "references" / "big.md").write_text(
                    f"# Big\n\n{words(ref_tokens)}\n", encoding="utf-8"
                )
            return vs._budget(skill_dir)

    def test_small_skill_rates_great_with_no_advice(self):
        _, rating, advice, _, within = self.report(200)
        self.assertEqual(rating, "Great")
        self.assertEqual(advice, "")
        self.assertFalse(within)

    def test_oversized_skill_rates_poor_with_advice(self):
        _, rating, advice, driver_is_main, within = self.report(20000)
        self.assertEqual(rating, "Poor")
        self.assertIn("Poor", advice)
        self.assertTrue(driver_is_main)
        self.assertFalse(within)

    def test_reference_driven_rating_names_the_reference(self):
        """A reference driving the rating is a branch-loaded cost, so the cure
        must name the reference rather than tell the author to thin SKILL.md."""
        _, rating, advice, driver_is_main, _ = self.report(50, ref_tokens=20000)
        self.assertEqual(rating, "Poor")
        self.assertFalse(driver_is_main)
        self.assertIn("big.md", advice)

    def test_justified_budget_suppresses_advice(self):
        meta = "metadata:\n  token-budget: 99000 # deliberately branchy\n"
        lines, rating, advice, _, within = self.report(20000, metadata=meta)
        self.assertEqual(rating, "Poor")
        self.assertTrue(within)
        self.assertEqual(advice, "")
        self.assertIn("within the declared budget 99000", lines[0])

    def test_unjustified_budget_is_ignored(self):
        meta = "metadata:\n  token-budget: 99000\n"
        lines, _, advice, _, within = self.report(20000, metadata=meta)
        self.assertFalse(within)
        self.assertNotEqual(advice, "")
        self.assertTrue(any("ignored" in line for line in lines))

    def test_load_over_declared_budget_applies_normal_bands(self):
        meta = "metadata:\n  token-budget: 5000 # too low for this body\n"
        lines, rating, advice, _, within = self.report(20000, metadata=meta)
        self.assertEqual(rating, "Poor")
        self.assertFalse(within)
        self.assertNotEqual(advice, "")
        self.assertTrue(any("Over the declared budget" in line for line in lines))

    def test_corpus_line_counts_skill_md(self):
        lines, *_ = self.report(50, ref_tokens=200)
        # One reference: line 1 already names every file, so no corpus line.
        self.assertEqual(len(lines), 1)


class CorpusCountTests(unittest.TestCase):
    def test_corpus_line_appears_with_multiple_references_and_counts_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            body = "# T\n\nSee `references/a.md` and `references/b.md` for detail.\n"
            skill_dir = build_skill(Path(tmp), body)
            for name in ("a", "b"):
                (skill_dir / "references" / f"{name}.md").write_text(
                    f"# {name}\n\n{words(50)}\n", encoding="utf-8"
                )
            lines, *_ = vs._budget(skill_dir)
            self.assertEqual(len(lines), 2)
            self.assertIn("across 3 .md file(s), SKILL.md included", lines[1])


class ReferenceDiscoveryTests(unittest.TestCase):
    def refs(self, body: str, extra: dict[str, str]) -> set[str]:
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), body)
            for rel, text in extra.items():
                target = skill_dir / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(text, encoding="utf-8")
            return {p.name for p in vs.referenced_md_files(skill_dir)}

    def test_resources_directory_is_discovered(self):
        """`resources/` and `references/` are used interchangeably in the wild;
        discovery is path-based, so both must resolve."""
        found = self.refs("# T\n\nSee `resources/guide.md`.\n", {"resources/guide.md": "# G\n"})
        self.assertIn("guide.md", found)

    def test_bare_basename_fallback(self):
        found = self.refs("# T\n\nSee api-design.md for detail.\n", {"references/api-design.md": "# A\n"})
        self.assertIn("api-design.md", found)

    def test_housekeeping_files_are_excluded(self):
        found = self.refs("# T\n\nSee CHANGELOG.md and README.md.\n",
                          {"CHANGELOG.md": "# C\n", "README.md": "# R\n"})
        self.assertNotIn("CHANGELOG.md", found)
        self.assertNotIn("README.md", found)

    def test_md_mentions_inside_fences_are_not_loads(self):
        found = self.refs("# T\n\n```\nsee references/example.md\n```\n",
                          {"references/example.md": "# E\n"})
        self.assertNotIn("example.md", found)

    def test_transitive_references_are_followed(self):
        found = self.refs("# T\n\nSee `references/a.md`.\n",
                          {"references/a.md": "# A\n\nSee `references/b.md`.\n",
                           "references/b.md": "# B\n"})
        self.assertIn("b.md", found)


class ExitCodeTests(unittest.TestCase):
    """The report-only path is the post-edit hook's caller, and the full path is
    the gate, so their exit codes are behaviour worth pinning."""

    def run_validator(self, skill_dir: Path, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_skill.py"), *args, str(skill_dir)],
            capture_output=True, text=True,
        )

    def test_report_only_passes_a_healthy_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_validator(build_skill(Path(tmp), f"# T\n\n{words(50)}\n"), "--report-only")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_report_only_fails_on_poor(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_validator(build_skill(Path(tmp), f"# T\n\n{words(20000)}\n"), "--report-only")
            self.assertEqual(result.returncode, 1)

    def test_justified_budget_clears_the_exit_gate(self):
        meta = "metadata:\n  token-budget: 99000 # deliberately branchy\n"
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), f"# T\n\n{words(20000)}\n", metadata=meta)
            result = self.run_validator(skill_dir, "--report-only")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("within the declared budget", result.stdout)

    def test_missing_skill_md_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_validator(Path(tmp), "--report-only")
            self.assertEqual(result.returncode, 1)
            self.assertIn("no SKILL.md", result.stdout + result.stderr)


class MultiSkillRunTests(unittest.TestCase):
    """Multiple skills per invocation: every skill must be reported, in argument
    order, and one bad path must not cost the others their report."""

    def run_validator(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "validate_skill.py"), "--report-only", *args],
            capture_output=True, text=True,
        )

    def test_every_skill_is_reported_in_argument_order(self):
        with tempfile.TemporaryDirectory() as tmp:
            dirs = [
                build_skill(Path(tmp), f"# T\n\n{words(50 * n)}\n", name=f"skill{n}")
                for n in range(1, 6)
            ]
            result = self.run_validator(*(str(d) for d in dirs))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            positions = [result.stdout.index(f"=== {d} ===") for d in dirs]
            self.assertEqual(positions, sorted(positions))
            self.assertIn("5/5 skill(s) passed", result.stdout)

    def test_one_failure_fails_the_run_without_hiding_the_rest(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = build_skill(Path(tmp), f"# T\n\n{words(50)}\n", name="good")
            bad = build_skill(Path(tmp), f"# T\n\n{words(20000)}\n", name="bad")
            result = self.run_validator(str(good), str(bad))
            self.assertEqual(result.returncode, 1)
            self.assertIn("1/2 skill(s) passed", result.stdout)
            self.assertIn("[Great]", result.stdout)
            self.assertIn("[Poor]", result.stdout)

    def test_unusable_path_fails_only_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            good = build_skill(Path(tmp), f"# T\n\n{words(50)}\n", name="good")
            result = self.run_validator(str(Path(tmp) / "nope"), str(good))
            self.assertEqual(result.returncode, 1)
            self.assertIn("does not exist", result.stdout)
            self.assertIn("1/2 skill(s) passed", result.stdout)

    def test_single_skill_output_has_no_header(self):
        """The post-edit hook parses the bare report; a header would be new noise."""
        with tempfile.TemporaryDirectory() as tmp:
            skill = build_skill(Path(tmp), f"# T\n\n{words(50)}\n")
            out = self.run_validator(str(skill)).stdout
            self.assertNotIn("===", out)
            self.assertNotIn("skill(s) passed", out)


class LintTests(unittest.TestCase):
    """Spec checks need PyYAML; skip rather than fail where it is absent."""

    def setUp(self):
        if vs.yaml is None:
            self.skipTest("PyYAML not installed")

    def lint(self, description: str, name: str = "fixture", extra: str = ""):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = Path(tmp) / name
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {name}\ndescription: {description}\n{extra}---\n\n# T\n\nA line.\n",
                encoding="utf-8",
            )
            return vs.lint(skill_dir)

    def test_valid_skill_has_no_errors(self):
        errors, _ = self.lint(FIXTURE_DESCRIPTION)
        self.assertEqual(errors, [])

    def test_over_long_description_errors(self):
        errors, _ = self.lint(" ".join(["word"] * 80))
        self.assertTrue(any("description" in e.lower() for e in errors))

    def test_short_description_warns(self):
        _, warnings = self.lint("Too short.")
        self.assertTrue(any("description" in w.lower() for w in warnings))

    def test_unknown_frontmatter_field_is_a_warning_not_an_error(self):
        """Documented Claude Code extensions and fields newer than this linter
        must not fail a valid skill."""
        errors, warnings = self.lint(FIXTURE_DESCRIPTION, extra="some-future-field: true\n")
        self.assertEqual(errors, [])
        self.assertTrue(warnings)

    def test_flow_style_allowed_tools_parses(self):
        errors, _ = self.lint(FIXTURE_DESCRIPTION, extra="allowed-tools: [Read, Write]\n")
        self.assertEqual(errors, [])


class RealSkillTests(unittest.TestCase):
    """The primer is the validator's own most-exercised subject; if the script
    cannot rate it, the report an agent reads after every edit is broken."""

    def test_primer_validates(self):
        primer = Path(__file__).resolve().parent.parent
        text, rating, _, within_budget = vs.build_report(primer)
        self.assertIn("worst-case load", text)
        self.assertIn(rating, ("Great", "Good", "OK", "Poor"))
        self.assertTrue(
            rating in ("Great", "Good") or within_budget,
            f"primer rates {rating} with no declared budget covering it",
        )


if __name__ == "__main__":
    unittest.main()
