---------------------------- MODULE AgentToolLoop ----------------------------
(***************************************************************************)
(* A tool-using AI agent with a human approval gate, in pure TLA+.         *)
(*                                                                         *)
(* Abstraction decisions:                                                  *)
(*   - The language model is an adversarial oracle: Propose(t) may pick    *)
(*     ANY tool at ANY planning step.  Nothing about the model's           *)
(*     "intent" is assumed, so every safety property holds for every       *)
(*     possible model output, including prompt-injected ones.              *)
(*   - Tool results are not modelled; only the control flow that decides   *)
(*     whether a call may run.                                             *)
(*   - approvals and log are history variables: they record what was       *)
(*     approved and what ran so the safety property is a state predicate.  *)
(*   - steps bounds the loop (the agent's step budget), which also makes   *)
(*     termination provable under weak fairness.                           *)
(***************************************************************************)
EXTENDS Naturals, Sequences

CONSTANTS
  Tools,       \* every tool the agent can name
  Sensitive,   \* tools that need human approval before they run
  MaxSteps,    \* the step budget
  NoCall       \* a value that is not a tool

ASSUME ConstantsOK ==
  /\ Sensitive \subseteq Tools
  /\ MaxSteps \in Nat
  /\ NoCall \notin Tools

VARIABLES
  phase,       \* "plan", "review", "execute" or "done"
  pending,     \* the proposed tool call, or NoCall
  steps,       \* number of proposals made so far
  approvals,   \* history: set of <<step, tool>> pairs a human approved
  log          \* history: sequence of executed calls

vars == <<phase, pending, steps, approvals, log>>

Call == [step : 1..MaxSteps, tool : Tools]

TypeOK ==
  /\ phase \in {"plan", "review", "execute", "done"}
  /\ pending \in Tools \cup {NoCall}
  /\ steps \in 0..MaxSteps
  /\ approvals \in SUBSET ((1..MaxSteps) \X Sensitive)
  /\ log \in Seq(Call)

Init ==
  /\ phase = "plan"
  /\ pending = NoCall
  /\ steps = 0
  /\ approvals = {}
  /\ log = <<>>

-----------------------------------------------------------------------------
\* The model proposes a tool call.  Sensitive calls are routed to review.
Propose(t) ==
  /\ phase = "plan"
  /\ steps < MaxSteps
  /\ steps' = steps + 1
  /\ pending' = t
  /\ phase' = IF t \in Sensitive THEN "review" ELSE "execute"
  /\ UNCHANGED <<approvals, log>>

\* The human approves exactly the pending call at the current step.
Approve ==
  /\ phase = "review"
  /\ approvals' = approvals \cup {<<steps, pending>>}
  /\ phase' = "execute"
  /\ UNCHANGED <<pending, steps, log>>

\* The human denies; the call is dropped and never runs.
Deny ==
  /\ phase = "review"
  /\ pending' = NoCall
  /\ phase' = "plan"
  /\ UNCHANGED <<steps, approvals, log>>

Execute ==
  /\ phase = "execute"
  /\ log' = Append(log, [step |-> steps, tool |-> pending])
  /\ pending' = NoCall
  /\ phase' = "plan"
  /\ UNCHANGED <<steps, approvals>>

\* The model may stop at any planning step, and must once the budget is spent.
Finish ==
  /\ phase = "plan"
  /\ phase' = "done"
  /\ UNCHANGED <<pending, steps, approvals, log>>

Next ==
  \/ \E t \in Tools : Propose(t)
  \/ Approve
  \/ Deny
  \/ Execute
  \/ Finish

\* Weak fairness on Next as a whole is enough here, because every step either
\* ends the run or advances a phase cycle that spends the step budget.
Spec == Init /\ [][Next]_vars /\ WF_vars(Next)

-----------------------------------------------------------------------------
(* Safety: a sensitive tool runs only with an approval for that very call. *)
ApprovalGate ==
  \A i \in 1..Len(log) :
    log[i].tool \in Sensitive => <<log[i].step, log[i].tool>> \in approvals

(* Safety: an approval is never reused; each step executes at most once.   *)
NoReplay ==
  \A i, j \in 1..Len(log) : log[i].step = log[j].step => i = j

(***************************************************************************)
(* Inductive strengthening: the phase determines what pending may be, a    *)
(* call sitting in "execute" already satisfies the gate, and a pending call*)
(* belongs to a step that has not run yet.  IndAgentToolLoop.cfg checks    *)
(* that Inv is inductive.                                                  *)
(***************************************************************************)
Inv ==
  /\ TypeOK
  /\ ApprovalGate
  /\ NoReplay
  /\ (phase \in {"plan", "done"}) <=> (pending = NoCall)
  /\ phase = "review" => pending \in Sensitive
  /\ phase \in {"review", "execute"} => steps >= 1
  /\ phase = "execute" /\ pending \in Sensitive => <<steps, pending>> \in approvals
  /\ \A i \in 1..Len(log) :
       /\ log[i].step <= steps
       /\ phase \in {"review", "execute"} => log[i].step < steps

(* Liveness: the step budget forces the loop to end. *)
Termination == <>(phase = "done")

THEOREM Spec => []Inv /\ []NoReplay /\ Termination
=============================================================================
