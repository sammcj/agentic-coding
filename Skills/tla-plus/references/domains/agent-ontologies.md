# Ontologies for agents

A TBox (fixed terminology) is constant data, an ABox (assertions that change) is state, and inference is a definition over the current state. Because nothing caches an inference, no state can hold a stale one.

Questions to answer before modelling:

- What is TBox and what is ABox? A subclass relation held in a variable needs someone to maintain it, which is usually a bug.
- Is each inference computed from the current ABox, or cached in a variable? Cached inference is unsound.
- Where is each axiom enforced: by `ASSUME` on constants (disjointness, acyclicity), or by guards on the assert and retract actions?
- Can any derived relation lose its ground? In the example, `AllowedGrounded` shows every permission traces to a granting class.

## Mapping (worked in `assets/examples/ontology/`)

- Class: an element of the `Class` constant
- `rdfs:subClassOf`: a set of pairs `SubClassOf`, with subsumption as `TC(SubClassOf)`
- `owl:disjointWith`: a `Disjoint` set, enforced by the `Classify` guard and the `ABoxConsistent` invariant
- class membership (`rdf:type`): `asserted[a] \subseteq Class`, the ABox variable
- property or relation: a set of tuples, such as `delegated \subseteq Agent \X Agent \X Action`
- property granting capability: `Grants \subseteq Class \X Action`, with derived `Intrinsic` and `Allowed`
- constraint violation (SHACL-style): a state invariant plus an action guard
- inference or entailment: pure definitions (`Types`, `Allowed`), never actions

## Patterns

- **Acyclic hierarchy**: `ASSUME \A c \in Class : <<c, c>> \notin TC(SubClassOf)`, stated once on the constant TBox.
- **Cascade on retract**: `Retract` removes the delegations whose backing capability disappeared. Use the same shape for capability revocation, role changes and licence expiry.
- **Delegate only what you hold**: `Delegate` requires `act \in Intrinsic(a)`, which makes `NoEscalation` inductive. Loosen the guard and the checker produces the privilege-escalation trace.
- **Separation of duty as disjoint classes**: one `Disjoint` pair blocks every derived path. See `SeparationOfDuty` in `MCAgentOntology`.
- **Precomputed closure**: tla-rs recomputes a definition on every use (see the gotchas in `SKILL.md`). `MCAgentOntology` writes the closure as a literal `MCSub`, substitutes it with `<-`, and keeps it correct with `ASSUME MCSub = TC(MCSubClassOf)`.

## Standards

- **OWL 2 overview** - https://www.w3.org/TR/owl2-overview/ - classes, subclasses, disjointness, domains and ranges, property chains. Take the construct and express it as sets, closure and constraints.
- **OWL 2 primer** - https://www.w3.org/TR/owl2-primer/ - its examples translate directly into ABox assertions.
- **PROV-O** - https://www.w3.org/TR/prov-o/ - provenance. Agents, activities and entities become three sorts plus tuple sets, and provenance queries become reachability.
- **SHACL** - https://www.w3.org/TR/shacl/ - shapes map to invariants plus action guards.

## How to use

1. Write the TBox as `CONSTANT` plus `ASSUME` first, and check a concrete MC instance before the ABox exists.
2. Write every entailment rule as a definition, and every assertion or retraction as an action whose guard preserves the axioms.
3. Put the security question ("who may do what") in one derived predicate and check that it is grounded.
4. For provenance and audit, add the history variables described in `security.md`.
