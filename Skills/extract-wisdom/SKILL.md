---
name: extract-wisdom
description: Extract wisdom, insights, and actionable takeaways from YouTube videos, blog posts, articles, or text files. Use when asked to analyse, summarise, or extract key insights from a given content source. Downloads YouTube transcripts, fetches web articles, reads local files, performs analysis, and saves structured markdown.
compatibility: Requires Bash Prettier Pandoc & WeasyPrint
allowed-tools: Read Write Edit Glob Grep Task AskUserQuestion WebFetch WebSearch Bash(bash scripts/download_video.sh *) Bash(bash ~/.claude/skills/extract-wisdom/scripts/download_video.sh *) Bash(bash scripts/send_notification.sh) Bash(bash ~/.claude/skills/extract-wisdom/scripts/send_notification.sh) Bash(* bash scripts/send_notification.sh) Bash(* bash ~/.claude/skills/extract-wisdom/scripts/send_notification.sh) Bash(bash scripts/render_pdf.sh *) Bash(bash ~/.claude/skills/extract-wisdom/scripts/render_pdf.sh *) Bash(mv *) Bash(mkdir *) Bash(prettier *) Bash(npx prettier *) Bash(npx -y prettier *) Bash(OPENSSL_CONF=/dev/null npx -y prettier *) Bash(mmdc *) Bash(mermaid-check *) Bash(npx @mermaid-js/mermaid-cli *) Bash(npx -y @mermaid-js/mermaid-cli *) Bash(* --help *)
---

# Wisdom Extraction

## Workflow

### Step 0: Ask User Preferences

If you have the ability to ask the user questions using `AskUserQuestion` or similar ask the user what level of detail they want in the document, use multi-choice if possible with: "Highly detailed", "Medium detail", "Concise"

### Step 1: Identify Source and Acquire Content

Determine the source type and acquire content accordingly:

#### **YouTube URL** (contains youtube.com or youtu.be)

Execute the download script to fetch only the transcript (no video file):

```bash
bash scripts/download_video.sh <youtube-url>
```

The script will:
- Auto-detect your environment (Claude Code or Claw based agents) and OS (macOS or Linux)
- Download English subtitles or auto-generated transcripts
- Output the transcript path and next steps

**Cookie handling:** The script first attempts to download using browser cookies (for access-restricted videos). If no browser is found or cookies fail, it automatically falls back to trying cookie-less download.

After downloading, execute the rename command the script provides:

```bash
mv <OUTPUT_DIR> <OUTPUT_DIR>/../YYYY-MM-DD-<concise-description>
```

- Keep the description short (1-6 words), use hyphens instead of spaces
- Take the video content and title into consideration
- Example: Video "My Interview With Demis Hassabis" becomes `2026-02-05-Demis-Hassabis-Interview`

Then read the transcript file from `TRANSCRIPT_PATH`. Transcripts are cleaned and formatted as continuous text with minimal whitespace.

**Note:** The download script uses `--restrict-filenames` to sanitise special characters in filenames for safer handling.

#### **Web URL or Document Path** (blog posts, articles, any non-YouTube URL)

Use WebFetch to extract content, for example:
```
WebFetch with prompt: "Extract the main article content"
```
WebFetch returns cleaned markdown-formatted content ready for analysis.

Note: Ensure the Webfetch tool does not truncate the content that we likely want to keep! If you have problems with Webfetch you can always use the Fetch tool (or similar).

**Local file path** (.txt, .md, or other text formats):

Use the Read tool to load content directly.

