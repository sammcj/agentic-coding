# Slide-extractor sub-agent prompt template

This prompt is dispatched to one fresh sub-agent per slide. Substitute the
placeholders before sending. Each agent runs independently with no shared
state - all context comes from its manifest.

## Placeholders

- `{SLIDE_NUMBER}` - source slide number (e.g. 12)
- `{TOTAL_SLIDES}` - total source slide count (e.g. 66)
- `{DECK_TITLE}` - human-readable deck title (e.g. "Effective Agentic Coding")
- `{MANIFEST_PATH}` - absolute path to slideNN.json
- `{OUTPUT_PATH}` - absolute path the agent should write slideNN.md to
- `{EMBEDDED_DIR_RELATIVE}` - relative path under the workspace where embedded images live (e.g. `embedded_images/slideNN/`)
- `{DECK_SPECIFIC_NOTES}` - optional - any deck-specific guardrails (e.g. "keep references to 'Cline' verbatim; we modernise content in a later pass")

## Substituting placeholders

The template body contains literal `{` and `}` braces inside the markdown structure shown to the agent (the YAML frontmatter, the image blockquote shape). Use `str.replace()` to fill in placeholders, not Python's `str.format()` or f-strings - those would try to parse every brace as a field and fail.

```python
prompt = template.replace("{SLIDE_NUMBER}", str(n)).replace("{TOTAL_SLIDES}", str(total))  # etc.
```

## Template

```
Extract source slide {SLIDE_NUMBER} of {TOTAL_SLIDES} from a deck "{DECK_TITLE}" into a high-fidelity markdown file.

Inputs at `{MANIFEST_PATH}`:
- `rendered_slide_jpg`: full slide as JPG (use for layout AND text the XML missed)
- `embedded_images`: high-res PNGs for individual visuals
- `source_text_paragraphs`: authoritative verbatim text from slide XML - ground truth
- `speaker_notes_paragraphs`: speaker notes
- `external_links`: hyperlinks on the slide

Steps:
1. Read the manifest JSON.
2. Read the rendered slide JPG to understand layout.
3. Read each embedded image to understand its content.
4. Write `{OUTPUT_PATH}`:

---
slide: {SLIDE_NUMBER}
title: <inferred>
---

# <Title>

<Body using source_text_paragraphs verbatim, woven into the layout from the rendered JPG. Preserve columns, panels, callouts, ordering.>

<Where an embedded image sits in the layout, insert at that position:>

> **Image: <short label>**
> <Description of what's shown. Length depends on the image:
>   - Decorative or repeating visuals (icons, brand motifs, generic graphics, repeated bricks/shapes): ONE sentence.
>   - Screenshots, diagrams, code blocks, content-bearing visuals: 2-4 sentences with specifics so a reader without the image still grasps WHY it's on the slide.>
> Source: `{EMBEDDED_DIR_RELATIVE}<image filename>`

## Speaker notes

<Verbatim notes, or "_(none)_" if empty.>

## External links

<Bulleted list ONLY for links that appear on the slide but are NOT already in the body content above. Omit the section entirely if all links are already in the body, or if there are none.>

Rules:
- Use source_text_paragraphs as authoritative wording. Do not paraphrase.
- The rendered JPG is for layout, ordering, and reading text the XML missed (e.g. SmartArt, grouped shapes). Include such text inline.
- Australian English. No emojis. No marketing fluff. Plain hyphens, plain quotes, no em-dashes.
{DECK_SPECIFIC_NOTES}

Reply with one short line confirming the path written and the inferred title. Nothing else.
```

## Why each rule matters

- **Three inputs in one agent.** Source text alone loses image context. Image
  captions alone lose layout context. Giving the agent text + rendered slide
  + standalone PNGs lets it use each input for what it's best at: source
  text as ground truth, rendered slide for layout and any text the XML
  missed (SmartArt, grouped shapes), individual PNGs for high-res image
  description.

- **Length-tuned image descriptions.** Without this rule, agents write the
  same 2-4 sentence description for every visual, including decorative
  brand icons that appear on every slide. The "one sentence for decorative,
  2-4 for content-bearing" rule was added after a pilot showed repetitive
  descriptions of identical lego-brick icons.

- **External links de-duplication.** Agents tend to copy URLs both inline
  in the body (where they appear on the slide) and into a dedicated
  External links section. The rule keeps each URL in one place.

- **Single-line reply.** Each agent returns only a confirmation line so the
  orchestrator's context stays clean across many parallel runs.

## Optional deck-specific notes

When the source deck has terminology that should not be modernised during
extraction (e.g. references to a deprecated tool that the user wants kept
verbatim until a later content-uplift pass), append a line like:

```
- The deck references "Cline" (an older agent) in places - keep verbatim; do not modernise.
```

Add it via `{DECK_SPECIFIC_NOTES}` rather than rewriting the template.
