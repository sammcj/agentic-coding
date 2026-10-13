# The HTML skill report

## Running it

```
uv run <skill-creator-primer>/scripts/render_report.py SKILL_DIR [--findings FILE|-] [--against OTHER_DIR] [-o OUT]
```

Writes one self-contained HTML file and prints the absolute path.

- Run it under `uv` so the spec cell has PyYAML and skills-ref.
- Output defaults to `~/Downloads`. Pass `-o` only when the user names another path, and keep it outside the skill directory: the primer's "What to Not Include in a Skill" rule covers stray files.
- `--against` takes another copy of the same skill - a git worktree at the previous commit, or a snapshot taken before a compression pass - and adds a before-and-after cell. Use it to show what a rewrite bought.
- Marks and shaded blocks sit on one ramp by confidence: yellow is possible (a `?` row, ranked last, with its caveat in the reason and split out of the brief), orange probable, red certain. Bold keeps its own blue and code its grey, since neither is a defect at the span.

## Passing your findings

When you reviewed the skill (see "Reviewing a Skill"), pass your graded findings with `--findings`, a JSON file or `-` for stdin. They get their own cell and brief section, and spec and primer grades fail the verdict:

```json
[{"grade": "primer", "finding": "Prerequisites restate the script's own checks.",
  "where": "SKILL.md:12", "fix": "Delete the list.", "cite": "Failure Modes: Tool compensation"}]
```

- `grade` is `spec`, `primer` or `judgement`; `finding` is one sentence. Both are required.
- `where` as `path:line` makes the row jump to the line. Put judgement calls the page cannot make here (a flagged word correct in context, a blob that earns its length) rather than in chat. They inform the reader; the mechanical verdict stays as it is.
- Leave out mechanical findings the page already lists.

## What to hand back

Give the user the path and stop; hand it back rather than opening it, since `open` and its equivalents are often sandboxed and a failed launch reads as a failed report. Do not paste the HTML into the conversation, restate the findings it already lists, or walk them through the layout: the page exists so they can read it themselves, and repeating it in chat spends the context the page was meant to save.

Add one line naming the finding you would fix first, and why. If you passed no findings, add one naming anything the page gets wrong: a false positive, or a blob that earns its length. Mention the Copy brief button once. It puts the findings on the clipboard as text, each with its reason, for pasting into whichever agent is doing the fixing - which is the point of handing over a page rather than a transcript.

Editing the renderer is a separate job from running it; `scripts/render_report.py`'s module docstring carries what constrains a change to it.
