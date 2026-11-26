"""Re-check the template and every bundled example, comparing each verdict with the expected one."""

import argparse
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
CHECKER = SKILL_DIR / "scripts" / "tla_check.py"
EXAMPLES_DIR = SKILL_DIR / "assets" / "examples"


@dataclass(frozen=True)
class Case:
    spec: Path
    config: str
    expect: str
    violates: str = ""


CASES = [
    Case(SKILL_DIR / "assets" / "Template.tla", "Template.cfg", "pass"),
    Case(EXAMPLES_DIR / "distributed" / "TwoPhaseCommit.tla", "TwoPhaseCommit.cfg", "pass"),
    Case(EXAMPLES_DIR / "distributed" / "RingLeaderElection.tla", "RingLeaderElection.cfg", "pass"),
    Case(EXAMPLES_DIR / "ai" / "AgentToolLoop.tla", "AgentToolLoop.cfg", "pass"),
    Case(EXAMPLES_DIR / "ai" / "IndAgentToolLoop.tla", "IndAgentToolLoop.cfg", "pass"),
    Case(EXAMPLES_DIR / "ai" / "MultiAgentOrchestrator.tla", "MultiAgentOrchestrator.cfg", "pass"),
    Case(EXAMPLES_DIR / "ontology" / "MCAgentOntology.tla", "MCAgentOntology.cfg", "pass"),
    Case(EXAMPLES_DIR / "security" / "NeedhamSchroeder.tla", "NeedhamSchroeder.cfg", "pass"),
    Case(
        EXAMPLES_DIR / "security" / "NeedhamSchroeder.tla",
        "NeedhamSchroederAttack.cfg",
        "violation",
        "Secrecy",
    ),
    Case(EXAMPLES_DIR / "security" / "TokenSession.tla", "TokenSession.cfg", "pass"),
    Case(EXAMPLES_DIR / "lean4" / "LockMutex.tla", "LockMutex.cfg", "pass"),
]
LEAN_FILE = EXAMPLES_DIR / "lean4" / "LockMutex.lean"


def run_case(case: Case) -> bool:
    config = str(case.spec.parent / case.config)
    command = [sys.executable, str(CHECKER), str(case.spec), "--config", config, "--expect", case.expect]
    if case.violates:
        command += ["--expect-property", case.violates]
    done = subprocess.run(command, capture_output=True, text=True, check=False)
    wanted = " ".join(filter(None, [case.expect, case.violates]))
    label = f"{case.spec.relative_to(SKILL_DIR)} ({case.config}): {wanted}"
    if done.returncode == 0:
        states = next((line.strip() for line in done.stdout.splitlines() if "tates" in line), "")
        print(f"ok    {label}  [{states}]")
        return True
    print(f"FAIL  {label}\n{done.stdout.strip()}")
    return False


def run_lean() -> bool:
    if shutil.which("lean") is None:
        print(f"skip  {LEAN_FILE.relative_to(SKILL_DIR)} (lean not installed)")
        return True
    done = subprocess.run(["lean", str(LEAN_FILE)], capture_output=True, text=True, check=False)
    print(f"{'ok   ' if done.returncode == 0 else 'FAIL '} {LEAN_FILE.relative_to(SKILL_DIR)}")
    if done.returncode != 0:
        print(done.stdout.strip() or done.stderr.strip())
    return done.returncode == 0


def main() -> int:
    argparse.ArgumentParser(description=__doc__).parse_args()
    results = [run_case(case) for case in CASES]
    results.append(run_lean())
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
