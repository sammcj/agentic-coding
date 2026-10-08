// Reference for the installed OpenSpec CLI, read from its own --help output.
import { copyText } from "../export.js";
import { html, useApi, useState } from "../lib.js";
import { Empty, ErrorBox, Loading, PageHeader } from "../ui.js";

const DOCS = "https://github.com/Fission-AI/OpenSpec/blob/main/docs";
const LINKS = [
  { href: `${DOCS}/cli.md`, label: "CLI reference" },
  { href: `${DOCS}/commands.md`, label: "Agent slash commands" },
  { href: `${DOCS}/getting-started.md`, label: "Getting started" },
];

function Copyable({ text }) {
  const [done, setDone] = useState(false);
  const copy = async () => {
    if (!(await copyText(text))) return;
    setDone(true);
    setTimeout(() => setDone(false), 1500);
  };
  return html`<button type="button" class=${`copyable ${done ? "done" : ""}`} title="Copy to clipboard" onClick=${copy}>
    ${text}${done ? " ✓ copied" : ""}
  </button>`;
}

function Command({ cmd, children }) {
  const full = `openspec ${cmd.path.join(" ")}`;
  const usage = cmd.usage.replace(/^openspec\s+/, "").split(" ").slice(cmd.path.length).filter((t) => t !== "[options]" && t !== "[command]").join(" ");
  return html`<div class="cmd">
    <div class="cmd-head">
      <${Copyable} text=${full} />
      ${usage && html`<span class="mono muted">${usage}</span>`}
      ${cmd.aliases.length > 0 && html`<span class="muted small">alias ${cmd.aliases.join(", ")}</span>`}
    </div>
    <div class="cmd-desc">${cmd.description}</div>
    ${cmd.arguments.length > 0 && html`<dl class="cmd-opts">${cmd.arguments.map((a) => html`<dt class="mono">${a.term}</dt><dd>${a.desc}</dd>`)}</dl>`}
    ${cmd.options.length > 0 && html`<dl class="cmd-opts">${cmd.options.map((o) => html`<dt class="mono">${o.term}</dt><dd>${o.desc}</dd>`)}</dl>`}
    ${children}
  </div>`;
}

const matches = (cmd, f) =>
  !f || `${cmd.path.join(" ")} ${cmd.description} ${cmd.options.map((o) => `${o.term} ${o.desc}`).join(" ")}`.toLowerCase().includes(f);

export function Commands() {
  const { data, error } = useApi("/api/commands");
  const [filter, setFilter] = useState("");
  const links = html`<div class="docs-links">${LINKS.map((l) => html`<a href=${l.href} target="_blank" rel="noreferrer">${l.label} ↗</a>`)}</div>`;
  if (error) return html`<div class="page"><${PageHeader} title="Commands" />${links}<${ErrorBox} error=${error} /></div>`;
  if (!data) return html`<${Loading} what="Asking the OpenSpec CLI for its commands" />`;
  if (data.error) {
    return html`<div class="page">
      <${PageHeader} title="Commands" />${links}
      <${Empty}>The OpenSpec CLI is not available (${data.error}). Install it, or point OPENSPECCER_OPENSPEC_BIN at it.<//>
    </div>`;
  }
  const f = filter.trim().toLowerCase();
  const top = data.commands.filter((c) => c.path.length === 1);
  const kids = (c) => data.commands.filter((k) => k.path.length === c.path.length + 1 && c.path.every((p, i) => k.path[i] === p));
  const render = (c) => {
    const sub = kids(c).map(render).filter(Boolean);
    if (!matches(c, f) && !sub.length) return null;
    return html`<${Command} key=${c.path.join(" ")} cmd=${c}>${sub.length > 0 && html`<div class="cmd-sub">${sub}</div>`}<//>`;
  };
  const shown = top.map(render).filter(Boolean);
  return html`<div class="page">
    <${PageHeader} title="Commands" sub=${`OpenSpec CLI ${data.version || ""} · ${data.commands.length} commands · click a command to copy it`} />
    <div class="toolbar">
      <input class="filter" type="search" placeholder="Filter commands and options" aria-label="Filter commands" value=${filter} onInput=${(e) => setFilter(e.currentTarget.value)} />
      ${links}
    </div>
    ${data.global_options.length > 0 && !f && html`<div class="cmd">
      <div class="cmd-head"><strong>Global options</strong></div>
      <dl class="cmd-opts">${data.global_options.map((o) => html`<dt class="mono">${o.term}</dt><dd>${o.desc}</dd>`)}</dl>
    </div>`}
    ${shown.length ? shown : html`<${Empty}>No command matches.<//>`}
  </div>`;
}
