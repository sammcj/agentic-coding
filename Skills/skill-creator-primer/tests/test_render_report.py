#!/usr/bin/env python3
"""Tests for scripts/render_report.py.

Stdlib unittest, no third-party runner. The renderer itself is stdlib-only, so
every test here runs under plain python3; the one PyYAML-dependent path (the
spec cell) is exercised by forcing the absent-dependency branch rather than by
requiring the dependency.

Run: python3 -m unittest discover -s tests -v
"""

import contextlib
import importlib.util
import io
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import render_report as rr  # noqa: E402  # pyright: ignore[reportMissingImports]
import validate_skill as vs  # noqa: E402  # pyright: ignore[reportMissingImports]

from test_validate_skill import build_skill  # noqa: E402  # pyright: ignore[reportMissingImports]

# The real void set only. The page's bars, ticks and gauge markers are <i>, <b>,
# <s>, <u> and <em>, which do carry end tags, so exempting them would let an
# unclosed one through the balance check unseen.
VOID = {"meta", "br", "hr", "img", "link", "input"}

# A paragraph past BLOB_WORDS, wrapped over several source lines, so the blob it
# produces spans a line range rather than a single line.
BLOB = "\n".join(["filler words repeated to clear the blob threshold on purpose"] * 14)

# A fence past CODE_FENCE_LINES, so the code finding also spans a range.
FENCE = "```python\n" + "\n".join(f"x{n} = {n}" for n in range(12)) + "\n```"


class Balance(HTMLParser):
    """Minimal tag-balance check: the page is written by string concatenation,
    so an unclosed cell is a real regression the browser would silently absorb."""

    def __init__(self):
        super().__init__()
        self.stack: list[str] = []
        self.mismatched: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
        else:
            self.mismatched.append(tag)


def shaded(page: str, kind: str) -> list[int]:
    """The SKILL.md line numbers the page shades with the given class.

    Anchors are keyed by load order; SKILL.md sorts ahead of references/, so a
    fixture's SKILL.md is always file 0.
    """
    return sorted(int(n) for n in re.findall(r'class="l %s" id="L-0-(\d+)"' % kind, page))


