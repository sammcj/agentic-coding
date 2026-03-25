# Source Acquisition: Web URLs and Local Files

## Web URL (blog posts, articles, any non-YouTube URL)

Use WebFetch to extract content, for example:

```
WebFetch with prompt: "Extract the main article content"
```

WebFetch returns cleaned markdown-formatted content ready for analysis.

Note: Ensure the Webfetch tool does not truncate the content that we likely want to keep! If you have problems with Webfetch you can always use the Fetch tool (or similar).

## Local file path (.txt, .md, or other text formats)

Use your standard file reading tool (e.g. `Read`) to load the full content directly.

## Images in content

If the content clearly indicates there was an image that is highly likely to contain important information that would not be captured or inferred from the text alone (e.g. a diagram of a complex concept, but NOT things like a photo the author, memes, product logos, screenshots etc...) and if you have the link to the image URL, you may wish to:

- Fetch the image to a temporary location
- Read the image to understand the content
- Validate if the content of the image adds value beyond what is already captured in the text or not
- If it does you could add a concise written description of what the image is trying to convey (but only if the content doesn't already convey this!), or if it's a diagram, use Mermaid within the Markdown wisdom document you're creating.

## Output directory

Create a date-prefixed output directory using the `create-dir` subcommand:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py create-dir "<Short Description>"
```

The script automatically prepends today's date (local timezone) and creates the directory in the wisdom base directory. Keep the description short (1-6 words). It outputs `OUTPUT_DIR: <path>` with the created directory path.

- Example: `create-dir "Sam Altman On AGI"` produces `2026-03-25-Sam-Altman-On-Agi`
- Do NOT create the directory manually or use `mkdir`. Always use `create-dir` to ensure the date is today's date in the local timezone.

Return to SKILL.md and continue with Step 3.
