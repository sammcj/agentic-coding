---
name: json-schema-lookup
description: >-
  Query schemastore.org to validate config file structure, discover available
  options, and check valid values for JSON/JSONC/YAML configuration files.
  Use when editing or creating config files (tsconfig.json, package.json,
  GitHub Actions workflows, docker-compose.yml, .eslintrc, renovate.json,
  pyproject.toml, etc.) and you need to verify field names, check allowed
  values, or discover what options are available. Also use when a user asks
  about valid configuration for any tool/framework that publishes a JSON schema.
# model: inherit
# allowed-tools: Bash WebFetch
---

# JSON Schema Lookup via SchemaStore

Query schemastore.org's catalog of 800+ configuration file schemas to validate structure, discover options, and check allowed values.

## API

- **Catalog**: `https://www.schemastore.org/api/json/catalog.json`
  - Structure: `{ "schemas": [{ "name", "description", "fileMatch", "url", "versions"? }] }`
- **Individual schemas**: Fetch the `url` from the matching catalog entry

## Workflow

### 1. Find the schema

Search the catalog by name or filename pattern:

```bash
# Search by name (case-insensitive)
curl -s https://www.schemastore.org/api/json/catalog.json | jq '.schemas[] | select(.name | test("tsconfig"; "i")) | {name, url, fileMatch}'

# Search by filename match
curl -s https://www.schemastore.org/api/json/catalog.json | jq '.schemas[] | select(.fileMatch[]? | test("package\\.json")) | {name, url}'
```

Alternatively, use WebFetch on the catalog URL and ask for the relevant entry.

### 2. Fetch and inspect the schema

```bash
# Get the full schema
curl -s SCHEMA_URL | jq .

# List top-level properties
curl -s SCHEMA_URL | jq '.properties | keys'

# Inspect a specific field (type, enum values, description)
curl -s SCHEMA_URL | jq '.properties.FIELD_NAME'

# Check definitions/shared types (schemas use $ref to these)
curl -s SCHEMA_URL | jq '.definitions.DEF_NAME.properties'
```

### 3. Common queries

```bash
# Find all required fields
curl -s SCHEMA_URL | jq '.required'

# Find enum values for a field
curl -s SCHEMA_URL | jq '.properties.FIELD.enum'

# List nested properties (e.g. compilerOptions in tsconfig)
curl -s SCHEMA_URL | jq '.definitions.compilerOptionsDefinition.properties.compilerOptions.properties | keys'
```

## Tips

- Some schemas use `allOf`/`anyOf` composition -- check those arrays for the full property set
- The `versions` field on catalog entries provides version-specific schema URLs when available
- Schema URLs vary: some point to `json.schemastore.org`, others to `raw.githubusercontent.com`
- For large schemas, query specific paths rather than dumping the entire document
- Cache the catalog response locally if making multiple lookups in one session
