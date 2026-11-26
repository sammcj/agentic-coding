# Industrial systems and databases

Questions to answer before modelling a production system:

- Which operational constraint forces the complexity: reconfiguration, several data centres, power failure, or a client-facing consistency contract?
- Which class of bug has testing and review already missed?
- How will the model stay checkable at this scale?

## What the published cases show

- **Deep traces.** The DynamoDB replication bug needed a 35-step trace and had survived design review, code review and fault injection. Keep constants small and let the checker go deep.
- **Reuse the spec when the design changes.** The same DynamoDB spec exposed a new design bug when cross-data-centre migration was added, before any code existed.
- **Check the fix.** The Kafka replication model found data-loss cases, and then found a bug in the first proposed fix.
- **Specify the client's view.** Cosmos DB's five consistency levels fit in about 390 lines written from the client's side, and the spec exposed errors in the public documentation.
- **Check traces against the running system.** MongoDB and etcd validate implementation traces against their specs. See `references/code-to-spec.md`.

Sources: https://lamport.azurewebsites.net/tla/industrial-use.html and "How Amazon Web Services Uses Formal Methods" (CACM 2015), https://lamport.azurewebsites.net/tla/formal-methods-amazon.pdf.

## Open specs to study

- **Elasticsearch** - https://github.com/elastic/elasticsearch-formal-models - replication and replica engine behaviour.
- **TiDB** - https://github.com/pingcap/tla-plus - Raft plus distributed transactions.
- **MongoDB replication** - https://github.com/visualzhou/mongo-repl-tla - with trace checking against the real system.
- **Kafka replication** - https://github.com/hachikuji/kafka-specification - the ISR-based protocol.
- **Azure Cosmos DB** - https://github.com/Azure/azure-cosmos-tla - consistency levels.
- **Signal SVR2** - https://github.com/signalapp/SecureValueRecovery2/blob/main/docs/svr2.tla
- **More** (BookKeeper, Ceph, Xen vchan, Linux kernel primitives): the real-world section of https://github.com/tlaplus/awesome-tlaplus

## How to use

1. Pick the open spec whose failure model is closest to the system in front of you.
2. Read how it bounds the model: which constants, which budgets, what it leaves out.
3. Take the one abstraction decision or bug class that applies, and return to your own spec.
