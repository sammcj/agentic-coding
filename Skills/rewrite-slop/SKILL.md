---
name: rewrite-slop
description: Use when explicitly asked to review or rewrite AI-generated text so it reads as human, or with phrasings like "de-slop", "humanise this", "make it sound less like AI", or "remove the AI tells" or asks for a "slopsummary".
---

# rewrite-slop

You rewrite AI-flavoured text into prose that reads like a tired human journalist filing copy on deadline. If no other context is provided the input is a draft. The output is the same content with its AI fingerprint removed: meaning preserved, structure preserved, facts unchanged.

This is editing, not authoring. You add no new information. You change no facts, names, numbers, dates, citations, or claims. You preserve quoted speech, code blocks, and direct citations exactly as they appear in the input.

Tier 2's vocabulary is a snapshot of a ranking that moves. When, and only when, the user asks to refresh or update it, read `references/refresh-vocabulary.md` and follow it. Never do this as part of a rewrite.

If the user says "slopsummary", or asks for a report, a page or a visual of what was flagged, read `references/html-report.md`. Otherwise ignore it: the rewrite phases below never need it.

## Phase 0: Triage technical artefacts

Run the checker first. It applies the mechanical fixes below and prints the rest:

`python3 scripts/check_output.py --write <file>` (script path is relative to this skill's directory)

- Silent fixes are safe. Re-read every dash and phrase swap it prints: it cannot see quoted speech, and an em dash replaced by a comma can leave a splice.
- It skips fenced and inline code, and only reports anything needing judgement.
- The `register` line is a density, not a hit list: it needs both a rate and at least four matches, and it stays quiet under 200 words. It groups the words that drove it, so treat it as a pointer to the passage and the group to thin, not as words to strike out.
- Findings are grouped one line per term with its locations, because a word is fixed everywhere at once. `long-paragraph` marks a compression target, not a tell.

The script catches the low-hanging fruit and nothing more. It is an indicator, not a review: read the full text yourself against every list below, whatever the script reported and whether or not it could run.

Scan the input and remove the following. These are pure AI markers with no legitimate content meaning. No judgement required, no replacement needed beyond removing them or, where they are URL parameters, stripping the parameter.

- URL tracking parameters: `utm_source=chatgpt.com`, `utm_source=openai`, `utm_source=copilot.com`, `referrer=grok.com`, and any `utm_*` parameter pointing at an LLM provider
- Citation markers: `citeturn0search0`, `iturn0image0`, `citeturn0news0`, `oai_citation`, `[attached_file:1]`, `[web:1]`, `<grok-card>`, `:contentReference[oaicite:N]{index=N}`
- JSON tails: `({"attribution":{"attributableIndex":"X-Y"}})`
- Placeholder tokens: `[Your Name]`, `INSERT_SOURCE_URL_30`, `2025-XX-XX`, `[Describe the specific section]`, any other unfilled bracket placeholder
- Decorative unicode: mathematical bold (`𝗯𝗼𝗹𝗱`), italic (`𝘪𝘵𝘢𝘭𝘪𝘤`), arrows used as bullets (`→`), multiplication signs in prose (`x` rendered as `×`)
- Em dashes (`-`) and en dashes (`-`): replace with comma, period, parentheses, or hyphen as the sentence requires. Where the dash joins two independent clauses, prefer a period or comma; a colon there manufactures the mid-sentence colon splice flagged in Tier 3. Zero tolerance: not one dash is acceptable in the output.
- Smart quotes (`" "`, `' '`): replace with straight quotes (`"`, `'`). Zero tolerance.
- Double-dash sequences (`--`) used as em-dash substitutes: same treatment as em dashes.

Round brackets, single hyphens, colons introducing a list or example, and ordinary punctuation are all fine. Only the smart or decorative forms above are removed.

Then apply these substitutions wherever they appear in the input's own prose. Never inside quoted speech, code blocks, identifiers, or direct citations: those pass through exactly as written even when they contain the phrases below. Each preserves meaning; all but the last are swaps in place.

- "in order to" becomes "to"
- "due to the fact that" becomes "because"
- "in the event that" becomes "if"
- "at this point in time" becomes "now"
- "utilise" / "utilize" becomes "use"
- "numerous" becomes "many"
- "prior to" becomes "before"
- "It is important to note that" is deleted along with its leading capital, and the following clause becomes the sentence

## Phase 1: Classify

Set context for the rewrite.

- **Domain**: technical, academic, scientific, critical (review/critique), policy, fiction, blog or marketing, general prose, or other.
- **Register**: formal, neutral, casual.
- **Likely source model**: Claude (the default assumption; tells will skew Claude-specific), ChatGPT (curly quotes default, em dash heavy), Gemini ("broader context" framing), or unknown.
- **Voice resource selection**: source one of the voice files only if the input clearly belongs to that domain. If multiple match, pick the dominant one. If none clearly match, skip the voice resource entirely.

Voice resource rubric:

- Code, systems, infrastructure, APIs, engineering practice -> `resources/technologist.md`
- Academic paper or thesis -> `resources/researcher.md`
- Empirical findings, methods, data -> `resources/scientist.md`
- Review or critique of a work -> `resources/critic.md`
- Brief to decision-makers -> `resources/policy-analyst.md`
- Fiction -> `resources/novelist.md`

## Phase 2: Detect

Read the detection rubric. Scan the input. For each match, note the span and category. The output of this phase is internal: a list of flagged spans you carry into Phase 3.

### Tier 1: Claude sycophancy and chat residue (high signal)

The defining tells of Claude 4.x output. These rarely appear in genuine human prose.

- Sycophancy openers and validations: "You're absolutely right", "You're absolutely correct", "That's a great question", "Great question!", "Perfect!", "Excellent point!", "You're absolutely correct to point that out"
- Coding and agentic residue: "I'll help you...", "Let me [verb]", "Let me start by", "Let me first", "Let me check", "Now let me...", "I'll go ahead and"
- Helpful-chat closers: "I hope this helps", "Let me know if you'd like", "Feel free to", "Would you like me to", "I'd be happy to", "Happy to..."
- Performative anti-sycophancy: "to be straight to the point", "no BS", "I want to be honest with you", "to be clear with you"
- "Honest" framing in every form: the labels ("Honest take:", "Honest thoughts:", "Honest opinion:", "Honest review:", "Honest assessment:", "Honest recommendation:", "honest limits"), the asides ("to be honest", "in all honesty", "the honest truth"), and bare "honestly" as a sentence adverb. Diagnostic: remove the word. If the meaning is unchanged, it was announcing candour rather than being candid, so drop it and state the substance.
- Parenthetical hedging asides: "(or, more precisely, ...)", "(and, increasingly, ...)"
- Progress-update meta-narration in long-form: "Let me mark X as complete", "Now I'll examine"
- False intimacy openers preceding the obvious: "Here's the thing:", "Let's be honest:", "The truth is"
- Claude metaphor tics: "smoking gun" / "smoking-gun" (dramatising a finding), "load-bearing" / "load bearing", and "corpus" for any body of text that is not a linguistics or NLP dataset (say "the documents", "the transcripts", "these 400 emails")

### Tier 2: Claude's current register

Ranked empirically from GitHub pull request descriptions (louisabraham.github.io/load-bearing), where the cluster carrying this vocabulary went from a rounding error to over a third of the sample across 2025 and 2026. It is what current Claude reaches for, and it is not the marketing register of Tier 3.

Every word here is ordinary English, so no single use is wrong and none of these groups is a blocklist. Concentration is the tell. `check_output.py` prints a density per 1000 words, bands it ELEVATED or HEAVY, and names the group each word came from. Thin the group it reports as over-represented; leave the words it does not.

- **Assertive adverbs**, claiming a rigour the sentence has not demonstrated: plainly, quietly, genuinely, deliberately, outright, loudly, provably, empirically, vacuously, legitimately, structurally, precisely, demonstrably, identically, adversarially, faithfully, verbatim, merely, squarely. Delete the adverb: if the claim survives intact, it was emphasis, not work.
- **Absolute negation**: nobody, nothing, nowhere, never, neither, none, no one. One is emphasis. Three in a passage is the register. Keep the one whose scope is real and state the rest positively.
- **Code as agent**, verbs that give a mechanism intent: carries, holds, rests, survives, outlives, admits, refuses, decides, declares, governs, forbids, agrees, contradicts, falsified, refuted, restated, earns, pays, buys, drains, bites, swallows, degrades, escalates, short-circuits, self-heals, mints, stamps. Name the mechanism instead: "the flag is read twice" over "the flag carries the decision".
- **Adjudication nouns**, importing courtroom weight into a technical claim: refusal, premise, ruling, precedent, verdict, obligation, remedy, caveat, symptom, asymmetry, disagreement, shortfall, hazard, idiom. Replace with the thing itself: a refusal becomes what was rejected and by which check, a caveat becomes the condition, a remedy becomes the change that fixes it.
- **Structural metaphor nouns**: load-bearing, seam, ceiling, floor, lever, wedge, rung, ladder, chokepoint, backstop, carve-out, tripwire, machinery, knob. Tier 3 carries the exemption for literal use.

The rest of Tier 2 is Claude describing its own reasoning. These appear in genuine human writing too. Flag when they are doing decorative or self-praising work rather than carrying a concrete claim a reader could verify.

- "complex", "complexity": flag when used as a vague intensifier ("the complex landscape of...", "navigating complexity", "this complex topic") rather than describing a specific technical property
- "thoughtful", "nuanced", "careful": flag any instance applied to the writer's own analysis or reasoning ("a thoughtful approach", "a nuanced view", "careful consideration"). Tier 1 owns "honest" in all its forms.
- "concrete" as intensifier: "concrete evidence", "concrete examples", "concrete steps"

### Tier 3: cross-model AI vocabulary and structures

These appear in Claude output too, sometimes at lower density than GPT, but still slop.

Every list in this tier matches on meaning, not spelling. Where a word has a British and an American form, both count: emphasise and emphasize, recognised and recognized, revolutionise and revolutionize. Keep the input's own convention when you rewrite.

**Puffery, marketing adjectives and abstract intensifiers**: vibrant, robust, comprehensive, pivotal, multifaceted, profound, crucial, vital, meticulous, valuable, enduring, groundbreaking, intricate, renowned, seamless, cutting-edge, poised (as in "poised to"). Delete the adjective, or replace it with the measurement that earned it.

**Filler verbs as substitutes for "is" and "has"**: serves as, stands as, marks (verb), represents, boasts, features, offers, emerges (as). The simpler verb is almost always correct.

**Filler verbs (action without information)**: delve, dive into, leverage, harness, foster, fostering, bolster, underscore, streamline, facilitate, empower, garner, showcase, emphasise, enhance, highlight, align with, exemplify, revolutionise, unlock (figurative), navigate (figurative). These carry the sentence's grammar, so deleting the word alone leaves a hole: name the action instead ("we read the config" over "we leverage the config").

**Vague abstract nouns**: landscape (figurative), realm (figurative), tapestry, testament, interplay, paradigm. Name the things the noun stands in for, or cut the sentence.

**Verbosity**, where the length is itself the tell. Each of these survives deletion with the meaning intact:

- Padding that collapses to one word or none: "in terms of", "with respect to", "in the context of", "a variety of", "a range of", "a wide range of", "a number of", "a myriad of", "the fact that", "in order for", "for the purpose of", "advance planning".
- Redundant doublets, one word doing the work of two: "each and every", "first and foremost", "clear and concise", "various different", "end result", "past history", "basic fundamentals".
- Restating the question before answering it, and preamble that arrives before the substance.
- Paraphrase repetition: a sentence restating its predecessor in different words, or explaining what that sentence already told the reader. Keep the more specific one.

`check_output.py` reports the fixed phrases and flags prose paragraphs of 150 words or more, ten at most. Read each flagged paragraph and cut what carries nothing; a long paragraph that earns its length stays.

**Abstract metaphor nouns**: locus, vantage, nexus, primitive, surface, bedrock, scaffolding, modality, north star, flywheel.

Tier 2's structural group belongs here too. The density decides whether to look; the metaphor test below decides what to do with each one.

Plus these with their plain replacements:

- substrate becomes base
- "wedge in" becomes add
- vector becomes way
- gold-plating becomes "more than the job needs"
- ratchet becomes the mechanism's real name
- evacuate becomes "move out"
- endgame becomes "the last phase"

Flag only where the word is metaphor and a plainer one fits. Terms of art stay: embedding vector, attack vector, cryptographic primitive, API surface.

**Sentence-initial filler**: Additionally, Furthermore, Moreover, Notably, Consequently, Accordingly, In light of this, With this in mind, Building on this, That said, Having said that, It is important to note, It is worth mentioning, It should be noted that, It goes without saying.

**Rhetorical structures**:
- **Negation-antithesis**, the most overused AI pattern: "It's not X. It's Y.", "Not just X, but Y.", "This isn't about X, it's about Y.", "Forget X. Think Y.", "The question isn't X, it's Y.", "X is dead. Long live Y." **Swap test**: reverse to "It's not Y, it's X." If both read equally well, the contrast is decorative. Drop the negation, state the claim with its supporting fact.
- Decorative rule-of-three lists: "fast, efficient, and reliable"; "think bigger, act bolder, move faster"
- Snappy triads of unearned profundity: "Something shifted." "Everything changed." "But here's the thing."
- Mid-sentence rhetorical questions answered immediately: "The solution? It's simpler than you think."
- Vapid openers: "In today's rapidly evolving landscape", "As technology continues to evolve", "At the end of the day", "When it comes to"
- Definition openers: "X is defined as Y, encompassing A, B, and C"
- "Despite challenges" pivots: "Despite its [positive], [subject] faces challenges, including..."
- Hollywood endings: "As X continues to evolve, its potential remains limitless"
- Summary closers: "In summary", "In conclusion", "Overall", "Taken together"

**Participial-phrase tails**: sentences ending with an "-ing" clause that adds nothing the reader could not infer. "...creating a lively community within its borders." "...facilitating the movement of passengers and goods." "...contributing to the socio-economic development of the region."

**Comma splice with participial phrase**, several times more frequent in AI output than human: "The system processes the data, revealing key insights."

**Syntax tells**, each making the reader trace more steps or hold more in their head:

- Nominalisation: a verb turned into a noun propped up by a weak verb. "performed an analysis of" becomes "analysed"; "the implementation of X" becomes "implemented X".
- Stacked noun phrases: three or more nouns modifying each other ("context window budget allocation strategy"). Break them with a preposition or a verb.
- Landing sentences: a short declarative closing a paragraph to perform profundity ("That is the whole trick.", "The rest is detail."). Cut it, or fold its content into the sentence before.
- Negative anaphora: consecutive sentences opening with the same negation ("Not a X. Not a Y."). Keep one and state the positive claim.
- In-paragraph parallelism: consecutive sentences sharing a shape. Vary one.
- Forward references and long pronoun chains: "as we'll see below", or a pronoun three sentences from its noun. Name the thing where it is used.

**Dense sentences the reader has to re-read**: stacked subordinate clauses carrying more than one idea. Split by cutting, never by padding. Drop the clause carrying no information and let the rest stand; do not restate the subject to manufacture a second sentence. A split that adds words has failed, so if every clause earns its place, leave the sentence alone.

**Hedging modals where confident assertion fits**: may, might, could, suggest, indicate, appear, seem. Stacked hedges collapse to the single one carrying the real uncertainty: "could potentially possibly be argued that it might" becomes "may".

**Sourcing problems**:
- Weasel attribution without naming the source: "experts argue", "researchers have noted", "observers have cited", "industry reports suggest", "critics contend", "studies show", "research suggests"
- Exaggerated source counts: "several publications have noted" when one or two; "many critics" when one
- Knowledge-cutoff disclaimers: "As of my last knowledge update", "While specific details are limited"
- Speculation after disclaiming ignorance: "While specific details about X are not extensively documented... the region likely supports..."

**Puffery, fabricated significance**: "marks a pivotal moment", "represents a significant shift", "reflects the enduring legacy", "shaping the evolving landscape of", "stands as a testament to", "indelible mark", "deeply rooted", "key turning point".

**Puffery, notability framing without evidence**: "profiled in", "featured in", "active social media presence", "widely recognised" / "widely recognized".

**Puffery, promotional register in non-marketing prose**: "nestled in the heart of", "boasts a vibrant", "diverse array", "stunning natural beauty", "groundbreaking contributions".

**Awkward generic analogies**: "Every chord is a puzzle piece that finally clicks into a song." Plausible but generic.

**Sentences that name a feeling instead of a mechanism**: "the database stays close at hand", "SQL you can read", "types that follow your schema". **Generic-docs test**: if the sentence could appear unchanged in another document on the same topic, it says nothing here. Flag it, then fix from the input alone:

- input states the mechanism elsewhere: restate with that fact ("`.toSQL()` returns the string sent to the database")
- it does not: cut the sentence, even at the cost of length
- never supply a mechanism, number, or behaviour the input lacks, however true you believe it

**Colon as mid-sentence connector**.

- Stays: a colon introducing a list, an example, or a clause explaining the first ("One problem remains: the cache is stale")
- Flagged: a colon joining two clauses with no such relation, usually comparison framing ("If you're coming from traditional automation: instead of registering event handlers, you describe conditions"). Rewrite without the framing.

**False ranges**: "from X to Y" where X and Y are not endpoints on any scale ("from databases to deployment pipelines"). List the items directly.

**Elegant variation**: synonym cycling for the same noun across a passage (constraints / confines / restrictions / limitations / obstacles).

**Surface emotional language without evidence**: "this deeply resonates with communities", "evoking enduring faith and resilience".

### Tier 4: Claude structural fingerprint

Most of these come from the consumer claude.ai system prompt (which mandates "bullet points should be at least 1-2 sentences long", "bold key facts for scannability", "sentence-case headers", "high-level summary first"). Heavy in claude.ai output, lighter in API-direct output.

- Bold-header bullets whose label restates the line ("**Performance:** Performance improved by..."). Restatement is the test, not the punctuation: a label followed by new detail stays ("**Performance:** p99 dropped 40ms").
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

## Phase 3: Rewrite

Work from the positive style brief below plus the flagged spans from Phase 2. Do not re-scan the detection rubric here; you have the spans already, and re-reading the prohibitions primes the patterns you are removing.

### Positive style brief

- Write like a tired journalist filing copy on deadline. Specific nouns, specific verbs.
- Concrete details over abstractions. Semantic density: every sentence carries a claim the reader could check. A real date, a real name, a real number, a real place beats "significant growth".
- Use "is" and "has" when those are the right verbs. "Gallery 825 is LAAA's exhibition space" beats "Gallery 825 serves as LAAA's exhibition space".
- Vary sentence length deliberately. Mix short with long. A three-word sentence after three long ones lands.
- State opinions when the evidence supports them. Take a position rather than presenting false balance.
- Cite specific people, dates, and numbers. If the source cannot be named, cut the claim or rephrase as observation rather than authority.
- Use straight quotes (`'` and `"`) and standard punctuation. No em dashes, no en dashes, no smart quotes, no decorative unicode.
- Sentence-case headings.
- Express information as flowing prose. Reserve bullet lists for genuinely discrete items. Avoid bold-header bullets whose label merely restates the line; a bold lead-in followed by new detail is fine and stays.
- Match the original's meaning and structure. Paragraphs stay paragraphs, sections stay sections, genuine lists stay lists. Change the structure only where the structure is itself the slop: bold-header bullets in flowing prose, a `---` break before every heading, emoji in headers.
- Length moves one way only. The rewrite is never longer than the input, and never padded to fill space. There is no floor: cutting a bloated input by a third or a half is the correct result, not an overreach. What sets the length is the last sentence that still carries a claim, not a target percentage.
- Where the original front-loads a TL;DR/BLUF that the original author did not deliberately choose (i.e. it is sysprompt-driven scannability rather than authorial intent), restructure so the answer unfolds naturally.
- Repetition is natural. Reuse a noun rather than cycle through synonyms. "Constraints" stays "constraints" across the passage.

### Voice

If Phase 1 selected a voice resource, source it now and let it tune the brief. The voice resource adjusts register, vocabulary preferences, and rhythm. It does not override the rules above on em dashes, smart quotes, or factual fidelity.

### How to work the spans

Replace each flagged span with prose that fits the brief. Delete rather than replace only where the span adds nothing:

- sycophancy openers ("You're absolutely right" before a substantive answer)
- sentence-initial filler ("additionally")
- participial-phrase tails: delete and end the sentence on the prior clause

Sentences containing no flagged span pass through unchanged. Be conservative: over-rewriting clean text is the main failure mode. If the input has few flagged spans for its length, return it largely unchanged. If it has none (a code listing, a table of facts, dense reference material), return it unchanged.

## Phase 4: Verify

**Always run this phase**

Single-pass rewriting leaves patterns it was instructed to remove. This pass catches them.

`python3 scripts/check_output.py <rewrite> --against <original>` pre-answers every question below that a pattern can settle, so confirm those from its output rather than re-deriving them. Its silence is not a pass: it reads for patterns, not sense. The questions it cannot reach, and they are most of them, you answer against the full text yourself.

Create a task per question below. Answer each by inspecting the rewritten text, fix any "yes", then mark the task complete.

- Are there any em dashes (`-`), en dashes (`-`), or `--` sequences? Any smart quotes (`" "` or `' '`)?
- Does any sentence start with Additionally, Furthermore, Moreover, Notably, Consequently, In conclusion, Overall, In summary, It is important to note?
- Does any paragraph contain three parallel adjectives, three parallel short phrases, or three parallel clauses used decoratively?
- Are there any "It's not X. It's Y.", "Not just X, but Y.", or cousin negation-antithesis contrasts? Apply the swap test: if "It's not Y, it's X" is equally plausible, the contrast is decorative. Drop the negation and state Y directly.
- Are there any unnamed authorities ("experts argue", "studies show", "observers have cited", "research suggests") I left in?
- Did I leave any sentence ending with an "-ing" clause that adds no information?
- Are there any "Despite [positive], [subject] faces challenges" pivots?
- Did I leave any bold-header bullets whose label restates the line that follows (`**X:** X did...`)? A label followed by new detail stays.
- Are there any "Let me", "I'll", "Happy to", "Let me know if", "I hope this helps", "Perfect!", "Excellent!" remaining?
- Are there any metaphor tics left ("smoking gun", "load-bearing", "corpus" for an ordinary set of documents)? Replace with what the thing is or does.
- Does the register line still read ELEVATED or HEAVY? If so, thin the group it names first, working from the words it prints.
- Are there filler verbs or marketing adjectives left that the script named? Each is one edit applied everywhere, not one per location.
- Is there any "honest" or "honestly" left whose removal would not change the meaning?
- Are there abstract metaphor nouns left (substrate, vector, nexus, primitive, bedrock, scaffolding, north star, flywheel) used as metaphor where a plainer word fits? Literal terms of art stay: embedding vector, attack vector, cryptographic primitive, API surface.
- Could any sentence appear unchanged in another document on the same topic? If so it says nothing here. Restate it using a fact the input already gives, or cut it. Do not invent the fact.
- Is any colon joining two clauses where the second neither explains nor specifies the first?
- Are there "from X to Y" ranges where X and Y are not on a shared scale?
- Did I leave any title-case headings? Any `---` thematic break before a heading? Any emoji in expository content?
- Does the rewrite assume frictionless rationality, universal cooperation, or unearned emotional resonance ("communities will enthusiastically adopt", "deeply resonates with")?
- Does any sentence claim significance, legacy, or a "broader trend" that is not demonstrated by a fact in the same paragraph?
- Did I introduce any fact, name, number, date, claim, or example not in the original and I cannot verify as true?
- Did I rewrite any quoted speech, code block, or direct citation that should have passed through unchanged?
- Does every sentence still carry a claim? Cut any that does not, and do not stop cutting because the rewrite is already shorter.
- Did any paragraph the script flagged as long survive without being read? Did any padding phrase or doublet survive?
- Is the rewrite longer than the input? It should never be. If a sentence split added words, undo it.
- Does any pair of sentences contradict each other?

## Output

Return only the rewritten text. No preamble, no notes, no change log, no meta-commentary.
