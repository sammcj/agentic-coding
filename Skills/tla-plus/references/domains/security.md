# Security specifications

An attack is a counterexample trace, and the adversary is more nondeterminism in `Next`.

Questions to answer before modelling:

- Who is the adversary: a network controller (Dolev-Yao), a compromised participant (Byzantine), a holder of a stolen credential, or an honest-but-curious party? Write down the actions it can take.
- Which property: secrecy, authentication, authorisation or non-repudiation? Each has a different formula shape, listed below.
- Is cryptography idealised? Perfect-cryptography records (`[key |-> B, ...]`) are the right grain until the cryptography itself is the target.
- Does the property hold under every adversary interleaving? The adversary's actions must be enabled everywhere the real adversary could act.

## Adversary patterns in the bundled examples

- **Dolev-Yao intruder** (`assets/examples/security/NeedhamSchroeder.tla`): the intruder sees every message in `msgs`, learns what is encrypted under its own key, and delivers anything it can build from `known`. Forgery folds into delivery, which keeps the state space small. With `Fix = FALSE` the checker produces Lowe's man-in-the-middle attack. With `Fix = TRUE` secrecy and authentication hold.
- **Bearer-token lifecycle** (`assets/examples/security/TokenSession.tla`): unguessable tokens, a `leaked` history set, an attacker replaying exactly `leaked \cap valid`, and `NoUseAfterRevoke` as an action property.
- **Authorisation gate** (`assets/examples/ai/AgentToolLoop.tla`): a sensitive capability executes only behind an approval recorded for that call.
- **Delegation** (`assets/examples/ontology/AgentOntology.tla`): `NoEscalation` lets a delegator pass on only the powers it holds itself.

## Property shapes

- **Secrecy**: `honest-party-finished-with-honest-peer => secret \notin known`. Condition it on an honest run completing. In the example that is `bState = "done" /\ bPeer = A`.
- **Authentication**: `finished believing P => the other party ran believing Q`. This needs peer-recording variables such as `aPeer` and `bPeer`.
- **Authorisation**: `dangerous-action-executed => gate-was-satisfied-for-that-call`. Use history variables, since a flag can be reused.
- **Post-revocation safety**: the action property `[][new-use => token \notin revoked]_vars`. A state invariant cannot say that the use came after the revocation.
- **Non-escalation**: `delegation => delegator-holds-the-power-itself`.

## References

- **Lowe, "An attack on the Needham-Schroeder public-key authentication protocol"** - https://www.cs.ox.ac.uk/people/gavin.lowe/Security/Papers/NSFDR.ps - the attack the bundled module reproduces.
- **Signal SVR2** - https://github.com/signalapp/SecureValueRecovery2/blob/main/docs/svr2.tla - Raft inside SGX enclaves with an active adversary, as a protocol layer plus a threat-model layer.
- **Byzantizing Paxos and Tendermint accountability** - https://github.com/tlaplus/Examples/tree/master/specifications/byzpaxos , https://github.com/tendermint/spec - a Byzantine participant follows `Next` arbitrarily. Fork accountability is a security property stated as the existence of evidence.
- **Azure Cosmos DB** - https://github.com/Azure/azure-cosmos-tla - specs where the adversary is the network and storage stack.

## How to use

1. Write the adversary's actions into `Next` before the honest actions.
2. Keep two cfg files beside the spec: one where the attack must violate, one where the fix must pass. `scripts/verify_examples.py` shows the idiom with `NeedhamSchroederAttack.cfg`.
3. Use perfect-cryptography records and unguessable model values until the user names the cryptographic assumption under attack.
