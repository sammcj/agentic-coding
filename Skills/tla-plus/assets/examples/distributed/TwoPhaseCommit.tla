--------------------------- MODULE TwoPhaseCommit ---------------------------
(***************************************************************************)
(* Two-phase commit over an asynchronous network, in pure TLA+.            *)
(*                                                                         *)
(* Abstraction decisions:                                                  *)
(*   - The network is the set msgs of all messages ever sent.  A set (not  *)
(*     a queue) models reordering and duplication; never removing a        *)
(*     message models arbitrary delay.  Message loss is not modelled       *)
(*     because it cannot violate safety.                                   *)
(*   - Commit and Abort are broadcast, so they carry no destination.       *)
(*   - Each action is one local step of one participant: the grain of      *)
(*     atomicity is "receive one message, update local state, send".       *)
(***************************************************************************)
CONSTANT RM          \* the set of resource managers

VARIABLES
  rmState,           \* rmState[r] is the state of resource manager r
  tmState,           \* the state of the transaction manager
  tmPrepared,        \* the RMs from which the TM has received "Prepared"
  msgs               \* the set of all messages sent so far

vars == <<rmState, tmState, tmPrepared, msgs>>

Message ==
  [type : {"Prepared"}, rm : RM] \cup [type : {"Commit", "Abort"}]

TypeOK ==
  /\ rmState \in [RM -> {"working", "prepared", "committed", "aborted"}]
  /\ tmState \in {"init", "committed", "aborted"}
  /\ tmPrepared \subseteq RM
  /\ msgs \subseteq Message

Init ==
  /\ rmState = [r \in RM |-> "working"]
  /\ tmState = "init"
  /\ tmPrepared = {}
  /\ msgs = {}

-----------------------------------------------------------------------------
(* Transaction manager actions *)

TMRcvPrepared(r) ==
  /\ tmState = "init"
  /\ [type |-> "Prepared", rm |-> r] \in msgs
  /\ tmPrepared' = tmPrepared \cup {r}
  /\ UNCHANGED <<rmState, tmState, msgs>>

TMCommit ==
  /\ tmState = "init"
  /\ tmPrepared = RM
  /\ tmState' = "committed"
  /\ msgs' = msgs \cup {[type |-> "Commit"]}
  /\ UNCHANGED <<rmState, tmPrepared>>

TMAbort ==
  /\ tmState = "init"
  /\ tmState' = "aborted"
  /\ msgs' = msgs \cup {[type |-> "Abort"]}
  /\ UNCHANGED <<rmState, tmPrepared>>

(* Resource manager actions *)

RMPrepare(r) ==
  /\ rmState[r] = "working"
  /\ rmState' = [rmState EXCEPT ![r] = "prepared"]
  /\ msgs' = msgs \cup {[type |-> "Prepared", rm |-> r]}
  /\ UNCHANGED <<tmState, tmPrepared>>

RMChooseToAbort(r) ==
  /\ rmState[r] = "working"
  /\ rmState' = [rmState EXCEPT ![r] = "aborted"]
  /\ UNCHANGED <<tmState, tmPrepared, msgs>>

RMRcvCommit(r) ==
  /\ [type |-> "Commit"] \in msgs
  /\ rmState' = [rmState EXCEPT ![r] = "committed"]
  /\ UNCHANGED <<tmState, tmPrepared, msgs>>

RMRcvAbort(r) ==
  /\ [type |-> "Abort"] \in msgs
  /\ rmState' = [rmState EXCEPT ![r] = "aborted"]
  /\ UNCHANGED <<tmState, tmPrepared, msgs>>

Next ==
  \/ TMCommit
  \/ TMAbort
  \/ \E r \in RM :
       \/ TMRcvPrepared(r)
       \/ RMPrepare(r)
       \/ RMChooseToAbort(r)
       \/ RMRcvCommit(r)
       \/ RMRcvAbort(r)

Spec == Init /\ [][Next]_vars

-----------------------------------------------------------------------------
(* Safety: no two resource managers disagree on the outcome. *)
Consistent ==
  \A r1, r2 \in RM : ~(rmState[r1] = "aborted" /\ rmState[r2] = "committed")

(***************************************************************************)
(* Inductive strengthening.  Consistent alone is not inductive: it says    *)
(* nothing about messages in flight.  Inv ties each message and each       *)
(* terminal state to the fact that justifies it.                           *)
(***************************************************************************)
Inv ==
  /\ TypeOK
  /\ ([type |-> "Commit"] \in msgs) <=> (tmState = "committed")
  /\ ([type |-> "Abort"] \in msgs) <=> (tmState = "aborted")
  /\ tmState = "committed" => tmPrepared = RM
  /\ \A r \in RM :
       /\ r \in tmPrepared => [type |-> "Prepared", rm |-> r] \in msgs
       /\ [type |-> "Prepared", rm |-> r] \in msgs => rmState[r] # "working"
       /\ rmState[r] = "committed" => tmState = "committed"
       /\ rmState[r] = "aborted" /\ [type |-> "Prepared", rm |-> r] \in msgs
            => tmState = "aborted"

THEOREM Spec => [](TypeOK /\ Consistent)
=============================================================================
