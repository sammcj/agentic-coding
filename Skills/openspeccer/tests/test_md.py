import json
import shutil
import subprocess
import unittest
from pathlib import Path

WEB = Path(__file__).resolve().parent.parent / "assets" / "web"

# md.js imports bare specifiers that the browser resolves with index.html's import map.
# This hook gives node the same mapping, then prints renderMarkdown() of each argv input.
RENDER = """
import { registerHooks } from "node:module";
import { pathToFileURL } from "node:url";
const web = pathToFileURL(process.argv[1] + "/");
const vendor = { preact: "preact.mjs", "preact/hooks": "hooks.mjs", htm: "htm.mjs", marked: "marked.esm.js" };
registerHooks({
  resolve: (s, c, next) =>
    s in vendor ? { url: new URL("vendor/" + vendor[s], web).href, shortCircuit: true } : next(s, c),
});
const { renderMarkdown } = await import(new URL("md.js", web).href);
console.log(JSON.stringify(process.argv.slice(2).map((src) => renderMarkdown(src))));
"""


def render(*sources: str) -> list[str]:
    cmd = ["node", "--input-type=module", "-e", RENDER, str(WEB), *sources]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=30)
    return json.loads(out.stdout)


@unittest.skipUnless(shutil.which("node"), "node not installed")
class MarkdownTest(unittest.TestCase):
    def test_mermaid_block_becomes_escaped_placeholder(self) -> None:
        [out] = render("```mermaid\ngraph TD\n  A[<img src=x>] --> B\n```")
        self.assertIn('<pre class="mermaid-src">graph TD\n  A[&lt;img src=x&gt;] --&gt; B', out)
        self.assertNotIn("<img", out)

    def test_other_languages_keep_default_code_block(self) -> None:
        [out] = render("```python\nprint(1)\n```")
        self.assertIn('<code class="language-python">', out)
        self.assertNotIn("mermaid-src", out)


if __name__ == "__main__":
    unittest.main()
