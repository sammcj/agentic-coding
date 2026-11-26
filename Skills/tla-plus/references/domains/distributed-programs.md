# Distributed programs

Questions to answer before modelling:

- What is the failure model (crash-stop, crash-recovery, message loss, duplication, reordering, Byzantine), and does the spec state it as actions?
- At what grain does each action run, and does the real system have that grain? Claiming a task and a compare-and-swap are the usual suspects.
- What happens to in-flight messages on a timeout? The spec must say.
- If liveness is claimed, which fairness on which actions provides it?

## Canonical models (tlaplus/Examples)

- **transaction_commit and TwoPhase** - https://github.com/tlaplus/Examples/tree/master/specifications/transaction_commit - one coordinator, n resource managers, safety under any interleaving. A set-valued `msgs` models reordering and duplication at no extra cost.
- **ewd998** (Safra termination detection) - https://github.com/tlaplus/Examples/tree/master/specifications/ewd998 - termination detection over asynchronous links, with fairness subtleties and token bookkeeping.
- **ewd840, chang_roberts, MisraReachability** - https://github.com/tlaplus/Examples/tree/master/specifications/ewd840 - token passing and ring leader election.
- **lamport_mutex, Bakery-Boulangerie** - https://github.com/tlaplus/Examples/tree/master/specifications/lamport_mutex - mutual exclusion without atomic registers, and unbounded counters in finite-state checking.
- **KeyValueStore, NanoBlockchain** - https://github.com/tlaplus/Examples/tree/master/specifications/KeyValueStore - snapshots and transactions as state machines.

## Production protocols

- **etcd Raft** - https://github.com/etcd-io/raft/tree/main/tla - a spec that tracks the Go code. https://github.com/Vanlightly/raft-tlaplus adds reconfiguration.
- **Tendermint and CometBFT** - https://github.com/tendermint/spec , https://github.com/cometbft/cometbft/tree/main/spec - consensus, light client and accountability specs used in production.

## Timeouts

tla-rs does not implement the `RealTime` standard module. Where "eventually" must become "within a bound", model each clock as an explicit variable with a tick action.

## PlusCal sources

Many published distributed algorithms are written in PlusCal. This skill reads PlusCal and writes pure TLA+ (`references/pluscal.md`).

- **PlusCal manual** - https://lamport.azurewebsites.net/tla/p-manual.pdf - the translation rules for labels, `await`, `with`, `either`, fairness keywords and `pc`.
- **PlusCal cheat sheet** - https://github.com/tlaplus/PlusCalCheatSheet - label placement rules.

## Bundled examples (re-checked by `scripts/verify_examples.py`)

- `assets/examples/distributed/TwoPhaseCommit.tla` - pure TLA+, set-based network, full inductive invariant.
- `assets/examples/distributed/RingLeaderElection.tla` - PlusCal with translation, FIFO ring links, `Elected` liveness under process fairness.
- `assets/examples/ai/MultiAgentOrchestrator.tla` - PlusCal with translation, shared task board, double-claim exclusion, bounded-failure liveness.

## How to use

1. Start from the smallest canonical model that shares your protocol's failure model. A shared API surface is no guide.
2. Give every point where the real system can interleave (send, receive, claim, commit) its own action. If unsure, split finely, check, then coarsen.
3. For Byzantine or quorum-based protocols read `consensus.md`.
