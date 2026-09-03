# The HTML skill report

## Running it

```
uv run <skill-creator-primer>/scripts/render_report.py SKILL_DIR [--against OTHER_DIR] [-o OUT]
```

Writes one self-contained HTML file and prints the absolute path.

- Run it under `uv` so the spec cell has PyYAML and skills-ref.
- `--against` takes another copy of the same skill - a git worktree at the previous commit, or a snapshot taken before a compression pass - and adds a before-and-after cell. Use it to show what a rewrite bought.
- Output defaults to the platform temp directory. Pass `-o` when the user wants to keep it, and put it outside the skill directory: the primer's "What to Not Include in a Skill" rule covers stray files.
- Marks and shaded blocks sit on one ramp by confidence: yellow is possible (a `?` row, ranked last, with its caveat in the reason and split out of the brief), orange probable, red certain. Bold keeps its own blue and code its grey, since neither is a defect at the span.

## What to hand back

Give the user the path and stop; hand it back rather than opening it, since `open` and its equivalents are often sandboxed and a failed launch reads as a failed report. Do not paste the HTML into the conversation, restate the findings it already lists, or walk them through the layout: the page exists so they can read it themselves, and repeating it in chat spends the context the page was meant to save.

Two things are worth one line each, since the page shows them but makes no call on them:

- Which finding you would fix first, and why.
- Anything the page cannot know: a blob that earns its length, a flagged word that is correct in context, a warning that is a false positive.

Mention the Copy brief button once. It puts the findings on the clipboard as text, each with its reason, for pasting into whichever agent is doing the fixing - which is the point of handing over a page rather than a transcript.

Editing the renderer is a separate job from running it; `scripts/render_report.py`'s module docstring carries what constrains a change to it.
