import json
import threading
import time
import unittest
import urllib.error
import urllib.request

from helpers import make_repo, write
from openspeccer.repo import Repo
from openspeccer.server import serve


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


if __name__ == "__main__":
    unittest.main()
