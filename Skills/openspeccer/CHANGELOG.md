# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. Log only changes a reader would care about - new capability, changed or broken behaviour, removals, real fixes. Skip cosmetic and housekeeping edits (wording, formatting, typos, file moves); git history covers those. One line per change, aim under 15 words - say what changed, not how it was implemented. Write more only when the change is genuinely complex and the reasoning cannot be recovered from the source or git history. No versioning is required. -->

## 2026-10-30

- Changes in a worktree resolve schemas and the default schema from that worktree.

## 2026-10-22

- Guide shows every core `/opsx:` command, with opt-in expanded commands in a collapsed section.
- Config page: context, artifact rules, operation guidance, settings OpenSpec ignores, agent instruction files.
- Schemas and Agents pages open the item directly when there is only one.
- Default schema is also read from `openspec/config.yml`.

## 2026-10-21

- Guide page: OpenSpec concepts and workflow, using live repo counts and installed agent commands.
- Change Specs tab diffs each MODIFIED requirement against the main spec, flagging names archive won't match.
- Spec Diff tab no longer drops changed lines starting with `--` or `++`.
- Guide page fills the full panel width instead of a 1000px column.
- Fixed XSS: text after a raw `<pre>`, `<code>`, `<kbd>` or `<script>` tag rendered unescaped.
- Static HTML exports carry a CSP that blocks scripts and network loads.
- Schema Markdown export no longer breaks Mermaid on newlines, backticks or dangling edges.
- 0.0.0.0 binds refuse unknown Host names; `--allow-host NAME` adds one. IP literals always pass.

## 2026-10-20

- Export menu on dashboard, schemas, schema detail, agents and commands pages.
- Schema detail Markdown export includes the dependency graph as a Mermaid flowchart.
- Change detail export offers "This tab" and "All tabs"; default Markdown is now the current tab.
- Sidebar "Export all (HTML)" saves every page as one static HTML file with in-file links.
- Static HTML exports keep click-to-copy command text instead of dropping it.
- Specs page with no main specs lists active changes proposing specs, linking to their Specs tab.
- Spec tree pane border now runs full height when the tree is short.
- Added CHANGELOG.md and CLAUDE.md to track future changes.
