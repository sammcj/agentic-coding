# Local Marketplace

Personal Claude Code plugin marketplace for custom LSP servers and tools.

## Structure

```
local-marketplace/
  .claude-plugin/marketplace.json   # Marketplace manifest (name, owner, plugin list)
  {plugin-name}/
    plugin.json                     # Plugin manifest (name, description, version)
    .lsp.json                       # LSP server config (if code intelligence plugin)
```

## Adding a New LSP Plugin

1. Create `{plugin-name}/plugin.json`:
   ```json
   {
     "name": "{plugin-name}",
     "description": "...",
     "version": "1.0.0"
   }
   ```

2. Create `{plugin-name}/.lsp.json` with required fields `command` and `extensionToLanguage`:
   ```json
   {
     "server-name": {
       "command": "binary-name",
       "args": ["serve"],
       "extensionToLanguage": {
         ".ext": "language-id"
       }
     }
   }
   ```

3. Add an entry to `.claude-plugin/marketplace.json` `plugins` array with `source: "./{plugin-name}"`

4. Update the marketplace and install:
   ```
   /plugin marketplace update local-marketplace
   /plugin install {plugin-name}@local-marketplace
   ```

## Gotchas

- Plugin `source` paths must use `./` prefix (relative to marketplace root). `../` paths are rejected
- The LSP binary must be on `$PATH`. Claude Code does not manage language server installation
- `extensionToLanguage` is required (not `languages`). Keys are file extensions, values are LSP language identifiers
- After adding or modifying plugins, run `/plugin marketplace update local-marketplace` then restart Claude Code
- `claude plugin validate <path>` exits 1 with no output on errors; not useful for debugging

## Current Plugins

| Plugin | Binary | Extensions | Notes |
|--------|--------|------------|-------|
| tofu-lsp | `tofu-ls` | `.tf`, `.tfvars` | OpenTofu language server (fork of terraform-ls) |
