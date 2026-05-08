---
name: github
description: You MUST always activate this github skill whenever working with GitHub in any capacity, including but not limited to gh cli, API, Actions, issues, PRs and other routine Github interactions.
metadata:
  info: I moved these out of my global agent rules to save a few tokens
---

# GitHub

- Use the `gh` CLI tool for interacting with GitHub (issues, PRs, releases) and perform `gh` commands outside of the sandbox
- When when working with Github Actions, you should always check for and use the latest Actions versions that are at least 7 days old, you can use `pinact run -update --min-age 7` to achieve this
- For the general PR conversation timeline (not line-level review comments), use `gh pr view --comments` or the REST `/issues/N/comments` endpoint
- When you need to read line-level review comments with their resolved state (e.g. triaging bot or human review feedback), fetch them via GraphQL in one call:  `gh api graphql -f query='query { repository(owner: "OWNER", name: "REPO") { pullRequest(number: N) { reviewThreads(first: 100) { nodes { id isResolved path line comments(first: 1) { nodes { author { login } body } } } } } } }' --jq '.data.repository.pullRequest.reviewThreads.nodes[] | select(.isResolved == false)'`
- When explicitly asked by the user to "close" or "resolve" a review comment, resolve the thread via the GraphQL mutation (do not reply to a comment unless instructed): `gh api graphql -f query='mutation($id: ID!) { resolveReviewThread(input: { threadId: $id }) { thread { isResolved } } }' -f id="PRRT_..."`
- Thread IDs start with `PRRT_`. Use `unresolveReviewThread` to reopen
- You can audit Github Actions security by running `zizmor .`
