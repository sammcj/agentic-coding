"""Command line entry: serve the dashboard, or print a summary for an agent to read."""

from __future__ import annotations

import argparse
import errno
import json
import sys
import threading
import urllib.request
import webbrowser
from pathlib import Path

from . import __version__
from .repo import NotFound, Repo
from .server import serve

DEFAULT_PORT = 4380
_PORT_SPAN = 20
_LANE_TITLES = {
    "in_progress": "In progress",
    "ready": "Ready to archive",
    "planned": "Planned",
    "proposed": "Proposed",
}


def find_repo(start: Path) -> Path | None:
    """The nearest directory at or above `start` holding an `openspec/` directory."""
    for d in [start, *start.parents]:
        if (d / "openspec").is_dir():
            return d
    return None


def existing_instance(host: str, port: int, repo: Path) -> bool:
    try:
        with urllib.request.urlopen(f"http://{host}:{port}/api/ping", timeout=0.5) as resp:
            data = json.loads(resp.read())
    except (OSError, ValueError):
        return False
    return data.get("app") == "openspeccer" and data.get("repo") == str(repo)


def summary(snap: dict) -> str:
    s = snap["stats"]
    pct = f" ({100 * s['tasks_done'] // s['tasks_total']}%)" if s["tasks_total"] else ""
    lines = [
        f"{snap['repo']['name']} ({snap['repo']['path']})",
        f"Specs {s['specs']} ({s['requirements']} requirements) | Active {s['active']} | "
        f"Archived {s['archived']} | Active tasks {s['tasks_done']}/{s['tasks_total']}{pct}",
    ]
    active = [c for c in snap["changes"] if c["status"] == "active"]
    for lane, title in _LANE_TITLES.items():
        items = [c for c in active if c["lane"] == lane]
        if not items:
            continue
        lines.append(f"\n{title}:")
        for c in items:
            t = c["tasks"]
            tasks = f" {t['done']}/{t['total']} tasks" if t else ""
            where = "" if c["source"]["is_main"] else f" @ {c['source']['label']}"
            lines.append(f"  - {c['slug']} [{c['schema'] or '?'}]{tasks}, updated {c['updated'][:10]}{where}")
    archived = [c for c in snap["changes"] if c["status"] == "archived"][:5]
    if archived:
        lines.append("\nRecently archived:")
        lines += [f"  - {c['slug']}" for c in archived]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="openspeccer", description="Read-only OpenSpec dashboard.")
    p.add_argument("repo", nargs="?", default=".", help="repository path (default: nearest with openspec/)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=None, help=f"port (default {DEFAULT_PORT}, next free if busy)")
    p.add_argument("--no-open", action="store_true", help="do not open a browser")
    p.add_argument(
        "--jj", action="store_true", help="also include jj workspaces (git worktrees are always included)"
    )
    p.add_argument("--interval", type=float, default=1.0, help="watch poll interval in seconds")
    p.add_argument("--summary", action="store_true", help="print a short text summary and exit")
    p.add_argument("--change", metavar="SLUG", help="print one change (artifacts, tasks) as JSON and exit")
    p.add_argument("--json", action="store_true", help="print the whole snapshot as JSON and exit (large)")
    p.add_argument("--version", action="version", version=f"openspeccer {__version__}")
    args = p.parse_args(argv)

    root = find_repo(Path(args.repo).resolve())
    if root is None:
        print(f"openspeccer: no openspec/ directory at or above {args.repo}", file=sys.stderr)
        return 2
    repo = Repo(root)

    if args.change:
        try:
            detail = repo.change_detail(args.change, None, include_jj=args.jj)
        except NotFound:
            print(f"openspeccer: no change named {args.change}", file=sys.stderr)
            return 2
        print(json.dumps(detail, indent=2, default=str))
        return 0
    if args.summary or args.json:
        snap = repo.snapshot(True, args.jj)
        print(json.dumps(snap, indent=2, default=str) if args.json else summary(snap))
        return 0

    ports = [args.port] if args.port else range(DEFAULT_PORT, DEFAULT_PORT + _PORT_SPAN)
    for port in ports:
        url = f"http://{args.host}:{port}/"
        if existing_instance(args.host, port, repo.root):
            print(f"openspeccer already serving {root.name} at {url}", flush=True)
            if not args.no_open:
                webbrowser.open(url)
            return 0
        try:
            server, watcher = serve(repo, args.host, port, args.interval, args.jj)
        except OSError as e:
            if e.errno == errno.EADDRINUSE and not args.port:
                continue
            print(f"openspeccer: cannot listen on {args.host}:{port}: {e}", file=sys.stderr)
            return 1
        print(f"openspeccer serving {root.name} at {url}", flush=True)
        if not args.no_open:
            threading.Timer(0.3, webbrowser.open, args=(url,)).start()
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            watcher.stop()
            server.server_close()
        return 0
    print(f"openspeccer: no free port in {DEFAULT_PORT}-{DEFAULT_PORT + _PORT_SPAN - 1}", file=sys.stderr)
    return 1
