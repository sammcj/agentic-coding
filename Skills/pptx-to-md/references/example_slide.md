# Example output: a single extracted slide

A synthetic example showing both image-description length tiers and the full slide structure. Use it during the pilot to calibrate output before fanning out.

The depicted slide has a title, a left column of bullets, a screenshot of a config file on the right, and a small brand icon in the corner.

---

```
---
slide: 7
title: Configuring MCP Servers in settings.json
---

# Configuring MCP Servers in settings.json

MCP servers are declared in the `mcpServers` block of your settings file. Each entry needs:

- A unique server name (used as the namespace prefix for its tools)
- A `command` and optional `args` to launch the server process
- Optional `env` for credentials or feature flags

Settings can live at the user level (applies everywhere) or the project level (applies to one repo). User-level settings load first; project-level settings override matching keys.

> **Image: settings.json with three MCP servers configured**
> A VS Code editor view of a settings.json file with the `mcpServers` object expanded. Three servers are configured: a `filesystem` server pointing at the repo root, a `github` server with a `GITHUB_TOKEN` env var, and a `postgres` server with a connection-string arg. The `github` token line is highlighted in yellow with a margin annotation reading "store secrets in 1Password, not the file". Conveys both the shape of a real config and the reviewer's primary security concern.
> Source: `embedded_images/slide07/image12.png`

> **Image: Brand mark**
> Small circular brand logo in the slide corner.
> Source: `embedded_images/slide07/image01.png`

## Speaker notes

Walk through one server entry line by line. The audience is usually unsure where the file lives; show both `~/.claude/settings.json` and `.claude/settings.json` paths before moving on. If anyone asks about secrets, redirect to slide 9.

## External links

- https://docs.claude.com/en/docs/agents-and-tools/mcp
```

---

## What this example demonstrates

- **YAML frontmatter** with the source slide number and a title inferred from the slide.
- **Body text taken verbatim** from `source_text_paragraphs`, woven into the layout observed in the rendered JPG (left bullets, right screenshot).
- **Content-bearing image** gets a description specific enough that a reader without the image still grasps what was on screen and why it matters. Note the call-out on the highlighted line - that comes from looking at the rendered slide, not just the standalone PNG.
- **Decorative image** gets one sentence. The brand mark adds no information, so a longer description would be noise.
- **Speaker notes** verbatim, even if terse.
- **External links** present because that URL appeared on the slide and is not already in the body.
