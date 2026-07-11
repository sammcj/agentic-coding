#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "yt-dlp",
#   "weasyprint",
#   "markdown",
#   "graphviz",
#   "tzdata",
#   "Pillow",
# ]
# ///
"""Extract-wisdom helper tools.

Single script replacing the individual bash scripts for transcript download,
markdown formatting, and PDF rendering. Run via: uv run wisdom.py <subcommand>

Subcommands:
    transcript <url>                Download YouTube transcript
    output-dir                      Print the resolved output directory
    create-dir <description>        Create a date-prefixed directory for non-YouTube sources
    rename <dir> <description>      Rename directory with date prefix
    format [--check] <files...>     Format markdown with prettier
    pdf [--css F] [--open] [--no-stamp] [file]
                                    Render markdown to styled PDF
    regenerate-pdfs [base_dir] [--stamp] [--css F]
                                    Re-render every wisdom analysis PDF (no date stamp by default)
    index [base_dir]                Regenerate the wisdom library index.html
    epub [base_dir] [--output F] [--title T] [--descriptions] [--kindle] [--open]
                                    Bind the whole corpus into a single .epub
                                    (grouped by year; --kindle also emits .azw3)
    backfill [dir] [--all] [--force] Backfill metadata and thumbnails
"""

from __future__ import annotations

import argparse
import base64
import difflib
import fcntl
import hashlib
import html as html_mod
import json
import math
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import tempfile
import urllib.error
import urllib.request
import uuid
import zipfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

# ---------------------------------------------------------------------------
# Configuration - adjust these defaults as needed
# ---------------------------------------------------------------------------

# Minimum gap (ms) between subtitle events to insert a paragraph break.
PARAGRAPH_GAP_MS = 2500

# Subtitle language preference (first match wins).
SUBTITLE_LANGS = ["en"]

# Browser search order for cookie-based YouTube downloads.
COOKIE_BROWSERS = ("firefox", "brave", "chrome", "chromium", "safari")

# Markdown extensions used when converting to HTML for PDF rendering.
# See https://python-markdown.github.io/extensions/
MD_EXTENSIONS = ["tables", "fenced_code"]

# ---------------------------------------------------------------------------
# Paths (derived from script location)
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
CSS_FILE = SKILL_DIR / "styles" / "wisdom-pdf.css"
TEMPLATE_FILE = SKILL_DIR / "styles" / "wisdom-pdf.html5"
EPUB_CSS_FILE = SKILL_DIR / "styles" / "wisdom-epub.css"

# Index generation settings.
_INDEX_SCHEMA_VERSION = 7
_INDEX_ENV_VAR = "EXTRACT_WISDOM_CREATE_INDEX"
_INDEX_TEMPLATE = SKILL_DIR / "styles" / "wisdom-index.html"
_INDEX_LOCK_TIMEOUT = 300  # seconds (5 minutes)


# ---------------------------------------------------------------------------
# Environment detection
# ---------------------------------------------------------------------------

def _is_mac() -> bool:
    return platform.system() == "Darwin"


def detect_base_dir() -> Path:
    """Detect the output directory based on environment and OS."""
    home = Path.home()
    detected_env = ""

    # Check script path for claw-based environments: ~/.{name}/workspace/...
    try:
        relative = SCRIPT_DIR.relative_to(home)
        parts: tuple[str, ...] = relative.parts
        if len(parts) >= 2 and parts[0].startswith(".") and parts[1] == "workspace":
            detected_env = parts[0].lstrip(".")
        elif parts and parts[0] == ".claude":
            detected_env = "claude-code"
    except ValueError:
        pass

    if detected_env and detected_env != "claude-code":
        ws_dir = home / f".{detected_env}" / "workspace"
        if _is_mac():
            return ws_dir / "wisdom"
        env_var = f"{detected_env.upper()}_WISDOM_DIR"
        override = os.environ.get(env_var)
        if override:
            return Path(override)
        return ws_dir / "wisdom"

    if detected_env == "claude-code":
        if _is_mac():
            icloud = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Documents"
            if icloud.is_dir():
                return icloud / "Wisdom"
            return home / "Wisdom"
        return home / ".claude" / "wisdom"

    # Unknown environment fallback
    if _is_mac():
        icloud = home / "Library" / "Mobile Documents" / "com~apple~CloudDocs" / "Documents"
        if icloud.is_dir():
            return icloud / "Wisdom"
    return home / "Wisdom"


def detect_browser() -> str | None:
    """Find a browser whose cookies yt-dlp can use."""
    home = Path.home()
    for browser in COOKIE_BROWSERS:
        if shutil.which(browser):
            return browser
        # Check common config directories
        if (home / ".config" / browser).is_dir():
            return browser
        if browser == "chrome" and (home / ".var" / "app" / "com.google.Chrome").is_dir():
            return browser
    return None


# ---------------------------------------------------------------------------
# Transcript download
# ---------------------------------------------------------------------------

def _sanitise_filename(name: str) -> str:
    """Restrict to alphanumeric, hyphens, underscores."""
    name = re.sub(r"[^a-zA-Z0-9_-]", "_", name)
    name = re.sub(r"__+", "_", name)
    return name.strip("_")


def _json3_to_text(json3_path: Path) -> str:
    """Convert yt-dlp JSON3 subtitle file to clean paragraph text."""
    data = json.loads(json3_path.read_text(encoding="utf-8"))
    entries: list[tuple[int, str]] = []
    for event in data.get("events", []):
        segs = event.get("segs")
        if not segs:
            continue
        text = "".join(seg.get("utf8", "") for seg in segs)
        t = event.get("tStartMs", 0)
        entries.append((t, text))

    prev_t = 0
    parts: list[str] = []
    for t, text in entries:
        if not re.sub(r"\s+", "", text):
            continue
        if parts and (t - prev_t) > PARAGRAPH_GAP_MS:
            parts.append("\n\n")
        parts.append(text)
        prev_t = t

    raw = "".join(parts)
    raw = re.sub(r"[ \t]+", " ", raw)
    raw = re.sub(r"\n ", "\n", raw)
    raw = re.sub(r" \n", "\n", raw)
    return raw.strip()


class _SilentLogger:
    """Logger that discards all yt-dlp output."""

    def debug(self, _: str) -> None:
        pass

    def info(self, _: str) -> None:
        pass

    def warning(self, _: str) -> None:
        pass

    def error(self, _: str) -> None:
        pass


def _download_transcript(url: str, video_dir: Path, use_cookies: bool = False) -> bool:
    """Download subtitles using yt-dlp Python API."""
    from yt_dlp import YoutubeDL

    opts: dict = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "subtitlesformat": "json3",
        "subtitleslangs": SUBTITLE_LANGS,
        "restrictfilenames": True,
        "outtmpl": str(video_dir / "%(title)s.%(ext)s"),
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "logger": _SilentLogger(),
        "remote_components": {"ejs:github"},
    }
    if use_cookies:
        browser = detect_browser()
        if browser:
            opts["cookiesfrombrowser"] = (browser,)
    # Redirect stderr at the OS level to suppress yt-dlp's direct fd writes
    old_fd = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        with YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
            ydl.download([url])
        return True
    except Exception as exc:
        os.dup2(old_fd, 2)  # restore before printing error
        print(f"Download error: {exc}", file=sys.stderr)
        return False
    finally:
        try:
            os.dup2(old_fd, 2)
        except OSError:
            pass
        os.close(old_fd)


def _download_audio(url: str, video_dir: Path, use_cookies: bool = False) -> bool:
    """Download audio from YouTube and convert to WAV using yt-dlp + ffmpeg."""
    from yt_dlp import YoutubeDL

    opts: dict = {
        "format": "bestaudio/best",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "wav",
        }],
        "outtmpl": str(video_dir / "audio.%(ext)s"),
        "restrictfilenames": True,
        "quiet": True,
        "no_warnings": True,
        "noprogress": True,
        "logger": _SilentLogger(),
    }
    if use_cookies:
        browser = detect_browser()
        if browser:
            opts["cookiesfrombrowser"] = (browser,)
    old_fd = os.dup(2)
    devnull = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull, 2)
    os.close(devnull)
    try:
        with YoutubeDL(opts) as ydl:  # type: ignore[arg-type]
            ydl.download([url])
        return True
    except Exception as exc:
        os.dup2(old_fd, 2)
        print(f"Audio download error: {exc}", file=sys.stderr)
        return False
    finally:
        try:
            os.dup2(old_fd, 2)
        except OSError:
            pass
        os.close(old_fd)


def _audio_transcription_fallback(url: str, video_dir: Path) -> Path | None:
    """Download audio and transcribe with Parakeet TDT v2 when subtitles are unavailable."""
    if not shutil.which("ffmpeg"):
        print("MISSING_DEPS: ffmpeg (required for audio transcription fallback)", file=sys.stderr)
        if _is_mac():
            print("INSTALL: brew install ffmpeg", file=sys.stderr)
        else:
            print("INSTALL: sudo apt install ffmpeg", file=sys.stderr)
        return None

    print("No subtitles available. Attempting audio transcription...", file=sys.stderr)

    download_ok = _download_audio(url, video_dir, use_cookies=True)
    if not download_ok:
        download_ok = _download_audio(url, video_dir, use_cookies=False)

    wav_file = video_dir / "audio.wav"
    if not download_ok or not wav_file.is_file():
        print("Error: Failed to download audio from video", file=sys.stderr)
        return None

    # Convert to 16kHz mono WAV (onnx-asr requires mono input).
    mono_file = video_dir / "audio_mono.wav"
    conv = subprocess.run(
        ["ffmpeg", "-y", "-i", str(wav_file), "-ac", "1", "-ar", "16000", str(mono_file)],
        capture_output=True,
    )
    if conv.returncode == 0 and mono_file.is_file():
        wav_file.unlink()
        mono_file.rename(wav_file)
    else:
        print("Warning: ffmpeg mono conversion failed, trying original", file=sys.stderr)

    transcript_file = video_dir / "audio-transcript.txt"
    transcribe_script = SCRIPT_DIR / "transcribe.py"

    result = subprocess.run(
        ["uv", "run", str(transcribe_script), str(wav_file), str(transcript_file)],
        stdout=subprocess.PIPE,
        text=True,
    )

    wav_file.unlink(missing_ok=True)

    if result.returncode != 0:
        return None

    if transcript_file.is_file():
        return transcript_file
    return None


def _extract_youtube_metadata(url: str) -> dict[str, str] | None:
    """Extract video metadata (id, title, channel, description, thumbnail URL) via yt-dlp.

    Returns None on failure so callers can decide how to handle errors.
    """
    from yt_dlp import YoutubeDL

    try:
        with YoutubeDL({"quiet": True, "no_warnings": True, "logger": _SilentLogger()}) as ydl:  # type: ignore[arg-type]
            info = ydl.extract_info(url, download=False)
    except Exception as exc:
        print(f"Error: Could not extract video metadata: {exc}", file=sys.stderr)
        return None

    if not info or not info.get("id"):
        print("Error: Could not extract video ID from URL", file=sys.stderr)
        return None

    vid = info["id"]

    # Truncate description to ~300 chars at a sentence boundary.
    # Use ". " or ".\n" to find real sentence endings (avoids "1." list markers).
    raw_desc = info.get("description") or ""
    if len(raw_desc) > 300:
        candidate = raw_desc[:300]
        # Search for the last sentence-ending period: letter followed by ". "
        # (avoids matching list markers like "1." or abbreviations).
        best = -1
        for m in re.finditer(r"(?<=[a-zA-Z])\.\s", candidate):
            best = m.start()
        if best > 100:
            raw_desc = raw_desc[: best + 1]
        else:
            raw_desc = candidate.rsplit("\n", 1)[0] if "\n" in candidate[100:] else candidate

    return {
        "id": vid,
        "title": info.get("title") or "",
        "channel": info.get("channel") or info.get("uploader") or "",
        "description": raw_desc,
        "thumbnail_url": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
    }


def _fetch_web_metadata(url: str) -> dict[str, str] | None:
    """Fetch OpenGraph and Twitter Card metadata from a web page.

    Parses <meta> tags from the page's <head>. Returns a dict with keys
    site_name, title, description, image_url (all optional, empty string
    if not found). Returns None if the page cannot be fetched.
    """
    from html.parser import HTMLParser

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "wisdom/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            # Read only the first 50KB - meta tags are in <head>.
            raw = resp.read(50 * 1024).decode(errors="replace")
    except Exception:
        return None

    og: dict[str, str] = {}
    tc: dict[str, str] = {}

    class _MetaParser(HTMLParser):
        def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
            if tag != "meta":
                return
            attr: dict[str, str] = {k: v for k, v in attrs if v is not None}
            content = attr.get("content", "")
            if not content:
                return
            prop = attr.get("property", "")
            name = attr.get("name", "")
            if prop.startswith("og:"):
                og[prop[3:]] = content
            elif name.startswith("twitter:"):
                tc[name[8:]] = content

    try:
        _MetaParser().feed(raw)
    except Exception:
        return None

    # Prefer OG, fall back to Twitter Card.
    image_url = og.get("image", tc.get("image", ""))
    # Handle relative image URLs.
    if image_url and not image_url.startswith(("http://", "https://")):
        from urllib.parse import urljoin
        image_url = urljoin(url, image_url)

    return {
        "site_name": og.get("site_name", tc.get("site", "")),
        "title": og.get("title", tc.get("title", "")),
        "description": og.get("description", tc.get("description", "")),
        "image_url": image_url,
    }


def _enrich_entry(md_path: Path, *, overwrite: bool = False) -> bool:
    """Enrich a wisdom entry with metadata and thumbnail from its source.

    For YouTube entries, fetches via yt-dlp. For web entries, fetches
    OpenGraph/Twitter Card metadata. Returns True if anything was updated.
    """
    fm = _parse_frontmatter(md_path)
    if not fm:
        return False
    sources = _fm_sources(fm)
    if not sources:
        return False
    primary = sources[0]

    source_type = fm.get("source_type", "")
    entry_dir = md_path.parent
    has_thumbnail = (entry_dir / "thumbnail.jpg").is_file()
    updates: dict[str, str] = {}

    if source_type == "youtube":
        if not overwrite and has_thumbnail and fm.get("youtube_channel"):
            return False
        metadata = _extract_youtube_metadata(primary)
        if metadata is None:
            return False
        if metadata.get("channel"):
            updates["youtube_channel"] = metadata["channel"]
        if metadata.get("title"):
            updates["youtube_title"] = metadata["title"]
        if metadata.get("description"):
            updates["youtube_description"] = metadata["description"]
        image_url = metadata.get("thumbnail_url", "")

    elif source_type == "web":
        if not overwrite and has_thumbnail and fm.get("og_site_name"):
            return False
        metadata = _fetch_web_metadata(primary)
        if metadata is None:
            return False
        if metadata.get("site_name"):
            updates["og_site_name"] = metadata["site_name"]
        image_url = metadata.get("image_url", "")

    else:
        return False

    # Download thumbnail if we have an image URL and no existing thumbnail.
    if image_url and (overwrite or not has_thumbnail):
        _download_thumbnail(image_url, entry_dir / "thumbnail.jpg")

    if not fm.get("thumbnail", "").startswith("false") and (entry_dir / "thumbnail.jpg").is_file():
        updates["thumbnail"] = "thumbnail.jpg"

    if updates:
        _update_frontmatter(md_path, updates, overwrite=overwrite)
        return True
    return False


