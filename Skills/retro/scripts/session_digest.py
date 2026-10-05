#!/usr/bin/env python3
"""Digest a Claude Code session transcript into a compact timeline of prompts, tool calls, errors and costly results."""
import argparse
import collections
import datetime
import json
import re
import sys
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
# Results above this size are flagged as expensive; ~10k chars is roughly 2.5k tokens.
BIG_RESULT_CHARS = 10_000
SNIP = 160
# Claude Code moves large outputs to tool-results/ and leaves a stub stating the original size.
PERSISTED = re.compile(r"Output too large \(([\d.]+)(KB|MB)\)")


def records(path: Path):
    for line in path.open(errors="replace"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue  # live sessions can end on a half-written line
        if isinstance(d, dict):
            yield d


def find_transcript(ref: str) -> Path:
    p = Path(ref).expanduser()
    if p.is_file():
        return p
    hits = sorted(PROJECTS.glob(f"*/{ref}*.jsonl"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not hits:
        sys.exit(f"No transcript matching '{ref}' under {PROJECTS}")
    return hits[0]


def session_label(path: Path) -> str:
    title = prompt = ""
    for d in records(path):
        t = d.get("type")
        if t == "ai-title":
            title = d.get("aiTitle") or title
        elif t == "user" and not prompt and not d.get("isMeta"):
            content = (d.get("message") or {}).get("content")
            if isinstance(content, str) and not content.startswith("<"):
                prompt = content
    return snip(title or prompt, 90)


def list_recent(n: int, project: str | None) -> None:
    # Project dirs replace every non-alphanumeric path character with '-'.
    pattern = f"*{re.sub(r'[^A-Za-z0-9]', '-', project)}*/*.jsonl" if project else "*/*.jsonl"
    files = sorted(PROJECTS.glob(pattern), key=lambda f: f.stat().st_mtime, reverse=True)[:n]
    for f in files:
        when = datetime.datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
        print(f"{f.stem}  {when}  {f.parent.name}  {f.stat().st_size // 1024}KB  {session_label(f)}")


def snip(text, n=SNIP) -> str:
    s = " ".join(str(text).split())
    return s if len(s) <= n else s[: n - 3] + "..."


def ends(text, n=SNIP) -> str:
    """Head and tail: hook blocks explain themselves up front, shell failures at the end."""
    s = " ".join(str(text).split())
    return s if len(s) <= n else f"{s[: n // 2]} ... {s[-n // 2 :]}"


def result_text(content) -> str:
    if isinstance(content, list):
        return " ".join(b.get("text", "") for b in content if isinstance(b, dict))
    return str(content or "")


def result_size(text: str) -> int:
    m = PERSISTED.search(text[:300])
    if m:
        return int(float(m.group(1)) * (1024 if m.group(2) == "KB" else 1024 * 1024))
    return len(text)


def tool_summary(name: str, inp: dict) -> str:
    for key in ("command", "file_path", "pattern", "query", "skill", "description", "prompt", "url", "code", "queries", "commands"):
        if key in inp:
            return f"{name}({snip(inp[key], 120)})"
    return f"{name}({snip(json.dumps(inp), 120)})" if inp else name


def digest(path: Path, full: bool) -> None:
    calls = {}
    counts = collections.Counter()
    commands = collections.Counter()
    errors, big = [], []
    n = 0
    print(f"# {path}\n")
    for d in records(path):
        t = d.get("type")
        if t == "attachment":
            a = d.get("attachment") or {}
            if a.get("type") in ("hook_blocking_error", "hook_non_blocking_error"):
                idx, summary = calls.get(a.get("toolUseID"), (0, "?"))
                err = a.get("blockingError") or a.get("stderr") or ""
                if isinstance(err, dict):
                    err = err.get("blockingError", err)
                errors.append((idx, f"[{a.get('hookName')}] {summary}", err))
                print(f"  #{idx} HOOK-BLOCK {a.get('hookName')} {ends(err)}")
            continue
        if t == "system":
            if d.get("hookErrors"):
                print(f"[hook-error] {snip(d['hookErrors'])}")
            if d.get("subtype") in ("compact_boundary", "api_error"):
                print(f"[{d['subtype']}] {snip(d.get('content', ''))}")
            continue
        msg = d.get("message")
        if t not in ("user", "assistant") or not isinstance(msg, dict):
            continue
        content = msg.get("content")
        if t == "user" and isinstance(content, str) and not d.get("isMeta"):
            print(f"\n[user] {snip(content, 300)}")
            continue
        if not isinstance(content, list):
            continue
        for b in content:
            if not isinstance(b, dict):
                continue
            bt = b.get("type")
            if bt == "text" and t == "assistant" and full:
                print(f"[assistant] {snip(b.get('text', ''))}")
            elif bt == "text" and t == "user" and not d.get("isMeta"):
                print(f"\n[user] {snip(b.get('text', ''), 300)}")
            elif bt == "tool_use":
                n += 1
                name, inp = b.get("name", "?"), b.get("input") or {}
                summary = tool_summary(name, inp)
                calls[b.get("id")] = (n, summary)
                counts[name] += 1
                if name == "Bash":
                    commands[" ".join(str(inp.get("command", "")).split())] += 1
                print(f"  #{n} {summary}")
            elif bt == "tool_result":
                idx, summary = calls.get(b.get("tool_use_id"), (0, "?"))
                text = result_text(b.get("content"))
                if b.get("is_error"):
                    errors.append((idx, summary, text))
                    print(f"  #{idx} ERROR {ends(text)}")
                size = result_size(text)
                if size > BIG_RESULT_CHARS:
                    big.append((size, idx, summary))

    print("\n## Summary")
    print(f"tool calls: {n}  " + ", ".join(f"{k}={v}" for k, v in counts.most_common()))
    print(f"errors and hook blocks: {len(errors)}")
    for idx, summary, text in errors[:15]:
        print(f"  #{idx} {summary} -> {ends(text, 120)}")
    print(f"results over {BIG_RESULT_CHARS} chars: {len(big)}")
    for size, idx, summary in sorted(big, reverse=True)[:10]:
        print(f"  #{idx} {size} chars {summary}")
    repeats = [(c, k) for k, c in commands.items() if c > 1]
    if repeats:
        print("repeated Bash commands:")
        for c, k in sorted(repeats, reverse=True)[:10]:
            print(f"  x{c} {snip(k, 100)}")
    subagents = path.with_suffix("") / "subagents"
    if subagents.is_dir():
        print("subagent transcripts (digest separately):")
        for f in sorted(subagents.glob("*.jsonl")):
            print(f"  {f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session", nargs="?", help="transcript path, or session id (prefix ok) under ~/.claude/projects")
    ap.add_argument("--list", type=int, metavar="N", help="list the N most recent sessions instead of digesting")
    ap.add_argument("--project", help="project path or name fragment, e.g. 'llama.cpp' or '~/git/foo', to scope --list")
    ap.add_argument("--full", action="store_true", help="include assistant text blocks in the timeline")
    args = ap.parse_args()
    if args.list:
        list_recent(args.list, args.project)
    elif args.session:
        digest(find_transcript(args.session), args.full)
    else:
        ap.error("give a session or --list N")


if __name__ == "__main__":
    main()
