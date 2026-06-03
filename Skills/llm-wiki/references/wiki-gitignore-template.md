# Wiki .gitignore template

Written to the wiki project root at init (it is one of the files init creates). It keeps personal content and per-machine editor state out of git while leaving every tracked file plain markdown. Copy the block below verbatim. Lint offers it to a wiki that predates this and has no `.gitignore`.

```gitignore
# Personal, uncommitted notes - this clone only, never committed
local/

# OS noise
.DS_Store
Thumbs.db

# Obsidian per-machine state (vault config and graph are fine to commit; these are not)
.obsidian/workspace*
.obsidian/cache
.trash/

# Safety net: the wiki should hold no secrets (filter at ingest), but never commit these
.env
*.pem
*.key
```

Notes:
- `local/` is the line that powers personal content (`references/local-content.md`). The rest is noise reduction and a secrets backstop.
- Do not ignore `.obsidian/` wholesale if the user wants their vault settings shared; only the per-machine `workspace*` and `cache` files churn. Adjust to taste.
- This is the wiki's own `.gitignore`, separate from any `.gitignore` in the surrounding project.
