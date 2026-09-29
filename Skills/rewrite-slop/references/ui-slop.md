# Slop in user interfaces

Read this when the input is an interface: a screenshot, a page, or component and style code. The tells below are visual and structural. Interface copy (headings, taglines, badges, empty states) is text, so it still goes through Phases 0 to 4.

## Steps

1. Create a task per step, each with its completion criterion.
2. Take stock of the interface. View screenshots; for code, read the components and styles, then run `rg -n 'gradient|backdrop-(filter|blur)|animate-(pulse|ping)|border-l-[0-9]|glow|\bInter\b|JetBrains' <dir> | head -100` to find candidate tells.
3. Judge each candidate against the tells below. For every one, ask what information the element gives the user. An element that gives none is slop.
4. Collect the interface copy and run it through the text phases.
5. Report or fix, whichever the user asked for. A review lists each finding as element, tell and fix, grouped by the headings below. A rewrite edits the code, keeps behaviour and data unchanged, and gets a screenshot afterwards when the environment can take one.

## Tells and their fixes

### Colour and surface

- Gradients everywhere: buttons, backgrounds, headline text, big numbers. Purple or blue to pink is the default. Use flat colour, and keep a gradient only where it encodes something, such as a heat scale.
- A different hue per card, stat or field, with no meaning behind it (green, blue and red KPI tiles for plain counts). Keep a neutral base, one secondary colour and one accent. Give a hue one meaning (error, warning, category) and hold it everywhere.
- Radial glow blobs behind the content, dark navy with coloured haze. Use a plain background.
- Glassmorphism: translucent blurred panels over glowing gradients. Use opaque surfaces with enough contrast.
- The stock brutalist variant: yellow and black, hard offset shadows, an ASCII-art banner, SCREAMING_SNAKE labels. Every model produces the same one. If brutalism is the brief, design it for this product.

### Decoration without state

- Status badges that can only ever show one value: "Active" on an ID that logs you out when inactive, "Active Student", "Verified" beside a logo, a green dot on an avatar. Test: can the badge ever show something else? If not, delete it.
- Pulsing dots and pills (`animate-pulse`, `animate-ping`) on static content. Save motion for something that is changing, such as a live connection or a running job.
- Fingernail cards: a rounded card with a thick coloured stripe down the left edge. Remove the stripe unless its colour encodes a category the user reads.
- An icon before every line of metadata (clock, person, door) where the value already says what it is. Keep an icon only where it reads faster than the label.
- A grid of cards, each topped with the same rounded-square icon tile over a title and a two-line grey description. Size cards by how much they hold, and cut descriptions that repeat the title.
- Emoji as icons: one per list item or heading, often the wrong object (a lollipop for sugar, a test tube for baking powder), or an emoji standing in for a logo. Use the project's icon set, or text alone.
- Chips on everything: tag pills that repeat the heading, corner chips on stat cards ("+2", "Score 75"). Keep a chip only when the user filters or acts on it.

### Typography and naming

- Inter for all text, and JetBrains Mono for anything near technology. Pick type for the product. If Inter is the house font, it stays.
- Letter-spaced mono capitals as eyebrow labels, often numbered ("02 · CLOUDFLARE EDGE", "THE SOLUTION"). Use a plain heading, or drop the label.
- `//` as a separator and fake-system naming on ordinary software: "CYBER_BAKE // PROTOCOL", "SYS.REQ", "PURGE_DATA", "EXECUTION_IN_PROGRESS", a "v2.0.26" pill on a recipe app. Name things in the user's words: "Reset", "Sponge cake", "3 of 13 steps done".
- A headline with one word picked out in the accent colour or a gradient. Set the headline in one colour.

### Layout and alignment

- Elements outside a box drift out of alignment: SVGs, ASCII art, timeline dots against their rail, time labels against their markers, icons against the text baseline. Measure rather than judge by eye: inspect the computed boxes, or overlay a grid on the screenshot.
- The landing-page template: an announcement pill, a headline with a coloured word, a grey subtitle, a code block or CTA pair, a strip of mono caps stats, and a glow behind it all. Build the page around what the product does.
- Vanity numbers and gauges: "50,000+ combinations", "335+ CITIES · ~3S TO URL", a 0% progress bar with "(0/13 TASKS)" on a checklist, an unrequested "SFX: ON" toggle. Show a number only when the user acts on it.

### Copy

- Prompt leakage: text that repeats what the builder told the agent. "Built with Hugo. Written from Neovim", "Built with modern C++20", "One campus. One app." (the brief to merge three campus apps shows through). Test: would a user of this screen care? If not, cut it.
- Hype vocabulary: elevate, seamless, next-generation, supercharge, unleash, empower, revolutionise. Tier 3 covers these; replace each with what the feature does.
- A grey subtitle under every H1 ("Experience the power of task management with our intuitive interface"), and greetings like "Welcome to your Dashboard, [Name] ✨". Title a working screen with what is on it, and drop the subtitle.

## Not slop on their own

- One gradient, one accent, or one badge whose state varies
- Inter, a mono font in a code view, a dark theme, rounded corners
- A stripe or icon that encodes a category the user filters by
- Brutalism or glass chosen on purpose and applied consistently

Flag a pattern when it is a default with no reason behind it, and weigh it higher when several stack on one screen.
