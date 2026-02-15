#!/usr/bin/env python3
"""Generate native .excalidraw files with all required element fields.

The `label` property on shapes works for Excalidraw MCP `create_view` inline
rendering but does NOT survive export to excalidraw.com or .excalidraw files.

Native Excalidraw requires bound text elements:
- Shape: "boundElements": [{"id": "text-id", "type": "text"}]
- Text: "containerId": "shape-id", "textAlign": "center", "verticalAlign": "middle"
- Text elements need: fontFamily, width, height, originalText, lineHeight, autoResize

This script provides helper functions that generate elements with all required
fields, including random seeds, version nonces, and proper bound text binding.

Usage as a library:
    from generate_excalidraw import rect, txt, arrow, scene, write_scene

Usage from CLI:
    python3 generate_excalidraw.py  # runs the built-in example
"""

import json
import os
import random
import sys
from typing import Any


def _base(id: str, typ: str, x: float, y: float, w: float, h: float, **kw) -> dict[str, Any]:
    """Create a base element with all required native Excalidraw fields."""
    return {
        "id": id,
        "type": typ,
        "x": x,
        "y": y,
        "width": w,
        "height": h,
        "angle": 0,
        "strokeColor": kw.get("stroke", "#1e1e1e"),
        "backgroundColor": kw.get("bg", "transparent"),
        "fillStyle": kw.get("fill", "solid"),
        "strokeWidth": kw.get("sw", 2),
        "strokeStyle": kw.get("ss", "solid"),
        "roughness": 1,
        "opacity": kw.get("opacity", 100),
        "groupIds": [],
        "frameId": None,
        "roundness": {"type": 3} if kw.get("round", False) else None,
        "seed": random.randint(1, 2**31),
        "version": 1,
        "versionNonce": random.randint(1, 2**31),
        "isDeleted": False,
        "boundElements": kw.get("bound", None),
        "updated": 1708000000000,
        "link": None,
        "locked": False,
    }


def rect(
    id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    bg: str,
    stroke: str,
    sw: int = 2,
    opacity: int = 100,
    bound_text: str | None = None,
    ss: str = "solid",
) -> dict[str, Any]:
    """Create a rectangle element.

    Args:
        id: Unique element ID.
        x, y: Top-left position.
        w, h: Width and height.
        bg: Background colour (hex).
        stroke: Stroke colour (hex).
        sw: Stroke width.
        opacity: Element opacity (0-100).
        bound_text: ID of a text element bound inside this rectangle.
        ss: Stroke style ("solid", "dashed", "dotted").
    """
    r = _base(id, "rectangle", x, y, w, h, bg=bg, stroke=stroke, sw=sw, opacity=opacity, round=True, ss=ss)
    if bound_text:
        r["boundElements"] = [{"id": bound_text, "type": "text"}]
    return r


def txt(
    id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    text: str,
    size: int,
    color: str = "#1e1e1e",
    align: str = "left",
    valign: str = "top",
    container: str | None = None,
) -> dict[str, Any]:
    """Create a text element.

    Args:
        id: Unique element ID.
        x, y: Position (left edge for standalone, approximate centre for bound).
        w, h: Text bounding box dimensions.
        text: The text content. Use \\n for multi-line.
        size: Font size in pixels.
        color: Text colour (hex).
        align: Horizontal alignment ("left", "center", "right").
        valign: Vertical alignment ("top", "middle").
        container: ID of the parent shape (for bound text). None for standalone.
    """
    t = _base(id, "text", x, y, w, h, stroke=color, sw=1)
    t.update({
        "text": text,
        "fontSize": size,
        "fontFamily": 1,
        "textAlign": align,
        "verticalAlign": valign,
        "containerId": container,
        "originalText": text,
        "autoResize": True,
        "lineHeight": 1.25,
    })
    return t


def arrow(
    id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    points: list[list[float]],
    stroke: str = "#1e1e1e",
    sw: int = 2,
    ss: str = "solid",
    end: str | None = "arrow",
) -> dict[str, Any]:
    """Create an arrow element.

    Args:
        id: Unique element ID.
        x, y: Start position.
        w, h: Bounding box (derived from points, but required by format).
        points: List of [dx, dy] offsets from x,y.
        stroke: Arrow colour (hex).
        sw: Stroke width.
        ss: Stroke style ("solid", "dashed", "dotted").
        end: End arrowhead type ("arrow", "bar", "dot", "triangle", or None).
    """
    a = _base(id, "arrow", x, y, w, h, stroke=stroke, sw=sw, ss=ss)
    a.update({
        "points": points,
        "lastCommittedPoint": None,
        "startBinding": None,
        "endBinding": None,
        "startArrowhead": None,
        "endArrowhead": end,
    })
    return a


