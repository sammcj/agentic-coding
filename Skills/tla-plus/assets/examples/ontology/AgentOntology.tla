---------------------------- MODULE AgentOntology ----------------------------
(***************************************************************************)
(* An ontology for agents, in pure TLA+: a fixed terminology (TBox) of     *)
(* classes, and a changing set of assertions (ABox) about which agent      *)
(* belongs to which class and who has delegated what to whom.              *)
(*                                                                         *)
(* Abstraction decisions:                                                  *)
(*   - The TBox is CONSTANT: subclass edges, disjointness axioms, and the  *)
(*     actions each class grants.  Only the ABox changes.                  *)
(*   - Inference is a definition, not a step: Types(a) is the upward       *)
(*     closure of what is asserted, recomputed in every state.  No state   *)
(*     can hold a stale inference.                                         *)
(*   - Delegation is one level deep and only of capabilities the           *)
(*     delegator holds by its own classes.  That is what makes             *)
(*     NoEscalation inductive.                                             *)
(***************************************************************************)
CONSTANTS
  Agent,        \* individuals
  Class,        \* class names
  Action,       \* things an agent can be permitted to do
  SubClassOf,   \* set of <<sub, super>> pairs: the asserted hierarchy
  Disjoint,     \* set of <<c, d>> pairs that may share no member
  Grants        \* set of <<class, action>> pairs: membership permits action

(***************************************************************************)
(* Transitive closure of a binary relation given as a set of pairs.        *)
(* Close sits at module level because tla-rs does not parse RECURSIVE      *)
(* after another definition inside a LET.                                  *)
(***************************************************************************)
RECURSIVE Close(_, _)
Close(T, Field) ==
  LET T2 == T \cup {<<a, c>> \in Field \X Field :
                       \E b \in Field : <<a, b>> \in T /\ <<b, c>> \in T}
  IN  IF T2 = T THEN T ELSE Close(T2, Field)

TC(R) == Close(R, {r[1] : r \in R} \cup {r[2] : r \in R})

Sub == TC(SubClassOf)

ASSUME TBoxWellFormed ==
  /\ SubClassOf \subseteq Class \X Class
  /\ Disjoint \subseteq Class \X Class
  /\ Grants \subseteq Class \X Action
  /\ \A c \in Class : <<c, c>> \notin Sub        \* the hierarchy is acyclic

VARIABLES
  asserted,     \* asserted[a] is the set of classes directly asserted of a
  delegated     \* set of <<from, to, action>> delegations in force

vars == <<asserted, delegated>>

-----------------------------------------------------------------------------
(* Inference, as definitions over the current state. *)

Supers(c) == {c} \cup {d \in Class : <<c, d>> \in Sub}
TypesOf(S) == UNION {Supers(c) : c \in S}
Types(a) == TypesOf(asserted[a])

ConsistentSet(S) ==
  \A c, d \in TypesOf(S) : <<c, d>> \notin Disjoint /\ <<d, c>> \notin Disjoint

IntrinsicOf(S) == {act \in Action : \E c \in TypesOf(S) : <<c, act>> \in Grants}
Intrinsic(a) == IntrinsicOf(asserted[a])

\* The authorisation query the ontology answers.
Allowed(a, act) ==
  \/ act \in Intrinsic(a)
  \/ \E d \in Agent : <<d, a, act>> \in delegated

-----------------------------------------------------------------------------
TypeOK ==
  /\ asserted \in [Agent -> SUBSET Class]
  /\ delegated \subseteq Agent \X Agent \X Action

Init ==
  /\ asserted = [a \in Agent |-> {}]
  /\ delegated = {}

\* Assert that a is a c, unless that would put a in two disjoint classes.
Classify(a, c) ==
  /\ c \notin asserted[a]
  /\ ConsistentSet(asserted[a] \cup {c})
  /\ asserted' = [asserted EXCEPT ![a] = @ \cup {c}]
  /\ UNCHANGED delegated

\* Retract an assertion; delegations a can no longer back are revoked with it.
Retract(a, c) ==
  /\ c \in asserted[a]
  /\ LET S == asserted[a] \ {c}
     IN  /\ asserted' = [asserted EXCEPT ![a] = S]
         /\ delegated' = {t \in delegated : t[1] = a => t[3] \in IntrinsicOf(S)}

Delegate(a, b, act) ==
  /\ a # b
  /\ act \in Intrinsic(a)
  /\ delegated' = delegated \cup {<<a, b, act>>}
  /\ UNCHANGED asserted

Revoke(a, b, act) ==
  /\ <<a, b, act>> \in delegated
  /\ delegated' = delegated \ {<<a, b, act>>}
  /\ UNCHANGED asserted

Next ==
  \E a \in Agent :
    \/ \E c \in Class : Classify(a, c) \/ Retract(a, c)
    \/ \E b \in Agent, act \in Action : Delegate(a, b, act) \/ Revoke(a, b, act)

Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
(* The ABox never contradicts a disjointness axiom. *)
ABoxConsistent == \A a \in Agent : ConsistentSet(asserted[a])

(* Every delegation is backed by a capability its delegator holds now. *)
NoEscalation == \A t \in delegated : t[3] \in Intrinsic(t[1])

(* Anything allowed traces back to some class that grants it. *)
AllowedGrounded ==
  \A a \in Agent, act \in Action :
    Allowed(a, act) => \E c \in Class : <<c, act>> \in Grants

(***************************************************************************)
(* Inv is inductive: Classify only adds classes, so Intrinsic only grows;  *)
(* Retract filters out exactly the delegations it would orphan; Delegate   *)
(* checks Intrinsic directly; Revoke only removes.                         *)
(***************************************************************************)
Inv == TypeOK /\ ABoxConsistent /\ NoEscalation

THEOREM Spec => [](Inv /\ AllowedGrounded)
=============================================================================
