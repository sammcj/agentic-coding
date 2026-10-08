"""HTTP server: JSON API, static UI, and server-sent events driven by a polling watcher.

Polling (stat every interval) is deliberate: it works the same on every filesystem, including
network mounts and container bind mounts where native change events never arrive.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import mimetypes
import os
import sys
import threading
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, cast
from urllib.parse import parse_qs, urlparse

from . import __version__
from .repo import NotFound, Repo

ASSETS = Path(__file__).resolve().parents[2] / "assets" / "web"
_HEARTBEAT = 15.0
_WILDCARD_HOSTS = ("0.0.0.0", "::", "")
_WORKTREE_RECHECK = 5  # ticks between worktree list refreshes, which spawn git


class Watcher(threading.Thread):
    """Bumps the repo version whenever any file under a watched `openspec/` tree changes."""

    def __init__(self, repo: Repo, interval: float, include_jj: bool) -> None:
        super().__init__(daemon=True, name="openspeccer-watcher")
        self.repo = repo
        self.interval = interval
        self.include_jj = include_jj
        self.changed = threading.Condition()
        self._roots: list[Path] = []
        self._halt = threading.Event()

    def stop(self) -> None:
        self._halt.set()

    def _refresh_roots(self) -> None:
        trees = self.repo.worktrees(True, self.include_jj)
        self._roots = [Path(w.path) / "openspec" for w in trees]

    def signature(self) -> tuple[str, str]:
        """(everything, project schemas). Schemas are tracked apart because re-resolving them
        spawns the CLI, which is too slow to repeat on every artifact save."""
        everything, schemas = hashlib.sha1(), hashlib.sha1()
        for root in self._roots:
            everything.update(str(root).encode())
            schema_dir = str(root / "schemas")
            for dirpath, dirnames, filenames in os.walk(root):
                dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
                for name in sorted(filenames):
                    try:
                        st = os.stat(os.path.join(dirpath, name))
                    except OSError:
                        continue
                    entry = f"{dirpath}/{name}:{st.st_mtime_ns}:{st.st_size}".encode()
                    everything.update(entry)
                    if dirpath.startswith(schema_dir):
                        schemas.update(entry)
        return everything.hexdigest(), schemas.hexdigest()

    def run(self) -> None:
        self._refresh_roots()
        last = self.signature()
        tick = 0
        while not self._halt.wait(self.interval):
            tick += 1
            if tick % _WORKTREE_RECHECK == 0:
                self._refresh_roots()
            sig = self.signature()
            if sig != last:
                if sig[1] != last[1]:
                    self.repo.schemas_changed()
                last = sig
                self.repo.bump()
                with self.changed:
                    self.changed.notify_all()


def _flag(qs: dict[str, list[str]], name: str, default: bool) -> bool:
    v = qs.get(name, [None])[0]
    return default if v is None else v not in ("0", "false", "no")


def _arg(qs: dict[str, list[str]], name: str) -> str:
    return qs.get(name, [""])[0]


def make_handler(repo: Repo, watcher: Watcher | None, default_jj: bool) -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server_version = f"openspeccer/{__version__}"

        def log_message(self, format: str, *args: Any) -> None:
            if os.environ.get("OPENSPECCER_DEBUG"):
                sys.stderr.write(f"{self.address_string()} - {format % args}\n")

        def do_GET(self) -> None:
            url = urlparse(self.path)
            qs = parse_qs(url.query)
            if not self._host_allowed():
                return self._json({"error": "unexpected Host header"}, HTTPStatus.FORBIDDEN)
            try:
                if url.path == "/api/events":
                    return self._events()
                if url.path.startswith("/api/"):
                    return self._json(self._api(url.path, qs))
                return self._static(url.path)
            except NotFound as e:
                self._json({"error": f"not found: {e}"}, HTTPStatus.NOT_FOUND)
            except (BrokenPipeError, ConnectionResetError):
                pass
            except Exception as e:  # keep serving; report the failure to the page
                sys.stderr.write(f"openspeccer: error handling {url.path}: {e!r}\n")
                self._json({"error": str(e)}, HTTPStatus.INTERNAL_SERVER_ERROR)

        def _host_allowed(self) -> bool:
            """Refuse a Host the server was not reached by. A page on another site can rebind its
            own hostname to 127.0.0.1 and then read the API as same-origin; its Host header still
            names that site."""
            bound, port = cast(tuple[str, int], self.server.server_address)[:2]
            if bound in _WILDCARD_HOSTS:
                return True  # listening on every interface is an explicit choice to accept any name
            names = {bound, "localhost", "127.0.0.1", "[::1]"}
            return self.headers.get("Host", "") in {f"{n}:{port}" for n in names}

        def _api(self, path: str, qs: dict[str, list[str]]) -> Any:
            scope = {"include_jj": _flag(qs, "jj", default_jj), "aggregate": _flag(qs, "aggregate", True)}
            wt = _arg(qs, "wt") or None
            match path:
                case "/api/ping":
                    return {"app": "openspeccer", "repo": str(repo.root), "version": __version__}
                case "/api/snapshot":
                    return repo.snapshot(**scope)
                case "/api/change":
                    return repo.change_detail(_arg(qs, "slug"), wt, **scope)
                case "/api/spec":
                    return repo.spec_detail(_arg(qs, "topic"), **scope)
                case "/api/spec/delta":
                    return repo.spec_delta(_arg(qs, "topic"), _arg(qs, "slug"), wt, **scope)
                case "/api/spec/diff":
                    return repo.spec_diff(_arg(qs, "topic"), _arg(qs, "base"), _arg(qs, "head") or "working")
                case "/api/schemas":
                    return repo.schemas(**scope)
                case "/api/schema":
                    return repo.schema_detail(_arg(qs, "name"))
                case "/api/search":
                    return {"query": _arg(qs, "q"), "hits": repo.search(_arg(qs, "q"), **scope)}
            raise NotFound(path)

        def _json(self, data: Any, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(data, default=str).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self._send_body(body)

        def _send_body(self, body: bytes) -> None:
            if len(body) > 1024 and "gzip" in self.headers.get("Accept-Encoding", ""):
                body = gzip.compress(body, compresslevel=5)
                self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _static(self, path: str) -> None:
            rel = "index.html" if path in ("", "/") else path.lstrip("/")
            target = (ASSETS / rel).resolve()
            if not target.is_relative_to(ASSETS) or not target.is_file():
                raise NotFound(path)
            ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
            if target.suffix in (".js", ".mjs"):
                ctype = "text/javascript"
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", f"{ctype}; charset=utf-8")
            self.send_header("Cache-Control", "no-cache")
            self._send_body(target.read_bytes())

        def _events(self) -> None:
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            seen = -1
            try:
                while True:
                    if repo.version != seen:
                        seen = repo.version
                        self.wfile.write(f"event: version\ndata: {seen}\n\n".encode())
                    else:
                        self.wfile.write(b": heartbeat\n\n")
                    self.wfile.flush()
                    if watcher is None:
                        time.sleep(_HEARTBEAT)
                        continue
                    with watcher.changed:
                        # Re-check under the lock: a bump between the write and here would
                        # otherwise wait out a whole heartbeat.
                        if repo.version == seen:
                            watcher.changed.wait(_HEARTBEAT)
            except (BrokenPipeError, ConnectionResetError, OSError):
                return

    return Handler


class Server(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def serve(repo: Repo, host: str, port: int, interval: float, include_jj: bool) -> tuple[Server, Watcher]:
    watcher = Watcher(repo, interval, include_jj)
    server = Server((host, port), make_handler(repo, watcher, include_jj))
    watcher.start()
    return server, watcher
