// Change lifecycles as bars on a shared time axis: created -> archived (or today).
import { ExportMenu, mdTable } from "../export.js";
import { changeHref, html, setQuery, useRef, useWidth } from "../lib.js";
import { Chips, Empty, PageHeader, laneLabel } from "../ui.js";
import { Burndown, DAY, burndownStats, isoDay, midnight, toTime } from "./burndown.js";

const ROW = 24;
const LABEL_W = 240;
const AXIS_H = 28;
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

const spanDays = (c, today) => Math.max(1, Math.round(((c.archived ? toTime(c.archived) : today) + DAY - toTime(c.created)) / DAY));

function timelineMarkdown(repoName, all, dated, today) {
  const s = burndownStats(all, today);
  const r = (n) => Math.round(n * 10) / 10;
  const clear = s.openNow === 0 ? "clear" : s.clearBy === null ? "not burning down" : isoDay(s.clearBy);
  return [
    `# ${repoName} timeline`,
    "",
    `- Open now: ${s.openNow}`,
    `- Archived per week (last 4 weeks): ${r(s.archivedPerWeek)}`,
    `- Opened per week (last 4 weeks): ${r(s.openedPerWeek)}`,
    `- Projected clear: ${clear}`,
    "",
    mdTable(
      ["Change", "Stage", "Created", "Archived", "Days"],
      dated.map((c) => [c.name, laneLabel(c.lane), c.created, c.archived || "", spanDays(c, today)]),
    ),
    "",
  ].join("\n");
}

function ticks(start, end) {
  const out = [];
  const spanDays = (end - start) / DAY;
  const d = new Date(start);
  if (spanDays <= 60) {
    d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); // Monday
    for (; d.getTime() <= end; d.setDate(d.getDate() + 7)) out.push({ t: d.getTime(), label: `${d.getDate()} ${MONTHS[d.getMonth()]}` });
  } else {
    d.setDate(1);
    const step = spanDays > 730 ? 3 : 1;
    for (; d.getTime() <= end; d.setMonth(d.getMonth() + step)) {
      out.push({ t: d.getTime(), label: d.getMonth() === 0 || !out.length ? `${MONTHS[d.getMonth()]} ${d.getFullYear()}` : MONTHS[d.getMonth()] });
    }
  }
  return out;
}

export function Timeline({ snap, query }) {
  const status = query.get("status") || "all";
  const group = query.get("group") === "spec";
  const ref = useRef(null);
  const width = useWidth(ref);

  const changes = snap.changes.filter((c) => status === "all" || c.status === status);
  const dated = changes.filter((c) => c.created).sort((a, b) => a.created.localeCompare(b.created) || a.name.localeCompare(b.name));
  const undated = changes.length - dated.length;
  if (!dated.length) {
    return html`<div class="page" ref=${ref}>
      <${PageHeader} title="Timeline" />
      <${Empty}>No changes with a created date. Dates come from .openspec.yaml or the first git commit.<//>
    </div>`;
  }

  const today = midnight(Date.now());
  const start = Math.min(...dated.map((c) => toTime(c.created))) - DAY;
  const end = Math.max(today, ...dated.map((c) => (c.archived ? toTime(c.archived) : today))) + DAY;
  const plotW = Math.max(200, width - LABEL_W - 16);
  const x = (t) => LABEL_W + ((t - start) / (end - start)) * plotW;

  const rows = [];
  if (group) {
    const topics = new Map();
    for (const c of dated) for (const t of c.spec_topics.length ? c.spec_topics : ["(no spec deltas)"]) {
      if (!topics.has(t)) topics.set(t, []);
      topics.get(t).push(c);
    }
    for (const [t, cs] of [...topics.entries()].sort(([a], [b]) => (a < b ? -1 : 1))) {
      rows.push({ header: t });
      for (const c of cs) rows.push({ change: c });
    }
  } else {
    for (const c of dated) rows.push({ change: c });
  }
  const height = AXIS_H + rows.length * ROW + 8;
  const grid = ticks(start, end).map((t) => t.t);

  return html`<div class="page" ref=${ref}>
    <${PageHeader} title="Timeline" sub=${`${dated.length} changes${undated ? ` · ${undated} without a date not shown` : ""}`}>
      <${ExportMenu} name=${`${snap.repo.name}-timeline`} title=${`${snap.repo.name} timeline`} markdown=${() => timelineMarkdown(snap.repo.name, snap.changes, dated, today)} />
    <//>
    <${Burndown} changes=${snap.changes} start=${start} end=${end} today=${today} x=${x} width=${width} labelW=${LABEL_W} grid=${grid} />
    <h2 class="panel-title">Lifecycles</h2>
    <div class="toolbar">
      <${Chips}
        options=${[{ id: "all", label: "All" }, { id: "active", label: "Active" }, { id: "archived", label: "Archived" }]}
        value=${status}
        onChange=${(s) => setQuery({ status: s === "all" ? "" : s })}
      />
      <${Chips}
        options=${[{ id: "flat", label: "By start date" }, { id: "spec", label: "Group by spec" }]}
        value=${group ? "spec" : "flat"}
        onChange=${(g) => setQuery({ group: g === "spec" ? "spec" : "" })}
      />
    </div>
    <svg class="timeline" width=${width} height=${height} role="img" aria-label="Change lifecycles over time">
      ${ticks(start, end).map((t) => {
        // A tick before the range keeps its label at the left edge; one under "today" drops it.
        const tx = Math.max(LABEL_W, x(t.t));
        const nearToday = Math.abs(tx - x(today)) < 48;
        return html`<g>
          ${t.t >= start && html`<line class="tl-grid" x1=${tx} x2=${tx} y1=${AXIS_H - 6} y2=${height} />`}
          ${!nearToday && html`<text class="tl-tick" x=${tx + 3} y=${AXIS_H - 10}>${t.label}</text>`}
        </g>`;
      })}
      <line class="tl-today" x1=${x(today)} x2=${x(today)} y1=${AXIS_H - 6} y2=${height} />
      <text class="tl-today-label" x=${x(today) - 3} y=${AXIS_H - 10} text-anchor="end">today</text>
      ${rows.map((r, i) => {
        const y = AXIS_H + i * ROW;
        if (r.header) return html`<text class="tl-group" x="4" y=${y + 16}>${r.header}</text>`;
        const c = r.change;
        const s = toTime(c.created);
        const e = c.archived ? toTime(c.archived) + DAY : today + DAY;
        const days = spanDays(c, today);
        const tip = `${c.name}\n${laneLabel(c.lane)} · ${c.created} -> ${c.archived || "now"} (${days}d)`;
        return html`<a href=${changeHref(c)} class="tl-row">
          <title>${tip}</title>
          <rect class="tl-hit" x="0" y=${y} width=${width} height=${ROW} />
          <text class="tl-label" x=${group ? 16 : 4} y=${y + 16}>${c.name.length > 30 ? `${c.name.slice(0, 29)}…` : c.name}</text>
          <rect class=${`tl-bar lane-fill-${c.lane}`} x=${x(s)} y=${y + 5} width=${Math.max(4, x(e) - x(s))} height=${ROW - 10} rx="3" />
        </a>`;
      })}
    </svg>
    <div class="legend small">
      ${["proposed", "planned", "in_progress", "ready", "archived"].map(
        (l) => html`<span class="legend-item"><span class=${`legend-swatch lane-fill-${l}`}></span>${laneLabel(l)}</span>`,
      )}
    </div>
  </div>`;
}
