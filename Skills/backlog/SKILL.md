---
name: backlog
description: Capture single backlog items, or list and triage an existing project backlog. Use this skill whenever the user wants to file a bug, feature request, or backlog item without writing a full PRD, including casual requests mid-conversation like "create an issue for that", "add this to the backlog", or "file a quick bug for X". Also use when the user wants to see what's open, triage stale items, or pick something to work on ("what's open?", "show me the issues", "review the backlog"). Auto-detects destination (GitHub via `gh` CLI, or local `docs/BACKLOG.md` / `docs/issues/`). For multi-bug conversational QA sessions, use qa-to-issues. For full PRDs with user stories, use to-prd. For breaking an existing plan into vertical-slice implementation tickets, use to-issues.
---

# Backlog management

Capture single items to a project backlog, or list and triage an existing one. Detect the user's intent and run in either **add** mode (one item being filed) or **review** mode (looking at what's there). The two modes share destination detection.

## Destination detection

Try in order; cache the result for any follow-up in the same flow:

1. `gh repo view` succeeds → use GitHub issues for that repo.
2. Else `docs/BACKLOG.md` exists → append for adds, read for reviews.
3. Else `docs/issues/` directory exists → per-issue files (one `.md` per issue, numbered prefix).
4. Else ask the user where to put it. Don't silently create files in the project root.

If the user invokes this skill in a directory with no obvious project (no git, no `docs/`), say so and ask before doing anything.

## Add mode

The user has a single item to file. Goal: lower ceremony than typing the issue themselves. If it's heavier than that, they'll stop using the skill.

1. **Dupe check.** Search existing items for keyword overlap (`gh issue list --search "<keywords>"` or grep the local file). If a near-match exists, surface it and ask whether to update that one or file new. This is the cheapest defence against ending up with three issues for the same thing.

2. **Enhance proportional to input.** A one-liner from the user warrants 2-3 short context bullets drawn from CLAUDE.md and the current project state (technical caveats, related modules, open questions). If the user already wrote a paragraph or more, file it as-is. Don't restructure their words. The point of enhancement is to capture context they didn't bother to type, not to dress up what they did type.

3. **One clarifying question max**, and only when scope or category (bug vs enhancement) is genuinely ambiguous. If you can guess from context, guess.

4. **File and return the URL or path.** No trailing summary; the URL is the receipt.

### Labels

GitHub: pick from `gh label list`. Don't invent new labels without asking. Projects often have label conventions wired into filters, project boards, or release automation, and an invented label is invisible to those.

Local `docs/BACKLOG.md` or per-issue files: prefix the title with `[bug]` / `[enhancement]` / `[question]` for easy scanning.

## Review mode

The user wants to see what's open and possibly act on something.

1. **List.**
   - GitHub: `gh issue list --state open --limit 50 --json number,title,labels,createdAt`.
   - Local file: read it and parse the bullet/heading structure.
   - Per-issue files: list filenames with their first-line title.

2. **Group and present.** By label first (bug / enhancement / question / other), then by age within each group. One line per item: number, title, age, label. Don't paginate unless the list is genuinely long (>50 items).

3. **Offer three actions** without auto-picking:
   - **Triage**: re-label, close stale items, merge duplicates. Per-item confirmation.
   - **Pick one**: load the full item into context and stop. Do not auto-implement; the user might be scanning the backlog before deciding what to focus on.
   - **Themes**: cluster related items, suggest groupings or parent issues.

The "pick one" action is deliberately a stop point. Sliding into implementation work breaks the user's actual flow, which was reviewing.

## When to redirect

These adjacent skills cover cases this skill should NOT handle. Detect early; if the user's opening line fits one of these, suggest the right skill before doing any work:

- **Multiple items in one go** ("I've found three bugs", "let me run through what's broken") → `qa-to-issues`. The interactive multi-bug interview pattern is what that skill exists for.
- **Full PRD with user stories** ("write up a spec for X", "I want a PRD") → `to-prd`.
- **Breaking an existing plan into slices** ("break this plan into issues", "convert this PRD into tickets") → `to-issues`.

The redirect is a sentence, not a process. Tell the user which skill fits better, then stop.

## Gotchas

- **Don't bulk-close in triage.** "Close the stale ones" almost always means show them first, then close after confirmation. Wrong-close is much more expensive than an extra confirmation step.
- **Don't invent labels.** `gh label list` is cheap; respecting existing label conventions matters because labels drive filters and project boards downstream.
- **Capture must be lighter than typing the issue manually.** The "one clarifying question max" rule isn't about being terse; it's about preserving the value proposition. If the skill takes longer than the user just typing it, they'll stop using it.
- **Per-issue local files need a numbering scheme.** When using `docs/issues/`, look at existing files (`0001-slug.md`? `001-slug.md`?) and continue the existing scheme. Don't impose a new one.
- **Project root pollution.** If no `gh`, no `docs/BACKLOG.md`, no `docs/issues/`, ask. Silently creating `BACKLOG.md` in the project root surprises the user.
- **Don't restructure the user's words.** If they wrote a paragraph, file the paragraph. Reformatting into your preferred template feels like the AI is overwriting their intent, even if the template is "better".
- **Respect issue templates.** If the repo has `.github/ISSUE_TEMPLATE/`, conform the body to the matching template (typically bug vs feature). `gh issue create --title --body` skips templates silently, which surprises maintainers who built filters or automations around the template's fields.
