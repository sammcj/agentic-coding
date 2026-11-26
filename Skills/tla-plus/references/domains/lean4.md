# TLA+ and Lean 4

A model checker exhausts small finite instances and returns counterexample traces. Lean proves a theorem for every parameter value and returns no trace. The two answer different questions about one system.

Questions to answer first:

- Is the claim about reachable states of a bounded model, or about all parameter values? The first belongs to the checker, the second to a proof.
- Is the invariant inductive? If the checker needed a strengthened `Inv`, the Lean proof needs the same one.
- Does the Lean side define reachability over behaviours (an inductive `Reachable`), or only single steps? Only the first corresponds to `Spec => []Inv`.

## Correspondence (pair in `assets/examples/lean4/`)

`LockMutex.tla` and `LockMutex.lean` use the same names and the same invariant.

- `VARIABLES lock, pc`: fields of `structure State`
- state predicate `Init`, `Inv`: definitions of type `State -> Prop`
- action `Next`: `State -> State -> Prop`
- `x' = e`, `EXCEPT`: a field update
- `Spec == Init /\ [][Next]_vars`: `inductive Reachable` (stuttering adds no states)
- `Spec => []P`: `forall s, Reachable s -> P s`
- `TypeOK`: mostly discharged by Lean's type checker
- checker counterexample: a goal that cannot be proved. A `sorry` only marks a gap nobody has proved yet.
- sentinel constant `NoProc`: `Option Proc` and `none`
- `InvInit`, `InvNext` lemmas: `inv_init`, `inv_next` theorems

What is checked: `scripts/verify_examples.py` checks `LockMutex.tla` every run, and `LockMutex.lean` only when `lean` is installed. The TLAPS proof inside `LockMutex.tla` is not machine-checked here, and its own comment lists the edits `tlapm` needs.

If the task needs the Lean half and `command -v lean` finds nothing, ask the user whether to install it. On macOS that is `brew install elan-init` then `elan default stable`. Other platforms: https://github.com/leanprover/elan. Install only after they agree.

## Division of work

1. Model check first. Shrink the parameters until the state space completes, and use the counterexample traces to debug the design.
2. Port the inductive invariant, which is stronger than the property, into Lean as `Inv`. Prove `inv_init`, `inv_next`, then safety by induction on `Reachable`.
3. Keep names identical across the pair so a reviewer can compare the mathematics.
4. State the scope of each result separately: "model-checked for 3 processes" and "proved in Lean for all `Proc`".

## Choosing a prover

- **TLAPS** - https://proofs.tlapl.us , https://github.com/tlaplus/tlapm - hierarchical proofs inside the TLA+ module, run by `tlapm` (OCaml, not bundled). Choose it when the audience reads TLA+.
- **Lean 4** - choose it when someone downstream needs a Lean term, tactic automation or mathlib.
- **Veil** - https://github.com/verse-lab/veil - a transition-system DSL in Lean 4 with state, actions and invariants. Study it when designing the Lean half of a pair.

## References

- **Theorem Proving in Lean 4** - https://lean-lang.org/theorem_proving_in_lean4/ - inductive propositions, structures, `DecidableEq`, tactic proofs.
- **Lean 4 language reference** - https://lean-lang.org/doc/reference/latest/
- **mathlib4** - https://github.com/leanprover-community/mathlib4 - import it when the spec's mathematics needs sets or lattices.
- **Lamport, "How to Write a Proof"** - https://lamport.azurewebsites.net/pubs/proof.pdf - the hierarchical proof style both systems share.
