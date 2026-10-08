import { apiUrl, changeHref, href, html, pref, relative, setPref, setQuery, useApi, useState } from "../lib.js";
import { Markdown, Toc, headings } from "../md.js";
import { ExportMenu, mdTable } from "../export.js";
import { Badge, Chips, Empty, ErrorBox, LANES, LaneBadge, Loading, PageHeader, Progress, Select, SourceBadge, laneLabel } from "../ui.js";
import { SpecDoc, docToc } from "./specs.js";

// -- list --

const SORTS = [
  { id: "updated", label: "Last updated" },
  { id: "created", label: "Created" },
  { id: "name", label: "Name" },
  { id: "progress", label: "Task progress" },
];

const sorters = {
  updated: (a, b) => (b.archived || b.updated).localeCompare(a.archived || a.updated),
  created: (a, b) => (b.created || "").localeCompare(a.created || ""),
  name: (a, b) => (a.name < b.name ? -1 : a.name > b.name ? 1 : 0),
  progress: (a, b) => ratio(b) - ratio(a),
};
const ratio = (c) => (c.tasks?.total ? c.tasks.done / c.tasks.total : -1);

function changeListMarkdown(repoName, rows, status) {
  return [
    `# ${repoName} changes (${status})`,
    "",
    mdTable(
      ["Change", "Status", "Stage", "Schema", "Tasks", "Created", "Updated", "Archived"],
      rows.map((c) => [c.name, c.status, laneLabel(c.lane), c.schema || "", c.tasks ? `${c.tasks.done}/${c.tasks.total}` : "", c.created || "", (c.updated || "").slice(0, 10), c.archived || ""]),
    ),
    "",
  ].join("\n");
}

