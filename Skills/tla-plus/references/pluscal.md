# Working with PlusCal

No PlusCal translator runs here, because the only one is part of the Java tools. New specs are written in pure TLA+.

## A PlusCal file that already has its translation

- The TLA+ between `\* BEGIN TRANSLATION` and `\* END TRANSLATION` is what the checker reads. Check it as usual.
- Editing the algorithm comment changes nothing the checker sees. Make the change in the translated TLA+ and update the algorithm text to match, or convert the file to pure TLA+ and delete the algorithm.
- Tell the user which of the two you did.

## A PlusCal algorithm with no translation

Translate it by hand, one label at a time:

- Each label starts an atomic step. Everything from one label to the next becomes one TLA+ action.
- Add a `pc` variable: a function from process to label for a multi-process algorithm. Each action's guard includes `pc[self] = "label"` and its effect sets the next label.
- `x := e` becomes `x' = e`. Every variable the step does not assign goes in `UNCHANGED`.
- `either ... or` becomes a disjunction. `with v \in S` becomes `\E v \in S`.
- `await P` becomes a guard.
- `if` becomes `IF ... THEN ... ELSE` inside the action. A false test takes the else branch and the step still happens.
- `while` at a label behaves as an `if`: when the test holds, run the body and return to the same label, otherwise move to the next label.
- After `x := e`, later statements in the same step read the new value, so they refer to `x'` in the translation.
- `fair process` becomes `WF_vars(p(self))`: weak fairness on the disjunction of that process's label actions, which is weaker than fairness on each label. `fair+` gives strong fairness.
- A `define` block cannot mention `pc` or process variables. State their types in a definition after the translation, as the bundled examples do with `ProcTypeOK`.
- A process that reaches the end gets `pc[self] = "Done"`. Add `CHECK_DEADLOCK FALSE` to the cfg, or a stuttering action enabled when every process is done.

## Label placement decides the grain

- A missing label merges steps the real system interleaves, which hides races.
- An extra label only costs state space.
- When reviewing PlusCal, check each label-to-label block against what the implementation really does atomically.

The three PlusCal examples under `assets/examples/` (`RingLeaderElection`, `MultiAgentOrchestrator`, `TokenSession`) show algorithm and translation side by side. The PlusCal manual is at https://lamport.azurewebsites.net/tla/p-manual.pdf.
