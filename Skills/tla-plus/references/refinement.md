# Refinement and composition

## Refinement

A concrete spec refines an abstract spec when a refinement mapping makes every behaviour of the concrete spec a behaviour of the abstract one. The mapping gives each abstract variable as an expression over concrete variables. A concrete step that leaves the abstract state unchanged is a stutter and is allowed.

### Steps

1. Write and check the abstract spec first. It states the essential safety property with almost no mechanism.
2. Decide what detail the next level adds.
3. Write the concrete spec.
4. Write the mapping as an instance in the concrete module: `Abs == INSTANCE AbstractSpec WITH v <- expression`, where the expression uses concrete variables.
5. Check it: `python3 scripts/tla_check.py Concrete.tla -- --check-refinement Abs`. A violation shows a concrete step that is neither an abstract step nor a stutter.
6. That check covers safety only: initial states and steps. It ignores the abstract spec's fairness and liveness. To check a liveness property at the concrete level, restate it over the concrete variables and list it under `PROPERTY`. A definition that reaches it through the instance (`Abs!Live`) raises an error.
7. Prefer several small refinement steps to one large one.

### Pitfalls

- Claiming refinement with no explicit mapping.
- A mapping that needs information the concrete state lacks. Add a history variable to the concrete spec, or a prophecy variable when the abstract step depends on the future.
- Adding detail until the state space is intractable, before the abstract level has been checked.
- A model that cannot be shown to refine any simple abstract spec. The abstraction is wrong or the model is too concrete.

Come back to refinement when the state space becomes unmanageable or the invariants read like implementation detail.

## Composition

- `EXTENDS` imports another module's definitions. Use it for standard modules and shared definitions.
- `INSTANCE M WITH p <- e` instantiates a module under a substitution. Several instances of one module are normal, for example one channel module instantiated per link.
- Extended and instantiated modules must sit in the same directory as the spec.
- Design each module around its interface: the variables and actions other modules see.
- Make joint actions and the interleaving between components explicit in the composed `Next`.
- Model the environment as a component, so the composed spec is a closed system.
- Hiding internal variables with `\EE` cannot be checked here. Leave them visible in the checked module and name the internal ones in a comment.

## Specs to study

- **PaxosHowToWinATuringAward** - https://github.com/tlaplus/Examples/tree/master/specifications/PaxosHowToWinATuringAward - successive refinement from Consensus to Voting to Paxos. Read the mappings and which invariants survive each step.
- **Byzantizing Paxos by Refinement** - https://github.com/tlaplus/Examples/tree/master/specifications/byzpaxos - Byzantine consensus obtained by refining a non-Byzantine model.
- **Murat Demirbas, multi-grained specifications** - https://muratbuffalo.blogspot.com/2025/04/multi-grained-specifications-for.html - combining a protocol-level model with finer implementation detail.
- Smaller cases in tlaplus/Examples: Peterson lock with auxiliary variables, barrier synchronisation, transaction commit.
