# Source Acquisition: Web URLs and Local Files

## Web URL (blog posts, articles, any non-YouTube URL)

Fetch the article with the script. It extracts the main content to markdown, strips invisible characters, and stages it in a directory alongside `metadata.json`:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py fetch <url>
```

On `FETCH_STATUS: ok` it prints `ARTICLE_PATH`, `OUTPUT_DIR`, `WORDS`, and `TITLE`, `AUTHOR`, `DATE`, `SITE_NAME` when the page provides them. Rename the directory, then read `article.md` in full from the renamed `OUTPUT_DIR`:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py rename "<OUTPUT_DIR>" "<Short Description>"
```

Keep the description short (1-6 words). Use `AUTHOR` and `DATE` for the `author` and `content_date` frontmatter fields.

### Fallback

Any other `FETCH_STATUS` (`blocked`, `thin`, `error`, `unsupported content type`) means the page did not yield an article. Fall back to WebFetch:

```
WebFetch with prompt: "Extract the main article content"
```

Check the result is the whole article and not a truncated or summarised version. For `unsupported content type application/pdf`, download the file and use your PDF tooling instead. Then create the output directory with `create-dir` (see below).

## Local file path (.txt, .md, or other text formats)

Use your standard file reading tool (e.g. `Read`) to load the full content directly, then create the output directory with `create-dir`.

## Images in content

If the content clearly indicates there was an image that is highly likely to contain important information that would not be captured or inferred from the text alone (e.g. a diagram of a complex concept, but NOT things like a photo the author, memes, product logos, screenshots etc...) and if you have the link to the image URL, you may wish to:

- Fetch the image to a temporary location
- Read the image to understand the content
- Validate if the content of the image adds value beyond what is already captured in the text or not
- If it does you could add a concise written description of what the image is trying to convey (but only if the content doesn't already convey this!), or if it's a diagram, use Mermaid within the Markdown wisdom document you're creating.

## Output directory (local files and fallback only)

Create a date-prefixed output directory using the `create-dir` subcommand:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py create-dir "<Short Description>"
```

The script automatically prepends today's date (local timezone) and creates the directory in the wisdom base directory. Keep the description short (1-6 words). It outputs `OUTPUT_DIR: <path>` with the created directory path.

- Example: `create-dir "Sam Altman On AGI"` produces `2026-03-25-Sam-Altman-On-Agi`
- Do NOT create the directory manually or use `mkdir`. Always use `create-dir` to ensure the date is today's date in the local timezone.

Return to SKILL.md and continue with Step 2.
