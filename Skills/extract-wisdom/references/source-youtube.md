# Source Acquisition: YouTube

Execute the download script to fetch the transcript:

```bash
uv run <skill-dir>/scripts/wisdom.py transcript <youtube-url>
```

The script downloads English subtitles or auto-generated text transcripts (not audio).

## No subtitles

When the video has no subtitles the script prints `NO_SUBTITLES`, the video `DURATION` and a `TRANSCRIBE_HINT`, then exits with status 2.

If the output contains `COOKIE_HINT`, follow its instructions before offering transcription.

Do not transcribe on your own initiative. Ask the user whether to transcribe locally with Parakeet, stating the duration and that it downloads the audio plus, on first run, the model. Only if they agree, rerun with the flag:

```bash
uv run <skill-dir>/scripts/wisdom.py transcript <youtube-url> --transcribe
```

If the user declines, or the script fails for any other reason, report the error and stop.

## After download

Rename the directory using the rename subcommand:

```bash
uv run <skill-dir>/scripts/wisdom.py rename "<OUTPUT_DIR>" "<Short Description>"
```

The script automatically prepends today's date and sanitises the description into a clean directory name. Keep the description short (1-6 words).

- Example: `rename "<path>/O7SSQfiPDXA" "Demis Hassabis Interview"` produces `2026-02-05-Demis-Hassabis-Interview`

Then read the `*-transcript.txt` file inside the renamed directory (the `TRANSCRIPT_PATH` printed earlier points at the old name). Each paragraph opens with a `[m:ss]` or `[h:mm:ss]` marker giving its start time in the video; the `DURATION` line gives the video length. Transcribed audio (via `--transcribe`) carries no markers.

The transcript command also outputs `YOUTUBE_CHANNEL`, `YOUTUBE_TITLE`, and `THUMBNAIL` lines when metadata is available. Use these to populate the corresponding frontmatter fields (`youtube_channel`, `youtube_title`, `thumbnail`). The video description is saved in `metadata.json` in the output directory; read it to populate `youtube_description`.

**Do not re-fetch the YouTube video page** after downloading the transcript. The transcript content, metadata output, and the video title provide everything needed for analysis. Infer the speaker/author from the transcript content itself. If you cannot determine the author, use the channel name or leave the author field as "Unknown".

**Note:** The script uses `--restrict-filenames` to sanitise special characters in filenames for safer handling.

## Frames (optional)

Use when the speaker refers to something on screen ("this diagram", "as you can see here") and the transcript alone loses its content. Skip for talking-head video.

```bash
uv run <skill-dir>/scripts/wisdom.py frames "<renamed-dir>" --quote "as you can see in this diagram"
```

- `--quote`: 4 or more consecutive words copied verbatim from the transcript. Gives the moment they are spoken, so prefer it over `--at m:ss`
- Max 5 frames per run. Frames go to a temp directory, printed as `FRAME:` lines
- Read each frame, and use what it shows in the analysis. If it misses the visual, retry with `--at` a few seconds later
- Leave frames in the temp directory unless the user asks to keep them
- On any error line, adjust the arguments as its hint says, or continue the analysis without frames

Return to SKILL.md and continue with Step 2.
