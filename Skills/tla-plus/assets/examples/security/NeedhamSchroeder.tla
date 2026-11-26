-------------------------- MODULE NeedhamSchroeder --------------------------
(***************************************************************************)
(* The Needham-Schroeder public-key protocol with a Dolev-Yao intruder,    *)
(* in pure TLA+.  With Fix = FALSE, the checker finds Lowe's               *)
(* man-in-the-middle attack.  With Fix = TRUE (Lowe's fix: the responder   *)
(* names itself in message 2) both properties hold.                        *)
(*                                                                         *)
(*   1.  A -> p : {Na, A}_pk(p)                                            *)
(*   2.  B -> A : {Na, Nb}_pk(A)        Fix adds B:  {Na, Nb, B}_pk(A)     *)
(*   3.  A -> p : {Nb}_pk(p)                                               *)
(*                                                                         *)
(* Abstraction decisions:                                                  *)
(*   - Perfect cryptography: a ciphertext is a record tagged with the      *)
(*     agent whose public key encrypts it; only that agent reads it.       *)
(*   - The intruder I is a legitimate participant that also controls the   *)
(*     network: it sees every message, decrypts those under its own key,   *)
(*     and can deliver any message it can build from nonces it knows.      *)
(*   - Forgery is folded into delivery (Deliverable) instead of being a    *)
(*     separate "intruder sends" action.  The reachable behaviours are the *)
(*     same and the state space stays small.                               *)
(*   - One session: A initiates once with a peer of its choosing, B        *)
(*     responds once.  This is enough to exhibit the attack.               *)
(***************************************************************************)
CONSTANTS A, B, I, Na, Nb, Ni, None, Fix

ASSUME Fix \in BOOLEAN

Agents == {A, B, I}
Nonces == {Na, Nb, Ni}

Msg1 == [type : {"m1"}, key : Agents, nonce : Nonces, from : Agents]
Msg2 == [type : {"m2"}, key : Agents, n1 : Nonces, n2 : Nonces,
         from : Agents \cup {None}]
Msg3 == [type : {"m3"}, key : Agents, nonce : Nonces]
Message == Msg1 \cup Msg2 \cup Msg3

NoncesIn(m) ==
  CASE m.type = "m1" -> {m.nonce}
    [] m.type = "m2" -> {m.n1, m.n2}
    [] m.type = "m3" -> {m.nonce}

VARIABLES
  msgs,      \* every ciphertext an honest agent has sent
  known,     \* the nonces the intruder knows
  aState,    \* "idle", "waiting" or "done"
  aPeer,     \* whom A believes it is talking to
  bState,    \* "idle", "waiting" or "done"
  bPeer      \* whom B believes it is talking to

vars == <<msgs, known, aState, aPeer, bState, bPeer>>

TypeOK ==
  /\ msgs \subseteq Message
  /\ known \subseteq Nonces
  /\ aState \in {"idle", "waiting", "done"}
  /\ aPeer \in {B, I, None}
  /\ bState \in {"idle", "waiting", "done"}
  /\ bPeer \in Agents \cup {None}

Init ==
  /\ msgs = {}
  /\ known = {Ni}
  /\ aState = "idle"
  /\ aPeer = None
  /\ bState = "idle"
  /\ bPeer = None

-----------------------------------------------------------------------------
(* What the network can hand to an honest agent: a message an honest agent *)
(* really sent (replay), or one the intruder can build from known nonces.  *)
Deliverable(m) == m \in msgs \/ NoncesIn(m) \subseteq known

\* Sending discloses to the intruder whatever is encrypted under I's key.
Send(m) ==
  /\ msgs' = msgs \cup {m}
  /\ known' = IF m.key = I THEN known \cup NoncesIn(m) ELSE known

AStart(p) ==
  /\ aState = "idle"
  /\ aState' = "waiting"
  /\ aPeer' = p
  /\ Send([type |-> "m1", key |-> p, nonce |-> Na, from |-> A])
  /\ UNCHANGED <<bState, bPeer>>

BRespond(m) ==
  /\ bState = "idle"
  /\ m.type = "m1" /\ m.key = B
  /\ Deliverable(m)
  /\ bState' = "waiting"
  /\ bPeer' = m.from
  /\ Send([type |-> "m2", key |-> m.from, n1 |-> m.nonce, n2 |-> Nb,
           from |-> IF Fix THEN B ELSE None])
  /\ UNCHANGED <<aState, aPeer>>

AFinish(m) ==
  /\ aState = "waiting"
  /\ m.type = "m2" /\ m.key = A /\ m.n1 = Na
  /\ Fix => m.from = aPeer
  /\ Deliverable(m)
  /\ aState' = "done"
  /\ Send([type |-> "m3", key |-> aPeer, nonce |-> m.n2])
  /\ UNCHANGED <<aPeer, bState, bPeer>>

BFinish(m) ==
  /\ bState = "waiting"
  /\ m.type = "m3" /\ m.key = B /\ m.nonce = Nb
  /\ Deliverable(m)
  /\ bState' = "done"
  /\ UNCHANGED <<msgs, known, aState, aPeer, bPeer>>

Next ==
  \/ \E p \in {B, I} : AStart(p)
  \/ \E m \in Message : BRespond(m) \/ AFinish(m) \/ BFinish(m)

Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
(* Secrecy: if B finishes a run it believes is with A, B's nonce is secret. *)
Secrecy == (bState = "done" /\ bPeer = A) => Nb \notin known

(* Authentication: if B finishes believing it talks to A, A was running    *)
(* the protocol with B.                                                    *)
Authentication == (bState = "done" /\ bPeer = A) => aPeer = B

THEOREM Fix => (Spec => [](Secrecy /\ Authentication))
=============================================================================
