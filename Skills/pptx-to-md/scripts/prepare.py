#!/usr/bin/env python3
"""Prepare a PPTX for slide-by-slide extraction.

Unpacks the PPTX, renders each visible slide to a JPG via LibreOffice and
pdftoppm, then writes one manifest JSON per visible slide. Each manifest
contains everything a sub-agent needs to compose markdown for that slide:
verbatim text from XML, the rendered slide JPG, the embedded PNG paths in
layout order, speaker notes, and external links.

Usage:
    python prepare.py PPTX_PATH WORKSPACE_DIR [--dpi 150] [--include-hidden]

Workspace layout produced:
    WORKSPACE_DIR/
        unpacked/                    raw OOXML
        rendered/                    PDF + ordered slide JPGs from LibreOffice
        manifests/slideNN.json       one per visible slide
        slide_images/slideNN.jpg     rendered whole-slide JPG (stable name)
        embedded_images/slideNN/     embedded PNGs grouped per slide
        slides/                      empty - sub-agents write slideNN.md here
        deck_index.json              {hidden, visible, src_to_render}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

NS_A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def slide_num(filename: str) -> int:
    m = re.search(r"(\d+)", filename)
    return int(m.group(1)) if m else 0


def unpack_pptx(pptx_path: Path, dest: Path) -> None:
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    with zipfile.ZipFile(pptx_path) as zf:
        zf.extractall(dest)


def render_deck(pptx_path: Path, out_dir: Path, dpi: int, include_hidden: bool = False) -> int:
    """Convert PPTX -> PDF (LibreOffice) -> per-slide JPGs (pdftoppm).

    Returns the number of JPGs produced. LibreOffice skips hidden slides
    by default; pass include_hidden=True to render them too.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        sys.exit("error: 'soffice' (LibreOffice) not found on PATH")
    pdftoppm = shutil.which("pdftoppm")
    if not pdftoppm:
        sys.exit("error: 'pdftoppm' (poppler) not found on PATH")

    if include_hidden:
        # JSON-form filter argument keeps hidden slides in the PDF.
        convert_to = (
            'pdf:impress_pdf_Export:'
            '{"ExportHiddenSlides":{"type":"boolean","value":"true"}}'
        )
    else:
        convert_to = "pdf"

    subprocess.run(
        [soffice, "--headless", "--convert-to", convert_to, "--outdir", str(out_dir), str(pptx_path)],
        check=True,
    )
    pdfs = list(out_dir.glob("*.pdf"))
    if not pdfs:
        sys.exit("error: PDF conversion produced no output")
    pdf = pdfs[0]
    subprocess.run([pdftoppm, "-jpeg", "-r", str(dpi), str(pdf), str(out_dir / "slide")], check=True)
    return len(list(out_dir.glob("slide-*.jpg")))


def list_slides(unpacked: Path) -> tuple[list[int], list[int]]:
    """Return (visible_slide_nums, hidden_slide_nums) in source order."""
    slides_dir = unpacked / "ppt" / "slides"
    visible, hidden = [], []
    files = sorted([f for f in slides_dir.iterdir() if f.suffix == ".xml"], key=lambda p: slide_num(p.name))
    for f in files:
        n = slide_num(f.name)
        tree = ET.parse(f)
        if tree.getroot().get("show") == "0":
            hidden.append(n)
        else:
            visible.append(n)
    return visible, hidden


def slide_text(unpacked: Path, n: int) -> list[str]:
    tree = ET.parse(unpacked / "ppt" / "slides" / f"slide{n}.xml")
    out: list[str] = []
    for p in tree.getroot().iter(f"{NS_A}p"):
        runs = [r.text for r in p.iter(f"{NS_A}t") if r.text]
        line = "".join(runs).strip()
        if line:
            out.append(line)
    return out


def slide_notes(unpacked: Path, slide_n: int) -> list[str]:
    """Read speaker notes for slide_n by following the slide's _rels."""
    rels = unpacked / "ppt" / "slides" / "_rels" / f"slide{slide_n}.xml.rels"
    if not rels.exists():
        return []
    notes_target = None
    for rel in ET.parse(rels).getroot():
        if "notesSlide" in rel.get("Type", ""):
            notes_target = rel.get("Target", "")
            break
    if not notes_target:
        return []
    m = re.search(r"notesSlide(\d+)\.xml", notes_target)
    if not m:
        return []
    notes_path = unpacked / "ppt" / "notesSlides" / f"notesSlide{m.group(1)}.xml"
    if not notes_path.exists():
        return []
    out: list[str] = []
    for p in ET.parse(notes_path).getroot().iter(f"{NS_A}p"):
        runs = [r.text for r in p.iter(f"{NS_A}t") if r.text]
        line = "".join(runs).strip()
        if line and not re.fullmatch(r"\d+", line):
            out.append(line)
    return out


