#!/usr/bin/env python3
"""Tests for scripts/render_report.py.

Stdlib unittest, no third-party runner. The renderer itself is stdlib-only, so
every test here runs under plain python3; the one PyYAML-dependent path (the
spec cell) is exercised by forcing the absent-dependency branch rather than by
requiring the dependency.

Run: python3 -m unittest discover -s tests -v
"""

import contextlib
import html
import importlib.util
import io
import re
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from html.parser import HTMLParser
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import render_report as rr  # noqa: E402  # pyright: ignore[reportMissingImports]
import validate_skill as vs  # noqa: E402  # pyright: ignore[reportMissingImports]
from test_validate_skill import build_skill  # noqa: E402  # pyright: ignore[reportMissingImports]

# The real void set only. The page's bars, ticks and gauge markers are <i>, <b>, <s>, <u> and <em>, which do carry end
# tags, so exempting them would let an unclosed one through the balance check unseen.
VOID = {"meta", "br", "hr", "img", "link", "input"}

# A paragraph past BLOB_WORDS, wrapped over several source lines, so the blob it produces spans a line range rather than
# a single line.
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
        # _filler blanks inline code before matching, so a page that re-located terms by searching the raw line would
        # flag an identifier as a no-op.
        page, skill_dir = self.render("# H\n\nUse `robust` mode and the robust option.\n")
        self.assertEqual(len(vs._filler(skill_dir)), 1)
        self.assertEqual(len(re.findall(r"<mark ", page)), 1)
        self.assertIn(">robust</mark> option", page)
        self.assertIn('data-term="robust"', page)

    def test_a_sentence_initial_rule_does_not_mark_mid_sentence(self):
        # The opener rule is anchored to a sentence start; the second occurrence here is not a finding and must not be
        # marked.
        page, skill_dir = self.render("# H\n\nAdditionally we go. We additionally note.\n")
        self.assertEqual(len(vs._filler(skill_dir)), 1)
        self.assertEqual(len(re.findall(r"<mark ", page)), 1)

    def test_mark_spans_the_matched_text_exactly(self):
        page, _ = self.render("# H\n\nIt is a comprehensive plan.\n")
        self.assertIn("It is a <mark ", page)
        self.assertIn(">comprehensive</mark> plan.", page)

    def test_overlapping_rules_share_one_mark_carrying_both_terms(self):
        # "robust" sits inside the negation-antithesis span. Both are findings and both get a frequency row, so both
        # must resolve to a mark - a row with nothing to highlight fades the whole document and selects nothing.
        page, skill_dir = self.render("# H\n\nIt is not just robust but fast.\n")
        self.assertEqual(len(vs._filler(skill_dir)), 2)
        marks = re.findall(r'<mark [^>]*data-term="([^"]+)"', page)
        self.assertEqual(len(marks), 1)
        rows = re.findall(r'<tr class="pick [a-z]+" data-term="([^"]+)"', page)
        for term in rows:
            self.assertIn(term, marks[0].split("|"))

    def test_a_term_is_marked_and_ranked_under_the_same_key(self):
        page, _ = self.render("# H\n\nA comprehensive line.\n")
        marked = re.search(r'<mark [^>]*data-term="([^"]+)"', page)
        assert marked is not None
        self.assertIn('<tr class="pick probable" data-term="%s"' % marked.group(1), page)

    def test_clean_skill_says_so_and_keeps_the_search_box(self):
        # The page's JS binds unconditionally to #find; dropping the element on a clean skill would break every other
        # interaction on the page.
        page, _ = self.render("# H\n\nA plain line of body text.\n")
        self.assertIn("No lexical no-ops, American spellings, bold abuse or invisible characters found.", page)
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
        # The validator passes a skill inside a justified ceiling, so the band must not contradict the note sitting
        # under it. The body is sized to rate OK on its own, or the assertion would hold without the fix.
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
        self.assertEqual(len(re.findall(r'<div class="bar', page)), 2)

    def test_the_largest_file_is_the_one_marked_as_leading(self):
        # `.bar:first-of-type` matched the band div above these rows and reached no bar at all, so the accent never
        # rendered.
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill_dir = build_skill(Path(tmp.name), "# H\n\nSee references/extra.md.\n" + "word " * 400)
        (skill_dir / "references" / "extra.md").write_text("# Extra\n", encoding="utf-8")
        page = rr.render(skill_dir)
        lead = re.search(r'<div class="bar lead"><u>([^<]+)</u>', page)
        self.assertIsNotNone(lead)
        self.assertEqual(lead.group(1), "SKILL.md")  # pyright: ignore