def _download_thumbnail(thumbnail_url: str, dest_path: Path) -> bool:
    """Download an image, resize, and save as compressed JPEG."""
    try:
        req = urllib.request.Request(thumbnail_url, headers={"User-Agent": "wisdom/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            raw = resp.read()
    except Exception as exc:
        print(f"Warning: Could not download thumbnail: {exc}", file=sys.stderr)
        return False

    try:
        import io

        from PIL import Image

        img = Image.open(io.BytesIO(raw))
        if img.width > 480:
            ratio = 480 / img.width
            img = img.resize((480, int(img.height * ratio)), Image.Resampling.LANCZOS)
        img = img.convert("RGB")
        img.save(dest_path, "JPEG", quality=80, optimize=True)
    except ImportError:
        dest_path.write_bytes(raw)
    except Exception as exc:
        print(f"Warning: Thumbnail processing failed, saving raw: {exc}", file=sys.stderr)
        dest_path.write_bytes(raw)

    return True


_PLACEHOLDER_PALETTES = [
    ("#667eea", "#764ba2"),  # indigo to purple
    ("#f093fb", "#f5576c"),  # pink to coral
    ("#4facfe", "#00f2fe"),  # sky blue to cyan
    ("#43e97b", "#38f9d7"),  # green to mint
    ("#fa709a", "#fee140"),  # rose to gold
    ("#a18cd1", "#fbc2eb"),  # lavender to blush
    ("#fccb90", "#d57eeb"),  # peach to violet
    ("#e0c3fc", "#8ec5fc"),  # lilac to blue
    ("#f6d365", "#fda085"),  # amber to salmon
    ("#84fab0", "#8fd3f4"),  # seafoam to light blue
    ("#cfd9df", "#e2ebf0"),  # silver to mist
    ("#a1c4fd", "#c2e9fb"),  # soft blue to ice
]


def _placeholder_thumbnail_svg(title: str) -> str:
    """Generate an SVG data URI placeholder based on a hash of the title."""
    digest = int(hashlib.md5(title.encode()).hexdigest(), 16)  # noqa: S324
    palette = _PLACEHOLDER_PALETTES[digest % len(_PLACEHOLDER_PALETTES)]
    angle = (digest >> 8) % 360
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" width="102" height="76">'
        "<defs>"
        f'<linearGradient id="g" gradientTransform="rotate({angle},.5,.5)"'
        ' gradientUnits="objectBoundingBox">'
        f'<stop offset="0%" stop-color="{palette[0]}"/>'
        f'<stop offset="100%" stop-color="{palette[1]}"/>'
        "</linearGradient>"
        "</defs>"
        '<rect width="102" height="76" fill="url(#g)" rx="4"/>'
        "</svg>"
    )
    encoded = base64.b64encode(svg.encode()).decode()
    return f"data:image/svg+xml;base64,{encoded}"


def _write_metadata_json(video_dir: Path, metadata: dict[str, str]) -> None:
    """Persist video metadata to metadata.json in the output directory."""
    meta_path = video_dir / "metadata.json"
    payload = {
        "id": metadata.get("id", ""),
        "title": metadata.get("title", ""),
        "channel": metadata.get("channel", ""),
        "description": metadata.get("description", ""),
        "thumbnail_url": metadata.get("thumbnail_url", ""),
    }
    meta_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _print_transcript_output(
    transcript_file: Path, video_dir: Path, metadata: dict[str, str] | None = None,
) -> None:
    """Print standard transcript output lines."""
    print(f"TRANSCRIPT_PATH: {transcript_file}")
    print(f"OUTPUT_DIR: {video_dir}")
    if metadata:
        _write_metadata_json(video_dir, metadata)
        if metadata.get("channel"):
            print(f"YOUTUBE_CHANNEL: {metadata['channel']}")
        if metadata.get("title"):
            print(f"YOUTUBE_TITLE: {metadata['title']}")
        if (video_dir / "thumbnail.jpg").is_file():
            print("THUMBNAIL: thumbnail.jpg")
        print("METADATA: metadata.json")
    print(f"NEXT_STEP: uv run <skill-dir>/scripts/wisdom.py rename \"{video_dir}\" \"<Short-Description>\"")


def cmd_transcript(args: argparse.Namespace) -> None:
    url: str = args.url
    base_dir = detect_base_dir()

    metadata = _extract_youtube_metadata(url)
    if not metadata:
        print("Error: Could not extract video metadata from URL", file=sys.stderr)
        sys.exit(1)

    video_id = metadata["id"]
    video_dir = base_dir / video_id
    video_dir.mkdir(parents=True, exist_ok=True)

    # Download thumbnail (non-fatal on failure).
    thumb_url = metadata.get("thumbnail_url")
    if thumb_url:
        _download_thumbnail(thumb_url, video_dir / "thumbnail.jpg")

    # Try with cookies first, then without
    download_ok = _download_transcript(url, video_dir, use_cookies=True)
    if not download_ok:
        download_ok = _download_transcript(url, video_dir, use_cookies=False)

    json3_files = list(video_dir.glob("*.json3"))
    if not download_ok or not json3_files:
        # Fallback: download audio and transcribe locally with Parakeet TDT v2
        transcript_file = _audio_transcription_fallback(url, video_dir)
        if transcript_file is None:
            print("Error: No subtitles available and audio transcription failed", file=sys.stderr)
            print(f"Check: {video_dir}", file=sys.stderr)
            print("", file=sys.stderr)
            print("This may be due to:", file=sys.stderr)
            print("  - Age-restricted video requiring login", file=sys.stderr)
            print("  - Video has no available subtitles", file=sys.stderr)
            print("  - Video is private or unlisted", file=sys.stderr)
            print("  - Rate limiting from YouTube", file=sys.stderr)
            print("  - Audio transcription deps not installed (pip install 'onnx-asr[cpu,hub]')", file=sys.stderr)
            sys.exit(1)

        _print_transcript_output(transcript_file, video_dir, metadata)
        return

    # Convert JSON3 to clean text
    converted = 0
    for json3_file in json3_files:
        base_name = json3_file.stem  # e.g. "Title.en"
        # Remove language code suffix
        if "." in base_name:
            base_name = base_name.rsplit(".", 1)[0]
        safe_name = _sanitise_filename(base_name)
        output_file = video_dir / f"{safe_name}-transcript.txt"

        try:
            text = _json3_to_text(json3_file)
            output_file.write_text(text, encoding="utf-8")
            json3_file.unlink()
            converted += 1
        except Exception as exc:
            print(f"Error: Failed to convert {json3_file.name}: {exc}", file=sys.stderr)

    # Clean up stray .txt files without the -transcript suffix
    for txt_file in video_dir.glob("*.txt"):
        if not txt_file.name.endswith("-transcript.txt"):
            txt_file.unlink()

    if converted == 0:
        print("Error: No subtitles found or downloaded for this video", file=sys.stderr)
        print(f"Check: {video_dir}", file=sys.stderr)
        sys.exit(1)

    # Find the transcript file
    transcript_files = list(video_dir.glob("*-transcript.txt"))
    if not transcript_files:
        print("Error: Transcript file not found after conversion", file=sys.stderr)
        sys.exit(1)

    _print_transcript_output(transcript_files[0], video_dir, metadata)


# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

def cmd_output_dir(_: argparse.Namespace) -> None:
    print(detect_base_dir())


# ---------------------------------------------------------------------------
# Create directory with today's date prefix
# ---------------------------------------------------------------------------

def cmd_create_dir(args: argparse.Namespace) -> None:
    """Create a new date-prefixed directory in the wisdom base directory."""
    base_dir = detect_base_dir()
    tz = _local_tz()
    today = datetime.now(tz=tz).date().isoformat()
    clean_desc = _sanitise_dirname(args.description)
    if not clean_desc:
        print("Error: Description is empty after sanitisation", file=sys.stderr)
        sys.exit(1)

    new_name = f"{today}-{clean_desc}"
    dest = base_dir / new_name

    if dest.exists():
        print(f"Error: Directory already exists: {dest}", file=sys.stderr)
        sys.exit(1)

    dest.mkdir(parents=True, exist_ok=True)
    print(f"OUTPUT_DIR: {dest}")


# ---------------------------------------------------------------------------
# Rename directory
# ---------------------------------------------------------------------------

def _sanitise_dirname(name: str) -> str:
    """Convert a description into a clean directory name component.

    Replaces spaces and special chars with hyphens, collapses runs,
    strips leading/trailing hyphens, and title-cases each word.
    """
    # Replace common separators with hyphens
    name = re.sub(r"[\s_]+", "-", name)
    # Remove anything that isn't alphanumeric or hyphen
    name = re.sub(r"[^a-zA-Z0-9-]", "", name)
    # Collapse multiple hyphens
    name = re.sub(r"-{2,}", "-", name)
    name = name.strip("-")
    # Title-case each segment
    return "-".join(word.capitalize() for word in name.split("-") if word)


_FALLBACK_TZ = "Australia/Melbourne"


def _local_tz() -> ZoneInfo:
    """Resolve the local timezone. Works on macOS and Linux even in sandboxed environments."""
    # 1. Try /etc/localtime symlink (macOS and most Linux)
    try:
        link = os.readlink("/etc/localtime")
        tz_name = link.split("zoneinfo/")[-1]
        return ZoneInfo(tz_name)
    except (OSError, KeyError):
        pass
    # 2. Try /etc/timezone (Debian/Ubuntu)
    try:
        tz_name = Path("/etc/timezone").read_text().strip()
        return ZoneInfo(tz_name)
    except (OSError, KeyError):
        pass
    return ZoneInfo(_FALLBACK_TZ)


def cmd_rename(args: argparse.Namespace) -> None:
    source = Path(args.directory)
    if not source.is_dir():
        print(f"Error: Directory not found: {source}", file=sys.stderr)
        sys.exit(1)

    # Resolve local timezone - sandbox environments may force UTC
    tz = _local_tz()
    today = datetime.now(tz=tz).date().isoformat()
    clean_desc = _sanitise_dirname(args.description)
    if not clean_desc:
        print("Error: Description is empty after sanitisation", file=sys.stderr)
        sys.exit(1)

    new_name = f"{today}-{clean_desc}"
    dest = source.parent / new_name

    if dest.exists():
        print(f"Error: Destination already exists: {dest}", file=sys.stderr)
        sys.exit(1)

    source.rename(dest)
    print(f"OUTPUT_DIR: {dest}")


# ---------------------------------------------------------------------------
# Markdown formatting
# ---------------------------------------------------------------------------

def cmd_format(args: argparse.Namespace) -> None:
    os.environ["OPENSSL_CONF"] = "/dev/null"

    runner: list[str] | None = None
    if shutil.which("bunx"):
        runner = ["bunx"]
    elif shutil.which("npx"):
        runner = ["npx", "-y"]
    else:
        if _is_mac():
            install = "brew install node (for npx) or: curl -fsSL https://bun.sh/install | bash (for bunx)"
        else:
            install = "sudo apt install nodejs npm (for npx) or: curl -fsSL https://bun.sh/install | bash (for bunx)"
        msg = (
            "MISSING_DEPS: bunx or npx\n"
            f"INSTALL: {install}\n"
            "ACTION: If you are allowed to, install one of the above and call this script again. "
            "Otherwise, continue without formatting and at the end of your analysis let the user know "
            "that prettier could not run because neither bunx nor npx is installed. "
            "The output will still be correct, just not consistently formatted."
        )
        print(msg, file=sys.stderr)
        sys.exit(2)

    mode = "--check" if args.check else "--write"
    cmd = [*runner, "prettier", mode, *args.files]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"prettier failed (exit {result.returncode}):", file=sys.stderr)
        if result.stdout:
            print(result.stdout, file=sys.stderr)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)


# ---------------------------------------------------------------------------
# Frontmatter helpers
# ---------------------------------------------------------------------------

def _strip_frontmatter(md_text: str) -> str:
    """Remove YAML frontmatter (between --- markers) from markdown text."""
    if not md_text.startswith("---"):
        return md_text
    end = md_text.find("\n---", 3)
    if end == -1:
        return md_text
    return md_text[end + 4:].lstrip("\n")


def _unquote_yaml_scalar(value: str) -> str:
    """Strip matching surrounding quotes from a YAML scalar."""
    if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
        return value[1:-1].replace('\\"', '"').replace("\\'", "'")
    return value


def _split_yaml_flow_list(inner: str) -> list[str]:
    """Split a flow-style YAML list body, respecting quoted commas."""
    items: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    for ch in inner:
        if quote is not None:
            buf.append(ch)
            if ch == quote:
                quote = None
        elif ch in ('"', "'"):
            buf.append(ch)
            quote = ch
        elif ch == ",":
            items.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    if buf:
        items.append("".join(buf))
    return items


def _parse_frontmatter(md_path: Path) -> dict[str, Any] | None:
    """Parse YAML frontmatter from a markdown file.

    Handles simple key: value pairs, quoted strings, YAML folded block
    scalars (>), flow-style lists ([a, b, c]) and block-style lists
    (one ``- item`` per line). Scalar values come back as strings; list
    values come back as ``list[str]``. Returns None if no frontmatter
    is found.
    """
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm_block = text[4:end]

    result: dict[str, Any] = {}
    current_key: str | None = None
    value_lines: list[str] = []
    list_items: list[str] | None = None

    def _flush() -> None:
        if current_key is None:
            return
        if list_items is not None:
            result[current_key] = list_items
            return
        joined = " ".join(value_lines).strip()
        # Late-detect a flow-style list that spanned multiple lines
        # (e.g. ``tags:`` followed by ``[\n  a,\n  b,\n]``).
        if joined.startswith("[") and joined.endswith("]"):
            inner = joined[1:-1].strip()
            result[current_key] = (
                [_unquote_yaml_scalar(item.strip())
                 for item in _split_yaml_flow_list(inner) if item.strip()]
                if inner else []
            )
            return
        result[current_key] = joined

    for line in fm_block.split("\n"):
        key_match = re.match(r"^([a-z_]+)\s*:\s*(.*)", line)
        if key_match and not line[0].isspace():
            _flush()
            current_key = key_match.group(1)
            value = key_match.group(2).strip()
            list_items = None
            value_lines = []
            if value.startswith("[") and value.endswith("]"):
                inner = value[1:-1].strip()
                list_items = (
                    [_unquote_yaml_scalar(item.strip())
                     for item in _split_yaml_flow_list(inner) if item.strip()]
                    if inner else []
                )
            elif value in (">", "|", ">-", "|-") or value == "":
                value_lines = []
            else:
                value_lines = [_unquote_yaml_scalar(value)]
        elif current_key is not None and (line.startswith("  ") or line.startswith("\t")):
            stripped = line.strip()
            if stripped.startswith("- "):
                if list_items is None:
                    list_items = []
                list_items.append(_unquote_yaml_scalar(stripped[2:].strip()))
            elif list_items is None:
                value_lines.append(stripped)

    _flush()
    return result if result else None