def slide_rels(unpacked: Path, n: int) -> tuple[list[str], list[str]]:
    """Return (image_filenames, external_link_urls) referenced by slide n."""
    rels = unpacked / "ppt" / "slides" / "_rels" / f"slide{n}.xml.rels"
    if not rels.exists():
        return [], []
    images, links = [], []
    for rel in ET.parse(rels).getroot():
        target = rel.get("Target", "")
        rtype = rel.get("Type", "")
        if "image" in rtype.lower() or target.startswith("../media/"):
            images.append(os.path.basename(target))
        elif "hyperlink" in rtype.lower():
            links.append(target)
    return images, links


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pptx", type=Path, help="path to .pptx file")
    ap.add_argument("workspace", type=Path, help="output workspace directory")
    ap.add_argument("--dpi", type=int, default=150, help="JPG render DPI (default: 150)")
    ap.add_argument(
        "--include-hidden",
        action="store_true",
        help="treat hidden slides as visible (default: skip them)",
    )
    args = ap.parse_args()

    if not args.pptx.is_file():
        sys.exit(f"error: not a file: {args.pptx}")

    ws = args.workspace
    ws.mkdir(parents=True, exist_ok=True)
    unpacked = ws / "unpacked"
    rendered = ws / "rendered"
    manifests = ws / "manifests"
    slide_imgs = ws / "slide_images"
    embedded = ws / "embedded_images"
    slides_md = ws / "slides"
    for d in (manifests, slide_imgs, embedded, slides_md):
        d.mkdir(parents=True, exist_ok=True)

    print(f"[1/4] unpacking {args.pptx.name}")
    unpack_pptx(args.pptx, unpacked)

    print(f"[2/4] rendering deck (LibreOffice + pdftoppm @ {args.dpi} dpi"
          f"{', including hidden' if args.include_hidden else ''})")
    jpg_count = render_deck(args.pptx, rendered, args.dpi, include_hidden=args.include_hidden)

    print("[3/4] indexing slides")
    visible, hidden = list_slides(unpacked)
    # target is the set of slides we will produce manifests for, in source order.
    # LibreOffice emits the rendered JPGs in the same order it processed slides,
    # so target order maps 1:1 onto the JPG sequence whether hidden are included or not.
    target = sorted(set(visible) | set(hidden)) if args.include_hidden else visible
    src_to_render = {sn: i + 1 for i, sn in enumerate(target)}

    if jpg_count != len(target):
        print(
            f"warning: rendered {jpg_count} JPGs but expected {len(target)}. "
            "LibreOffice may have silently dropped a slide. "
            "Check rendered/ before dispatching sub-agents.",
            file=sys.stderr,
        )

    print(f"[4/4] writing manifests for {len(target)} slides")
    media_dir = unpacked / "ppt" / "media"
    written: list[str] = []
    for sn in target:
        text = slide_text(unpacked, sn)
        notes = slide_notes(unpacked, sn)
        imgs, links = slide_rels(unpacked, sn)

        rendered_jpg_path = None
        if sn in src_to_render:
            rj = rendered / f"slide-{src_to_render[sn]:02d}.jpg"
            if rj.exists():
                stable = slide_imgs / f"slide{sn:02d}.jpg"
                shutil.copy(rj, stable)
                rendered_jpg_path = str(stable)

        per_slide_dir = embedded / f"slide{sn:02d}"
        per_slide_dir.mkdir(exist_ok=True)
        embedded_paths: list[str] = []
        for im in imgs:
            src = media_dir / im
            if src.exists():
                dst = per_slide_dir / im
                if not dst.exists():
                    shutil.copy(src, dst)
                embedded_paths.append(str(dst))

        manifest = {
            "source_slide_number": sn,
            "is_hidden": sn in hidden,
            "rendered_slide_jpg": rendered_jpg_path,
            "embedded_images": embedded_paths,
            "external_links": links,
            "source_text_paragraphs": text,
            "speaker_notes_paragraphs": notes,
            "output_markdown_path": str(slides_md / f"slide{sn:02d}.md"),
        }
        mpath = manifests / f"slide{sn:02d}.json"
        mpath.write_text(json.dumps(manifest, indent=2))
        written.append(str(mpath))

    index = {
        "pptx": str(args.pptx),
        "workspace": str(ws),
        "visible": visible,
        "hidden": hidden,
        "extracted": target,
        "src_to_render": {str(k): v for k, v in src_to_render.items()},
    }
    (ws / "deck_index.json").write_text(json.dumps(index, indent=2))

    print(f"done. workspace: {ws}")
    print(f"  visible slides: {len(visible)}")
    print(f"  hidden slides: {hidden if hidden else 'none'}")
    print(f"  manifests: {len(written)}")
    print(f"  next: dispatch sub-agents using references/sub_agent_prompt.md, one per manifest")


if __name__ == "__main__":
    main()
