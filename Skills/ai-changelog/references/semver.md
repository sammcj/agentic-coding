# SemVer Setup

Use this when the project already declares SemVer (CHANGELOG mentions "SemVer", git tags are `vX.Y.Z`, or a config file holds an explicit `X.Y.Z` version). SemVer projects have a source of truth for the current version; the script does not auto-compute.

## Source of truth

Pick one canonical source. The script can stamp into any of these when it discovers them at the repo root:

- Plain `VERSION` file (one line, `X.Y.Z`)
- `package.json` `version` field
- `Cargo.toml` `version` field
- `pyproject.toml` `version` field

Multi-source projects (e.g. a Cargo workspace with a `VERSION` file too) get all matching files stamped on each call.

## Versioning behaviour

- The script never auto-computes a SemVer. `--version X.Y.Z` is required at release time
- Format must match `^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$`
- Validation belongs in the build system, not the script (so the same script serves both schemes)

## Build system integration

### Makefile (canonical source = VERSION file)

```makefile
# Freeze CHANGELOG [Unreleased] using the version currently in VERSION.
# No-op if [Unreleased] is empty.
.PHONY: stamp-version
stamp-version:
	@V=$$(cat VERSION | tr -d '[:space:]'); \
	if command -v uv >/dev/null 2>&1; then \
		uv run scripts/version.py stamp --version "$$V" --changelog-only; \
	else \
		python3 scripts/version.py stamp --version "$$V" --changelog-only; \
	fi

# Bump version: writes VERSION (and any discovered manifest), freezes CHANGELOG.
# Usage: make version V=0.2.0
.PHONY: version
version:
	@if [ -z "$(V)" ]; then \
		echo "ERROR: pass V=X.Y.Z, e.g. make version V=0.2.0"; exit 1; \
	fi
	@if ! echo "$(V)" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$$'; then \
		echo "ERROR: '$(V)' is not a valid semver string"; exit 1; \
	fi
	@if command -v uv >/dev/null 2>&1; then \
		uv run scripts/version.py stamp --version "$(V)"; \
	else \
		python3 scripts/version.py stamp --version "$(V)"; \
	fi
```

`make version V=0.2.0` rewrites `VERSION` in place via the script's `VERSION` handler and freezes `[Unreleased]` as `[0.2.0]`.

### Makefile (canonical source = package.json / Cargo.toml / pyproject.toml)

If the project's package manifest already holds the canonical version, `stamp-version` should read that value rather than a separate `VERSION` file:

```makefile
# Reads version from package.json (or Cargo.toml / pyproject.toml).
.PHONY: stamp-version
stamp-version:
	@V=$$(node -p "require('./package.json').version"); \
	uv run scripts/version.py stamp --version "$$V" --changelog-only

# Bump: pass V=X.Y.Z, the script rewrites the manifest in place.
.PHONY: version
version:
	@if [ -z "$(V)" ]; then echo "ERROR: pass V=X.Y.Z"; exit 1; fi
	uv run scripts/version.py stamp --version "$(V)"
```

For Cargo: `V=$$(cargo metadata --format-version 1 --no-deps | jq -r '.packages[0].version')`. For pyproject: `V=$$(python3 -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])")`.

### Justfile

```just
stamp-version:
    #!/usr/bin/env bash
    V=$(cat VERSION | tr -d '[:space:]')
    uv run scripts/version.py stamp --version "$V" --changelog-only

version ver:
    #!/usr/bin/env bash
    if ! echo "{{ver}}" | grep -qE '^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$'; then
        echo "ERROR: '{{ver}}' is not a valid semver string"; exit 1
    fi
    uv run scripts/version.py stamp --version "{{ver}}"
```

### package.json scripts

```json
{
  "scripts": {
    "stamp-version": "node -e \"const v=require('./package.json').version; require('child_process').execSync('uv run scripts/version.py stamp --version '+v+' --changelog-only',{stdio:'inherit'})\"",
    "version:bump": "uv run scripts/version.py stamp --version"
  }
}
```

Use `npm run version:bump 0.2.0`.

## CLAUDE.md snippet

```markdown
Update CHANGELOG.md under the [Unreleased] section with concise bullet points grouped under Added/Changed/Fixed/Removed. Combine or update items refined within the same session. Don't add version numbers; at release time use `make version V=X.Y.Z` to bump the canonical version source and freeze the changelog (or `make stamp-version` to freeze using the existing version). Truncate when the file exceeds 2000 lines.
```

Replace `make` with `just`/`npm run` to match the project's build system.

## GitHub Actions

```yaml
on:
  workflow_dispatch:
    inputs:
      version:
        description: "Semver version (leave empty to use VERSION file)"
        required: false

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          persist-credentials: false

      - name: Stamp version
        id: version
        env:
          INPUT_VERSION: ${{ inputs.version }}
        run: |
          if [[ -n "$INPUT_VERSION" ]]; then
            if [[ ! "$INPUT_VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z0-9.]+)?$ ]]; then
              echo "ERROR: '$INPUT_VERSION' is not valid semver"; exit 1
            fi
            echo "$INPUT_VERSION" > VERSION
          fi
          V=$(tr -d '[:space:]' < VERSION)
          echo "version=$V" >> "$GITHUB_OUTPUT"
          python3 scripts/version.py stamp --version "$V" --changelog-only
```

## Gotchas

- **Never call the script without `--version` for a SemVer project.** With no `--version`, the script falls back to auto-computing CalVer and would silently stamp a date-based version into a SemVer changelog. The Makefile/Justfile recipes here always pass `--version`; preserve that
- The semver regex appears in three places (Makefile, Justfile, GH Actions). If you tighten it (e.g. to require pre-release format), tighten all three. Don't move validation into the script; the script is scheme-agnostic by design
- `--changelog-only` skips config file stamping. Use it in `stamp-version` (which only freezes the changelog) but NOT in `version` (which is bumping the canonical source and should stamp it too)
- The script's `VERSION` file handler only stamps if the existing content matches `^\d+\.\d+\.\d+`. If the file holds something else (e.g. a build number, a tag prefix), the script leaves it alone and the Makefile's `make version` won't update it. Convert the file format first or stamp it manually
