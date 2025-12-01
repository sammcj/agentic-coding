---
name: youtube-wisdom
description: Extract wisdom, insights, and actionable takeaways from YouTube videos. Use when asked to analyse, summarise, or extract key learnings from YouTube content. Downloads transcripts only (no video files), performs comprehensive analysis including key insights, notable quotes, structured summaries, and actionable takeaways, then saves the analysis to a markdown file.
---

# YouTube Wisdom Extraction

## Overview

Extract meaningful insights, key learnings, and actionable wisdom from YouTube videos. This skill handles the complete workflow: downloading transcripts using yt-dlp (no video files), parsing subtitle data, performing comprehensive analysis, and saving results to organised markdown files.

## When to Use This Skill

Activate this skill when users request:
- Analysis or summary of YouTube video content
- Extraction of key insights or learnings from videos
- Identification of notable quotes or important statements
- Structured breakdown of video content
- Actionable takeaways from educational or informational videos

## Workflow

### Step 1: Download Transcript

Execute the download script to fetch only the transcript (no video file):

```bash
bash ~/.claude/skills/youtube-wisdom/scripts/download_video.sh <youtube-url>
```

The script will:
- Extract the video ID from the URL
- Create directory structure: `~/Downloads/videos/<video-id>/`
- Download English subtitles or auto-generated transcripts (no video file)
- Convert subtitle JSON3 format to clean text files
- Save transcript to the video ID directory

**Note:** The script uses Firefox cookies to handle age-restricted or login-required videos.

### Step 2: Locate and Read Transcript

The script outputs the location of the transcript. Read the transcript file from the video ID directory:

```bash
# The transcript will be at:
~/Downloads/videos/<video-id>/<video-title>.en.txt
```

Read the transcript file to analyse content. Transcripts are cleaned and formatted as continuous text with minimal whitespace.

#### Step 2.1: Rename the directory

Rename the directory to use today's date concise description of instead of the video for easier identification, e.g:

```bash
DATE=$(date +%Y-%m-%d)
mv ~/Downloads/videos/<video-id>/ "~/Downloads/videos/${DATE}-<concise-description>/"
```

### Step 3: Analyse and Extract Wisdom

Perform comprehensive analysis on the transcript, extracting:

#### 1. Key Insights & Takeaways
- Identify the main ideas, core concepts, and central arguments
- Extract fundamental learnings and important revelations
- Highlight expert advice, best practices, or recommendations
- Note any surprising or counterintuitive information

#### 2. Notable Quotes
- Extract memorable, impactful, or particularly well-articulated statements
- Include context for each quote when relevant
- Focus on quotes that encapsulate key ideas or provide unique perspectives
- Preserve the original wording exactly as spoken

#### 3. Structured Summary
- Create hierarchical organisation of content
- Break down into logical sections or themes
- Provide clear section headings that reflect content structure
- Include high-level overview followed by detailed breakdowns
- Note any important examples, case studies, or demonstrations

#### 4. Actionable Takeaways
- List specific, concrete actions viewers can implement
- Frame as clear, executable steps
- Prioritise practical advice over theoretical concepts
- Include any tools, resources, or techniques mentioned
- Distinguish between immediate actions and longer-term strategies

### Step 4: Write Analysis to Markdown File

Write the complete analysis to a markdown file in the video's directory:

**File location:** `~/Downloads/videos/<video-id>/analysis.md`

Format the analysis using this structure:

```markdown
# Video Analysis: [Video Title]

**Video URL:** [YouTube URL]
**Analysis Date:** [Current date in YYYY-MM-DD]

## Summary
[Brief 2-3 sentence overview of the video's main topic and purpose]

## Key Insights
- [Insight 1 with supporting detail]
- [Insight 2 with supporting detail]
- [Insight 3 with supporting detail]
- etc..

## Notable Quotes (Only add this if there are notable quotes / statements)
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
[Any tools, links, or references mentioned in the video]
```

After writing the analysis file, inform the user of the location:
- Transcript location: `~/Downloads/videos/<video-id>/<title>.en.txt`
- Analysis location: `~/Downloads/videos/<video-id>/analysis.md`

## Additional Capabilities

### Multiple Video Analysis
When analysing multiple videos:
- Process each video sequentially using the workflow above
- Each video gets its own directory by video ID
- Create comparative analysis highlighting common themes or contrasting viewpoints
- Synthesise insights across multiple sources in a separate summary file

### Time-Stamped Analysis
If timestamps are needed:
- Note that basic transcripts don't preserve timestamps
- Can reference general flow (beginning, middle, end) of content
- For precise timestamps, may need to cross-reference with the actual video

### Topic-Specific Focus
When user requests focused analysis on specific topics:
- Search transcript for relevant keywords and themes
- Extract only content related to specified topics
- Provide concentrated analysis on areas of interest

## Tips

- Don't had new lines between items in a list
- Avoid marketing speak or fluff
- Always use Australian English spelling
- Do not use em-dashes or smart quotes
- Only use **bold* where emphasis is truly needed
- Ensure clarity and conciseness in summaries and takeaways

## Resources

### scripts/
- `download_video.sh`: Bash script that downloads YouTube transcripts (no video files) using yt-dlp with optimised settings. Organises files by video ID in `~/Downloads/videos/<video-id>/`.