def _fm_str(fm: dict[str, Any] | None, key: str, default: str = "") -> str:
    """Read a scalar string from frontmatter; coerce list values to comma-joined."""
    if not fm:
        return default
    val = fm.get(key, default)
    if isinstance(val, list):
        return ", ".join(str(v) for v in val)
    return str(val) if val is not None else default


def _fm_list(fm: dict[str, Any] | None, key: str) -> list[str]:
    """Read a list value from frontmatter; tolerate scalar by splitting on commas."""
    if not fm:
        return []
    val = fm.get(key)
    if isinstance(val, list):
        return [str(v).strip() for v in val if str(v).strip()]
    if isinstance(val, str) and val.strip():
        return [item.strip() for item in val.split(",") if item.strip()]
    return []


def _fm_sources(fm: dict[str, Any] | None) -> list[str]:
    """Read one or more source URLs from frontmatter.

    Prefers the ``sources`` list (current schema); falls back to the legacy
    scalar ``source`` field so entries created before the migration still
    resolve. Returns an empty list when neither is present.
    """
    sources = _fm_list(fm, "sources")
    if sources:
        return sources
    legacy = _fm_str(fm, "source")
    return [legacy] if legacy else []


# Separators seen where several URLs were crammed into one legacy ``source``
# value: a comma, or " + " / " and " flanked by whitespace, or a newline.
# The whitespace flanks keep us from splitting a path segment like ``/and/``.
_SOURCE_SPLIT_RE = re.compile(r"\s*,\s*|\s+\+\s+|\s+and\s+|\n")


def _split_source_value(value: str) -> list[str]:
    """Split one legacy source value into individual URLs.

    A single URL returns a one-element list; a value holding several URLs
    (comma, ``+``, or ``and`` separated) is split into one entry per URL.
    """
    value = value.strip()
    if value.count("http") <= 1:
        return [value] if value else []
    return [p.strip() for p in _SOURCE_SPLIT_RE.split(value) if p.strip()]


_LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]|\d+\.)\s")


def _normalise_list_markdown(md_text: str) -> str:
    """Fix common markdown list issues that break the Python markdown renderer.

    1. Remove blank lines between list items - parsers treat these as separate
       lists, causing orphaned empty bullets in PDF output.
    2. Convert 2-space nested list indentation to 4-space - the Python markdown
       library requires 4-space indent for nesting, but most agents and editors
       default to 2-space.
    """
    lines = md_text.split("\n")
    result: list[str] = []
    for i, line in enumerate(lines):
        # Drop blank lines between two list items to prevent split lists
        if (line.strip() == ""
                and 0 < i < len(lines) - 1
                and _LIST_ITEM_RE.match(lines[i - 1])
                and _LIST_ITEM_RE.match(lines[i + 1])):
            continue
        # Double leading whitespace on indented list items so 2-space nesting
        # becomes 4-space (what the Python markdown library expects).
        m = _LIST_ITEM_RE.match(line)
        if m:
            leading = len(line) - len(line.lstrip())
            if leading > 0:
                line = " " * (leading * 2) + line.lstrip()
        result.append(line)
    return "\n".join(result)


def _stamp_analysis_date(md_path: Path) -> None:
    """Stamp today's local date as the analysis date in frontmatter and body.

    Sets the ``date`` frontmatter field (overwriting any existing value) and
    replaces the **Analysis Date** line in the markdown body so the date
    always reflects when the analysis was actually produced.
    """
    tz = _local_tz()
    today = datetime.now(tz=tz).date().isoformat()

    _update_frontmatter(md_path, {"date": today}, overwrite=True)

    text = md_path.read_text(encoding="utf-8")
    updated = re.sub(
        r"(\*\*Analysis Date\*\*:\s*).*",
        rf"\g<1>{today}",
        text,
    )
    if updated != text:
        md_path.write_text(updated, encoding="utf-8")


def _open_file(path: Path) -> None:
    """Open a file with the OS default viewer. Fails silently if unavailable."""
    try:
        if _is_mac():
            subprocess.run(["open", str(path)], stderr=subprocess.DEVNULL)
        elif shutil.which("xdg-open"):
            subprocess.run(["xdg-open", str(path)], stderr=subprocess.DEVNULL)
    except OSError:
        pass


# Diagram language identifiers that trigger rendering.
_DIAGRAM_LANGS = {"mermaid", "graphviz", "dot"}

# Regex matching <pre><code class="language-{lang}">...code...</code></pre>
_DIAGRAM_BLOCK_RE = re.compile(
    r'<pre><code class="language-(' + "|".join(_DIAGRAM_LANGS) + r')">'
    r"(.*?)</code></pre>",
    re.DOTALL,
)

_MERMAID_INK_URL = "https://mermaid.ink/img/"
_MERMAID_TIMEOUT = 10

# Cross-process throttle for mermaid.ink. Workers coordinate via a lock file
# in the system tempdir so no single worker can exceed the rate, regardless of
# how many ProcessPool children are active.
_MERMAID_LOCK_PATH = Path(tempfile.gettempdir()) / "wisdom-mermaid.lock"
_MERMAID_MIN_INTERVAL_S = float(os.environ.get("WISDOM_MERMAID_MIN_INTERVAL", "0.25"))
_MERMAID_MAX_RETRIES = 4
_MERMAID_BACKOFF_BASE_S = 1.0

# Anthropic-aligned theme init block for Mermaid diagrams.
_MERMAID_THEME_INIT = """\
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'primaryColor': '#e8e6dc',
    'primaryTextColor': '#141413',
    'primaryBorderColor': '#87867f',
    'secondaryColor': '#f0eee6',
    'secondaryTextColor': '#3d3d3a',
    'secondaryBorderColor': '#b0aea5',
    'tertiaryColor': '#faf9f5',
    'tertiaryTextColor': '#5e5d59',
    'tertiaryBorderColor': '#d1cfc5',
    'lineColor': '#87867f',
    'textColor': '#141413',
    'mainBkg': '#e8e6dc',
    'nodeBorder': '#87867f',
    'clusterBkg': '#f0eee6',
    'clusterBorder': '#d1cfc5',
    'titleColor': '#141413',
    'edgeLabelBackground': '#faf9f5',
    'nodeTextColor': '#141413',
    'actorBkg': '#e8e6dc',
    'actorBorder': '#87867f',
    'actorTextColor': '#141413',
    'actorLineColor': '#b0aea5',
    'signalColor': '#141413',
    'signalTextColor': '#141413',
    'labelBoxBkgColor': '#f0eee6',
    'labelBoxBorderColor': '#b0aea5',
    'labelTextColor': '#141413',
    'loopTextColor': '#3d3d3a',
    'noteBkgColor': '#ebdbbc',
    'noteTextColor': '#3d3d3a',
    'noteBorderColor': '#d4a27f',
    'activationBkgColor': '#d97757',
    'activationBorderColor': '#c6613f',
    'sequenceNumberColor': '#faf9f5',
    'sectionBkgColor': '#e8e6dc',
    'altSectionBkgColor': '#f0eee6',
    'sectionBkgColor2': '#faf9f5',
    'taskBkgColor': '#bcd1ca',
    'taskBorderColor': '#788c5d',
    'taskTextColor': '#141413',
    'taskTextDarkColor': '#141413',
    'taskTextClickableColor': '#d97757',
    'activeTaskBkgColor': '#d97757',
    'activeTaskBorderColor': '#c6613f',
    'doneTaskBkgColor': '#cbcadb',
    'doneTaskBorderColor': '#87867f',
    'critBkgColor': '#ebcece',
    'critBorderColor': '#c46686',
    'todayLineColor': '#d97757',
    'fontFamily': 'system-ui, -apple-system, sans-serif',
    'fontSize': '14px'
  }
}}%%
"""

# Anthropic-aligned default attributes for Graphviz diagrams.
_GRAPHVIZ_THEME_ATTRS = """\
    graph [
        bgcolor="#faf9f5"
        fontname="Helvetica Neue"
        fontsize=12
        fontcolor="#141413"
        pad=0.5
    ]
    node [
        shape=box
        style="filled,rounded"
        fillcolor="#e8e6dc"
        color="#87867f"
        fontname="Helvetica Neue"
        fontsize=11
        fontcolor="#141413"
        penwidth=1.2
        margin="0.15,0.1"
    ]
    edge [
        color="#87867f"
        fontname="Helvetica Neue"
        fontsize=10
        fontcolor="#3d3d3a"
        arrowsize=0.8
        penwidth=1.0
    ]
"""


def _apply_mermaid_theme(code: str) -> str:
    """Prepend the Anthropic theme init block if the diagram lacks one."""
    if "%%{init:" in code or "%%{ init:" in code:
        return code
    return _MERMAID_THEME_INIT + code


def _apply_graphviz_theme(code: str) -> str:
    """Inject default graph/node/edge attributes if the diagram lacks them."""
    # Skip if the user already defined graph-level attributes
    if re.search(r"(?:graph|node|edge)\s*\[", code):
        return code
    # Insert defaults after the opening brace of the first graph/digraph
    m = re.search(r"((?:di)?graph\s+\w*\s*\{)", code)
    if m:
        insert_pos = m.end()
        return code[:insert_pos] + "\n" + _GRAPHVIZ_THEME_ATTRS + code[insert_pos:]
    return code


# A4 usable width in pt with 18mm margins: (210 - 36) * 72/25.4 ~ 493pt
_PAGE_WIDTH_PT = 493.0


def _render_graphviz(code: str, *, fmt: str = "svg", dpi: int | None = None) -> bytes | None:
    """Render a Graphviz DOT string. Returns image bytes, or None if unavailable.

    ``fmt`` selects the output ("svg" for the PDF path, "png" for ePub where
    Kindle's SVG support is unreliable). ``dpi`` (raster only) is injected as a
    graph attribute so PNG output is sharp on high-density e-reader screens.
    """
    try:
        import graphviz  # type: ignore[import-untyped]
    except ImportError:
        return None
    if dpi is not None:
        m = re.search(r"((?:di)?graph\s+\w*\s*\{)", code)
        if m:
            code = code[:m.end()] + f"\n    graph [dpi={dpi}];\n" + code[m.end():]
    try:
        return graphviz.Source(code).pipe(format=fmt)
    except Exception:
        return None


def _svg_dimensions(svg: bytes) -> tuple[float, float] | None:
    """Extract width and height (in pt) from an SVG's attributes."""
    header = svg[:1024].decode(errors="replace")
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)pt"[^>]*\bheight="([\d.]+)pt"', header)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


def _mermaid_throttle() -> None:
    """Cross-process token bucket: ensure at least _MERMAID_MIN_INTERVAL_S
    has elapsed since the last mermaid.ink call by any worker.

    Uses fcntl.flock on a tempfile that stores the last-call timestamp.
    Sleeps inside the critical section to enforce spacing, then writes the
    new timestamp before releasing the lock.
    """
    if _MERMAID_MIN_INTERVAL_S <= 0:
        return
    # 'a+' creates if missing; we read+seek+write inside the lock.
    # Wall-clock time.time() is required: monotonic clocks have per-process
    # origins and are not comparable across worker processes.
    with open(_MERMAID_LOCK_PATH, "a+") as fh:
        fcntl.flock(fh.fileno(), fcntl.LOCK_EX)
        try:
            fh.seek(0)
            raw = fh.read().strip()
            last = float(raw) if raw else 0.0
            now = time.time()
            wait = _MERMAID_MIN_INTERVAL_S - (now - last)
            if wait > 0:
                time.sleep(wait)
            fh.seek(0)
            fh.truncate()
            fh.write(f"{time.time():.6f}")
            fh.flush()
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def _render_mermaid(code: str) -> tuple[bytes, str] | None:
    """Render a Mermaid diagram via the mermaid.ink public API.

    Returns (image_bytes, mime_type) or None on failure. Uses the /img/
    endpoint which returns a rasterised JPEG - the /svg/ endpoint uses
    foreignObject for text labels which WeasyPrint cannot render.

    Cross-worker rate limiting via _mermaid_throttle prevents bursts when
    multiple ProcessPool workers render diagrams simultaneously. Retries
    with exponential backoff on HTTP 429/503.
    """
    payload = base64.urlsafe_b64encode(code.encode()).decode()
    url = _MERMAID_INK_URL + payload
    req = urllib.request.Request(url, headers={"User-Agent": "wisdom-pdf/1.0"})

    for attempt in range(_MERMAID_MAX_RETRIES):
        _mermaid_throttle()
        try:
            with urllib.request.urlopen(req, timeout=_MERMAID_TIMEOUT) as resp:
                data: bytes = resp.read()
                content_type = resp.headers.get("Content-Type", "image/jpeg")
                mime = content_type.split(";")[0].strip()
                return data, mime
        except urllib.error.HTTPError as exc:
            # Retry on rate limit / transient server errors.
            if exc.code in (429, 502, 503, 504) and attempt < _MERMAID_MAX_RETRIES - 1:
                retry_after = exc.headers.get("Retry-After") if exc.headers else None
                try:
                    delay = float(retry_after) if retry_after else 0.0
                except (TypeError, ValueError):
                    delay = 0.0
                delay = max(delay, _MERMAID_BACKOFF_BASE_S * (2 ** attempt))
                time.sleep(delay)
                continue
            return None
        except Exception:
            return None
    return None


def _png_dimensions(data: bytes) -> tuple[int, int] | None:
    """Parse width and height (px) from a PNG's IHDR chunk."""
    import struct

    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def _jpeg_dimensions(data: bytes) -> tuple[int, int] | None:
    """Parse width and height from JPEG SOF marker."""
    import struct

    i = 2
    while i < len(data) - 9:
        if data[i] != 0xFF:
            break
        marker = data[i + 1]
        if marker in (0xC0, 0xC2):
            h = struct.unpack(">H", data[i + 5 : i + 7])[0]
            w = struct.unpack(">H", data[i + 7 : i + 9])[0]
            return w, h
        seg_len = struct.unpack(">H", data[i + 2 : i + 4])[0]
        i += 2 + seg_len
    return None


def _size_pct(natural_width_pt: float) -> int:
    """Map a diagram's natural width to a max-width percentage of the page.

    Small diagrams stay small, large ones can fill the page. Uses a
    linear ramp between 25% and 95% based on what fraction of the page
    the diagram naturally occupies.
    """
    ratio = natural_width_pt / _PAGE_WIDTH_PT
    pct = int(25 + ratio * 70)
    return max(25, min(pct, 95))


def _image_to_img_tag(data: bytes, mime: str, max_width_pct: int = 95) -> str:
    """Convert image bytes to an <img> tag with a base64 data URI."""
    b64 = base64.b64encode(data).decode()
    return (
        f'<img class="diagram" style="max-width:{max_width_pct}%"'
        f' src="data:{mime};base64,{b64}" alt="diagram" />'
    )


