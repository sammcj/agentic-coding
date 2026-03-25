# Extract Wisdom Skill

Before making major changes to the Extract Wisdom skill you should first activate any skill-builder / skill-creator related skills you might have, you can skip this however for simple change requests.

When making changes to the Python script, always run the LSP / linter and ensure there's no errors:
- `uvx ty check scripts/wisdom.py`

When testing PDF functionality during development or debugging avoid reading the raw PDF data in to your context directly as this can overload the context.

If you make changes to the static index.html template or if the user asks you to regenerate the index HTML, run `uv run ~/.claude/skills/extract-wisdom/scripts/wisdom.py index`
