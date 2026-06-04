---
name: markedit-tools
description: Provides tools for managing MarkEdit, a macOS markdown editor
---

# Purpose

Help users configure and extend [MarkEdit](https://github.com/MarkEdit-app/MarkEdit), a free and open-source markdown editor for macOS.

## Key Capabilities

- Upgrade the MarkEdit app
- Install, upgrade, and manage MarkEdit extensions
- Configure MarkEdit advanced settings
- Answer questions related to MarkEdit

## Core Concepts

### File Locations

| Path | Description |
|------|-------------|
| `~/Library/Containers/app.cyan.markedit/Data/Documents/scripts/` | Extensions directory |
| `~/Library/Containers/app.cyan.markedit/Data/Documents/settings.json` | Advanced settings |
| `~/Library/Containers/app.cyan.markedit/Data/Documents/editor.css` | Custom stylesheets |
| `~/Library/Containers/app.cyan.markedit/Data/Documents/editor.js` | Custom JavaScript |

### Extension URLs

When a user provides an extension name, download from this URL pattern:

```
https://github.com/MarkEdit-app/extension-name/blob/main/dist/extension-name-kebab-cased.js?raw=true
```

Always normalise the extension name to kebab-case.

For example, [MarkEdit Preview](https://github.com/MarkEdit-app/MarkEdit-preview) is available at:
`https://github.com/MarkEdit-app/MarkEdit-preview/blob/main/dist/markedit-preview.js?raw=true`

When a user requests a "lite" build, it is located in the `lite` subfolder under `dist`:
`https://github.com/MarkEdit-app/MarkEdit-preview/blob/main/dist/lite/markedit-preview.js?raw=true`

The filename is identical to the standard build; do not add a `-lite` suffix.

If the dist file is not found (non-200 response), fall back to the GitHub **latest release** asset:

1. Fetch the latest release tag from the GitHub API:
   `https://api.github.com/repos/MarkEdit-app/extension-name/releases/latest`
2. Read the `tag_name` field from the response.
3. Download the asset using:

```
https://github.com/MarkEdit-app/extension-name/releases/download/{tag_name}/extension-name-kebab-cased.js
```

For example, if `dist/markedit-preview.js` is not available in the repository and the latest release tag is `v1.0.0`:
`https://github.com/MarkEdit-app/MarkEdit-preview/releases/download/v1.0.0/markedit-preview.js`

If the user provides a URL ending with `.js`, use that URL directly.

## Common Tasks

### Upgrading MarkEdit

1. Retrieve the latest release from [GitHub releases](https://github.com/MarkEdit-app/MarkEdit/releases)
2. Prompt the user to choose: `.dmg` or `apple-silicon.dmg`
3. Download the selected installer
4. Extract the `.app` bundle from the `.dmg`
5. Move the `.app` bundle to `/Applications`
6. Launch MarkEdit

### Re-Launching MarkEdit

```sh
osascript -e 'quit app "MarkEdit"' -e 'delay 1' -e 'launch app "MarkEdit"'
```

### Installing Extensions

1. Download the extension by name or URL
2. Place it in the extensions directory
3. Re-launch MarkEdit

Use the filename derived from the URL. If a file with the same name exists, prompt the user to confirm overwriting.

### Listing Extensions

List all `.js` files in the extensions directory with their sizes and last modification dates.

### Upgrading Extensions

1. Re-download the extension from the same source (lite or full)
2. Overwrite the existing file
3. Re-launch MarkEdit

### Uninstalling Extensions

1. Add `.js` suffix to the name if needed
2. Remove the file from the extensions directory
3. Re-launch MarkEdit

### Editing Preferences

1. Use the [wiki](https://github.com/MarkEdit-app/MarkEdit/wiki/Customization#advanced-settings) as reference
2. Edit `settings.json` directly
3. Re-launch MarkEdit

### Answering Questions

When users ask questions:

1. If it's a **task** (install, configure, upgrade) → perform the action
2. If it's a **customisation** question → explain editor.css, editor.js, or settings.json
3. If it's a **feature** question → fetch from wiki and issues
4. If unknown → suggest the [wiki](https://github.com/MarkEdit-app/MarkEdit/wiki) or GitHub issues

## Examples

- "Upgrade MarkEdit"
- "Install MarkEdit Preview extension"
- "Install the lite version of MarkEdit Preview"
- "Upgrade MarkEdit Preview"
- "List installed extensions"
- "Remove MarkEdit Preview"
- "Enable autoSaveWhenIdle in MarkEdit"
- "How to customise the editor appearance?"

## Error Handling

- If extension download fails from both the dist URL and the latest release, suggest checking the extension name or URL
- If `settings.json` is malformed, suggest validating JSON syntax
- If MarkEdit is not installed, suggest installation methods

## Documentation

When answering questions, refer to the [MarkEdit Wiki](https://github.com/MarkEdit-app/MarkEdit/wiki):

| Page | URL |
|------|-----|
| Customisation | https://github.com/MarkEdit-app/MarkEdit/wiki/Customization |
| Extensions | https://github.com/MarkEdit-app/MarkEdit/wiki/Extensions |
| User Manual | https://github.com/MarkEdit-app/MarkEdit/wiki/Manual |
| Text Processing | https://github.com/MarkEdit-app/MarkEdit/wiki/Text-Processing |
| Philosophy | https://github.com/MarkEdit-app/MarkEdit/wiki/Philosophy |

Search also https://github.com/MarkEdit-app/MarkEdit/issues?q=is%3Aissue%20state%3Aclosed for answered questions or discussed topics.

When answering questions related to development, refer to the [MarkEdit API](https://github.com/MarkEdit-app/MarkEdit-api) repository too.

---

## Chezmoi

The user manages their markedit config files with chezmoi.

After making changes to settings.json or other config files, ensure you add them to chezmoi (`chezmoi add --encrypt <file>`), but do not run any git commands.
