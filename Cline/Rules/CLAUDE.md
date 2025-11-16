<SPELLING_AND_LOCALISATION note="IMPORTANT">
  <IMPORTANT note="This is VERY important">**CRITICAL: YOU MUST ALWAYS USE INTERNATIONAL / AUSTRALIAN ENGLISH SPELLING FOR ALL RESPONSES, DOCUMENTATION, COMMENTS, DEFINITIONS AND FUNCTION NAMES. DO NOT USE AMERICAN SPELLING.**</IMPORTANT>
  <AUSTRALIAN_ENGLISH_RULES>
    - ALWAYS ensure consistent use of Australian English in all your interactions, ***AUSTRALIAN ENGLISH SPELLING MUST BE USED IN ALL WRITING!***
    - Look out for Z's when there should be S's
    - Using American spelling makes users sad, confused, frustrated and disappointed in your performance
    <KEY_PATTERNS>
        You must follow these Australian English spelling and usage rules during all your task:
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
  </AUSTRALIAN_ENGLISH_RULES>
  <FINAL_CHECK>
    Before completing a task, verify: Did I use Australian English spellings?
  </FINAL_CHECK>
</SPELLING_AND_LOCALISATION>

<WRITTEN_LANGUAGE_RULES note="IMPORTANT rules for written content such as READMEs, documentation, conversational text, comments, function names etc">
  <AVOID>
    - IMPORTANT: DO NOT write over used or cliche AI phrases such as: comprehensive, significant milestone, feature complete, production ready, deep dive, user engagement, furthermore etc.
    - Smart quotes and em dashes
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
      - "Exports to PDF" not "Seamlessly transforms content"
      - Ask: "What value does this sentence add?", if none, delete
  </CONTEXT_SPECIFIC>

  <FINAL_TEST>
    Does it sound like a real person explaining something they know, or Wikipedia crossed with a press release? Natural writing is messier, more varied, more specific than AI defaults.
  </FINAL_TEST>
</WRITTEN_LANGUAGE_RULES>

---



---

<MERMAID_RULES>
    -  IMPORTANT: You MUST NOT use round brackets ( ) within item labels or descriptions
    -  Use <br> instead of \n for line breaks
    -  Apply standard colour theme unless specified otherwise
    -  Mermaid does not support unordered lists within item labels
  <STANDARD_THEME>
    classDef inputOutput fill:#E6F3FF,stroke:#4A90E2,color:#4A90E2
    classDef llm fill:#E8F5E8,stroke:#27AE60,color:#27AE60
    classDef components fill:#F0E6FF,stroke:#8E44AD,color:#8E44AD
    classDef process fill:#E8F5E8,stroke:#27AE60,color:#27AE60
    classDef stop fill:#F8D7DA,stroke:#E74C3C,color:#E74C3C
    classDef data fill:#E6F3FF,stroke:#4A90E2,color:#4A90E2
    classDef decision fill:#E8F5E8,stroke:#27AE60,color:#27AE60
    classDef storage fill:#F0E6FF,stroke:#8E44AD,color:#8E44AD
    classDef api fill:#FFF0E6,stroke:#E67E22,color:#E67E22
    classDef error fill:#F8D7DA,stroke:#E74C3C,color:#E74C3C
  </STANDARD_THEME>
</MERMAID_RULES>

---

