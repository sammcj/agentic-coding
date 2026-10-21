import base64
import hashlib
import http.client
import json
import re
import threading
import time
import unittest
import urllib.error
import urllib.request

from helpers import make_repo, write
from openspeccer.repo import Repo
from openspeccer.server import host_allowed, serve


class ServerTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp, self.root = make_repo()
        self.server, self.watcher = serve(Repo(self.root), "127.0.0.1", 0, 0.05, False)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def tearDown(self) -> None:
        self.watcher.stop()
        self.server.shutdown()
        self.server.server_close()
        self.tmp.cleanup()

    def get(self, path: str) -> tuple[int, bytes]:
        try:
            with urllib.request.urlopen(self.base + path, timeout=5) as r:
                return r.status, r.read()
        except urllib.error.HTTPError as e:
            with e:
                return e.code, e.read()

    def json(self, path: str) -> dict:
        status, body = self.get(path)
        self.assertEqual(status, 200, body)
        return json.loads(body)

    def test_api_and_static(self) -> None:
        self.assertEqual(self.json("/api/ping")["repo"], str(self.root))
        self.assertEqual(self.json("/api/snapshot")["stats"]["active"], 3)
        self.assertEqual(self.json("/api/spec?topic=billing/invoices")["doc"]["requirement_count"], 1)
        self.assertEqual(self.json("/api/change?slug=idea-sso")["lane"], "proposed")
        self.assertEqual(
            self.json("/api/spec/delta?topic=auth&slug=add-passkeys")["doc"]["groups"][0]["op"], "ADDED"
        )
        self.assertTrue(self.json("/api/search?q=lockout")["hits"])
        status, body = self.get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"importmap", body)

    def test_page_csp_allows_only_local_and_hashed_inline_scripts(self) -> None:
        with urllib.request.urlopen(self.base + "/", timeout=5) as r:
            csp, page = r.headers["Content-Security-Policy"], r.read().decode()
        importmap = re.search(r'<script type="importmap">(.*?)</script>', page, re.S)
        assert importmap and csp
        digest = base64.b64encode(hashlib.sha256(importmap[1].encode()).digest()).decode()
        directives = dict(d.strip().split(" ", 1) for d in csp.split(";"))
        self.assertEqual(directives["default-src"], "'self'")
        self.assertEqual(directives["script-src"], f"'self' 'sha256-{digest}'")

    def test_not_found_and_traversal(self) -> None:
        for path in (
            "/api/nope",
            "/api/spec?topic=../../x",
            "/api/change?slug=..%2F..",
            "/../scripts/serve.py",
            "/%2e%2e/pyproject.toml",
        ):
            status, _ = self.get(path)
            self.assertEqual(status, 404, path)

    def test_live_reload_bumps_version_over_sse(self) -> None:
        events: list[str] = []

        def listen() -> None:
            with urllib.request.urlopen(self.base + "/api/events", timeout=5) as r:
                for raw in r:
                    line = raw.decode().strip()
                    if line.startswith("data:"):
                        events.append(line[5:].strip())
                        if len(events) == 2:
                            return

        t = threading.Thread(target=listen, daemon=True)
        t.start()
        deadline = time.monotonic() + 3
        while not events and time.monotonic() < deadline:
            time.sleep(0.02)
        before = self.json("/api/snapshot")["changes"]
        write(self.root, "openspec/changes/idea-sso/tasks.md", "- [ ] new task\n")
        t.join(timeout=5)
        self.assertEqual(len(events), 2, "no version event after a file change")
        self.assertGreater(int(events[1]), int(events[0]))
        after = {c["name"]: c for c in self.json("/api/snapshot")["changes"]}
        self.assertNotEqual(before, after)
        self.assertEqual(after["idea-sso"]["lane"], "planned")

    def test_foreign_host_header_is_refused(self) -> None:
        port = self.server.server_address[1]
        conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
        conn.request("GET", "/api/ping", headers={"Host": f"evil.example:{port}"})
        self.assertEqual(conn.getresponse().status, 403)
        conn.close()


class HostAllowedTest(unittest.TestCase):
    def test_loopback_bind_accepts_loopback_names_on_its_port(self) -> None:
        for h in ("localhost:4381", "LocalHost:4381", "127.0.0.1:4381", "[::1]:4381"):
            self.assertTrue(host_allowed(h, "127.0.0.1", 4381), h)
        for h in ("evil.example:4381", "localhost:9999", "localhost", "", "127.0.0.1.nip.io:4381"):
            self.assertFalse(host_allowed(h, "127.0.0.1", 4381), h)

    def test_wildcard_bind_accepts_ip_literals_but_not_names(self) -> None:
        for h in ("192.168.1.5:4381", "[fe80::1]:4381", "localhost:4381"):
            self.assertTrue(host_allowed(h, "0.0.0.0", 4381), h)
        for h in ("evil.example:4381", "mybox.local:4381"):
            self.assertFalse(host_allowed(h, "0.0.0.0", 4381), h)

    def test_named_bind_and_allowed_names(self) -> None:
        self.assertTrue(host_allowed("mybox.local:4381", "0.0.0.0", 4381, ("MyBox.local",)))
        self.assertTrue(host_allowed("mybox.local:4381", "mybox.local", 4381))
        self.assertFalse(host_allowed("other.local:4381", "0.0.0.0", 4381, ("mybox.local",)))


if __name__ == "__main__":
    unittest.main()
