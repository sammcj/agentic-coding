---
name: analyse-design
description: Reverse-engineer an application's design system from its codebase and screenshots. Use when asked to analyse visual design, extract a colour palette, document UI patterns, identify typography and spacing systems, audit design consistency, or understand the design language of a frontend codebase.
# allowed-tools: Read,Write,Edit,Grep,Glob
# model: inherit
---

# Analysing Design Systems

Act as a UI/UX design analyst conducting analysis of frontend and design systems.

You may be asked to reverse-engineer the design system from a codebase, website or provided screenshots.

Unless otherwise stated by the user your goal is to produce a design system reference document a developer could use to build components that belong in this application.

## Where to Look

Scan for design-relevant sources in this priority order:

1. **Theme/token files** -- tailwind.config.*, theme.ts/js, tokens.json, design-tokens.*, variables.css/scss
2. **Global styles** -- global.css, app.css, index.css, _variables.scss, CSS custom properties (`:root` / `[data-theme]`)
3. **Component library config** -- shadcn components.json, MUI theme, Chakra theme, Ant Design config
4. **Layout components** -- shell, sidebar, header, navigation components for spacing and structure patterns
5. **Representative components** -- buttons, inputs, cards, modals for recurring visual patterns

Use `Glob` and `Grep` to locate these efficiently before reading files.

## Dimensions to Analyse

For each dimension, cite specific files and style definitions.

- **Design language** -- visual school/philosophy (e.g., neo-brutalist, material, glassmorphism, minimal flat). Mood conveyed. Unique visual signatures
- **Colour palette** -- extract actual values. Identify primary, secondary, accent, background, surface, semantic colours (error, success, warning). Note contrast ratios and dark/light mode support
- **Typography** -- font families, weight scale, size scale, line heights. How hierarchy is established
- **Spacing and layout** -- spacing scale, grid system, whitespace usage, information density, consistent sizing patterns
- **Component patterns** -- common shapes, border radii, shadow treatments, interaction states across buttons, inputs, cards, navigation, status indicators
- **Iconography** -- icon style (outline, filled, duotone), library if identifiable
- **Motion** -- animation patterns, easing curves, transition durations found in code
- **Responsive behaviour** -- breakpoints, layout shifts, mobile adaptations

## Output Format

Structure findings as:

1. **Overview** -- one paragraph: design philosophy, overall feel, distinguishing characteristics
2. **Colour System** -- table of colour tokens with hex/HSL values, usage context, and contrast notes
3. **Typography Scale** -- table of font families, sizes, weights, line-heights with semantic roles
4. **Spacing Scale** -- list of spacing values and where they apply
5. **Component Inventory** -- key patterns with border-radius, shadows, states, and the source file they come from
6. **Iconography and Motion** -- brief notes on icon style and any animation patterns
7. **Responsive Strategy** -- breakpoints and layout behaviour
8. **Consistency Notes** -- any inconsistencies, one-off values, or areas where the design system breaks down

## Tips

- If you have the ability to ask the user questions using `AskUserQuestion` or similar you can ask the user multi-choice questions to clarify the scope of the analysis, their desired goals and output format.
- Suggest the user provide screenshots if none are available -- visual context significantly improves the analysis.
- Leverage sub-agents with sufficient context and clear operating boundaries to parallelise work.
