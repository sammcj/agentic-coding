-------------------------- MODULE IndAgentToolLoop --------------------------
(***************************************************************************)
(* Checks that Inv in AgentToolLoop is inductive.  Every state satisfying  *)
(* Inv becomes an initial state, so a violation of Inv is a one-step       *)
(* counterexample to induction.                                            *)
(***************************************************************************)
EXTENDS AgentToolLoop

\* Seq(Call) cannot be enumerated, so the induction check bounds the log.
BoundedLog == UNION {[1..k -> Call] : k \in 0..MaxSteps}

\* The typing conjuncts come first, each in a form the checker can enumerate.
IndInit ==
  /\ phase \in {"plan", "review", "execute", "done"}
  /\ pending \in Tools \cup {NoCall}
  /\ steps \in 0..MaxSteps
  /\ approvals \in SUBSET ((1..MaxSteps) \X Sensitive)
  /\ log \in BoundedLog
  /\ Inv

IndSpec == IndInit /\ [][Next]_vars
=============================================================================