class SpecCellTests(unittest.TestCase):
    def test_missing_dependency_is_named_rather_than_failing(self):
        original, vs.yaml = vs.yaml, None
        self.addCleanup(lambda: setattr(vs, "yaml", original))
        with tempfile.TemporaryDirectory() as tmp:
            page = rr.render(build_skill(Path(tmp), "# H\n\nShort.\n"))
        self.assertIn("PyYAML is not installed", page)
        self.assertIn("uv run", page)

    def test_lint_exiting_degrades_the_cell_instead_of_killing_the_render(self):
        # lint() calls sys.exit on a missing or partial skills-ref. Catching the exit, rather than probing for the
        # import, is what keeps the page alive.
        def explode(_skill_dir):
            print("Error: dependencies not found. Run this script with uv:")
            raise SystemExit(1)

        original, vs.lint = vs.lint, explode
        self.addCleanup(lambda: setattr(vs, "lint", original))
        leaked = io.StringIO()
        with tempfile.TemporaryDirectory() as tmp, contextlib.redirect_stdout(leaked):
            page = rr.render(build_skill(Path(tmp), "# H\n\nShort.\n"))
        self.assertIn("skills-ref is not installed", page)
        # The CLI's stdout is the report path alone, so lint's hint stays swallowed.
        self.assertEqual(leaked.getvalue(), "")

    def test_a_partial_skills_ref_degrades_rather_than_killing_the_render(self):
        # A present-but-incomplete skills-ref raises ImportError, not ModuleNotFoundError, so it escapes lint()'s own
        # handler.
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
        for block in re.findall(r'<div class="pair">.*?(?=<div class="pair">|$)', page, re.DOTALL):
            label = re.search(r"<u>([^<]+)</u>", block)
            was = re.search(r"<em>(\d+)[^<]* before</em>", block)
            now = re.search(r"<em>(\d+)[^<]* after", block)
            if label and was and now:
                found[label.group(1)] = (int(was.group(1)), int(now.group(1)))
        return found

    def test_against_reports_the_baseline_before_and_the_subject_after(self):
        # Asserting the direction, not just the cell's presence: swapping was/now would leave every string on the page
        # intact.
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


