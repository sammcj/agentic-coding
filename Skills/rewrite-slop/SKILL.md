---
name: rewrite-slop
description: Rewrites text containing AI slop to make it more human-like. Use when explicitly asked to rewrite AI generated text.
---

# rewrite-slop

You review and/or rewrite AI-flavoured text into prose that reads like a tired human journalist filing copy on deadline. If no other context is provided the input is a draft. The output is the same content with its AI fingerprint removed: meaning preserved, structure preserved, facts unchanged.

This is reviewing and/or editing, not authoring. You add no new information. You change no facts, names, numbers, dates, citations, or claims. You preserve quoted speech, code blocks, and direct citations exactly as they appear in the input.

---

## Phase 0: Triage technical artefacts

Scan the input and remove the following. These are pure AI markers with no legitimate content meaning. No judgement required, no replacement needed beyond removing them or, where they are URL parameters, stripping the parameter.

- URL tracking parameters: `utm_source=chatgpt.com`, `utm_source=openai`, `utm_source=copilot.com`, `referrer=grok.com`, and any `utm_*` parameter pointing at an LLM provider
- Citation markers: `citeturn0search0`, `iturn0image0`, `citeturn0news0`, `oai_citation`, `[attached_file:1]`, `[web:1]`, `<grok-card>`, `:contentReference[oaicite:N]{index=N}`
- JSON tails: `({"attribution":{"attributableIndex":"X-Y"}})`
- Placeholder tokens: `[Your Name]`, `INSERT_SOURCE_URL_30`, `2025-XX-XX`, `[Describe the specific section]`, any other unfilled bracket placeholder
- Decorative unicode: mathematical bold (`𝗯𝗼𝗹𝗱`), italic (`𝘪𝘵𝘢𝘭𝘪𝘤`), arrows used as bullets (`->`), multiplication signs in prose (`x` rendered as `×`)
- Em dashes (`—`) and en dashes (`–`): replace with comma, period, colon, parentheses, or hyphen as the sentence requires. Zero tolerance: not one is acceptable in the output.
- Smart quotes (`" "`, `' '`): replace with straight quotes (`"`, `'`). Zero tolerance.
- Double-dash sequences (`--`) used as em-dash substitutes: same treatment as em dashes.

---

## Phase 1: Classify

Set context for the rewrite.

- **Domain**: technical, academic, scientific, critical (review/critique), policy, fiction, blog or marketing, general prose, or other.
- **Register**: formal, neutral, casual.
- **Likely source model**: Claude (the default assumption; tells will skew Claude-specific), ChatGPT (curly quotes default, em dash heavy), Gemini ("broader context" framing), or unknown.
- **Voice resource selection**: source one of the voice files only if the input clearly belongs to that domain. If multiple match, pick the dominant one. If none clearly match, skip the voice resource entirely.

Voice resource rubric:

- Code, systems, infrastructure, APIs, engineering practice → `resources/technologist.md`
- Academic paper or thesis → `resources/researcher.md`
- Empirical findings, methods, data → `resources/scientist.md`
- Review or critique of a work → `resources/critic.md`
- Brief to decision-makers → `resources/policy-analyst.md`
- Fiction → `resources/novelist.md`

---

## Phase 2: Detect

Read the detection rubric. Scan the input. For each match, note the span and category. The output of this phase is internal: a list of flagged spans you carry into Phase 3.

### Tier 1: Claude sycophancy and chat residue (high signal)

The defining tells of Claude 4.x output. These rarely appear in genuine human prose.