export function ChangeList({ snap, query }) {
  const status = query.get("status") || "all";
  const lane = query.get("lane") || "";
  const sort = query.get("sort") || "updated";
  const [filter, setFilter] = useState("");
  const f = filter.trim().toLowerCase();
  let rows = snap.changes.filter((c) => status === "all" || c.status === status);
  if (lane) rows = rows.filter((c) => c.lane === lane);
  if (f) rows = rows.filter((c) => c.slug.toLowerCase().includes(f) || (c.schema || "").includes(f) || c.spec_topics.some((t) => t.includes(f)));
  // Active first, so the archived group follows its divider whatever the sort.
  rows = [...rows].sort((a, b) => (a.status === b.status ? 0 : a.status === "active" ? -1 : 1) || (sorters[sort] || sorters.updated)(a, b));
  const firstArchived = status === "all" ? rows.findIndex((c) => c.status === "archived") : -1;
  const count = (s) => snap.changes.filter((c) => s === "all" || c.status === s).length;
  const lanes = [{ id: "", label: "Any stage" }, ...LANES.filter((l) => l.id !== "archived")];
  return html`<div class="page">
    <${PageHeader} title="Changes" sub=${`${rows.length} shown`}>
      <${ExportMenu} name=${`${snap.repo.name}-changes`} title=${`${snap.repo.name} changes`} markdown=${() => changeListMarkdown(snap.repo.name, rows, status)} />
    <//>
    <div class="toolbar">
      <${Chips}
        options=${[
          { id: "active", label: "Active", count: count("active") },
          { id: "archived", label: "Archived", count: count("archived") },
          { id: "all", label: "All", count: count("all") },
        ]}
        value=${status}
        onChange=${(s) => setQuery({ status: s === "all" ? "" : s, lane: "" })}
      />
      ${status !== "archived" && html`<${Select} label="Stage" value=${lane} options=${lanes} onChange=${(v) => setQuery({ lane: v })} />`}
      <${Select} label="Sort" value=${sort} options=${SORTS} onChange=${(v) => setQuery({ sort: v === "updated" ? "" : v })} />
      <input class="filter" type="search" placeholder="Filter by name, schema or spec" aria-label="Filter changes" value=${filter} onInput=${(e) => setFilter(e.currentTarget.value)} />
    </div>
    ${rows.length === 0
      ? html`<${Empty}>No changes match.<//>`
      : html`<table class="table">
          <thead><tr><th>Change</th><th>Stage</th><th>Schema</th><th>Tasks</th><th>Created</th><th>${status === "archived" ? "Archived" : "Updated"}</th></tr></thead>
          <tbody>
            ${rows.flatMap(
              (c, i) => html`${i === firstArchived && i > 0 && html`<tr key="archived-divider" class="group-divider"><td colspan="6">Archived · ${rows.length - i}</td></tr>`}
              <tr key=${c.slug + c.source.key} class="row-link">
                <td><a class="row-target" href=${changeHref(c)}>${c.name}</a> <${SourceBadge} source=${c.source} />
                  ${c.variants > 1 && html`<${Badge} kind="warn">${c.variants} versions<//>`}
                  ${c.status === "archived" && html`<div class="muted small mono">${c.slug}</div>`}</td>
                <td><${LaneBadge} lane=${c.lane} /></td>
                <td class="mono small">${c.schema || "-"}</td>
                <td>${c.tasks ? html`<${Progress} done=${c.tasks.done} total=${c.tasks.total} />` : html`<span class="muted small">-</span>`}</td>
                <td class="mono small">${c.created || "-"}</td>
                <td class="mono small">${c.archived || relative(c.updated)}</td>
              </tr>`,
            )}
          </tbody>
        </table>`}
  </div>`;
}

// -- detail --

const ART_SORTS = [
  { id: "modified", label: "Modified" },
  { id: "schema", label: "Schema order" },
  { id: "alpha", label: "A-Z" },
];

function sortArtifacts(arts, mode, order) {
  if (mode === "alpha") return [...arts].sort((a, b) => a.title.localeCompare(b.title));
  if (mode === "schema" && order) {
    const rank = (a) => {
      const i = order.indexOf(a.schema_artifact);
      return i < 0 ? order.length : i;
    };
    return [...arts].sort((a, b) => rank(a) - rank(b) || a.path.localeCompare(b.path));
  }
  return arts; // the server sends newest first
}

function TaskList({ tasks }) {
  return html`<div class="tasks">
    ${tasks.sections.map((s) => {
      const done = s.items.filter((i) => i.done).length;
      return html`<section class="task-section">
        ${s.title && html`<h3 class="task-section-title">${s.title} <span class="muted small">${done}/${s.items.length}</span></h3>`}
        <ul class="task-items">
          ${s.items.map(
            (i) => html`<li class=${`task ${i.done ? "done" : ""}`}>
              <span class="task-box" aria-label=${i.done ? "done" : "to do"}>${i.done ? "✓" : ""}</span>
              <${Markdown} src=${i.text} className="task-text" />
            </li>`,
          )}
        </ul>
      </section>`;
    })}
  </div>`;
}

function SpecsTab({ art }) {
  const toc = [];
  art.specs.forEach((s, i) => {
    toc.push({ level: 0, text: s.path, id: `f${i}` });
    toc.push(...docToc(s.doc, `f${i}-`, 1));
  });
  return html`<div class="with-toc">
    <div class="doc-col">
      ${art.specs.map(
        (s, i) => html`<section class="delta-file">
          <header class="file-head" id=${`f${i}`}>
            <span class="mono">${s.path}</span>
            <a class="small" href=${href(["specs", s.topic])}>main spec</a>
          </header>
          <${SpecDoc} doc=${s.doc} prefix=${`f${i}-`} />
        </section>`,
      )}
    </div>
    <${Toc} items=${toc} />
  </div>`;
}

function ArtifactView({ art }) {
  if (art.kind === "specs") return html`<${SpecsTab} art=${art} />`;
  if (art.kind === "tasks" && art.tasks) {
    return html`<div class="doc-col">
      <${Progress} done=${art.tasks.done} total=${art.tasks.total} wide />
      <${TaskList} tasks=${art.tasks} />
    </div>`;
  }
  if (art.kind === "data") return html`<pre class="code-block"><code>${art.content}</code></pre>`;
  const toc = headings(art.content, "a-").map((h) => ({ level: h.depth - 2, text: h.text, id: h.id }));
  return html`<div class="with-toc">
    <div class="doc-col"><${Markdown} src=${art.content} prefix="a-" /></div>
    <${Toc} items=${toc} />
  </div>`;
}

export function ChangeDetail({ slug, query }) {
  const wt = query.get("wt") || "";
  const { data: c, error } = useApi(apiUrl("change", { slug, wt }));
  const [sortMode, setSortMode] = useState(pref("artifact-sort", "modified"));
  const [filter, setFilter] = useState("");
  if (error) return html`<${ErrorBox} error=${error} />`;
  if (!c) return html`<${Loading} />`;
  const order = c.schema_order;
  let arts = sortArtifacts(c.artifacts, sortMode, order);
  const f = filter.trim().toLowerCase();
  if (f) arts = arts.filter((a) => a.title.toLowerCase().includes(f) || a.path.toLowerCase().includes(f));
  const current = c.artifacts.find((a) => a.id === query.get("tab")) || arts[0] || c.artifacts[0];
  const choose = (mode) => {
    setSortMode(mode);
    setPref("artifact-sort", mode);
  };
  const expected = order ? order.length : null;
  const present = new Set(c.artifacts.map((a) => a.schema_artifact).filter(Boolean)).size;
  const sub = [
    c.schema ? `Schema: ${c.schema}` : "No schema",
    expected ? `${present}/${expected} artifacts` : `${c.artifacts.length} artifacts`,
    c.created && `created ${c.created}`,
    c.archived ? `archived ${c.archived}` : `updated ${relative(c.updated)}`,
  ].filter(Boolean).join(" · ");
  return html`<div class="detail">
    <${PageHeader} title=${c.name} sub=${sub} back=${href(["changes"])}>
      <${LaneBadge} lane=${c.lane} />
      <${SourceBadge} source=${c.source} />
      ${c.tasks && html`<${Progress} done=${c.tasks.done} total=${c.tasks.total} />`}
      <${ExportMenu} name=${c.slug} title=${c.name} markdown=${() => changeMarkdown(c, sub, sortArtifacts(c.artifacts, sortMode, order))} />
    <//>
    ${c.artifacts.length === 0
      ? html`<${Empty}>This change has no artifacts yet.<//>`
      : html`<div class="tabbar">
          <div class="tabs" role="tablist">
            ${arts.map(
              (a) => html`<button type="button" role="tab" aria-selected=${a === current}
                class=${`tab ${a === current ? "on" : ""}`} title=${a.path}
                onClick=${() => setQuery({ tab: a.id })}>
                <span class=${`tab-kind kind-${a.kind}`} aria-hidden="true">${{ tasks: "☑", specs: "§", data: "{}", markdown: "¶" }[a.kind]}</span>${a.title}
              </button>`,
            )}
          </div>
          <div class="tab-tools">
            ${c.artifacts.length > 5 && html`<input class="filter small" type="search" placeholder="Filter" aria-label="Filter artifacts" value=${filter} onInput=${(e) => setFilter(e.currentTarget.value)} />`}
            <${Select} label="Sort" value=${sortMode} options=${order ? ART_SORTS : ART_SORTS.filter((s) => s.id !== "schema")} onChange=${choose} />
          </div>
        </div>
        ${current.kind !== "specs" && html`<div class="artifact-path muted small mono">${current.path}</div>`}
        <${ArtifactView} key=${current.id} art=${current} />
        <${PrevNext} arts=${arts} current=${current} />`}
    <${MetaCard} meta=${c.meta} />
  </div>`;
}

// Every artifact verbatim, in the tab order, each under its file path.
function changeMarkdown(c, sub, arts) {
  const parts = [`# ${c.name}`, "", sub];
  const file = (path, body) => parts.push("", "---", "", `**\`${path}\`**`, "", body.trim());
  for (const a of arts) {
    if (a.kind === "specs") for (const s of a.specs) file(s.path, s.content);
    else file(a.path, a.kind === "data" ? `\`\`\`${a.path.split(".").pop()}\n${a.content.trim()}\n\`\`\`` : a.content);
  }
  return `${parts.join("\n")}\n`;
}