class BriefTests(unittest.TestCase):
    """The copied brief is the page's findings as text, for pasting into another
    agent. It must agree with the page and stay small enough to be worth pasting."""

    def brief_of(self, body, metadata=""):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        page = rr.render(build_skill(Path(tmp.name), body, metadata=metadata))
        found = re.search(r'<pre id="brief" hidden>(.*?)</pre>', page, re.DOTALL)
        self.assertIsNotNone(found)
        return html.unescape(found.group(1)), page  # pyright: ignore

    def test_brief_opens_by_telling_the_agent_what_to_do(self):
        text, _ = self.brief_of("# H\n\nA comprehensive plan.\n")
        self.assertTrue(text.startswith("Skill report for fixture."))
        self.assertIn("Load the skill-creator-primer skill", text)
        self.assertIn("Cut words, not behaviour", text)

    def test_every_finding_kind_carries_its_reason(self):
        text, _ = self.brief_of("# H\n\n" + BLOB + "\n\n" + FENCE + "\n\nA robust plan.\n")
        for rule in ("blob", "code", "puffery"):
            self.assertIn(rule, text)
            self.assertIn(rr.WHY[rule], text)

    def test_one_rule_is_one_line_however_often_it_fired(self):
        text, _ = self.brief_of("# H\n\nrobust and robust and comprehensive.\n")
        self.assertEqual(len(re.findall(r"^- puffery,", text, re.MULTILINE)), 1)
        self.assertIn("puffery, 3 uses", text)

    def test_brief_counts_agree_with_the_page(self):
        body = "# H\n\n" + BLOB + "\n\nA robust plan.\n"
        text, page = self.brief_of(body)
        rows = len(re.findall(r'<tr class="pick', page))
        listed = len(re.findall(r"^- ", text, re.MULTILINE))
        self.assertEqual(rows, 2)  # one blob, one term
        self.assertEqual(listed, 2)

    def test_examples_are_capped_per_rule(self):
        fences = "\n\n".join(FENCE for _ in range(rr.BRIEF_EXAMPLES + 3))
        text, _ = self.brief_of("# H\n\n" + fences + "\n")
        line = next(x for x in text.splitlines() if x.startswith("- code,"))
        self.assertIn("code, %d code blocks" % (rr.BRIEF_EXAMPLES + 3), line)
        self.assertEqual(line.count("SKILL.md:"), rr.BRIEF_EXAMPLES)

    def test_budget_cure_appears_only_when_over(self):
        over, _ = self.brief_of("# H\n\n" + "word " * 40000 + "\n")
        self.assertIn(rr.WHY["load"], over)
        under, _ = self.brief_of("# H\n\nShort.\n")
        self.assertNotIn(rr.WHY["load"], under)

    def test_a_justified_ceiling_is_stated_instead_of_the_cure(self):
        text, _ = self.brief_of(
            "# H\n\n" + "word " * 9000 + "\n",
            metadata="metadata:\n  skill-lint:\n    max-load-tokens: 20000 # fixture\n",
        )
        self.assertIn("Within the declared max-load-tokens 20000.", text)
        self.assertNotIn(rr.WHY["load"], text)

    def test_a_clean_skill_says_so(self):
        text, _ = self.brief_of("# H\n\nA plain line of body text.\n")
        self.assertIn("Nothing else flagged.", text)

    def test_brief_is_escaped_into_the_page(self):
        _, page = self.brief_of("# H\n\nUse <script>alert(1)</script> robustly.\n")
        stash = re.search(r'<pre id="brief" hidden>(.*?)</pre>', page, re.DOTALL)
        self.assertNotIn("<script>", stash.group(1))  # pyright: ignore

    def test_the_copy_button_and_its_source_are_both_present(self):
        _, page = self.brief_of("# H\n\nShort.\n")
        self.assertIn('<button id="copy"', page)
        self.assertIn('<pre id="brief" hidden>', page)
        # The fallback path needs execCommand when file:// is not a secure context.
        self.assertIn("navigator.clipboard", page)
        self.assertIn("execCommand", page)


class WhyCaptionTests(unittest.TestCase):
    def render(self, body):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return rr.render(build_skill(Path(tmp.name), body))

    def test_every_rule_the_renderer_reports_has_a_reason(self):
        for _category, _pattern in vs._ALL_TEXT_RULES:
            self.assertIn(_category, rr.WHY, f"no WHY entry for {_category}")
        for rule in ("blob", "code", "load", "spec-error", "spec-warning",
                     "bold-emphasis"):
            self.assertIn(rule, rr.WHY)

    def test_marks_in_the_document_carry_their_reason(self):
        # Clicking a highlighted word has to answer why it is flagged; the mark carried a term but no reason, so the
        # caption fell back to idle.
        page = self.render("# H\n\nA comprehensive plan.\n")
        mark = re.search(r'<mark [^>]*data-term="[^"]*" data-why="([^"]+)"', page)
        self.assertIsNotNone(mark)
        self.assertEqual(html.unescape(mark.group(1)), rr.WHY["puffery"])  # pyright: ignore

    def test_a_shared_mark_carries_both_reasons(self):
        page = self.render("# H\n\nIt is not just robust but fast.\n")
        mark = re.search(r'<mark [^>]*data-term="[^"]*" data-why="([^"]+)"', page)
        why = html.unescape(mark.group(1))  # pyright: ignore
        self.assertIn(rr.WHY["negation-antithesis"], why)
        self.assertIn(rr.WHY["puffery"], why)

    def test_rows_carry_their_reason(self):
        page = self.render("# H\n\n" + BLOB + "\n\nA robust plan.\n")
        self.assertIn('data-why="%s"' % rr.WHY["blob"].replace("'", "&#x27;"), page)
        self.assertIn("puffery", page)
        self.assertIn('<p id="why" class="why">', page)

    def test_an_american_spelling_is_marked_and_ranked_like_any_term(self):
        page = self.render("# H\n\nNormalize the color before analyzing it.\n")
        self.assertEqual(len(re.findall(r"<mark ", page)), 3)
        self.assertIn('<tr class="pick possible" data-term="normalize"', page)
        self.assertIn("americanism", page)

    def test_the_spec_cell_still_checks_the_description_without_skills_ref(self):
        # The description rule is the primer's own and needs only PyYAML. Routing it
        # solely through lint() lost it wherever skills-ref was not installed.
        long_desc = " ".join(["trigger word"] * 60)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill_dir = build_skill(Path(tmp.name), "# H\n\nShort.\n")
        (skill_dir / "SKILL.md").write_text(
            "---\nname: fixture\ndescription: %s\n---\n\n# H\n\nShort.\n" % long_desc,
            encoding="utf-8")
        with unittest.mock.patch.object(vs, "lint", side_effect=SystemExit(1)):
            findings = rr.spec_findings(skill_dir)
        self.assertIsInstance(findings, tuple)
        errors, warnings = findings
        self.assertTrue(any("120 words" in x for x in errors))
        self.assertTrue(any("skills-ref" in x for x in warnings))

    def test_the_copy_button_sits_in_the_footer(self):
        # It belongs on the footer rule beside the date, not over the stat strip:
        # the brief is what you leave with, so it reads at the end of the page.
        page = self.render("# H\n\nA robust plan.\n")
        footer = page.split("<footer>")[1].split("</footer>")[0]
        self.assertIn('id="copy"', footer)
        self.assertNotIn('id="copy"', page.split("</header>")[0])

    def test_the_caption_survives_a_clean_skill(self):
        # The JS binds to #why unconditionally; dropping it would break the page.
        page = self.render("# H\n\nA plain line of body text.\n")
        self.assertIn('id="why"', page)


