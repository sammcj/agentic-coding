"""Regression cases: worktree election and scope, symlink containment, bad dates, monorepo layout,
schema lookup caching and Host checking."""

import http.client
import os
import shutil
import threading
import time
import unittest
from pathlib import Path
from unittest import mock

from helpers import git, make_repo, write
from openspeccer.repo import Repo
from openspeccer.server import serve


def age(path: Path, seconds: float) -> None:
    """Backdate every file under path."""
    past = time.time() - seconds
    for f in [path, *path.rglob("*")]:
        os.utime(f, (past, past))


class ElectionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, self.root = make_repo()
        self.wt = self.root.parent / "wt"
        git(self.root, "worktree", "add", "-q", str(self.wt), "-b", "feature")
        self.wt_change = self.wt / "openspec/changes/add-passkeys"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_newer_main_copy_beats_stale_worktree_copy(self) -> None:
        write(self.wt, "openspec/changes/add-passkeys/tasks.md", "- [ ] old\n")
        age(self.wt_change, 7 * 86400)
        write(self.root, "openspec/changes/add-passkeys/tasks.md", "- [x] a\n- [x] b\n- [x] c\n")
        c = next(c for c in Repo(self.root).snapshot()["changes"] if c["slug"] == "add-passkeys")
        self.assertTrue(c["source"]["is_main"])
        self.assertEqual(c["tasks"], {"done": 3, "total": 3})
        self.assertEqual(c["variants"], 2)

    def test_detail_follows_scope_and_worktree_key(self) -> None:
        write(self.wt, "openspec/changes/add-passkeys/tasks.md", "- [x] a\n- [x] b\n- [ ] c\n")
        repo = Repo(self.root)
        main_key = repo.snapshot()["worktrees"][0]["key"]

        def total(d: dict) -> int:
            return next(a for a in d["artifacts"] if a["kind"] == "tasks")["tasks"]["total"]

        self.assertEqual(total(repo.change_detail("add-passkeys")), 3)
        self.assertEqual(total(repo.change_detail("add-passkeys", aggregate=False)), 2)
        # The election picked the worktree copy; asking for main's by key still gets main's.
        self.assertEqual(total(repo.change_detail("add-passkeys", main_key)), 2)


class ContainmentTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, self.root = make_repo(with_git=False)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_symlinks_out_of_the_change_are_ignored(self) -> None:
        secret = write(self.root.parent, "secret.md", "TOPSECRET\n")
        change = self.root / "openspec/changes/idea-sso"
        os.symlink(secret, change / "leak.md")
        os.symlink(self.root.parent, self.root / "openspec/changes/linked-change")
        repo = Repo(self.root)
        slugs = {c["slug"] for c in repo.snapshot()["changes"]}
        self.assertNotIn("linked-change", slugs)
        paths = [a["path"] for a in repo.change_detail("idea-sso")["artifacts"]]
        self.assertEqual(paths, ["proposal.md"])
        self.assertEqual(repo.search("TOPSECRET"), [])

    def test_impossible_date_does_not_break_the_snapshot(self) -> None:
        write(self.root, "openspec/changes/idea-sso/.openspec.yaml", "created: 2026-02-30\n")
        write(self.root, "openspec/changes/archive/2026-13-01-bad/proposal.md", "x\n")
        snap = Repo(self.root).snapshot()
        cs = {c["slug"]: c for c in snap["changes"]}
        self.assertIsNone(cs["idea-sso"]["created"])
        self.assertIsNone(cs["2026-13-01-bad"]["archived"])
        self.assertEqual(snap["stats"]["archived"], 2)


class MonorepoTest(unittest.TestCase):
    """openspec/ below the git top level."""

    def setUp(self) -> None:
        self.tmp, built = make_repo(with_git=False)
        self.top = built.parent / "mono"
        self.root = self.top / "packages" / "app"
        self.root.parent.mkdir(parents=True)
        shutil.move(built, self.root)
        git(self.top, "init", "-q", "-b", "main")
        git(self.top, "add", "-A")
        git(self.top, "commit", "-qm", "init")
        write(self.root, "openspec/specs/auth/spec.md", "# Auth\n\nChanged.\n")
        git(self.top, "commit", "-qam", "edit auth")
        self.wt = self.top.parent / "mono-wt"
        git(self.top, "worktree", "add", "-q", str(self.wt), "-b", "feature")
        write(self.wt, "packages/app/openspec/changes/wt-only/proposal.md", "x\n")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_worktrees_dates_and_history(self) -> None:
        repo = Repo(self.root)
        snap = repo.snapshot()
        cs = {c["slug"]: c for c in snap["changes"]}
        self.assertIn("wt-only", cs)
        self.assertEqual(snap["worktrees"][1]["path"], str((self.wt / "packages/app").resolve()))
        self.assertIsNotNone(cs["idea-sso"]["created"])
        versions = repo.spec_detail("auth")["versions"]
        self.assertEqual(len(versions), 2)
        diff = repo.spec_diff("auth", versions[1]["rev"][:7], "working")
        self.assertGreater(diff["added"], 0)


class SchemaLookupTest(unittest.TestCase):
    def test_cli_answer_of_unknown_schema_is_cached(self) -> None:
        tmp, root = make_repo(with_git=False)
        self.addCleanup(tmp.cleanup)
        log = root.parent / "calls.log"
        cli = write(
            root.parent,
            "fake-openspec",
            f'#!/bin/sh\necho "$*" >> "{log}"\necho \'{{"error": "not found"}}\'\nexit 1\n',
        )
        cli.chmod(0o755)
        with mock.patch.dict(os.environ, {"OPENSPECCER_OPENSPEC_BIN": str(cli)}):
            repo = Repo(root)
            repo.snapshot()
            repo.bump()
            repo.snapshot()
        calls = log.read_text().splitlines()
        self.assertEqual(calls.count("schema which spec-driven --json"), 1)


class HostCheckTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, root = make_repo(with_git=False)
        self.server, self.watcher = serve(Repo(root), "127.0.0.1", 0, 0.05, False)
        self.port = self.server.server_address[1]
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self) -> None:
        self.watcher.stop()
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def status(self, host: str) -> int:
        conn = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        try:
            conn.request("GET", "/api/ping", headers={"Host": host})
            resp = conn.getresponse()
            resp.read()
            return resp.status
        finally:
            conn.close()

    def test_rebound_host_is_refused(self) -> None:
        self.assertEqual(self.status(f"127.0.0.1:{self.port}"), 200)
        self.assertEqual(self.status(f"localhost:{self.port}"), 200)
        self.assertEqual(self.status(f"evil.example:{self.port}"), 403)
        self.assertEqual(self.status("localhost:1"), 403)


if __name__ == "__main__":
    unittest.main()
