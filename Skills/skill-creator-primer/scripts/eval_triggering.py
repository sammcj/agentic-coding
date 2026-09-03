#!/usr/bin/env python3
"""Measure how often a skill activates on a set of eval queries, by driving `claude -p` in a scratch project holding the real skill."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import mkdtemp


def skill_name(skill_path: Path) -> str:
    in_fm = False
    for line in (skill_path / "SKILL.md").read_text().splitlines():
        if line.strip() == "---":
            if in_fm:
                break
            in_fm = True
            continue
        if in_fm and line.startswith("name:"):
            return line.split(":", 1)[1].strip()
    return skill_path.name


def is_activation(tool: str, inp: dict, name: str) -> bool:
    if tool == "Skill":
        # Match the invoked skill exactly (a leading slash for the command form aside), not as a substring: skill
        # "review" must not match a call to "code-review".
        invoked = str(inp.get("command") or inp.get("skill") or "").strip().lstrip("/")
        return invoked == name
    return tool == "Read" and f"/skills/{name}/" in str(inp.get("file_path") or "")


def run_once(query, skill_path, name, model, timeout, within, claude) -> bool:
    """Run one query and return whether the skill activates within the first N
    tool calls. Streams the transcript and kills the subprocess as soon as the
    decision is made, so the model never plays the task out to completion."""
    proj = Path(mkdtemp())
    proc = None
    try:
        dest = proj / ".claude" / "skills" / name
        dest.parent.mkdir(parents=True)
        shutil.copytree(skill_path, dest)
        # --setting-sources project drops user-global SessionStart hooks, which otherwise steer the child away from
        # consulting skills and flatten every query to a non-trigger, while keeping keychain auth. --bare or a
        # redirected CLAUDE_CONFIG_DIR would also drop the hooks but force auth onto ANTHROPIC_API_KEY.
        cmd = [
            claude,
            "-p",
            query,
            "--setting-sources",
            "project",
            "--output-format",
            "stream-json",
            "--verbose",
        ]
        if model:
            cmd += ["--model", model]
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
        proc = subprocess.Popen(
            cmd, cwd=proj, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        assert proc.stdout is not None  # stdout=PIPE guarantees a stream
        timer = threading.Timer(timeout, proc.kill)
        timer.start()
        seen = 0
        try:
            for line in proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "result":
                    return False  # terminal: run ended without the skill firing in time
                if event.get("type") != "assistant":
                    continue
                for c in event.get("message", {}).get("content", []):
                    if c.get("type") != "tool_use":
                        continue
                    if is_activation(c.get("name", ""), c.get("input", {}), name):
                        return True
                    seen += 1
                    if seen >= within:
                        return False
            return False
        finally:
            timer.cancel()
    finally:
        if proc and proc.poll() is None:
            proc.kill()
            proc.wait()
        shutil.rmtree(proj, ignore_errors=True)


def query_passes(should_trigger: bool, fired: int, runs: int) -> bool:
    """Per-query verdict: a should-trigger query passes when it fires in at least
    half its runs; a should-not-trigger query passes when it fires in fewer."""
    rate = fired / runs
    return (rate >= 0.5) if should_trigger else (rate < 0.5)


def select_cases(cases, substrings):
    """Return cases whose query contains any of substrings (case-insensitive).
    With no substrings, returns the cases unchanged - the full set."""
    if not substrings:
        return list(cases)
    needles = [s.lower() for s in substrings]
    return [c for c in cases if any(n in c["query"].lower() for n in needles)]


def main():
    p = argparse.ArgumentParser(
        description=__doc__,
        epilog="Run outside any command sandbox: claude and node need network. Each run is killed as soon as the "
        "activation decision is made and its scratch project deleted.",
    )
    p.add_argument(
        "--eval-set", required=True, metavar="FILE",
        help='JSON array of {"query": str, "should_trigger": bool} cases',
    )
    p.add_argument("--skill-path", required=True, metavar="DIR", help="skill directory (holds SKILL.md)")
    p.add_argument(
        "--within", type=int, default=3, metavar="N",
        help="count a trigger when the skill activates within the first N tool calls; a tool-using task "
        "legitimately opens with a Read or Bash before consulting a skill (default %(default)s)",
    )
    p.add_argument(
        "--runs", type=int, default=3, metavar="N",
        help="runs per query; a should-trigger query passes when it fires in at least half, a should-not in fewer "
        "(default %(default)s; raise for a stabler read)",
    )
    p.add_argument(
        "--model", default=None, metavar="ID",
        help="model for the child sessions; prefer a mid-range one (e.g. Claude Sonnet): the strongest reasons its "
        "way to the right skill despite a weak description, the weakest misroutes in ways typical sessions won't "
        "(default: the user's configured model)",
    )
    p.add_argument("--workers", type=int, default=8, metavar="N", help="concurrent claude sessions (default %(default)s)")
    p.add_argument(
        "--timeout", type=int, default=150, metavar="SECONDS",
        help="kill a run that has not decided by then and count it as not fired (default %(default)s)",
    )
    p.add_argument(
        "--only",
        action="append",
        metavar="SUBSTRING",
        help="run only cases whose query contains SUBSTRING (case-insensitive); "
        "repeatable, a case matching ANY is included",
    )
    if len(sys.argv) == 1:
        p.print_help()
        sys.exit(2)
    args = p.parse_args()

    skill_path = Path(args.skill_path).resolve()
    name = skill_name(skill_path)
    cases = json.loads(Path(args.eval_set).read_text())
    if args.only:
        selected = select_cases(cases, args.only)
        if not selected:
            names = ", ".join(repr(s) for s in args.only)
            sys.exit(f"--only matched no queries: {names}")
        print(f"{len(selected)}/{len(cases)} queries selected by --only")
        cases = selected
    claude = shutil.which("claude")
    if not claude:
        sys.exit("claude not found on PATH")

    def run_job(case):
        query = case["query"]
        should = case.get("should_trigger", True)
        try:
            fired = run_once(query, skill_path, name, args.model, args.timeout, args.within, claude)
        except Exception as e:  # one flaky run shouldn't sink the whole batch
            print(f"warning: run failed for {query[:60]!r}: {e}", file=sys.stderr)
            fired = False
        return query, should, fired

    jobs = [c for c in cases for _ in range(args.runs)]
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(run_job, jobs))

    by_query = {}
    for query, should, fired in results:
        rec = by_query.setdefault(query, {"should": should, "fired": 0, "runs": 0})
        rec["fired"] += int(fired)
        rec["runs"] += 1

    passed = 0
    print(f"skill: {name}  |  trigger = activates within first {args.within} tool call(s)\n")
    for query, rec in by_query.items():
        ok = query_passes(rec["should"], rec["fired"], rec["runs"])
        passed += ok
        print(
            f"  [{'PASS' if ok else 'FAIL'}] {rec['fired']}/{rec['runs']} "
            f"expected={rec['should']}: {query[:70]}"
        )
    print(f"\nResults: {passed}/{len(by_query)} passed")


if __name__ == "__main__":
    main()
