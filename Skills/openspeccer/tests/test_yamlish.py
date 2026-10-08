import unittest

from openspeccer.yamlish import YamlError, loads


class YamlishTest(unittest.TestCase):
    def test_flat_mapping_with_scalars(self) -> None:
        self.assertEqual(
            loads("schema: spec-driven\ncreated: 2026-01-02\ncount: 3\nok: true\nnothing: ~\n"),
            {"schema": "spec-driven", "created": "2026-01-02", "count": 3, "ok": True, "nothing": None},
        )

    def test_comments_and_quotes(self) -> None:
        doc = "# header\na: 'it''s' # trailing\nb: \"x: \\u00e9\\n\"\nc: url http://x/#frag\n"
        self.assertEqual(loads(doc), {"a": "it's", "b": "x: é\n", "c": "url http://x/#frag"})

    def test_sequence_of_mappings_with_block_scalars(self) -> None:
        doc = (
            "artifacts:\n"
            "  - id: proposal\n"
            "    generates: proposal.md\n"
            "    instruction: |\n"
            "      line one\n"
            "\n"
            "      line two\n"
            "    requires: []\n"
            "  - id: tasks\n"
            "    requires:\n"
            "      - proposal\n"
            "apply:\n"
            "  requires: [tasks, 'x y']\n"
            "  tracks: tasks.md\n"
        )
        self.assertEqual(
            loads(doc),
            {
                "artifacts": [
                    {
                        "id": "proposal",
                        "generates": "proposal.md",
                        "instruction": "line one\n\nline two\n",
                        "requires": [],
                    },
                    {"id": "tasks", "requires": ["proposal"]},
                ],
                "apply": {"requires": ["tasks", "x y"], "tracks": "tasks.md"},
            },
        )

    def test_sequence_at_key_indent(self) -> None:
        self.assertEqual(loads("requires:\n- a\n- b\nnext: 1\n"), {"requires": ["a", "b"], "next": 1})

    def test_folded_and_chomping(self) -> None:
        self.assertEqual(loads("a: >-\n  one\n  two\n\n  three\n"), {"a": "one two\nthree"})
        self.assertEqual(loads("a: |+\n  keep\n\nb: 1\n"), {"a": "keep\n\n", "b": 1})

    def test_empty_document(self) -> None:
        self.assertIsNone(loads("# only a comment\n"))

    def test_bad_indentation_raises(self) -> None:
        with self.assertRaises(YamlError):
            loads("a: 1\n    b: 2\n")


if __name__ == "__main__":
    unittest.main()
