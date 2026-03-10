# Extract Wisdom Skill

When making changes to the Python script, always run the LSP / linter and ensure there's no errors:
- `uvx ty check scripts/wisdom.py`

When testing PDF functionality during development or debugging avoid reading the raw PDF data in to your context directly as this can overload the context.

If the user asks you to regenerate the index HTML, you can run `uv run ~/.claude/skills/extract-wisdom/scripts/wisdom.py index`
