---
name: ambitious-model-use
description: "Use when the user asks to be more ambitious with an AI task: aim at the outcome behind it, work it like a field-leading expert from raw data, or bring in other fields. Do NOT use for plain prompt rewording; use prompt-enhancer."
disable-model-invocation: true
metadata:
  version: 2026-10-16
---

# Ambitious Model Use - Altitude, Depth and Range

## Workflow

1. Create a task per step below, each with its completion criterion.
2. Diagnose the request on each dimension:
   - **Altitude**: deliverable, or the outcome behind it? Strongest when the work ends in a meeting or decision; weak for open creative work.
   - **Depth**: raw data and the instruments a field-leading expert uses, or digested summaries? Fits any task the user wants done really well.
   - **Range**: only the field the task names on its surface? Strongest for creative work.
3. Pick the dimensions with the largest gap and write the rewritten brief using the techniques below. Read `references/examples.md` first for worked QBR, churn and homepage rewrites.
4. List the access the brief needs (a computer, installable tools, raw data via files or MCP connectors) and flag what is missing.
5. Name the outside judge: a tool, metric or held-out dataset the model runs. The model's own judgement does not count.
6. Present steps 2-5 to the user. Execute the brief only after the user confirms it, applying the Depth and Range techniques yourself.

## Altitude Techniques

- Ask the user "what do you want to happen next?" instead of assuming the goal. Only the user can answer it.
- Move from "fix crashes" to "keep the app crash-free". Durable outcomes need workflow changes first: crash-report access, a version-to-commit map, and machines to reproduce and verify fixes.
- Decompose open-ended goals ("go make money") into outcomes the model can verify.

## Depth Techniques

Models often change vocabulary without changing methods. Insist on the instruments the best practitioners use.

- Demand databases, statistical models, simulations or domain tools instead of markdown tables.
- Set unreasonable targets and call them reasonable (5 s load time needed -> ask for 200 ms). When the model calls something impossible, restate that it is solvable and have it keep going.
- Adversarially check assumptions against raw data: "We believe X. Try to reproduce that from the raw data."
- Produce new knowledge: build a simulation that reproduces historical data, then find the earliest unknown predictive signal and test it on held-out data.

Meta-prompt (adapt freely):

> I want a deeper version of this task, not a bigger one. Before rewriting it: (1) say what a top professional in this field would do here that I'm not asking for; (2) name the rawest material they would start from instead of what has already been digested for me; (3) name the specific methods and tools they would use; (4) say what, other than you or me, would show the result is right. Then rewrite my prompt to ask for exactly that.

## Range Techniques

Draw on fields that would have been too expensive to assemble before.

- Replace nouns with verbs (from _The Art of Innovation_). A quarterly review becomes "getting busy people to believe a story about cause and effect and to decide under uncertainty in 30 minutes".
- Assemble the crew: name the specialists you would summon if the stakes were extreme (analyst, journalist, editor, motion designer, a red team such as a short-seller or forensic accountant). Have the model do what each does with the tools each would use, including tools from outside the task's field (Blender for interior design). Role-play makes the transcript weirder without improving the outcome.
- Run the crew as parallel sub-agents or threads where the environment supports it, each applying one field's methods.