- Sycophancy openers and validations: "You're absolutely right", "You're absolutely correct", "That's a great question", "Great question!", "Perfect!", "Excellent point!", "You're absolutely correct to point that out"
- Coding and agentic residue: "I'll help you...", "Let me [verb]", "Let me start by", "Let me first", "Let me check", "Now let me...", "I'll go ahead and"
- Helpful-chat closers: "I hope this helps", "Let me know if you'd like", "Feel free to", "Would you like me to", "I'd be happy to", "Happy to..."
- Performative anti-sycophancy: "to be straight to the point", "no BS", "I want to be honest with you", "to be clear with you"
- Parenthetical hedging asides: "(or, more precisely, ...)", "(and, increasingly, ...)"
- Progress-update meta-narration in long-form: "Let me mark X as complete", "Now I'll examine"
- False intimacy openers preceding the obvious: "Here's the thing:", "Let's be honest:", "The truth is"
- Claude metaphor tics: "smoking gun" (Claude reaches for this to dramatise findings or evidence)

### Tier 2: Claude self-describing vocabulary

These words appear in genuine human writing too. Flag when they are doing decorative or self-praising work rather than carrying a concrete claim a reader could verify.

- "complex", "complexity": flag when used as a vague intensifier ("the complex landscape of...", "navigating complexity", "this complex topic") rather than describing a specific technical property
- "thoughtful", "nuanced", "careful", "honest": flag any instance applied to the writer's own analysis or reasoning ("a thoughtful approach", "a nuanced view", "careful consideration", "an honest take", "honest reasoning", "to be honest")
- "concrete" as intensifier: "concrete evidence", "concrete examples", "concrete steps"

### Tier 3: cross-model AI vocabulary and structures

These appear in Claude output too, sometimes at lower density than GPT, but still slop.

**Marketing adjectives and abstract intensifiers**: vibrant, robust, comprehensive, pivotal, multifaceted, profound, crucial, vital, meticulous, valuable, enduring, groundbreaking, intricate, renowned, seamless, cutting-edge.

**Filler verbs as substitutes for "is" and "has"**: serves as, stands as, marks (verb), represents, boasts, features, offers. The simpler verb is almost always correct.

**Filler verbs (action without information)**: delve, dive into, leverage, harness, foster, fostering, bolster, underscore, streamline, facilitate, empower, garner, showcase, emphasise, enhance, highlight, align with, exemplify, unlock (figurative), navigate (figurative), utilise (use "use").

**Vague abstract nouns**: landscape (figurative), tapestry, testament, interplay, paradigm.

**Sentence-initial filler**: Additionally, Furthermore, Moreover, Notably, Consequently, Accordingly, In light of this, With this in mind, Building on this, That said, Having said that, It is important to note, It is worth mentioning, It should be noted that, It goes without saying.

**Rhetorical structures**:
- "Not just X, but also Y" / "It's not just X, it's Y" parallelism
- Decorative rule-of-three lists: "fast, efficient, and reliable"; "think bigger, act bolder, move faster"
- Snappy triads of unearned profundity: "Something shifted." "Everything changed." "But here's the thing."
- Mid-sentence rhetorical questions answered immediately: "The solution? It's simpler than you think."
- Vapid openers: "In today's rapidly evolving landscape", "As technology continues to evolve", "At the end of the day", "When it comes to"
- Definition openers: "X is defined as Y, encompassing A, B, and C"
- "Despite challenges" pivots: "Despite its [positive], [subject] faces challenges, including..."
- Hollywood endings: "As X continues to evolve, its potential remains limitless"
- Summary closers: "In summary", "In conclusion", "Overall", "Taken together"

**Participial-phrase tails**: sentences ending with an "-ing" clause that adds nothing the reader could not infer. "...creating a lively community within its borders." "...facilitating the movement of passengers and goods." "...contributing to the socio-economic development of the region."

**Comma splice with participial phrase** (reported at 2 to 5x human rate in AI output): "The system processes the data, revealing key insights."

**Hedging modals where confident assertion fits** (AI uses these at elevated frequency where humans would assert): may, might, could, suggest, indicate, appear, seem.

**Sourcing problems**:
- Weasel attribution without naming the source: "experts argue", "researchers have noted", "observers have cited", "industry reports suggest", "critics contend", "studies show", "research suggests"
- Exaggerated source counts: "several publications have noted" when one or two; "many critics" when one
- Knowledge-cutoff disclaimers: "As of my last knowledge update", "While specific details are limited"
- Speculation after disclaiming ignorance: "While specific details about X are not extensively documented... the region likely supports..."

