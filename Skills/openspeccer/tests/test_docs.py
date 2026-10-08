import unittest

from helpers import DELTA, SPEC
from openspeccer.docs import count_tasks, parse_spec, parse_tasks


class TasksTest(unittest.TestCase):
    def test_sections_counts_and_state(self) -> None:
        t = parse_tasks("## 1. Setup\n\n- [x] a\n- [ ] b\n\n## 2. Ship\n\n* [X] c\n")
        self.assertEqual((t.done, t.total), (2, 3))
        self.assertEqual([s.title for s in t.sections], ["1. Setup", "2. Ship"])
        self.assertEqual([(i.text, i.done) for i in t.sections[0].items], [("a", True), ("b", False)])

    def test_indented_checkbox_is_part_of_parent_text(self) -> None:
        t = parse_tasks("- [ ] parent\n  - [x] child\n")
        self.assertEqual(t.total, 1)
        self.assertEqual(t.sections[0].items[0].text, "parent\n- [x] child")

    def test_continuation_and_its_end(self) -> None:
        t = parse_tasks(
            "- [ ] first line\nlazy continuation\n\n  indented after blank\n\nstandalone prose\n- [ ] next\n"
        )
        items = t.sections[0].items
        self.assertEqual(items[0].text, "first line\nlazy continuation\n\nindented after blank")
        self.assertEqual(items[1].text, "next")

    def test_column_zero_block_opener_ends_task(self) -> None:
        t = parse_tasks("- [ ] task\n# Heading\n- [ ] other\n")
        self.assertEqual([s.title for s in t.sections], [None, "Heading"])

    def test_checkbox_in_fence_not_counted(self) -> None:
        text = "- [ ] real\n\n```\n- [x] example\n```\n"
        self.assertEqual(parse_tasks(text).total, 1)
        self.assertEqual(count_tasks(text), (0, 1))

    def test_crlf(self) -> None:
        self.assertEqual(count_tasks("- [x] a\r\n- [ ] b\r\n"), (1, 2))


class SpecDocTest(unittest.TestCase):
    def test_structure(self) -> None:
        doc = parse_spec(SPEC)
        self.assertEqual(doc.title, "Auth")
        self.assertEqual([g.heading for g in doc.groups], ["Purpose", "Requirements"])
        self.assertEqual(doc.groups[0].body, "Users sign in.")
        reqs = doc.groups[1].blocks
        self.assertEqual(
            [(b.kind, b.name) for b in reqs], [("requirement", "Password login"), ("requirement", "Lockout")]
        )
        self.assertEqual([c.name for c in reqs[0].children], ["Correct password", "Wrong password"])
        self.assertEqual(reqs[0].body, "The system SHALL accept a password.")
        self.assertIn("**THEN** sign-in fails", reqs[0].children[1].body)
        self.assertEqual(doc.requirement_count, 2)

    def test_delta_operation_and_unique_anchors(self) -> None:
        doc = parse_spec(DELTA + "\n## MODIFIED Requirements\n\n### Requirement: Passkeys\nChanged.\n")
        self.assertEqual([g.op for g in doc.groups], ["ADDED", "MODIFIED"])
        anchors = [b.anchor for g in doc.groups for b in g.blocks]
        self.assertEqual(anchors, ["requirement-passkeys", "requirement-passkeys-1"])

    def test_headings_inside_fences_ignored(self) -> None:
        doc = parse_spec("## Requirements\n\n### Requirement: A\n```\n### Requirement: fake\n```\n")
        self.assertEqual(doc.requirement_count, 1)
        self.assertIn("fake", doc.groups[0].blocks[0].body)


if __name__ == "__main__":
    unittest.main()