class BoldReportTests(unittest.TestCase):
    """Bold reaches the page as one row and many marks. The row is the finding;
    the marks are the only way to see the density the row names."""

    BODY = ("# H\n\n"
            + "\n\n".join("Line %d carries **phrase %d** mid-sentence." % (n, n)
                          for n in range(vs.BOLD_LEAST))
            + "\n\n- **Lead.** An exempt bullet lead.\n\n" + "word " * 700 + "\n")

    def render(self, body: str) -> tuple[str, Path]:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill_dir = build_skill(Path(tmp.name), body)
        return rr.render(skill_dir), skill_dir

    def test_every_counted_span_is_marked_and_nothing_else_is(self):
        page, skill_dir = self.render(self.BODY)
        stats = vs._bold(skill_dir)
        assert stats is not None
        self.assertEqual(len(re.findall(r'<mark class="em"', page)), stats["total"])

    def test_the_exempt_bullet_lead_is_not_marked(self):
        # The page marks the spans the scan handed it, so an exemption the detector applied cannot come back on the
        # page.
        page, _ = self.render(self.BODY)
        self.assertIn("- **Lead.** An exempt bullet lead.", page)
        self.assertNotRegex(page, r'<mark [^>]*data-term="bold-emphasis"[^>]*>\*\*Lead\.\*\*')

    def test_the_row_and_the_marks_share_one_selection_key(self):
        page, _ = self.render(self.BODY)
        self.assertIn('<tr class="pick em" data-term="bold-emphasis"', page)
        self.assertIn('<mark class="em" data-conf="" data-term="bold-emphasis"', page)

    def test_the_row_names_the_band_and_the_thresholds(self):
        page, _ = self.render(self.BODY)
        self.assertIn("SLOPPY: ", page)
        self.assertIn("abused at %.0f" % vs.BOLD_ABUSED, page)

    def test_a_no_op_inside_a_bold_shares_one_mark_carrying_both_keys(self):
        # Nesting a mark inside a mark cannot be closed by the single pass, and a row with no mark to reach fades the
        # document and selects nothing.
        body = self.BODY.replace("**phrase 0**", "**a comprehensive phrase**")
        page, _ = self.render(body)
        marks = re.findall(r'<mark [^>]*data-term="([^"]+)"[^>]*>\*\*a comprehensive', page)
        self.assertEqual(len(marks), 1)
        self.assertIn("bold-emphasis", marks[0].split("|"))
        self.assertIn("comprehensive", marks[0].split("|"))

    def test_a_shared_mark_spans_both_findings(self):
        # Here the bold opens first and the no-op runs past it. Merging without extending the end cut the mark off at
        # the closing asterisks, so the rest of the flagged phrase lost its highlight.
        body = self.BODY.replace("Line 0 carries **phrase 0** mid-sentence.",
                                 "It is **not just robust** but fast.")
        page, _ = self.render(body)
        mark = re.search(r'<mark [^>]*data-term="[^"]*"[^>]*>([^<]+)</mark>', page)
        assert mark is not None
        self.assertEqual(html.unescape(mark.group(1)), "**not just robust** but")

    def test_the_brief_carries_the_band_not_just_the_count(self):
        page, _ = self.render(self.BODY)
        brief = html.unescape(re.search(r'<pre id="brief" hidden>(.*?)</pre>',
                                        page, re.DOTALL).group(1))  # pyright: ignore
        self.assertIn("bold-emphasis", brief)
        self.assertIn("SLOPPY", brief)
        self.assertIn(rr.WHY["bold-emphasis"], brief)

    def test_a_clean_skill_shows_no_bold_row(self):
        page, _ = self.render("# H\n\nA plain line of body text.\n")
        self.assertNotIn("bold-emphasis", page.split("<style>")[0]
                         + page.split("</style>")[-1])


