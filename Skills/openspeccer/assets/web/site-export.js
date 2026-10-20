// Whole-site export: every page rendered off-screen into one static HTML file, with app
// links rewritten to anchors inside the file.
import { cleanForExport, documentHtml, download, escapeHtml, fileSafe, renderOffscreen } from "./export.js";
import { apiUrl, changeHref, href, html, useState } from "./lib.js";
import { Agents } from "./views/agents.js";
import { ChangeDetail, ChangeList } from "./views/changes.js";
import { Commands } from "./views/commands.js";
import { Dashboard } from "./views/dashboard.js";
import { SchemaDetail, SchemaList } from "./views/schemas.js";
import { SpecDetail, SpecsPage } from "./views/specs.js";
import { Timeline } from "./views/timeline.js";

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
    ...snap.specs.map((s) => ({ hash: href(["specs", s.topic]), view: html`<${SpecDetail} topic=${s.topic} snap=${snap} query=${none} expand />` })),
    { hash: href(["changes"]), view: html`<${ChangeList} snap=${snap} query=${none} />` },
    ...snap.changes.map((c) => ({ hash: changeHref(c), view: html`<${ChangeDetail} slug=${c.slug} query=${wt(c)} expand />` })),
    { hash: href(["timeline"]), view: html`<${Timeline} snap=${snap} query=${none} />` },
    { hash: href(["schemas"]), view: html`<${SchemaList} snap=${snap} />` },
    ...schemas.map((s) => ({ hash: href(["schemas", s.name]), view: html`<${SchemaDetail} snap=${snap} name=${s.name} />` })),
    { hash: href(["agents"]), view: html`<${Agents} snap=${snap} />` },
    { hash: href(["commands"]), view: html`<${Commands} />` },
  ];
}

// Every page as one section, with links to pages in the file kept as in-file anchors.
async function renderSite(pages, onProgress) {
  const sections = pages.map((p) => html`<section class="site-page" id=${anchor(p.hash).full} key=${p.hash}>${p.view}</section>`);
  const { root, waiting } = await renderOffscreen(sections, { onProgress });
  const ids = new Set(pages.map((p) => anchor(p.hash).full));
  cleanForExport(root, (h) => {
    const a = anchor(h);
    if (ids.has(a.full)) return `#${a.full}`;
    return ids.has(a.path) ? `#${a.path}` : null;
  });
  return { body: root.innerHTML, waiting };
}

// Resolves to the number of pages still loading when the wait timed out.
async function exportSite(snap, nav, onProgress) {
  const pages = await sitePages(snap);
  const { body, waiting } = await renderSite(pages, onProgress);
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
  return waiting;
}

export function SiteExport({ snap, nav }) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const run = async () => {
    setBusy(true);
    setNote("Exporting...");
    let msg = "";
    try {
      const waiting = await exportSite(snap, nav, (done, total) => setNote(`Exporting ${done}/${total}`));
      if (waiting) msg = `Exported, ${waiting} page${waiting === 1 ? "" : "s"} incomplete`;
    } catch (err) {
      console.error(err);
      msg = "Export failed";
    } finally {
      setBusy(false);
      setNote(msg);
      if (msg) setTimeout(() => setNote(""), 4000);
    }
  };
  return html`<button type="button" class="btn site-export" disabled=${busy} title="Save every page as one static HTML file" onClick=${run}>
    ${note || "Export all (HTML)"}
  </button>`;
}
