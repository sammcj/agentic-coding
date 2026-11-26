------------------------- MODULE RingLeaderElection -------------------------
(***************************************************************************)
(* Chang-Roberts leader election on a unidirectional ring, in PlusCal      *)
(* (P-syntax).  Node identifiers are 1..N; the highest identifier wins.    *)
(*                                                                         *)
(* Abstraction decisions:                                                  *)
(*   - Each link is a FIFO queue inbox[n]; links are reliable.             *)
(*   - Label placement fixes the grain of atomicity: "recv" dequeues one   *)
(*     message, "decide" forwards, swallows, or declares leadership.       *)
(*   - "fair process" asserts weak fairness of each node's steps, which    *)
(*     is what the liveness property Elected needs.                        *)
(***************************************************************************)
EXTENDS Naturals, Sequences, FiniteSets

CONSTANT N
ASSUME NIsPositive == N \in Nat \ {0}

Node == 1..N
Succ(n) == IF n = N THEN 1 ELSE n + 1

(* --algorithm RingLeaderElection

variables
  inbox = [n \in Node |-> <<>>],
  leader = {};

define
  TypeOK ==
    /\ inbox \in [Node -> Seq(Node)]
    /\ leader \subseteq Node

  AtMostOneLeader == Cardinality(leader) <= 1
  OnlyMaxWins == leader \subseteq {N}

  \* A token t waiting in inbox[n] has travelled Hops(t, n) links.
  Hops(t, n) == IF n = t THEN N ELSE (n - t + N) % N

  \* Every node a token has already passed is smaller than the token.
  TokensAhead ==
    \A n \in Node : \A i \in 1..Len(inbox[n]) :
      LET t == inbox[n][i]
      IN  \A k \in Node \ {t} : Hops(t, k) < Hops(t, n) => k < t

  Elected == <>(leader = {N})
end define;

fair process node \in Node
variable m = 0;
begin
  start:
    inbox[Succ(self)] := Append(inbox[Succ(self)], self);
  recv:
    while TRUE do
      await inbox[self] # <<>>;
      m := Head(inbox[self]);
      inbox[self] := Tail(inbox[self]);
  decide:
      if m = self then
        leader := leader \cup {self};
      elsif m > self then
        inbox[Succ(self)] := Append(inbox[Succ(self)], m);
      end if;
    end while;
end process;

end algorithm; *)
\* BEGIN TRANSLATION
VARIABLES inbox, leader, pc

(* define statement *)
TypeOK ==
  /\ inbox \in [Node -> Seq(Node)]
  /\ leader \subseteq Node

AtMostOneLeader == Cardinality(leader) <= 1
OnlyMaxWins == leader \subseteq {N}


Hops(t, n) == IF n = t THEN N ELSE (n - t + N) % N


TokensAhead ==
  \A n \in Node : \A i \in 1..Len(inbox[n]) :
    LET t == inbox[n][i]
    IN  \A k \in Node \ {t} : Hops(t, k) < Hops(t, n) => k < t

Elected == <>(leader = {N})

VARIABLE m

vars == << inbox, leader, pc, m >>

ProcSet == (Node)

Init == (* Global variables *)
        /\ inbox = [n \in Node |-> <<>>]
        /\ leader = {}
        (* Process node *)
        /\ m = [self \in Node |-> 0]
        /\ pc = [self \in ProcSet |-> "start"]

start(self) == /\ pc[self] = "start"
               /\ inbox' = [inbox EXCEPT ![Succ(self)] = Append(inbox[Succ(self)], self)]
               /\ pc' = [pc EXCEPT ![self] = "recv"]
               /\ UNCHANGED << leader, m >>

recv(self) == /\ pc[self] = "recv"
              /\ inbox[self] # <<>>
              /\ m' = [m EXCEPT ![self] = Head(inbox[self])]
              /\ inbox' = [inbox EXCEPT ![self] = Tail(inbox[self])]
              /\ pc' = [pc EXCEPT ![self] = "decide"]
              /\ UNCHANGED leader

decide(self) == /\ pc[self] = "decide"
                /\ IF m[self] = self
                      THEN /\ leader' = (leader \cup {self})
                           /\ inbox' = inbox
                      ELSE /\ IF m[self] > self
                                 THEN /\ inbox' = [inbox EXCEPT ![Succ(self)] = Append(inbox[Succ(self)], m[self])]
                                 ELSE /\ TRUE
                                      /\ inbox' = inbox
                           /\ UNCHANGED leader
                /\ pc' = [pc EXCEPT ![self] = "recv"]
                /\ m' = m

node(self) == start(self) \/ recv(self) \/ decide(self)

(* Allow infinite stuttering to prevent deadlock on termination. *)
Terminating == /\ \A self \in ProcSet: pc[self] = "Done"
               /\ UNCHANGED vars

Next == (\E self \in Node: node(self))
           \/ Terminating

Spec == /\ Init /\ [][Next]_vars
        /\ \A self \in Node : WF_vars(node(self))

Termination == <>(\A self \in ProcSet: pc[self] = "Done")

\* END TRANSLATION

\* A define block cannot mention pc or process variables, so their types are stated here.
ProcTypeOK ==
  /\ pc \in [Node -> {"start", "recv", "decide"}]
  /\ m \in [Node -> 0..N]

=============================================================================
