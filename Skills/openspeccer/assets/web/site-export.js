// Whole-site export: every page rendered off-screen into one static HTML file that shows one page
// at a time, with app links rewritten to anchors inside the file.
import { cleanForExport, documentHtml, download, escapeHtml, fileSafe, renderOffscreen } from "./export.js";
import { apiUrl, changeHref, href, html, useState } from "./lib.js";
import { Agents } from "./views/agents.js";
import { ChangeDetail, ChangeList } from "./views/changes.js";
import { Config } from "./views/config.js";
import { Commands } from "./views/commands.js";
import { Dashboard } from "./views/dashboard.js";
import { Guide } from "./views/guide.js";
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

export const withoutArchived = (snap) => ({ ...snap, changes: snap.changes.filter((c) => c.status !== "archived") });

// `excludeArchived` applies to the change list and change pages only. The timeline's burndown needs
// archived changes, and the dashboard's archived lane would otherwise contradict its archived count.
async function sitePages(snap, excludeArchived) {
  const listed = excludeArchived ? withoutArchived(snap) : snap;
  const api = (url) =>
    fetch(url)
      .then((r) => (r.ok ? r.json() : null))
      .catch(() => null);
  // Both sections are the OpenSpec CLI's answers. Without it there are no commands, and only the
  // repo's own schemas, so a section with nothing to show is left out of the file.
  const [schemaList, commands] = await Promise.all([api(apiUrl("schemas")), api("/api/commands")]);
  const schemas = schemaList?.schemas || [];
  const hasCommands = Boolean(commands && !commands.error);
  const none = new URLSearchParams();
  const wt = (c) => new URLSearchParams(c.source && !c.source.is_main ? { wt: c.source.key } : {});
  return [
    { hash: href([]), view: html`<${Dashboard} snap=${snap} />` },
    { hash: href(["specs"]), view: html`<${SpecsPage} snap=${snap} topic="" query=${none} />` },
    ...snap.specs.map((s) => ({ hash: href(["specs", s.topic]), view: html`<${SpecDetail} topic=${s.topic} snap=${snap} query=${none} expand />` })),
    { hash: href(["changes"]), view: html`<${ChangeList} snap=${listed} query=${none} />` },
    ...listed.changes.map((c) => ({ hash: changeHref(c), view: html`<${ChangeDetail} slug=${c.slug} query=${wt(c)} expand />` })),
    { hash: href(["timeline"]), view: html`<${Timeline} snap=${snap} query=${none} />` },
    ...(schemas.length ? [{ hash: href(["schemas"]), view: html`<${SchemaList} snap=${snap} />` }] : []),
    ...schemas.map((s) => ({ hash: href(["schemas", s.name]), view: html`<${SchemaDetail} snap=${snap} name=${s.name} />` })),
    { hash: href(["config"]), view: html`<${Config} snap=${snap} />` },
    { hash: href(["agents"]), view: html`<${Agents} snap=${snap} />` },
    ...(hasCommands ? [{ hash: href(["commands"]), view: html`<${Commands} />` }] : []),
    { hash: href(["guide"]), view: html`<${Guide} snap=${snap} />` },
  ];
}

// The nav entry a route belongs to: its first path segment, empty for the dashboard.
const navId = (hash) => anchor(hash).path.split("/")[1] || "";

// Nav entries whose section made it into the export.
export function navWithPages(nav, hashes) {
  const present = new Set(hashes.map(navId));
  return nav.filter((n) => present.has(n.id));
}

// The export's CSP forbids scripts, so the URL fragment picks the page: CSS shows the section that is
// `:target`, or the first when nothing is, and marks that section's nav entry as active.
export function siteCss(nav) {
  const active = nav.map((n) => `.static-site:has(.site-page[data-nav="${n.id}"]:target) .nav-item[data-nav="${n.id}"]`);
  return `.static-site { grid-template-rows: 1fr; }
.site-page { display: none; }
.site-page:target, .main:not(:has(.site-page:target)) > .site-page:first-child { display: block; }
${active.join(",\n")},
.static-site:not(:has(.site-page:target)) .nav-item[data-nav=""] { background: var(--accent); color: #fff; }
@media print {
  .static-site { display: block; height: auto; }
  .static-site .sidebar { display: none; }
  .static-site .main { overflow: visible; }
  .site-page { display: block; }
  .site-page + .site-page { border-top: 2px solid var(--border-strong); }
}`;
}

// Every page as one section, with links to pages in the file kept as in-file anchors.
async function renderSite(pages, onProgress) {
  const sections = pages.map((p) => html`<section class="site-page" id=${anchor(p.hash).full} data-nav=${navId(p.hash)} key=${p.hash}>${p.view}</section>`);
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
async function exportSite(snap, nav, excludeArchived, onProgress) {
  const pages = await sitePages(snap, excludeArchived);
  const { body, waiting } = await renderSite(pages, onProgress);
  nav = navWithPages(nav, pages.map((p) => p.hash));
  const links = nav
    .map((n) => `<a class="nav-item" data-nav="${n.id}" href="#${anchor(href(n.id ? [n.id] : [])).full}"><span class="nav-icon" aria-hidden="true">${n.icon}</span>${escapeHtml(n.label)}</a>`)
    .join("");
  // Local time as YYYY-MM-DD HH:MM; the sv-SE locale formats dates in that order.
  const stamp = new Date().toLocaleString("sv-SE").slice(0, 16);
  const doc = await documentHtml(
    `${snap.repo.name} - openspeccer`,
    `<div class="shell static-site">
<aside class="sidebar"><a class="wordmark" href="#/">OPENSPECCER</a><div class="muted small">${escapeHtml(snap.repo.name)} · exported ${stamp}${excludeArchived ? " · archived change pages excluded" : ""}</div><nav class="nav">${links}</nav></aside>
<main class="main">${body}</main>
</div>`,
    siteCss(nav),
  );
  download(`${fileSafe(snap.repo.name)}-openspeccer.html`, doc, "text/html");
  return waiting;
}

export function SiteExport({ snap, nav }) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");
  const [excludeArchived, setExcludeArchived] = useState(false);
  const run = async () => {
    setBusy(true);
    setNote("Exporting...");
    let msg = "";
    try {
      const waiting = await exportSite(snap, nav, excludeArchived, (done, total) => setNote(`Exporting ${done}/${total}`));
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
  return html`<div class="site-export">
    <button type="button" class="btn" disabled=${busy} title="Save every page as one static HTML file" onClick=${run}>
      ${note || "Export all (HTML)"}
    </button>
    <label class="muted small">
      <input type="checkbox" checked=${excludeArchived} disabled=${busy} onChange=${(e) => setExcludeArchived(e.currentTarget.checked)} />
      Exclude archived change pages
    </label>
  </div>`;
}
