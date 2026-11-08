// Page exports: Markdown builders, clipboard, file download, and a static HTML snapshot.
import { render } from "preact";
import { html, useEffect, useRef, useState } from "./lib.js";

export async function copyText(text) {
  try {
    await navigator.clipboard.writeText(text);
    return true;
  } catch {
    // The async clipboard API is refused outside a secure context, e.g. a LAN address.
    const ta = Object.assign(document.createElement("textarea"), { value: text });
    ta.style.cssText = "position:fixed;opacity:0";
    document.body.append(ta);
    ta.select();
    const ok = document.execCommand("copy");
    ta.remove();
    return ok;
  }
}

export function download(filename, text, type) {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = Object.assign(document.createElement("a"), { href: url, download: filename });
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export const fileSafe = (s) => s.replace(/[^\w.-]+/g, "-").replace(/^-+|-+$/g, "") || "openspec";

const cell = (v) => String(v ?? "").replace(/\|/g, "\\|").replace(/\n/g, " ");

export function mdTable(head, rows) {
  return [`| ${head.map(cell).join(" | ")} |`, `|${head.map(() => " --- |").join("")}`, ...rows.map((r) => `| ${r.map(cell).join(" | ")} |`)].join("\n");
}

export const escapeHtml = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// Still fetching, or a diagram mermaid has neither drawn nor rejected yet.
const PENDING = ".loading, pre.mermaid-src:not(:has(+ .mermaid-error))";

// Renders `parts` (vnodes) off-screen and returns a copy once nothing is pending, plus how many
// parts were still pending at the timeout. The host sits in the document so charts can measure
// their width and mermaid will draw; the copy is taken because unmounting empties the host.
export async function renderOffscreen(parts, { timeout = 30000, onProgress } = {}) {
  const host = document.createElement("div");
  host.style.cssText = `position:absolute; left:-100000px; top:0; width:${document.querySelector(".main")?.clientWidth || 1200}px`;
  document.body.append(host);
  try {
    render(html`<div>${parts}</div>`, host);
    const root = host.firstElementChild;
    const until = Date.now() + timeout;
    let waiting;
    do {
      await new Promise((r) => setTimeout(r, 100));
      waiting = [...root.children].filter((el) => el.querySelector(PENDING)).length;
      onProgress?.(root.children.length - waiting, root.children.length);
    } while (waiting && Date.now() < until);
    // Effects such as BDD keyword highlighting run after the next frame.
    await new Promise((r) => requestAnimationFrame(() => setTimeout(r)));
    return { root: root.cloneNode(true), waiting };
  } finally {
    render(null, host);
    host.remove();
  }
}

// The export's CSP forbids scripts, so each tab is a radio followed by its label and panel, and
// CSS shows the panel after the checked radio. This runs after rendering because panels must be
// visible while charts measure their width, and `checked` has to be an attribute to be serialised.
function staticTabs(root) {
  for (const [g, group] of [...root.querySelectorAll(".all-tabs")].entries()) {
    const panels = [...group.children];
    if (panels.length > 1) group.classList.add("static-tabs");
    panels.forEach((panel, i) => {
      const { tab, icon } = panel.dataset;
      delete panel.dataset.tab;
      delete panel.dataset.icon;
      if (panels.length === 1) return;
      const id = `tab-${g}-${i}`;
      const radio = Object.assign(document.createElement("input"), { type: "radio", name: `tabs-${g}`, id, className: "tab-radio" });
      if (i === 0) radio.setAttribute("checked", "");
      const label = Object.assign(document.createElement("label"), { htmlFor: id, className: "tab" });
      const kind = Object.assign(document.createElement("span"), { className: "tab-kind", textContent: icon });
      kind.setAttribute("aria-hidden", "true");
      label.append(kind, tab);
      panel.before(radio, label);
    });
  }
}

// Strips the controls from rendered app markup. App routes go nowhere offline, so each
// `#` link is dropped unless `link` maps it to an anchor inside the exported file.
export function cleanForExport(root, link = () => null) {
  // Click-to-copy commands are buttons, but their text is the content.
  for (const b of root.querySelectorAll("button.copyable")) b.replaceWith(Object.assign(document.createElement("code"), { textContent: b.textContent.trim() }));
  for (const el of root.querySelectorAll(".export-menu, input, select, .toolbar .chips, button")) el.remove();
  // Hover text repeating each entry, and mermaid's edge data, which only its own script reads.
  for (const a of root.querySelectorAll(".toc-item")) a.removeAttribute("title");
  for (const p of root.querySelectorAll("[data-points]")) p.removeAttribute("data-points");
  for (const a of root.querySelectorAll('a[href^="#"]')) {
    const to = link(a.getAttribute("href"));
    if (to) a.setAttribute("href", to);
    else a.removeAttribute("href");
  }
  staticTabs(root);
}

// Whitespace next to these tags renders nothing, unlike the space in `<b>a</b> <i>b</i>`.
const BLOCK = "article|aside|blockquote|dd|div|dl|dt|h[1-6]|header|hr|li|main|nav|ol|p|pre|section|table|tbody|td|th|thead|tr|ul";
// Matches pre, style and svg whole so nothing inside them is touched.
// The gap is optional so a lazy match stops at its first closing tag instead of backtracking past it.
const BLOCK_GAP = new RegExp(`(<(pre|style|svg)\\b[\\s\\S]*?</\\2>|</?(?:${BLOCK})\\b[^>]*>)(?:\\s+(?=</?(?:${BLOCK})\\b))?`, "g");

export const minifyHtml = (s) => s.replace(BLOCK_GAP, "$1");

export const minifyCss = (s) =>
  s
    .replace(/\/\*[\s\S]*?\*\//g, "")
    .replace(/\s+/g, " ")
    .replace(/ ?([{};,]) ?/g, "$1")
    .trim();

// A standalone document with the app stylesheet inlined. It needs no script or network, so the
// CSP stops any repository markup that slipped through rendering from running when opened.
export async function documentHtml(title, body, css = "") {
  const appCss = await fetch("/style.css").then((r) => r.text());
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:">
<title>${escapeHtml(title)}</title>
<style>${minifyCss(`${appCss}
body { overflow: auto; height: auto; }
.main.static-export { height: auto; overflow: visible; }
${css}`)}</style>
</head><body>${minifyHtml(body)}</body></html>
`;
}

// The page as rendered. `swap` may rewrite the cloned page first, e.g. to replace one tab with
// every tab, and resolves to how many parts were still loading.
async function staticHtml(title, swap) {
  const main = document.querySelector(".main").cloneNode(true);
  const waiting = swap ? await swap(main) : 0;
  cleanForExport(main);
  return { doc: await documentHtml(title, `<main class="main static-export">${main.innerHTML}</main>`), waiting };
}

const ACTIONS = [
  { id: "md", label: "Save as Markdown" },
  { id: "copy", label: "Copy as Markdown" },
  { id: "html", label: "Save as static HTML" },
];

// `swap`, when given, rewrites the cloned page for the static HTML save.
export function ExportMenu({ name, title, markdown, swap }) {
  const [open, setOpen] = useState(false);
  const [note, setNote] = useState("");
  const ref = useRef(null);
  useEffect(() => {
    if (!open) return;
    const close = (e) => !ref.current?.contains(e.target) && setOpen(false);
    const esc = (e) => e.key === "Escape" && setOpen(false);
    addEventListener("pointerdown", close);
    addEventListener("keydown", esc);
    return () => {
      removeEventListener("pointerdown", close);
      removeEventListener("keydown", esc);
    };
  }, [open]);
  const flash = (msg) => {
    setNote(msg);
    setTimeout(() => setNote(""), 1800);
  };
  const run = async (action) => {
    setOpen(false);
    const base = fileSafe(name);
    if (action === "md") download(`${base}.md`, markdown(), "text/markdown");
    if (action === "copy") flash((await copyText(markdown())) ? "Copied" : "Copy failed");
    if (action === "html") {
      if (swap) setNote("Exporting...");
      try {
        const { doc, waiting } = await staticHtml(title || name, swap);
        download(`${base}.html`, doc, "text/html");
        if (waiting) flash("Exported, incomplete");
        else setNote("");
      } catch (err) {
        console.error(err);
        flash("Export failed");
      }
    }
  };
  return html`<div class="export-menu" ref=${ref}>
    <button type="button" class="btn" aria-haspopup="menu" aria-expanded=${open} onClick=${() => setOpen(!open)}>${note || "Export"} ▾</button>
    ${open && html`<div class="menu" role="menu">
      ${ACTIONS.map((a) => html`<button type="button" role="menuitem" onClick=${() => run(a.id)}>${a.label}</button>`)}
    </div>`}
  </div>`;
}
