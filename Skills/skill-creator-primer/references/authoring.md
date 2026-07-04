# Authoring craft: on-demand sections

Single-branch guidance moved out of SKILL.md so it loads only when its branch applies. Contents:

- **Degrees of Freedom** - when creating a skill, deciding how prescriptive to make instructions.
- **Capture Intent from Conversation** - when the user says "turn this into a skill" or a workflow to capture already sits in the conversation.
- **Writing Scripts** - when the skill bundles scripts.
- **Examples: concise vs verbose** - when writing a section and unsure how terse to make it.

## Degrees of Freedom

Match specificity to the task's fragility and variability:

**High freedom** (text instructions): Multiple approaches valid, decisions depend on context, heuristics guide approach.

**Medium freedom** (pseudocode/parameterised scripts): Preferred pattern exists, some variation acceptable, configuration affects behaviour.

**Low freedom** (specific scripts, few parameters): Operations fragile and error-prone, consistency critical, specific sequence required.

Think of Claude exploring a path: a narrow bridge with cliffs needs guardrails (low freedom), an open field allows many routes (high freedom).

## Capture Intent from Conversation

When a user says "turn this into a skill", extract the workflow from the current conversation before asking questions. Look for:

- Tools used and the sequence of steps taken
- Corrections the user made along the way
- Input/output formats observed
- Patterns that repeated across the conversation

Fill gaps with the user, then proceed to skill creation.

## Writing Scripts

When a skill bundles scripts:

- **Solve, don't punt.** Handle error conditions in the script rather than failing and leaving the agent to improvise. A script that creates a missing file or falls back to a sensible default is more reliable than one that throws.
- **No voodoo constants.** Justify and document config values in a comment. If you can't explain why a timeout is 30s, the agent can't either.
- **State execution intent.** Make clear whether to run the script ("Run `extract_fields.py` to pull form fields") or read it as reference ("See `extract_fields.py` for the extraction algorithm"). Execution is usually preferred.
- **Lean on the standard library; declare real deps inline.** A stdlib-only script runs anywhere with no setup, so prefer it. When a script genuinely needs a third-party package, run it with `uv` and declare the dependency in [PEP-723](https://peps.python.org/pep-0723/) inline metadata at the top of the script - the dependency then travels with the file instead of relying on the environment being pre-provisioned.

## Examples: concise vs verbose

Good example (concise, actionable):

```
## Extract PDF text

Use pdfplumber for text extraction:

`python scripts/extract_pdf_text.py <pdf-file>`

```

Bad example (verbose):

```
## Extract PDF text

PDF (Portable Document Format) files are a common file format that contains
text, images, and other content. To extract text from a PDF, you'll need to
use a library. There are many libraries available for PDF processing, but
pdfplumber is recommended because it's easy to use and handles most cases well.
First, you'll need to install it using pip. Then you can use the code below...
```
