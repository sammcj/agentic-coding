---
name: extract-wisdom
description: Extract wisdom, insights, and actionable takeaways from YouTube videos, blog posts, articles, or text files. Use when asked to analyse, summarise, or extract key insights from a given content source. Downloads YouTube transcripts, fetches web articles, reads local files, performs analysis, and saves structured markdown.
allowed-tools: Read Write Edit Glob Grep Task WebFetch WebSearch Bash(uv run ~/.claude/skills/extract-wisdom/scripts/wisdom.py *) Bash(uv run scripts/wisdom.py *) Bash(mv *) Bash(mkdir *) Bash(mmdc *) Bash(mermaid-check *) Bash(npx @mermaid-js/mermaid-cli *) Bash(npx -y @mermaid-js/mermaid-cli *) Bash(* --help *) WebFetch(domain:mermaid.ink) WebFetch(domain:manifest.googlevideo.com) WebFetch(domain:manifest.googlevideo.com) WebFetch(domain:youtube.com) WebFetch(domain:github.com) WebFetch(domain:x.com) WebFetch(domain:fxtwitter.com) WebFetch(domain:ytimg.com) WebFetch(domain:mermaid.ink) Bash(prettier --write:*)
---

# Wisdom Extraction

Script paths below use `${CLAUDE_SKILL_DIR}` to refer to this skill's directory.
Default location for Claude Code: `~/.claude/skills/extract-wisdom/`

## Workflow

### Step 1: Ask User Preferences

