// The project's openspec/config.yaml: what OpenSpec adds to agent instructions.
import { ExportMenu } from "../export.js";
import { apiUrl, href, html, useApi } from "../lib.js";
import { Markdown } from "../md.js";
import { Badge, Empty, ErrorBox, Loading, PageHeader } from "../ui.js";

const OP_NOTE = {
  apply: "Given to the agent implementing a change's tasks",
  archive: "Given to the agent archiving a finished change",
};

const kb = (n) => `${(n / 1024).toFixed(1)}KB`;
const yamlish = (v) => (typeof v === "string" ? v : JSON.stringify(v));

export function configMarkdown(repoName, c) {
  const out = [`# ${repoName} OpenSpec config`, "", `\`${c.path}\``];
  if (c.warnings.length) out.push("", ...c.warnings.map((w) => `> Warning: ${w}`));
  if (c.schema) out.push("", `Default schema: \`${c.schema}\``);
  if (c.context) out.push("", "## Context", "", c.context.trim());
  const rules = Object.entries(c.rules);
  if (rules.length) {
    out.push("", "## Artifact rules");
    for (const [a, list] of rules) out.push("", `### ${a}`, "", ...list.map((r) => `- ${r}`));
  }
  const ops = Object.entries(c.operations);
  if (ops.length) {
    out.push("", "## Operation guidance");
    for (const [op, list] of ops) out.push("", `### ${op}`, "", ...list.map((g) => `- ${g}`));
  }
  const other = Object.entries(c.other);
  if (other.length) out.push("", "## Other settings", "", ...other.map(([k, v]) => `- \`${k}\`: \`${yamlish(v)}\``));
  if (c.instructions.length) out.push("", "## Agent instructions", "", ...c.instructions.map((f) => `- \`${f.path}\` (${kb(f.bytes)})`));
  return `${out.join("\n")}\n`;
}

function Section({ title, note, children }) {
  return html`<section class="panel">
    <h2 class="panel-title">${title}</h2>
    ${note && html`<div class="muted small config-note">${note}</div>`}
    ${children}
  </section>`;
}

// Standard instruction files agents load on their own, outside OpenSpec.
function Instructions({ files }) {
  return html`<${Section} title="Agent instructions" note="Loaded by agents directly, alongside OpenSpec's instructions">
    <div class="card">
      ${files.length === 0
        ? html`<div class="muted small">No AGENTS.md, CLAUDE.md, rule or sub-agent files found.</div>`
        : files.map(
            (f) => html`<details class="config-file">
              <summary><span class="mono">${f.path}</span> <span class="muted small">${kb(f.bytes)}</span></summary>
              ${f.content ? html`<${Markdown} src=${f.content} bdd=${false} />` : html`<div class="muted small">Too large to preview.</div>`}
            </details>`,
          )}
    </div>
  <//>`;
}

export function Config({ snap }) {
  const { data: c, error } = useApi(apiUrl("config"));
  if (error) return html`<${ErrorBox} error=${error} />`;
  if (!c) return html`<${Loading} />`;
  if (!c.path) {
    return html`<div class="page">
      <${PageHeader} title="Config" />
      <${Empty}>No <span class="mono">openspec/config.yaml</span>. It sets the default schema, project context, per-artifact rules and apply/archive guidance. Run <span class="mono">openspec init</span> to create one.<//>
      <${Instructions} files=${c.instructions} />
    </div>`;
  }
  const rules = Object.entries(c.rules);
  const ops = Object.entries(c.operations);
  const other = Object.entries(c.other);
  return html`<div class="page">
    <${PageHeader} title="Config" sub=${`${c.path} · added to agent instructions by the OpenSpec CLI`}>
      <${ExportMenu} name=${`${snap.repo.name}-config`} title=${`${snap.repo.name} OpenSpec config`} markdown=${() => configMarkdown(snap.repo.name, c)} />
    <//>
    ${c.error && html`<div class="notice">Could not parse the config: ${c.error}</div>`}
    ${c.warnings.map((w) => html`<div class="notice">${w}</div>`)}
    ${c.schema && html`<div>Default schema <a class="mono" href=${href(["schemas", c.schema])}>${c.schema}</a></div>`}
    ${c.context &&
    html`<${Section} title="Context" note=${`Sent with every artifact and operation · ${kb(c.context_bytes)} of ${kb(c.context_limit)}`}>
      <div class="card"><${Markdown} src=${c.context} bdd=${false} /></div>
    <//>`}
    ${rules.length > 0 &&
    html`<${Section} title="Artifact rules" note="Sent only when the agent writes that artifact">
      ${rules.map(
        ([a, list]) => html`<div class="card config-op">
          <div class="card-title mono">${a} ${c.unknown_rules.includes(a) && html`<${Badge} kind="warn" title="Matches no artifact in any schema">unused<//>`}</div>
          <ul class="config-list small">${list.map((r) => html`<li>${r}</li>`)}</ul>
        </div>`,
      )}
    <//>`}
    ${ops.length > 0 &&
    html`<${Section} title="Operation guidance">
      ${ops.map(
        ([op, list]) => html`<div class="card config-op">
          <div class="card-title mono">${op}</div>
          <div class="muted small">${OP_NOTE[op]}</div>
          <ul class="config-list small">${list.map((g) => html`<li>${g}</li>`)}</ul>
        </div>`,
      )}
    <//>`}
    ${other.length > 0 &&
    html`<${Section} title="Other settings">
      <dl class="cmd-opts">${other.map(([k, v]) => html`<dt class="mono">${k}</dt><dd class="mono">${yamlish(v)}</dd>`)}</dl>
    <//>`}
    ${!c.error && !c.context && !rules.length && !ops.length && html`<${Empty}>No context, rules or operation guidance set.<//>`}
    <${Instructions} files=${c.instructions} />
    <${Section} title="Raw file">
      <details class="card config-raw">
        <summary class="mono">${c.path}</summary>
        <pre class="mono small">${c.raw}</pre>
      </details>
    <//>
  </div>`;
}