If the content clearly indicates there was an image that is highly likely to contain important information that would not be captured or inferred from the text alone (e.g. a diagram of a complex concept, but NOT things like a photo the author, memes, product logos, screenshots etc...) and if you have the link to the image URL, you may wish to:
- Fetch the image to a temporary location
- Read the image to understand the content
- Validate if the content of the image adds value beyond what is already captured in the text or not
- If it does you could add a concise written description of what the image is trying to convey (but only if the content doesn't already convey this!), - OR if it's a diagram, use Mermaid within the Markdown wisdom document you're creating.

### Step 2: Analyse and Extract Wisdom

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

### Step 3: Write Analysis to Markdown File

Determine the output directory:

**YouTube sources:** The renamed directory from Step 1.

**Web and text sources:** Run the following to determine the base output directory, then use it as described below:

```bash
bash scripts/download_video.sh --output-dir
```

If the command fails or is unavailable, fall back to `~/Downloads/text-wisdom/`.

Save to `<base-output-dir>/YYYY-MM-DD-<concise-description>/`:
- Create the directory if it doesn't exist
- Use the same date-prefixed naming convention as YouTube sources

**File name:** `<source-title> - analysis.md`

Format the analysis using this structure:

```markdown
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

**Claw note:** When running via Claw, also return the full analysis content in your response. Users often want to read the insights immediately without opening a separate file.

### Step 4: Critical Self-Review

Conduct a critical self-review of your summarisation and analysis.

Create tasks to track the following (mechanical checks first, then content quality):
- [ ] No American English spelling - check and fix (e.g. judgment->judgement, practicing->practising, organize->organise)
- [ ] No em-dashes, smart quotes, or non-standard typography
- [ ] Proper markdown formatting
- [ ] Accuracy & faithfulness to the original content
- [ ] Completeness
- [ ] Concise, clear content with no fluff, marketing speak, filler, or padding (high signal-to-noise ratio)
- [ ] Logical organisation & structure

Re-read the analysis file, verify each item, fix any issues found, then mark tasks completed.

### Step 5: Formatting and Send Completion Notification (Claude Code Only & Optional)

Run `OPENSSL_CONF=/dev/null npx -y prettier --write "path/to/file.md"` to auto-format the markdown file.

Use `scripts/send_notification.sh` to send a desktop notification:

```bash
TITLE="Wisdom Extracted" MESSAGE="<short description>" PLAY_SOUND=true DIR="<output-directory>" bash scripts/send_notification.sh
```

Then stop unless further instructions are given.

## Additional Capabilities

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

### PDF Export

After all content is created and reviewed, render the markdown analysis to a styled PDF for easier sharing with the following command:

```bash
bash scripts/render_pdf.sh "<path-to-analysis.md>"
```

The PDF is saved alongside the markdown file with a `.pdf` extension. Use `--open` to open it after rendering, or `--css <file>` to provide an alternative stylesheet.

Dependencies: `pandoc` and `weasyprint` (Ask the user if they want you run `brew install pandoc weasyprint` if these are not installed).

### Time-Stamped Analysis (YouTube only)
If timestamps are needed:
- Note that basic transcripts don't preserve timestamps
- Can reference general flow (beginning, middle, end) of content
- For precise timestamps, may need to cross-reference with the actual video

## Tips

- Don't add new lines between items in a list
- Avoid marketing speak, fluff or other unnecessary verbiage such as "comprehensive", "cutting-edge", "state-of-the-art", "enterprise-grade" etc.
- Always use Australian English spelling
- Do not use em-dashes or smart quotes
- Only use **bold** where emphasis is truly needed
- Ensure clarity and conciseness in summaries and takeaways
- Always ask yourself if the sentence adds value - if not, remove it
- If the source mentions a specific tool, resource or website, task a sub-agent to look it up and provide a brief summary, then include it in the Additional Resources section
- You can consider creating mermaid diagrams to explain complex concepts, relationships, or workflows found in the content

## Resources

### scripts/
- `download_video.sh`: Downloads YouTube transcripts (no video files) using yt-dlp. Auto-detects environment (Claude Code/Claw) and OS, outputs paths and next steps.
- `send_notification.sh`: Sends desktop notifications when analysis is complete (Claude Code only, optional).
- `render_pdf.sh`: Converts analysis markdown to a styled PDF using pandoc + weasyprint.

### styles/
- `wisdom-pdf.css`: CSS stylesheet for PDF rendering. Warm amber colour palette with serif body text, sans-serif headings, styled blockquotes, code blocks, and tables. Customisable or replaceable via `--css` flag.

### Installation Paths
This skill works with both Claude Code and Claw based agents:
- **Claude Code:** `~/.claude/skills/extract-wisdom/`
- **Claw:** `~/.<open|zero>claw/workspace/skills/extract-wisdom/`
