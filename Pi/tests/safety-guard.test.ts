/**
 * Containment tests for the project-scoped delete allowance in safety-guard.
 *
 * Every case runs against a real temp tree, because the check resolves symlinks and existing
 * ancestors on disk - a fixture built from strings alone would not exercise the escape paths.
 *
 * Run: bun test tests/safety-guard.test.ts
 */

import { beforeAll, describe, expect, test } from "bun:test"
import * as fs from "node:fs"
import * as os from "node:os"
import * as path from "node:path"

import { __test } from "../extensions/safety-guard.ts"

const tmp = fs.realpathSync(fs.mkdtempSync(path.join(os.tmpdir(), "safety-guard-")))
const root = path.join(tmp, "project")
const outside = path.join(tmp, "outside")

beforeAll(() => {
  fs.mkdirSync(path.join(root, "build"), { recursive: true })
  fs.mkdirSync(path.join(root, "src", "nested"), { recursive: true })
  fs.mkdirSync(path.join(root, ".git"), { recursive: true })
  fs.mkdirSync(outside, { recursive: true })
  fs.symlinkSync(outside, path.join(root, "escape"), "dir")
})

/** Mirrors the tool_call path: bash risk classification with the launch project as the scope. */
function risk(command: string, cwd = root) {
  return __test.classifyBash(command, { root, cwd })
}

describe("allows deletes provably inside the project", () => {
  const allowed = [
    "rm -rf ./build",
    "rm -f foo.txt",
    "rm -rf build",
    "rm -rf build/ src/nested",
    "rm -rf ./build && npm run build",
    "rm -rf ./build && bun test",
    "rm -rf ./build; echo done",
    "rm -rf ./build/*.js",
    "rm -rf src/*",
    "rm -rf --recursive --force ./build",
    "rm -rf './build'",
    'rm -rf "./my dir"',
    "rm -rf -- ./build",
    "rm -rf /bin/../tmp/x".replace("/bin/../tmp/x", path.join(root, "build")),
  ]
  for (const command of allowed) {
    test(command, () => expect(risk(command)).toBeUndefined())
  }
})

describe("allows deletes from a subdirectory of the project", () => {
  test("relative target under cwd", () => {
    expect(risk("rm -rf ./nested", path.join(root, "src"))).toBeUndefined()
  })
  test("bare glob under a subdirectory", () => {
    expect(risk("rm -f *.log", path.join(root, "src"))).toBeUndefined()
  })
})

describe("prompts for anything it cannot prove is inside the project", () => {
  const blocked: Record<string, string> = {
    "escapes upward": "rm -rf ../outside",
    "absolute path elsewhere": "rm -rf /tmp/foo",
    "home directory": "rm -rf ~/stuff",
    "variable expansion": "rm -rf $HOME/x",
    "command substitution": "rm -rf $(cat list)",
    "backtick substitution": "rm -rf `cat list`",
    "symlink out of the project": "rm -rf ./escape",
    "symlink traversal": "rm -rf ./escape/data",
    "wipes the project root": "rm -rf *",
    "deletes the project root": "rm -rf .",
    "git metadata": "rm -rf ./.git",
    "elevated": "sudo rm -f ./build",
    "elevated in a later segment": "rm -rf ./build && sudo rm -f /etc/hosts",
    "unelevated escape in a later segment": "rm -rf ./build; rm -rf /",
    "cwd moved before the delete": "cd .. && rm -rf project",
    "no-preserve-root": "rm -rf --no-preserve-root /",
    "env prefix hides the binary": "PATH=/tmp rm -rf ./build",
    "nested shell": "bash -c 'rm -rf /'",
    "nested shell after a scoped delete": "rm -rf ./build && bash -c 'cd .. && rm -rf project'",
    "interpreter payload that deletes": "rm -rf ./build && node -e 'require(\"fs\").rmSync(\"/x\")'",
    "xargs": "ls | xargs rm -rf",
    "find -delete": "find . -name '*.ts' -delete",
    "brace expansion": "rm -rf {build,/etc}",
    "no operands": "rm -rf",
  }
  for (const [name, command] of Object.entries(blocked)) {
    test(name, () => expect(risk(command)?.action).toBeTruthy())
  }
})

describe("scope is refused outright when unavailable", () => {
  test("no scope configured", () => {
    expect(__test.deleteIsProjectScoped("rm -rf ./build", undefined)).toBe(false)
  })
  test("cwd outside the project root", () => {
    expect(risk("rm -rf ./build", outside)?.action).toBeTruthy()
  })
})

describe("does not mistake a subcommand named rm for the binary", () => {
  for (const command of ["cargo rm serde", "npm rm left-pad", "git rm --cached foo.txt"]) {
    test(command, () => expect(risk(command)).toBeUndefined())
  }
})

describe("redirects into the project no longer prompt", () => {
  for (const command of [
    "cat a.ts > b.ts",
    "jq . x.json > out/y.json",
    "bun test 2>&1 | tee out.log",
    "npx tsc 2> errors.txt",
    "echo hi >> src/notes.json",
    "bun run build &> build/log.json",
  ]) {
    test(command, () => expect(risk(command)).toBeUndefined())
  }
})

describe("redirects out of the project still prompt", () => {
  const blocked: Record<string, string> = {
    absolute: "echo hi > /etc/hosts.json",
    upward: "cat a.ts > ../escaped.ts",
    home: "echo x > ~/notes.json",
    "through a symlink": "echo x > ./escape/thing.json",
    "dotenv even in-project": "echo SECRET=1 > .env",
    "unparseable target": "echo x > $HOME/y.json",
  }
  for (const [name, command] of Object.entries(blocked)) {
    test(name, () => expect(risk(command)?.action).toBeTruthy())
  }
})

describe("consent requires quoting the command, not a matching verb", () => {
  const forcePush = risk("git push --force")
  if (!forcePush) throw new Error("fixture: expected git push --force to be a risk")

  test("a destructive verb alone is not consent", () => {
    expect(__test.userExplicitlyRequestedRisk("please force push the branch", forcePush)).toBe(false)
  })
  test("an unrelated delete request does not license a different command", () => {
    expect(__test.userExplicitlyRequestedRisk("delete the old build output", forcePush)).toBe(false)
  })
  test("the verbatim command is consent", () => {
    expect(__test.userExplicitlyRequestedRisk("run git push --force now", forcePush)).toBe(true)
  })
  test("whitespace and case are normalised", () => {
    expect(__test.userExplicitlyRequestedRisk("GIT PUSH   --force", forcePush)).toBe(true)
  })
  test("a risk with no command can never be waved through", () => {
    expect(__test.userExplicitlyRequestedRisk("delete everything", { action: "Delete files" })).toBe(false)
  })
})

describe("unrelated rules still fire", () => {
  test("force push is unaffected by the delete allowance", () => {
    expect(risk("git push --force")?.action).toBe("Force push git history")
  })
  test("sudo alone still prompts", () => {
    expect(risk("sudo systemctl stop nginx")?.action).toBeTruthy()
  })
})
