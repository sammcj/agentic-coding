#!/usr/bin/env python3
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "yt-dlp",
#   "weasyprint",
#   "markdown",
#   "graphviz",
#   "tzdata",
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
import base64
import fcntl
import html as html_mod
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
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
_INDEX_SCHEMA_VERSION = 2
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


def _parse_frontmatter(md_path: Path) -> dict[str, str] | None:
    """Parse YAML frontmatter from a markdown file.

    Handles simple key: value pairs, quoted strings, and YAML folded
    block scalars (>). Returns None if no frontmatter is found.
    """
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    if end == -1:
        return None
    fm_block = text[4:end]

    result: dict[str, str] = {}
    current_key: str | None = None
    value_lines: list[str] = []

    for line in fm_block.split("\n"):
        key_match = re.match(r"^([a-z_]+)\s*:\s*(.*)", line)
        if key_match and not line[0].isspace():
            if current_key is not None:
                result[current_key] = " ".join(value_lines).strip()
            current_key = key_match.group(1)
            value = key_match.group(2).strip()
            if value in (">", "|", ">-", "|-"):
                value_lines = []
            else:
                if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                    value = value[1:-1].replace('\\"', '"').replace("\\'", "'")
                value_lines = [value] if value else []
        elif current_key is not None and (line.startswith("  ") or line.startswith("\t")):
            value_lines.append(line.strip())

    if current_key is not None:
        result[current_key] = " ".join(value_lines).strip()

    return result if result else None


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
    md_text = _strip_frontmatter(md_text)
    md_text = _normalise_list_markdown(md_text)
    html_body = md_lib.markdown(md_text, extensions=MD_EXTENSIONS)
    html_body, diagram_fallbacks = _render_diagrams(html_body)

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

    entries: list[dict[str, str | int]] = []
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

        entries.append({
            "title": fm.get("title", dir_name),
            "source": fm.get("source", ""),
            "source_type": fm.get("source_type", ""),
            "author": fm.get("author", ""),
            "date": fm.get("date", ""),
            "description": fm.get("description", ""),
            "word_count": word_count,
            "reading_time": reading_time,
            "dir_path": dir_name,
            "pdf_path": f"{dir_name}/{pdf_file.name}" if pdf_file.is_file() else "",
            "md_path": f"{dir_name}/{md_file.name}",
        })

    if not entries:
        return

    template = _INDEX_TEMPLATE.read_text(encoding="utf-8")
    entries_json = json.dumps(entries, indent=2, ensure_ascii=False)
    # Escape </ sequences to prevent breaking out of the <script> tag.
    entries_json = entries_json.replace("</", r"<\/")
    gen_date = datetime.now(tz=_local_tz()).date().isoformat()

    html = template.replace("$ENTRIES_JSON$", entries_json)
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

    p_index = sub.add_parser("index", help="Regenerate the wisdom library index.html")
    p_index.add_argument("base_dir", nargs="?", default=None, help="Wisdom base directory (default: auto-detect)")

    args = parser.parse_args()

    dispatch = {
        "transcript": cmd_transcript,
        "output-dir": cmd_output_dir,
        "rename": cmd_rename,
        "format": cmd_format,
        "pdf": cmd_pdf,
        "index": cmd_index,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