# DPI for rasterised (ePub) graphviz output. 200 keeps labels sharp on
# high-density e-reader screens (the Kindle Oasis is 300 ppi).
_GRAPHVIZ_RASTER_DPI = 200


def _render_diagrams(html_body: str, *, raster: bool = False) -> tuple[str, dict[str, int]]:
    """Find diagram code blocks in HTML and replace them with rendered images.

    Returns (modified_html, fallback_counts) where fallback_counts maps
    diagram language names to the number of blocks that failed to render.
    With ``raster=True`` (ePub), graphviz diagrams render to PNG rather than
    SVG, which Kindle's format conversion handles reliably.
    """
    fallbacks: dict[str, int] = {}

    def _replace(match: re.Match[str]) -> str:
        lang = match.group(1)
        code = html_mod.unescape(match.group(2))

        if lang in ("graphviz", "dot"):
            themed = _apply_graphviz_theme(code)
            if raster:
                png = _render_graphviz(themed, fmt="png", dpi=_GRAPHVIZ_RASTER_DPI)
                if png:
                    dims = _png_dimensions(png)
                    # px -> pt at the render DPI (72 pt per inch).
                    pct = _size_pct(dims[0] * 72 / _GRAPHVIZ_RASTER_DPI) if dims else 70
                    return _image_to_img_tag(png, "image/png", pct)
            else:
                svg = _render_graphviz(themed)
                if svg:
                    dims = _svg_dimensions(svg)
                    pct = _size_pct(dims[0]) if dims else 70
                    return _image_to_img_tag(svg, "image/svg+xml", pct)
        elif lang == "mermaid":
            result = _render_mermaid(_apply_mermaid_theme(code))
            if result:
                img_data, mime = result
                dims = _jpeg_dimensions(img_data) if "jpeg" in mime else None
                # Mermaid native px at ~96 DPI; convert to pt (* 0.75)
                pct = _size_pct(dims[0] * 0.75) if dims else 70
                return _image_to_img_tag(img_data, mime, pct)

        # Fallback: styled code block with a diagram-type label
        fallbacks[lang] = fallbacks.get(lang, 0) + 1
        return (
            f'<pre class="diagram-fallback" data-diagram-type="{lang}">'
            f'<code>{match.group(2)}</code></pre>'
        )

    result = _DIAGRAM_BLOCK_RE.sub(_replace, html_body)
    return result, fallbacks


def _import_pdf_deps() -> tuple[Any, Any]:
    """Import markdown + weasyprint, exiting with a friendly message if missing."""
    try:
        import markdown as md_lib  # type: ignore[import-untyped]  # ty: ignore[unresolved-import]
        from weasyprint import HTML  # type: ignore[import-untyped]  # ty: ignore[unresolved-import]
    except OSError as exc:
        if _is_mac():
            hint = "brew install pango"
        else:
            hint = "sudo apt install libpango-1.0-0 libcairo2 libgdk-pixbuf-2.0-0"
        print(
            f"MISSING_DEPS: weasyprint system libraries (Pango/Cairo)\n"
            f"INSTALL: {hint}\n"
            f"DETAIL: {exc}\n"
            f"ACTION: Install the missing system libraries and call this script again. "
            f"The markdown analysis is complete and usable without the PDF.",
            file=sys.stderr,
        )
        sys.exit(2)
    return md_lib, HTML


def _md_to_content_html(
    md_text: str, md_lib: Any, *, raster: bool = False,
) -> tuple[str, dict[str, int]]:
    """Convert analysis markdown to a rendered HTML body.

    Strips frontmatter, normalises list indentation, converts to HTML via
    python-markdown, then renders diagram code blocks to embedded images.
    Shared by the PDF and ePub renderers. ``raster=True`` (ePub) renders
    graphviz diagrams to PNG instead of SVG for Kindle compatibility.
    Returns (html_body, diagram_fallback_counts).
    """
    md_text = _strip_frontmatter(md_text)
    md_text = _normalise_list_markdown(md_text)
    html_body = md_lib.markdown(md_text, extensions=MD_EXTENSIONS)
    return _render_diagrams(html_body, raster=raster)


def _render_pdf_file(
    input_file: Path,
    output_file: Path,
    css_path: Path,
    md_lib: Any,
    HTML: Any,
    *,
    stamp_date: bool,
) -> dict[str, int]:
    """Render a single markdown file to PDF. Returns diagram fallback counts."""
    if stamp_date:
        _stamp_analysis_date(input_file)

    _enrich_entry(input_file)

    md_text = input_file.read_text(encoding="utf-8")
    html_body, diagram_fallbacks = _md_to_content_html(md_text, md_lib)

    if TEMPLATE_FILE.is_file():
        template = TEMPLATE_FILE.read_text(encoding="utf-8")
        css_link = f'  <link rel="stylesheet" href="{css_path.resolve()}" />'
        html = template.replace("$body$", html_body)
        html = html.replace("$lang$", "en")
        html = re.sub(r"\$for\(css\)\$.*?\$endfor\$", css_link, html, flags=re.DOTALL)
        html = re.sub(r"\$if\(.*?\)\$.*?\$endif\$", "", html, flags=re.DOTALL)
        html = re.sub(r"\$[a-z]+\$", "", html)
    else:
        html = (
            '<!DOCTYPE html>\n<html lang="en">\n<head>\n'
            '  <meta charset="utf-8" />\n'
            f'  <link rel="stylesheet" href="{css_path.resolve()}" />\n'
            f"</head>\n<body>\n{html_body}\n</body>\n</html>"
        )

    HTML(string=html, base_url=str(css_path.resolve().parent)).write_pdf(str(output_file))
    return diagram_fallbacks


def _print_diagram_fallbacks(diagram_fallbacks: dict[str, int]) -> None:
    for lang, count in diagram_fallbacks.items():
        s = "s" if count > 1 else ""
        print(f"DIAGRAM_FALLBACK: {count} {lang} diagram{s} could not be rendered and "
              f"ha{'ve' if count > 1 else 's'} been included as code block{s} instead.",
              file=sys.stderr)
        if lang == "mermaid":
            print("HINT: Mermaid rendering requires network access to mermaid.ink. "
                  "If offline, consider rewriting the diagram as a graphviz/dot code "
                  "block which renders locally. Alternatively, simplify the mermaid "
                  "diagram as complex diagrams may exceed the API's limits.",
                  file=sys.stderr)
        elif lang in ("graphviz", "dot"):
            print("HINT: Graphviz rendering requires the 'graphviz' system package. "
                  "Install with: brew install graphviz (macOS) or "
                  "sudo apt install graphviz (Linux).",
                  file=sys.stderr)


def cmd_pdf(args: argparse.Namespace) -> None:
    md_lib, HTML = _import_pdf_deps()

    css_path = Path(args.css) if args.css else CSS_FILE

    # Resolve input file: explicit arg or auto-detect single .md in cwd
    input_file: Path
    if args.input_file:
        input_file = Path(args.input_file)
    else:
        md_files = list(Path(".").glob("*.md"))
        if len(md_files) == 1:
            input_file = md_files[0]
        elif len(md_files) == 0:
            print("Error: No .md files found in current directory", file=sys.stderr)
            sys.exit(1)
        else:
            print("Error: Multiple .md files found, please specify one:", file=sys.stderr)
            for f in md_files:
                print(f"  {f}", file=sys.stderr)
            sys.exit(1)

    if not input_file.is_file():
        print(f"Error: File not found: {input_file}", file=sys.stderr)
        sys.exit(1)

    output_file = Path(args.output_file) if args.output_file else input_file.with_suffix(".pdf")

    if not css_path.is_file():
        print(f"Error: CSS stylesheet not found: {css_path}", file=sys.stderr)
        sys.exit(1)

    diagram_fallbacks = _render_pdf_file(
        input_file, output_file, css_path, md_lib, HTML, stamp_date=not args.no_stamp,
    )

    if args.open_after:
        _open_file(output_file)

    print(f"PDF_PATH: {output_file}")
    _print_diagram_fallbacks(diagram_fallbacks)

    # Regenerate the wisdom library index (non-fatal on failure).
    try:
        _regenerate_index(detect_base_dir())
    except Exception as exc:
        print(f"Warning: Index generation failed: {exc}", file=sys.stderr)


def _render_pdf_worker(
    md_path_str: str, output_path_str: str, css_path_str: str, stamp_date: bool,
) -> tuple[str, dict[str, int], str | None]:
    """Multiprocessing-safe wrapper around _render_pdf_file.

    Imports weasyprint inside the worker so the heavy native libs load once
    per process. Returns (output_path, diagram_fallbacks, error_str_or_None).
    Strings are used for arguments because Path objects pickle fine but
    keeping it explicit avoids surprises.
    """
    try:
        md_lib, HTML = _import_pdf_deps()
        fallbacks = _render_pdf_file(
            Path(md_path_str), Path(output_path_str), Path(css_path_str),
            md_lib, HTML, stamp_date=stamp_date,
        )
        return output_path_str, fallbacks, None
    except SystemExit as exc:
        return output_path_str, {}, f"PDF deps missing (exit {exc.code})"
    except Exception as exc:
        return output_path_str, {}, str(exc)


