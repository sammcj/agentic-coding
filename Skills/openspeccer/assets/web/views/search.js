import { apiUrl, href, html, useApi } from "../lib.js";
import { Badge, Empty, ErrorBox, Loading, PageHeader } from "../ui.js";

function Snippet({ hit }) {
  if (!hit.snippet) return null;
  if (hit.offset < 0) return html`<div class="snippet muted small">${hit.snippet}</div>`;
  const q = hit.qlen;
  return html`<div class="snippet small">
    ${hit.snippet.slice(0, hit.offset)}<mark>${hit.snippet.slice(hit.offset, hit.offset + q)}</mark>${hit.snippet.slice(hit.offset + q)}
  </div>`;
}

function hitHref(hit) {
  if (hit.kind === "spec") return href(["specs", hit.topic]);
  let tab;
  if (hit.file) tab = hit.file.startsWith("specs/") ? "specs" : hit.file.endsWith(".md") ? hit.file.slice(0, -3) : hit.file;
  return href(["changes", hit.slug], { tab, wt: hit.source_key });
}

export function SearchPage({ query }) {
  const { data, error } = useApi(query ? apiUrl("search", { q: query }) : null);
  if (!query) return html`<div class="page"><${PageHeader} title="Search" /><${Empty}>Type in the search box to search specs and change artifacts.<//></div>`;
  if (error) return html`<${ErrorBox} error=${error} />`;
  if (!data) return html`<${Loading} what="Searching" />`;
  const hits = data.hits.map((h) => ({ ...h, qlen: query.trim().length }));
  const specs = hits.filter((h) => h.kind === "spec");
  const changes = hits.filter((h) => h.kind === "change");
  return html`<div class="page">
    <${PageHeader} title=${`Search: ${query}`} sub=${`${hits.length} result${hits.length === 1 ? "" : "s"}`} />
    ${hits.length === 0 && html`<${Empty}>Nothing matches.<//>`}
    ${[["Specs", specs], ["Changes", changes]].map(
      ([title, list]) =>
        list.length > 0 &&
        html`<section class="panel">
          <h2 class="panel-title">${title} <span class="muted small">${list.length}</span></h2>
          <ul class="results">
            ${list.map(
              (h) => html`<li class="result">
                <a href=${hitHref(h)}>${h.title}</a>
                ${h.status && html` <${Badge} kind=${h.status === "active" ? "lane-in_progress" : "lane-archived"}>${h.status}<//>`}
                ${h.file && html` <span class="muted small mono">${h.file}</span>`}
                <${Snippet} hit=${h} />
              </li>`,
            )}
          </ul>
        </section>`,
    )}
  </div>`;
}
