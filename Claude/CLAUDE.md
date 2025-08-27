<NATURAL_WRITING_GUIDELINES note="For written content such as READMEs, documentation, conversational text, comments, etc">
  <NOTE>Guidelines for natural, human-like writing in READMEs, documentation, and conversational text.</NOTE>

  <BACKGROUND>
    <PROBLEM>AI absorbed institutional writing's worst habits from billions of press releases and SEO content. Fine-tuning rewards comprehensive, inoffensive writing with safety phrases and promotional tone.</PROBLEM>
    <DETECTION>Uniform 15-20 word sentences. Empty "-ing" phrases. Tourist brochure language.  Readers flee at "Moreover" or "rich cultural heritage".</DETECTION>
  </BACKGROUND>

  <CORE_PRINCIPLE>
    Match writing to purpose and audience:
    - PhD thesis: precision, not "utilises" everywhere
    - Casual email: warmth, not "I hope this finds you well"
    - Technical guide: clarity, not "it's important to note"

    Human qualities: Natural rhythm, specific language, confident uncertainty, varied structure
  </CORE_PRINCIPLE>

  <NATURAL_WRITING_TIPS>
    RHYTHM/STRUCTURE:
    - Mix 5-word sentences with 30-word ones (e.g. 8, 23, 14, 7, 19 words)
    - Vary paragraph length - some one sentence, others several
    - Trust implicit connections without signposting every step

    VOICE/TONE:
    - "first international acquisition" not "significant milestone"
    - "30km from the capital" not "vibrant hub"
    - No "-ing" phrase endings adding interpretation
    - Say "probably/seems to" not "research suggests"
    - Avoid self-congratulation

    CONTENT:
    - "2024 McKinsey study of 2,000 consumers" not "studies show"
    - Not everything has "rich cultural heritage"
    - No "In conclusion" unless genuinely complex
    - Add natural imperfection: tangents, specific examples, occasional repetition
    - **CRITICAL: British/Australian spelling only - NO American spelling**
  </NATURAL_WRITING_TIPS>

  <BETTER_PHRASES>
    - "stands as a testament to" → describe what it is
    - "plays a vital role in" → explain what it does
    - "highlighting/underscoring importance" → delete
    - "moreover/furthermore" → use only when essential
    - "experts believe" → cite specifically
    - "It's not just X, it's Y" → state directly
  </BETTER_PHRASES>

  <AVOID>
    - IMPORTANT: Avoid over used or cliche AI phrases such as: comprehensive (only if truly exhaustive), significant milestone (state achievement), feature complete (list what's done), production ready (specify why), deep dive (just "explore"), user engagement (describe behaviour), "furthermore", "significant milestone"
    - Every paragraph 3-4 sentences
    - Smart quotes and em dashes
    - Every list three items
    - Bullet points with bolded headers everywhere
    - American spelling
    - Transitions between every paragraph
    - Summary paragraphs (unless genuinely complex)
    - Marketing or enthusiastic, self congratulatory statements
 </AVOID>

  <CONTEXT_SPECIFIC>
    TECHNICAL: Start with solution. Skip "this section covers". Inline code/commands.
    BUSINESS: Main point first sentence. One topic per paragraph. No marketing or MBA speak.
    SCIENTIFIC: Findings first. Data before interpretation. Specific paper citations.
    SOFTWARE_DOCS:
      - What it does/how to configure, not why revolutionary
      - Technical info over philosophy
      - "Setup" not "🚀 Getting Started"
      - "Processes 1000 req/sec" not "Lightning-fast"
      - "Exports to PDF" not "Seamlessly transforms content"
      - Ask: "What value does this sentence add?", if none, delete
  </CONTEXT_SPECIFIC>

  <CHECKLIST>
    - Vary every 3rd-5th sentence length
    - Delete one transition per paragraph
    - Replace vague claims with specifics
    - Remove one "-ing" ending per paragraph
    - Question triads - need all three?
    - ALWAYS use British/Australian spelling
  </CHECKLIST>

  <FINAL_TEST>
    Does it sound like a real person explaining something they know, or Wikipedia crossed with a press release? Natural writing is messier, more varied, more specific than AI defaults.
  </FINAL_TEST>
</NATURAL_WRITING_GUIDELINES>

---

<CLAUDE_PARALLEL_TASKS note="Accelerate your work with parallel sub-agents">
- You may choose to complete tasks and tool calls in parallel with subagents to speed up the development process
- Ensure sub-agents have clear boundaries and responsibilities with TODOs and clear instructions
- Task file specificity: Each task handles ONLY specified files or file types
- Combine small updates: Combine small config/doc updates to prevent over-splitting
- REMEMBER: Sub agents could compete each other and erase each others changes, so ensure they are well defined, do not overlap and your instructions to them state that they are one of several sub agents working in the project, thus it's important to respect the defined boundaries and not to change files that are not within the scope of the task

  <WORKFLOW>
    Example Parallel Feature Implementation Workflow:
      1. **Component**: Create main component file
      2. **Styles**: Create component styles/CSS
      3. **Tests**: Create test files
      4. **Types**: Create type definitions
      5. **Hooks**: Create custom hooks/utilities
      6. **Integration**: Update routing, imports, exports
      7. **Remaining**: Update package definitions, documentation, configuration files
      8. **Review and Validation**: Coordinate integration, run tests, verify build, check for misalignments and gaps
  </WORKFLOW>
</CLAUDE_PARALLEL_TASKS>

---

<IMPORTANT_RULES>

  <SPELLING_AND_LOCALISATION note="IMPORTANT">
    <IMPORTANT note="This is VERY important">**CRITICAL: YOU MUST ALWAYS USE INTERNATIONAL / BRITISH ENGLISH SPELLING FOR ALL RESPONSES, DOCUMENTATION, COMMENTS, DEFINITIONS AND FUNCTION NAMES. DO NOT USE AMERICAN SPELLING.**</IMPORTANT>
    <BRITISH_ENGLISH_RULES>
      - ALWAYS ensure consistent use of British English in all your interactions, British English spelling MUST be used in ALL writing.
      - Look out for Z's when there should be S's
      - Using American spelling makes users sad, confused, frustrated and disappointed in your performance
      <KEY_PATTERNS>
          You must follow these British English spelling and usage rules during all your task:
          1. Use -our instead of -or (e.g., colour, favour, humour)
          2. Use -ise/-yse instead of -ize/-yze (e.g., organise, analyse)
          3. Use -re instead of -er (e.g., centre, metre)
          4. Use -ogue instead of -og (e.g., catalogue, dialogue)
          5. Use -ae/-oe instead of -e (e.g., anaemia, oesophagus)
          6. Use -ll- instead of -l- (e.g., travelled, cancelled)
          7. Use -t instead of -ed for certain past tense verbs (e.g., learnt, dreamt)
          8. Use -ence instead of -ense for nouns (e.g., defence, licence)
          9. Use British vocabulary (e.g., mum, aeroplane, autumn)
      </KEY_PATTERNS>
    </BRITISH_ENGLISH_RULES>
    <FINAL_CHECK>
      Before completing a task, verify: Did I use British English spellings?
    </FINAL_CHECK>
  </SPELLING_AND_LOCALISATION>

  <CODING_STYLE note="IMPORTANT">
    <FAVOUR_SIMPLICITY>
      - CRITICAL: Favour elegance through simplicity - use a "less is more" approach with concise architecture, code structure and logic unless specified otherwise
      - Avoid over-engineering or unnecessary abstractions unless complexity genuinely warrants them
    </FAVOUR_SIMPLICITY>
    - Follow language and framework best practices
    - Use sensible variable defaults, parameterised as configuration options where appropriate
    - Always use the latest available package versions unless otherwise specified
    - Follow project's established architecture and patterns
  </CODING_STYLE>

  <GOLANG>
  - Use os and io packages instead of deprecated io/ioutil
  - Build with -ldflags="-s -w" to reduce binary size
  - Do not build for Windows - we do not ever need or want Windows support
  </GOLANG>

  <WORKFLOW note="IMPORTANT">
  - Edit only what's necessary
  - Make minimal changes to existing structures unless instructed
  - Run make lint/format/test/build if available after completing tasks
  - You MUST fix all failing tests before marking task complete
  - Check off dev plan checklist tasks as completed
  - Don't ever state something is fixed unless you have confirmed it is by means of testing or measuring output or if the user has confirmed
  - Use Australian/British English spelling in all communication, comments and code
  </WORKFLOW>

  <DO_NOT_WASTE_TOKENS note="IMPORTANT">
    - Be succinct and concise - don't waste tokens
    - Combine multiple, nearby changes where possible
  </DO_NOT_WASTE_TOKENS>

  <NEVER_DO_THESE note="IMPORTANT">
    - NEVER perform git add/commit/push operations
    - NEVER hardcode credentials or unique identifiers
    - NEVER add comments pertaining only to development process (e.g. "improved function", "optimised version", "# FIX:")
    - NEVER claim an issue is resolved until user verification
    - NEVER implement placeholder or mocked functionality unless explicitly instructed - don't be lazy!
  </NEVER_DO_THESE>

  <TOOL_USE note="IMPORTANT">
    - CRITICAL: Prioritise available tools over manual approaches and use tools to reduce token usage
    - If you stuck don't just keep making things up - use the tools available to you to lookup package documentation or search the web
    - Using purpose built tools is often a better approach than searching the web (e.g. using get_library_docs for library documentation)
    - Keep files under 700 lines - split if longer, if you are asked to split large files and you have access to the find_long_files tool, use it to help identify potential targets
    - When asked to do math that's more than adding one or two items, use the calculator tool to ensure accuracy
  </TOOL_USE>

  <CONTRIBUTING_TO_OPEN_SOURCE when="If the user states they are contributing to an open source project">
    - You MUST align to the style of the existing code and you MUST follow the project's contribution guidelines and coding standards, start by reading CONTRIBUTING.md or similar files in the repository
    - You MUST NOT add placeholder comments or code
  </CONTRIBUTING_TO_OPEN_SOURCE>

  <DOCUMENTATION_RULES note="IMPORTANT">
    - When writing documentation, keep the focus technical.
    - There's more value in detailing configuration and examples than showcasing features.
    - When writing content ask yourself 'What is the value that this is adding?'
    - You MUST avoid marketing language, superlatives and self congratulatory statements
  </DOCUMENTATION_RULES>

  <DIAGRAM_SPECIFICATIONS>
    <MERMAID_RULES>
      -  IMPORTANT: You MUST NOT use round brackets ( ) within item labels or descriptions
      -  Use <br> instead of \n for line breaks
      -  Apply standard colour theme unless specified otherwise
      -  Mermaid does not support unordered lists within item labels
    </MERMAID_RULES>
    <STANDARD_THEME>
      classDef inputOutput fill:#FEE0D2,stroke:#E6550D,color:#E6550D
      classDef llm fill:#E5F5E0,stroke:#31A354,color:#31A354
      classDef components fill:#E6E6FA,stroke:#756BB1,color:#756BB1
      classDef process fill:#EAF5EA,stroke:#C6E7C6,color:#77AD77
      classDef stop fill:#E5E1F2,stroke:#C7C0DE,color:#8471BF
      classDef data fill:#EFF3FF,stroke:#9ECAE1,color:#3182BD
      classDef decision fill:#FFF5EB,stroke:#FD8D3C,color:#E6550D
      classDef storage fill:#F2F0F7,stroke:#BCBDDC,color:#756BB1
      classDef api fill:#FFF5F0,stroke:#FD9272,color:#A63603
      classDef error fill:#FCBBA1,stroke:#FB6A4A,color:#CB181D
    </STANDARD_THEME>
  </DIAGRAM_SPECIFICATIONS>

</IMPORTANT_RULES>
