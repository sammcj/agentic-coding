// OpenSpec's core model, annotated with this repo's counts, and the everyday workflow mapped to
// the agent commands actually installed here. Kept to concepts that rarely change upstream.
import { href, html } from "../lib.js";
import { LANES, OpBadge, PageHeader } from "../ui.js";
import { Copyable } from "./commands.js";

const plural = (n, word) => `${n} ${word}${n === 1 ? "" : "s"}`;

function Folders({ snap }) {
  const s = snap.stats;
  return html`<div class="guide-folders">
    <a class="guide-box" href=${href(["changes"], { status: "active" })}>
      <div class="guide-path">openspec/changes/</div>
      <div>What you propose to change</div>
      <div class="muted small">${plural(s.active, "active change")}</div>
    </a>
    <div class="guide-arrow" aria-hidden="true">archive<br />→</div>
    <a class="guide-box" href="#/specs">
      <div class="guide-path">openspec/specs/</div>
      <div>What the system does now</div>
      <div class="muted small">${plural(s.specs, "spec")}, ${plural(s.requirements, "requirement")}</div>
    </a>
  </div>`;
}

const STEPS = {
  proposed: { verb: "propose", what: "proposal written, no tasks yet" },
  planned: { verb: "propose", what: "tasks.md written, none ticked" },
  in_progress: { verb: "apply", what: "tasks being ticked off" },
  ready: { verb: "apply", what: "every task ticked" },
  archived: { verb: "archive", what: "deltas merged into specs/, folder moved to changes/archive/" },
};

function Lifecycle({ snap }) {
  const count = (lane) => snap.changes.filter((c) => c.lane === lane).length;
  const link = (lane) => (lane === "archived" ? href(["changes"], { status: "archived" }) : href(["changes"], { lane }));
  return html`<ol class="guide-steps">
    ${LANES.map(
      (l) => html`<li>
        <a class=${`guide-step lane-edge-${l.id}`} href=${link(l.id)}>
          <div class="guide-verb muted small">${STEPS[l.id].verb}</div>
          <div class=${`guide-lane lane-${l.id}`}>${l.label} <span class="muted">${count(l.id)}</span></div>
          <div class="small">${STEPS[l.id].what}</div>
        </a>
      </li>`,
    )}
  </ol>`;
}

const ANATOMY = [
  ["proposal.md", "why", "Intent and scope. Written first."],
  ["design.md", "how", "Technical decisions. Optional."],
  ["tasks.md", "do", "- [ ] checklist. Ticks drive the lifecycle above."],
];

function Anatomy() {
  return html`<div class="guide-tree">
    <div class="guide-path">openspec/changes/add-login/</div>
    ${ANATOMY.map(
      ([file, role, what]) => html`<div class="guide-file">
        <span class="mono">${file}</span>
        <span class="badge">${role}</span>
        <span class="muted">${what}</span>
      </div>`,
    )}
    <div class="guide-file">
      <span class="mono">${"specs/<capability>/spec.md"}</span>
      <span class="badge">what</span>
      <span class="muted"
        >${["ADDED", "MODIFIED", "REMOVED"].map((op) => html`<${OpBadge} op=${op} /> `)} requirements against openspec/specs/</span
      >
    </div>
  </div>`;
}

// OpenSpec's `core` profile, in the order they are used.
const WORKFLOW = [
  { verb: "explore", optional: true, what: "Think an idea through with your agent. Nothing is written." },
  { verb: "propose", what: "Describe the change. The agent writes the proposal, spec deltas, design and tasks. Review them on the Changes page." },
  { verb: "update", optional: true, what: "Revise the planning artifacts when the plan shifts, keeping them consistent. Never edits code." },
  { verb: "apply", what: "The agent implements the change, ticking tasks.md as it goes." },
  { verb: "sync", optional: true, what: "Merge the deltas into openspec/specs/ without archiving. Archive offers to, so it's rarely needed." },
  { verb: "archive", what: "Merge the deltas into openspec/specs/ and file the change away." },
];

const DOCS = "https://openspec.dev/docs/skills";
const PROFILES = "https://openspec.dev/docs/profiles";

