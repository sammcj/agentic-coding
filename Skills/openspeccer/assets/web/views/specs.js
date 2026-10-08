import { apiUrl, changeHref, href, html, setQuery, useApi, useState } from "../lib.js";
import { Markdown, Toc } from "../md.js";
import { Badge, Chips, Empty, ErrorBox, Loading, OpBadge, PageHeader } from "../ui.js";

// -- spec document as cards --

export function docToc(doc, prefix = "", base = 0) {
  const items = [];
  for (const g of doc.groups) {
    if (g.heading) items.push({ level: base, text: g.heading, id: prefix + g.anchor });
    for (const b of g.blocks) {
      items.push({ level: base + 1, text: b.name, id: prefix + b.anchor });
      for (const c of b.children) items.push({ level: base + 2, text: c.name, id: prefix + c.anchor });
    }
  }
  return items;
}

function BlockCard({ block, prefix }) {
  const label = block.kind === "requirement" ? "Requirement" : null;
  return html`<article class=${`req-card kind-${block.kind}`} id=${prefix + block.anchor}>
    <h3 class="req-title">${label && html`<span class="req-kind">${label}</span>`}${block.name}</h3>
    ${block.body && html`<${Markdown} src=${block.body} prefix=${`${prefix}${block.anchor}--`} />`}
    ${block.children.map(
      (c) => html`<section class="scenario" id=${prefix + c.anchor}>
        <h4 class="scenario-title">${c.kind === "scenario" && html`<span class="req-kind">Scenario</span>`}${c.name}</h4>
        ${c.body && html`<${Markdown} src=${c.body} prefix=${`${prefix}${c.anchor}--`} />`}
      </section>`,
    )}
  </article>`;
}

export function SpecDoc({ doc, prefix = "" }) {
  return html`<div class="spec-doc">
    ${doc.intro && html`<${Markdown} src=${doc.intro} prefix=${prefix} />`}
    ${doc.groups.map(
      (g) => html`<section class="spec-group">
        ${g.heading &&
        html`<h2 class="group-title" id=${prefix + g.anchor}>
          ${g.op ? html`<${OpBadge} op=${g.op} /> ${g.heading.replace(g.op, "").trim()}` : g.heading}
        </h2>`}
        ${g.body && html`<div class=${g.blocks.length ? "" : "overview-card"}><${Markdown} src=${g.body} prefix=${`${prefix}${g.anchor}--`} /></div>`}
        ${g.blocks.map((b) => html`<${BlockCard} block=${b} prefix=${prefix} />`)}
      </section>`,
    )}
  </div>`;
}

// -- topic tree --

function buildTree(specs) {
  const root = { children: new Map(), spec: null, path: "" };
  for (const s of specs) {
    let node = root;
    for (const seg of s.topic.split("/")) {
      if (!node.children.has(seg)) node.children.set(seg, { children: new Map(), spec: null, path: node.path ? `${node.path}/${seg}` : seg });
      node = node.children.get(seg);
    }
    node.spec = s;
  }
  return root;
}

function TreeNode({ name, node, current }) {
  const kids = [...node.children.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  const s = node.spec;
  return html`<li>
    ${s
      ? html`<a class=${`tree-leaf ${current === s.topic ? "active" : ""}`} href=${href(["specs", s.topic])} title=${s.topic}>
          <span class="tree-name">${name}</span>
          ${s.in_flight.length > 0 && html`<span class="flight-dot" title=${`${s.in_flight.length} active change(s)`}>●</span>`}
          <span class="tree-count">${s.requirement_count}</span>
        </a>`
      : html`<span class="tree-dir">${name}/</span>`}
    ${kids.length > 0 && html`<ul>${kids.map(([n, child]) => html`<${TreeNode} key=${child.path} name=${n} node=${child} current=${current} />`)}</ul>`}
  </li>`;
}

function SpecTree({ specs, current }) {
  const [filter, setFilter] = useState("");
  const f = filter.trim().toLowerCase();
  const shown = f ? specs.filter((s) => s.topic.toLowerCase().includes(f)) : specs;
  const tree = buildTree(shown);
  const top = [...tree.children.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0));
  return html`<aside class="tree-pane">
    <input class="filter" type="search" placeholder="Filter specs" aria-label="Filter specs" value=${filter} onInput=${(e) => setFilter(e.currentTarget.value)} />
    <div class="muted small tree-summary">${shown.length} of ${specs.length} specs</div>
    <ul class="tree">${top.map(([n, child]) => html`<${TreeNode} key=${child.path} name=${n} node=${child} current=${current} />`)}</ul>
  </aside>`;
}

// -- detail tabs --

