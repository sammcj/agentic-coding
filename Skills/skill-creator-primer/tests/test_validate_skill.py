#!/usr/bin/env python3
"""Tests for scripts/validate_skill.py.

Stdlib unittest, no third-party runner, so this works wherever the validator's
own --report-only path works. PyYAML-dependent paths (lint) are skipped when
PyYAML is absent rather than failing.

Run: python3 -m unittest discover -s tests -v
"""

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate_skill as vs  # noqa: E402  # pyright: ignore[reportMissingImports]

# Long enough to clear the 30-word description floor the linter enforces, so fixtures exercise the token/structure paths
# rather than tripping that check.
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
            _, skill_blobs, ref_blobs, long_code, _dense = vs._structure(build_skill(Path(tmp), body))
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

    # Findings carry an inclusive line span so a caller rendering the source can mark the whole unit. The fixture's
    # frontmatter puts the first body line at 6.
    def test_wrapped_blob_reports_its_first_and_last_line(self):
        body = "# T\n\n" + "\n".join(["ten short words on this line to build the unit up"] * 12)
        skill_blobs, _, _ = self.blobs(body + "\n")
        _size, _path, first, last, _opening = skill_blobs[0]
        self.assertEqual((first, last), (8, 19))

    def test_code_fence_spans_opening_to_closing_line(self):
        fence = "\n".join(f"line {n}" for n in range(vs.CODE_FENCE_LINES + 5))
        _, _, long_code = self.blobs(f"# T\n\n```\n{fence}\n```\n")
        _size, _path, first, last, _opening = long_code[0]
        self.assertEqual((first, last), (8, 24))


class FillerDetectionTests(unittest.TestCase):
    """Lexical no-ops are a SIGNAL, so precision matters more than recall: a
    false hit costs a reviewing agent's attention on prose that is already fine."""

    def filler(self, body: str):
        with tempfile.TemporaryDirectory() as tmp:
            return vs._filler(build_skill(Path(tmp), body))

    def categories(self, body: str) -> list[str]:
        return [category for category, _, _, _ in self.filler(body)]

    def test_sentence_initial_filler_is_flagged(self):
        self.assertEqual(
            self.categories("# T\n\nRun the build. Additionally, check the logs.\n"),
            ["opener"],
        )

    def test_opener_word_mid_sentence_is_not_flagged(self):
        """'Overall' inside a clause is ordinary English, not a filler opener."""
        self.assertEqual(self.categories("# T\n\nReport the overall token count.\n"), [])

    def test_puffery_adjective_is_flagged(self):
        self.assertEqual(self.categories("# T\n\nWrite a comprehensive report.\n"), ["puffery"])

    def test_filler_verb_is_flagged(self):
        self.assertEqual(self.categories("# T\n\nLeverage the cache for speed.\n"), ["filler-verb"])

    def test_noun_sense_of_a_filler_verb_is_not_flagged(self):
        """Skills name a test or eval harness constantly; only the verb is slop."""
        self.assertEqual(self.categories("# T\n\nRun it against the eval harness.\n"), [])
        self.assertEqual(self.categories("# T\n\nHarness the power of caching.\n"), ["filler-verb"])

    def test_negation_antithesis_is_flagged(self):
        self.assertEqual(
            self.categories("# T\n\nIt's not a linter, it's a budget check.\n"),
            ["negation-antithesis"],
        )

    def test_plain_negation_is_not_antithesis(self):
        """'X, not Y' states the claim already; only the two-clause reversal is slop."""
        self.assertEqual(self.categories("# T\n\nGate on tokens, not on prose shape.\n"), [])

    def test_fenced_code_is_skipped(self):
        body = "# T\n\n```\nleverage = comprehensive_robust()\n```\n"
        self.assertEqual(self.filler(body), [])

    def test_inline_code_is_skipped(self):
        """A flag or identifier named after a filler word is not prose."""
        self.assertEqual(self.categories("# T\n\nPass `--comprehensive` to widen it.\n"), [])

    def test_prose_either_side_of_inline_code_still_scans(self):
        body = "# T\n\nRun `build.py` first. Additionally, check `logs`.\n"
        self.assertEqual(self.categories(body), ["opener"])

    def test_finding_carries_its_location(self):
        category, path, lineno, hit = self.filler("# T\n\nDelve into the logs.\n")[0]
        self.assertEqual((category, path, hit), ("filler-verb", "SKILL.md", "Delve"))
        self.assertEqual(lineno, 8)

    def test_clean_body_reports_nothing(self):
        self.assertEqual(self.filler(f"# T\n\n{words(60)}\n"), [])

    def test_filler_lands_in_signals_not_facts(self):
        """Judgement call, never a gate: a skill may mean 'robust' literally."""
        with tempfile.TemporaryDirectory() as tmp:
            skill = build_skill(Path(tmp), "# T\n\nLeverage the comprehensive cache.\n")
            text, rating, _, _ = vs.build_report(skill)
        signals = text.split("SIGNALS")[1]
        self.assertIn("Lexical no-ops (2)", signals)
        self.assertNotIn("Lexical no-ops", text.split("SIGNALS")[0])
        self.assertEqual(rating, "Great")

    def test_listing_groups_one_line_per_term(self):
        """The agent fixes a word everywhere at once, so repeats must not each
        cost a line of report."""
        group = [("puffery", "SKILL.md", n, "Robust") for n in range(4)]
        out = vs._filler_listing(group)
        self.assertEqual(len(out), 1)
        self.assertIn('"robust" x4', out[0])
        self.assertIn("SKILL.md:0", out[0])

    def test_listing_dedupes_repeats_on_one_line(self):
        group = [("puffery", "SKILL.md", 9, "robust")] * 2
        self.assertEqual(vs._filler_listing(group)[0].count("SKILL.md:9"), 1)

    def test_listing_caps_locations_per_term(self):
        group = [("puffery", "SKILL.md", n, "robust") for n in range(vs.FILLER_LOCATIONS_MAX + 3)]
        self.assertIn("+3 more", vs._filler_listing(group)[0])

    def test_listing_truncates_past_the_term_cap(self):
        group = [("puffery", "SKILL.md", n, f"term{n}") for n in range(vs.FILLER_LIST_MAX + 2)]
        out = vs._filler_listing(group)
        self.assertEqual(len(out), vs.FILLER_LIST_MAX + 1)
        self.assertIn("+2 more terms", out[-1])


