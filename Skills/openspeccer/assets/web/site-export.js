// Whole-site export: every page rendered off-screen into one static HTML file, with app
// links rewritten to anchors inside the file.
import { render } from "preact";
import { cleanForExport, documentHtml, download, escapeHtml, fileSafe } from "./export.js";
import { apiUrl, changeHref, href, html, useState } from "./lib.js";
import { Agents } from "./views/agents.js";
import { ChangeDetail, ChangeList } from "./views/changes.js";
import { Commands } from "./views/commands.js";
import { Dashboard } from "./views/dashboard.js";
import { SchemaDetail, SchemaList } from "./views/schemas.js";
import { SpecDetail, SpecsPage } from "./views/specs.js";
import { Timeline } from "./views/timeline.js";

// Still fetching, or a diagram mermaid has neither drawn nor rejected yet.
const PENDING = ".loading, pre.mermaid-src:not(:has(+ .mermaid-error))";
const TIMEOUT_MS = 30000;

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

// An app route as an anchor id: the hash without `#` or the `tab` param, which only picks a view of the same page.
function anchor(hash) {
  const [path, qs = ""] = hash.replace(/^#/, "").split("?");
  const q = new URLSearchParams(qs);
  q.delete("tab");
  const rest = q.toString();
  return { full: rest ? `${path}?${rest}` : path, path };
}

async function sitePages(snap) {
  const schemas = await fetch(apiUrl("schemas"))
    .then((r) => r.json())
    .then((d) => d.schemas || [])
    .catch(() => []);
  const none = new URLSearchParams();
  const wt = (c) => new URLSearchParams(c.source && !c.source.is_main ? { wt: c.source.key } : {});
  return [
    { hash: href([]), view: html`<${Dashboard} snap=${snap} />` },
    { hash: href(["specs"]), view: html`<${SpecsPage} snap=${snap} topic="" query=${none} />` },
    ...snap.specs.map((s) => ({ hash: href(["specs", s.topic]), view: html`<${SpecDetail} topic=${s.topic} snap=${snap} query=${none} />` })),
    { hash: href(["changes"]), view: html`<${ChangeList} snap=${snap} query=${none} />` },
    ...snap.changes.map((c) => ({ hash: changeHref(c), view: html`<${ChangeDetail} slug=${c.slug} query=${wt(c)} expand />` })),
    { hash: href(["timeline"]), view: html`<${Timeline} snap=${snap} query=${none} />` },
    { hash: href(["schemas"]), view: html`<${SchemaList} snap=${snap} />` },
    ...schemas.map((s) => ({ hash: href(["schemas", s.name]), view: html`<${SchemaDetail} snap=${snap} name=${s.name} />` })),
    { hash: href(["agents"]), view: html`<${Agents} snap=${snap} />` },
    { hash: href(["commands"]), view: html`<${Commands} />` },
  ];
}

// Renders every page into an off-screen host (in the document, so charts can measure their
// width), waits for the data to arrive, then returns the cleaned markup.
async function renderSite(pages, onProgress) {
  const host = document.createElement("div");
  host.style.cssText = `position:absolute; left:-100000px; top:0; width:${document.querySelector(".main")?.clientWidth || 1200}px`;
  document.body.append(host);
  try {
    render(html`<div>${pages.map((p) => html`<section class="site-page" id=${anchor(p.hash).full} key=${p.hash}>${p.view}</section>`)}</div>`, host);
    const until = Date.now() + TIMEOUT_MS;
    for (;;) {
      await sleep(100);
      const waiting = [...host.firstElementChild.children].filter((s) => s.querySelector(PENDING)).length;
      onProgress(pages.length - waiting, pages.length);
      if (!waiting || Date.now() > until) break;
    }
    // Effects such as BDD keyword highlighting run after the next frame.
    await new Promise((r) => requestAnimationFrame(() => setTimeout(r)));
    const ids = new Set(pages.map((p) => anchor(p.hash).full));
    const copy = host.firstElementChild.cloneNode(true);
    cleanForExport(copy, (h) => {
      const a = anchor(h);
      if (ids.has(a.full)) return `#${a.full}`;
      return ids.has(a.path) ? `#${a.path}` : null;
    });
    return copy.innerHTML;
  } finally {
    render(null, host);
    host.remove();
  }
}

async function exportSite(snap, nav, onProgress) {
  const pages = await sitePages(snap);
  const body = await renderSite(pages, onProgress);
  const links = nav
    .map((n) => `<a class="nav-item" href="#${anchor(href(n.id ? [n.id] : [])).full}"><span class="nav-icon" aria-hidden="true">${n.icon}</span>${escapeHtml(n.label)}</a>`)
    .join("");
  // Local time as YYYY-MM-DD HH:MM; the sv-SE locale formats dates in that order.
  const stamp = new Date().toLocaleString("sv-SE").slice(0, 16);
  const doc = await documentHtml(
    `${snap.repo.name} - openspeccer`,
    `<div class="shell static-site">
<aside class="sidebar"><span class="wordmark">OPENSPECCER</span><div class="muted small">${escapeHtml(snap.repo.name)} · exported ${stamp}</div><nav class="nav">${links}</nav></aside>
<main class="main">${body}</main>
</div>`,
    ".static-site { grid-template-rows: 1fr; }\n.site-page + .site-page { border-top: 2px solid var(--border-strong); }",
  );
  download(`${fileSafe(snap.repo.name)}-openspeccer.html`, doc, "text/html");
}

export function SiteExport({ snap, nav }) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const run = async () => {
    setBusy(true);
    setNote("Exporting...");
    try {
      await exportSite(snap, nav, (done, total) => setNote(`Exporting ${done}/${total}`));
      setNote("");
    } catch (err) {
      console.error(err);
      setNote("Export failed");
      setTimeout(() => setNote(""), 2500);
    } finally {
      setBusy(false);
    }
  };
  return html`<button type="button" class="btn site-export" disabled=${busy || !snap} title="Save every page as one static HTML file" onClick=${run}>
    ${note || "Export all (HTML)"}
  </button>`;
}
