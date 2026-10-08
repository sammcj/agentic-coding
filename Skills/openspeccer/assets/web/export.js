// Page exports: Markdown builders, clipboard, file download, and a static HTML snapshot.
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

function download(filename, text, type) {
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

const escapeHtml = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);

// The page as rendered, with the app stylesheet inlined so the file stands alone.
async function staticHtml(title) {
  const css = await fetch("/style.css").then((r) => r.text());
  const main = document.querySelector(".main").cloneNode(true);
  for (const el of main.querySelectorAll(".export-menu, input, select, .toolbar .chips, button")) el.remove();
  for (const a of main.querySelectorAll('a[href^="#"]')) a.removeAttribute("href"); // app routes go nowhere offline
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(title)}</title>
<style>${css}
body { overflow: auto; height: auto; }
.main.static-export { height: auto; overflow: visible; }</style>
</head><body><main class="main static-export">${main.innerHTML}</main></body></html>
`;
}

export function ExportMenu({ name, title, markdown }) {
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
    if (action === "html") download(`${base}.html`, await staticHtml(title || name), "text/html");
  };
  return html`<div class="export-menu" ref=${ref}>
    <button type="button" class="btn" aria-haspopup="menu" aria-expanded=${open} onClick=${() => setOpen(!open)}>${note || "Export"} ▾</button>
    ${open && html`<div class="menu" role="menu">
      <button type="button" role="menuitem" onClick=${() => run("md")}>Save as Markdown</button>
      <button type="button" role="menuitem" onClick=${() => run("copy")}>Copy as Markdown</button>
      <button type="button" role="menuitem" onClick=${() => run("html")}>Save as static HTML</button>
    </div>`}
  </div>`;
}
