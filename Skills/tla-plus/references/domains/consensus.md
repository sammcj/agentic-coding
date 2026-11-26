# Consensus and agreement

Questions to answer before modelling:

- What exact safety property is protected, and at what grain of atomicity?
- Where does the model abstract message loss, delay or process failure?
- Is there an abstract spec (single-value consensus, voting) that the protocol refines?
- Which constraint adds the most complexity: reconfiguration, linearisability under crash, or partial synchrony?

## Start here

- **PaxosHowToWinATuringAward** - https://github.com/tlaplus/Examples/tree/master/specifications/PaxosHowToWinATuringAward - Consensus refined to Voting refined to Paxos. Read the refinement mappings and the invariants each level preserves.
- **Paxos** (classic) - https://github.com/tlaplus/Examples/tree/master/specifications/Paxos - the protocol specified directly. Compare it with the refined version above.
- **byzpaxos** (Byzantizing Paxos by Refinement) - https://github.com/tlaplus/Examples/tree/master/specifications/byzpaxos - Byzantine consensus obtained by refining a non-Byzantine model. Shows what Byzantine tolerance costs in structure.
- **MultiPaxos, MultiPaxos-SMR, diskpaxos, SimplifiedFastPaxos, TencentPaxos** - all in tlaplus/Examples - leader-based, multi-decree and disk-based variants.

## Raft family

- **Raft** (Diego Ongaro) - https://github.com/ongardie/raft.tla - the formalisation that accompanied the Raft paper, split into leader election, log replication and safety.
- **etcd Raft** - https://github.com/etcd-io/raft/tree/main/tla - a spec maintained beside the Go implementation, with trace validation against the running code.
- **Atomix Raft and client sequencer** - https://github.com/atomix/atomix-tlaplus - adds linearisable client interaction. Read it when the client-facing contract matters.

## Modern and Byzantine variants

- **Flexible Paxos** - https://github.com/fpaxos/fpaxos-tlaplus
- **Egalitarian Paxos** - https://github.com/efficient/epaxos
- **Tendermint and CometBFT light client and accountability** - https://github.com/tendermint/spec - safety and fork accountability under partial synchrony.
- **Signal SVR2** - https://github.com/signalapp/SecureValueRecovery2/blob/main/docs/svr2.tla - Raft inside SGX enclaves.
- **Spire, HotStuff, CBC Casper, Just-in-Time Paxos** - listed in the real-world section of https://github.com/tlaplus/awesome-tlaplus - different trade-offs in latency, view change and accountability.
- **Dr. TLA+ series** - https://github.com/tlaplus/DrTLAPlus - sessions pairing an algorithm explanation with a reading of its TLA+ model (Paxos, Raft, ByzPaxos, TiDB).

## How to use

1. For any agreement task, write the abstract safety property first, in the style of the Consensus module in PaxosHowToWinATuringAward.
2. Move to a concrete variant only after that abstract property is checked.
3. When the model feels too concrete too early, go back to the refinement chain and add one level at a time.