**Fabricated significance**: "marks a pivotal moment", "represents a significant shift", "reflects the enduring legacy", "shaping the evolving landscape of", "stands as a testament to", "indelible mark", "deeply rooted", "key turning point".

**Notability framing without evidence**: "profiled in", "featured in", "active social media presence", "widely recognised".

**Promotional register in non-marketing prose**: "nestled in the heart of", "boasts a vibrant", "diverse array", "stunning natural beauty", "groundbreaking contributions".

**Awkward generic analogies**: "Every chord is a puzzle piece that finally clicks into a song." Plausible but generic.

**Elegant variation**: synonym cycling for the same noun across a passage (constraints / confines / restrictions / limitations / obstacles).

**Surface emotional language without evidence**: "this deeply resonates with communities", "evoking enduring faith and resilience".

### Tier 4: Claude structural fingerprint

Most of these come from the consumer claude.ai system prompt (which mandates "bullet points should be at least 1-2 sentences long", "bold key facts for scannability", "sentence-case headers", "high-level summary first"). Heavy in claude.ai output, lighter in API-direct output.

- `**Inline header:** description` bullet pattern
- Long descriptive bullets (1-2+ sentences each, where terse bullets would do)
- Bold noun phrases mid-sentence: "the **key tradeoff** is..."
- BLUF / TL;DR front-loading: first sentence summarises the entire answer, then expansion follows
- Triple-backtick fenced blocks for non-code: file paths, single commands, error strings
- Tables for non-tabular comparisons (pros/cons, "approach A vs B")
- `---` thematic breaks before headings
- Title case in headings (use sentence case)
- Inline natural-language lists in prose: "things include x, y, and z"
- Skipped heading levels (h3 without a preceding h2)
- Closing meta-summary or "to recap" paragraph the reader did not ask for
- Emoji in headings, bullets, or expository body text

### Things that look like AI but are not (do not flag on these alone)

Some patterns are commonly mistaken for AI tells but appear in genuine human writing:

- Academic vocabulary in academic prose
- Lack of typos (Grammarly is widespread)
- Avoidance of contractions in formal contexts (could be ESL, autistic writing, or deliberate register)
- Mixing casual and formal registers (technical writers, multi-author wikis)
- Letter salutations and valedictions in actual letters
- Unsourced claims (many legitimate documents have unsourced claims)

Em dashes, en dashes, and smart quotes are NOT exceptions to this. They are always removed regardless of context or apparent intent.

---

## Phase 3: Rewrite

Work from the positive style brief below plus the flagged spans from Phase 2. Do not re-scan the prohibition rubric during this phase; you have the spans already. The detection rubric is for detection. The rewrite works from positive targets only.

### Positive style brief

- Write like a tired journalist filing copy on deadline. Specific nouns, specific verbs.
- Concrete details over abstractions. A real date, a real name, a real number, a real place beats "significant growth".
- Use "is" and "has" when those are the right verbs. "Gallery 825 is LAAA's exhibition space" beats "Gallery 825 serves as LAAA's exhibition space".
- Vary sentence length deliberately. Mix short with long. A three-word sentence after three long ones lands.
- State opinions when the evidence supports them. Take a position rather than presenting false balance.
- Cite specific people, dates, and numbers. If the source cannot be named, cut the claim or rephrase as observation rather than authority.
- Use straight quotes (`'` and `"`) and standard punctuation. No em dashes, no en dashes, no smart quotes, no decorative unicode.
- Sentence-case headings.
- Express information as flowing prose. Reserve bullet lists for genuinely discrete items. Avoid the `**Header:** description` bullet pattern.
- Match the original's meaning, length (within ~10%), and structure. Paragraphs stay paragraphs. Sections stay sections. Genuine lists stay lists.
- Where the original front-loads a TL;DR/BLUF that the original author did not deliberately choose (i.e. it is sysprompt-driven scannability rather than authorial intent), restructure so the answer unfolds naturally.
- Repetition is natural. Reuse a noun rather than cycle through synonyms. "Constraints" stays "constraints" across the passage.

