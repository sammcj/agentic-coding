import { changeHref, href, html, relative } from "../lib.js";
import { ExportMenu, mdTable } from "../export.js";
import { Badge, LANES, PageHeader, Progress, SourceBadge } from "../ui.js";

const RECENT_ARCHIVED = 8;

function Stat({ label, value, sub, link }) {
  const body = html`<div class="stat-value">${value}</div>
    <div class="stat-label">${label}</div>
    ${sub && html`<div class="stat-sub">${sub}</div>`}`;
  return link ? html`<a class="stat" href=${link}>${body}</a>` : html`<div class="stat">${body}</div>`;
}

export function ChangeCard({ c, defaultSchema }) {
  return html`<a class=${`card change-card lane-edge-${c.lane}`} href=${changeHref(c)}>
    <div class="card-title">${c.name}</div>
    <div class="card-meta">
      ${c.schema && c.schema !== defaultSchema && html`<${Badge} kind="schema">${c.schema}<//>`}
      <${SourceBadge} source=${c.source} />
      ${c.variants > 1 && html`<${Badge} kind="warn" title="Working copies hold different versions of this change">${c.variants} versions<//>`}
    </div>
    ${c.status === "active" && c.tasks && html`<${Progress} done=${c.tasks.done} total=${c.tasks.total} />`}
    <div class="card-foot muted small">
      ${c.status === "archived" ? `archived ${c.archived}` : `updated ${relative(c.updated)}`}
      ${c.spec_topics.length ? ` · ${c.spec_topics.length} spec${c.spec_topics.length > 1 ? "s" : ""}` : ""}
    </div>
  </a>`;
}

function Board({ snap }) {
  const lanes = LANES.map((lane) => {
    let items = snap.changes.filter((c) => c.lane === lane.id);
    let more = 0;
    if (lane.id === "archived") {
      more = Math.max(0, items.length - RECENT_ARCHIVED);
      items = items.slice(0, RECENT_ARCHIVED);
    }
    return { ...lane, items, more, total: items.length + more };
  });
  return html`<section class="board" aria-label="Changes by stage">
    ${lanes.map(
      (lane) => html`<div class=${`lane lane-col-${lane.id}`}>
        <div class="lane-head">
          <span class=${`lane-dot lane-${lane.id}`}></span>
          <span class="lane-title">${lane.id === "archived" ? "Recently archived" : lane.label}</span>
          <span class="lane-count">${lane.total}</span>
        </div>
        <div class="lane-body">
          ${lane.items.length === 0 && html`<div class="lane-empty muted small">None</div>`}
          ${lane.items.map((c) => html`<${ChangeCard} key=${c.slug + c.source.key} c=${c} defaultSchema=${snap.default_schema} />`)}
          ${lane.more > 0 && html`<a class="lane-more small" href=${href(["changes"], { status: "archived" })}>${lane.more} more archived</a>`}
        </div>
      </div>`,
    )}
  </section>`;
}

// Spec topics that active changes add but openspec/specs does not have yet.
function newTopics(snap) {
  const known = new Set(snap.specs.map((s) => s.topic));
  return [...new Set(snap.changes.filter((c) => c.status === "active").flatMap((c) => c.spec_topics))].filter((t) => !known.has(t));
}

const changesAdding = (snap, topic) => snap.changes.filter((c) => c.status === "active" && c.spec_topics.includes(topic));

function SpecsInFlight({ snap }) {
  const specs = snap.specs.filter((s) => s.in_flight.length);
  const added = newTopics(snap);
  if (!specs.length && !added.length) return null;
  const byChange = new Map(snap.changes.map((c) => [c.slug, c]));
  return html`<section class="panel">
    <h2 class="panel-title">Specs in flight</h2>
    <ul class="flight-list">
      ${specs.map(
        (s) => html`<li>
          <a class="mono" href=${href(["specs", s.topic])}>${s.topic}</a>
          <span class="muted small"> ${s.requirement_count} req</span>
          <span class="flight-changes">
            ${s.in_flight.map((slug) => {
              const c = byChange.get(slug);
              return c ? html`<a class="badge change-ref" href=${changeHref(c, "specs")}>${c.name}</a>` : null;
            })}
          </span>
        </li>`,
      )}
      ${added.map((topic) => {
        const cs = changesAdding(snap, topic);
        return html`<li>
          <span class="mono">${topic}</span> <${Badge} kind="op op-added">new<//>
          <span class="flight-changes">
            ${cs.map((c) => html`<a class="badge change-ref" href=${changeHref(c, "specs")}>${c.name}</a>`)}
          </span>
        </li>`;
      })}
    </ul>
  </section>`;
}

const tasksPct = (s) => (s.tasks_total ? Math.round((100 * s.tasks_done) / s.tasks_total) : null);

export function dashboardMarkdown(snap) {
  const s = snap.stats;
  const pct = tasksPct(s);
  const out = [
    `# ${snap.repo.name} dashboard`,
    "",
    mdTable(
      ["Metric", "Value"],
      [
        ["Specs", `${s.specs} (${s.requirements} requirements)`],
        ["Active changes", s.active],
        ["Active tasks", pct === null ? "no tasks yet" : `${pct}% (${s.tasks_done} of ${s.tasks_total} done)`],
        ["Archived", s.archived],
        ["Avg lifecycle", s.avg_lifecycle_days === null ? "-" : `${s.avg_lifecycle_days}d`],
        ["Stale (active, untouched 30d+)", s.stale],
      ],
    ),
  ];
  for (const lane of LANES) {
    const all = snap.changes.filter((c) => c.lane === lane.id);
    // Like the board: only the most recent archived changes.
    const items = lane.id === "archived" ? all.slice(0, RECENT_ARCHIVED) : all;
    out.push("", `## ${lane.id === "archived" ? "Recently archived" : lane.label} (${all.length})`, "");
    if (!items.length) out.push("None");
    for (const c of items) {
      const when = c.status === "archived" ? `archived ${c.archived}` : `updated ${(c.updated || "").slice(0, 10)}`;
      const tasks = c.status === "active" && c.tasks ? `, tasks ${c.tasks.done}/${c.tasks.total}` : "";
      out.push(`- ${c.name} (${when}${tasks})`);
    }
    if (all.length > items.length) out.push(`- ${all.length - items.length} more archived`);
  }
  const rows = [
    ...snap.specs.filter((sp) => sp.in_flight.length).map((sp) => [sp.topic, sp.requirement_count, sp.in_flight.join(", ")]),
    ...newTopics(snap).map((t) => [`${t} (new)`, "", changesAdding(snap, t).map((c) => c.slug).join(", ")]),
  ];
  if (rows.length) out.push("", "## Specs in flight", "", mdTable(["Spec", "Requirements", "Changes"], rows));
  return `${out.join("\n")}\n`;
}