class AmericanismTests(unittest.TestCase):
    """Australian spelling is the house style. Same precision-over-recall rule as
    the no-ops: a word that names a thing is not a spelling to fix."""

    def terms(self, body: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            return [hit.lower() for category, _, _, hit in vs._filler(build_skill(Path(tmp), body))
                    if category == "americanism"]

    def test_the_ise_family_is_flagged_across_its_forms(self):
        self.assertEqual(
            self.terms("# T\n\nNormalize it, then organized and summarizing the optimization.\n"),
            ["normalize", "organized", "summarizing", "optimization"],
        )

    def test_the_yse_family_is_flagged(self):
        self.assertEqual(self.terms("# T\n\nAnalyze it while analyzing the rest.\n"),
                         ["analyze", "analyzing"])

    def test_a_prefix_does_not_hide_the_stem(self):
        self.assertEqual(self.terms("# T\n\nReorganize and deserialize the input.\n"),
                         ["reorganize", "deserialize"])

    def test_the_australian_form_is_not_flagged(self):
        body = ("# T\n\nNormalise it, analyse the colour and behaviour, then centre "
                "the labelled panel and organise the visualisation.\n")
        self.assertEqual(self.terms(body), [])

    def test_our_and_doubled_l_families_are_flagged(self):
        self.assertEqual(
            self.terms("# T\n\nThe color and behavior of a labeled, cancelled panel.\n"),
            ["color", "behavior", "labeled"],
        )

    def test_an_agent_noun_is_a_component_name_not_a_spelling(self):
        # Measured over the corpus, `analyzer` and `optimizer` almost always carry a
        # tool's name into prose; respelling would rename the thing.
        self.assertEqual(self.terms("# T\n\nRun the analyzer, then the optimizer.\n"), [])

    def test_words_whose_form_turns_on_sense_are_left_alone(self):
        # `dialog` is Claude Code's own permission dialog and the HTML element;
        # `catalog` names a published thing; `program` is Australian in computing.
        body = "# T\n\nOpen the dialog, read the catalog, run the program, load the tokenizer.\n"
        self.assertEqual(self.terms(body), [])

    def test_a_lookalike_word_is_not_a_false_positive(self):
        body = "# T\n\nCheck the sizes, the prized capsized resized output, and the size.\n"
        self.assertEqual(self.terms(body), [])

    def test_inline_code_and_fences_are_skipped(self):
        self.assertEqual(self.terms("# T\n\nPass `--normalize` to it.\n"), [])
        self.assertEqual(self.terms("# T\n\n```\nnormalize(color)\n```\n"), [])

    def test_the_report_lists_spellings_apart_from_no_ops(self):
        # The fix differs - one word is cut, the other respelled - so one line each.
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# T\n\nA comprehensive plan to normalize the color.\n")
            text, _rating, _advice, _within = vs.build_report(skill_dir)
        self.assertIn("Lexical no-ops (1)", text)
        self.assertIn("American spellings (2)", text)

    def test_the_report_carries_the_caveat_on_the_spelling_line(self):
        # A possible finding is a read, not a fix, and the agent reading the text report has no page to tell it so.
        with tempfile.TemporaryDirectory() as tmp:
            text, *_ = vs.build_report(build_skill(Path(tmp), "# T\n\nNormalize the color.\n"))
        line = next(x for x in text.splitlines() if "American spellings" in x)
        self.assertIn("? " + vs.POSSIBLE["americanism"], line)

    def test_every_word_lands_on_the_right_side(self):
        # The second list is the point: a rule that fires on rigorous, sizing or dialogue costs a lookup every time.
        # Add to KEEP before widening a pattern.
        rule = dict(vs._SPELLING_RULES)["americanism"]
        missed = [w for w in CATCH.split() if not rule.search(w)]
        false = [w for w in KEEP.split() if rule.search(w)]
        self.assertEqual(missed, [])
        self.assertEqual(false, [])

    def test_the_izable_and_izational_suffixes_are_flagged(self):
        self.assertEqual(self.terms("# T\n\nAn organizational, customizable, parallelizable step.\n"),
                         ["organizational", "customizable", "parallelizable"])


# Words the americanism rule must catch, and words it must not. The exclusions the primer chose on measurement
# (agent nouns, the -log family, tokenize, program, licence/practice, math, harbor, distill) sit in KEEP.
CATCH = """
organize organizes organized organizing organization organizations organizational
realize realized recognize recognized prioritize prioritized customizable
normalize serialize sanitize standardization Organization parallelize
analyze analyzed analyzing paralyzed catalyzed
color colors colored coloring colorful colorless behavior behavioral behaviors
favor favors favorite favorites favorable honor honors honorable neighbor neighborhood
humor flavor flavors rumors vapor armor armory endeavor
splendor valor savor savory odor candor clamor demeanor fervor parlor tumor
vigor labor ardor glamor rigor Color Behavior
center centers centered centering theater fiber fibers liter kilometers
caliber somber specter scepter luster maneuver maneuvers maneuvering
defense defenses defenseless offense offenses pretense
traveled traveling traveler canceled canceling modeled modeling labeled
labeling signaled signaling fueled totaled counseled counselor marvelous
jewelry woolen enrollment fulfillment installment skillful willful
instill enroll fulfills
aluminum gray grayish mold molded moldy plow plowed smoldering airplane
aging acknowledgment sizable practicing
"""

KEEP = """
size sizes sized sizing resize resized resizing downsize upsize oversize
capsize prize prizes prized maize baize seize seizes seized seizing assize
advise advised revise revised surprise comprise compromise exercise
improvise supervise televise franchise merchandise despise chastise incise
organise organised realise recognised prioritise customisable normalise
analyse analysed paralysed catalyse
colour colours coloured behaviour behavioural favour favourite honour
neighbour humour flavour harbour rumour vapour armour endeavour splendour
valour savour odour candour clamour demeanour fervour parlour tumour vigour
labour ardour glamour rigour
humorous vigorous glamorous laborious clamorous odorous rigorous
laboratory laboratories collaborator elaborate major minor senior junior
prior error mirror doctor actor factor motor sector vector monitor
centre centres centred theatre fibre litre kilometre calibre sombre spectre
lustre manoeuvre metre metres meter meters sceptic sceptical
bluster cluster fluster muster
catalogue catalogues dialogue dialogues monologue epilogue analogue
analogous analogy defence offence pretence defensive offensive
travelled travelling traveller cancelled cancelling modelled modelling
labelled labelling signalled fuelled totalled counselled counsellor
marvellous jewellery woollen enrolment fulfilment instalment skilful wilful
installed installing install fulfilled enrolled distilled instilled
aluminium grey greyish mould moulded plough ploughed smouldering aeroplane
ageing acknowledgement maths sizeable practising programs program artifact
artifacts licence license practice
analyzer optimizer serializer tokenizer tokenize tokenized dialog dialogs catalog
cataloged analog math harbor distill Distill
"""


class DenseRunTests(unittest.TestCase):
    """Consecutive dense units short of a blob: a wall with nowhere to rest."""

    PARA = "dense words that stop just short of the blob threshold " * 9  # 90 words, under the blob line
    ITEM = "- " + "list item words " * 24  # 72 words

    def runs(self, body: str):
        with tempfile.TemporaryDirectory() as tmp:
            return vs._structure(build_skill(Path(tmp), body))[4]

    def test_three_dense_paragraphs_are_a_run(self):
        body = "# T\n\n" + "\n\n".join([self.PARA] * vs.DENSE_RUN) + "\n"
        runs = self.runs(body)
        self.assertEqual(len(runs), 1)
        size, path, first, last, _opening, count, longest, listed = runs[0]
        self.assertEqual((path, count, listed), ("SKILL.md", vs.DENSE_RUN, False))
        self.assertEqual(size, 90 * vs.DENSE_RUN)
        self.assertEqual(longest, 90)
        self.assertEqual((first, last), (8, 8 + 2 * (vs.DENSE_RUN - 1)))

    def test_one_fewer_paragraph_is_not_a_run(self):
        self.assertEqual(self.runs("# T\n\n" + "\n\n".join([self.PARA] * (vs.DENSE_RUN - 1)) + "\n"), [])

    def test_a_paragraph_under_the_floor_is_not_dense(self):
        short = "word " * (vs.DENSE_WORDS - 1)
        self.assertEqual(self.runs("# T\n\n" + "\n\n".join([short] * vs.DENSE_RUN) + "\n"), [])

    def test_list_items_run_sooner_and_at_a_lower_floor(self):
        runs = self.runs("# T\n\n" + "\n".join([self.ITEM] * vs.DENSE_LIST_RUN) + "\n")
        self.assertEqual(len(runs), 1)
        self.assertTrue(runs[0][7])
        self.assertEqual(runs[0][5], vs.DENSE_LIST_RUN)

    def test_a_mixed_run_holds_to_the_paragraph_rule(self):
        # One paragraph and one list item is not a list run, and two units is under the paragraph count.
        self.assertEqual(self.runs("# T\n\n" + self.PARA + "\n\n" + self.ITEM + "\n"), [])

    def test_a_mixed_run_of_three_is_reported_as_units(self):
        body = "# T\n\n" + self.PARA + "\n\n" + self.ITEM + "\n\n" + self.PARA + "\n"
        runs = self.runs(body)
        self.assertEqual((len(runs), runs[0][5], runs[0][7]), (1, 3, False))
        with tempfile.TemporaryDirectory() as tmp:
            text, *_ = vs.build_report(build_skill(Path(tmp), body))
        self.assertIn("(3 units, ", text)

    def test_a_heading_a_fence_and_a_table_row_each_end_a_run(self):
        for wall in ("## Rest", "```\nx\n```", "| a | b |", "> quoted"):
            body = "# T\n\n" + self.PARA + "\n\n" + wall + "\n\n" + "\n\n".join([self.PARA] * 2) + "\n"
            self.assertEqual(self.runs(body), [], wall)

    def test_a_blank_line_does_not_end_a_run(self):
        body = "# T\n\n" + "\n\n\n\n".join([self.PARA] * vs.DENSE_RUN) + "\n"
        self.assertEqual(len(self.runs(body)), 1)

    def test_a_run_made_only_of_blobs_is_left_to_the_blob_list(self):
        blob = "blob words " * 75  # 150 words
        self.assertEqual(self.runs("# T\n\n" + "\n\n".join([blob] * vs.DENSE_RUN) + "\n"), [])

    def test_a_blob_inside_a_run_keeps_the_run_and_names_the_longest(self):
        blob = "blob words " * 80  # 160 words
        body = "# T\n\n" + self.PARA + "\n\n" + blob + "\n\n" + self.PARA + "\n"
        runs = self.runs(body)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0][6], 160)

    def test_the_report_lists_runs_under_signals_with_the_caveat(self):
        body = "# T\n\n" + "\n\n".join([self.PARA] * vs.DENSE_RUN) + "\n"
        with tempfile.TemporaryDirectory() as tmp:
            text, *_ = vs.build_report(build_skill(Path(tmp), body))
        signals = text.split("SIGNALS")[1].split("INFO:")[0]
        self.assertIn("Dense runs (1)", signals)
        self.assertIn("? " + vs.POSSIBLE["dense-run"], signals)
        self.assertRegex(signals, r"SKILL\.md:8-12 \(3 units, 270w, longest 90w\)")


