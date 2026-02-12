---
name: extract-wisdom
description: Extract wisdom, insights, and actionable takeaways from YouTube videos, blog posts, articles, or text files. Use when asked to analyse, summarise, or extract key insights from a given content source. Downloads YouTube transcripts, fetches web articles, reads local files, performs analysis, and saves structured markdown.
---

# Wisdom Extraction

## Workflow

### Step 1: Identify Source and Acquire Content

Determine the source type and acquire content accordingly:

**YouTube URL** (contains youtube.com or youtu.be):

Execute the download script to fetch only the transcript (no video file):

```bash
bash scripts/download_video.sh <youtube-url>
```

The script will:
- Auto-detect your environment (Claude Code or OpenClaw) and OS (macOS or Linux)
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

**Web URL** (blog posts, articles, any non-YouTube URL):

Use WebFetch to extract content:
```
WebFetch with prompt: "Extract the main article content"
```
WebFetch returns cleaned markdown-formatted content ready for analysis.

**Local file path** (.txt, .md, or other text formats):

Use the Read tool to load content directly.

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
- Preserve the original wording exactly, except correct American spellings to Australian English

#### 3. Structured Summary
- Create hierarchical organisation of content
- Break down into logical sections or themes
- Provide clear section headings that reflect content structure
- Include high-level overview followed by detailed breakdowns
- Note any important examples, case studies, or demonstrations

#### 4. Actionable Takeaways
- List specific, concrete actions the audience can implement
- Frame as clear, executable steps
- Prioritise practical advice over theoretical concepts
- Include any tools, resources, or techniques mentioned
- Distinguish between immediate actions and longer-term strategies

### Step 3: Write Analysis to Markdown File

Determine the output directory:

**YouTube sources:** The renamed directory from Step 1.

**Web and text sources:** `~/Downloads/text-wisdom/YYYY-MM-DD-<concise-description>/`
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

## Additional Resources
[Any tools, links, or references mentioned in the content]

_Wisdom Extraction: [Current date in YYYY-MM-DD]_
```

After writing the analysis file, inform the user of the location.

**OpenClaw note:** When running via OpenClaw, also return the full analysis content in your response. Users often want to read the insights immediately without opening a separate file.

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

### Step 5: Send Completion Notification (Claude Code Only & Optional)

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
- `download_video.sh`: Downloads YouTube transcripts (no video files) using yt-dlp. Auto-detects environment (Claude Code/OpenClaw) and OS, outputs paths and next steps.
- `send_notification.sh`: Sends desktop notifications when analysis is complete (Claude Code only, optional).

### Installation Paths
This skill works with both Claude Code and OpenClaw:
- **Claude Code:** `~/.claude/skills/extract-wisdom/`
- **OpenClaw:** `~/.openclaw/workspace/skills/extract-wisdom/`