class MarkCountTests(unittest.TestCase):
    """The page must agree with the text report, or the two disagree about the
    same skill and the reader cannot tell which is wrong."""

    def render(self, body: str) -> tuple[str, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill_dir = build_skill(Path(tmp.name), body)
        return rr.render(skill_dir), skill_dir

    def test_mark_count_equals_the_filler_finding_count(self):
        body = "# H\n\nA comprehensive and robust and seamless line.\n\nAnother robust line.\n"
        page, skill_dir = self.render(body)
        self.assertEqual(len(re.findall(r"<mark ", page)), len(vs._filler(skill_dir)))

    def test_repeated_term_marks_every_occurrence_on_one_line(self):
        page, _ = self.render("# H\n\nrobust and robust and robust.\n")
        self.assertEqual(len(re.findall(r"<mark ", page)), 3)

    def test_a_term_inside_inline_code_is_not_marked(self):
        # _filler blanks inline code before matching, so a page that re-located
        # terms by searching the raw line would flag an identifier as a no-op.
        page, skill_dir = self.render("# H\n\nUse `robust` mode and the robust option.\n")
        self.assertEqual(len(vs._filler(skill_dir)), 1)
        self.assertEqual(len(re.findall(r"<mark ", page)), 1)
        self.assertIn("<mark data-term=\"robust\">robust</mark> option", page)

    def test_a_sentence_initial_rule_does_not_mark_mid_sentence(self):
        # The opener rule is anchored to a sentence start; the second occurrence
        # here is not a finding and must not be marked.
        page, skill_dir = self.render("# H\n\nAdditionally we go. We additionally note.\n")
        self.assertEqual(len(vs._filler(skill_dir)), 1)
        self.assertEqual(len(re.findall(r"<mark ", page)), 1)

    def test_mark_spans_the_matched_text_exactly(self):
        page, _ = self.render("# H\n\nIt is a comprehensive plan.\n")
        self.assertIn('<mark data-term="comprehensive">comprehensive</mark> plan.', page)

    def test_overlapping_rules_share_one_mark_carrying_both_terms(self):
        # "robust" sits inside the negation-antithesis span. Both are findings and
        # both get a frequency row, so both must resolve to a mark - a row with
        # nothing to highlight fades the whole document and selects nothing.
        page, skill_dir = self.render("# H\n\nIt is not just robust but fast.\n")
        self.assertEqual(len(vs._filler(skill_dir)), 2)
        marks = re.findall(r'<mark data-term="([^"]+)"', page)
        self.assertEqual(len(marks), 1)
        rows = re.findall(r'<tr class="pick" data-term="([^"]+)"', page)
        for term in rows:
            self.assertIn(term, marks[0].split("|"))

    def test_a_term_is_marked_and_ranked_under_the_same_key(self):
        page, _ = self.render("# H\n\nA comprehensive line.\n")
        marked = re.search(r'<mark data-term="([^"]+)"', page)
        assert marked is not None
        self.assertIn('<tr class="pick" data-term="%s"' % marked.group(1), page)

    def test_clean_skill_says_so_and_keeps_the_search_box(self):
        # The page's JS binds unconditionally to #find; dropping the element on a
        # clean skill would break every other interaction on the page.
        page, _ = self.render("# H\n\nA plain line of body text.\n")
        self.assertIn("No lexical no-ops found.", page)
        self.assertIn('id="find"', page)


class SpanShadingTests(unittest.TestCase):
    """Blobs and code fences are shaded across their whole span, which is what
    the end line added to _structure exists for."""

    def render(self, body: str) -> str:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return rr.render(build_skill(Path(tmp.name), body))

    # The fixture's frontmatter and heading put the first body line at 8.
    def test_blob_shades_every_line_of_the_unit(self):
        page = self.render("# H\n\n" + BLOB + "\n")
        self.assertEqual(shaded(page, "blob"), list(range(8, 22)))

    def test_code_fence_shades_opening_through_closing_line(self):
        page = self.render("# H\n\n" + FENCE + "\n")
        self.assertEqual(shaded(page, "code"), list(range(8, 22)))

    def test_short_paragraph_and_short_fence_are_not_shaded(self):
        page = self.render("# H\n\nA short paragraph.\n\n```\none\ntwo\n```\n")
        self.assertEqual(shaded(page, "blob"), [])
        self.assertEqual(shaded(page, "code"), [])

    def test_each_finding_row_jumps_to_the_line_it_names(self):
        page = self.render("# H\n\n" + BLOB + "\n")
        goto = re.findall(r'data-goto="([^"]+)"', page)
        self.assertEqual(goto, ["L-0-8"])
        self.assertIn('id="L-0-8"', page)


class PageIntegrityTests(unittest.TestCase):
    def test_every_tag_closes(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# H\n\n" + BLOB + "\n\n" + FENCE + "\n\nrobust.\n")
            parser = Balance()
            parser.feed(rr.render(skill_dir))
        self.assertEqual(parser.stack, [])
        self.assertEqual(parser.mismatched, [])

    def test_source_text_is_escaped(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# H\n\nUse <script>alert(1)</script> here.\n")
            page = rr.render(skill_dir)
        self.assertNotIn("<script>alert(1)</script>", page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", page)

    def test_paths_differing_only_in_punctuation_get_distinct_anchors(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# H\n\nSee references/a_b.md and references/a-b.md.\n")
            for name in ("a_b.md", "a-b.md"):
                (skill_dir / "references" / name).write_text("# X\n", encoding="utf-8")
            page = rr.render(skill_dir)
        ids = re.findall(r'id="(L-\d+-\d+)"', page)
        self.assertEqual(len(ids), len(set(ids)))

    def test_reference_files_are_rendered_alongside_skill_md(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# H\n\nSee references/extra.md for detail.\n")
            (skill_dir / "references" / "extra.md").write_text("# Extra\n\nrobust.\n", encoding="utf-8")
            page = rr.render(skill_dir)
        self.assertIn("references/extra.md", page)
        self.assertIn("<mark ", page)


class BudgetCellTests(unittest.TestCase):
    def render(self, body: str, metadata: str = "") -> str:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return rr.render(build_skill(Path(tmp.name), body, metadata=metadata))

    def test_band_matches_the_validator_rating(self):
        page = self.render("# H\n\n" + "word " * 40000 + "\n")
        self.assertIn('<div class="band poor">POOR</div>', page)

    def test_a_small_skill_rates_great(self):
        self.assertIn('<div class="band great">GREAT</div>', self.render("# H\n\nShort.\n"))

    def test_justified_ceiling_is_shown_instead_of_the_cure(self):
        page = self.render(
            "# H\n\n" + "word " * 5000 + "\n",
            metadata="metadata:\n  skill-lint:\n    max-load-tokens: 20000 # fixture\n",
        )
        self.assertIn("Within the declared max-load-tokens 20000.", page)

    def test_a_justified_ceiling_is_not_painted_as_a_failure(self):
        # The validator passes a skill inside a justified ceiling, so the band
        # must not contradict the note sitting under it. The body is sized to rate
        # OK on its own, or the assertion would hold without the fix.
        page = self.render(
            "# H\n\n" + "word " * 9000 + "\n",
            metadata="metadata:\n  skill-lint:\n    max-load-tokens: 20000 # fixture\n",
        )
        self.assertIn(">OK</div>", page)
        self.assertIn('<div class="band good">', page)
        self.assertNotIn('<div class="band ok">', page)

    @unittest.skipIf(importlib.util.find_spec("tiktoken") is None, "tiktoken not installed")
    def test_tiktoken_counts_differ_from_the_heuristic(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill_dir = build_skill(Path(tmp.name), "# H\n\n" + "word " * 800 + "\n")
        loads = [re.search(r"(\d+) tokens worst-case load", rr.render(skill_dir, use_tiktoken=flag))
                 for flag in (False, True)]
        self.assertTrue(all(loads))
        self.assertNotEqual(loads[0].group(1), loads[1].group(1))  # pyright: ignore

    def test_every_loadable_file_gets_a_bar(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill_dir = build_skill(Path(tmp.name), "# H\n\nSee references/extra.md.\n")
        (skill_dir / "references" / "extra.md").write_text("# Extra\n", encoding="utf-8")
        page = rr.render(skill_dir)
        self.assertEqual(len(re.findall(r'<div class="bar">', page)), 2)


class SpecCellTests(unittest.TestCase):
    def test_missing_dependency_is_named_rather_than_failing(self):
        original, vs.yaml = vs.yaml, None
        self.addCleanup(lambda: setattr(vs, "yaml", original))
        with tempfile.TemporaryDirectory() as tmp:
            page = rr.render(build_skill(Path(tmp), "# H\n\nShort.\n"))
        self.assertIn("PyYAML is not installed", page)
        self.assertIn("uv run", page)

    def test_lint_exiting_degrades_the_cell_instead_of_killing_the_render(self):
        # lint() calls sys.exit on a missing or partial skills-ref. Catching the
        # exit, rather than probing for the import, is what keeps the page alive.
        def explode(_skill_dir):
            print("Error: dependencies not found. Run this script with uv:")
            raise SystemExit(1)

        original, vs.lint = vs.lint, explode
        self.addCleanup(lambda: setattr(vs, "lint", original))
        leaked = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp:
            with contextlib.redirect_stdout(leaked):
                page = rr.render(build_skill(Path(tmp), "# H\n\nShort.\n"))
        self.assertIn("skills-ref is not installed", page)
        # The CLI's stdout is the report path alone, so lint's hint stays swallowed.
        self.assertEqual(leaked.getvalue(), "")

    def test_a_partial_skills_ref_degrades_rather_than_killing_the_render(self):
        # A present-but-incomplete skills-ref raises ImportError, not
        # ModuleNotFoundError, so it escapes lint()'s own handler.
        def partial(_skill_dir):
            raise ImportError("cannot import name 'validator' from 'skills_ref'")

        original, vs.lint = vs.lint, partial
        self.addCleanup(lambda: setattr(vs, "lint", original))
        with tempfile.TemporaryDirectory() as tmp:
            page = rr.render(build_skill(Path(tmp), "# H\n\nShort.\n"))
        self.assertIn("skills-ref is not installed", page)

    @unittest.skipIf(vs.yaml is None, "PyYAML not installed")
    def test_spec_findings_returns_findings_or_the_missing_dependency(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = rr.spec_findings(build_skill(Path(tmp), "# H\n\nShort.\n"))
        self.assertTrue(isinstance(result, (str, tuple)))


class CompareCellTests(unittest.TestCase):
    def pairs(self, page):
        """{label: (before, after)} from the before-and-after cell."""
        found = {}
        for block in re.findall(r'<div class="pair">.*?(?=<div class="pair">|$)', page, re.S):
            label = re.search(r"<u>([^<]+)</u>", block)
            was = re.search(r"<em>(\d+)[^<]* before</em>", block)
            now = re.search(r"<em>(\d+)[^<]* after", block)
            if label and was and now:
                found[label.group(1)] = (int(was.group(1)), int(now.group(1)))
        return found

    def test_against_reports_the_baseline_before_and_the_subject_after(self):
        # Asserting the direction, not just the cell's presence: swapping was/now
        # would leave every string on the page intact.
        with tempfile.TemporaryDirectory() as tmp:
            before = build_skill(Path(tmp), "# H\n\n" + BLOB + "\n\nrobust.\n", name="before")
            after = build_skill(Path(tmp), "# H\n\nShort.\n", name="after")
            page = rr.render(after, against=before)
        pairs = self.pairs(page)
        self.assertEqual(pairs["blobs"], (1, 0))
        self.assertEqual(pairs["lexical no-ops"], (1, 0))
        self.assertGreater(pairs["SKILL.md tokens"][0], pairs["SKILL.md tokens"][1])

    def test_no_compare_cell_without_against(self):
        with tempfile.TemporaryDirectory() as tmp:
            page = rr.render(build_skill(Path(tmp), "# H\n\nShort.\n"))
        self.assertNotIn("Before and after", page)


class CommandLineTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "render_report.py"), *args],
            capture_output=True, text=True,
        )

    def test_default_output_lands_in_the_temp_dir_named_for_the_skill(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# H\n\nShort.\n", name="named")
            result = self.run_cli(str(skill_dir))
        out = Path(result.stdout.strip())
        self.addCleanup(lambda: out.unlink(missing_ok=True))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(out.name, "named.skill-report.html")
        self.assertEqual(out.parent, Path(tempfile.gettempdir()).resolve())
        self.assertTrue(out.is_file())

    def test_out_flag_writes_where_it_is_told(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# H\n\nShort.\n")
            target = Path(tmp) / "nested" / "report.html"
            result = self.run_cli(str(skill_dir), "-o", str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(target.resolve()))

    def test_out_pointing_at_a_directory_names_the_file_itself(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# H\n\nShort.\n", name="named")
            target = Path(tmp) / "reports"
            target.mkdir()
            result = self.run_cli(str(skill_dir), "-o", str(target))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(Path(result.stdout.strip()), (target / "named.skill-report.html").resolve())

    def test_a_directory_without_skill_md_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(tmp)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no SKILL.md", result.stderr)


if __name__ == "__main__":
    unittest.main()
