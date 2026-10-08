import { html } from "../lib.js";
import { Empty, PageHeader } from "../ui.js";

export function Agents({ snap }) {
  const agents = snap.agents;
  return html`<div class="page">
    <${PageHeader} title="Agents" sub="Coding agents with OpenSpec skills or commands in this project" />
    ${agents.length === 0
      ? html`<${Empty}>No OpenSpec skills or commands found in any agent config directory. Run <span class="mono">openspec init</span> or <span class="mono">openspec update</span> to install them.<//>`
      : html`<div class="card-grid">
          ${agents.map(
            (a) => html`<section class="card agent-card">
              <div class="card-title">${a.tools.join(", ")}</div>
              <div class="muted small mono">${a.root}/</div>
              ${a.skills.length > 0 &&
              html`<div class="agent-group">
                <div class="agent-group-title small">Skills <span class="muted">${a.skills.length}</span></div>
                <div class="chip-list">${a.skills.map((s) => html`<span class="badge mono">${s}</span>`)}</div>
              </div>`}
              ${a.commands.length > 0 &&
              html`<div class="agent-group">
                <div class="agent-group-title small">Commands <span class="muted">${a.commands.length}</span></div>
                <ul class="plain mono small">${a.commands.map((c) => html`<li>${c}</li>`)}</ul>
              </div>`}
            </section>`,
          )}
        </div>`}
  </div>`;
}