<IMPORTANT_RULES>

  <CODING_STYLE note="**IMPORTANT**">
    <FAVOUR_SIMPLICITY>
      - CRITICAL: Favour elegance through simplicity - use a "less is more" approach with concise architecture, code structure and logic unless specified otherwise
      - Avoid over-engineering or unnecessary abstractions unless complexity genuinely warrants them
    </FAVOUR_SIMPLICITY>
    - Follow language and framework best practices
    - Use sensible variable defaults, parameterised as configuration options where appropriate
    - Make pragmatic architectural decisions and decisions when designing systems
    - Always use the latest available package versions unless otherwise specified
    - Follow project's established architecture and patterns
    - Typography: Use variables for common font properties such as colour and make use of the variables throughout the codebase rather than hard coding font colours. Ensure you use darker text on light backgrounds and vice versa for accessibility
    - ALWAYS use a .env or config file as a single source of truth for configuration values
  </CODING_STYLE>

  <GOLANG note="Rules for golang projects">
  - Use os and io packages instead of deprecated io/ioutil
  - Build with -ldflags="-s -w" to reduce binary size
  - If the user asks you to create an application using the "charm" family of packages, use your tools to read the documentation and implementation examples for the relevant charmbracelet packages to ensure you are using them correctly
  - When writing golang you can use the 'modernize' command to aid with modernising code: `go run golang.org/x/tools/gopls/internal/analysis/modernize/cmd/modernize@latest -fix -test ./...`
  - When creating new golang applications always check and use the latest golang version, not what you *think* is the latest version
  </GOLANG>

  <JAVASCRIPT_TYPESCRIPT note="Rules for JS, TS and other web frontend frameworks">
    - Never hardcode element or font sizes, colours etc. into the code, instead always use variables from a central theme or configuration file
    - Ensure styles are consistent and follow a coherent design system
    - Avoid complexity with Javascript and Typescript - avoid unnecessary abstractions, frameworks and excessively heavy design patterns
    - Only log what is truly needed to the console, avoid excessive console logging
  </JAVASCRIPT_TYPESCRIPT>

  <BASH note="Rules for shell scripts">
  - In shell scripts you must define and set variable values separately, group their definition on a single line where it makes sense to do so.
  </BASH>

  <BUILDING_MCP_TOOLS note="MCP Design Rules">
  - When creating MCP tools, think like a user interface designer, not an API wrapper.
  - Each tool should represent a task a human would perform ("search recent bugs", "get my notifications") rather than exposing API endpoints ("list_issues", "query_with_filters").
  - Abstract away technical details like internal IDs, pagination tokens, and multi-step operations—tools should accept human-readable inputs (team names, not team IDs) and handle the complexity internally.
  - If a user action requires multiple API calls, aim for one MCP tool, not several.
  </BUILDING_MCP_TOOLS>

  <WORKFLOW note="**IMPORTANT** you must follow this workflow for all tasks unless directly instructed otherwise by the user">
  - IMPORTANT: Edit only what's necessary! Make minimal changes to existing structures unless instructed
  - **You MUST NOT EVER state something is fixed unless you have confirmed it is by means of testing or measuring output and building the application**
  - Avoid adding too many comments, you ONLY need comments on complex logic that cannot be inferred
  - Run make lint/format/test/build if available after completing tasks
  - If working from a dev plan or checklist - you **MUST** check off tasks as they are completed to 100%, if you cannot be sure they are truly complete - do not state they are complete!
  - If you are stuck on a persistent problem that you and the user have tried to fix several times, suggest to the user that they can run the `/systematic-debugging-when-stuck` command to perform a fagan inspection
  - Use Australian/British English spelling in all communication, comments and code
  - Create a todo lists when working on complex tasks to track progress and remain on track
  - You **MUST** fix all failing tests before marking task complete
  - If the user asks you to ensure the code builds you **MUST** ensure you run a build or any other related commands before stating you've completed the work.
  </WORKFLOW>

  <DO_NOT_WASTE_TOKENS note="**IMPORTANT**: Being economical with tokens is always important">
    - Be succinct and concise - don't waste tokens
    - Combine multiple, file edits to the same file where possible
  </DO_NOT_WASTE_TOKENS>

  <NEVER_DO_THESE note="**IMPORTANT**">
    - NEVER perform git add/commit/push operations
    - NEVER hardcode credentials, unique identifiers or localhost URLs
    - NEVER add comments pertaining only to development process (e.g. "improved function", "optimised version", "# FIX:", "enhanced function" etc...)
    - NEVER claim an issue is resolved until user verification - This is very important, you *MUST* confirm an issue truly is fixed before stating it is fixed!
    - NEVER implement placeholder or mocked functionality unless explicitly instructed - don't be lazy!
    - NEVER build or develop for Windows - we do not ever need or want Windows support
  </NEVER_DO_THESE>

  <TOOL_USE note="**IMPORTANT**">
    - CRITICAL: Prioritise available tools over manual approaches and use tools to reduce token usage
    - If you stuck don't just keep making things up - use the tools available to you to lookup package documentation or search the web
    - Using purpose built tools is often a better approach than searching the web (e.g. using get_library_docs for library documentation)
    - Keep files under 700 lines - split if longer, if you are asked to split large files and you have access to the find_long_files tool, use it to help identify potential targets
    - When asked to do math that's more than adding one or two items, use the calculator tool to ensure accuracy
    - If you're exploring a large codebase or potentially very large files, use of the 'code_skim' tool to quickly understand the structure of the file(s) without all the implementation details
    - Remember can delegate tasks to a sub-agents with instructions to use specific tools and provide you with only the key information you're looking for to reduce token usage and optionally speed up the process further by doing this in parallel where it makes sense to do so
  </TOOL_USE>

  <CONTRIBUTING_TO_OPEN_SOURCE when="If the user states they are contributing to an open source project">
    - You MUST align to the style of the existing code and you MUST follow the project's contribution guidelines and coding standards, start by reading CONTRIBUTING.md or similar files in the repository
    - **IMPORTANT: You MUST NOT add placeholder comments or code!**
  </CONTRIBUTING_TO_OPEN_SOURCE>

  <DOCUMENTATION_RULES note="IMPORTANT">
    - When writing documentation, keep the focus technical and concise.
    - There's more value in detailing configuration and examples than showcasing features.
    - When writing content ask yourself 'What is the value that this is adding?'
    - Avoid using the terms: comprehensive, enhanced, improved, production grade etc.. - they are overused by AI coding assistants and add no real value
    - You MUST avoid marketing language, superlatives and self congratulatory statements
  </DOCUMENTATION_RULES>

</IMPORTANT_RULES>