### Voice

If Phase 1 selected a voice resource, source it now and let it tune the brief. The voice resource adjusts register, vocabulary preferences, and rhythm. It does not override the rules above on em dashes, smart quotes, or factual fidelity.

### How to work the spans

For each flagged span, replace it with prose that fits the brief. Do not simply delete unless the span adds nothing. Where a sycophancy opener can be removed entirely without harming the prose ("You're absolutely right" before a substantive answer), remove it. Where filler like "additionally" can be removed without restructuring, remove it. Where a participial-phrase tail adds nothing, delete it and end the sentence on the prior clause.

If the input contains very few flagged spans relative to its length, return it largely unchanged. The skill is conservative. Over-rewriting clean text is a failure mode.

---

## Phase 4: Verify

**Always run this phase**

Single-pass rewriting reliably leaves some patterns it was instructed to remove; the verify pass exists to catch them.

Create a task for each of the following items. Mark tasks complete after verification.

Generate verification questions about your rewrite. Answer each by inspecting the rewritten text. For any "yes" on a defect question, fix it before returning the output.

- Are there any em dashes (`—`), en dashes (`–`), or `--` sequences? Any smart quotes (`" "` or `' '`)?
- Does any sentence start with Additionally, Furthermore, Moreover, Notably, Consequently, In conclusion, Overall, In summary, It is important to note?
- Does any paragraph contain three parallel adjectives, three parallel short phrases, or three parallel clauses used decoratively?
- Are there any unnamed authorities ("experts argue", "studies show", "observers have cited", "research suggests") I left in?
- Did I leave any sentence ending with an "-ing" clause that adds no information?
- Are there any "Despite [positive], [subject] faces challenges" pivots?
- Did I leave any inline-bold-header bullets (`**X:** description`)?
- Are there any "Let me", "I'll", "Happy to", "Let me know if", "I hope this helps", "Perfect!", "Excellent!" remaining?
- Did I leave any title-case headings? Any `---` thematic break before a heading? Any emoji in expository content?
- Does the rewrite assume frictionless rationality, universal cooperation, or unearned emotional resonance ("communities will enthusiastically adopt", "deeply resonates with")?
- Does any sentence claim significance, legacy, or a "broader trend" that is not demonstrated by a fact in the same paragraph?
- Did I introduce any fact, name, number, date, claim, or example not in the original and I cannot verify as true?
- Did I rewrite any quoted speech, code block, or direct citation that should have passed through unchanged?
- Is it too verbose? Could the same story, meaning, detail and intent be conveyed in fewer words?
- Does any pair of sentences contradict each other?

---

## Output

Return only the rewritten text. No preamble, no notes, no change log, no meta-commentary.

---

## Gotchas

- Quoted speech, code blocks, citations, and direct quotes pass through unchanged. The detector flags AI-shaped prose, not all unfamiliar text.
- The detection rubric exists for Phase 2 only. The rewriter (Phase 3) works from the positive style brief plus flagged spans. Re-reading the prohibition list during Phase 3 primes the very patterns the rewrite is removing.
- Length match within ~10%. Don't pad to look thorough; don't compress to look terse.
- If the input has nothing to rewrite (a code listing, a table of facts, dense reference material), return it unchanged.
- Do not rewrite the input's structure unless the structure itself is the slop (e.g. inline-bold-header bullets in flowing prose, a `---` thematic break before every heading, emoji in headers).
- Voice resources tune register and vocabulary; they do not override em-dash, smart-quote, or factual-fidelity rules.

---

## Voice resources

- `resources/technologist.md`: engineering, code, systems, infrastructure, APIs
- `resources/researcher.md`: academic papers and theses
- `resources/scientist.md`: empirical findings, methods, data
- `resources/critic.md`: book, film, art reviews and critique
- `resources/policy-analyst.md`: briefs to decision-makers
- `resources/novelist.md`: fiction
