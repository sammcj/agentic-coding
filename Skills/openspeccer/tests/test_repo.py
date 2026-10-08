import os
import unittest

from helpers import git, make_repo, write
from openspeccer.repo import NotFound, Repo
from openspeccer.scan import discover_specs


def by_name(snap: dict) -> dict[str, dict]:
    return {c["name"]: c for c in snap["changes"]}


class SnapshotTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, self.root = make_repo()
        self.repo = Repo(self.root)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_changes_lanes_and_dates(self) -> None:
        snap = self.repo.snapshot()
        cs = by_name(snap)
        self.assertEqual(set(cs), {"add-passkeys", "idea-sso", "loop-work", "init-auth"})
        self.assertEqual(cs["add-passkeys"]["lane"], "in_progress")
        self.assertEqual(cs["add-passkeys"]["tasks"], {"done": 1, "total": 2})
        self.assertEqual(cs["idea-sso"]["lane"], "proposed")
        self.assertEqual(cs["init-auth"]["lane"], "archived")
        self.assertEqual(
            (cs["init-auth"]["created"], cs["init-auth"]["archived"]), ("2026-07-20", "2026-08-01")
        )
        # No .openspec.yaml: created falls back to the first git commit.
        self.assertIsNotNone(cs["idea-sso"]["created"])

    def test_schema_tracks_custom_file(self) -> None:
        loop = by_name(self.repo.snapshot())["loop-work"]
        self.assertEqual(loop["tasks"], {"done": 2, "total": 2})
        self.assertEqual(loop["lane"], "ready")
        kinds = {a["path"]: (a["kind"], a["schema_artifact"]) for a in loop["artifacts"]}
        self.assertEqual(kinds["loop/checks.md"], ("tasks", "checks"))
        self.assertEqual(kinds["loop/intake.md"], ("markdown", "intake"))

    def test_specs_and_stats(self) -> None:
        snap = self.repo.snapshot()
        specs = {s["topic"]: s for s in snap["specs"]}
        self.assertEqual(set(specs), {"auth", "billing/invoices"})
        self.assertEqual(specs["auth"]["requirement_count"], 2)
        self.assertEqual(specs["auth"]["in_flight"], ["add-passkeys"])
        self.assertEqual(set(specs["auth"]["history"]), {"add-passkeys", "2026-08-01-init-auth"})
        st = snap["stats"]
        self.assertEqual((st["specs"], st["requirements"], st["active"], st["archived"]), (2, 3, 3, 1))
        self.assertEqual((st["tasks_done"], st["tasks_total"]), (3, 4))
        self.assertEqual(st["avg_lifecycle_days"], 12.0)

    def test_agents_detected(self) -> None:
        agents = self.repo.snapshot()["agents"]
        self.assertEqual(len(agents), 1)
        self.assertEqual(agents[0]["root"], ".claude")
        self.assertEqual(agents[0]["skills"], ["openspec-apply-change"])
        self.assertEqual(agents[0]["commands"], ["commands/opsx/apply.md"])

    def test_change_detail(self) -> None:
        d = self.repo.change_detail("add-passkeys")
        arts = {a["id"]: a for a in d["artifacts"]}
        self.assertEqual(set(arts), {"proposal", "tasks", "specs"})
        self.assertEqual(arts["tasks"]["tasks"]["total"], 2)
        self.assertEqual(arts["specs"]["specs"][0]["doc"]["groups"][0]["op"], "ADDED")
        self.assertEqual(d["meta"], {"schema": "spec-driven", "created": "2026-09-01"})

    def test_spec_detail_history_and_diff(self) -> None:
        d = self.repo.spec_detail("auth")
        self.assertEqual([h["name"] for h in d["history"]], ["add-passkeys", "init-auth"])
        self.assertEqual(d["history"][0]["ops"], {"ADDED": 1})
        self.assertEqual(len(d["versions"]), 1)
        write(self.root, "openspec/specs/auth/spec.md", "# Auth\n\nRewritten.\n")
        diff = self.repo.spec_diff("auth", d["versions"][0]["rev"])
        self.assertGreater(diff["removed"], 0)
        self.assertEqual(diff["added"], 1)

    def test_rejects_unsafe_names(self) -> None:
        main_key = self.repo.snapshot()["worktrees"][0]["key"]
        for call in (
            # Via a worktree key the slug becomes a path; `../..` would read the repo root.
            lambda: self.repo.change_detail("../..", main_key),
            lambda: self.repo.spec_detail("../etc"),
            lambda: self.repo.change_detail("../x"),
            lambda: self.repo.spec_diff("auth", "HEAD; rm"),
            lambda: self.repo.schema_detail("-x"),
        ):
            with self.assertRaises(NotFound):
                call()

    def test_search(self) -> None:
        hits = self.repo.search("passkey")
        self.assertEqual([(h["kind"], h["title"]) for h in hits][:1], [("change", "add-passkeys")])
        self.assertTrue(any(h["file"] == "proposal.md" for h in hits))
        hit = next(h for h in self.repo.search("sign-in fails") if h["kind"] == "spec")
        self.assertEqual(hit["snippet"][hit["offset"] : hit["offset"] + 13].lower(), "sign-in fails")

    def test_schema_fallback_without_cli(self) -> None:
        listed = self.repo.schemas()
        self.assertEqual([s["name"] for s in listed["schemas"]], ["loop"])
        self.assertIsNotNone(listed["degraded"])
        self.assertEqual(listed["unresolved"], {"spec-driven": 2})
        detail = self.repo.schema_detail("loop")
        self.assertEqual([n["key"] for n in detail["nodes"]], ["intake", "checks", "apply"])


class WorktreeTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, self.root = make_repo()
        self.wt = self.root.parent / "wt"
        git(self.root, "worktree", "add", "-q", str(self.wt), "-b", "feature")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_aggregation(self) -> None:
        # Diverged copy wins; worktree-only change appears; stale copy of an archived change is dropped.
        write(self.wt, "openspec/changes/add-passkeys/tasks.md", "- [x] a\n- [x] b\n- [ ] c\n")
        write(self.wt, "openspec/changes/wt-only/proposal.md", "x\n")
        write(self.wt, "openspec/changes/init-auth/proposal.md", "stale\n")
        snap = Repo(self.root).snapshot(aggregate=True)
        cs = {c["name"]: c for c in snap["changes"] if c["status"] == "active"}
        self.assertEqual(cs["add-passkeys"]["tasks"], {"done": 2, "total": 3})
        self.assertEqual(cs["add-passkeys"]["source"]["label"], "feature")
        self.assertEqual(cs["add-passkeys"]["variants"], 2)
        self.assertFalse(cs["wt-only"]["source"]["is_main"])
        self.assertNotIn("init-auth", cs)
        self.assertEqual(cs["idea-sso"]["source"]["is_main"], True)
        self.assertEqual(len(snap["worktrees"]), 2)

        main_only = Repo(self.root).snapshot(aggregate=False)
        self.assertNotIn("wt-only", {c["name"] for c in main_only["changes"]})

    def test_detail_by_worktree_key(self) -> None:
        write(self.wt, "openspec/changes/wt-only/proposal.md", "from the worktree\n")
        repo = Repo(self.root)
        key = next(w["key"] for w in repo.snapshot()["worktrees"] if not w["is_main"])
        d = repo.change_detail("wt-only", key)
        self.assertEqual(d["artifacts"][0]["content"], "from the worktree\n")


class DiscoveryTest(unittest.TestCase):
    def test_spec_discovery_rules(self) -> None:
        tmp, root = make_repo(with_git=False)
        try:
            specs = root / "openspec" / "specs"
            write(specs, "spec.md", "root spec is ignored")
            write(specs, ".hidden/spec.md", "dot dirs are skipped")
            outside = root / "elsewhere"
            write(outside, "x/spec.md", "outside")
            os.symlink(outside / "x", specs / "linked-dir")
            (specs / "escape").mkdir()
            os.symlink(outside / "x" / "spec.md", specs / "escape" / "spec.md")
            self.assertEqual(list(discover_specs(specs)), ["auth", "billing/invoices"])
        finally:
            tmp.cleanup()

    def test_non_git_directory(self) -> None:
        tmp, root = make_repo(with_git=False)
        try:
            snap = Repo(root).snapshot()
            self.assertEqual([w["vcs"] for w in snap["worktrees"]], ["none"])
            self.assertEqual(Repo(root).spec_detail("auth")["versions"], [])
        finally:
            tmp.cleanup()

    def test_unreadable_yaml_is_ignored(self) -> None:
        tmp, root = make_repo(with_git=False)
        try:
            write(root, "openspec/changes/idea-sso/.openspec.yaml", "a: [unterminated\n")
            cs = by_name(Repo(root).snapshot())
            self.assertIsNone(cs["idea-sso"]["created"])
            self.assertEqual(cs["idea-sso"]["schema"], "spec-driven")
        finally:
            tmp.cleanup()


if __name__ == "__main__":
    unittest.main()
