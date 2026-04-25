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
    pdf [--css F] [--open] [file]   Render markdown to styled PDF
    index [base_dir]                Regenerate the wisdom library index.html
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
import urllib.request
from collections import Counter
from datetime import datetime
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
    if not fm or not fm.get("source"):
        return False

    source_type = fm.get("source_type", "")
    entry_dir = md_path.parent
    has_thumbnail = (entry_dir / "thumbnail.jpg").is_file()
    updates: dict[str, str] = {}

    if source_type == "youtube":
        if not overwrite and has_thumbnail and fm.get("youtube_channel"):
            return False
        metadata = _extract_youtube_metadata(fm["source"])
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
        metadata = _fetch_web_metadata(fm["source"])
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


def _render_graphviz(code: str) -> bytes | None:
    """Render a Graphviz DOT string to SVG bytes. Returns None if unavailable."""
    try:
        import graphviz  # type: ignore[import-untyped]
    except ImportError:
        return None
    try:
        return graphviz.Source(code).pipe(format="svg")
    except Exception:
        return None


def _svg_dimensions(svg: bytes) -> tuple[float, float] | None:
    """Extract width and height (in pt) from an SVG's attributes."""
    header = svg[:1024].decode(errors="replace")
    m = re.search(r'<svg[^>]*\bwidth="([\d.]+)pt"[^>]*\bheight="([\d.]+)pt"', header)
    if m:
        return float(m.group(1)), float(m.group(2))
    return None


def _render_mermaid(code: str) -> tuple[bytes, str] | None:
    """Render a Mermaid diagram via the mermaid.ink public API.

    Returns (image_bytes, mime_type) or None on failure.  Uses the /img/
    endpoint which returns a rasterised JPEG - the /svg/ endpoint uses
    foreignObject for text labels which WeasyPrint cannot render.
    """
    try:
        payload = base64.urlsafe_b64encode(code.encode()).decode()
        url = _MERMAID_INK_URL + payload
        req = urllib.request.Request(url, headers={"User-Agent": "wisdom-pdf/1.0"})
        with urllib.request.urlopen(req, timeout=_MERMAID_TIMEOUT) as resp:
            data: bytes = resp.read()
            content_type = resp.headers.get("Content-Type", "image/jpeg")
            mime = content_type.split(";")[0].strip()
            return data, mime
    except Exception:
        return None


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


def _render_diagrams(html_body: str) -> tuple[str, dict[str, int]]:
    """Find diagram code blocks in HTML and replace them with rendered images.

    Returns (modified_html, fallback_counts) where fallback_counts maps
    diagram language names to the number of blocks that failed to render.
    """
    fallbacks: dict[str, int] = {}

    def _replace(match: re.Match[str]) -> str:
        lang = match.group(1)
        code = html_mod.unescape(match.group(2))

        if lang in ("graphviz", "dot"):
            svg = _render_graphviz(_apply_graphviz_theme(code))
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


def cmd_pdf(args: argparse.Namespace) -> None:
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

    # Stamp the analysis date (always today's local date, script-controlled).
    _stamp_analysis_date(input_file)

    # Enrich entry with metadata and thumbnail if not already present.
    _enrich_entry(input_file)

    # Convert markdown to HTML
    md_text = input_file.read_text(encoding="utf-8")
    md_text = _strip_frontmatter(md_text)
    md_text = _normalise_list_markdown(md_text)
    html_body = md_lib.markdown(md_text, extensions=MD_EXTENSIONS)
    html_body, diagram_fallbacks = _render_diagrams(html_body)

    # Append thumbnail at end of PDF if available (unless disabled via frontmatter).
    fm = _parse_frontmatter(input_file)
    input_dir = input_file.resolve().parent
    thumb_path = input_dir / "thumbnail.jpg"
    if thumb_path.is_file() and (not fm or not fm.get("thumbnail", "").startswith("false")):
        try:
            thumb_data = thumb_path.read_bytes()
            thumb_b64 = base64.b64encode(thumb_data).decode()
            html_body += (
                '<div style="margin-top:2em; padding-top:1em; '
                'border-top:1px solid #e8e6dc; text-align:center;">'
                f'<img src="data:image/jpeg;base64,{thumb_b64}" '
                'alt="Source thumbnail" '
                'style="max-width:60%; border-radius:6px; margin:0.5em auto;" />'
                '<p style="font-family:Helvetica Neue,sans-serif; '
                'font-size:0.8em; color:#b0aea5; margin-top:0.3em;">'
                'Source thumbnail</p>'
                '</div>'
            )
        except Exception:
            pass

    # Load and populate the HTML5 template
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

    if args.open_after:
        _open_file(output_file)

    print(f"PDF_PATH: {output_file}")

    # Report diagram rendering fallbacks so the calling agent can act on them
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

    # Regenerate the wisdom library index (non-fatal on failure).
    try:
        _regenerate_index(detect_base_dir())
    except Exception as exc:
        print(f"Warning: Index generation failed: {exc}", file=sys.stderr)


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

    entries: list[dict[str, Any]] = []
    for md_file in sorted(base_dir.glob("*/*analysis.md"), reverse=True):
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
            "source": _fm_str(fm, "source"),
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


def cmd_index(args: argparse.Namespace) -> None:
    """Regenerate the wisdom library index.html."""
    base_dir = Path(args.base_dir) if args.base_dir else detect_base_dir()
    _regenerate_index(base_dir, force=True)


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
            if fm and fm.get("source_type") in ("youtube", "web") and fm.get("source"):
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
    p_pdf.add_argument("input_file", nargs="?", default=None, help="Markdown file to render")
    p_pdf.add_argument("output_file", nargs="?", default=None, help="Output PDF path")

    p_index = sub.add_parser("index", help="Regenerate the wisdom library index.html")
    p_index.add_argument("base_dir", nargs="?", default=None, help="Wisdom base directory (default: auto-detect)")

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
        "index": cmd_index,
        "backfill": cmd_backfill,
        "search": cmd_search,
        "related": cmd_related,
        "tags": cmd_tags,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