// Reading a change front to back: the neighbouring tabs in the current sort order.
function PrevNext({ arts, current }) {
  const i = arts.indexOf(current);
  const prev = arts[i - 1];
  const next = arts[i + 1];
  if (!prev && !next) return null;
  const go = (a) => {
    setQuery({ tab: a.id });
    document.querySelector(".main")?.scrollTo({ top: 0 });
  };
  return html`<nav class="prev-next">
    ${prev ? html`<button type="button" class="pn" onClick=${() => go(prev)}>← ${prev.title}</button>` : html`<span></span>`}
    ${next && html`<button type="button" class="pn" onClick=${() => go(next)}>${next.title} →</button>`}
  </nav>`;
}

// `.openspec.yaml` keys beyond the two already in the header line.
function MetaCard({ meta }) {
  const extra = Object.entries(meta || {}).filter(([k]) => k !== "schema" && k !== "created");
  if (!extra.length) return null;
  return html`<section class="panel">
    <h2 class="panel-title">Metadata <span class="muted small mono">.openspec.yaml</span></h2>
    <dl class="meta-card">
      ${extra.map(([k, v]) => html`<dt class="mono">${k}</dt><dd class="mono">${typeof v === "object" ? JSON.stringify(v) : String(v)}</dd>`)}
    </dl>
  </section>`;
}
