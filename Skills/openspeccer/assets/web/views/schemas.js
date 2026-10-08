// Workflow schemas: catalogue and the artifact dependency graph of one schema.
import { apiUrl, href, html, useApi, useState } from "../lib.js";
import { Badge, Empty, ErrorBox, Loading, PageHeader } from "../ui.js";

export function SchemaList() {
  const { data, error } = useApi(apiUrl("schemas"));
  if (error) return html`<${ErrorBox} error=${error} />`;
  if (!data) return html`<${Loading} />`;
  return html`<div class="page">
    <${PageHeader} title="Schemas" sub="Workflow schemas resolvable from this repo" />
    ${data.degraded && html`<div class="notice">${data.degraded}</div>`}
    ${data.schemas.length === 0 && html`<${Empty}>No schemas found.<//>`}
    <div class="card-grid">
      ${data.schemas.map(
        (s) => html`<a class="card schema-card" href=${href(["schemas", s.name])}>
          <div class="card-title">${s.name}</div>
          <div class="card-meta">
            <${Badge} kind="source">${s.source}<//>
            ${s.is_default && html`<${Badge} kind="lane-ready">default<//>`}
          </div>
          <p class="small">${s.description}</p>
          <div class="card-foot muted small">${s.artifact_count} artifacts · ${s.active_changes} active change${s.active_changes === 1 ? "" : "s"}</div>
        </a>`,
      )}
    </div>
    ${Object.keys(data.unresolved).length > 0 &&
    html`<div class="notice">
      Active changes name schemas that do not resolve here:
      ${Object.entries(data.unresolved).map(([n, c]) => html` <span class="mono">${n}</span> (${c})`)}
    </div>`}
  </div>`;
}

const NODE_W = 168;
const NODE_H = 48;
const COL = 210;
const ROW_H = 76;
const PAD = 24;

function Graph({ schema, selected, onSelect }) {
  const nodes = schema.nodes;
  const pos = new Map(nodes.map((n) => [n.key, { x: PAD + n.level * COL, y: PAD + n.row * ROW_H }]));
  const levels = Math.max(...nodes.map((n) => n.level)) + 1;
  const rows = Math.max(...nodes.map((n) => n.row)) + 1;
  const w = PAD * 2 + (levels - 1) * COL + NODE_W;
  const h = PAD * 2 + (rows - 1) * ROW_H + NODE_H + 18;
  const related = new Set();
  if (selected) {
    related.add(selected);
    for (const e of schema.edges) if (e.source === selected || e.target === selected) related.add(e.source).add(e.target);
  }
  return html`<svg class="dag" viewBox=${`0 0 ${w} ${h}`} width=${w} height=${h} role="img" aria-label=${`Dependency graph of ${schema.name}`}>
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0,0 L10,5 L0,10 z" class="dag-arrow" />
      </marker>
    </defs>
    ${schema.edges.map((e) => {
      const a = pos.get(e.source);
      const b = pos.get(e.target);
      const x1 = a.x + NODE_W, y1 = a.y + NODE_H / 2, x2 = b.x - 2, y2 = b.y + NODE_H / 2;
      const mx = (x1 + x2) / 2;
      const dim = selected && !(related.has(e.source) && related.has(e.target));
      return html`<g class=${`dag-edge ${e.derived ? "derived" : ""} ${dim ? "dim" : ""}`}>
        <path d=${`M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`} marker-end="url(#arrow)" />
        ${e.derived && html`<text class="dag-edge-label" x=${mx} y=${(y1 + y2) / 2 - 6} text-anchor="middle">derived</text>`}
      </g>`;
    })}
    ${nodes.map((n) => {
      const p = pos.get(n.key);
      const dim = selected && !related.has(n.key);
      return html`<g class=${`dag-node kind-${n.kind} ${n.derived ? "derived" : ""} ${selected === n.key ? "selected" : ""} ${dim ? "dim" : ""}`}
        transform=${`translate(${p.x},${p.y})`} tabindex="0" role="button" aria-label=${n.label}
        onClick=${() => onSelect(selected === n.key ? null : n.key)}
        onKeyDown=${(e) => (e.key === "Enter" || e.key === " ") && onSelect(selected === n.key ? null : n.key)}>
        <rect width=${NODE_W} height=${NODE_H} rx="6" />
        <text class="dag-label" x="12" y="20">${n.label}</text>
        <text class="dag-sub" x="12" y="37">${(n.generates || "").slice(0, 24)}</text>
      </g>`;
    })}
  </svg>`;
}

function NodePanel({ schema, nodeKey }) {
  const n = schema.nodes.find((x) => x.key === nodeKey);
  if (!n) return html`<aside class="dag-panel muted small">Select a step to see what it produces and needs.</aside>`;
  return html`<aside class="dag-panel">
    <h2 class="panel-title">${n.label} ${n.kind === "apply" && html`<${Badge} kind="lane-ready">implementation<//>`}</h2>
    ${n.generates && html`<div class="small"><span class="muted">${n.kind === "apply" ? "Tracks" : "Generates"}</span> <span class="mono">${n.generates}</span></div>`}
    <div class="small"><span class="muted">Requires</span> ${n.requires.length ? n.requires.map((r) => html`<span class="badge">${r}</span> `) : "nothing"}</div>
    ${n.description && html`<p class="small">${n.description}</p>`}
    ${n.derived && html`<p class="small notice">Placed after implementation by inference: it depends on everything apply needs, and apply does not need it. OpenSpec cannot declare this ordering, so the dashed edge is derived, not a dependency the CLI enforces.</p>`}
  </aside>`;
}

export function SchemaDetail({ name }) {
  const { data, error } = useApi(apiUrl("schema", { name }));
  const [selected, setSelected] = useState(null);
  if (error) return html`<${ErrorBox} error=${error} />`;
  if (!data) return html`<${Loading} />`;
  return html`<div class="detail">
    <${PageHeader} title=${data.name} sub=${`${data.source} schema · ${data.nodes.length - 1} artifacts · tracks ${data.tracks}`} back="#/schemas" />
    ${data.description && html`<p>${data.description}</p>`}
    <div class="dag-wrap">
      <div class="dag-scroll"><${Graph} schema=${data} selected=${selected} onSelect=${setSelected} /></div>
      <${NodePanel} schema=${data} nodeKey=${selected} />
    </div>
    <div class="legend small">
      <span class="legend-item"><svg width="28" height="8"><line x1="0" y1="4" x2="28" y2="4" class="legend-line" /></svg>requires</span>
      <span class="legend-item"><svg width="28" height="8"><line x1="0" y1="4" x2="28" y2="4" class="legend-line derived" /></svg>derived: runs after implementation</span>
      <span class="muted">Edges implied by a longer path are omitted.</span>
    </div>
    <div class="muted small mono">${data.path}</div>
  </div>`;
}
