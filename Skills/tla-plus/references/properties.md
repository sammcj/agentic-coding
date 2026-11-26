# Invariants, fairness and liveness

## Safety

- State the property in English first, then as a formula.
- `TypeOK` comes first. Then the properties the system exists to guarantee: mutual exclusion, agreement, validity, conservation.
- A state invariant (cfg `INVARIANT`) holds in every reachable state.
- An action property `[][A]_vars` (cfg `PROPERTY`) constrains every step. Use it when the claim is about a transition, such as "no use after revocation".
- A claim about the past needs a history variable.

## When an invariant fails

1. Read the trace as a behaviour of the real system.
2. If the real system can do this, the design has a bug. Report it with the trace.
3. If the real system cannot, the model allows too much. Find the missing guard or the action with the wrong grain.
4. If the behaviour is acceptable, the property is wrong. Rewrite it and give the reason in the report.

Case 4 is the only one that justifies weakening a property.

## Inductive invariants

A check run shows `Inv` holds in reachable states. It does not show `Inv` is inductive, meaning `Init => Inv` and `Inv /\ [Next]_vars => Inv'`. A proof needs the inductive form, and writing it explains why the design works.

- Strengthen by tying every message and every piece of state to its justification: "a commit message exists only if every participant voted yes".
- Put a paragraph in the module saying why each action preserves the invariant.

Test inductiveness on a small model. `assets/examples/ai/IndAgentToolLoop.tla` and its cfg show the whole pattern.

1. In a module that extends the spec, define `IndInit` as one typing conjunct per variable followed by `Inv`, and `IndSpec == IndInit /\ [][Next]_vars`. Every state satisfying `Inv` becomes an initial state.
2. Write each typing conjunct so the checker can enumerate it: `x \in SUBSET D`, never `x \subseteq D`, and a bounded set such as `UNION {[1..k -> S] : k \in 0..Max}` in place of `Seq(S)`.
3. In its cfg name `SPECIFICATION IndSpec`, `INVARIANT Inv` and `CHECK_DEADLOCK FALSE`. Final states are initial states here, so the deadlock check would fail on a correct invariant.
4. Run the check. A violation of `Inv` is a one-step counterexample to induction: add the missing conjunct and run again.

## Liveness

- Check safety first. Add liveness only when the task claims something eventually happens.
- Without fairness, a liveness property fails unless the initial state already satisfies it, because the spec may stutter forever.
- Put weak fairness on each action that must make progress: `WF_vars(Deliver)`. Fairness on `Next` as a whole does not make any particular action happen.
- Use strong fairness `SF_vars(A)` when other actions repeatedly disable `A`, as with processes competing for a lock.
- Put no fairness on failure actions (crash, message loss). A spec must not require failures.
- Keep the spec machine closed: assert fairness only on actions that are disjuncts of `Next`. Fairness on any other formula can leave a finite behaviour that `Init` and `Next` allow with no fair continuation, which turns a liveness assumption into a hidden safety constraint.
- A step that can fail forever defeats weak fairness. Either bound the failures with a budget constant, or make success its own action with strong fairness, which assumes a retried step eventually succeeds. Say which in the report.
- Shapes: `P ~> Q` for request and response, `<>[]P` for stabilisation, `[]<>P` for recurrence.

## Common failures

- The property is true of the real system but the model lacks the history variable needed to state it.
- A liveness property fails and the cause is missing fairness rather than a design error.
- The invariant mentions implementation detail that the model abstracted away.
- The invariant passes because the model never reaches the dangerous state. The broken-variant run in the workflow catches this.