class InvisibleCharacterTests(unittest.TestCase):
    """Characters nobody can see, found wherever they sit - frontmatter and code included."""

    def found(self, body: str, metadata: str = ""):
        with tempfile.TemporaryDirectory() as tmp:
            return vs._invisible(build_skill(Path(tmp), body, metadata=metadata))

    def test_a_no_break_space_is_named_and_placed(self):
        found = self.found("# T\n\nRun\u00a0this.\n")
        self.assertEqual(found, [("SKILL.md", 8, 3, 4, "U+00A0 no-break space")])

    def test_zero_width_and_private_use_are_found_in_code_and_frontmatter(self):
        found = self.found("# T\n\n```\nls\u200b-la\n```\n", metadata="x: a\ue000b\n")
        self.assertEqual([name for *_at, name in found],
                         ["U+E000 private-use character", "U+200B zero-width space"])

    def test_a_leading_bom_is_reported_from_the_bytes(self):
        # utf-8-sig strips it on read, and byte 0 is exactly where a BOM lands and breaks a frontmatter parser.
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# T\n\nShort.\n")
            path = skill_dir / "SKILL.md"
            path.write_bytes(b"\xef\xbb\xbf" + path.read_bytes())
            self.assertEqual(vs._invisible(skill_dir), [("SKILL.md", 1, 0, 0, "U+FEFF byte-order mark")])

    def test_emoji_joiners_are_not_flagged(self):
        self.assertEqual(self.found("# T\n\nA family \U0001f468\u200d\U0001f469 emoji.\n"), [])

    def test_the_report_lists_them_under_facts(self):
        with tempfile.TemporaryDirectory() as tmp:
            text, *_ = vs.build_report(build_skill(Path(tmp), "# T\n\nRun\u00a0this\u00a0now.\n"))
        facts = text.split("FACTS")[1].split("INFO:")[0]
        self.assertIn("Invisible characters (2)", facts)
        self.assertIn('[invisible] "u+00a0 no-break space" x2 - SKILL.md:8', facts)