class ConfidenceTests(unittest.TestCase):
    """One ramp by confidence: possible marks are yellow and ranked last, certain ones red and first."""

    def render(self, body: str) -> str:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return rr.render(build_skill(Path(tmp.name), body))

    def test_a_no_op_is_probable_and_a_spelling_is_possible(self):
        page = self.render("# H\n\nA comprehensive plan to normalize.\n")
        self.assertIn('data-conf="probable" data-term="comprehensive"', page)
        self.assertIn('data-conf="possible" data-term="normalize"', page)

    def test_possible_rows_rank_below_probable_ones_whatever_their_count(self):
        page = self.render("# H\n\nNormalize the color and the colors. A comprehensive plan.\n")
        rows = re.findall(r'<tr class="pick ([a-z]+)" data-term="([^"]+)"', page)
        self.assertEqual(rows[0], ("probable", "comprehensive"))
        self.assertEqual({c for c, _ in rows[1:]}, {"possible"})

    def test_a_possible_reason_ends_with_its_caveat_everywhere(self):
        page = self.render("# H\n\nNormalize it.\n")
        text = html.unescape(re.search(r'<pre id="brief" hidden>(.*?)</pre>', page, re.DOTALL).group(1))
        self.assertIn("Possible, read before changing:", text)
        self.assertIn(vs.POSSIBLE["americanism"], text)
        self.assertNotIn("Findings, fix these:", text)
        self.assertIn('data-why="%s' % html.escape(rr.WHY["americanism"], quote=True)[:40], page)
        self.assertIn("Possible only: %s." % html.escape(vs.POSSIBLE["americanism"], quote=True), page)

    def test_the_brief_splits_fixes_from_reads(self):
        page = self.render("# H\n\nA comprehensive plan to normalize.\n")
        text = html.unescape(re.search(r'<pre id="brief" hidden>(.*?)</pre>', page, re.DOTALL).group(1))
        fix, maybe = text.index("Findings, fix these:"), text.index("Possible, read before changing:")
        self.assertLess(fix, maybe)
        self.assertLess(text.index("- puffery,"), maybe)
        self.assertGreater(text.index("- americanism,"), maybe)

    def test_the_strip_counts_possible_findings_apart(self):
        page = self.render("# H\n\nA comprehensive plan to normalize the color.\n")
        self.assertIn("<b>1</b><u>findings, 2 possible</u>", page)

    def test_the_legend_is_headed_confidence_with_every_step(self):
        page = self.render("# H\n\nA comprehensive plan.\n")
        self.assertIn("<b>Confidence</b>", page)
        for step in ("possible", "probable", "certain"):
            self.assertIn('class="key k-%s"' % step, page)

    def test_a_shared_mark_takes_the_higher_confidence(self):
        body = ("# H\n\n"
                + "\n\n".join("Line %d carries **phrase %d** mid-sentence." % (n, n) for n in range(vs.BOLD_LEAST))
                + "\n\n" + "word " * 700 + "\n").replace("**phrase 0**", "**a comprehensive phrase**")
        page = self.render(body)
        self.assertRegex(page, r'<mark class="" data-conf="probable" data-term="[^"]*comprehensive[^"]*"')


