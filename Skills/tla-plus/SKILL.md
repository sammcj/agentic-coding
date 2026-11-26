---
name: tla-plus
description: Use when writing, model checking, reviewing or repairing a TLA+ or PlusCal spec, answering whether a concurrent algorithm satisfies a property, extracting a spec from code, or formally verifying a concurrent or distributed design.
disable-model-invocation: true
metadata:
  version: 2026-11-27
---

A spec is trusted because of checker runs. Every claim made about a spec names the run behind it: the constants, the properties checked, the state count.

The checker is `tla` ([tla-rs](https://github.com/fabracht/tla-rs), written in Rust). This skill uses no Java tooling, so TLC, SANY, Apalache and the PlusCal translator are unavailable. Write pure TLA+.

Run `command -v tla` before the first check. If it is missing, ask the user whether to install it with `cargo install tla-checker`, and install only after they agree, because it downloads and compiles a third-party package. If they decline, write the spec and report that nothing was checked.

## Workflow

To review or audit an existing spec, do steps 1 and 2, follow `references/review.md` in place of steps 3 to 8, then report as in step 9 with the findings in that file's format.

1. Create a task per step below, phrased with its completion criterion, then work them to completion. With no task tool, keep the list in your reply.
2. **Scope.** Read any existing `.tla` and `.cfg` files first. Then write one line for each of: the processes and their environment (network, clock, adversary); the failure model (crash, recovery, loss, duplication, reorder, Byzantine); what must never happen; what must eventually happen; the bounds of the model. Ask the user only what the code and documents cannot answer.
3. **Sample behaviours.** Before any module, write two behaviours as sequences of states: one normal run, and one containing the interleaving or failure most likely to break the design. Done when every step says which values change. The step boundaries give the grain of atomicity. Keep both in the module header comment, because step 6 replays them.
4. **Model in layers.** Start from `assets/Template.tla` and `assets/Template.cfg`. Write constants, variables and `TypeOK`, then `Init`, then one action at a time, then `Next` and `Spec`, then the properties. Begin the `.cfg` with `CONSTANTS` only, and add `SPECIFICATION`, `INVARIANTS` and `PROPERTY` as each definition appears, because a cfg that names a missing definition fails. After each layer run `python3 scripts/tla_check.py Spec.tla --validate-only` and fix what it reports before adding the next.
5. **Skeleton check.** Confirm all five before the first check run:
   - `TypeOK` has one conjunct per variable, and every sentinel is excluded from its real domain by an `ASSUME`.
   - `Init` assigns every variable.
   - `Next` is a disjunction of named actions, each with a guard, an effect, and `UNCHANGED` for every other variable.
   - At least one invariant beyond `TypeOK` states what the system must guarantee, with a comment arguing why each action preserves it.
   - The module header lists the abstraction decisions and the grain of atomicity.
6. **Check.** In the `.cfg`, name `SPECIFICATION` and every `INVARIANT` and `PROPERTY`, with the smallest constants that still exhibit the protocol. Replay both sample behaviours with `python3 scripts/tla_check.py Spec.tla --scenario FILE` until each prints `VERDICT: allowed` (file format in `references/modelling.md`). Then run `python3 scripts/tla_check.py Spec.tla` (`--help` lists the options). On a violation, read the trace as a behaviour and decide which is wrong: the model, the design or the property. Fix that one and run again. Done when a run prints `VERDICT: pass`.
   - When the design is wrong, keep that cfg as the failing variant. Put each candidate fix behind its own constant switch and check each alone before combining them. The smallest fix is the fewest switches that pass.
7. **Make it fail.** A model that cannot fail shows nothing. Add a second `.cfg`, or a constant switch, that removes a guard or enables a known attack, and run it with `--expect violation --expect-property Name`, naming the property you care about. Done when it prints `EXPECTED violation Name: ok`. A deadlock, or a different property failing, does not count. If the variant still passes, the property is too weak or the model never reaches the dangerous state.
8. **Liveness, when claimed.** Add it after safety passes. State the fairness assumption for each action that must make progress, and check the property through `PROPERTY` in the cfg. The template's `Fairness` and `Finishes` show the shape. Delete them when no liveness is claimed.
9. **Report.** Give:
   - the abstraction decisions: what the model leaves out and why
   - each run: cfg, constants, properties checked, verdict, states and depth
   - the scope: a pass for 3 processes is a bounded result, so say "checked for 3 processes", and name the checker and its version (`tla --version`)
   - what was not checked: larger bounds, liveness, proofs
   - for a design bug: the violating trace, restated in the system's own terms

## References

Read the one that matches the task in front of you.

- Choosing variables, the grain of atomicity or action boundaries -> `references/modelling.md`
- A parse error, a `TypeOK` idiom or a `.cfg` question -> `references/syntax.md`
- An invariant fails or needs strengthening, or the task claims liveness -> `references/properties.md`
- The source of truth is existing code -> `references/code-to-spec.md`
- Reviewing or auditing a spec someone else wrote -> `references/review.md`
- Two specs at different levels of detail, or more than one module -> `references/refinement.md`
- The input is PlusCal -> `references/pluscal.md`
- An outside spec, paper or tutorial to compare against -> `references/sources.md`
- Agreement, leader election, replicated logs, Byzantine faults -> `references/domains/consensus.md`
- Message passing, queues, timeouts, failure handling -> `references/domains/distributed-programs.md`
- A production-scale system, or a model that feels too clean -> `references/domains/industrial.md`
- Adversaries, secrecy, authentication, tokens -> `references/domains/security.md`
- LLM agents, tool calls, orchestrators -> `references/domains/ai-agents.md`
- Class hierarchies, roles, capabilities, delegation -> `references/domains/agent-ontologies.md`
- A proof for all parameter values, or Lean 4 -> `references/domains/lean4.md`

Checked examples sit under `assets/examples/`, and each domain reference names the ones that apply. `python3 scripts/verify_examples.py` re-checks all of them.

## Checker gotchas

These differ from TLC, which is what most published TLA+ assumes.

- **Unparsed definitions are warnings.** tla-rs skips a definition it cannot parse, still prints `Validation passed`, and can report a passing check. `tla_check.py` treats the warning as an error, so validate and check through it.
- **Only the cfg is checked.** A `THEOREM` is parsed and skipped, as are proof steps. With no cfg `INVARIANT`, tla-rs guesses invariants from definition names.
- **`RECURSIVE` after another definition inside a `LET` does not parse.** Declare recursive operators at module level.
- **Definitions are recomputed on every use.** An expensive constant-level definition, such as a recursive transitive closure, can slow a check by tens of times. Write its value as a literal in the `MC` module, substitute it with `<-`, and add an `ASSUME` that the literal equals the definition. See `assets/examples/ontology/`.
- **`Nat` and `Int` are silently bounded to 0..100 and -100..100** unless `--symbolic-integers` is set. `tla_check.py` sets it.
- **Ignored cfg directives.** tla-rs drops `ACTION_CONSTRAINT`, `ALIAS` and `POSTCONDITION` with a warning and still reports a pass. `tla_check.py` returns `VERDICT: error` for a cfg that uses one.
- **Unsupported syntax**: infix operators spelt with new symbols such as `++` (a predefined one such as `\oplus` can be defined), `\EE` and `\AA`, and the `RealTime` module. The full list is in the tla-rs `SYNTAX_STATUS.md`.
- **Trace arrows omit action arguments.** `--[ Acquire ]-->` does not say which process moved. Read the changed variables.
- **A timeout usually means the model is too big.** Shrink the constants before raising `--timeout`.
- **tla-rs is a young checker.** When a result carries real weight, say in the report that it has not been confirmed with TLC.
