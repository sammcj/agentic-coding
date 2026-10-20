import json
import shutil
import subprocess
import unittest
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "assets" / "web"

# Same import-map hook as test_md.py. Calls `module.fn(...args)` for the JSON job in argv.
RUN = """
import { registerHooks } from "node:module";
import { pathToFileURL } from "node:url";
const web = pathToFileURL(process.argv[1] + "/");
const vendor = { preact: "preact.mjs", "preact/hooks": "hooks.mjs", htm: "htm.mjs", marked: "marked.esm.js" };
registerHooks({
  resolve: (s, c, next) =>
    s in vendor ? { url: new URL("vendor/" + vendor[s], web).href, shortCircuit: true } : next(s, c),
});
const { module, fn, args } = JSON.parse(process.argv[2]);
const mod = await import(new URL(module, web).href);
console.log(JSON.stringify(mod[fn](...args)));
"""


def call(module: str, fn: str, *args) -> str:
    job = json.dumps({"module": module, "fn": fn, "args": args})
    cmd = ["node", "--input-type=module", "-e", RUN, str(WEB), job]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
    return json.loads(out.stdout)


def cmd(path: list[str], desc: str) -> dict:
    return {"path": path, "usage": "", "aliases": [], "description": desc, "arguments": [], "options": []}


CHANGE = {
    "name": "add-login",
    "slug": "add-login",
    "lane": "in_progress",
    "status": "active",
    "updated": "2026-10-01T10:00:00Z",
    "tasks": {"done": 1, "total": 3},
}


@unittest.skipUnless(shutil.which("node"), "node not installed")
class ExportMarkdownTest(unittest.TestCase):
    def test_dashboard_lists_stats_lanes_and_specs_in_flight(self) -> None:
        stats = dict(specs=2, requirements=5, active=1, tasks_done=1, tasks_total=3, archived=0, stale=0)
        snap = {
            "repo": {"name": "demo"},
            "stats": {**stats, "avg_lifecycle_days": None},
            "changes": [CHANGE],
            "specs": [
                {"topic": "auth", "requirement_count": 3, "in_flight": ["add-login"]},
                {"topic": "ui", "requirement_count": 2, "in_flight": []},
            ],
        }
        out = call("views/dashboard.js", "dashboardMarkdown", snap)
        self.assertIn("# demo dashboard", out)
        self.assertIn("| Active tasks | 33% (1 of 3 done) |", out)
        self.assertIn("## In progress (1)\n\n- add-login (updated 2026-10-01, tasks 1/3)", out)
        self.assertIn("## Proposed (0)\n\nNone", out)
        self.assertIn("| auth | 3 | add-login |", out)
        self.assertNotIn("| ui |", out)

    def test_agents_lists_skills_and_commands(self) -> None:
        agent = {"tools": ["Claude Code"], "root": ".claude", "commands": []}
        agents = [{**agent, "skills": ["openspec-propose"]}]
        out = call("views/agents.js", "agentsMarkdown", "demo", agents)
        self.assertIn("## Claude Code\n\n`.claude/`", out)
        self.assertIn("### Skills (1)\n\n- `openspec-propose`", out)
        self.assertNotIn("### Commands", out)

    def test_schema_list_escapes_pipes_and_notes_unresolved(self) -> None:
        schema = dict(name="spec-driven", source="package", is_default=True, artifact_count=4)
        data = {
            "schemas": [{**schema, "active_changes": 2, "description": "a | b"}],
            "unresolved": {"custom": 1},
        }
        out = call("views/schemas.js", "schemaListMarkdown", "demo", data)
        self.assertIn("| spec-driven | package | yes | 4 | 2 | a \\| b |", out)
        self.assertIn("- `custom` (1)", out)

    def test_schema_detail_draws_graph_as_mermaid(self) -> None:
        apply = {"key": "apply", "label": "Apply", "kind": "apply"}
        data = {
            "name": "spec-driven",
            "source": "package",
            "tracks": "tasks.md",
            "path": "/x/schema.yaml",
            "description": "",
            "nodes": [
                {"key": "proposal", "label": 'Pro"posal', "kind": "artifact", "requires": []},
                {**apply, "generates": "tasks.md", "requires": ["proposal"]},
            ],
            "edges": [
                {"source": "proposal", "target": "apply"},
                {"source": "apply", "target": "proposal", "derived": True},
            ],
        }
        out = call("views/schemas.js", "schemaMarkdown", data)
        graph = '```mermaid\nflowchart LR\n  n0["Pro#quot;posal"]\n  n1["Apply"]\n'
        self.assertIn(graph + "  n0 --> n1\n  n1 -. derived .-> n0\n```", out)
        self.assertIn("| Apply | apply | tasks.md | proposal |  |", out)

    def test_commands_follow_filter_and_keep_matching_parents(self) -> None:
        data = {
            "version": "1.2.0",
            "global_options": [{"term": "--json", "desc": "JSON output"}],
            "commands": [cmd(["list"], "List things"), cmd(["spec"], "Spec"), cmd(["spec", "show"], "Show")],
        }
        full = call("views/commands.js", "commandsMarkdown", data)
        self.assertIn("## Global options\n\n- `--json` JSON output", full)
        self.assertIn("### `openspec spec show`", full)
        filtered = call("views/commands.js", "commandsMarkdown", data, "show")
        self.assertIn("## `openspec spec`", filtered)
        self.assertIn("### `openspec spec show`", filtered)
        self.assertNotIn("openspec list", filtered)
        self.assertNotIn("Global options", filtered)

    def test_change_markdown_includes_only_given_tabs(self) -> None:
        arts = [
            {"kind": "markdown", "path": "proposal.md", "content": "# Proposal\n"},
            {"kind": "data", "path": "meta.yaml", "content": "a: 1\n"},
        ]
        one = call("views/changes.js", "changeMarkdown", CHANGE, "sub", arts[:1])
        self.assertIn("**`proposal.md`**", one)
        self.assertNotIn("meta.yaml", one)
        both = call("views/changes.js", "changeMarkdown", CHANGE, "sub", arts)
        self.assertIn("**`meta.yaml`**\n\n```yaml\na: 1\n```", both)


if __name__ == "__main__":
    unittest.main()
