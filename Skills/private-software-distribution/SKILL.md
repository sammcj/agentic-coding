---
name: private-software-distribution
description: Use when setting up private self-updating distribution to a project, with signed updates for closed testers through a Cloudflare Worker and R2.
metadata:
  version: 2026-11-04
---

Ships signed, self-updating builds to closed testers from a Cloudflare Worker, with no public downloads. It suits any updater that can send an auth header and verify a signature. This is a pattern to adapt, so read the updater's own docs for the client side.

## How it works

1. Client sends `GET` feed with `Authorization: Bearer <token>`.
2. Worker looks up `sha256(token)` in KV. Unknown gets 401, over a rate limit gets 429.
3. Registered client gets the feed from R2, then `GET /download/<archive>` with the same header.
4. Client verifies the signature against its embedded public key, then installs.

Two separate controls:

- **Access** comes from the Worker. KV holds only SHA-256 hashes of tokens, so a KV leak yields nothing usable.
- **Integrity** comes from the signature. The client accepts only archives signed by the key it shipped with, so a compromised bucket or Worker can't push code to testers.

Per project: a Worker, an R2 bucket, a KV namespace, a hostname and an update signing key. Releases run locally, so signing keys stay off CI.

## Setup

1. Ask the user for the project name, a hostname on their Cloudflare zone, and which rate limit namespaces are in use.
2. Copy `assets/` into the project root and rename `package.json.tmpl` to `package.json`. Fill in `wrangler.jsonc`, and add the feed file to `ROUTE` in `src/index.js` if it isn't `latest.json` or `appcast.xml`.
3. Generate the update key with the updater's tool and embed the public half in the client.
4. Provision Cloudflare and deploy.
5. Add the client.
6. Add a single release command, such as `make release`, following the pipeline below.
7. Write a `RELEASING.md` in the project covering releases, recovery, tester tokens and key rules, so operating it needs nothing from this skill.
8. Release, add a token with `scripts/beta-token.sh add <label>`, and give it and the first build to a tester by hand. Release again and confirm the first build updates itself.

Leave these to the user: key passwords, private key backups, sending tokens. Confirm before anything that publishes or deploys.

## Cloudflare

Run from `updates-worker/`:

```bash
npx wrangler@4 r2 bucket create <project>-updates
npx wrangler@4 kv namespace create <PROJECT>_BETA_TOKENS
npx wrangler@4 deploy
```

- Use a project-specific KV title. Sharing a namespace admits one project's testers to another's builds. If `kv namespace create` offers to add the binding, decline and put the id in `wrangler.jsonc`.
- Rate limit `namespace_id`s must be unique across the account and can't be listed. Each project's `wrangler.jsonc` holds its pair.
- R2 must be enabled once per account in the dashboard.
- The custom domain creates its own DNS record and certificate, even two levels deep, so the hostname must have no existing CNAME. Expect TLS failures for a few minutes after the first deploy.
- After deploy, expect 401 with no token, 401 with an unknown token, 404 on an unknown path and 405 on POST. The first publish proves R2.
- `wrangler r2 object put` handles up to 315 MB, and `wrangler` can't list a bucket.
- `wrangler whoami` exits 0 when logged out, so read its text.

## Client rules

- **No token, no request.** Keep the token in the Keychain or equivalent, and read it per check so a new one applies without a restart.
- **No feed, no updater.** Dev builds must not check, or they replace themselves with a release. Give them a separate bundle id.
- **Check at launch and daily,** plus a manual check with a 60 second cooldown, because the Worker allows 2 feed requests per token per minute. Automatic checks stay silent on failure.
- **Restart only on request,** after the download, and never during work the user would lose.
- **Keep the bundle id and team stable,** so macOS keeps its permissions across updates.

Known starting points:

- **Sparkle:** set `updater.httpHeaders`, generate with `generate_keys --account <project>` because the default account is shared, and leave `SUFeedURL` out of dev builds.
- **Tauri:** `check({ headers })` keeps the header for the download. A local build doesn't write `latest.json`, so generate it. Restart runs after `RunEvent::Exit`, so an `_exit` there stops the relaunch.
- **CLIs:** sign with `minisign`, which Tauri's signatures also wrap. Rust has `minisign-verify` and `self-replace`, and Go has `aead.dev/minisign` and `minio/selfupdate`.

## Release pipeline

Order it so anything that can fail cheaply runs before the version changes, and a refused release changes nothing:

1. Preflight: clean tree, release notes present, `wrangler` logged in, signing credentials found.
2. Stamp the version.
3. Build, sign, notarise.
4. Write the feed.
5. Verify before publishing: the archive passes against the embedded public key, a flipped byte fails, and the URL is https on the feed's host. Sparkle sends the token to every URL in the feed.
6. Commit and tag.
7. Upload archives first and the feed last, so the live feed never names a missing file.
8. Delete archives past the newest few tags.

Versions must only go up, or testers are offered nothing. `YYYY.M.<git commit count>` is valid semver and needs no state.

## Keys and signing

- One update key per project. Back up the private half straight away.
- A lost or changed key strands every install. To replace one, ship a release signed by the old key that embeds the new public key, then wait for testers to take it. The verify step must check that release against the old key.
- Moving the feed URL also strands installs, so choose the hostname carefully.
- Keep build credentials in the login Keychain, out of `.env` files and the repo.
- Re-signing with `codesign --force --deep` needs `--entitlements`, or permissions fail with no prompt.
- The DMG and the update archive must be the same build, so make no changes after notarisation.
- `notarytool` won't take a bare binary, so zip it. A bare Mach-O can't be stapled, and testers need the signed binary, not an earlier build output.

The Worker tests pass, and `wrangler deploy --dry-run` accepted its config on 2026-11-04. The rest comes from Sparkle and Tauri apps in production and CLI test builds, so check it against current docs.
