"""Validate then model check a TLA+ spec with tla-rs and print a short verdict."""

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

INSTALL_HINT = (
    "tla (tla-rs) is not on PATH.\n"
    "Ask the user whether to install it with: cargo install tla-checker\n"
    "Install only after they agree. It needs a Rust toolchain (cargo) and puts tla in ~/.cargo/bin.\n"
)
PASS_MARK = "Model checking complete. No errors found."
DEADLOCK_MARK = "Deadlock detected"
VIOLATED_NAME = re.compile(
    r"Invariant \d+ \((\w+)\) violated|Liveness property violated: (\w+)|Action property (\w+) is violated"
)
SCENARIO_ALLOWED = "Scenario completed successfully"
SCENARIO_BLOCKED = "Scenario failed"
NOISE = re.compile(
    r"^\s*(Progress: |\d+ states explored \||Computing initial states|Found \d+ initial states"
    r"|Starting exploration|Exploring states|Running liveness checking|Reusing \d+ collected)"
)
EXTENDS_REF = re.compile(r"^\s*EXTENDS\s+(\w+(?:\s*,\s*\w+)*)", re.MULTILINE)
INSTANCE_REF = re.compile(r"\bINSTANCE\s+(\w+)")
PARSE_FAILURE = "failed to parse"
# tla-rs drops ACTION_CONSTRAINT, ALIAS and POSTCONDITION with only this warning.
IGNORED_DIRECTIVE = "not yet supported"
# The slowest bundled example finishes in under 10 s. A model that needs more than
# two minutes should shrink its constants before it gets a longer timeout.
DEFAULT_TIMEOUT_SECS = 120
# A trace longer than this is cut in the middle. The first and last states carry the diagnosis.
MAX_OUTPUT_LINES = 160
KEEP_HEAD_LINES = 60
EXIT_PASS, EXIT_VIOLATION, EXIT_ERROR = 0, 1, 2
GOOD_VERDICTS = ("pass", "allowed")
EXPECTABLE = ("pass", "violation", "deadlock", "allowed", "blocked")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog=(
            "Verdicts: pass, violation, deadlock, error; with --scenario: allowed, blocked, error; "
            "with --validate-only: valid, error. "
            "Exit codes without --expect: 0 pass, valid or allowed; 1 violation, deadlock or blocked; "
            "2 error or timeout. With --expect: 0 when the verdict matches, 1 when it does not, 2 on error. "
            "Arguments after -- go to tla unchanged, for example: -- --check-refinement Abs"
        ),
    )
    parser.add_argument("spec", type=Path, help="the .tla module to check")
    parser.add_argument(
        "--config", type=Path, help="TLC-style .cfg file (default: <spec>.cfg beside the spec)"
    )
    parser.add_argument("--expect", choices=EXPECTABLE, help="the verdict this run must produce")
    parser.add_argument(
        "--expect-property",
        metavar="NAME",
        help="with --expect violation: the invariant or property that must be the one violated",
    )
    parser.add_argument(
        "--scenario",
        type=Path,
        metavar="FILE",
        help="replay the behaviour in FILE (one 'action: Name' or 'step: expr' line per step) "
        "in place of model checking",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT_SECS,
        help=f"seconds before the check is killed (default {DEFAULT_TIMEOUT_SECS})",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="stop after parsing; for a module still being written, with a .cfg that names only what exists",
    )
    parser.add_argument("tla_args", nargs="*", help="extra arguments for tla, after --")
    args = parser.parse_args()
    if args.expect_property and args.expect != "violation":
        parser.error("--expect-property needs --expect violation")
    return args


def run_tla(args: list[str], cwd: Path, timeout: int) -> str:
    done = subprocess.run(
        ["tla", *args],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        timeout=timeout,
        check=False,
    )
    return done.stdout


def local_modules(spec: Path) -> list[Path]:
    """The spec plus every module beside it that it reaches through EXTENDS or INSTANCE."""
    found: dict[Path, None] = {spec: None}
    queue = [spec]
    while queue:
        text = queue.pop().read_text()
        extended = [name.strip() for group in EXTENDS_REF.findall(text) for name in group.split(",")]
        for name in [*extended, *INSTANCE_REF.findall(text)]:
            candidate = spec.parent / f"{name}.tla"
            if candidate.is_file() and candidate not in found:
                found[candidate] = None
                queue.append(candidate)
    return list(found)


def ignored_directives(output: str) -> list[str]:
    return [line.strip() for line in output.splitlines() if IGNORED_DIRECTIVE in line]