function HistoryEntry({ topic, h, snap }) {
  const [open, setOpen] = useState(false);
  const change = snap.changes.find((c) => c.slug === h.slug && c.source.key === h.source_key) || { slug: h.slug, source: null };
  const { data, error } = useApi(open ? apiUrl("spec/delta", { topic, slug: h.slug, wt: h.source_key }) : null);
  return html`<li class=${`history-item status-${h.status}`}>
    <div class="history-dot"></div>
    <div class="history-body">
      <div class="history-head">
        <span class="history-date mono">${h.date || "undated"}</span>
        <a href=${changeHref(change, "specs")}>${h.name}</a>
        ${h.status === "active" && html`<${Badge} kind="lane-in_progress">active<//>`}
        ${Object.entries(h.ops).map(([op, n]) => html`<${OpBadge} op=${op} count=${n} />`)}
        <button type="button" class="link-button" onClick=${() => setOpen(!open)} aria-expanded=${open}>${open ? "Hide delta" : "Show delta"}</button>
      </div>
      ${open && (error ? html`<${ErrorBox} error=${error} />` : data ? html`<div class="delta"><${SpecDoc} doc=${data.doc} prefix=${`d-${h.slug}-`} /></div>` : html`<${Loading} />`)}
    </div>
  </li>`;
}

function History({ topic, spec, snap }) {
  if (!spec.history.length) return html`<${Empty}>No change has a delta for this spec.<//>`;
  return html`<ol class="history">${spec.history.map((h) => html`<${HistoryEntry} key=${h.slug + h.source_key} topic=${topic} h=${h} snap=${snap} />`)}</ol>`;
}

function Diff({ topic, spec, query }) {
  const versions = spec.versions;
  const base = query.get("base") || versions[1]?.rev || versions[0]?.rev;
  const head = query.get("head") || "working";
  const { data, error } = useApi(base ? apiUrl("spec/diff", { topic, base, head }) : null);
  if (!versions.length) return html`<${Empty}>No git history for this spec, so there is nothing to compare.<//>`;
  const label = (v) => `${v.date.slice(0, 10)} ${v.rev.slice(0, 7)} ${v.subject}`;
  return html`<div class="diff-view">
    <div class="diff-controls">
      <label>From <select value=${base} onChange=${(e) => setQuery({ base: e.currentTarget.value })}>
        ${versions.map((v) => html`<option value=${v.rev}>${label(v)}</option>`)}
      </select></label>
      <label>To <select value=${head} onChange=${(e) => setQuery({ head: e.currentTarget.value })}>
        <option value="working">Working copy</option>
        ${versions.map((v) => html`<option value=${v.rev}>${label(v)}</option>`)}
      </select></label>
      ${data && html`<span class="diff-stat"><span class="add">+${data.added}</span> <span class="del">-${data.removed}</span></span>`}
    </div>
    ${error ? html`<${ErrorBox} error=${error} />` : !data ? html`<${Loading} />` : data.lines.length === 0 ? html`<${Empty}>No differences.<//>` : html`<pre class="diff">${data.lines.map(
      (l) => html`<div class=${`dl dl-${{ "+": "add", "-": "del", "@": "hunk", " ": "ctx" }[l.t]}`}><span class="dl-sign">${l.t === "@" ? "" : l.t}</span>${l.text}</div>`,
    )}</pre>`}
  </div>`;
}

function SpecDetail({ topic, snap, query }) {
  const { data: spec, error } = useApi(apiUrl("spec", { topic }));
  const tab = query.get("tab") || "spec";
  if (error) return html`<${ErrorBox} error=${error} />`;
  if (!spec) return html`<${Loading} />`;
  const meta = snap.specs.find((s) => s.topic === topic);
  const tabs = [
    { id: "spec", label: "Spec" },
    { id: "history", label: "History", count: spec.history.length },
    { id: "diff", label: "Diff", count: spec.versions.length },
  ];
  return html`<div class="detail">
    <${PageHeader}
      title=${topic}
      sub=${`${spec.doc.requirement_count} requirements${meta?.in_flight.length ? ` · ${meta.in_flight.length} active change(s)` : ""}`}
    />
    <${Chips} options=${tabs} value=${tab} onChange=${(t) => setQuery({ tab: t === "spec" ? "" : t, base: "", head: "" })} />
    ${tab === "spec" &&
    html`<div class="with-toc">
      <div class="doc-col"><${SpecDoc} doc=${spec.doc} /></div>
      <${Toc} items=${docToc(spec.doc)} />
    </div>`}
    ${tab === "history" && html`<${History} topic=${topic} spec=${spec} snap=${snap} />`}
    ${tab === "diff" && html`<${Diff} topic=${topic} spec=${spec} query=${query} />`}
  </div>`;
}

export function SpecsPage({ snap, topic, query }) {
  return html`<div class="split">
    <${SpecTree} specs=${snap.specs} current=${topic} />
    <div class="split-main">
      ${topic
        ? html`<${SpecDetail} key=${topic} topic=${topic} snap=${snap} query=${query} />`
        : html`<${Empty}>${snap.specs.length ? "Pick a spec from the tree." : "No specs in openspec/specs yet."}<//>`}
    </div>
  </div>`;
}