def cmd_regenerate_pdfs(args: argparse.Namespace) -> None:
    """Re-render every wisdom analysis PDF under base_dir, in parallel."""
    # Validate deps in the parent so we fail fast with a friendly message
    # before spawning workers.
    _import_pdf_deps()

    css_path = Path(args.css) if args.css else CSS_FILE
    if not css_path.is_file():
        print(f"Error: CSS stylesheet not found: {css_path}", file=sys.stderr)
        sys.exit(1)

    base_dir = Path(args.base_dir) if args.base_dir else detect_base_dir()
    if not base_dir.is_dir():
        print(f"Error: Base directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(base_dir.glob("*/*analysis.md"))
    if not md_files:
        print(f"No analysis markdown files found under {base_dir}", file=sys.stderr)
        return

    cpu_total = os.cpu_count() or 1
    default_workers = max(1, cpu_total - 2)
    workers = args.workers if args.workers is not None else default_workers
    workers = max(1, min(workers, len(md_files)))

    print(f"Regenerating {len(md_files)} PDF(s) under {base_dir}"
          f" (stamp_date={'on' if args.stamp else 'off'}, workers={workers})")

    rendered = 0
    failed: list[tuple[str, str]] = []
    css_str = str(css_path)

    if workers == 1:
        # Sequential path keeps imports cheap and tracebacks clean.
        md_lib, HTML = _import_pdf_deps()
        for md_file in md_files:
            output_file = md_file.with_suffix(".pdf")
            try:
                fallbacks = _render_pdf_file(
                    md_file, output_file, css_path, md_lib, HTML, stamp_date=args.stamp,
                )
                rendered += 1
                print(f"PDF_PATH: {output_file}")
                _print_diagram_fallbacks(fallbacks)
            except Exception as exc:
                failed.append((str(md_file), str(exc)))
                print(f"FAILED: {md_file}: {exc}", file=sys.stderr)
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {
                pool.submit(
                    _render_pdf_worker,
                    str(md_file), str(md_file.with_suffix(".pdf")), css_str, args.stamp,
                ): md_file
                for md_file in md_files
            }
            for fut in as_completed(futures):
                md_file = futures[fut]
                output_path_str, fallbacks, err = fut.result()
                if err is None:
                    rendered += 1
                    print(f"PDF_PATH: {output_path_str}")
                    _print_diagram_fallbacks(fallbacks)
                else:
                    failed.append((str(md_file), err))
                    print(f"FAILED: {md_file}: {err}", file=sys.stderr)

    print(f"Done: {rendered} rendered, {len(failed)} failed")

    # Regenerate the wisdom library index once at the end (non-fatal on failure).
    try:
        _regenerate_index(base_dir, force=True)
    except Exception as exc:
        print(f"Warning: Index generation failed: {exc}", file=sys.stderr)

    if failed:
        sys.exit(1)


# ---------------------------------------------------------------------------
# Index generation
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Search index, related entries, and tag-sprawl detection
# ---------------------------------------------------------------------------

# Filename used for the FTS5 search database written alongside index.html.
_SEARCH_DB_NAME = "wisdom-search.db"

# Filename caching precomputed related entries per dir_path.
_RELATED_CACHE_NAME = "wisdom-related.json"

# How many related entries to surface per item.
_RELATED_TOP_K = 8

# Reciprocal Rank Fusion constant. 60 is the conventional value.
_RRF_K = 60

# Maximum tags to consider for sprawl detection per pair.
_TAG_SPRAWL_RATIO = 0.82  # difflib SequenceMatcher.ratio threshold

# Minimal stopword list - small, English-only, focused on filler that hurts
# TF-IDF signal without filtering meaningful terms.
_STOPWORDS = frozenset({
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
    "have", "he", "in", "is", "it", "its", "of", "on", "or", "she", "that",
    "the", "their", "them", "they", "this", "to", "was", "we", "were", "what",
    "when", "which", "who", "will", "with", "you", "your", "but", "not", "so",
    "if", "about", "into", "than", "then", "there", "these", "those", "would",
    "could", "should", "can", "do", "does", "did", "i", "my", "me", "our",
    "us", "his", "her", "him",
})

_TOKEN_RE = re.compile(r"[a-z][a-z0-9'-]{2,}")


def _tokenise(text: str) -> list[str]:
    """Lowercase + strip; keep tokens of >=3 chars not in the stopword list."""
    return [
        t for t in _TOKEN_RE.findall(text.lower())
        if t not in _STOPWORDS
    ]


def _compute_related(
    entries: list[dict[str, Any]], top_k: int = _RELATED_TOP_K,
) -> dict[str, list[dict[str, Any]]]:
    """Compute related entries per item using TF-IDF cosine + tag Jaccard,
    fused via Reciprocal Rank Fusion.

    Returns a mapping from ``dir_path`` to a ranked list of related entries,
    each annotated with ``score``, ``why`` (``content``/``tags``/``both``)
    and a small subset of source fields.
    """
    n = len(entries)
    if n < 2:
        return {e["dir_path"]: [] for e in entries}

    # 1. Build term frequencies and document frequencies.
    tf_per_doc: list[Counter[str]] = []
    df: Counter[str] = Counter()
    for e in entries:
        tokens = _tokenise(str(e.get("body", "")))
        tf = Counter(tokens)
        tf_per_doc.append(tf)
        df.update(tf.keys())

    # 2. TF-IDF vector per doc (sparse dict). IDF uses smoothed log form.
    idf: dict[str, float] = {
        term: math.log((n + 1) / (count + 1)) + 1.0
        for term, count in df.items()
    }
    tfidf_per_doc: list[dict[str, float]] = []
    norms: list[float] = []
    for tf in tf_per_doc:
        if not tf:
            tfidf_per_doc.append({})
            norms.append(0.0)
            continue
        max_tf = max(tf.values())
        vec = {
            term: (0.5 + 0.5 * cnt / max_tf) * idf.get(term, 0.0)
            for term, cnt in tf.items()
        }
        norm = math.sqrt(sum(v * v for v in vec.values()))
        tfidf_per_doc.append(vec)
        norms.append(norm)

    # 3. Tag sets per doc.
    tag_sets: list[set[str]] = [
        {t.lower() for t in e.get("tags", []) if isinstance(t, str)}
        for e in entries
    ]

    def _cosine(i: int, j: int) -> float:
        if norms[i] == 0.0 or norms[j] == 0.0:
            return 0.0
        a, b = tfidf_per_doc[i], tfidf_per_doc[j]
        # Iterate over the smaller vector for fewer lookups.
        if len(a) > len(b):
            a, b = b, a
        return sum(v * b.get(k, 0.0) for k, v in a.items()) / (norms[i] * norms[j])

    def _jaccard(i: int, j: int) -> float:
        a, b = tag_sets[i], tag_sets[j]
        if not a or not b:
            return 0.0
        inter = len(a & b)
        if inter == 0:
            return 0.0
        return inter / len(a | b)

    related: dict[str, list[dict[str, Any]]] = {}

    for i in range(n):
        content_scores: list[tuple[float, int]] = []
        tag_scores: list[tuple[float, int]] = []
        for j in range(n):
            if i == j:
                continue
            cs = _cosine(i, j)
            if cs > 0:
                content_scores.append((cs, j))
            ts = _jaccard(i, j)
            if ts > 0:
                tag_scores.append((ts, j))

        content_scores.sort(reverse=True)
        tag_scores.sort(reverse=True)

        # Reciprocal Rank Fusion across the two signals.
        rrf: dict[int, float] = {}
        seen_in_content: set[int] = set()
        seen_in_tags: set[int] = set()
        for rank, (_, j) in enumerate(content_scores):
            rrf[j] = rrf.get(j, 0.0) + 1.0 / (_RRF_K + rank + 1)
            seen_in_content.add(j)
        for rank, (_, j) in enumerate(tag_scores):
            rrf[j] = rrf.get(j, 0.0) + 1.0 / (_RRF_K + rank + 1)
            seen_in_tags.add(j)

        if not rrf:
            related[entries[i]["dir_path"]] = []
            continue

        ranked = sorted(rrf.items(), key=lambda kv: kv[1], reverse=True)[:top_k]
        out: list[dict[str, Any]] = []
        for j, score in ranked:
            in_content = j in seen_in_content
            in_tags = j in seen_in_tags
            why = "both" if in_content and in_tags else "tags" if in_tags else "content"
            shared = sorted(tag_sets[i] & tag_sets[j]) if in_tags else []
            other = entries[j]
            out.append({
                "dir_path": other["dir_path"],
                "title": other["title"],
                "source_type": other.get("source_type", ""),
                "score": round(score, 5),
                "why": why,
                "shared_tags": shared,
            })
        related[entries[i]["dir_path"]] = out

    return related


def _detect_tag_sprawl(tag_freq: dict[str, int]) -> list[tuple[str, int, str, int]]:
    """Find pairs of tags that are likely duplicates.

    Compares every pair using difflib's SequenceMatcher.ratio for tags
    >=4 chars; for shorter tags, applies a containment check (one tag
    fully contained within the other). Returns tuples of
    (tag, count, near_tag, near_count) sorted so the higher-frequency
    tag in each pair appears first.
    """
    tags = list(tag_freq.keys())
    seen: set[tuple[str, str]] = set()
    pairs: list[tuple[str, int, str, int]] = []
    for i, a in enumerate(tags):
        for b in tags[i + 1:]:
            if a == b:
                continue
            similar = False
            if min(len(a), len(b)) >= 4:
                ratio = difflib.SequenceMatcher(a=a, b=b, autojunk=False).ratio()
                if ratio >= _TAG_SPRAWL_RATIO:
                    similar = True
            else:
                # Short tags: only flag when the shorter tag matches a
                # hyphen-separated component of the longer tag, or is a
                # prefix of its first component (catches `rl`/`rlhf`,
                # `ai`/`ai-safety` while avoiding coincidental letter
                # overlaps like `ai`/`guardrails`).
                short, long = (a, b) if len(a) <= len(b) else (b, a)
                if short != long:
                    parts = long.split("-")
                    if short in parts or parts[0].startswith(short):
                        similar = True
            if not similar:
                continue
            sa, sb = sorted((a, b))
            key: tuple[str, str] = (sa, sb)
            if key in seen:
                continue
            seen.add(key)
            ca, cb = tag_freq[a], tag_freq[b]
            if ca >= cb:
                pairs.append((a, ca, b, cb))
            else:
                pairs.append((b, cb, a, ca))
    pairs.sort(key=lambda p: (-p[1], -p[3]))
    return pairs


def _build_fts_index(
    base_dir: Path, entries: list[dict[str, Any]],
) -> Path | None:
    """Build a FTS5 SQLite index alongside index.html.

    Drops and rebuilds on every call - corpus is small enough that
    incremental updates are not worth the bookkeeping. Returns the path
    to the database, or None on failure.
    """
    db_path = base_dir / _SEARCH_DB_NAME
    try:
        # Touch a fresh file - simpler than DROP TABLE for FTS5 because
        # the contentless config and tokenizer settings can drift.
        if db_path.exists():
            db_path.unlink()
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("PRAGMA journal_mode = WAL")
            conn.execute("""
                CREATE VIRTUAL TABLE wisdom USING fts5(
                    dir_path UNINDEXED,
                    title,
                    author,
                    description,
                    tags,
                    body,
                    source_type UNINDEXED,
                    date UNINDEXED,
                    pdf_path UNINDEXED,
                    md_path UNINDEXED,
                    tokenize='porter unicode61'
                )
            """)
            rows = [
                (
                    str(e.get("dir_path", "")),
                    str(e.get("title", "")),
                    str(e.get("author", "")),
                    str(e.get("description", "")),
                    " ".join(str(t) for t in e.get("tags", [])),
                    str(e.get("body", "")),
                    str(e.get("source_type", "")),
                    str(e.get("date", "")),
                    str(e.get("pdf_path", "")),
                    str(e.get("md_path", "")),
                )
                for e in entries
            ]
            conn.executemany(
                "INSERT INTO wisdom("
                "dir_path, title, author, description, tags, body, "
                "source_type, date, pdf_path, md_path) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )
            conn.commit()
        finally:
            conn.close()
        return db_path
    except sqlite3.Error as exc:
        print(f"Warning: Could not build search index: {exc}", file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Index generation
# ---------------------------------------------------------------------------

def _collect_entries(base_dir: Path, *, reverse: bool = True) -> list[dict[str, Any]]:
    """Walk the wisdom corpus and build one metadata record per analysis entry.

    Parses frontmatter, computes word count and reading time, normalises short
    dates and tags, and resolves thumbnail presentation. Shared by index
    generation and ePub export so both operate on an identical entry set.
    Entries without frontmatter are skipped. Directories are date-prefixed, so
    ``reverse=True`` yields newest-first.
    """
    entries: list[dict[str, Any]] = []
    for md_file in sorted(base_dir.glob("*/*analysis.md"), reverse=reverse):
        fm = _parse_frontmatter(md_file)
        if not fm:
            continue

        dir_name = md_file.parent.name
        pdf_file = md_file.with_suffix(".pdf")

        # Compute word count and reading time from the analysis body.
        body = _strip_frontmatter(md_file.read_text(encoding="utf-8"))
        word_count = len(body.split())
        reading_time = max(1, round(word_count / 200))

        # Normalise short dates (YYYY-MM) to YYYY-MM-DD so string
        # comparison sorts them correctly in the JS frontend.
        raw_date = _fm_str(fm, "date")
        if re.fullmatch(r"\d{4}-\d{2}", raw_date):
            raw_date += "-01"
        raw_content_date = _fm_str(fm, "content_date")
        if re.fullmatch(r"\d{4}-\d{2}", raw_content_date):
            raw_content_date += "-01"

        title = _fm_str(fm, "title", dir_name)
        thumbnail_pref = _fm_str(fm, "thumbnail")

        # Normalise tags: lowercase, hyphenated, strip empties, dedupe.
        tags = [
            re.sub(r"\s+", "-", t.strip().lower()).strip("-")
            for t in _fm_list(fm, "tags")
        ]
        tags = [t for t in dict.fromkeys(tags) if t]

        entries.append({
            "title": title,
            "sources": _fm_sources(fm),
            "source_type": _fm_str(fm, "source_type"),
            "author": _fm_str(fm, "author"),
            "date": raw_date,
            "content_date": raw_content_date,
            "description": _fm_str(fm, "description"),
            "youtube_channel": _fm_str(fm, "youtube_channel"),
            "og_site_name": _fm_str(fm, "og_site_name"),
            "word_count": word_count,
            "reading_time": reading_time,
            "dir_path": dir_name,
            "pdf_path": f"{dir_name}/{pdf_file.name}" if pdf_file.is_file() else "",
            "md_path": f"{dir_name}/{md_file.name}",
            "tags": tags,
            "thumbnail": (
                _placeholder_thumbnail_svg(title)
                if thumbnail_pref.startswith("placeholder")
                else f"{dir_name}/thumbnail.jpg"
                if (not thumbnail_pref.startswith("false")
                    and (md_file.parent / "thumbnail.jpg").is_file())
                else ""
            ),
            "body": body,
        })
    return entries


def _regenerate_index(base_dir: Path, *, force: bool = False) -> None:
    """Regenerate the index.html in the wisdom base directory.

    Walks all subdirectories, parses frontmatter from analysis markdown
    files, computes reading time, and writes a self-contained HTML index.
    Controlled by the EXTRACT_WISDOM_CREATE_INDEX environment variable
    (defaults to "true"). Pass force=True to bypass the env var check.
    """
    if not force:
        env_val = os.environ.get(_INDEX_ENV_VAR, "true").lower()
        if env_val in ("false", "0", "no"):
            return

    if not base_dir.is_dir():
        return

    if not _INDEX_TEMPLATE.is_file():
        return

    entries = _collect_entries(base_dir, reverse=True)
    if not entries:
        return

    # Aggregate tag frequencies.
    tag_freq: dict[str, int] = {}
    for e in entries:
        for t in e.get("tags", []):
            tag_freq[t] = tag_freq.get(t, 0) + 1

    # Compute related entries (graceful fallback to empty lists on error).
    try:
        related_map = _compute_related(entries)
    except Exception as exc:
        print(f"Warning: related-entry computation failed: {exc}", file=sys.stderr)
        related_map = {e["dir_path"]: [] for e in entries}

    for e in entries:
        e["related"] = related_map.get(e["dir_path"], [])

    # Build the FTS5 search database alongside index.html.
    _build_fts_index(base_dir, entries)

    # Write related cache so the `related` subcommand can serve it without
    # re-walking the corpus or rebuilding the FTS5 db.
    try:
        cache_payload = {e["dir_path"]: e["related"] for e in entries}
        (base_dir / _RELATED_CACHE_NAME).write_text(
            json.dumps(cache_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        print(f"Warning: Could not write related cache: {exc}", file=sys.stderr)

    # Tag-sprawl warnings (informational; never fatal).
    if tag_freq:
        sprawl = _detect_tag_sprawl(tag_freq)
        if sprawl:
            print("TAG_SPRAWL_WARNINGS:", file=sys.stderr)
            for hi, hi_count, lo, lo_count in sprawl:
                print(
                    f"  {hi} ({hi_count}) ~ {lo} ({lo_count})  # consider "
                    f"merging via: wisdom.py tags --merge \"{lo}\" \"{hi}\"",
                    file=sys.stderr,
                )

    template = _INDEX_TEMPLATE.read_text(encoding="utf-8")
    entries_json = json.dumps(entries, indent=2, ensure_ascii=False)
    tag_freq_json = json.dumps(
        sorted(tag_freq.items(), key=lambda kv: (-kv[1], kv[0])),
        ensure_ascii=False,
    )
    # Escape </ sequences to prevent breaking out of the <script> tag.
    entries_json = entries_json.replace("</", r"<\/")
    tag_freq_json = tag_freq_json.replace("</", r"<\/")
    gen_date = datetime.now(tz=_local_tz()).date().isoformat()

    html = template.replace("$ENTRIES_JSON$", entries_json)
    html = html.replace("$TAG_FREQ_JSON$", tag_freq_json)
    html = html.replace("$SCHEMA_VERSION$", str(_INDEX_SCHEMA_VERSION))
    html = html.replace("$GENERATED_DATE$", gen_date)

    index_path = base_dir / "index.html"
    lock_path = base_dir / ".index.lock"

    # Acquire an exclusive file lock before writing to prevent concurrent
    # writes from parallel agents corrupting the index.
    try:
        lock_file = open(lock_path, "w")  # noqa: SIM115
        deadline = time.monotonic() + _INDEX_LOCK_TIMEOUT
        while True:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= deadline:
                    lock_file.close()
                    print(
                        f"LOCK_TIMEOUT: Could not acquire index lock after "
                        f"{_INDEX_LOCK_TIMEOUT}s.\n"
                        f"LOCK_FILE: {lock_path}\n"
                        f"ACTION: Another process may be holding the lock. "
                        f"Check for other running wisdom.py processes. "
                        f"If none exist, delete {lock_path} and retry.",
                        file=sys.stderr,
                    )
                    return
                time.sleep(0.5)

        index_path.write_text(html, encoding="utf-8")
        fcntl.flock(lock_file, fcntl.LOCK_UN)
        lock_file.close()
    except OSError as exc:
        print(f"Warning: Could not write index: {exc}", file=sys.stderr)

    # Optionally rebuild the corpus ebook (off by default; see _maybe_build_epub).
    _maybe_build_epub(base_dir)


def cmd_index(args: argparse.Namespace) -> None:
    """Regenerate the wisdom library index.html."""
    base_dir = Path(args.base_dir) if args.base_dir else detect_base_dir()
    _regenerate_index(base_dir, force=True)


# ---------------------------------------------------------------------------
# ePub export - bind the whole corpus into a single ebook
# ---------------------------------------------------------------------------
#
# An ePub is a ZIP of XHTML content documents, a shared stylesheet, images,
# and two navigation documents (nav.xhtml for EPUB3 readers, toc.ncx for older
# EPUB2 ones). Each wisdom entry becomes one chapter; the navigation documents
# plus a readable index chapter provide the generated table of contents.

_EPUB_ENV_VAR = "EXTRACT_WISDOM_CREATE_EPUB"
_EPUB_FILENAME = "Wisdom-Library.epub"

# Cover dimensions (px). 2:3 aspect matches common e-reader covers.
_EPUB_COVER_W = 1400
_EPUB_COVER_H = 2100

_EPUB_CONTAINER_XML = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<container version="1.0" '
    'xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n'
    '  <rootfiles>\n'
    '    <rootfile full-path="OEBPS/content.opf" '
    'media-type="application/oebps-package+xml"/>\n'
    '  </rootfiles>\n'
    '</container>\n'
)

_XHTML_OPEN = (
    '<?xml version="1.0" encoding="utf-8"?>\n'
    '<!DOCTYPE html>\n'
    '<html xmlns="http://www.w3.org/1999/xhtml" '
    'xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="en" lang="en">\n'
)


def _xhtml_document(title: str, body_html: str, *, body_class: str = "") -> str:
    """Wrap a rendered body in a minimal, well-formed XHTML5 document."""
    cls = f' class="{body_class}"' if body_class else ""
    return (
        _XHTML_OPEN
        + "<head>\n"
        + f"  <title>{html_mod.escape(title)}</title>\n"
        + '  <meta charset="utf-8"/>\n'
        + '  <link rel="stylesheet" type="text/css" href="style.css"/>\n'
        + "</head>\n"
        + f"<body{cls}>\n{body_html}\n</body>\n</html>\n"
    )


def _wellformed_body(body_html: str) -> str:
    """Return body_html unchanged if it parses as well-formed XML, else a safe
    fallback.

    ePub content documents must be valid XHTML. python-markdown emits XHTML
    (self-closed void elements), but raw HTML in a source file could slip in
    malformed markup. Rather than fail the whole book, a bad chapter degrades
    to an escaped code block so the build still completes.
    """
    import xml.etree.ElementTree as ET
    try:
        ET.fromstring(f"<div>{body_html}</div>")
        return body_html
    except ET.ParseError:
        return f"<pre>{html_mod.escape(body_html)}</pre>"


def _epub_chapter_name(idx: int) -> str:
    return f"chap-{idx:04d}.xhtml"


def _epub_part_name(year: str) -> str:
    return f"part-{year.lower()}.xhtml"


def _group_by_year(
    entries: list[dict[str, Any]],
) -> list[tuple[str, list[tuple[int, dict[str, Any]]]]]:
    """Group entries into contiguous year blocks, preserving order.

    Entries arrive newest-first, so years are already contiguous. Each group is
    ``(year_label, [(chapter_number, entry), ...])`` where chapter_number is the
    entry's 1-based position in the flat list (its ``chap-NNNN`` file). Entries
    without a parseable year fall under "Undated".
    """
    groups: list[tuple[str, list[tuple[int, dict[str, Any]]]]] = []
    for idx, e in enumerate(entries, 1):
        date = str(e.get("date") or "")
        year = date[:4] if re.fullmatch(r"\d{4}", date[:4]) else "Undated"
        if not groups or groups[-1][0] != year:
            groups.append((year, []))
        groups[-1][1].append((idx, e))
    return groups


def _epub_part_body(year: str, count: int) -> str:
    """Build a year part-divider page."""
    plural = "entry" if count == 1 else "entries"
    return (
        '<section class="part-divider">\n'
        f'<h1 class="part-title">{html_mod.escape(year)}</h1>\n'
        f'<p class="part-sub">{count} {plural}</p>\n'
        "</section>\n"
    )


def _hex_to_rgb(colour: str) -> tuple[int, int, int]:
    c = colour.lstrip("#")
    return (int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16))


def _load_cover_font(size: int) -> Any:
    """Load a sans-serif TrueType font at ``size``, trying common system paths
    and falling back to Pillow's default (scaled where supported)."""
    from PIL import ImageFont
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/HelveticaNeue.ttc",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size)
    except TypeError:  # Pillow < 10.1 has no size parameter
        return ImageFont.load_default()


def _wrap_text(text: str, font: Any, max_width: float, draw: Any) -> list[str]:
    """Greedily wrap ``text`` to lines no wider than ``max_width``."""
    lines: list[str] = []
    current = ""
    for word in text.split():
        trial = f"{current} {word}".strip()
        if not current or draw.textlength(trial, font=font) <= max_width:
            current = trial
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _generate_cover_png(title: str, subtitle: str) -> bytes | None:
    """Render a gradient cover with the title on a translucent panel.

    Fully offline: the gradient palette is chosen from a hash of the title
    (same scheme as index placeholders) and the text uses a system font.
    Returns PNG bytes, or None if Pillow is unavailable or rendering fails.
    """
    try:
        import io

        from PIL import Image, ImageDraw
    except ImportError:
        return None
    try:
        w, h = _EPUB_COVER_W, _EPUB_COVER_H
        digest = int(hashlib.md5(title.encode()).hexdigest(), 16)  # noqa: S324
        c1, c2 = _PLACEHOLDER_PALETTES[digest % len(_PLACEHOLDER_PALETTES)]
        top, bot = _hex_to_rgb(c1), _hex_to_rgb(c2)

        # Vertical gradient: build a 1px column then stretch to full width.
        grad = Image.new("RGB", (1, h))
        for y in range(h):
            t = y / (h - 1)
            grad.putpixel((0, y), tuple(
                round(top[k] + (bot[k] - top[k]) * t) for k in range(3)
            ))
        img = grad.resize((w, h)).convert("RGBA")

        # Translucent dark panel keeps text legible on any palette.
        margin = int(w * 0.09)
        panel_top, panel_bot = int(h * 0.30), int(h * 0.70)
        overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        box = [margin, panel_top, w - margin, panel_bot]
        try:
            od.rounded_rectangle(box, radius=int(w * 0.03), fill=(20, 20, 19, 140))
        except AttributeError:
            od.rectangle(box, fill=(20, 20, 19, 140))
        img = Image.alpha_composite(img, overlay).convert("RGB")

        draw = ImageDraw.Draw(img)
        title_font = _load_cover_font(int(w * 0.11))
        sub_font = _load_cover_font(int(w * 0.045))
        text_w = w - 2 * margin - int(w * 0.06)
        lines = _wrap_text(title, title_font, text_w, draw)

        line_h = int(w * 0.14)
        block_h = line_h * len(lines)
        y = panel_top + ((panel_bot - panel_top) - block_h) // 2
        ink = (250, 249, 245)
        for line in lines:
            lw = draw.textlength(line, font=title_font)
            draw.text(((w - lw) / 2, y), line, font=title_font, fill=ink)
            y += line_h
        if subtitle:
            sw = draw.textlength(subtitle, font=sub_font)
            draw.text(((w - sw) / 2, panel_bot - int(w * 0.10)), subtitle,
                      font=sub_font, fill=(230, 228, 220))

        buf = io.BytesIO()
        img.save(buf, "PNG", optimize=True)
        return buf.getvalue()
    except Exception as exc:
        print(f"Warning: cover generation failed: {exc}", file=sys.stderr)
        return None


def _epub_index_body(
    title: str, groups: list[tuple[str, list[tuple[int, dict[str, Any]]]]],
    gen_date: str, *, include_descriptions: bool = False,
) -> str:
    """Build the readable index chapter, grouped by year.

    Each entry shows its title link, a metadata line, and tags under a year
    heading. The description preview is omitted by default (more entries per
    page); pass include_descriptions=True to add it.
    """
    total = sum(len(chapters) for _, chapters in groups)
    parts = [
        f"<h1>{html_mod.escape(title)}</h1>",
        f'<p class="index-sub">{total} entries · generated {gen_date}</p>',
    ]
    for year, chapters in groups:
        parts.append(f'<h2 class="index-year">{html_mod.escape(year)}</h2>')
        parts.append('<ol class="entry-list">')
        for idx, e in chapters:
            href = _epub_chapter_name(idx)
            meta_bits = [e.get("date", ""), e.get("author", ""), e.get("source_type", "")]
            if e.get("reading_time"):
                meta_bits.append(f"{e['reading_time']} min read")
            meta = " · ".join(html_mod.escape(b) for b in meta_bits if b)
            parts.append('<li class="entry">')
            parts.append(f'<a class="entry-title" href="{href}">{html_mod.escape(e["title"])}</a>')
            if meta:
                parts.append(f'<p class="entry-meta">{meta}</p>')
            if include_descriptions and e.get("description"):
                parts.append(f'<p class="entry-desc">{html_mod.escape(e["description"])}</p>')
            if e.get("tags"):
                tags = " · ".join(html_mod.escape(t) for t in e["tags"])
                parts.append(f'<p class="entry-tags">{tags}</p>')
            parts.append("</li>")
        parts.append("</ol>")
    return "\n".join(parts)


def _epub_nav_xhtml(
    groups: list[tuple[str, list[tuple[int, dict[str, Any]]]]], *, has_cover: bool,
) -> str:
    """Build the EPUB3 navigation document: a nested (year -> chapters) ToC plus
    a landmarks nav so Kindle's Go-To menu and start-reading location work."""
    toc_items = ['<li><a href="index.xhtml">Wisdom Library</a></li>']
    for year, chapters in groups:
        subs = "".join(
            f'<li><a href="{_epub_chapter_name(i)}">{html_mod.escape(e["title"])}</a></li>'
            for i, e in chapters
        )
        toc_items.append(
            f'<li><a href="{_epub_part_name(year)}">{html_mod.escape(year)}</a>'
            f"<ol>{subs}</ol></li>"
        )
    toc = (
        '<nav epub:type="toc" id="toc">\n'
        "<h1>Contents</h1>\n"
        "<ol>\n" + "\n".join(toc_items) + "\n</ol>\n"
        "</nav>\n"
    )

    landmarks_items = []
    if has_cover:
        landmarks_items.append('<li><a epub:type="cover" href="cover.xhtml">Cover</a></li>')
    landmarks_items.append('<li><a epub:type="toc" href="index.xhtml">Contents</a></li>')
    landmarks_items.append('<li><a epub:type="bodymatter" href="index.xhtml">Start Reading</a></li>')
    landmarks = (
        '<nav epub:type="landmarks" id="landmarks" hidden="hidden">\n'
        "<h2>Guide</h2>\n"
        "<ol>\n" + "\n".join(landmarks_items) + "\n</ol>\n"
        "</nav>\n"
    )
    return _xhtml_document("Contents", toc + landmarks)


def _epub_ncx(
    title: str, uid: str, groups: list[tuple[str, list[tuple[int, dict[str, Any]]]]],
) -> str:
    """Build the EPUB2 NCX navigation document (fallback for older readers).

    Mirrors the nested nav.xhtml: a year navPoint wraps its chapter navPoints.
    playOrder runs sequentially through the whole tree in reading order.
    """
    def label(text: str) -> str:
        return f"<navLabel><text>{html_mod.escape(text)}</text></navLabel>"

    order = 1
    points = [
        f'<navPoint id="nav-index" playOrder="{order}">{label("Wisdom Library")}'
        f'<content src="index.xhtml"/></navPoint>'
    ]
    for gi, (year, chapters) in enumerate(groups):
        order += 1
        part_order = order
        child_xml: list[str] = []
        for i, e in chapters:
            order += 1
            child_xml.append(
                f'<navPoint id="nav-{i}" playOrder="{order}">{label(e["title"])}'
                f'<content src="{_epub_chapter_name(i)}"/></navPoint>'
            )
        points.append(
            f'<navPoint id="part-{gi}" playOrder="{part_order}">{label(year)}'
            f'<content src="{_epub_part_name(year)}"/>{"".join(child_xml)}</navPoint>'
        )
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">\n'
        "<head>\n"
        f'<meta name="dtb:uid" content="urn:uuid:{uid}"/>\n'
        '<meta name="dtb:depth" content="2"/>\n'
        '<meta name="dtb:totalPageCount" content="0"/>\n'
        '<meta name="dtb:maxPageNumber" content="0"/>\n'
        "</head>\n"
        f"<docTitle><text>{html_mod.escape(title)}</text></docTitle>\n"
        "<navMap>\n" + "\n".join(points) + "\n</navMap>\n"
        "</ncx>\n"
    )


