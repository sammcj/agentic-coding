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

const WORKFLOW = [
  { verb: "explore", optional: true, what: "Think an idea through with your agent. Nothing is written." },
  { verb: "propose", alt: ["new", "continue"], what: "Describe the change. The agent writes the proposal, spec deltas, design and tasks. Review them on the Changes page." },
  { verb: "apply", what: "The agent implements the change, ticking tasks.md as it goes." },
  { verb: "verify", optional: true, what: "Check the code matches the change's specs and tasks." },
  { verb: "archive", what: "Merge the deltas into openspec/specs/ and file the change away." },
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

function Workflow({ agents }) {
  return html`<ol class="guide-flow">
    ${WORKFLOW.map((step) => {
      const cmds = invocations(agents, step.verb);
      const alts = (step.alt || []).flatMap((v) => invocations(agents, v));
      return html`<li class="guide-flow-step">
        <div class="guide-flow-verb">${step.verb}${step.optional && html` <span class="muted small">optional</span>`}</div>
        <div>
          ${cmds.length > 0 &&
          html`<div class="guide-cmds">${cmds.map(([text, tools]) => html`<${Copyable} text=${text} title=${`${tools.join(", ")}: click to copy`} />`)}</div>`}
          <div>${step.what}</div>
          ${alts.length > 0 && html`<div class="muted small">Step by step: ${alts.map(([text]) => text).join(", ")}</div>`}
        </div>
      </li>`;
    })}
  </ol>
  <p class="muted small">
    ${agents.length
      ? html`Commands found in this repo's agent config. See <a href="#/agents">Agents</a> for every tool, <a href="#/commands">Commands</a> for the CLI.`
      : html`No agent commands installed. See <a href="#/commands">Commands</a> to set OpenSpec up, or ask your agent in plain words.`}
  </p>`;
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