// Opt-in through `openspec config profile`; no fixed order.
const EXPANDED = [
  { verb: "new", what: "Start a change scaffold without writing artifacts." },
  { verb: "continue", what: "Write the next artifact whose dependencies are done." },
  { verb: "ff", what: "Fast-forward: write every planning artifact at once." },
  { verb: "verify", what: "Check the code matches the change's specs and tasks." },
  { verb: "bulk-archive", what: "Archive several finished changes at once." },
  { verb: "onboard", what: "Guided tutorial through the whole workflow." },
];

// How to invoke a step with what is installed: `opsx/propose.md` is `/opsx:propose`,
// `opsx-propose.md` is `/opsx-propose`, and a skill such as `openspec-apply-change` is named as is.
// A skill only shows for an agent with no command for the step. Returns [text, tools] pairs.
function invocations(agents, verb) {
  const found = new Map();
  const add = (text, tools) => found.set(text, [...new Set([...(found.get(text) || []), ...tools])]);
  for (const a of agents) {
    const cmds = a.commands.flatMap((c) => {
      const m = c.match(/opsx([/:-])([\w-]+?)(?:\.prompt)?\.\w+$/);
      return m && m[2] === verb ? [m[1] === "-" ? `/opsx-${verb}` : `/opsx:${verb}`] : [];
    });
    const skills = a.skills.filter((s) => ["openspec-", "opsx-"].some((p) => s === p + verb || s.startsWith(`${p}${verb}-`)));
    for (const text of cmds.length ? cmds : skills) add(text, a.tools);
  }
  return [...found];
}

// Leads with what to type in the agent; OpenSpec's own spelling when nothing here provides it.
function FlowStep({ agents, step }) {
  const found = invocations(agents, step.verb);
  const cmds = found.length ? found : [[`/opsx:${step.verb}`, []]];
  return html`<li class="guide-flow-step">
    <div>
      <div class="guide-cmds">
        ${cmds.map(([text, tools]) => html`<${Copyable} text=${text} title=${`${tools.join(", ") || "Not installed here"}: click to copy`} />`)}
      </div>
      ${step.optional && html`<div class="muted small">optional</div>`}
    </div>
    <div>${step.what}</div>
  </li>`;
}

function Workflow({ agents }) {
  return html`<ol class="guide-flow">
    ${WORKFLOW.map((step) => html`<${FlowStep} agents=${agents} step=${step} />`)}
  </ol>
  <p class="muted small">
    ${agents.length
      ? html`Hover a command to see which tools have it. See <a href="#/agents">Agents</a> for every tool, <a href="#/commands">Commands</a> for the CLI.`
      : html`No agent commands installed. See <a href="#/commands">Commands</a> to set OpenSpec up, or ask your agent in plain words.`}
    ${" "}Reference: <a href=${DOCS} target="_blank" rel="noopener noreferrer">OpenSpec skills and commands</a>.
  </p>
  <details class="guide-more">
    <summary>Expanded commands</summary>
    <p class="muted small">
      Opt-in. Run <span class="mono">openspec config profile</span>, select workflows, then${" "}
      <span class="mono">openspec update</span> in the project. See <a href=${PROFILES} target="_blank" rel="noopener noreferrer">profiles</a>.
    </p>
    <ul class="guide-flow">
      ${EXPANDED.map((step) => html`<${FlowStep} agents=${agents} step=${step} />`)}
    </ul>
  </details>`;
}

export function Guide({ snap }) {
  return html`<div class="page guide">
    <${PageHeader} title="Guide" sub="How OpenSpec works, with this repo's numbers" />
    <section class="panel">
      <h2 class="panel-title">Two folders</h2>
      <${Folders} snap=${snap} />
    </section>
    <section class="panel">
      <h2 class="panel-title">How to use it</h2>
      <${Workflow} agents=${snap.agents} />
    </section>
    <section class="panel">
      <h2 class="panel-title">Lifecycle of a change</h2>
      <${Lifecycle} snap=${snap} />
    </section>
    <section class="panel">
      <h2 class="panel-title">Anatomy of a change</h2>
      <${Anatomy} />
    </section>
  </div>`;
}
