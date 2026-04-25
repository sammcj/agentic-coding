# CalVer Setup

Use this when the project has no existing version convention, or has explicitly opted into date-based versions like `YYYY.M.COMMITS` (e.g. `2026.4.142`).

## Versioning behaviour

- `python3 scripts/version.py version` prints today's CalVer to stdout
- `python3 scripts/version.py stamp` (no `--version`) auto-computes CalVer and stamps both CHANGELOG.md and any discovered config files (`package.json`, `Cargo.toml`, `pyproject.toml`, `tauri.conf.json`, `VERSION`)
- Manual override: `--version X.Y.Z`
- The version increases monotonically as long as commits accumulate; CI must use `fetch-depth: 0`

## Build system integration

### Makefile

```makefile
# Auto-compute CalVer and stamp CHANGELOG + discovered config files.
.PHONY: stamp-version
stamp-version:
	uv run scripts/version.py stamp

# Auto CalVer (no args) or manual override (V=X.Y.Z).
.PHONY: version
version:
	@if [ -n "$(V)" ]; then \
		uv run scripts/version.py stamp --version "$(V)"; \
	else \
		uv run scripts/version.py stamp; \
	fi
```

If `build` or `release` targets exist, add `stamp-version` as a dependency.

### Justfile

```just
stamp-version:
    uv run scripts/version.py stamp

version ver="":
    #!/usr/bin/env bash
    if [ -n "{{ver}}" ]; then
        uv run scripts/version.py stamp --version "{{ver}}"
    else
        uv run scripts/version.py stamp
    fi
```

### package.json

```json
{
  "scripts": {
    "version": "uv run scripts/version.py stamp",
    "stamp-version": "uv run scripts/version.py stamp"
  }
}
```

## CLAUDE.md snippet

```markdown
Update CHANGELOG.md under the [Unreleased] section with concise bullet points grouped under Added/Changed/Fixed/Removed. Combine or update items refined within the same session. Don't add version numbers; the build process computes the CalVer at release time via `make stamp-version`. Truncate when the file exceeds 2000 lines.
```

Replace `make stamp-version` with `just stamp-version` or `npm run stamp-version` to match the project's build system.

## GitHub Actions

```yaml
on:
  workflow_dispatch:
    inputs:
      version:
        description: "Version override (leave empty for auto CalVer)"
        required: false

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # required for CalVer commit count
          persist-credentials: false

      - name: Stamp version
        id: version
        run: |
          if [[ -n "${{ inputs.version }}" ]]; then
            V="${{ inputs.version }}"
          else
            V=$(uv run scripts/version.py version)
          fi
          echo "version=$V" >> "$GITHUB_OUTPUT"
          uv run scripts/version.py stamp --version "$V"
```

## Gotchas

- `fetch-depth: 0` is mandatory; shallow clones produce wrong commit counts and a CalVer that goes backwards
- Apple's App Store accepts CalVer (any monotonically increasing three-integer string is valid for `CFBundleShortVersionString`), but reviewers occasionally query unfamiliar version formats
- If a project converts from CalVer to SemVer mid-flight, the changelog history mixes formats; that's fine, but the most recent entries should match the current scheme
