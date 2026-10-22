import unittest
from unittest import mock

from helpers import make_repo, write
from openspeccer.config import CONTEXT_LIMIT
from openspeccer.repo import Repo

CONFIG = """schema: spec-driven
context: |
  A backup client.
  Write in Australian English.
rules:
  specs:
    - Reference the requirement ID.
  checks:
    - Each check is observable.
  bogus:
    - Never applied.
operations:
  apply:
    guidance:
      - "Update CHANGELOG.md."
  deploy:
    guidance:
      - Ignored.
store: team-specs
"""


class ConfigTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, self.root = make_repo(with_git=False)
        self.repo = Repo(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_sections(self) -> None:
        write(self.root, "openspec/config.yaml", CONFIG)
        cfg = self.repo.config()
        self.assertEqual(cfg["path"], "openspec/config.yaml")
        self.assertEqual(cfg["schema"], "spec-driven")
        self.assertEqual(cfg["context"], "A backup client.\nWrite in Australian English.\n")
        self.assertEqual(cfg["rules"]["specs"], ["Reference the requirement ID."])
        self.assertEqual(cfg["operations"], {"apply": ["Update CHANGELOG.md."]})
        self.assertEqual(cfg["other"], {"store": "team-specs"})
        ignored = "operations.deploy is not an OpenSpec operation (apply, archive), so it is ignored"
        self.assertIn(ignored, cfg["warnings"])
        self.assertIsNone(cfg["error"])

    def test_unknown_rule_keys_checked_against_every_schema(self) -> None:
        write(self.root, "openspec/config.yaml", CONFIG)
        listed = [
            {"name": "spec-driven", "artifacts": ["proposal", "specs", "design", "tasks"]},
            {"name": "loop", "artifacts": ["intake", "checks"]},
        ]
        with mock.patch.object(self.repo.catalog, "summaries", return_value=(listed, None)):
            cfg = self.repo.config()
        self.assertEqual(cfg["unknown_rules"], ["bogus"])
        self.assertIn("rules.bogus matches no artifact in any schema", cfg["warnings"])

    def test_no_rule_warnings_without_cli(self) -> None:
        # Built-in schemas are unknown without the CLI, so `specs` would be a false alarm.
        write(self.root, "openspec/config.yaml", CONFIG)
        self.assertEqual(self.repo.config()["unknown_rules"], [])

    def test_oversized_context_flagged(self) -> None:
        body = "x" * (CONTEXT_LIMIT + 10)
        write(self.root, "openspec/config.yaml", f"schema: spec-driven\ncontext: |\n  {body}\n")
        cfg = self.repo.config()
        self.assertGreater(cfg["context_bytes"], CONTEXT_LIMIT)
        self.assertTrue(any("over OpenSpec's 50KB limit" in w for w in cfg["warnings"]))

    def test_yml_extension_and_default_schema(self) -> None:
        (self.root / "openspec/config.yaml").unlink()
        write(self.root, "openspec/config.yml", "schema: loop\n")
        self.assertEqual(self.repo.config()["path"], "openspec/config.yml")
        self.assertEqual(self.repo.snapshot()["default_schema"], "loop")

    def test_agent_instruction_files(self) -> None:
        write(self.root, "AGENTS.md", "# Rules\n")
        write(self.root, ".claude/rules/swift.md", "Use Swift 6.\n")
        write(self.root, ".claude/agents/reviewer.md", "Review only.\n")
        write(self.root, ".build/agent-rules.md", "Ad hoc, unseen by agents.\n")
        found = {f["path"]: f["content"] for f in self.repo.config()["instructions"]}
        expected = {
            "AGENTS.md": "# Rules\n",
            ".claude/rules/swift.md": "Use Swift 6.\n",
            ".claude/agents/reviewer.md": "Review only.\n",
        }
        self.assertEqual(found, expected)

    def test_missing_and_broken(self) -> None:
        (self.root / "openspec/config.yaml").unlink()
        self.assertIsNone(self.repo.config()["path"])
        write(self.root, "openspec/config.yaml", "rules:\n  - [unclosed\n")
        cfg = self.repo.config()
        self.assertIsNotNone(cfg["error"])
        self.assertEqual(cfg["raw"], "rules:\n  - [unclosed\n")


if __name__ == "__main__":
    unittest.main()