class DescriptionEnforcementTests(unittest.TestCase):
    """The description rule is the primer's own, not the spec's, and needs only
    PyYAML - so it must not be lost with an optional third-party install."""

    LONG = " ".join(["trigger word"] * 60)

    @unittest.skipIf(vs.yaml is None, "needs PyYAML to parse frontmatter")
    def test_report_only_fails_an_over_length_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# T\n\nShort.\n")
            (skill_dir / "SKILL.md").write_text(
                "---\nname: fixture\ndescription: %s\n---\n\n# T\n\nShort.\n" % self.LONG,
                encoding="utf-8")
            out, passed = vs.validate_one(skill_dir, report_only=True)
        self.assertFalse(passed)
        self.assertIn("Validation failed", "\n".join(out))

    @unittest.skipIf(vs.yaml is None, "needs PyYAML to parse frontmatter")
    def test_report_only_passes_a_normal_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# T\n\nShort.\n")
            _out, passed = vs.validate_one(skill_dir, report_only=True)
        self.assertTrue(passed)

    @unittest.skipIf(vs.yaml is None, "needs PyYAML to parse frontmatter")
    def test_a_folded_scalar_description_is_counted_whole(self):
        # The field is regularly a `>-` block running to a dozen lines, which is
        # what a regex reader gets wrong.
        folded = "---\nname: fixture\ndescription: >-\n" + "".join(
            "  %s\n" % (" ".join(["trigger word"] * 10)) for _ in range(6)) + "---\n\n# T\n\nShort.\n"
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "# T\n\nShort.\n")
            (skill_dir / "SKILL.md").write_text(folded, encoding="utf-8")
            self.assertEqual(vs.description_word_count(vs.skill_description(skill_dir)), 120)

    def test_a_missing_skill_md_reads_as_no_description(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(vs.skill_description(Path(tmp)), "")


class BoldDetectionTests(unittest.TestCase):
    """Bold is a rate, and a rate is only worth reporting when both gates trip.
    The exemptions carry the weight: a bullet lead and a table badge are labels,
    and flagging them would fire on well-shaped skills and reference tables."""

    def bold(self, body: str):
        with tempfile.TemporaryDirectory() as tmp:
            return vs._bold(build_skill(Path(tmp), body))

    def body(self, count: int, padding: int, line: str = "Line %d carries **phrase %d** mid-sentence.") -> str:
        lines = "\n\n".join(line % (n, n) for n in range(count))
        return f"# H\n\n{lines}\n\n{words(padding)}\n"

    def test_mid_sentence_bold_over_both_gates_bands_sloppy(self):
        stats = self.bold(self.body(vs.BOLD_LEAST, 700))
        assert stats is not None
        self.assertEqual(stats["total"], vs.BOLD_LEAST)
        self.assertEqual(stats["band"], "SLOPPY")
        self.assertLess(stats["rate"], vs.BOLD_ABUSED)

    def test_a_high_enough_rate_bands_abused(self):
        stats = self.bold(self.body(24, 700))
        assert stats is not None
        self.assertGreaterEqual(stats["rate"], vs.BOLD_ABUSED)
        self.assertEqual(stats["band"], "ABUSED")

    def test_one_span_short_of_the_count_gate_says_nothing(self):
        # The rate here is far past SLOPPY; the count gate is what keeps a short skill from banding on a handful of
        # spans.
        stats = self.bold(self.body(vs.BOLD_LEAST - 1, 210))
        self.assertIsNone(stats)

    def test_a_short_skill_says_nothing_however_dense(self):
        stats = self.bold(self.body(vs.BOLD_LEAST + 4, 10))
        self.assertIsNone(stats)

    def test_a_bullet_lead_is_exempt_at_any_volume(self):
        body = "# H\n\n" + "\n".join(
            "- **Lead %d.** The rest of the bullet is plain." % n for n in range(40)
        ) + f"\n\n{words(700)}\n"
        self.assertIsNone(self.bold(body))

    def test_a_bold_line_standing_in_for_a_heading_is_exempt(self):
        body = "# H\n\n" + "\n\n".join("**Section %d**" % n for n in range(40)) + f"\n\n{words(700)}\n"
        self.assertIsNone(self.bold(body))

    def test_a_table_badge_is_not_emphasis(self):
        # Reference tables of options and keybindings carry a trailing badge in a cell ("**macOS only**"); counting
        # those flagged the cleanest skills in the corpus this was calibrated against.
        rows = "\n".join("| `opt-%d` | Boolean | Does a thing. **macOS only** |" % n
                         for n in range(40))
        self.assertIsNone(self.bold(f"# H\n\n| Option | Type | Notes |\n| - | - | - |\n{rows}\n\n{words(700)}\n"))

    def test_bold_inside_a_fence_is_not_counted(self):
        fence = "```md\n" + "\n".join("text **bold %d** here" % n for n in range(40)) + "\n```"
        self.assertIsNone(self.bold(f"# H\n\n{fence}\n\n{words(700)}\n"))

    def test_a_span_locates_the_bold_on_the_raw_line(self):
        # The report marks by these offsets rather than searching the line, so a drift here puts every mark on the wrong
        # words.
        stats = self.bold(self.body(vs.BOLD_LEAST, 700))
        assert stats is not None
        rel, lineno, start, end, phrase = stats["spans"][0]
        line = (Path(rel).name and "Line 0 carries **phrase 0** mid-sentence.")
        self.assertEqual(rel, "SKILL.md")
        self.assertEqual(line[start:end], "**phrase 0**")
        self.assertEqual(phrase, "phrase 0")
        self.assertGreater(lineno, 1)

    def test_the_phrase_is_read_off_the_raw_line_not_the_blanked_one(self):
        # Inline code is blanked before matching so a term inside backticks is skipped; reading the phrase back out of
        # the blanked text would report a run of spaces where the identifier was.
        stats = self.bold(self.body(vs.BOLD_LEAST, 700,
                                    "Line %d runs **the `--flag` switch %d** mid-sentence."))
        assert stats is not None
        self.assertIn("`--flag`", stats["spans"][0][4])

    def test_the_worst_list_ranks_by_repetition(self):
        body = ("# H\n\n" + "\n\n".join(
            ["Text carries **repeated** mid-sentence."] * 5
            + ["Text carries **once** mid-sentence."]) + f"\n\n{words(700)}\n")
        stats = self.bold(body)
        assert stats is not None
        self.assertEqual(stats["worst"][0], ("repeated", 5))

    def test_the_report_names_the_band_and_the_thresholds(self):
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), self.body(vs.BOLD_LEAST, 700))
            text, _rating, _advice, _within = vs.build_report(skill_dir)
        self.assertIn("Bold SLOPPY", text)
        self.assertIn("abused at %.0f" % vs.BOLD_ABUSED, text)