def ellipse(
    id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    bg: str,
    stroke: str,
    sw: int = 2,
    opacity: int = 100,
    bound_text: str | None = None,
) -> dict[str, Any]:
    """Create an ellipse element.

    Args:
        id: Unique element ID.
        x, y: Top-left of bounding box.
        w, h: Width and height.
        bg: Background colour (hex).
        stroke: Stroke colour (hex).
        sw: Stroke width.
        opacity: Element opacity (0-100).
        bound_text: ID of a text element bound inside this ellipse.
    """
    e = _base(id, "ellipse", x, y, w, h, bg=bg, stroke=stroke, sw=sw, opacity=opacity, round=True)
    if bound_text:
        e["boundElements"] = [{"id": bound_text, "type": "text"}]
    return e


def diamond(
    id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    bg: str,
    stroke: str,
    sw: int = 2,
    opacity: int = 100,
    bound_text: str | None = None,
) -> dict[str, Any]:
    """Create a diamond element.

    Args:
        id: Unique element ID.
        x, y: Top-left of bounding box.
        w, h: Width and height.
        bg: Background colour (hex).
        stroke: Stroke colour (hex).
        sw: Stroke width.
        opacity: Element opacity (0-100).
        bound_text: ID of a text element bound inside this diamond.
    """
    d = _base(id, "diamond", x, y, w, h, bg=bg, stroke=stroke, sw=sw, opacity=opacity, round=True)
    if bound_text:
        d["boundElements"] = [{"id": bound_text, "type": "text"}]
    return d


def labeled_rect(
    id: str,
    x: float,
    y: float,
    w: float,
    h: float,
    bg: str,
    stroke: str,
    label: str,
    font_size: int = 16,
    sw: int = 2,
    opacity: int = 100,
    ss: str = "solid",
    text_color: str = "#1e1e1e",
) -> list[dict[str, Any]]:
    """Create a rectangle with centred bound text. Returns [rect, text].

    This is the convenience function for the most common pattern: a shape
    with text inside it. It calculates text dimensions and positioning
    automatically.

    Args:
        id: Unique element ID for the rectangle. Text ID will be f"{id}_t".
        x, y: Top-left position of the rectangle.
        w, h: Width and height of the rectangle.
        bg: Background colour (hex).
        stroke: Stroke colour (hex).
        label: Text content. Use \\n for multi-line.
        font_size: Font size in pixels.
        sw: Stroke width.
        opacity: Element opacity (0-100).
        ss: Stroke style.
        text_color: Text colour (hex).
    """
    text_id = f"{id}_t"
    lines = label.split("\n")
    max_line = max(lines, key=len)
    tw = len(max_line) * font_size * 0.5
    th = font_size * 1.25 * len(lines)
    tx = x + (w - tw) / 2
    ty = y + (h - th) / 2
    return [
        rect(id, x, y, w, h, bg, stroke, sw, opacity, bound_text=text_id, ss=ss),
        txt(text_id, tx, ty, tw, th, label, font_size, color=text_color,
            align="center", valign="middle", container=id),
    ]


def _find_element(elements: list[dict[str, Any]], element_id: str) -> dict[str, Any]:
    """Find an element by ID in the elements list."""
    for el in elements:
        if el["id"] == element_id:
            return el
    raise ValueError(f"Element '{element_id}' not found in elements list")


def _add_bound_element(element: dict[str, Any], bound_id: str, bound_type: str) -> None:
    """Add a bound element entry to a shape's boundElements list (mutates in place)."""
    if element["boundElements"] is None:
        element["boundElements"] = []
    element["boundElements"].append({"id": bound_id, "type": bound_type})


