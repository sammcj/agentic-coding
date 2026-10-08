import contextlib
import io
import json
import unittest

from helpers import make_repo
from openspeccer.cli import main


def run(*argv: str) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, self.root = make_repo()

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_summary_lists_active_changes(self) -> None:
        code, out, _ = run(str(self.root), "--summary")
        self.assertEqual(code, 0)
        self.assertIn("add-passkeys", out)

    def test_change_prints_one_change(self) -> None:
        code, out, _ = run(str(self.root), "--change", "add-passkeys")
        self.assertEqual(code, 0)
        detail = json.loads(out)
        self.assertEqual(detail["slug"], "add-passkeys")
        self.assertIn("artifacts", detail)

    def test_unknown_change_exits_2(self) -> None:
        code, out, err = run(str(self.root), "--change", "nope")
        self.assertEqual((code, out), (2, ""))
        self.assertIn("no change named nope", err)

    def test_finds_repo_from_a_subdirectory(self) -> None:
        code, out, err = run(str(self.root / "openspec" / "specs"), "--summary")
        self.assertEqual(code, 0, err)
        self.assertIn(str(self.root), out)


if __name__ == "__main__":
    unittest.main()
