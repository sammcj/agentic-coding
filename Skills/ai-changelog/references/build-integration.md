# Build System Integration

Patterns for integrating `scripts/version.py` into common build systems. Choose the pattern matching the project's existing build tool.

## Makefile

Add these targets. If the project already has a `build` or `release` target, add `stamp-version` as a dependency.

```makefile
# Stamp CalVer version into all config files and CHANGELOG.md
stamp-version:
	uv run scripts/version.py stamp

# Update version: auto-compute CalVer or manual override
# Usage: make version          (auto CalVer)
#        make version V=1.2.3  (manual override)
version:
	@if [ -n "$(V)" ]; then \
		uv run scripts/version.py stamp --version "$(V)"; \
	else \
		uv run scripts/version.py stamp; \
	fi
```

If existing `build` or `release` targets exist, add the dependency:
```makefile
build: stamp-version
	# existing build commands...

release: stamp-version
	# existing release commands...
```

## Justfile

```just
# Stamp CalVer version into all config files and CHANGELOG.md
stamp-version:
    uv run scripts/version.py stamp

# Update version: auto-compute or manual override
version ver="":
    #!/usr/bin/env bash
    if [ -n "{{ver}}" ]; then
        uv run scripts/version.py stamp --version "{{ver}}"
    else
        uv run scripts/version.py stamp
    fi
```

## package.json scripts

```json
{
  "scripts": {
    "version": "uv run scripts/version.py stamp",
    "stamp-version": "uv run scripts/version.py stamp",
    "version:override": "uv run scripts/version.py stamp --version"
  }
}
```

## No build system

If the project has no Makefile, Justfile, or package.json, create a minimal Makefile with the targets above.

## GitHub Actions release workflow snippet

Add this step to an existing release workflow, or create a new one. The key requirements:
- `fetch-depth: 0` for CalVer commit count to work
- Run `stamp-version` before build/release steps

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
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history needed for CalVer commit count

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

      - name: Create release
        uses: softprops/action-gh-release@v2
        with:
          tag_name: v${{ steps.version.outputs.version }}
          draft: ${{ github.ref != 'refs/heads/main' }}
```
