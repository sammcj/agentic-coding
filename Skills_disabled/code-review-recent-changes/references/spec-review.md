# Spec axis: locating the spec and briefing the sub-agent

Read this only when the review has a spec to check against - i.e. step 2 of SKILL.md found a spec signal (an issue reference in the commits, a path the user passed, or an issue/PRD the user named). With no such signal, skip the Spec axis and report "no spec available"; there's no need to open this file.

## Locate the spec

Look for the originating spec, in this order:

1. Issue references in the commit messages (`#123`, `Closes #45`, GitLab `!67`). To fetch one, detect how this repo's tracker works, trying in order:
   - `docs/agents/issue-tracker.md` exists → follow the workflow it documents.
   - `gh repo view` succeeds → GitHub issues; fetch with `gh issue view <number> --comments` (the always-on `github` skill covers the commands).
   - `docs/issues/` or `docs/BACKLOG.md` exists → the item may live there as a local backlog entry; read it directly.
   - none of the above → ask the user how to fetch the issue.
2. A path the user passed as an argument.
3. A PRD/spec file under `docs/`, `specs/`, or `.scratch/` matching the branch name or feature.

If a signal pointed at a spec but it can't be located or fetched, ask the user where it is. If after that nothing turns up, skip the Spec axis and note "no spec available" in the final report.

## Spec sub-agent brief

Spawn a `general-purpose` sub-agent. Include the diff command, the commit list, and the spec path or fetched contents. Brief:

> Read the spec, then the diff. Read beyond the diff where it helps you judge whether a requirement is genuinely wired up rather than stubbed or partial. Report: (a) requirements the spec asked for that are missing or partial; (b) behaviour in the diff that wasn't asked for (scope creep); (c) requirements that look implemented but where the implementation looks wrong. Quote the spec line for each finding. Order findings worst-first. Under 400 words.
