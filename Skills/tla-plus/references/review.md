# Reviewing a spec

## Run it before judging it

1. Check the spec with the author's own `.cfg`: `python3 scripts/tla_check.py Spec.tla`. Record the verdict and the state count.
2. Compare the cfg with the module. List every property the module defines, or claims in a `THEOREM`, that the cfg does not name. Those claims are unchecked.
3. Break it. Remove one guard, or flip the constant that enables a known attack, and run with `--expect violation --expect-property Name`. A spec that still passes has a property too weak to matter.
4. When the author claims an invariant is inductive, test it (see `properties.md`).

## What to examine

- **Sample behaviours**: can the model perform the normal run and the feared failure? Replay them with `--scenario` (see `modelling.md`).
- **Abstraction**: is each omission stated, and can any omission hide the errors of interest?
- **Grain**: does each action match a step the real system performs atomically?
- **TypeOK**: one conjunct per variable, sentinels excluded by `ASSUME`.
- **Actions**: named, guarded, with `UNCHANGED` for every other variable.
- **Invariants**: do they state what the system must guarantee, or only facts about the model?
- **Fairness**: present only where liveness is claimed, on progress actions only, machine closed.
- **Bounds**: are the constants large enough to exhibit the protocol, for example enough processes for two quorums to disagree?
- **Fidelity**: does the model match this system, or a textbook protocol with the same name?
- **Refinement**: is there a simple abstract spec this protocol should refine, and is the mapping written down?
- **Clarity**: can an engineer read it and say what is specified and why the abstraction is right?

## Findings

Report findings most severe first, each with its evidence.

- **CRITICAL**: a property the system needs is violated. Include the trace.
- **HIGH**: a claimed property is not checked, a check cannot fail, or the model omits a behaviour the real system has. Include the cfg line, the broken variant that still passed, or the missing action.
- **LOW**: clarity, naming, redundant variables, avoidable state space.

A finding with no trace, run or line reference is an opinion. Label it as one.
