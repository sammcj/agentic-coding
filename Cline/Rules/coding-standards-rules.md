<CODING_STANDARDS>
  <GENERAL_RULES>
    <RULE id="CS001">Avoid adding mock/placeholder code - don't be lazy - implement actual functionality</RULE>
    <RULE id="CS002">Ensure proper indentation and formatting in all code</RULE>
    <RULE id="CS003">Complete testing and documentation after primary implementation is complete</RULE>
    <RULE id="CS004">Consolidate multiple edits to the same file into single operations</RULE>
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
  <ERROR_HANDLING>
    <RULE id="EH001">For git merge conflicts, try copying file sideways, editing, then copying back</RULE>
  </ERROR_HANDLING>
</CODING_STANDARDS>
