// Markdown rendering with BDD keyword marks and stable heading ids.
import { Marked } from "marked";
import { html, useEffect, useRef } from "./lib.js";

const escapeHtml = (s) =>
  String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

export function slugify(text) {
  return (
    text
      .toLowerCase()
      .replace(/[^\w\- ]/g, "")
      .trim()
      .replace(/ /g, "-") || "section"
  );
}

let slugCounts = new Map();
let idPrefix = "";

const marked = new Marked({
  gfm: true,
  renderer: {
    // Repository content is rendered, never trusted: raw HTML shows as text.
    html({ text }) {
      return escapeHtml(text);
    },
    heading({ tokens, depth, text }) {
      const base = slugify(text);
      const n = slugCounts.get(base) || 0;
      slugCounts.set(base, n + 1);
      const id = idPrefix + (n ? `${base}-${n}` : base);
      return `<h${depth} id="${id}">${this.parser.parseInline(tokens)}</h${depth}>\n`;
    },
    link({ href, title, tokens }) {
      const inner = this.parser.parseInline(tokens);
      if (!/^(https?:|mailto:|#)/i.test(href || "")) return `<span class="link-local" title="${escapeHtml(href)}">${inner}</span>`;
      const t = title ? ` title="${escapeHtml(title)}"` : "";
      return `<a href="${escapeHtml(href)}"${t} target="_blank" rel="noreferrer">${inner}</a>`;
    },
    // Browsers break after "/", splitting a path or package name across lines. A short span
    // stays whole; a long one may still wrap rather than overflow the column.
    codespan({ text }) {
      const whole = text.length <= 60;
      return `<code${whole ? ' class="nowrap"' : ""}>${escapeHtml(text)}</code>`;
    },
    image({ text }) {
      return `<span class="img-alt">[image: ${escapeHtml(text)}]</span>`;
    },
  },
});

export function renderMarkdown(src, prefix = "") {
  slugCounts = new Map();
  idPrefix = prefix;
  return marked.parse(src || "");
}

// Headings for a table of contents, with the same ids `renderMarkdown` assigns.
export function headings(src, prefix = "", depths = [2, 3]) {
  const counts = new Map();
  const out = [];
  for (const t of marked.lexer(src || "")) {
    if (t.type !== "heading") continue;
    const base = slugify(t.text);
    const n = counts.get(base) || 0;
    counts.set(base, n + 1);
    if (depths.includes(t.depth)) out.push({ depth: t.depth, text: t.text, id: prefix + (n ? `${base}-${n}` : base) });
  }
  return out;
}

// -- BDD marks --
// Uppercase keywords anywhere in prose; title-case step words only when they are a whole
// **bold** run, since "When the server..." opening a sentence is ordinary prose.
const KEYWORDS = {
  GIVEN: "kw-step",
  WHEN: "kw-step",
  THEN: "kw-then",
  AND: "kw-and",
  MUST: "kw-must",
  SHALL: "kw-must",
  "MUST NOT": "kw-must",
  "SHALL NOT": "kw-must",
  ADDED: "kw-op op-added",
  MODIFIED: "kw-op op-modified",
  REMOVED: "kw-op op-removed",
  RENAMED: "kw-op op-renamed",
};
const STEP_TITLE = new Set(["Given", "When", "Then", "And"]);
const KW_RE = /\b(MUST NOT|SHALL NOT|GIVEN|WHEN|THEN|AND|MUST|SHALL|ADDED|MODIFIED|REMOVED|RENAMED)\b/g;
const SKIP = new Set(["CODE", "PRE", "H1", "H2", "H3", "H4", "H5", "H6", "A"]);

function highlightBdd(root) {
  for (const strong of root.querySelectorAll("strong")) {
    const text = strong.textContent.trim();
    const cls = KEYWORDS[text] || (STEP_TITLE.has(text) ? KEYWORDS[text.toUpperCase()] : null);
    if (cls && !strong.closest("h1,h2,h3,h4,h5,h6")) strong.className = `kw ${cls}`;
  }
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      for (let el = node.parentElement; el && el !== root; el = el.parentElement) {
        if (SKIP.has(el.tagName) || el.classList.contains("kw")) return NodeFilter.FILTER_REJECT;
      }
      KW_RE.lastIndex = 0;
      return KW_RE.test(node.data) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
    },
  });
  const nodes = [];
  while (walker.nextNode()) nodes.push(walker.currentNode);
  for (const node of nodes) {
    const frag = document.createDocumentFragment();
    let last = 0;
    node.data.replace(KW_RE, (m, _kw, offset) => {
      if (offset > last) frag.append(node.data.slice(last, offset));
      const span = document.createElement("span");
      span.className = `kw ${KEYWORDS[m]}`;
      span.textContent = m;
      frag.append(span);
      last = offset + m.length;
      return m;
    });
    if (last < node.data.length) frag.append(node.data.slice(last));
    node.replaceWith(frag);
  }
}

export function Markdown({ src, prefix = "", bdd = true, className = "" }) {
  const ref = useRef(null);
  const rendered = renderMarkdown(src, prefix);
  useEffect(() => {
    if (bdd && ref.current) highlightBdd(ref.current);
  }, [rendered, bdd]);
  // In-document `#anchor` links would otherwise replace the router's hash.
  const onClick = (e) => {
    const a = e.target.closest?.("a[href^='#']");
    if (!a || a.getAttribute("href").startsWith("#/")) return;
    e.preventDefault();
    const id = prefix + a.getAttribute("href").slice(1);
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  return html`<div ref=${ref} class=${`md ${className}`} onClick=${onClick} dangerouslySetInnerHTML=${{ __html: rendered }} />`;
}

export function Toc({ items, title = "On this page" }) {
  if (!items.length) return null;
  const go = (e, id) => {
    e.preventDefault();
    document.getElementById(id)?.scrollIntoView({ behavior: "smooth", block: "start" });
  };
  return html`<nav class="toc">
    <div class="toc-title">${title}</div>
    ${items.map(
      (it) => html`<a class=${`toc-item toc-l${it.level}`} href=${`#${it.id}`} title=${it.text} onClick=${(e) => go(e, it.id)}>
        ${it.text}
      </a>`,
    )}
  </nav>`;
}