def _epub_opf(
    title: str, uid: str, date_str: str, modified: str,
    groups: list[tuple[str, list[tuple[int, dict[str, Any]]]]], *, has_cover: bool,
) -> str:
    """Build the OPF package document (metadata, manifest, spine, and guide)."""
    manifest = [
        '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>',
        '<item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>',
        '<item id="css" href="style.css" media-type="text/css"/>',
        '<item id="index" href="index.xhtml" media-type="application/xhtml+xml"/>',
    ]
    spine: list[str] = []
    guide: list[str] = []
    if has_cover:
        manifest.append(
            '<item id="cover-image" href="cover.png" media-type="image/png" '
            'properties="cover-image"/>'
        )
        manifest.append('<item id="cover" href="cover.xhtml" media-type="application/xhtml+xml"/>')
        spine.append('<itemref idref="cover"/>')
        guide.append('<reference type="cover" title="Cover" href="cover.xhtml"/>')
    spine.append('<itemref idref="index"/>')
    for gi, (year, chapters) in enumerate(groups):
        part_id = f"part-{gi}"
        manifest.append(
            f'<item id="{part_id}" href="{_epub_part_name(year)}" '
            'media-type="application/xhtml+xml"/>'
        )
        spine.append(f'<itemref idref="{part_id}"/>')
        for i, _ in chapters:
            manifest.append(
                f'<item id="chap-{i:04d}" href="{_epub_chapter_name(i)}" '
                'media-type="application/xhtml+xml"/>'
            )
            spine.append(f'<itemref idref="chap-{i:04d}"/>')
    # Legacy guide references help older Kindle firmware open at the contents.
    guide.append('<reference type="toc" title="Contents" href="index.xhtml"/>')
    guide.append('<reference type="text" title="Start" href="index.xhtml"/>')
    cover_meta = '\n    <meta name="cover" content="cover-image"/>' if has_cover else ""
    return (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        '<package xmlns="http://www.idpf.org/2007/opf" version="3.0" '
        'unique-identifier="book-id" xml:lang="en">\n'
        '  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">\n'
        f'    <dc:identifier id="book-id">urn:uuid:{uid}</dc:identifier>\n'
        f"    <dc:title>{html_mod.escape(title)}</dc:title>\n"
        "    <dc:language>en-AU</dc:language>\n"
        "    <dc:creator>Extract Wisdom</dc:creator>\n"
        f"    <dc:date>{date_str}</dc:date>\n"
        f'    <meta property="dcterms:modified">{modified}</meta>{cover_meta}\n'
        "  </metadata>\n"
        "  <manifest>\n    " + "\n    ".join(manifest) + "\n  </manifest>\n"
        '  <spine toc="ncx">\n    ' + "\n    ".join(spine) + "\n  </spine>\n"
        "  <guide>\n    " + "\n    ".join(guide) + "\n  </guide>\n"
        "</package>\n"
    )


