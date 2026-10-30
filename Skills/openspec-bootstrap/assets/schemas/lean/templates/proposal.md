# Proposal

## Why

<!-- Explain the motivation for this change. What problem does this solve? Why now? -->

## What Changes

<!-- One bullet per change a user or another component would notice. -->

## Capabilities

### New Capabilities
<!-- Capabilities being introduced. Name each capability for a cohesive system behaviour that can own related requirements as the system evolves. Do not name implementation tasks or proposal sections. Avoid broad catch-all names. Use kebab-case for path segments you introduce (e.g., user-auth or identity/user-auth) that follow the project's existing spec organisation. Each creates specs/<capability-path>/spec.md. -->
- `<capability-path>`: <brief description of what this capability covers>

### Modified Capabilities
<!-- Existing capabilities whose REQUIREMENTS are changing (not just implementation). Only list here if spec-level behaviour changes. Each needs a delta spec file. Use the exact existing path under openspec/specs/. Leave empty if no requirement changes. A change with no capabilities at all (pure refactor, tooling, docs) must set `skip_specs: true` in its .openspec.yaml - openspec validate rejects a zero-delta change without that marker. Do not invent a requirement just to satisfy validation. -->
- `<existing-capability-path>`: <what requirement is changing>

## Impact

<!-- External APIs, dependencies, docs or build flavours affected. No file or symbol lists. -->

## Decisions for the user

<!-- Choices the user needs to see, each with a recommended answer. Omit if none. -->