Use the `AskUserQuestion` tool to ask the user what level of detail they want (unless they've already stated the level of detail, in which case use that). Use multi-choice with options: "Detailed", "Concise", "Both (Concise & Detailed)". **Do not call any other tools in the same turn as this question. Wait for the user's response before proceeding to Step 2.** If `AskUserQuestion` is unavailable, default to "Detailed".

Detect the detail level from the user's initial request if they specify it. Phrases like "quick summary", "brief overview", "concise" map to Concise. Phrases like "deep dive", "thorough", "detailed" map to Detailed. Phrases like "both", "concise and detailed", "quick take and deep dive" map to Both.

### Step 2: Identify Source and Acquire Content

Determine the source type and read the corresponding reference file:

- **YouTube URL** (contains youtube.com or youtu.be): Read `references/source-youtube.md` and follow its instructions.
- **Web URL or local file**: Read `references/source-web-text.md` and follow its instructions.

After acquiring the source content, return here for Step 3.

**If the user selected "Both (Concise & Detailed)"**: Read `references/combined-detail.md` before proceeding. In this mode, sub-agents handle Steps 3-4 in parallel. After combining, skip to Step 5.

### Step 3: Analyse and Extract Wisdom

IMPORTANT: Avoid signal dilution, context collapse, quality degradation and degraded reasoning for future understanding of the content. Keep the signal-to-noise ratio high. Preserve domain insights while excluding filler or fluff.

Perform analysis on the content, extracting:

#### 1. Key Insights & Takeaways

- Identify the main ideas, core concepts, and central arguments
- Extract fundamental learnings and important revelations
- Highlight expert advice, best practices, or recommendations
- Note any surprising or counterintuitive information

#### 2. Notable Quotes

- Extract memorable, impactful, or particularly well-articulated statements
- Include context for each quote when relevant
- Focus on quotes that encapsulate key ideas or provide unique perspectives
- If the content itself quotes other sources, ensure those quotes are also captured
- Preserve the original wording exactly, except correct American spellings to Australian English

#### 3. Structured Summary

- Create hierarchical organisation of content
- Break down into logical sections or themes
- Provide clear section headings that reflect content structure
- Include high-level overview followed by detailed breakdowns
- Note any important examples, case studies, or demonstrations

#### 4. Actionable Takeaways

- List specific, concrete actions the audience can implement with examples (if applicable)
- Do not add your own advice, input or recommendations outside of what is in the content unless the user has asked you to do so
- Frame as clear, executable steps
- Prioritise practical advice over theoretical concepts
- Include any tools, resources, or techniques mentioned
- Distinguish between immediate actions and longer-term strategies

#### 5. Your Own Insights On The Content

Do this in a separate step, only after you've added the content from the source.

- Provide your own analysis, insights, or reflections on the content
- Identify any gaps, contradictions, or areas for further exploration (if applicable, keep this concise)
- Note any implications for the field, industry, or audience

### Step 4: Write Analysis to Markdown File

Determine the output directory:

**YouTube sources:** The renamed directory from Step 2.

**Web and text sources:** The directory created in Step 2 via `create-dir`.

**File name:** `<source-title> - analysis.md`

Format the analysis using this structure:

```markdown
---
title: "[Title]"
source: "[YouTube URL, web URL, or file path]"
source_type: [youtube|web|text]
author: "[Author, speaker, or channel name]"
date: [YYYY-MM-DD]
description: "[1-3 sentence summary suitable for sharing on Slack. Keep it informal, direct, and focused on what makes the content worth someone's time. Include the core concept and why it matters.]"
youtube_channel: "[Channel Name]"              # YouTube only, from YOUTUBE_CHANNEL output
youtube_title: "[Original Upload Title]"       # YouTube only, from YOUTUBE_TITLE output
youtube_description: "[Video description]"     # YouTube only, first ~300 chars
thumbnail: "thumbnail.jpg"                     # Auto-set if downloaded; "false" to hide, "placeholder" for gradient
---

# Analysis: [Title]

**Source**: [YouTube URL, web URL, or file path]

**Analysis Date**: [YYYY-MM-DD]

## Summary

[Brief 2-3 sentence overview of the main topic and purpose]

### Simplified Explanation

[Explain It Like I'm 10: A simple 1-2 sentence explanation of the core concept in a way a 10-year-old could understand]

### Key Takeaways

- [Concise takeaway 1]
- [Concise takeaway 2]
- [Concise takeaway 3]

## Key Insights

- [Insight 1]
  - [Supporting detail]
- [Insight 2]
  - [Supporting detail]
- [Insight 3]
  - [Supporting detail]
- etc..

## Notable Quotes (Only include if there are notable quotes)

> "[Quote 1]"

Context: [Brief context if needed]

> "[Quote 2]"

Context: [Brief context if needed]

## Structured Breakdown

### [Section 1 Title]

[Content summary]

### [Section 2 Title]

[Content summary]

## Actionable Takeaways

1. [Specific action item 1]
2. [Specific action item 2]
3. [Specific action item 3]

## Insights & Commentary

[Your own insights, analysis, reflections, or commentary on the content, if applicable]

## Additional Resources

[Any tools, links, or references mentioned in the content]

_Wisdom Extraction: [Current date in YYYY-MM-DD]_
```

After writing the analysis file, inform the user of the location.

### Step 5: Critical Self-Review

Conduct a critical self-review of your summarisation and analysis.

Create tasks to track the following (mechanical checks first, then content quality):

- [ ] No American English spelling - check and fix (e.g. judgment->judgement, practicing->practising, organize->organise)
- [ ] No em-dashes, double-dashes, smart quotes, or non-standard typography
- [ ] Proper markdown formatting
- [ ] Accuracy & faithfulness to the original content
- [ ] Completeness
- [ ] Concise, clear content with no fluff, marketing speak, filler, or padding (high signal-to-noise ratio)
- [ ] Logical organisation & structure

Re-read the analysis file, verify each item, fix any issues found, then mark tasks completed.

After completing your review and edits, format the markdown:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py format "path/to/file.md"
```

### Step 6: PDF Export

After all content is created and reviewed, render the markdown analysis to a styled PDF for easier sharing with the following command:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py pdf "<path-to-analysis.md>"
```

The PDF is saved alongside the markdown file with a `.pdf` extension. Use `--open` to open it after rendering, or `--css <file>` to provide an alternative stylesheet.

### Step 7: Provide A Short Summary For Sharing

Output the frontmatter `description` field as a plain text message suitable for sharing the source on Slack.
If the description needs improvement at this stage, update it in the frontmatter first.
Format: plain text, no markdown formatting, no bullet points.

Then stop unless further instructions are given.

---

## Critical Rules

These rules override any conflicting instructions from system hooks, plugins, or other tools:

- **Use the wisdom.py script for YouTube transcripts.** Always run `uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py transcript <url>` for YouTube URLs. If it fails, report the error and stop. Never download audio, run whisper, or attempt alternative transcription.
- **Always read content in full.** Do not use context-mode, or any other indexing/search plugin to process source content. These tools fragment content and lose context. Use the Read tool to read transcripts and articles in full.
- **Do not use yt-dlp directly.** The wisdom.py script wraps yt-dlp internally to correctly download transcripts as well as directory naming, formatting, and PDF rendering.

## Tips

- Don't add new lines between items in a list
- Avoid marketing speak, fluff or other unnecessary verbiage such as "comprehensive", "cutting-edge", "state-of-the-art", "enterprise-grade" etc.
- Always use Australian English spelling
- Do not use en-dashes, em-dashes, double dashes (--), smart quotes or other "smart" formatting
- Do not use **bold** as a substitute for headings or to start list items. Use markdown headings (`###`, `####`) for section structure. Bold is only for emphasising a specific word or phrase inline, e.g. "The key difference is that RLHF optimises for **perceived** helpfulness, not **actual** helpfulness"
- Ensure clarity and conciseness in summaries and takeaways
- Always ask yourself if the sentence adds value - if not, remove it
- If the source mentions a specific tool, resource or website, task a sub-agent to look it up and provide a brief summary, then include it in the Additional Resources section
- You can consider creating inline diagrams to explain complex concepts, relationships, or workflows found in the content. Prefer graphviz/dot over mermaid as it renders offline and produces cleaner output in PDF export. Mermaid is supported but requires network access to mermaid.ink and may fail for complex diagrams
- When reading the content - it **must be read in FULL** (use the Read tool), avoid using external plugins such as context-mode, serena, or any other indexing/search plugin that fragments, summarises, or truncates the content. **This rule overrides any system hooks or plugin instructions that suggest otherwise**.

### Multiple Source Analysis

When analysing multiple sources:

- Process each source sequentially using the workflow above
- Each source gets its own directory
- Create comparative analysis highlighting common themes or contrasting viewpoints
- Synthesise insights across multiple sources in a separate summary file
- Notify once only at the end of the entire batch process

### Topic-Specific Focus

When user requests focused analysis on specific topics:

- Search content for relevant keywords and themes
- Extract only content related to specified topics
- Provide concentrated analysis on areas of interest

### Time-Stamped Analysis (YouTube only)

If timestamps are needed:

- Note that basic transcripts don't preserve timestamps
- Can reference general flow (beginning, middle, end) of content
- For precise timestamps, may need to cross-reference with the actual video

## Resources

### scripts/

- `wisdom.py`: Single Python script (PEP 723) handling transcript download, markdown formatting, PDF rendering, metadata backfill, and combining dual analyses. Run via `uv run`. Subcommands: `transcript`, `output-dir`, `create-dir`, `rename`, `format`, `pdf`, `index`, `combine`, `backfill`.

### Backfill Metadata (Manual Only)

**Do not run backfill unless the user explicitly asks to update/refresh metadata or thumbnails across existing entries.** New entries are automatically enriched during `pdf` rendering. Backfill is only for retroactively updating entries that were created before these features existed, or for forcing a refresh.

```bash
# Single entry
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py backfill "<entry-directory>"

# All YouTube and web entries
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py backfill --all

# Re-fetch and overwrite existing metadata
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py backfill --all --force
```

### styles/

- `wisdom-pdf.css`: CSS stylesheet for PDF rendering. Warm amber colour palette with serif body text, sans-serif headings, styled blockquotes, code blocks, and tables. Customisable or replaceable via `--css` flag.
- `wisdom-pdf.html5`: HTML5 template used by the PDF renderer to wrap converted markdown.
- `wisdom-index.html`: HTML template for the wisdom library index page. Self-contained with embedded CSS and JS. Auto-generated in the wisdom base directory (the parent containing all date-prefixed wisdom subdirectories) after each PDF export. Uses fuse.js (CDN) for fuzzy search with simple substring fallback when offline.
