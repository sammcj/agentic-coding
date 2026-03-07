#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "yt-dlp[default]",
#   "weasyprint",
#   "markdown",
# ]
# ///
"""Extract-wisdom helper tools.

Single script replacing the individual bash scripts for transcript download,
markdown formatting, and PDF rendering. Run via: uv run wisdom.py <subcommand>

Subcommands:
    transcript <url>                Download YouTube transcript
    output-dir                      Print the resolved output directory
    rename <dir> <description>      Rename directory with date prefix
    format [--check] <files...>     Format markdown with prettier
    pdf [--css F] [--open] [file]   Render markdown to styled PDF
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path

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


def _extract_video_id(url: str) -> str:
    """Extract video ID via yt-dlp."""
    from yt_dlp import YoutubeDL

    with YoutubeDL({"quiet": True, "no_warnings": True, "logger": _SilentLogger()}) as ydl:  # type: ignore[arg-type]
        info = ydl.extract_info(url, download=False)
        vid = info.get("id", "") if info else ""
    if not vid:
        print("Error: Could not extract video ID from URL", file=sys.stderr)
        sys.exit(1)
    return vid


def cmd_transcript(args: argparse.Namespace) -> None:
    url: str = args.url
    base_dir = detect_base_dir()

    video_id = _extract_video_id(url)

    video_dir = base_dir / video_id
    video_dir.mkdir(parents=True, exist_ok=True)

    # Try with cookies first, then without
    download_ok = _download_transcript(url, video_dir, use_cookies=True)
    if not download_ok:
        download_ok = _download_transcript(url, video_dir, use_cookies=False)

    json3_files = list(video_dir.glob("*.json3"))
    if not download_ok or not json3_files:
        print("Error: No subtitle files were downloaded", file=sys.stderr)
        print(f"Check: {video_dir}", file=sys.stderr)
        print("", file=sys.stderr)
        print("This may be due to:", file=sys.stderr)
        print("  - Age-restricted video requiring login", file=sys.stderr)
        print("  - Video has no available subtitles", file=sys.stderr)
        print("  - Video is private or unlisted", file=sys.stderr)
        print("  - Rate limiting from YouTube", file=sys.stderr)
        sys.exit(1)

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

    transcript_file = transcript_files[0]
    print(f"TRANSCRIPT_PATH: {transcript_file}")
    print(f"OUTPUT_DIR: {video_dir}")
    print(f"NEXT_STEP: uv run <skill-dir>/scripts/wisdom.py rename \"{video_dir}\" \"<Short-Description>\"")


# ---------------------------------------------------------------------------
# Output directory
# ---------------------------------------------------------------------------

def cmd_output_dir(_args: argparse.Namespace) -> None:  # noqa: ARG001
    print(detect_base_dir())


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


def cmd_rename(args: argparse.Namespace) -> None:
    source = Path(args.directory)
    if not source.is_dir():
        print(f"Error: Directory not found: {source}", file=sys.stderr)
        sys.exit(1)

    today = date.today().isoformat()
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
# PDF rendering
# ---------------------------------------------------------------------------

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


def _open_file(path: Path) -> None:
    """Open a file with the OS default viewer. Fails silently if unavailable."""
    try:
        if _is_mac():
            subprocess.run(["open", str(path)], stderr=subprocess.DEVNULL)
        elif shutil.which("xdg-open"):
            subprocess.run(["xdg-open", str(path)], stderr=subprocess.DEVNULL)
    except OSError:
        pass


def _ensure_homebrew_lib_path() -> None:
    """Ensure Homebrew shared libraries are discoverable on macOS.

    uv run creates isolated environments that may not inherit
    DYLD_FALLBACK_LIBRARY_PATH, causing ctypes to fail when
    weasyprint tries to load libgobject/libpango/libcairo.
    """
    if not _is_mac():
        return
    brew_lib = Path("/opt/homebrew/lib")
    if not brew_lib.is_dir():
        return
    key = "DYLD_FALLBACK_LIBRARY_PATH"
    current = os.environ.get(key, "")
    if str(brew_lib) not in current:
        os.environ[key] = f"{brew_lib}:{current}" if current else str(brew_lib)


def cmd_pdf(args: argparse.Namespace) -> None:
    _ensure_homebrew_lib_path()
    try:
        import markdown as md_lib
        from weasyprint import HTML  # type: ignore[import-untyped]
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

    # Convert markdown to HTML
    md_text = input_file.read_text(encoding="utf-8")
    md_text = _normalise_list_markdown(md_text)
    html_body = md_lib.markdown(md_text, extensions=MD_EXTENSIONS)

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

    args = parser.parse_args()

    dispatch = {
        "transcript": cmd_transcript,
        "output-dir": cmd_output_dir,
        "rename": cmd_rename,
        "format": cmd_format,
        "pdf": cmd_pdf,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
