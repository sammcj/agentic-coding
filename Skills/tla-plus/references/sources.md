# Outside sources

Read the one or two entries that bear on the current question, take the modelling decision you came for, and return to the spec. Many of these specs were written for TLC and can use constructs tla-rs lacks.

## Foundations

- **Specifying Systems** (Lamport) - https://lamport.azurewebsites.net/tla/book.html - the definitive method. Chapter 7 (writing a spec) and chapter 8 (liveness and fairness) matter most.
- **Lamport's TLA+ home page** - https://lamport.azurewebsites.net/tla/tla.html - the map of all official material.
- **TLA+ video course** - https://lamport.azurewebsites.net/video/videos.html - for returning to state-machine thinking when an abstraction feels forced.
- **TLA+ Hyperbook** - https://lamport.azurewebsites.net/tla/hyperbook.html - unfinished, with realistic examples.

## Example collections

- **tlaplus/Examples** - https://github.com/tlaplus/Examples - puzzles, classical algorithms, Paxos variants, termination detection and industrial-style models. Start from the README table.
- Termination detection and classical algorithms in that repository: EWD687a, EWD840, EWD998, Huang, Misra reachability, Chang-Roberts, Dijkstra mutual exclusion, Echo. They expose fairness and stuttering subtleties.
- **BlockingQueue** (Markus Kuppe) - https://github.com/lemmy/BlockingQueue - a concurrent queue with a subtle deadlock.
- **muratdem/PlusCal-examples** - https://github.com/muratdem/PlusCal-examples
- **spacejam/tla-rust** - https://github.com/spacejam/tla-rust - lock-free and distributed Rust guided by TLA+.

## Operators

- **CommunityModules** - https://github.com/tlaplus/CommunityModules - vetted operator definitions. tla-rs implements only Naturals, Integers, Sequences, FiniteSets, TLC and Bags, so copy the pure TLA+ definition you need into your module.

## Proofs

- **TLAPS** - https://proofs.tlapl.us - machine-checked proofs inside the module, run by `tlapm` (OCaml, not bundled). The checker here parses proofs and skips them.
- LearnProofs and the other TLAPS-flagged examples in tlaplus/Examples.

## The checker

- **tla-rs** - https://github.com/fabracht/tla-rs - `TLA_SUPPORT.md` and `SYNTAX_STATUS.md` list the supported subset and each known difference from TLC.
