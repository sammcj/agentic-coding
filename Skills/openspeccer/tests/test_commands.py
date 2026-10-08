import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from openspeccer.commands import CommandCatalog, parse_help

ROOT_HELP = """Usage: openspec [options] [command]

Root description

Options:
  --no-color  Disable color output
  -h, --help  display help for command

Commands:
  store       Manage stores
  ghost       Unknown to the CLI, so it answers with this help again
  help [command]  display help for command
"""

STORE_HELP = """Usage: openspec store [options] [command]

Manage stores

Options:
  -h, --help         display help for command

Commands:
  list|ls [options]  List locally registered stores, a description long enough
                     that commander wraps it
  help [command]     display help for command
"""

LIST_HELP = """Usage: openspec store list|ls [options]

List locally registered stores

Options:
  --json      Output as JSON
  -h, --help  display help for command
"""


def fake_cli(directory: Path) -> Path:
    for name, text in {"root": ROOT_HELP, "store": STORE_HELP, "list": LIST_HELP}.items():
        (directory / f"{name}.txt").write_text(text)
    script = directory / "openspec"
    script.write_text(
        "#!/bin/sh\n"
        'case "$*" in\n'
        '  "--version") echo 9.9.9 ;;\n'
        f'  "store --help") cat "{directory}/store.txt" ;;\n'
        f'  "store list --help") cat "{directory}/list.txt" ;;\n'
        # commander prints the nearest known command's help for an unknown name
        f'  *) cat "{directory}/root.txt" ;;\n'
        "esac\n"
    )
    script.chmod(0o755)
    return script


class ParseHelpTest(unittest.TestCase):
    def test_sections_and_wrapped_descriptions(self) -> None:
        parsed = parse_help(STORE_HELP)
        self.assertEqual(parsed["usage"], "openspec store [options] [command]")
        self.assertEqual(parsed["description"], "Manage stores")
        first = parsed["sections"]["commands"][0]
        self.assertEqual(first["term"], "list|ls [options]")
        self.assertTrue(first["desc"].endswith("that commander wraps it"))


class CommandCatalogTest(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)

    def test_tree_with_aliases_and_no_runaway_recursion(self) -> None:
        cli = fake_cli(self.dir)
        with mock.patch.dict(os.environ, {"OPENSPECCER_OPENSPEC_BIN": str(cli)}):
            result = CommandCatalog(self.dir).get()
        self.assertIsNone(result["error"])
        self.assertEqual(result["version"], "9.9.9")
        self.assertEqual([c["path"] for c in result["commands"]], [["store"], ["store", "list"]])
        listing = result["commands"][1]
        self.assertEqual(listing["aliases"], ["ls"])
        self.assertEqual([o["term"] for o in listing["options"]], ["--json"])
        self.assertEqual([o["term"] for o in result["global_options"]], ["--no-color"])

    def test_missing_cli_is_retried_and_an_answer_is_kept(self) -> None:
        missing = self.dir / "nowhere" / "openspec"
        with mock.patch.dict(os.environ, {"OPENSPECCER_OPENSPEC_BIN": str(missing)}):
            catalog = CommandCatalog(self.dir)
            self.assertIsNotNone(catalog.get()["error"])
        cli = fake_cli(self.dir)
        with mock.patch.dict(os.environ, {"OPENSPECCER_OPENSPEC_BIN": str(cli)}):
            self.assertIsNone(catalog.get()["error"])
            cli.unlink()
            self.assertEqual(len(catalog.get()["commands"]), 2)


if __name__ == "__main__":
    unittest.main()
