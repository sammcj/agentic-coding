<TOOLING_REQUIREMENTS>
  <MANDATORY_TOOL_USAGE>
    <TOOL name="package-version">
      <WHEN>Adding any packages or dependencies</WHEN>
      <PURPOSE>Use tools such as package version to ensure latest stable versions are used</PURPOSE>
    </TOOL>
    <TOOL name="context7">
      <WHEN>Implementing modern or complex libraries</WHEN>
      <PURPOSE>Use tools to such as context7 to access current documentation and implementation patterns</PURPOSE>
      <PROVIDES>resolve-library-id</PROVIDES>
        <DESCRIPTION> Resolves a package name to a Context7-compatible library ID and returns a list of matching libraries. You MUST call this function before 'get-library-docs' to obtain a valid Context7-compatible library ID. When selecting the best match, consider: - Name similarity to the query - Description relevance - Code Snippet count (documentation coverage) - GitHub Stars (popularity) Return the selected library ID and explain your choice. If there are multiple good matches, mention this but proceed with the most relevant one.
        <PARAMETERS>
          - `libraryName*` - Library name to search for and retrieve a Context7-compatible library ID.
        </PARAMETERS>
      <PROVIDES>get-library-docs</PARAMETERS>
        <DESCRIPTION> Fetches up-to-date documentation for a library. You must call 'resolve-library-id' first to obtain the exact Context7-compatible library ID required to use this tool.</DESCRIPTION>
        <PARAMETERS>
          - `context7CompatibleLibraryID*` - Exact Context7-compatible library ID (e.g., 'mongodb/docs', 'vercel/nextjs') retrieved from 'resolve-library-id'.
          - `topic` - Topic to focus documentation on (e.g., 'hooks', 'routing').
          - `tokens` - Maximum number of tokens of documentation to retrieve (default: 10000). Higher values provide more context but consume more tokens.
        </PARAMETERS>
      </PROVIDES>
    </TOOL>
    <TOOL name="fetch">
      <WHEN>Needing web content or documentation</WHEN>
      <PURPOSE>Efficient, lightweight content retrieval</PURPOSE>
    </TOOL>
    <TOOL name="think">
      <WHEN>Encountering complex problems or requiring intermediate reasoning</WHEN>
      <PURPOSE>Document thought process and solve complex issues</PURPOSE>
      <ESCALATION>Use 'think harder' if standard thinking insufficient</ESCALATION>
    </TOOL>
  </MANDATORY_TOOL_USAGE>
  <BEST_PRACTICES>
    <PRACTICE>Always consider available MCP tools before manual or guessed approaches</PRACTICE>
    <PRACTICE>Tool use is preferred for efficiency and accuracy</PRACTICE>
  </BEST_PRACTICES>
</TOOLING_REQUIREMENTS>