def validation_problem(spec: Path, base: list[str], timeout: int) -> str | None:
    """Print validation warnings. Return a message when the spec must not be checked yet."""
    validation = run_tla([*base, "--validate"], spec.parent, timeout)
    # Validating the root does not report parse failures inside modules it extends or instantiates.
    imported = [
        run_tla([module.name, "--validate"], spec.parent, timeout) for module in local_modules(spec)[1:]
    ]
    broken = [text.strip() for text in imported if PARSE_FAILURE in text]
    # tla-rs only warns about a definition it cannot parse, still prints "Validation passed",
    # and then checks without it.
    if "Validation passed" not in validation or PARSE_FAILURE in validation or broken:
        return "\n".join([validation.strip(), *broken, "Fix every parse failure above before checking."])
    for line in validation.splitlines():
        if "warning" in line.lower():
            print(line.strip())
    return None


def trim(output: str) -> str:
    lines = [line for line in output.splitlines() if not NOISE.match(line)]
    if len(lines) > MAX_OUTPUT_LINES:
        cut = len(lines) - MAX_OUTPUT_LINES
        keep_tail = MAX_OUTPUT_LINES - KEEP_HEAD_LINES
        lines = [*lines[:KEEP_HEAD_LINES], f"... {cut} lines cut ...", *lines[-keep_tail:]]
    return "\n".join(lines).strip()


def classify(output: str, scenario: bool) -> tuple[str, str]:
    """The verdict, and the name of the violated property when tla-rs printed one."""
    if PARSE_FAILURE in output:
        return "error", ""
    if scenario:
        if SCENARIO_ALLOWED in output:
            return "allowed", ""
        return ("blocked", "") if SCENARIO_BLOCKED in output else ("error", "")
    if PASS_MARK in output:
        return "pass", ""
    if DEADLOCK_MARK in output:
        return "deadlock", ""
    named = VIOLATED_NAME.search(output)
    if named:
        return "violation", next(name for name in named.groups() if name)
    return ("violation", "") if "violated" in output else ("error", "")


def fail(message: str) -> int:
    print(message)
    print("VERDICT: error")
    return EXIT_ERROR


def main() -> int:
    args = parse_args()
    if shutil.which("tla") is None:
        return fail(INSTALL_HINT)
    spec = args.spec.resolve()
    if not spec.is_file():
        return fail(f"spec not found: {args.spec}")
    config = (args.config or spec.with_suffix(".cfg")).resolve()
    if not config.is_file():
        return fail(
            f"config not found: {config}\n"
            "Write a .cfg with CONSTANTS, then SPECIFICATION and every INVARIANT and PROPERTY. "
            "Without one, tla-rs guesses which definitions are invariants from their names."
        )
    scenario = args.scenario.resolve() if args.scenario else None
    if scenario and not scenario.is_file():
        return fail(f"scenario file not found: {args.scenario}")
    base = [spec.name, "--config", str(config)]

    try:
        problem = validation_problem(spec, base, args.timeout)
    except subprocess.TimeoutExpired:
        return fail(f"TIMEOUT: validation did not finish in {args.timeout} s")
    if problem:
        return fail(problem)
    if args.validate_only:
        print("VERDICT: valid")
        return EXIT_PASS

    mode = ["--scenario", f"@{scenario}"] if scenario else []
    try:
        output = run_tla([*base, "--symbolic-integers", *mode, *args.tla_args], spec.parent, args.timeout)
    except subprocess.TimeoutExpired:
        return fail(
            f"TIMEOUT: no verdict in {args.timeout} s. Shrink the constants in {config.name}, "
            "or precompute an expensive constant definition (see the skill's gotchas)."
        )
    print(trim(output))
    if ignored_directives(output):
        return fail(
            f"tla-rs ignored the directives warned about above, so this run does not check what "
            f"{config.name} says. Remove them and restate each as an invariant or property in the module."
        )
    verdict, violated = classify(output, scenario is not None)
    print(f"VERDICT: {verdict}")
    if violated:
        print(f"VIOLATED: {violated}")
    if verdict == "error":
        return EXIT_ERROR
    if args.expect:
        matched = verdict == args.expect and args.expect_property in (None, violated)
        wanted = " ".join(filter(None, [args.expect, args.expect_property]))
        print(f"EXPECTED {wanted}: {'ok' if matched else 'MISMATCH'}")
        return EXIT_PASS if matched else EXIT_VIOLATION
    return EXIT_PASS if verdict in GOOD_VERDICTS else EXIT_VIOLATION


if __name__ == "__main__":
    sys.exit(main())