def bound_arrow(
    id: str,
    elements: list[dict[str, Any]],
    start_id: str,
    start_point: list[float],
    end_id: str,
    end_point: list[float],
    stroke: str = "#1e1e1e",
    sw: int = 2,
    ss: str = "solid",
    end_head: str | None = "arrow",
    start_head: str | None = None,
    gap: int = 5,
) -> dict[str, Any]:
    """Create an arrow bound to two shapes. Mutates the shapes' boundElements.

    Calculates arrow position and points from the shapes' geometry and the
    specified connection points. The shapes must already exist in `elements`.

    Args:
        id: Unique element ID for the arrow.
        elements: The working elements list (shapes are looked up and mutated here).
        start_id: ID of the shape the arrow starts from.
        start_point: fixedPoint on start shape as [fx, fy] where 0,0=top-left, 1,1=bottom-right.
            Common values: top=[0.5,0], right=[1,0.5], bottom=[0.5,1], left=[0,0.5].
        end_id: ID of the shape the arrow ends at.
        end_point: fixedPoint on end shape (same format as start_point).
        stroke: Arrow colour (hex).
        sw: Stroke width.
        ss: Stroke style ("solid", "dashed", "dotted").
        end_head: End arrowhead type ("arrow", "bar", "dot", "triangle", or None).
        start_head: Start arrowhead type (same options, default None).
        gap: Pixel gap between arrow endpoint and shape edge.
    """
    start_el = _find_element(elements, start_id)
    end_el = _find_element(elements, end_id)

    # Calculate absolute positions of the connection points
    sx = start_el["x"] + start_el["width"] * start_point[0]
    sy = start_el["y"] + start_el["height"] * start_point[1]
    ex = end_el["x"] + end_el["width"] * end_point[0]
    ey = end_el["y"] + end_el["height"] * end_point[1]

    dx = ex - sx
    dy = ey - sy
    dist = (dx**2 + dy**2) ** 0.5
    if dist < 60:
        import warnings
        warnings.warn(
            f"bound_arrow '{id}': distance between '{start_id}' and '{end_id}' is {dist:.0f}px. "
            f"Excalidraw recalculates bound arrow geometry and needs at least ~60px between "
            f"connection points to render correctly. Increase spacing between shapes.",
            stacklevel=2,
        )
    w = abs(dx)
    h = abs(dy)

    a = _base(id, "arrow", sx, sy, w, h, stroke=stroke, sw=sw, ss=ss)
    a.update({
        "points": [[0, 0], [dx, dy]],
        "lastCommittedPoint": None,
        "startBinding": {
            "elementId": start_id,
            "focus": 0,
            "gap": gap,
            "fixedPoint": start_point,
        },
        "endBinding": {
            "elementId": end_id,
            "focus": 0,
            "gap": gap,
            "fixedPoint": end_point,
        },
        "startArrowhead": start_head,
        "endArrowhead": end_head,
    })

    # Register the arrow on both shapes
    _add_bound_element(start_el, id, "arrow")
    _add_bound_element(end_el, id, "arrow")

    return a


def estimate_text_width(text: str, font_size: int) -> float:
    """Estimate text width in pixels. Approximate: chars * fontSize * 0.5."""
    return len(text) * font_size * 0.5


def estimate_text_height(text: str, font_size: int) -> float:
    """Estimate text height in pixels for single or multi-line text."""
    lines = text.split("\n")
    return font_size * 1.25 * len(lines)


def scene(elements: list[dict[str, Any]]) -> dict[str, Any]:
    """Wrap elements in a complete Excalidraw scene structure."""
    return {
        "type": "excalidraw",
        "version": 2,
        "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {
            "gridSize": None,
            "viewBackgroundColor": "#ffffff",
        },
        "files": {},
    }


def write_scene(elements: list[dict[str, Any]], path: str) -> None:
    """Write elements as a native .excalidraw file."""
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(scene(elements), f)
    print(f"Wrote {path}")


# ---------------------------------------------------------------------------
# Example: run directly to generate a simple test diagram
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    random.seed(42)
    elements = []

    # Title
    elements.append(txt("title", 150, 20, 300, 30, "Example Diagram", 24))

    # Two labelled boxes connected by a bound arrow (moves with shapes)
    elements.extend(labeled_rect("box1", 50, 80, 200, 70, "#a5d8ff", "#4a9eed", "Input"))
    elements.extend(labeled_rect("box2", 350, 80, 200, 70, "#b2f2bb", "#22c55e", "Output"))
    elements.append(bound_arrow("a1", elements, "box1", [1, 0.5], "box2", [0, 0.5]))

    out = sys.argv[1] if len(sys.argv) > 1 else "example.excalidraw"
    write_scene(elements, out)
