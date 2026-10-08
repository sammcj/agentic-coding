import unittest

from openspeccer.schemas import ArtifactDef, SchemaDef, artifact_for_file, build_graph, schema_order


def schema(artifacts: list[tuple[str, list[str]]], apply_requires: list[str]) -> SchemaDef:
    return SchemaDef(
        name="s",
        description="",
        version=1,
        source="project",
        path=None,
        artifacts=[ArtifactDef(id=a, generates=f"{a}.md", description="", requires=r) for a, r in artifacts],
        apply_requires=apply_requires,
        apply_tracks="tasks.md",
    )


def edges(s: SchemaDef) -> set[tuple[str, str, bool]]:
    return {(e.source, e.target, e.derived) for e in build_graph(s)[1]}


class GraphTest(unittest.TestCase):
    def test_spec_driven_levels_and_edges(self) -> None:
        s = schema(
            [
                ("proposal", []),
                ("specs", ["proposal"]),
                ("design", ["proposal"]),
                ("tasks", ["specs", "design"]),
            ],
            ["tasks"],
        )
        nodes, _ = build_graph(s)
        self.assertEqual(
            {n.key: n.level for n in nodes}, {"proposal": 0, "specs": 1, "design": 1, "tasks": 2, "apply": 3}
        )
        self.assertEqual(
            edges(s),
            {
                ("proposal", "specs", False),
                ("proposal", "design", False),
                ("specs", "tasks", False),
                ("design", "tasks", False),
                ("tasks", "apply", False),
            },
        )
        self.assertEqual(schema_order(s), ["proposal", "specs", "design", "tasks"])

    def test_transitively_implied_edge_dropped(self) -> None:
        s = schema([("a", []), ("b", ["a"]), ("c", ["a", "b"])], ["c"])
        self.assertNotIn(("a", "c", False), edges(s))
        self.assertIn(("b", "c", False), edges(s))

    def test_post_apply_step_is_derived_and_reduced(self) -> None:
        # verify needs tasks, which apply needs too, and apply does not need verify.
        s = schema([("proposal", []), ("tasks", ["proposal"]), ("verify", ["tasks"])], ["tasks"])
        nodes, _ = build_graph(s)
        verify = next(n for n in nodes if n.key == "verify")
        self.assertTrue(verify.derived)
        self.assertEqual(verify.level, 3)
        self.assertIn(("apply", "verify", True), edges(s))
        self.assertNotIn(("tasks", "verify", False), edges(s))

    def test_no_derivation_without_apply_requires(self) -> None:
        s = schema([("a", []), ("b", ["a"])], [])
        self.assertFalse(any(n.derived for n in build_graph(s)[0]))

    def test_artifact_named_apply_keeps_its_own_node(self) -> None:
        s = schema([("tasks", []), ("apply", ["tasks"])], ["tasks"])
        keys = [n.key for n in build_graph(s)[0]]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertIn("apply (phase)", keys)

    def test_cycle_does_not_hang(self) -> None:
        s = schema([("a", ["b"]), ("b", ["a"])], ["a"])
        nodes, _ = build_graph(s)
        self.assertEqual(len(nodes), 3)
        self.assertFalse(any(n.derived for n in nodes))

    def test_artifact_for_file(self) -> None:
        s = schema([("proposal", [])], [])
        s.artifacts.append(ArtifactDef(id="specs", generates="specs/**/*.md", description="", requires=[]))
        self.assertEqual(artifact_for_file(s, "proposal.md"), "proposal")
        self.assertEqual(artifact_for_file(s, "specs/a/b/spec.md"), "specs")
        self.assertIsNone(artifact_for_file(s, "notes.md"))


if __name__ == "__main__":
    unittest.main()
