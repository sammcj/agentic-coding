------------------------------ MODULE Template ------------------------------
(***************************************************************************)
(* One paragraph: what this models.                                        *)
(*                                                                         *)
(* Abstraction decisions: what is left out, and why that cannot hide the   *)
(* errors of interest.                                                     *)
(*                                                                         *)
(* Grain of atomicity: what one step is, and why the real system performs  *)
(* it atomically.                                                          *)
(***************************************************************************)
EXTENDS Naturals

CONSTANTS
  Proc,       \* process identifiers (model values in the .cfg)
  NoProc,     \* sentinel for "no owner"
  MaxRounds   \* budget that keeps the model finite

ASSUME ConstantsOK ==
  /\ NoProc \notin Proc
  /\ MaxRounds \in Nat

VARIABLES
  owner,      \* the process holding the resource, or NoProc
  rounds      \* completed acquire/release rounds

vars == <<owner, rounds>>

TypeOK ==
  /\ owner \in Proc \cup {NoProc}
  /\ rounds \in 0..MaxRounds

Init ==
  /\ owner = NoProc
  /\ rounds = 0

Acquire(p) ==
  /\ owner = NoProc
  /\ rounds < MaxRounds
  /\ owner' = p
  /\ UNCHANGED rounds

Release(p) ==
  /\ owner = p
  /\ owner' = NoProc
  /\ rounds' = rounds + 1

Next == \E p \in Proc : Acquire(p) \/ Release(p)

\* Fairness sits on the actions that must make progress, never on failures.
Fairness == \A p \in Proc : WF_vars(Acquire(p)) /\ WF_vars(Release(p))

Spec == Init /\ [][Next]_vars /\ Fairness

-----------------------------------------------------------------------------
(***************************************************************************)
(* Inv is inductive: Acquire needs rounds < MaxRounds and leaves rounds    *)
(* alone; Release adds one round only while a process holds the resource,  *)
(* which Acquire allowed only below the budget.                            *)
(***************************************************************************)
Inv ==
  /\ TypeOK
  /\ owner # NoProc => rounds < MaxRounds

Finishes == <>(rounds = MaxRounds /\ owner = NoProc)
=============================================================================