def _build_epub(
    base_dir: Path, entries: list[dict[str, Any]], output_file: Path,
    title: str, md_lib: Any, *, include_descriptions: bool = False,
) -> dict[str, int]:
    """Assemble the whole corpus into a single .epub. Returns diagram fallbacks."""
    fallbacks: dict[str, int] = {}
    chapter_docs: list[str] = []
    for e in entries:
        # raster=True renders graphviz to PNG (Kindle-safe) instead of SVG.
        body_html, fb = _md_to_content_html(e.get("body", ""), md_lib, raster=True)
        for lang, count in fb.items():
            fallbacks[lang] = fallbacks.get(lang, 0) + count
        chapter_docs.append(_xhtml_document(e["title"], _wellformed_body(body_html)))

    groups = _group_by_year(entries)

    tz = _local_tz()
    date_str = datetime.now(tz=tz).date().isoformat()
    modified = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # Deterministic id keyed to the library location so rebuilds keep it stable.
    uid = str(uuid.uuid5(uuid.NAMESPACE_URL, f"extract-wisdom:{base_dir}:{title}"))

    cover_png = _generate_cover_png(title, f"{len(entries)} entries · {date_str}")
    has_cover = cover_png is not None

    css_text = EPUB_CSS_FILE.read_text(encoding="utf-8") if EPUB_CSS_FILE.is_file() else ""
    index_doc = _xhtml_document(
        title, _epub_index_body(title, groups, date_str, include_descriptions=include_descriptions),
    )
    nav_doc = _epub_nav_xhtml(groups, has_cover=has_cover)
    ncx = _epub_ncx(title, uid, groups)
    opf = _epub_opf(title, uid, date_str, modified, groups, has_cover=has_cover)

    output_file.parent.mkdir(parents=True, exist_ok=True)
    deflate = zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(output_file, "w") as zf:
        # mimetype MUST be the first entry and stored uncompressed (ePub spec).
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("META-INF/container.xml", _EPUB_CONTAINER_XML, compress_type=deflate)
        zf.writestr("OEBPS/content.opf", opf, compress_type=deflate)
        zf.writestr("OEBPS/nav.xhtml", nav_doc, compress_type=deflate)
        zf.writestr("OEBPS/toc.ncx", ncx, compress_type=deflate)
        zf.writestr("OEBPS/style.css", css_text, compress_type=deflate)
        if has_cover:
            zf.writestr("OEBPS/cover.png", cover_png, compress_type=deflate)
            zf.writestr(
                "OEBPS/cover.xhtml",
                _xhtml_document("Cover", '<img class="cover-img" src="cover.png" alt="Cover"/>', body_class="cover"),
                compress_type=deflate,
            )
        zf.writestr("OEBPS/index.xhtml", index_doc, compress_type=deflate)
        for year, chapters in groups:
            zf.writestr(
                f"OEBPS/{_epub_part_name(year)}",
                _xhtml_document(year, _epub_part_body(year, len(chapters))),
                compress_type=deflate,
            )
        for idx, doc in enumerate(chapter_docs, 1):
            zf.writestr(f"OEBPS/{_epub_chapter_name(idx)}", doc, compress_type=deflate)

    return fallbacks


def _maybe_build_epub(base_dir: Path) -> None:
    """Rebuild the corpus ePub after an index refresh when opted in.

    Off by default: the build re-renders every chapter's diagrams, which is
    only fast enough for an automatic run when the corpus has no network-bound
    (mermaid) diagrams. Enable with EXTRACT_WISDOM_CREATE_EPUB=true.
    """
    if os.environ.get(_EPUB_ENV_VAR, "false").lower() not in ("true", "1", "yes"):
        return
    try:
        import markdown as md_lib  # type: ignore[import-untyped]  # ty: ignore[unresolved-import]
    except ImportError:
        return
    entries = _collect_entries(base_dir, reverse=True)
    if not entries:
        return
    try:
        _build_epub(base_dir, entries, base_dir / _EPUB_FILENAME, "Wisdom Library", md_lib)
    except Exception as exc:
        print(f"Warning: ePub generation failed: {exc}", file=sys.stderr)


def _find_ebook_convert() -> str | None:
    """Locate calibre's ebook-convert: PATH first, then the macOS app bundle."""
    exe = shutil.which("ebook-convert")
    if exe:
        return exe
    mac_bundled = "/Applications/calibre.app/Contents/MacOS/ebook-convert"
    if _is_mac() and os.access(mac_bundled, os.X_OK):
        return mac_bundled
    return None


def _convert_to_azw3(epub_path: Path, azw3_path: Path) -> bool:
    """Convert an ePub to native Kindle AZW3 via calibre. Returns success.

    AZW3 (Kindle Format 8) is the practical native format modern Kindles read;
    MOBI is deprecated by Amazon and KFX needs Kindle Previewer. Prints an
    install hint and returns False when calibre is unavailable.
    """
    exe = _find_ebook_convert()
    if not exe:
        print(
            "MISSING_DEPS: calibre ebook-convert (for --kindle AZW3 output)\n"
            "INSTALL: https://calibre-ebook.com/download (or `brew install --cask calibre`)\n"
            "ACTION: the .epub is complete and can be sent to a Kindle via Send to Kindle, "
            "which converts it server-side.",
            file=sys.stderr,
        )
        return False
    result = subprocess.run(
        [exe, str(epub_path), str(azw3_path)], capture_output=True, text=True,
    )
    if result.returncode != 0:
        tail = (result.stderr or result.stdout or "")[-500:]
        print(f"AZW3 conversion failed (exit {result.returncode}): {tail}", file=sys.stderr)
        return False
    return True


def cmd_epub(args: argparse.Namespace) -> None:
    """Bind the whole wisdom corpus into a single .epub ebook."""
    base_dir = Path(args.base_dir) if args.base_dir else detect_base_dir()
    if not base_dir.is_dir():
        print(f"Error: wisdom base directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        import markdown as md_lib  # type: ignore[import-untyped]  # ty: ignore[unresolved-import]
    except ImportError:
        print(
            "MISSING_DEPS: markdown\n"
            "INSTALL: run this script via `uv run` so the declared dependency is provided.",
            file=sys.stderr,
        )
        sys.exit(2)

    entries = _collect_entries(base_dir, reverse=True)
    if not entries:
        print(f"No analysis entries found under {base_dir}", file=sys.stderr)
        return

    output_file = Path(args.output) if args.output else base_dir / _EPUB_FILENAME
    title = args.title or "Wisdom Library"

    fallbacks = _build_epub(
        base_dir, entries, output_file, title, md_lib,
        include_descriptions=args.include_descriptions,
    )

    print(f"EPUB_PATH: {output_file}")
    print(f"CHAPTERS: {len(entries)}")
    _print_diagram_fallbacks(fallbacks)

    open_target = output_file
    if args.kindle:
        azw3_path = output_file.with_suffix(".azw3")
        if _convert_to_azw3(output_file, azw3_path):
            print(f"AZW3_PATH: {azw3_path}")
            open_target = azw3_path

    if args.open_after:
        _open_file(open_target)


# ---------------------------------------------------------------------------
# Backfill YouTube metadata and thumbnails
# ---------------------------------------------------------------------------

def _format_yaml_scalar(value: str) -> str:
    value = re.sub(r"\s*\n\s*", " ", value).strip()
    if any(c in value for c in (":", '"', "'", "#", "{", "}", "[", "]", ",")):
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return f'"{value}"'


def _format_yaml_list_item(item: str) -> str:
    item = item.strip()
    if re.fullmatch(r"[a-z0-9_\-]+", item):
        return item
    return _format_yaml_scalar(item)


def _format_yaml_value(value: str | list[str]) -> str:
    """Format a scalar or list for inclusion as a YAML value."""
    if isinstance(value, list):
        return "[" + ", ".join(_format_yaml_list_item(v) for v in value) + "]"
    return _format_yaml_scalar(value)


def _update_frontmatter(
    md_path: Path,
    updates: dict[str, Any],
    *,
    overwrite: bool = False,
) -> bool:
    """Add or update key-value pairs in YAML frontmatter.

    Values may be strings or list[str]; lists are written flow-style.
    By default, only adds keys that don't already exist. Pass overwrite=True
    to replace existing keys as well. Returns True on success, False if the
    file has no frontmatter.
    """
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end == -1:
        return False

    fm_block = text[4:end]
    fm_lines = fm_block.split("\n")

    # Collect existing top-level keys and their line ranges.
    existing_keys: set[str] = set()
    for line in fm_lines:
        m = re.match(r"^([a-z_]+)\s*:", line)
        if m:
            existing_keys.add(m.group(1))

    if overwrite:
        # Remove existing lines for keys we're overwriting (including continuation lines).
        keys_to_replace = set(updates.keys()) & existing_keys
        if keys_to_replace:
            filtered: list[str] = []
            skipping = False
            for line in fm_lines:
                m = re.match(r"^([a-z_]+)\s*:", line)
                if m:
                    # New key found - skip if it's one we're replacing, else stop skipping.
                    skipping = m.group(1) in keys_to_replace
                elif not skipping:
                    # Non-key line while not skipping - keep it.
                    pass
                # If skipping and line is not a new key, it's a continuation - skip it.
                if not skipping:
                    filtered.append(line)
            fm_lines = filtered
            existing_keys -= keys_to_replace

    new_lines: list[str] = []
    for key, value in updates.items():
        if key in existing_keys:
            continue
        new_lines.append(f"{key}: {_format_yaml_value(value)}")

    if not new_lines:
        return True

    new_fm = "\n".join(fm_lines).rstrip("\n") + "\n" + "\n".join(new_lines) + "\n"
    text = "---\n" + new_fm + "---" + text[end + 4:]
    md_path.write_text(text, encoding="utf-8")
    return True



def cmd_backfill(args: argparse.Namespace) -> None:
    """Backfill metadata and thumbnails for existing wisdom entries."""
    base_dir = detect_base_dir()

    md_files: list[Path] = []

    if args.all:
        for md_file in sorted(base_dir.glob("*/*analysis.md")):
            fm = _parse_frontmatter(md_file)
            if fm and fm.get("source_type") in ("youtube", "web") and _fm_sources(fm):
                md_files.append(md_file)
    elif args.directory:
        target_dir = Path(args.directory)
        if not target_dir.is_dir():
            target_dir = base_dir / args.directory
        if not target_dir.is_dir():
            print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
            sys.exit(1)
        found = list(target_dir.glob("*analysis.md"))
        if not found:
            print(f"Error: No analysis.md found in {target_dir}", file=sys.stderr)
            sys.exit(1)
        md_files.append(found[0])
    else:
        print("Error: Specify a directory or --all", file=sys.stderr)
        sys.exit(1)

    from concurrent.futures import ThreadPoolExecutor, as_completed

    force = args.force
    updated = 0
    skipped = 0

    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(_enrich_entry, md, overwrite=force): md for md in md_files}
        for future in as_completed(futures):
            try:
                if future.result():
                    updated += 1
                else:
                    skipped += 1
            except Exception as exc:
                print(f"Warning: {futures[future].parent.name}: {exc}", file=sys.stderr)
                skipped += 1

    print(f"Backfill complete: {updated} updated, {skipped} skipped")

    # Regenerate index.
    try:
        _regenerate_index(base_dir, force=True)
    except Exception as exc:
        print(f"Warning: Index regeneration failed: {exc}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Search subcommand
# ---------------------------------------------------------------------------

def _resolve_search_db(base_dir: Path) -> Path:
    return base_dir / _SEARCH_DB_NAME


def _format_fts_query(query: str) -> str:
    """Wrap raw user input as an FTS5 MATCH expression.

    Splits on whitespace, drops tokens with FTS5-special characters that
    can't be quoted safely, and quotes the rest as phrase terms joined
    with implicit AND. A bare star at the end of a token survives so
    users can still do prefix matches (e.g. ``rlhf*``).
    """
    raw = query.strip()
    if not raw:
        return ""
    parts: list[str] = []
    for token in raw.split():
        prefix = token.endswith("*")
        if prefix:
            token = token[:-1]
        if not token:
            continue
        # Strip embedded double quotes; everything else is fair game inside "...".
        cleaned = token.replace('"', "")
        if not cleaned:
            continue
        parts.append(f'"{cleaned}"' + ("*" if prefix else ""))
    return " ".join(parts)


def cmd_search(args: argparse.Namespace) -> None:
    """Query the FTS5 wisdom search database."""
    base_dir = detect_base_dir()
    db_path = _resolve_search_db(base_dir)
    if not db_path.is_file():
        print(
            f"Error: Search index not found at {db_path}.\n"
            f"Run: wisdom.py index",
            file=sys.stderr,
        )
        sys.exit(1)

    match_expr = _format_fts_query(args.query)
    if not match_expr:
        print("Error: empty search query", file=sys.stderr)
        sys.exit(1)

    where = ["wisdom MATCH ?"]
    params: list[Any] = [match_expr]
    if args.type:
        where.append("source_type = ?")
        params.append(args.type)
    params.append(args.top)

    sql = (
        "SELECT dir_path, title, author, source_type, date, tags, pdf_path, "
        "md_path, snippet(wisdom, 5, '<<', '>>', '...', 24) AS snip, "
        "bm25(wisdom) AS score "
        "FROM wisdom WHERE " + " AND ".join(where) + " "
        "ORDER BY bm25(wisdom) LIMIT ?"
    )

    try:
        conn = sqlite3.connect(db_path)
        try:
            rows = conn.execute(sql, params).fetchall()
        finally:
            conn.close()
    except sqlite3.Error as exc:
        print(f"Error: search failed: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps([
            {
                "rank": i + 1,
                # bm25 returns negative scores; invert so larger = better.
                "score": round(-r[9], 4),
                "dir_path": r[0],
                "title": r[1],
                "author": r[2],
                "source_type": r[3],
                "date": r[4],
                "tags": r[5].split() if r[5] else [],
                "pdf_path": r[6],
                "md_path": r[7],
                "snippet": r[8],
            }
            for i, r in enumerate(rows)
        ], ensure_ascii=False, indent=2))
        return

    if not rows:
        print("No matches.")
        return

    for i, r in enumerate(rows):
        score = -r[9]
        tags = r[5] or ""
        print(f"\n[{i+1}] {r[1]}")
        meta_bits = [r[3], r[2], r[4]]
        meta = "  ".join(b for b in meta_bits if b)
        if meta:
            print(f"     {meta}")
        if tags:
            print(f"     tags: {tags}")
        print(f"     {r[0]}/")
        print(f"     score: {score:.3f}")
        if r[8]:
            print(f"     {r[8]}")


# ---------------------------------------------------------------------------
# Related subcommand
# ---------------------------------------------------------------------------

def _resolve_entry_dirpath(base_dir: Path, entry: str) -> str | None:
    """Map a CLI ``entry`` argument to its dir_path inside the wisdom base.

    Accepts a bare directory name, an absolute path, or a path to an
    analysis.md file. Returns None when no matching directory exists.
    """
    candidate = Path(entry)
    if candidate.is_file() and candidate.suffix == ".md":
        candidate = candidate.parent
    if candidate.is_absolute():
        try:
            rel = candidate.resolve().relative_to(base_dir.resolve())
        except ValueError:
            return None
        return rel.parts[0] if rel.parts else None
    if (base_dir / candidate).is_dir():
        return candidate.name
    # Fall through to a name-only match.
    if any(p.name == entry and p.is_dir() for p in base_dir.glob("*")):
        return entry
    return None


