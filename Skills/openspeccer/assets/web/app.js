import { render } from "preact";
import { apiUrl, connectLive, href, html, pref, setPref, useApi, useLive, useRoute, useState } from "./lib.js";
import { ErrorBox, Loading } from "./ui.js";
import { Dashboard } from "./views/dashboard.js";
import { SpecsPage } from "./views/specs.js";
import { ChangeDetail, ChangeList } from "./views/changes.js";
import { Timeline } from "./views/timeline.js";
import { SchemaDetail, SchemaList } from "./views/schemas.js";
import { Agents } from "./views/agents.js";
import { SearchPage } from "./views/search.js";

const NAV = [
  { id: "", label: "Dashboard", icon: "▦" },
  { id: "specs", label: "Specs", icon: "§" },
  { id: "changes", label: "Changes", icon: "⑂" },
  { id: "timeline", label: "Timeline", icon: "═" },
  { id: "schemas", label: "Schemas", icon: "◇" },
  { id: "agents", label: "Agents", icon: "◎" },
];

function SearchBox({ initial }) {
  const [q, setQ] = useState(initial || "");
  const submit = (e) => {
    e.preventDefault();
    location.hash = href(["search"], { q: q.trim() });
  };
  return html`<form class="search-box" onSubmit=${submit} role="search">
    <input type="search" placeholder="Search (press /)" aria-label="Search" value=${q} onInput=${(e) => setQ(e.currentTarget.value)} />
  </form>`;
}

function StatusBar({ snap }) {
  const live = useLive();
  const scope = pref("scope", "worktrees");
  const label = { live: "Live", offline: "Offline", connecting: "Connecting" }[live.status];
  const trees = snap?.worktrees?.length ?? 0;
  return html`<footer class="statusbar">
    <span class=${`live live-${live.status}`} title=${live.status === "offline" ? "Lost connection to the openspeccer server" : "Updates as files change"}>● ${label}</span>
    ${snap && html`<span class="repo-name">${snap.repo.name}</span><span class="repo-path" title=${snap.repo.path}>${snap.repo.path}</span>`}
    <span class="spacer"></span>
    <label class="scope" title="Which working copies contribute active changes">
      Scope
      <select value=${scope} onChange=${(e) => setPref("scope", e.currentTarget.value)}>
        <option value="main">This checkout</option>
        <option value="worktrees">All git worktrees${scope !== "main" && trees > 1 ? ` (${trees})` : ""}</option>
        <option value="jj">Worktrees + jj (experimental)</option>
      </select>
    </label>
    ${live.status === "live" && html`<span class="muted">Watching for changes${live.at ? ` · ${live.at.toLocaleTimeString()}` : ""}</span>`}
  </footer>`;
}

function Page({ route, snap }) {
  const [section, ...rest] = route.parts;
  const q = route.query;
  switch (section ?? "") {
    case "":
      return html`<${Dashboard} snap=${snap} />`;
    case "specs":
      return html`<${SpecsPage} snap=${snap} topic=${rest.join("/")} query=${q} />`;
    case "changes":
      return rest.length
        ? html`<${ChangeDetail} snap=${snap} slug=${rest[0]} query=${q} />`
        : html`<${ChangeList} snap=${snap} query=${q} />`;
    case "timeline":
      return html`<${Timeline} snap=${snap} query=${q} />`;
    case "schemas":
      return rest.length ? html`<${SchemaDetail} snap=${snap} name=${rest[0]} />` : html`<${SchemaList} snap=${snap} />`;
    case "agents":
      return html`<${Agents} snap=${snap} />`;
    case "search":
      return html`<${SearchPage} query=${q.get("q") || ""} />`;
    default:
      return html`<div class="state">Unknown page. <a href="#/">Back to the dashboard</a></div>`;
  }
}

function App() {
  const route = useRoute();
  const { data: snap, error } = useApi(apiUrl("snapshot"));
  const section = route.parts[0] ?? "";
  return html`<div class="shell">
    <aside class="sidebar">
      <a class="wordmark" href="#/">OPENSPECCER</a>
      <${SearchBox} key=${route.query.get("q")} initial=${route.query.get("q")} />
      <nav class="nav">
        ${NAV.map(
          (n) => html`<a class=${`nav-item ${section === n.id ? "active" : ""}`} href=${`#/${n.id}`}>
            <span class="nav-icon" aria-hidden="true">${n.icon}</span>${n.label}
          </a>`,
        )}
      </nav>
    </aside>
    <main class="main">
      ${error && !snap ? html`<${ErrorBox} error=${error} />` : !snap ? html`<${Loading} />` : html`<${Page} route=${route} snap=${snap} />`}
    </main>
    <${StatusBar} snap=${snap} />
  </div>`;
}

// `/` jumps to search from anywhere that is not already a text field.
addEventListener("keydown", (e) => {
  if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
  if (e.target.closest?.("input, textarea, select, [contenteditable]")) return;
  e.preventDefault();
  document.querySelector(".search-box input")?.focus();
});

connectLive();
render(html`<${App} />`, document.getElementById("app"));
