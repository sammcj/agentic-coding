# TLA+ syntax and configuration

Start a new module from `assets/Template.tla` and `assets/Template.cfg`. The one-page operator summary is at https://lamport.azurewebsites.net/tla/summary-standalone.pdf.

## Errors to prevent

- `==` defines. `=` is equality only.
- Inequality is `#` or `/=`, never `!=`.
- Use ASCII operators (`/\`, `\/`, `~`, `=>`, `\in`). No semicolons, no backticks.
- A module needs its `---- MODULE Name ----` header and `====` terminator, and the name must match the file name.
- `vars` lists every variable. Each action primes or lists in `UNCHANGED` every variable.
- Only variables are primed. Priming a constant or a definition over constants is an error.
- Parenthesise nested temporal operators.
- Recursive operators need a `RECURSIVE` declaration at module level.
- Write the complete module each time, from the header line to the terminator.

## TypeOK idioms

Write `TypeOK` first, one conjunct per variable, in the order of `vars`.

- scalar: `x \in 0..Max`
- set: `s \in SUBSET D`
- function: `f \in [D -> R]`
- record: `r \in [f1 : S1, f2 : S2]`
- sequence: `q \in Seq(M)` (membership only, the checker cannot enumerate `Seq`)
- nullable: `v \in D \cup {None}`, with `None` a sentinel constant and `ASSUME None \notin D`. A real value such as 0 or "" must not double as the sentinel.
- mixed message shapes: a union of record sets, one per message kind, each with a `type` tag field, as in `assets/examples/security/NeedhamSchroeder.tla`

Constants need types too: bound them (`Proc == 1..N`) or state an `ASSUME`.

## The .cfg file

- `SPECIFICATION Spec` names the formula to check. `INVARIANTS` and `PROPERTY` list every property. A property the cfg does not name is not checked.
- An unquoted name (`Proc = {p1, p2}`) is a model value: an atom equal only to itself. Use model values for process and token identifiers.
- A quoted value (`{"commit", "abort"}`) is a string. Use strings for message tags and enum-like fields.
- A cfg value can be a number, a string, a set or a tuple (`R = {<<"a", "b">>}`). To give a constant a computed value, define it in a separate `MC` module that extends the spec and substitute it with `<-`, as in `assets/examples/ontology/MCAgentOntology.tla`.
- A spec whose behaviours end needs `CHECK_DEADLOCK FALSE`, otherwise the final state is reported as a deadlock.

## Repairing a parse error

Fix the one construct the checker names and leave the surrounding logic alone. Then validate again.
