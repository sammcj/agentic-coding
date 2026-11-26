------------------------------ MODULE LockMutex ------------------------------
(***************************************************************************)
(* Mutual exclusion by a single lock, in pure TLA+.  This module is the    *)
(* TLA+ half of a pair: LockMutex.lean states the same transition system   *)
(* and proves the same inductive invariant in Lean 4.  Read them side by   *)
(* side; every definition here has a definition of the same name there.    *)
(***************************************************************************)
CONSTANTS Proc, NoProc

ASSUME NoProcNotProc == NoProc \notin Proc

VARIABLES
  lock,   \* the process holding the lock, or NoProc
  pc      \* pc[p] is "idle" or "crit"

vars == <<lock, pc>>

TypeOK ==
  /\ lock \in Proc \cup {NoProc}
  /\ pc \in [Proc -> {"idle", "crit"}]

Init ==
  /\ lock = NoProc
  /\ pc = [p \in Proc |-> "idle"]

Acquire(p) ==
  /\ lock = NoProc
  /\ pc[p] = "idle"
  /\ lock' = p
  /\ pc' = [pc EXCEPT ![p] = "crit"]

Release(p) ==
  /\ pc[p] = "crit"
  /\ lock' = NoProc
  /\ pc' = [pc EXCEPT ![p] = "idle"]

Next == \E p \in Proc : Acquire(p) \/ Release(p)

Spec == Init /\ [][Next]_vars

MutualExclusion ==
  \A p, q \in Proc : (pc[p] = "crit" /\ pc[q] = "crit") => p = q

\* The inductive invariant: a process is critical exactly when it holds the lock.
Inv ==
  /\ TypeOK
  /\ \A p \in Proc : pc[p] = "crit" <=> lock = p

-----------------------------------------------------------------------------
(***************************************************************************)
(* The proof, in the hierarchical style TLAPS checks.  Its three           *)
(* obligations are exactly the three Lean theorems inv_init, inv_next and  *)
(* inv_mutex.  tla-rs skips this proof; to machine-check it with tlapm,    *)
(* add "EXTENDS TLAPS" and justify the temporal steps with "PTL".          *)
(***************************************************************************)
LEMMA InvInit == Init => Inv
  BY NoProcNotProc DEF Init, Inv, TypeOK

LEMMA InvNext == Inv /\ [Next]_vars => Inv'
<1> SUFFICES ASSUME Inv, [Next]_vars
             PROVE  Inv'
  OBVIOUS
<1>1. CASE UNCHANGED vars
  BY <1>1 DEF Inv, TypeOK, vars
<1>2. ASSUME NEW p \in Proc, Acquire(p)
      PROVE  Inv'
  BY <1>2, NoProcNotProc DEF Inv, TypeOK, Acquire
<1>3. ASSUME NEW p \in Proc, Release(p)
      PROVE  Inv'
  BY <1>3, NoProcNotProc DEF Inv, TypeOK, Release
<1>4. QED
  BY <1>1, <1>2, <1>3 DEF Next

LEMMA InvMutex == Inv => MutualExclusion
  BY DEF Inv, MutualExclusion

THEOREM Safety == Spec => []MutualExclusion
<1>1. Spec => []Inv
  BY InvInit, InvNext DEF Spec
<1>2. QED
  BY <1>1, InvMutex
=============================================================================
