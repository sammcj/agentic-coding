---
name: pptx-to-md
description: Convert a PPTX deck into per-slide markdown that preserves both the verbatim text and the meaning of embedded screenshots, diagrams and charts in their original layout positions. Use this skill whenever the user wants to extract content from or convert a slide deck / PPTX to markdown.
---

# Extract PPTX to per-slide markdown

This skill turns a `.pptx` file into one markdown file per slide, preserving layout context and image meaning. It does not paraphrase the text or describe images out of context. The output is suitable as input to a content uplift pass, a markdown-to-HTML build, or any other downstream transform.

## When to use

The deck mixes text with embedded screenshots, diagrams, charts, or code samples in a layout that matters (columns, side-by-side panels, callouts). Plain text extraction would lose either the layout or the meaning of the images.

If the deck is text-only with no meaningful images, `python -m markitdown deck.pptx` is faster and sufficient.

## Pipeline

```
PPTX -> prepare.py -> manifests + rendered JPGs + embedded PNGs
     -> dispatch one sub-agent per slide
     -> per-slide markdown files
     -> concatenate.py -> deck.md
```

The orchestrator (you, in the calling session) does two things: run the prepare and concatenate scripts, and dispatch one sub-agent per visible slide. Each sub-agent does the actual vision-and-text composition for one slide and writes one markdown file. Sub-agents are independent so they parallelise cleanly.

## Step 1 - prepare the workspace

```
python <skill>/scripts/prepare.py <pptx-path> <workspace-dir>
```

This unzips the PPTX, renders every visible slide to a JPG via LibreOffice and `pdftoppm`, then writes one manifest JSON per visible slide. After rendering, the script checks the JPG count matches the slide count and warns to stderr if they diverge - LibreOffice has been known to silently drop slides, so always read that warning before dispatching sub-agents.

Hidden slides (those with `show="0"` in the slide XML) are skipped by default. Pass `--include-hidden` to render and manifest them too; this enables the LibreOffice `ExportHiddenSlides` filter so hidden slides get real JPGs, not empty ones.

The workspace looks like:

```
workspace/
  unpacked/                    raw OOXML
  rendered/                    PDF + ordered slide JPGs
  manifests/slideNN.json       per-slide manifest
  slide_images/slideNN.jpg     rendered whole-slide JPG (stable name)
  embedded_images/slideNN/     embedded PNGs grouped per slide
  slides/                      empty - sub-agents write slideNN.md here
  deck_index.json              {visible, hidden, src_to_render}
```

## Step 2 - pilot before scaling

Pick 2-4 slides that span the deck's variety: one dense, one with screenshots, one with a custom diagram, one with sparse text. Dispatch sub-agents for those first using the prompt template at `references/sub_agent_prompt.md`, and compare the output against the exemplar in `references/example_slide.md`. Adjust the deck-specific notes in the prompt if needed (terminology to keep verbatim, terms to flag, conventions to enforce). Only then fan out to the rest of the deck.

The pilot is not optional. Per-deck variation in image style, layout density, and terminology means a prompt that works perfectly for one deck may produce bland or duplicated output on another.

## Step 3 - dispatch sub-agents in parallel

For each visible slide, dispatch one fresh sub-agent (named subagent type, not a fork - the agent only needs its manifest, so a fresh context is cheaper than inheriting the orchestrator's history). Each agent reads its manifest, the rendered slide JPG, and the embedded PNGs, then writes one slideNN.md.

To get the dispatch list, run:

```
python <skill>/scripts/dispatch_list.py <workspace-dir>
```

This emits one tab-separated row per slide that still needs a sub-agent (slide_number, manifest_path, output_path), skipping slides whose markdown already exists. That makes reruns after a partial failure trivial - no slide is re-extracted unnecessarily.

Suggested batching: **6 sub-agents per wave**. Larger waves work but produce more interleaved completion notifications, which is noisier without being faster. Each sub-agent typically takes 20-50 seconds.

The exact prompt to send each agent is in `references/sub_agent_prompt.md`. Substitute the placeholders before sending using `str.replace()` (not `str.format()` - the template contains literal braces). The prompt's rules - length-tuned image descriptions, external-links de-duplication, single-line reply - are not stylistic; they were each added after a real failure mode in earlier runs. See the prompt template for the rationale.

## Step 4 - concatenate

```
python <skill>/scripts/concatenate.py <workspace-dir> [--out deck.md] [--title "Deck title"]
```

This stitches the per-slide markdown into a single `deck.md` in source-slide order with a header noting any hidden slides that were excluded. It refuses to run if any expected slide markdown is missing, which is the right behaviour - a partial deck is rarely what's wanted.

## Gotchas

**LibreOffice's PDF export skips hidden slides by default.** This means the rendered JPG index drifts from the source slide number. `prepare.py` builds a `src_to_render` map and copies each rendered JPG to a stable `slide_images/slideNN.jpg` path keyed by source slide number, so manifests reference a stable name. If you regenerate the renders later, rerun `prepare.py` so the mapping stays fresh.

**Speaker notes mapping is not always 1:1.** This skill reads the slide-to-notesSlide relationship from the slide's `_rels` file rather than assuming `slideN.xml` maps to `notesSlideN.xml`. Most decks happen to be 1:1 but it isn't guaranteed.

**Source XML can have typos.** The pipeline preserves them verbatim. Correct them in a later content-uplift pass, not during extraction - this keeps extraction deterministic.

**Don't fork the sub-agents.** A fork inherits the orchestrator's full conversation context, which is large and unrelated. The sub-agent only needs the manifest. Use a named subagent type (e.g. `general-purpose`) so each starts fresh.

**Hidden slides are excluded by default.** Most decks contain hidden slides for a reason (work-in-progress, deprecated content, internal-only notes). Pass `--include-hidden` only when you want them in the output - the script then renders them properly via LibreOffice's `ExportHiddenSlides` filter, so they get real JPGs in the manifests.

**Dense screenshots benefit from higher DPI.** The default is 150 DPI. For decks where text inside screenshots needs to be readable in the rendered JPG, pass `--dpi 200` or `--dpi 250` to `prepare.py`.

## Dependencies

- LibreOffice (`soffice`) on PATH
- Poppler (`pdftoppm`) on PATH
- Python 3.10+

The prepare script checks for both binaries and exits early with a clear error if either is missing.
