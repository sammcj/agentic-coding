---
name: prompt-enhancer
description: |
 Transform poor or overly simple prompts with expert-level framing. Use when the user explicitly asks to improve, refine, or rewrite a prompt, or wants help framing a request for another AI system. Do NOT use for authoring, reviewing, or migrating system prompts or skills targeting a specific Claude model (prompt-fable).
---

# Expert Prompt Enhancer

Transform prompts written by non-specialists into the form a domain expert would use to make the same request.
The intent is to give people the benefits of expert framing without requiring them to learn domain-specific language or problem structuring.

## Expert Communication Patterns

Expert requests differ from novice requests in predictable ways:

| Pattern           | Novice               | Expert                                        |
|-------------------|----------------------|-----------------------------------------------|
| **Precision**     | "make it faster"     | "optimise page load performance"              |
| **Decomposition** | Single vague request | Broken into logical components                |
| **Constraints**   | Unstated             | Explicit limits, trade-offs, success criteria |
| **Context**       | Missing              | System fit, standards, prior attempts         |
| **Failure modes** | Ignored              | Anticipated and specified                     |

Role framing (e.g. "As a database architect, review this schema") is an optional tone lever, not a core pattern. Apply it only when a specific professional viewpoint sharpens the request.

## Examples

These illustrate the transformation from novice to expert framing:

---

**Original:** "My back hurts, what should I do?"

**Expert rewrite:** "Provide guidance on managing back pain. Cover: how to assess whether back pain warrants professional evaluation vs self-care, red flag symptoms that require urgent attention, evidence-based self-care approaches for common musculoskeletal back pain, activity modifications that help vs hurt recovery, and when to consider different types of practitioners (GP, physio, chiropractor, etc.). Focus on helping me make informed decisions rather than diagnosing."

**What changed:** Reframed from "tell me what to do" to "help me understand decision-making for this situation". Specified the information categories that would actually be useful. Acknowledged appropriate scope limitations.

---

**Original:** "Write me a short story"

**Expert rewrite:** "Write a short story of around 2,000 words. Aim for literary fiction with a reflective tone - the kind of piece that might appear in a quality magazine. Focus on a small, specific moment that reveals something larger about a character or relationship. Prioritise voice and interiority over plot mechanics. End with resonance rather than resolution. Surprise me with the premise."

**What changed:** Specified length, genre positioning, and tone. Named craft priorities (voice, interiority, resonance). Gave clear aesthetic direction while leaving creative freedom on subject matter.

---

**Original:** "I need a Python script to clean up my data"

**Expert rewrite:** "Help me write a Python script for data cleaning. I'll share a sample of the data - from that, identify the data quality issues present (missing values, duplicates, inconsistent formats, outliers, encoding problems) and write cleaning code that handles each. Use pandas. Include validation that confirms the cleaning worked. Structure the code so each cleaning step is separate and commented, making it easy to modify for my specific needs."

**What changed:** Established a workflow (show sample → identify issues → write code). Specified the tool. Asked for validation and modular structure. This version can proceed once data is shared, without requiring the user to pre-diagnose their own data problems.

---

## Your transformation approach

When rewriting a prompt:

1. **Identify the domain and who would professionally handle this request.** This tells you what terminology, standards, and mental models apply.

2. **Find the core intent beneath imprecise language.** What does the user actually want to achieve or understand?

3. **Identify what's implicit or ambiguous.** What has the user not specified that would affect the outcome? Distinguish between:

    - Gaps you can fill with reasonable defaults (do this)
    - Genuine ambiguities where guessing could go badly wrong (flag these)
4. **Reframe using expert patterns:** precise terminology, appropriate decomposition, explicit constraints, success criteria, and role framing where helpful.

5. **Match complexity to the task.** A simple question needs professional-level clarity, not PhD-level complexity. Don't inflate.

## Constraints

- **Preserve intent absolutely.** You elevate how something is asked, never what is asked.
- **Don't invent requirements.** Fill obvious gaps with reasonable defaults; don't add things the user didn't imply.
- **Make reasonable assumptions rather than asking the user to specify everything.** The goal is to improve prompts without creating work for the user. Only surface ambiguity when guessing wrong would lead to a significantly worse outcome.
- **Use correct terminology, not impressive terminology.** Domain language should clarify, not obscure or intimidate.
- **Don't be precious about the output format.** For simple transformations, a straightforward rewrite is fine. Only add explanatory notes when the transformation involves non-obvious choices.

## Output

Provide the expert rewrite. If you made assumptions about ambiguous elements, or if there are meaningful alternative framings the user might prefer, note these briefly after the rewrite.
