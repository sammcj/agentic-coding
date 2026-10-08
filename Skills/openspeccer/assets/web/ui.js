// Small presentational pieces shared across views.
import { html } from "./lib.js";

export const LANES = [
  { id: "proposed", label: "Proposed" },
  { id: "planned", label: "Planned" },
  { id: "in_progress", label: "In progress" },
  { id: "ready", label: "Ready to archive" },
  { id: "archived", label: "Archived" },
];
export const laneLabel = (id) => LANES.find((l) => l.id === id)?.label ?? id;

export function LaneBadge({ lane }) {
  return html`<span class=${`badge lane-${lane}`}>${laneLabel(lane)}</span>`;
}

export function Badge({ children, kind = "", title }) {
  return html`<span class=${`badge ${kind}`} title=${title}>${children}</span>`;
}

export function OpBadge({ op, count }) {
  return html`<span class=${`badge op op-${op.toLowerCase()}`}>${op}${count ? ` ${count}` : ""}</span>`;
}

export function Progress({ done, total, wide = false }) {
  if (!total) return html`<span class="muted small">no tasks</span>`;
  const pct = Math.round((100 * done) / total);
  return html`<span class=${`progress ${wide ? "wide" : ""}`} title=${`${done} of ${total} tasks (${pct}%)`}>
    <span class="progress-track"><span class=${`progress-fill ${done === total ? "complete" : ""}`} style=${`width:${pct}%`}></span></span>
    <span class="progress-label">${done}/${total}</span>
  </span>`;
}

export function SourceBadge({ source }) {
  if (!source || source.is_main) return null;
  return html`<${Badge} kind="source" title=${`From ${source.vcs} working copy ${source.label}`}>@${source.label}<//>`;
}

export function Loading({ what = "Loading" }) {
  return html`<div class="state muted">${what}...</div>`;
}

export function ErrorBox({ error }) {
  return html`<div class="state error">${String(error?.message || error)}</div>`;
}

export function Empty({ children }) {
  return html`<div class="state muted">${children}</div>`;
}

export function Chips({ options, value, onChange }) {
  return html`<div class="chips" role="group">
    ${options.map(
      (o) => html`<button type="button" class=${`chip ${value === o.id ? "on" : ""}`} aria-pressed=${value === o.id} onClick=${() => onChange(o.id)}>
        ${o.label}${o.count !== undefined ? html` <span class="chip-count">${o.count}</span>` : ""}
      </button>`,
    )}
  </div>`;
}

export function Select({ label, value, options, onChange }) {
  return html`<label class="select">
    <span>${label}</span>
    <select value=${value} onChange=${(e) => onChange(e.currentTarget.value)}>
      ${options.map((o) => html`<option value=${o.id}>${o.label}</option>`)}
    </select>
  </label>`;
}

export function PageHeader({ title, sub, children, back }) {
  return html`<header class="page-header">
    ${back && html`<a class="back" href=${back} title="Back">←</a>`}
    <div class="page-title">
      <h1>${title}</h1>
      ${sub && html`<div class="page-sub">${sub}</div>`}
    </div>
    ${children && html`<div class="page-actions">${children}</div>`}
  </header>`;
}
