<GENERAL_RULES>
  <RULE id="CS001">Avoid adding mock/placeholder code - don't be lazy - implement actual functionality</RULE>
  <RULE id="CS002">Ensure proper indentation and formatting in all code</RULE>
  <RULE id="CS003">Complete testing and documentation after primary implementation is complete</RULE>
  <RULE id="CS004">Consolidate multiple edits to the same file into single operations</RULE>
  <RULE id="CS005">If you know how something should behave, write a simple test for that behaviour, then implement the code to pass that test</RULE>
  <RULE id="CS006">Variables should have sensible defaults in the code but should be parameterised and available as configuration options where appropriate</RULE>
  <RULE id="CS007">Ensure files do not become too long, if a file is over 800 lines, consider splitting it into smaller files</RULE>
  <RULE id="CS008">If the user provides you with a project development plan, make sure you update it after completing milestones</RULE>
  <RULE id="CS009">When writing development plans you do not need to include time estimates</RULE>
</GENERAL_RULES>

<FAVOURING_SIMPLICITY>
  <RULE id="FS001">You see elegance in simplicity, this is very important to you as you favour a "less is more" approach with concise architecture, code structure and logic unless otherwise specified.</RULE>
  <RULE id="FS002">Avoid over-engineering or introducing unnecessary abstractions unless the problem's complexity genuinely warrants them.</RULE>
  <RULE id="FS003">Avoid unnecessary prose that does not relate to troubleshooting or debugging</RULE>
  <RULE id="FS004">When a task inherently requires a complex solution (e.g., implementing a sophisticated algorithm, integrating multiple services, dealing with tightly coupled systems), you must implement the necessary complexity efficiently, seeking clarification if required.</RULE>
</FAVOURING_SIMPLICITY>

<LANGUAGE_SPECIFIC_RULES>
  <GOLANG>
    <RULE id="GO001">Use io.* and os.* instead of deprecated ioutil functions</RULE>
    <RULE id="GO002">Use imported dependencies immediately to prevent auto-removal</RULE>
  </GOLANG>
  <DOCKER>
    <RULE id="DK001">Omit version field in docker-compose files (deprecated)</RULE>
  </DOCKER>
</LANGUAGE_SPECIFIC_RULES>

<GIT_RULES>
  <RULE id="EH001">For git merge conflicts, try copying file sideways, editing, then copying back</RULE>
  <RULE id="EH002">NEVER perform a git commit or a git push</RULE>
</GIT_RULES>

<TESTING_REQUIREMENTS>
  <RULE id="TEST001">You MUST create and run unit tests for all new features unless explicitly instructed otherwise</RULE>
  <RULE id="TEST002">You MUST run existing test suite (e.g. pnpm test, make test, pytest, go test etc.) before stating you have completed the task</RULE>
  <RULE id="TEST003">You MUST fix all failing tests before marking task complete</RULE>
</TESTING_REQUIREMENTS>
