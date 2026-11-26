--------------------------- MODULE MCAgentOntology ---------------------------
(***************************************************************************)
(* Model instance.  The TBox relations are defined here, beside the        *)
(* closure literal MCSub, and substituted with "<-" in the .cfg.           *)
(*                                                                         *)
(* MCSub is the closure written out as a literal.  tla-rs recomputes a     *)
(* definition on every use, and the recursive TC is expensive enough to    *)
(* make the check crawl.  The ASSUME keeps the literal equal to TC.        *)
(***************************************************************************)
EXTENDS AgentOntology

MCSubClassOf ==
  { <<"Executor", "AIAgent">>,
    <<"Auditor", "AIAgent">>,
    <<"CodeExecutor", "Executor">> }

MCSub ==
  { <<"Executor", "AIAgent">>,
    <<"Auditor", "AIAgent">>,
    <<"CodeExecutor", "Executor">>,
    <<"CodeExecutor", "AIAgent">> }

ASSUME MCSubIsClosure == MCSub = TC(MCSubClassOf)

MCDisjoint == { <<"Executor", "Auditor">> }

MCGrants ==
  { <<"AIAgent", "read">>,
    <<"Executor", "invoke_tool">>,
    <<"CodeExecutor", "run_code">>,
    <<"Auditor", "attest">> }

\* A CodeExecutor is inferred to be an Executor, so it can never audit.
SeparationOfDuty ==
  \A a \in Agent : ~({"CodeExecutor", "Auditor"} \subseteq Types(a))
=============================================================================
