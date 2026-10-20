# Changelog

<!-- AI agents: After completing changes to this project, add a terse TLDR style bullet describing the change under today's date heading (## YYYY-MM-DD), newest date first. Create the date heading if it does not exist. Log only changes a reader would care about - new capability, changed or broken behaviour, removals, real fixes. Skip cosmetic and housekeeping edits (wording, formatting, typos, file moves); git history covers those. One line per change, aim under 15 words - say what changed, not how it was implemented. Write more only when the change is genuinely complex and the reasoning cannot be recovered from the source or git history. No versioning is required. -->

## 2026-10-20

- Export menu on dashboard, schemas, schema detail, agents and commands pages.
- Schema detail Markdown export includes the dependency graph as a Mermaid flowchart.
- Change detail export offers "This tab" and "All tabs"; default Markdown is now the current tab.
- Sidebar "Export all (HTML)" saves every page as one static HTML file with in-file links.
- Static HTML exports keep click-to-copy command text instead of dropping it.
- Specs page with no main specs lists active changes proposing specs, linking to their Specs tab.
- Spec tree pane border now runs full height when the tree is short.
- Added CHANGELOG.md and CLAUDE.md to track future changes.
