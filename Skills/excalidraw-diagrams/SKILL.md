---
name: excalidraw-diagrams
description: Use when asked to create or update Excalidraw diagrams. Provides guidance on Excalidraw best practices.
---

# Creating Excalidraw Diagrams

When creating Excalidraw diagrams, ensure you:

- Generate the layout with correct spacing
- Make consistent and logical use of colours, fonts, and shapes
- Text is correctly added within shapes, not as separate text elements (unless desired)
- Arrows and lines are correctly anchored / connected to shapes (not floating) so that when objects are moved any connections remain intact
- You save the Excalidraw diagram content to a file and link the file path
- Call `read_me` before your first `create_view` call each session - it provides the colour palette, camera sizes, layout rules, and element format reference.
- If the user has asked you to create Excalidraw diagrams but you do not have the Excalidraw MCP enabled, you should ask them to add it for you, they can configured it by using the HTTP MCP URL of: https://excalidraw-mcp-app.vercel.app/mcp and they can view the MCP documentation here: https://github.com/excalidraw/excalidraw-mcp

## Choose your workflow

Pick one based on what the user needs. Do not default to doing both.

### Inline preview only (`create_view`)

Use when the diagram is for the conversation only - the user wants to see it in the chat and does not need a file.

- Use `create_view` with `label` on shapes (works fine here)
- Use `cameraUpdate` to animate and guide attention
- No file output needed

### File output only (Python script)

Use when the user needs a `.excalidraw` file to open, share, edit, or keep. Skip `create_view` entirely.

- Generate the file with `scripts/generate_excalidraw.py` (see below)
- Provide the file path to the user
- Files can be opened by dragging into excalidraw.com, the Excalidraw desktop app, or VS Code with the Excalidraw extension

### Both (inline preview + file)

Use when the user wants to see the diagram in the chat AND keep a file. Note: these are built independently with different element formats. There is no data bridge between them - you define the diagram structure once conceptually but render it twice.

- `create_view` with `label` for the inline preview
- Python script with `labeled_rect` for the `.excalidraw` file

## Critical: text does not survive export

The `label` property on shapes is a `create_view` convenience only. It does NOT work in:
- `export_to_excalidraw` uploads (shapes render, text is invisible)
- `.excalidraw` files written from `create_view` checkpoint data

Do NOT use `export_to_excalidraw` for shareable diagrams. It seems to have a bug that can silently drop all text.

Native Excalidraw represents text inside shapes as two linked elements:
1. Shape: `"boundElements": [{"id": "text-id", "type": "text"}]`
2. Text: `"containerId": "shape-id"`, `"textAlign": "center"`, `"verticalAlign": "middle"`

The text element requires fields the `label` shorthand omits: `fontFamily` (1), `width`, `height`, `originalText`, `lineHeight` (1.25), `autoResize` (true).

All elements in .excalidraw files also need: `angle`, `seed`, `version`, `versionNonce`, `isDeleted`, `groupIds`, `frameId`, `updated`, `link`, `locked`.

Hand-writing this JSON is error-prone. Use the Python script instead.

## Python script: `scripts/generate_excalidraw.py`

Generates native .excalidraw files with all required fields. Can be used inline in a bash heredoc or imported as a library.

Key functions:

| Function | Returns | Purpose |
|----------|---------|---------|
| `labeled_rect(id, x, y, w, h, bg, stroke, label, ...)` | `[rect, text]` | Shape with centred bound text (handles all binding and field generation) |
| `rect(id, x, y, w, h, bg, stroke, ...)` | element | Rectangle without text |
| `txt(id, x, y, w, h, text, size, ...)` | element | Standalone or bound text |
| `bound_arrow(id, elements, start_id, start_point, end_id, end_point, ...)` | element | Arrow anchored to two shapes (mutates shapes' boundElements) |
| `arrow(id, x, y, w, h, points, ...)` | element | Unbound/floating arrow (use `bound_arrow` instead when connecting shapes) |
| `ellipse(...)` / `diamond(...)` | element | Other shape types |
| `write_scene(elements, path)` | writes file | Wraps in scene structure and saves |

Example:

```bash
python3 << 'PYEOF'
import sys, random
sys.path.insert(0, "/Users/samm/.claude/skills/excalidraw-diagrams/scripts")
from generate_excalidraw import *

random.seed(42)
elements = []
elements.append(txt("t1", 200, 10, 300, 30, "My Diagram", 24))
elements.extend(labeled_rect("a", 50, 60, 200, 70, "#a5d8ff", "#4a9eed", "Step One"))
elements.extend(labeled_rect("b", 350, 60, 200, 70, "#b2f2bb", "#22c55e", "Step Two"))
elements.append(bound_arrow("a1", elements, "a", [1, 0.5], "b", [0, 0.5]))
write_scene(elements, "/path/to/output.excalidraw")
PYEOF
```

For shapes without the `labeled_rect` convenience, pair `rect(..., bound_text="tid")` with `txt(..., container="rid", align="center", valign="middle")`.

## Arrow anchoring

By default, arrows float free - moving a shape leaves the arrow behind. Use `bound_arrow` instead of `arrow` to anchor arrows to shapes. It handles the bidirectional binding automatically (arrow references shapes, shapes list the arrow in `boundElements`).

`fixedPoint` values for connection points on shapes: top=`[0.5, 0]`, right=`[1, 0.5]`, bottom=`[0.5, 1]`, left=`[0, 0.5]`. Any `[fx, fy]` value works where 0,0 is the shape's top-left corner and 1,1 is bottom-right.

**Important**: shapes must already exist in `elements` before calling `bound_arrow`, since it looks them up and mutates their `boundElements`.

For the inline `create_view` workflow, use `startBinding`/`endBinding` with `fixedPoint` directly on arrow elements.

## Privacy

Note that if the diagram contains potentially sensitive information (e.g. detailed network diagrams, identifiable information etc...) and the user asks you to upload the diagram to excalidraw.com - you should first warn them that this will make the diagram publicly accessible and ask if they want to proceed.
