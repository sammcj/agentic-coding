<ADDITIONAL_RULES note="Important Coding Rules">
  <RULE> You see elegance in simplicity, this is very important to you as you favour a "less is more" approach with concise architecture, code structure and logic unless otherwise specified </RULE>
  <RULE> Avoid adding mock/placeholder code - don't be lazy - implement actual functionality </RULE>
  <RULE> Variables should have sensible defaults in the code but should be parameterised and available as configuration options where appropriate </RULE>
  <RULE> You see elegance in simplicity, this is very important to you as you favour a "less is more" approach with concise architecture, code structure and logic unless otherwise specified. </RULE>
  <RULE> Avoid over-engineering or introducing unnecessary abstractions unless the problem's complexity genuinely warrants them </RULE>
  <RULE> You MUST use Australian / British English spelling for all communication, comments and code, we are not American, we are Australian </RULE>
  <RULE> Avoid over-engineering or introducing unnecessary abstractions unless the problem's complexity genuinely warrants them </RULE>
  <RULE> CRITICAL: NEVER perform a git add, a git commit or a git push! </RULE>
  <RULE> CRITICAL: NEVER hardcode credentials or unique identifiers in code or documentation </RULE>
  <RULE> Prioritise using the tools available to you over manual approaches whenever appropriate </RULE>
  <RULE> Ensure files do not become too long, if a file is over 700 lines, consider splitting it into smaller files </RULE>
  <RULE> If you're working on a project with a Makefile, you should run a make lint, make format, make test and make build if those commands are available after completing your task </RULE>
  <RULE> Follow language and framework specific best practices </RULE>
  <RULE> When writing Golang, do not use the deprecated io/ioutil package, use the os and io packages instead </RULE>
  <RULE> When completing tasks from a dev plan checklist, remember to check off tasks as you complete them </RULE>
  <RULE> Never confidently state that you have resolved an issue completely until the user has verified that is the case </RULE>
  <RULE> Follow project's established architecture and component patterns </RULE>
  <RULE> Unless otherwise instructed make minimal changes to existing patterns and structures </RULE>
</ADDITIONAL_RULES>

<CONTRIBUTING_TO_OPEN_SOURCE when="If the user states they are contributing to an open source project">
  <RULE> You MUST align to the style of the existing code and you MUST follow the project's contribution guidelines and coding standards, start by reading CONTRIBUTING.md or similar files in the repository </RULE>
  <RULE> You MUST NOT add placeholder comments or code </RULE>
  <RULE> You MUST NOT add comments relating to your own development process or progress (e.g. Do NOT add comments like "improved function", "optimised version" etc.) </RULE>
</CONTRIBUTING_TO_OPEN_SOURCE>

<DOCUMENTATION_RULES>
  <RULE> When writing documentation, keep the focus technical. There's more value in detailing configuration and examples than showcasing features. When writing content ask yourself 'What is the value that this is adding?' </RULE>
</DOCUMENTATION_RULES>

<DIAGRAM_SPECIFICATIONS>
  <MERMAID_RULES>
    <RULE> IMPORTANT: You MUST NOT use round brackets ( ) within item labels or descriptions </RULE>
    <RULE> Use <br> instead of \n for line breaks </RULE>
    <RULE> Apply standard colour theme unless specified otherwise </RULE>
    <RULE> Mermaid does not support unordered lists within item labels </RULE>
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

<PARALLEL_TASKS note="Feature Implementation Priority Rules">
  <RULE> You may choose to complete tasks in parallel with subagents to speed up the development process </RULE>
  <RULE> Ensure sub-agents have clear boundaries and responsibilities with TODOs and clear instructions </RULE>
  <RULE> TASK FILE SPECIFICITY: Each task handles ONLY specified files or file types </RULE>
  <RULE> COMBINE SMALL UPDATES: Combine small config/doc updates to prevent over-splitting </RULE>

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
</PARALLEL_TASKS>
