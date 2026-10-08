import { changeHref, href, html, relative } from "../lib.js";
import { Badge, LANES, Progress, SourceBadge } from "../ui.js";

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

function SpecsInFlight({ snap }) {
  const specs = snap.specs.filter((s) => s.in_flight.length);
  const known = new Set(snap.specs.map((s) => s.topic));
  const added = [...new Set(snap.changes.filter((c) => c.status === "active").flatMap((c) => c.spec_topics))].filter(
    (t) => !known.has(t),
  );
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
        const cs = snap.changes.filter((c) => c.status === "active" && c.spec_topics.includes(topic));
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

export function Dashboard({ snap }) {
  const s = snap.stats;
  const pct = s.tasks_total ? Math.round((100 * s.tasks_done) / s.tasks_total) : null;
  return html`<div class="page">
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
