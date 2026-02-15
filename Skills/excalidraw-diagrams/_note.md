Note for this skill, if my PR to Excalidraw's MCP server gets merged (https://github.com/excalidraw/excalidraw-mcp/pull/32) the SKILL.md will need one line updated.

Line 106 currently says:

For the inline create_view workflow, use startBinding/endBinding with fixedPoint directly on arrow elements.

After the PR merges, the simpler start/end format would be preferred for create_view:

For the inline `create_view` workflow, use `start`/`end` with target element IDs on arrow elements:
`{ "type": "arrow", "id": "a1", "start": { "id": "r1" }, "end": { "id": "r2" }, "endArrowhead": "arrow" }`
Target shapes must appear before the arrow in the elements array.