class DenseRunReportTests(unittest.TestCase):
    PARA = "dense words that stop just short of the blob threshold " * 9

    def render(self, body: str) -> str:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return rr.render(build_skill(Path(tmp.name), body))

    def test_a_run_is_shaded_across_every_unit_and_listed_as_possible(self):
        page = self.render("# H\n\n" + "\n\n".join([self.PARA] * vs.DENSE_RUN) + "\n")
        self.assertEqual(shaded(page, "dense"), [8, 9, 10, 11, 12])
        self.assertRegex(page, r'<tr class="pick dense possible" data-goto="L-0-8"')
        self.assertIn("3 units, longest 90w:", page)

    def test_a_blob_inside_a_run_keeps_its_own_shade(self):
        blob = "blob words " * 80
        page = self.render("# H\n\n" + self.PARA + "\n\n" + blob + "\n\n" + self.PARA + "\n")
        self.assertEqual(shaded(page, "dense"), [8, 9, 11, 12])
        self.assertEqual(shaded(page, "blob"), [10])

    def test_a_shaded_line_carries_its_reason(self):
        page = self.render("# H\n\n" + BLOB + "\n")
        self.assertRegex(page, r'<span class="l blob" id="L-0-8" data-why="%s'
                         % re.escape(html.escape(rr.WHY["blob"], quote=True)[:30]))


class InvisibleMarkTests(unittest.TestCase):
    def render(self, body: str) -> str:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return rr.render(build_skill(Path(tmp.name), body))

    def test_the_mark_shows_the_code_point_and_is_certain(self):
        page = self.render("# H\n\nRun\u00a0this.\n")
        self.assertIn('<mark class="inv" data-conf="certain" data-term="u+00a0 no-break space"', page)
        self.assertRegex(page, r'<mark class="inv"[^>]*>U\+00A0</mark>')

    def test_it_ranks_above_every_other_term(self):
        page = self.render("# H\n\nA comprehensive, comprehensive plan.\u00a0\n")
        rows = re.findall(r'<tr class="pick ([a-z]+)" data-term="([^"]+)"', page)
        self.assertEqual(rows[0], ("certain", "u+00a0 no-break space"))

    def test_an_invisible_inside_a_bold_leaves_the_visible_text_alone(self):
        body = ("# H\n\n"
                + "\n\n".join("Line %d carries **phrase %d** mid-sentence." % (n, n) for n in range(vs.BOLD_LEAST))
                + "\n\n" + "word " * 700 + "\n").replace("**phrase 0**", "**bold\u00a0phrase**")
        page = self.render(body)
        self.assertIn('data-conf="certain" data-term="bold-emphasis|u+00a0 no-break space"', page)
        self.assertIn(">**boldU+00A0phrase**</mark>", page)
        self.assertNotIn("U+002A", page)

    def test_a_leading_bom_shows_its_code_point(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        skill_dir = build_skill(Path(tmp.name), "# H\n\nShort.\n")
        path = skill_dir / "SKILL.md"
        path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
        page = rr.render(skill_dir)
        self.assertRegex(page, r'<mark class="inv" data-conf="certain" data-term="u\+feff byte-order mark"[^>]*>U\+FEFF</mark>')

    def test_it_is_found_inside_a_fence_the_no_ops_skip(self):
        page = self.render("# H\n\n```\nls\u00a0-la\n```\n")
        self.assertIn('data-term="u+00a0 no-break space"', page)


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

    def test_an_unwritable_output_path_is_one_line_not_a_traceback(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# H\n\nShort.\n")
            blocker = Path(tmp) / "file.txt"
            blocker.write_text("not a directory")
            result = self.run_cli(str(skill_dir), "-o", str(blocker / "report.html"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(len(result.stderr.strip().splitlines()), 1)
        self.assertIn("cannot write", result.stderr)
        self.assertIn("Pass -o", result.stderr)

    def test_a_directory_without_skill_md_is_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = self.run_cli(tmp)
        self.assertEqual(result.returncode, 2)
        self.assertIn("no SKILL.md", result.stderr)


if __name__ == "__main__":
    unittest.main()
