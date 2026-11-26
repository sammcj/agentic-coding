# Modelling a system as a state machine

## Variables

1. List every fact needed to state the properties of interest. Each must be a predicate over the variables.
2. Remove anything derivable from other variables, and pure implementation detail such as logs, buffers and temporaries.
3. Bound every domain so the checker can enumerate it.
4. Pick sets, functions or sequences by how the actions use the data. A network that reorders and duplicates is a set of messages. A FIFO link is a sequence.
5. Add a history variable (`log`, `approvals`, `used`, `leaked`) for any question about the past. A flag holding the current value cannot answer it.

TLA+ does not guarantee that values of different kinds are unequal. Where a set mixes shapes, use records with a `type` field.

## Grain of atomicity

The grain is what counts as one step. It decides whether the model can show the bugs that matter.

- One action is one step the real system performs atomically.
- Use the coarsest grain that still exposes the errors of interest. A coarser grain has fewer states and hides interleavings. A finer grain has more states and shows more bugs.
- Claim, validate and commit steps are where grains are most often too coarse. If the implementation reads and then writes, model two actions.
- Two actions that touch disjoint variables, and never enable or disable each other, can be merged without changing any property that cannot observe the state between them. Re-run the checks after merging.
- When unsure, split finely, check, then coarsen and confirm the verdicts match.
- Record the chosen grain and its justification in the module header comment.

## Actions

- An action is a guard over unprimed variables, an effect on primed variables, and `UNCHANGED` for every other variable.
- A variable that an action neither primes nor lists in `UNCHANGED` may take any value in the next state.
- The environment gets named actions too: message loss, crash, timeout, each move the adversary can make.
- Prefer several small actions to one large action wherever concurrency matters.

## Keeping the model checkable

- The product of the variable domains bounds the reachable state space. Estimate it before the first run and state it in the report.
- Shrink constants first: 2 or 3 processes, 2 values, a step budget. Most design errors appear in small models.
- For interchangeable identifiers use model values with `--symmetry` (see `tla --help`).
- A budget constant (`MaxSteps`, `MaxFailures`) makes an unbounded behaviour finite. The result then holds only up to that budget, and the report says so.

## Replaying a sample behaviour

Write the behaviour as a text file with one line per step:

- `action: Acquire` matches a step of that action.
- `action: Acquire; owner' = p1` adds a condition. Model values from the cfg can be named.
- `step: rounds' = 1` matches any step that satisfies the expression.

Run `python3 scripts/tla_check.py Spec.tla --scenario behaviour.txt`.

- `VERDICT: allowed`: the model permits the behaviour.
- `VERDICT: blocked`: the output lists the transitions available at the failing step. A guard is too strong or an action is missing.
- For a behaviour the design must forbid, add `--expect blocked`.
