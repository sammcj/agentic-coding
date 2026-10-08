// Open changes over time and the weekly flow in and out, drawn on the timeline's x scale.
// Counts every dated change whatever the page's status filter: a burndown of a subset misleads.
import { html, useState } from "../lib.js";

export const DAY = 86400000;
const WINDOW_DAYS = 28; // the rate is the last four weeks: long enough to smooth one slow week
const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const OPEN_H = 130;
const FLOW_H = 90;
const PAD = 10;

export const toTime = (d) => new Date(`${d}T00:00:00`).getTime();
// Calendar arithmetic, not +86400000: a DST change makes one day 23 or 25 hours long.
export const midnight = (t) => new Date(t).setHours(0, 0, 0, 0);
// Local YYYY-MM-DD; toISOString would give the UTC date, a day off for much of the world.
export const isoDay = (t) => {
  const d = new Date(t);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
const addDays = (t, n) => {
  const d = new Date(t);
  d.setDate(d.getDate() + n);
  return d.getTime();
};
const nextDay = (t) => addDays(t, 1);
const dayLabel = (t) => {
  const d = new Date(t);
  return `${d.getDate()} ${MONTHS[d.getMonth()]} ${d.getFullYear()}`;
};

// A change is open from its created day through its archive day.
function openSeries(changes) {
  const deltas = new Map();
  const bump = (t, n) => deltas.set(t, (deltas.get(t) || 0) + n);
  for (const c of changes) {
    if (!c.created) continue;
    bump(toTime(c.created), 1);
    if (c.archived) bump(nextDay(toTime(c.archived)), -1);
  }
  let open = 0;
  return [...deltas.entries()].sort(([a], [b]) => a - b).map(([t, n]) => ({ t, open: (open += n) }));
}

const openAt = (series, t) => {
  let v = 0;
  for (const p of series) {
    if (p.t > t) break;
    v = p.open;
  }
  return v;
};

function binStart(t, monthly) {
  const d = new Date(t);
  if (monthly) d.setDate(1);
  else d.setDate(d.getDate() - ((d.getDay() + 6) % 7)); // Monday
  return d.getTime();
}

function nextBin(t, monthly) {
  const d = new Date(t);
  if (monthly) d.setMonth(d.getMonth() + 1);
  else d.setDate(d.getDate() + 7);
  return d.getTime();
}

function flowBins(changes, monthly) {
  const bins = new Map();
  const add = (date, key) => {
    const t = binStart(toTime(date), monthly);
    const b = bins.get(t) || { t, opened: 0, archived: 0 };
    b[key] += 1;
    bins.set(t, b);
  };
  for (const c of changes) {
    if (!c.created) continue;
    add(c.created, "opened");
    if (c.archived) add(c.archived, "archived");
  }
  return [...bins.values()];
}

export function burndownStats(changes, today) {
  const from = addDays(today, 1 - WINDOW_DAYS);
  const inWindow = (d) => d && toTime(d) >= from && toTime(d) <= today;
  const archivedPerWeek = (changes.filter((c) => inWindow(c.archived)).length * 7) / WINDOW_DAYS;
  const openedPerWeek = (changes.filter((c) => inWindow(c.created)).length * 7) / WINDOW_DAYS;
  const openNow = changes.filter((c) => c.status === "active").length;
  const net = archivedPerWeek - openedPerWeek;
  const weeks = net > 0 ? openNow / net : null;
  return { openNow, archivedPerWeek, openedPerWeek, net, weeks, clearBy: weeks === null ? null : addDays(today, Math.ceil(weeks * 7)) };
}

const fmtRate = (n) => (Math.round(n * 10) / 10).toString();

function niceMax(v) {
  if (v <= 4) return Math.max(1, v);
  const step = 10 ** Math.floor(Math.log10(v));
  return Math.ceil(v / (step / 2)) * (step / 2);
}

function StatTiles({ s }) {
  const clear = s.openNow === 0
    ? { value: "Clear", sub: "no open changes" }
    : s.clearBy === null
      ? { value: "Not burning down", sub: "opening as fast as archiving" }
      : { value: dayLabel(s.clearBy), sub: `~${Math.ceil(s.weeks)} wk at net ${fmtRate(s.net)}/wk` };
  return html`<div class="stats">
    <div class="stat"><div class="stat-label">Open now</div><div class="stat-value">${s.openNow}</div></div>
    <div class="stat"><div class="stat-label">Archived / week</div><div class="stat-value">${fmtRate(s.archivedPerWeek)}</div><div class="stat-sub">last 4 weeks</div></div>
    <div class="stat"><div class="stat-label">Opened / week</div><div class="stat-value">${fmtRate(s.openedPerWeek)}</div><div class="stat-sub">last 4 weeks</div></div>
    <div class="stat"><div class="stat-label">Projected clear</div><div class="stat-value">${clear.value}</div><div class="stat-sub">${clear.sub}</div></div>
  </div>`;
}

export function Burndown({ changes, start, end, today, x, width, labelW, grid }) {
  const [hover, setHover] = useState(null);
  const series = openSeries(changes);
  const stats = burndownStats(changes, today);
  const last = nextDay(today);
  const plotW = x(end) - x(start);
  const monthly = (end - start) / DAY > 400;

  // -- open changes, a step area --
  const yMax = niceMax(Math.max(1, ...series.map((p) => p.open)));
  const y = (v) => PAD + (1 - v / yMax) * (OPEN_H - 2 * PAD);
  let d = `M${x(start)},${y(openAt(series, start))}`;
  for (const p of series) if (p.t > start && p.t <= last) d += `H${x(p.t)}V${y(p.open)}`;
  d += `H${x(last)}`;
  const area = `${d}V${y(0)}H${x(start)}Z`;

  const onMove = (e) => {
    const box = e.currentTarget.getBoundingClientRect();
    const t = start + ((e.clientX - box.left - labelW) / plotW) * (end - start);
    setHover(t < start || t >= last ? null : midnight(t));
  };
  const hoverX = hover === null ? 0 : x(hover);
  const hoverOpen = hover === null ? 0 : openAt(series, hover);

  // -- flow: opened up, archived down, one shared scale --
  const bins = flowBins(changes, monthly).filter((b) => b.t >= binStart(start, monthly) && b.t <= last);
  const fMax = niceMax(Math.max(1, ...bins.map((b) => Math.max(b.opened, b.archived))));
  const mid = FLOW_H / 2;
  const fy = (v) => ((mid - PAD / 2) * v) / fMax;
  const unit = monthly ? "month" : "week";

  return html`<section class="burndown">
    <${StatTiles} s=${stats} />
    <svg class="bd-chart" width=${width} height=${OPEN_H} role="img" aria-label="Open changes over time"
      onMouseMove=${onMove} onMouseLeave=${() => setHover(null)}>
      ${grid.map((g) => g >= start && html`<line class="tl-grid" x1=${x(g)} x2=${x(g)} y1="0" y2=${OPEN_H} />`)}
      <text class="bd-title" x="4" y="16">Open changes</text>
      ${[0, yMax / 2, yMax].map((v) => html`<g>
        <line class="bd-hgrid" x1=${labelW} x2=${labelW + plotW} y1=${y(v)} y2=${y(v)} />
        <text class="tl-tick" x=${labelW - 6} y=${y(v) + 4} text-anchor="end">${Number.isInteger(v) ? v : ""}</text>
      </g>`)}
      <path class="bd-area" d=${area} />
      <path class="bd-line" d=${d} />
      ${hover !== null && html`<g class="bd-hover">
        <line x1=${hoverX} x2=${hoverX} y1="0" y2=${OPEN_H} />
        <circle cx=${hoverX} cy=${y(hoverOpen)} r="4" />
        <text x=${hoverX + (hoverX > labelW + plotW - 140 ? -8 : 8)} y="16" text-anchor=${hoverX > labelW + plotW - 140 ? "end" : "start"}>${dayLabel(hover)} · ${hoverOpen} open</text>
      </g>`}
    </svg>
    <svg class="bd-chart" width=${width} height=${FLOW_H} role="img" aria-label=${`Changes opened and archived per ${unit}`}>
      ${grid.map((g) => g >= start && html`<line class="tl-grid" x1=${x(g)} x2=${x(g)} y1="0" y2=${FLOW_H} />`)}
      <text class="bd-title" x="4" y="16">Per ${unit}</text>
      <text class="tl-tick" x=${labelW - 6} y=${mid - fy(fMax) + 4} text-anchor="end">+${fMax}</text>
      <text class="tl-tick" x=${labelW - 6} y=${mid + fy(fMax) + 4} text-anchor="end">-${fMax}</text>
      ${bins.map((b) => {
        const bx = x(Math.max(b.t, start)) + 1;
        const bw = Math.max(2, x(Math.min(nextBin(b.t, monthly), end)) - bx - 2);
        return html`<g class="bd-bin">
          <title>${`${unit === "week" ? "Week of" : "Month of"} ${dayLabel(b.t)}: ${b.opened} opened, ${b.archived} archived`}</title>
          <rect class="bd-hit" x=${bx - 1} y="0" width=${bw + 2} height=${FLOW_H} />
          ${b.opened > 0 && html`<rect class="lane-fill-planned" x=${bx} y=${mid - 1 - fy(b.opened)} width=${bw} height=${fy(b.opened)} rx="2" />`}
          ${b.archived > 0 && html`<rect class="lane-fill-archived" x=${bx} y=${mid + 1} width=${bw} height=${fy(b.archived)} rx="2" />`}
        </g>`;
      })}
      <line class="bd-axis" x1=${labelW} x2=${labelW + plotW} y1=${mid} y2=${mid} />
    </svg>
    <div class="legend small">
      <span class="legend-item"><span class="legend-swatch bd-swatch-open"></span>Open changes</span>
      <span class="legend-item"><span class="legend-swatch lane-fill-planned"></span>Opened (up)</span>
      <span class="legend-item"><span class="legend-swatch lane-fill-archived"></span>Archived (down)</span>
    </div>
  </section>`;
}
