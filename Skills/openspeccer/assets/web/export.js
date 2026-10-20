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

// Strips the controls from rendered app markup. App routes go nowhere offline, so each
// `#` link is dropped unless `link` maps it to an anchor inside the exported file.
export function cleanForExport(root, link = () => null) {
  // Click-to-copy commands are buttons, but their text is the content.
  for (const b of root.querySelectorAll("button.copyable")) b.replaceWith(Object.assign(document.createElement("code"), { textContent: b.textContent.trim() }));
  for (const el of root.querySelectorAll(".export-menu, input, select, .toolbar .chips, button")) el.remove();
  for (const a of root.querySelectorAll('a[href^="#"]')) {
    const to = link(a.getAttribute("href"));
    if (to) a.setAttribute("href", to);
    else a.removeAttribute("href");
  }
}

// A standalone document with the app stylesheet inlined.
export async function documentHtml(title, body, css = "") {
  const appCss = await fetch("/style.css").then((r) => r.text());
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(title)}</title>
<style>${appCss}
body { overflow: auto; height: auto; }
.main.static-export { height: auto; overflow: visible; }
${css}</style>
</head><body>${body}</body></html>
`;
}

// The page as rendered. `swap` may rewrite the cloned page first, e.g. to replace one tab with every tab.
async function staticHtml(title, swap) {
  const main = document.querySelector(".main").cloneNode(true);
  if (swap) await swap(main);
  cleanForExport(main);
  return documentHtml(title, `<main class="main static-export">${main.innerHTML}</main>`);
}

const ACTIONS = [
  { id: "md", label: "Save as Markdown" },
  { id: "copy", label: "Copy as Markdown" },
  { id: "html", label: "Save as static HTML" },
];

// `all`, when given, adds the same actions for every tab: { name, markdown, swap }.
export function ExportMenu({ name, title, markdown, all }) {
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
  const run = async (action, target) => {
    setOpen(false);
    const base = fileSafe(target.name);
    if (action === "md") download(`${base}.md`, target.markdown(), "text/markdown");
    if (action === "copy") flash((await copyText(target.markdown())) ? "Copied" : "Copy failed");
    if (action === "html") {
      if (target.swap) setNote("Exporting...");
      download(`${base}.html`, await staticHtml(title || name, target.swap), "text/html");
      setNote("");
    }
  };
  const items = (target) => ACTIONS.map((a) => html`<button type="button" role="menuitem" onClick=${() => run(a.id, target)}>${a.label}</button>`);
  return html`<div class="export-menu" ref=${ref}>
    <button type="button" class="btn" aria-haspopup="menu" aria-expanded=${open} onClick=${() => setOpen(!open)}>${note || "Export"} ▾</button>
    ${open && html`<div class="menu" role="menu">
      ${all && html`<div class="menu-group" role="presentation">This tab</div>`}
      ${items({ name, markdown })}
      ${all && html`<div class="menu-group" role="presentation">All tabs</div>${items(all)}`}
    </div>`}
  </div>`;
}