def cmd_related(args: argparse.Namespace) -> None:
    """Print precomputed related entries for a given wisdom entry."""
    base_dir = detect_base_dir()
    cache_path = base_dir / _RELATED_CACHE_NAME
    if not cache_path.is_file():
        print(
            f"Error: Related cache not found at {cache_path}.\n"
            f"Run: wisdom.py index",
            file=sys.stderr,
        )
        sys.exit(1)

    dir_path = _resolve_entry_dirpath(base_dir, args.entry)
    if not dir_path:
        print(f"Error: Could not resolve entry '{args.entry}' inside {base_dir}", file=sys.stderr)
        sys.exit(1)

    try:
        cache = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error: could not read related cache: {exc}", file=sys.stderr)
        sys.exit(1)

    items = cache.get(dir_path, [])
    if args.by != "hybrid":
        items = [it for it in items if it.get("why") in (args.by, "both")]
    items = items[: args.top]

    if args.json:
        print(json.dumps(
            {"entry": dir_path, "by": args.by, "related": items},
            ensure_ascii=False, indent=2,
        ))
        return

    if not items:
        print(f"No related entries found for {dir_path}.")
        return

    print(f"Related to: {dir_path}")
    for i, it in enumerate(items, 1):
        why = it.get("why", "")
        shared = it.get("shared_tags", []) or []
        print(f"\n[{i}] {it.get('title', '')}")
        print(f"     {it.get('dir_path', '')}/")
        bits = [f"why: {why}"]
        if shared:
            bits.append("shared: " + ", ".join(shared))
        if it.get("source_type"):
            bits.append(it["source_type"])
        print("     " + "  ".join(bits))


# ---------------------------------------------------------------------------
# Tags subcommand (list, --warnings, --merge)
# ---------------------------------------------------------------------------

def _collect_tag_freq(base_dir: Path) -> tuple[dict[str, int], list[Path]]:
    """Walk the corpus and tally tag occurrences.

    Tags are deduplicated within each entry so frequency reflects the
    number of entries that mention a tag, not the number of mentions.
    """
    freq: dict[str, int] = {}
    files: list[Path] = []
    for md_file in sorted(base_dir.glob("*/*analysis.md")):
        fm = _parse_frontmatter(md_file)
        if not fm:
            continue
        files.append(md_file)
        seen_in_entry: set[str] = set()
        for t in _fm_list(fm, "tags"):
            t_norm = t.strip().lower()
            if not t_norm or t_norm in seen_in_entry:
                continue
            seen_in_entry.add(t_norm)
            freq[t_norm] = freq.get(t_norm, 0) + 1
    return freq, files


def _replace_tags_in_file(
    md_path: Path, source_tags: set[str], target: str,
) -> bool:
    """Rewrite the tags list in ``md_path``, replacing any ``source_tags``
    members with ``target`` and deduplicating. Returns True if changed.
    """
    fm = _parse_frontmatter(md_path)
    if not fm:
        return False
    current = _fm_list(fm, "tags")
    if not current:
        return False
    rewritten: list[str] = []
    seen: set[str] = set()
    changed = False
    for tag in current:
        norm = tag.strip().lower()
        if norm in source_tags:
            mapped = target
            changed = True
        else:
            mapped = norm
        if mapped and mapped not in seen:
            seen.add(mapped)
            rewritten.append(mapped)
    if not changed and rewritten == [t.strip().lower() for t in current]:
        return False
    _update_frontmatter(md_path, {"tags": rewritten}, overwrite=True)
    return True


def cmd_tags(args: argparse.Namespace) -> None:
    """List, warn about, or merge tags across the corpus."""
    base_dir = detect_base_dir()
    if not base_dir.is_dir():
        print(f"Error: wisdom base directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)

    if args.merge:
        if not args.target:
            print("Error: --merge requires a target tag positional argument", file=sys.stderr)
            sys.exit(1)
        sources = {
            s.strip().lower() for s in args.merge.split(",") if s.strip()
        }
        if not sources:
            print("Error: --merge value is empty", file=sys.stderr)
            sys.exit(1)
        target = args.target.strip().lower()
        _, files = _collect_tag_freq(base_dir)
        changed = 0
        for md in files:
            try:
                if _replace_tags_in_file(md, sources, target):
                    changed += 1
            except Exception as exc:
                print(f"Warning: could not rewrite {md.parent.name}: {exc}", file=sys.stderr)
        print(f"Tag merge complete: {changed} file(s) updated. "
              f"Run `wisdom.py index` to refresh search and related data.")
        return

    freq, _ = _collect_tag_freq(base_dir)

    if args.warnings:
        sprawl = _detect_tag_sprawl(freq)
        if not sprawl:
            print("No tag sprawl detected.")
            return
        if args.json:
            print(json.dumps([
                {"tag": hi, "count": hc, "near": lo, "near_count": lc}
                for hi, hc, lo, lc in sprawl
            ], ensure_ascii=False, indent=2))
            return
        for hi, hc, lo, lc in sprawl:
            print(f"{hi} ({hc}) ~ {lo} ({lc})")
        return

    if args.json:
        print(json.dumps(
            sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])),
            ensure_ascii=False, indent=2,
        ))
        return

    if not freq:
        print("No tags found across the corpus.")
        return

    for tag, count in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0])):
        print(f"{count:>4}\t{tag}")


# A top-level frontmatter key naming a source: ``source``, ``source_alt``,
# ``companion_source`` etc. ``source_type`` and the ``sources`` list target are
# excluded by the caller so they are not folded into themselves.
_SOURCE_KEY_RE = re.compile(r"^([a-z_]*source[a-z_]*)[ \t]*:[ \t]*(.*)$")


def _migrated_frontmatter(fm_block: str) -> str:
    """Return the frontmatter block with all source metadata consolidated into a
    single ``sources:`` list, one URL per item.

    Folds the legacy scalar ``source:`` line, any bespoke secondary key such as
    ``source_alt`` or ``companion_source``, and an existing block-style
    ``sources:`` list, splitting any value that crammed several URLs into one.
    URLs are de-duplicated in first-seen order. Returns the block unchanged when
    no source metadata is present. ``source_type`` is never folded.
    """
    lines = fm_block.split("\n")
    insert_at: int | None = None
    drop: set[int] = set()
    urls: list[str] = []

    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r"^sources:[ \t]*$", line):
            if insert_at is None:
                insert_at = i
            drop.add(i)
            j = i + 1
            while j < len(lines) and re.match(r"^[ \t]+-[ \t]+", lines[j]):
                item = _unquote_yaml_scalar(re.sub(r"^[ \t]+-[ \t]+", "", lines[j]).strip())
                urls.extend(_split_source_value(item))
                drop.add(j)
                j += 1
            i = j
            continue
        m = _SOURCE_KEY_RE.match(line)
        if m and m.group(1) not in ("source_type", "sources"):
            if insert_at is None:
                insert_at = i
            drop.add(i)
            urls.extend(_split_source_value(_unquote_yaml_scalar(m.group(2).strip())))
        i += 1

    if insert_at is None or not urls:
        return fm_block

    seen: set[str] = set()
    unique = [u for u in urls if not (u in seen or seen.add(u))]
    block = ["sources:"] + [f'  - "{u}"' for u in unique]

    kept = [l for k, l in enumerate(lines) if k not in drop]
    insert_idx = sum(1 for k in range(insert_at) if k not in drop)
    return "\n".join(kept[:insert_idx] + block + kept[insert_idx:])


def cmd_migrate_sources(args: argparse.Namespace) -> None:
    """Normalise source metadata to the ``sources:`` list and relabel the body
    ``**Source**:`` line to ``**Sources**:``.

    Migrates the legacy scalar ``source:`` field, folds bespoke secondary keys
    (``source_alt``, ``companion_source``, ...) into the list, and splits any
    value that crammed several URLs into one. Idempotent: a file already in
    canonical form produces no change and is skipped. Operates on raw text so
    all other frontmatter, quoting, and formatting are preserved.
    """
    base_dir = Path(args.base_dir) if args.base_dir else detect_base_dir()
    if not base_dir.is_dir():
        print(f"Error: Base directory not found: {base_dir}", file=sys.stderr)
        sys.exit(1)

    md_files = sorted(base_dir.glob("*/*analysis.md"))
    if not md_files:
        print(f"No analysis markdown files found under {base_dir}", file=sys.stderr)
        return

    # ``**Source**:`` will not match an already-relabelled ``**Sources**:`` line,
    # so the body rewrite is safe to re-run.
    body_re = re.compile(r"^\*\*Source\*\*:", re.MULTILINE)

    migrated = 0
    skipped = 0
    for md_file in md_files:
        text = md_file.read_text(encoding="utf-8")
        if not text.startswith("---"):
            skipped += 1
            continue
        end = text.find("\n---", 3)
        if end == -1:
            skipped += 1
            continue
        prefix, fm_block, rest = text[:4], text[4:end], text[end:]

        new_fm = _migrated_frontmatter(fm_block)
        new_rest = body_re.sub("**Sources**:", rest)

        if new_fm == fm_block and new_rest == rest:
            skipped += 1
            continue

        if args.dry_run:
            print(f"[dry-run] would migrate: {md_file.parent.name}/{md_file.name}")
        else:
            md_file.write_text(prefix + new_fm + new_rest, encoding="utf-8")
        migrated += 1

    verb = "Would migrate" if args.dry_run else "Migrated"
    print(f"{verb} {migrated} file(s); skipped {skipped} "
          "(already canonical or no frontmatter).")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract-wisdom helper tools",
        prog="wisdom.py",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # transcript
    p_transcript = sub.add_parser("transcript", help="Download YouTube transcript")
    p_transcript.add_argument("url", help="YouTube video URL")

    # output-dir
    sub.add_parser("output-dir", help="Print resolved output directory")

    # create-dir
    p_create_dir = sub.add_parser("create-dir", help="Create a new date-prefixed directory for non-YouTube sources")
    p_create_dir.add_argument("description", help="Short description (1-6 words, e.g. 'Sam Altman Blog Post')")

    # rename
    p_rename = sub.add_parser("rename", help="Rename download directory with date prefix")
    p_rename.add_argument("directory", help="Directory to rename (e.g. the video ID directory)")
    p_rename.add_argument("description", help="Short description (1-6 words, e.g. 'Demis Hassabis Interview')")

    # format
    p_format = sub.add_parser("format", help="Format markdown with prettier")
    p_format.add_argument("--check", action="store_true", help="Check formatting without writing")
    p_format.add_argument("files", nargs="+", help="Markdown files to format")

    # pdf
    p_pdf = sub.add_parser("pdf", help="Render markdown to styled PDF")
    p_pdf.add_argument("--css", default=None, help="Custom CSS stylesheet")
    p_pdf.add_argument("--open", action="store_true", dest="open_after", help="Open PDF after rendering")
    p_pdf.add_argument("--no-stamp", action="store_true", dest="no_stamp",
                       help="Skip stamping today's date as the analysis date")
    p_pdf.add_argument("input_file", nargs="?", default=None, help="Markdown file to render")
    p_pdf.add_argument("output_file", nargs="?", default=None, help="Output PDF path")

    p_regen = sub.add_parser("regenerate-pdfs",
                             help="Re-render every wisdom analysis PDF under the base directory")
    p_regen.add_argument("base_dir", nargs="?", default=None,
                         help="Wisdom base directory (default: auto-detect)")
    p_regen.add_argument("--css", default=None, help="Custom CSS stylesheet")
    p_regen.add_argument("--stamp", action="store_true",
                         help="Stamp today's date as the analysis date "
                              "(default: leave existing dates untouched)")
    p_regen.add_argument("--workers", type=int, default=None,
                         help="Number of parallel worker processes "
                              "(default: max(1, cpu_count - 2); use 1 for sequential)")

    p_index = sub.add_parser("index", help="Regenerate the wisdom library index.html")
    p_index.add_argument("base_dir", nargs="?", default=None, help="Wisdom base directory (default: auto-detect)")

    # epub
    p_epub = sub.add_parser("epub", help="Bind the whole corpus into a single .epub ebook")
    p_epub.add_argument("base_dir", nargs="?", default=None, help="Wisdom base directory (default: auto-detect)")
    p_epub.add_argument("--output", default=None, help=f"Output path (default: <base_dir>/{_EPUB_FILENAME})")
    p_epub.add_argument("--title", default=None, help="Book title (default: 'Wisdom Library')")
    p_epub.add_argument("--descriptions", action="store_true", dest="include_descriptions",
                        help="Include the description preview paragraph under each index entry")
    p_epub.add_argument("--kindle", action="store_true",
                        help="Also emit a native Kindle .azw3 via calibre (if installed)")
    p_epub.add_argument("--open", action="store_true", dest="open_after", help="Open the ebook after building")

    # migrate-sources
    p_migrate = sub.add_parser("migrate-sources",
                               help="Migrate legacy scalar source: to the sources: list")
    p_migrate.add_argument("base_dir", nargs="?", default=None,
                           help="Wisdom base directory (default: auto-detect)")
    p_migrate.add_argument("--dry-run", action="store_true",
                           help="Report what would change without writing")

    # backfill
    p_backfill = sub.add_parser("backfill", help="Backfill YouTube metadata and thumbnails")
    p_backfill.add_argument("directory", nargs="?", default=None, help="Specific entry directory to backfill")
    p_backfill.add_argument("--all", action="store_true", help="Backfill all YouTube entries")
    p_backfill.add_argument("--force", action="store_true", help="Re-fetch metadata and overwrite existing fields")

    # search
    p_search = sub.add_parser("search", help="Search the wisdom corpus via FTS5/BM25")
    p_search.add_argument("query", help="Search query (whitespace-separated terms; trailing * for prefix match)")
    p_search.add_argument("--top", type=int, default=10, help="Maximum results to return (default 10)")
    p_search.add_argument("--type", choices=("youtube", "web", "text"), default=None,
                          help="Restrict to a single source type")
    p_search.add_argument("--json", action="store_true", help="Output JSON instead of text")

    # related
    p_related = sub.add_parser("related", help="Show entries related to a given wisdom entry")
    p_related.add_argument("entry", help="Entry directory name, full path, or analysis.md path")
    p_related.add_argument("--top", type=int, default=8, help="Maximum related entries (default 8)")
    p_related.add_argument("--by", choices=("tags", "content", "hybrid"), default="hybrid",
                           help="Filter results by signal source (default hybrid)")
    p_related.add_argument("--json", action="store_true", help="Output JSON instead of text")

    # tags
    p_tags = sub.add_parser("tags", help="List, warn about, or merge tags across the corpus")
    p_tags.add_argument("target", nargs="?", default=None,
                        help="Target tag for --merge (positional after --merge value)")
    p_tags.add_argument("--warnings", action="store_true",
                        help="Print near-duplicate tag pairs flagged for review")
    p_tags.add_argument("--merge", default=None, metavar="OLD[,OLD2]",
                        help="Comma-separated tags to rewrite to TARGET across all entries")
    p_tags.add_argument("--json", action="store_true", help="Output JSON instead of text")

    args = parser.parse_args()

    dispatch = {
        "transcript": cmd_transcript,
        "output-dir": cmd_output_dir,
        "create-dir": cmd_create_dir,
        "rename": cmd_rename,
        "format": cmd_format,
        "pdf": cmd_pdf,
        "regenerate-pdfs": cmd_regenerate_pdfs,
        "index": cmd_index,
        "epub": cmd_epub,
        "migrate-sources": cmd_migrate_sources,
        "backfill": cmd_backfill,
        "search": cmd_search,
        "related": cmd_related,
        "tags": cmd_tags,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
