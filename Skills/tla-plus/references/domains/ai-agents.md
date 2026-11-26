# AI agents and LLM-assisted specification

Two different jobs share this file: specifying a system that contains an AI component, and running a loop in which an LLM writes specs.

Questions to answer before modelling a system with an AI component:

- What does the model assume about the AI's output? The AI is a nondeterministic and possibly adversarial oracle: `\E t \in Tools : Propose(t)` proposes any tool. A spec that assumes it usually picks well is wrong.
- Which properties hold for every model output (safety, authorisation gates), and which only when the model cooperates (task completion)? Claim only the first kind.
- What makes the state space finite: step budgets, failure budgets, finite tool sets, history variables in place of free text?

## Rules for modelling an AI component

- An LLM or planner is a set-valued choice: `\E act \in Actions`. Encode no policy.
- Guardrails are state predicates and action guards: approval gates, capability checks, budgets (`steps < MaxSteps`). They hold whatever the model outputs, which covers prompt injection.
- Refusal, hallucination and tool error are extra branches of the action. Bound them with a budget, or liveness cannot hold, and say so.
- Accountability is a history variable (`log`, `approvals`, `used`). A flag holding the current value cannot answer an audit question.

## Bundled examples

- `assets/examples/ai/AgentToolLoop.tla` - the pattern for "AI proposes, system disposes". An approval gate is a state invariant, approval reuse is excluded by `NoReplay`, and termination follows from a step budget plus weak fairness. `IndAgentToolLoop.tla` checks that its invariant is inductive.
- `assets/examples/ai/MultiAgentOrchestrator.tla` - workers draining a shared task board: double-claim exclusion, task conservation, and liveness that depends on `MaxFailures`.
- `assets/examples/security/TokenSession.tla` - token theft as a nondeterministic `leaked` step.
- `assets/examples/ontology/AgentOntology.tla` - "what may this agent do" as an inferred predicate over classes and delegation.

For agent permission structure read `agent-ontologies.md`. For guardrails as protocol properties read `security.md`.

## LLM-written specs

- A generated spec counts only with a clean validation, a completed check run, and a demonstrated violation from a broken variant. Known failure modes are specs that parse and encode nothing, and properties that are claimed and never checked.
- **Specula** - https://github.com/specula-org/Specula - LLM synthesis of TLA+ from documentation and code with iterative repair.
- **SysMoBench** - https://github.com/specula-org/SysMoBench - a benchmark for generating specs of real systems. Use it to judge how hard a code-to-spec task is.
- **TLAi+ challenge** - https://foundation.tlapl.us/challenge/index.html - the TLA+ Foundation's programme for AI-assisted specification.
- **tla-rs** - https://github.com/fabracht/tla-rs - the checker this skill runs. It also ships an MCP server, `tla-mcp`.
- **Spectacle** - https://github.com/will62794/spectacle - explore a spec's behaviours in a browser.

## How to use

1. For a system with an AI component, start from `AgentToolLoop.tla` and replace the tool set and the gate. Keep the adversarial-oracle assumption unless the user states a verified property of the AI.
2. For an LLM writing specs, the loop is the deliverable: generate, validate, check, break, repair.
