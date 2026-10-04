"""Tests for the frames command's caption timing and quote lookup (no network)."""

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

_spec = importlib.util.spec_from_file_location(
    "wisdom", Path(__file__).resolve().parent.parent / "scripts" / "wisdom.py"
)
assert _spec and _spec.loader
wisdom = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(wisdom)

# Trimmed from a real auto-caption JSON3 download: word segments with
# tOffsetMs, newline-only separator events, and a repeated phrase.
FIXTURE = {
    "events": [
        {"tStartMs": 0, "dDurationMs": 4000, "segs": [
            {"utf8": "hi"}, {"utf8": " everyone", "tOffsetMs": 300},
            {"utf8": " so", "tOffsetMs": 900}, {"utf8": " recently", "tOffsetMs": 1200}]},
        {"tStartMs": 4000, "dDurationMs": 10, "aAppend": 1, "segs": [{"utf8": "\n"}]},
        {"tStartMs": 4010, "dDurationMs": 3000, "segs": [
            {"utf8": "as"}, {"utf8": " you", "tOffsetMs": 200}, {"utf8": " can", "tOffsetMs": 400},
            {"utf8": " see", "tOffsetMs": 600}, {"utf8": " in", "tOffsetMs": 800},
            {"utf8": " this", "tOffsetMs": 1000}, {"utf8": " diagram", "tOffsetMs": 1200}]},
        {"tStartMs": 754000, "dDurationMs": 3000, "segs": [
            {"utf8": "the"}, {"utf8": " model's", "tOffsetMs": 250},
            {"utf8": " weights", "tOffsetMs": 500}, {"utf8": " as", "tOffsetMs": 900},
            {"utf8": " you", "tOffsetMs": 1100}, {"utf8": " can", "tOffsetMs": 1300},
            {"utf8": " see", "tOffsetMs": 1500}]},
    ]
}


class FramesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        tmp = Path(tempfile.mkdtemp())
        cls.json3 = tmp / "sub.en.json3"
        cls.json3.write_text(json.dumps(FIXTURE), encoding="utf-8")
        cls.timings = wisdom._json3_timings(cls.json3)

    def test_timings_are_per_word_and_skip_blank_segments(self) -> None:
        self.assertEqual(self.timings[1], (300, " everyone"))
        self.assertNotIn("\n", [text for _, text in self.timings])

    def test_exact_quote(self) -> None:
        self.assertEqual(wisdom._locate_quote(self.timings, "in this diagram"), [4810])

    def test_case_punctuation_and_marker_drift(self) -> None:
        self.assertEqual(wisdom._locate_quote(self.timings, "So, Recently... [0:04] As you"), [900])
        self.assertEqual(wisdom._locate_quote(self.timings, "the models weights"), [])
        self.assertEqual(wisdom._locate_quote(self.timings, "the model's  WEIGHTS"), [754000])

    def test_ambiguous_quote_returns_every_match(self) -> None:
        self.assertEqual(wisdom._locate_quote(self.timings, "as you can see"), [4010, 754900])

    def test_missing_quote(self) -> None:
        self.assertEqual(wisdom._locate_quote(self.timings, "this chart"), [])
        self.assertEqual(wisdom._locate_quote(self.timings, "..."), [])

    def test_quote_copied_from_transcript_is_found(self) -> None:
        transcript = wisdom._json3_to_text(self.json3)
        quote = " ".join(transcript.split()[4:10])
        self.assertEqual(wisdom._locate_quote(self.timings, quote), [1200])

    def test_manual_captions_time_words_by_line(self) -> None:
        # Manual captions: one phrase per event, no word offsets, no space between events.
        path = self.json3.with_name("manual.en.json3")
        path.write_text(json.dumps({"events": [
            {"tStartMs": 5000, "segs": [{"utf8": "It shows the graph"}]},
            {"tStartMs": 8000, "segs": [{"utf8": "of costs over time."}]},
        ]}), encoding="utf-8")
        timings = wisdom._json3_timings(path)
        self.assertEqual(wisdom._locate_quote(timings, "the graph of costs"), [5000])
        self.assertEqual(wisdom._locate_quote(timings, "costs over time"), [8000])

    def test_parse_time(self) -> None:
        self.assertEqual(wisdom._parse_time("12:34"), 754000)
        self.assertEqual(wisdom._parse_time("[1:02:03]"), 3723000)
        self.assertEqual(wisdom._parse_time("90"), 90000)
        for bad in ("1:2:3:4", "12m34s", "", "-5"):
            with self.assertRaises(ValueError):
                wisdom._parse_time(bad)

    def test_frame_name(self) -> None:
        self.assertEqual(wisdom._frame_name(754000), "12m34s.jpg")
        self.assertEqual(wisdom._frame_name(3723000), "1h02m03s.jpg")


if __name__ == "__main__":
    unittest.main()
