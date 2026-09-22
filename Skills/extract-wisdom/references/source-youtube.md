# Source Acquisition: YouTube

Execute the download script to fetch the transcript:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py transcript <youtube-url>
```

The script downloads English subtitles or auto-generated text transcripts (not audio).

## No subtitles

When the video has no subtitles the script prints `NO_SUBTITLES`, the video `DURATION` and a `TRANSCRIBE_HINT`, then exits with status 2. Do not transcribe on your own initiative. Ask the user whether to transcribe locally with Parakeet, stating the duration and that it downloads the audio plus, on first run, the model. Only if they agree, rerun with the flag:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py transcript <youtube-url> --transcribe
```

If the user declines, or the script fails for any other reason, report the error and stop.

## After download

Rename the directory using the rename subcommand:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py rename "<OUTPUT_DIR>" "<Short Description>"
```

The script automatically prepends today's date and sanitises the description into a clean directory name. Keep the description short (1-6 words).

- Example: `rename "<path>/O7SSQfiPDXA" "Demis Hassabis Interview"` produces `2026-02-05-Demis-Hassabis-Interview`

Then read the `*-transcript.txt` file inside the renamed directory (the `TRANSCRIPT_PATH` printed earlier points at the old name). Each paragraph opens with a `[m:ss]` or `[h:mm:ss]` marker giving its start time in the video; the `DURATION` line gives the video length. Transcribed audio (via `--transcribe`) carries no markers.

The transcript command also outputs `YOUTUBE_CHANNEL`, `YOUTUBE_TITLE`, and `THUMBNAIL` lines when metadata is available. Use these to populate the corresponding frontmatter fields (`youtube_channel`, `youtube_title`, `thumbnail`). The video description is saved in `metadata.json` in the output directory; read it to populate `youtube_description`.

**Do not re-fetch the YouTube video page** after downloading the transcript. The transcript content, metadata output, and the video title provide everything needed for analysis. Infer the speaker/author from the transcript content itself. If you cannot determine the author, use the channel name or leave the author field as "Unknown".

**Note:** The script uses `--restrict-filenames` to sanitise special characters in filenames for safer handling.

Return to SKILL.md and continue with Step 2.
