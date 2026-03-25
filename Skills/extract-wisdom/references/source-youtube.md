# Source Acquisition: YouTube

Execute the download script to fetch the transcript:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py transcript <youtube-url>
```

The script downloads English subtitles or auto-generated text transcripts (not audio).

If the script fails, report the error to the user and stop. Do not download audio, run whisper, or attempt any alternative transcription method unless instructed to do so by the user.

After downloading, rename the directory using the rename subcommand:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py rename "<OUTPUT_DIR>" "<Short Description>"
```

The script automatically prepends today's date and sanitises the description into a clean directory name. Keep the description short (1-6 words).

- Example: `rename "<path>/O7SSQfiPDXA" "Demis Hassabis Interview"` produces `2026-02-05-Demis-Hassabis-Interview`

Then read the transcript file from `TRANSCRIPT_PATH`. Transcripts are cleaned and formatted as continuous text with minimal whitespace.

The transcript command also outputs `YOUTUBE_CHANNEL`, `YOUTUBE_TITLE`, and `THUMBNAIL` lines when metadata is available. Use these to populate the corresponding frontmatter fields (`youtube_channel`, `youtube_title`, `thumbnail`). The video description is saved in `metadata.json` in the output directory; read it to populate `youtube_description`.

**Do not re-fetch the YouTube video page** after downloading the transcript. The transcript content, metadata output, and the video title provide everything needed for analysis. Infer the speaker/author from the transcript content itself. If you cannot determine the author, use the channel name or leave the author field as "Unknown".

**Note:** The script uses `--restrict-filenames` to sanitise special characters in filenames for safer handling.

Return to SKILL.md and continue with Step 3.