class ListingTests(unittest.TestCase):
    def test_listing_truncates_past_the_cap(self):
        group = [(100, "SKILL.md", n, n + 2, "opening words here") for n in range(vs.BLOB_LIST_MAX + 3)]
        out = vs._listing(group, "w")
        self.assertEqual(len(out), vs.BLOB_LIST_MAX + 1)
        self.assertIn("+3 more", out[-1])

    def test_listing_shows_every_finding_within_the_cap(self):
        group = [(100, "SKILL.md", n, n + 2, "opening words here") for n in range(vs.BLOB_LIST_MAX)]
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
        # 20 words is a realistic tight description; warning here would be an instruction to pad, which is what the
        # floor was lowered to stop.
        self.assertEqual(vs.description_findings(words(20)), ([], []))

    def test_no_finding_names_a_length_to_aim_for(self):
        for count in (5, vs.DESCRIPTION_WORDS_WARN + 1, vs.DESCRIPTION_WORDS_FAIL + 1):
            errors, warnings = vs.description_findings(words(count))
            for message in errors + warnings:
                self.assertNotIn("aim for", message.lower())
                self.assertNotRegex(message, r"\d+\s*-\s*\d+ words|\d+-\d+\b(?! words)")


class DeclaredBudgetTests(unittest.TestCase):
    """The ceiling is read by regex, not PyYAML, so the nesting it accepts and
    rejects is behaviour the stdlib-only --report-only path depends on."""

    def frontmatter(self, declaration: str, parent: str = "skill-lint") -> str:
        return f"---\nname: x\nmetadata:\n  {parent}:\n    {declaration}\n---\n"

    def test_ceiling_with_justifying_comment_is_read(self):
        text = self.frontmatter("max-load-tokens: 11000 # branchy by design")
        self.assertEqual(vs.declared_token_budget(text), (11000, True))

    def test_ceiling_without_comment_is_unjustified(self):
        self.assertEqual(
            vs.declared_token_budget(self.frontmatter("max-load-tokens: 11000")), (11000, False)
        )

    def test_empty_comment_does_not_justify(self):
        self.assertEqual(
            vs.declared_token_budget(self.frontmatter("max-load-tokens: 11000 #")), (11000, False)
        )

    def test_key_under_another_parent_is_ignored(self):
        """metadata is a free-form bag: another tool's same-named key must not
        silently raise this skill's ceiling."""
        text = self.frontmatter("max-load-tokens: 11000 # someone else's", parent="other-tool")
        self.assertEqual(vs.declared_token_budget(text), (None, False))

    def test_unnested_key_is_ignored(self):
        text = "---\nname: x\nmetadata:\n  max-load-tokens: 11000 # flat\n---\n"
        self.assertEqual(vs.declared_token_budget(text), (None, False))

    def test_sibling_keys_after_the_block_do_not_leak_in(self):
        text = (
            "---\nname: x\nmetadata:\n  skill-lint:\n    unrelated: 1\n"
            "  version: 2026-01-01\n  max-load-tokens: 11000 # outside the block\n---\n"
        )
        self.assertEqual(vs.declared_token_budget(text), (None, False))

    def test_ceiling_found_among_sibling_metadata_keys(self):
        text = (
            "---\nname: x\nmetadata:\n  version: 2026-01-01\n"
            "  skill-lint:\n    max-load-tokens: 11000 # branchy by design\n---\n"
        )
        self.assertEqual(vs.declared_token_budget(text), (11000, True))

    def test_absent_ceiling(self):
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
        meta = "metadata:\n  skill-lint:\n    max-load-tokens: 99000 # deliberately branchy\n"
        lines, rating, advice, _, within = self.report(20000, metadata=meta)
        self.assertEqual(rating, "Poor")
        self.assertTrue(within)
        self.assertEqual(advice, "")
        self.assertIn("within the declared max-load-tokens 99000", lines[0])

    def test_unjustified_budget_is_ignored(self):
        meta = "metadata:\n  skill-lint:\n    max-load-tokens: 99000\n"
        lines, _, advice, _, within = self.report(20000, metadata=meta)
        self.assertFalse(within)
        self.assertNotEqual(advice, "")
        self.assertTrue(any("ignored" in line for line in lines))

    def test_load_over_declared_budget_applies_normal_bands(self):
        meta = "metadata:\n  skill-lint:\n    max-load-tokens: 5000 # too low for this body\n"
        lines, rating, advice, _, within = self.report(20000, metadata=meta)
        self.assertEqual(rating, "Poor")
        self.assertFalse(within)
        self.assertNotEqual(advice, "")
        self.assertTrue(any("Over the declared max-load-tokens" in line for line in lines))

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
        meta = "metadata:\n  skill-lint:\n    max-load-tokens: 99000 # deliberately branchy\n"
        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), f"# T\n\n{words(20000)}\n", metadata=meta)
            result = self.run_validator(skill_dir, "--report-only")
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertIn("within the declared max-load-tokens", result.stdout)

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


class MainPathTests(unittest.TestCase):
    """`.` must validate: skills-ref matches the directory basename against the
    skill name, and an unresolved Path(".") has no basename."""

    def test_relative_dot_is_resolved_before_validation(self):
        seen = []

        def fake_validate_one(skill_dir, **kwargs):
            seen.append(skill_dir)
            return ["ok"], True

        with tempfile.TemporaryDirectory() as tmp:
            skill_dir = build_skill(Path(tmp), "A line.\n")
            cwd = os.getcwd()
            os.chdir(skill_dir)
            try:
                with mock.patch.object(vs, "validate_one", fake_validate_one), mock.patch.object(
                    sys, "argv", ["validate_skill.py", ".", "--report-only"]
                ):
                    with self.assertRaises(SystemExit) as ctx:
                        vs.main()
            finally:
                os.chdir(cwd)
        self.assertEqual(ctx.exception.code, 0)
        self.assertTrue(seen[0].is_absolute())
        self.assertEqual(seen[0].name, "fixture")


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
            f"primer rates {rating} with no declared max-load-tokens covering it",
        )


if __name__ == "__main__":
    unittest.main()