export function Dashboard({ snap }) {
  const s = snap.stats;
  const pct = tasksPct(s);
  return html`<div class="page">
    <${PageHeader} title="Dashboard" sub=${snap.repo.name}>
      <${ExportMenu} name=${`${snap.repo.name}-dashboard`} title=${`${snap.repo.name} dashboard`} markdown=${() => dashboardMarkdown(snap)} />
    <//>
    ${!snap.changes.length && html`<p class="guide-hint">No changes yet. New to OpenSpec? Start with the <a href="#/guide">Guide</a>.</p>`}
    <section class="stats">
      <${Stat} label="Specs" value=${s.specs} sub=${`${s.requirements} requirements`} link="#/specs" />
      <${Stat} label="Active changes" value=${s.active} link=${href(["changes"], { status: "active" })} />
      <${Stat}
        label="Active tasks"
        value=${pct === null ? "-" : `${pct}%`}
        sub=${s.tasks_total ? `${s.tasks_done} of ${s.tasks_total} done` : "no tasks yet"}
      />
      <${Stat} label="Archived" value=${s.archived} link=${href(["changes"], { status: "archived" })} />
      <${Stat} label="Avg lifecycle" value=${s.avg_lifecycle_days === null ? "-" : `${s.avg_lifecycle_days}d`} sub="created to archived" link="#/timeline" />
      <${Stat} label="Stale" value=${s.stale} sub="active, untouched 30d+" />
    </section>
    <${Board} snap=${snap} />
    <${SpecsInFlight} snap=${snap} />
  </div>`;
}
