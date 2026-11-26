----------------------- MODULE MultiAgentOrchestrator -----------------------
(***************************************************************************)
(* A pool of worker agents draining a shared task board, in PlusCal        *)
(* (C-syntax).  A worker claims a task, then either completes it or        *)
(* fails and returns it to the board.                                      *)
(*                                                                         *)
(* Abstraction decisions:                                                  *)
(*   - Claiming is one atomic step (test the board, pick a task, remove    *)
(*     it).  This is the property a real task queue must provide; if the   *)
(*     implementation cannot, split the "claim" label and watch the        *)
(*     checker find the double-claim.                                      *)
(*   - Agent failure (crash, refusal, bad output) is one nondeterministic  *)
(*     branch.  MaxFailures bounds it so AllDone holds under weak          *)
(*     fairness.  The alternative is a separate completion action with     *)
(*     strong fairness, which assumes a retried task eventually succeeds.  *)
(***************************************************************************)
EXTENDS Naturals, FiniteSets

CONSTANTS Workers, Tasks, NoTask, MaxFailures

ASSUME ConstantsOK ==
  /\ NoTask \notin Tasks
  /\ MaxFailures \in Nat

(* --algorithm MultiAgentOrchestrator {

  variables
    todo = Tasks,                          \* unclaimed tasks
    claimed = [w \in Workers |-> NoTask],  \* the task each worker holds
    results = {},                          \* completed tasks
    failures = 0;                          \* failed attempts so far

  define {
    Held == {claimed[w] : w \in Workers} \ {NoTask}

    TypeOK ==
      /\ todo \subseteq Tasks
      /\ claimed \in [Workers -> Tasks \cup {NoTask}]
      /\ results \subseteq Tasks
      /\ failures \in 0..MaxFailures

    \* No task is ever held by two workers.
    NoDoubleClaim ==
      \A w1, w2 \in Workers :
        (w1 # w2 /\ claimed[w1] # NoTask) => claimed[w1] # claimed[w2]

    \* Every task is in exactly one place: on the board, held, or done.
    Conservation ==
      /\ todo \cup Held \cup results = Tasks
      /\ todo \cap Held = {}
      /\ todo \cap results = {}
      /\ Held \cap results = {}

    AllDone == <>(results = Tasks)
  }

  fair process (worker \in Workers) {
    claim:
      while (todo # {} \/ Held # {}) {
        await todo # {};
        with (t \in todo) {
          claimed[self] := t;
          todo := todo \ {t};
        };
    work:
        either {
          results := results \cup {claimed[self]};
        } or {
          await failures < MaxFailures;
          failures := failures + 1;
          todo := todo \cup {claimed[self]};
        };
        claimed[self] := NoTask;
      }
  }
} *)
\* BEGIN TRANSLATION
VARIABLES todo, claimed, results, failures, pc

(* define statement *)
Held == {claimed[w] : w \in Workers} \ {NoTask}

TypeOK ==
  /\ todo \subseteq Tasks
  /\ claimed \in [Workers -> Tasks \cup {NoTask}]
  /\ results \subseteq Tasks
  /\ failures \in 0..MaxFailures


NoDoubleClaim ==
  \A w1, w2 \in Workers :
    (w1 # w2 /\ claimed[w1] # NoTask) => claimed[w1] # claimed[w2]


Conservation ==
  /\ todo \cup Held \cup results = Tasks
  /\ todo \cap Held = {}
  /\ todo \cap results = {}
  /\ Held \cap results = {}

AllDone == <>(results = Tasks)


vars == << todo, claimed, results, failures, pc >>

ProcSet == (Workers)

Init == (* Global variables *)
        /\ todo = Tasks
        /\ claimed = [w \in Workers |-> NoTask]
        /\ results = {}
        /\ failures = 0
        /\ pc = [self \in ProcSet |-> "claim"]

claim(self) == /\ pc[self] = "claim"
               /\ IF todo # {} \/ Held # {}
                     THEN /\ todo # {}
                          /\ \E t \in todo:
                               /\ claimed' = [claimed EXCEPT ![self] = t]
                               /\ todo' = todo \ {t}
                          /\ pc' = [pc EXCEPT ![self] = "work"]
                     ELSE /\ pc' = [pc EXCEPT ![self] = "Done"]
                          /\ UNCHANGED << todo, claimed >>
               /\ UNCHANGED << results, failures >>

work(self) == /\ pc[self] = "work"
              /\ \/ /\ results' = (results \cup {claimed[self]})
                    /\ UNCHANGED <<todo, failures>>
                 \/ /\ failures < MaxFailures
                    /\ failures' = failures + 1
                    /\ todo' = (todo \cup {claimed[self]})
                    /\ UNCHANGED results
              /\ claimed' = [claimed EXCEPT ![self] = NoTask]
              /\ pc' = [pc EXCEPT ![self] = "claim"]

worker(self) == claim(self) \/ work(self)

(* Allow infinite stuttering to prevent deadlock on termination. *)
Terminating == /\ \A self \in ProcSet: pc[self] = "Done"
               /\ UNCHANGED vars

Next == (\E self \in Workers: worker(self))
           \/ Terminating

Spec == /\ Init /\ [][Next]_vars
        /\ \A self \in Workers : WF_vars(worker(self))

Termination == <>(\A self \in ProcSet: pc[self] = "Done")

\* END TRANSLATION

\* A define block cannot mention pc, so its type is stated here.
ProcTypeOK == pc \in [Workers -> {"claim", "work", "Done"}]

=============================================================================
