<IMPORTANT_RULES_YOU_MUST_FOLLOW>
  <IMPORTANT>⚠️ THESE ARE _ALL_ CRITICAL RULES YOU **MUST** FOLLOW ⚠️</IMPORTANT>

  <CRITICAL_CODING_RULES>
    <TASK_AND_CONTEXT_MANAGEMENT>
      <IMPORTANT>Remember to start a new task when your context window is over 70%.</IMPORTANT>
    </TASK_AND_CONTEXT_MANAGEMENT>
    <PACKAGE_MANAGEMENT>
      <IMPORTANT>When adding packages to an application use the package-version MCP server's tools to ensure you use the latest versions.</IMPORTANT>
    </PACKAGE_MANAGEMENT>
    <PROJECT_CONTEXT>
      <RULE>Check project files before suggesting structural or dependency changes.</RULE>
      <RULE>If you're using the diff edit tool and it fails, try again before using the next option.</RULE>
      <RULE>You may complete multiple tasks at once when you are editing the same file.</RULE>
    </PROJECT_CONTEXT>
    <QUALITY_ASSURANCE>
      <RULE>Don't complete the analysis prematurely. If you think you've completed the task but have no way of verifying it, you should ask the user to verify your changes.</RULE>
      <RULE>If you're modifying software that has an existing test suite, you should run the tests and ensure they pass when you think you've completed the task.</RULE>
      <RULE>When updating documentation or fixing multiple errors in the same file do so in one edit rather than opening and editing it many times.</RULE>
    </QUALITY_ASSURANCE>
    <LANGUAGE_SPECIFIC_RULES>
      <GOLANG>
        <RULE>When writing golang code always use io. and os. instead of deprecated ioutil functions.</RULE>
        <RULE>When adding go dependencies to a file, remember that the autoformatter will remove them unless you actually use them in the code, so make sure to use them in the code when you add them before saving.</RULE>
      </GOLANG>
      <DOCKER>
        <RULE>When writing docker-compose files don't put the version in the file - this is deprecated and not needed.</RULE>
      </DOCKER>
    </LANGUAGE_SPECIFIC_RULES>
    <GENERAL_CODING_RULES>
      <RULE>Do not add mock/placeholder code where there should be real functionality.</RULE>
      <RULE>Always ensure code is properly indented and formatted.</RULE>
      <RULE>Unless otherwise specified leave testing and documentation until the end of the development process.</RULE>
    </GENERAL_CODING_RULES>
  </CRITICAL_CODING_RULES>

  <CRITICAL_TOOLING_RULES>
    <RULES>
      <RULE>Always utilise the available MCP tools for efficient information retrieval. These tools are essential for maintaining context window efficiency and accessing accurate, up-to-date information.</RULE>
      <RULE>You always think about what MCP tools may help answer the user's request and consider that using tools is often more efficient for the problems they solve. Using tools is highly recommended when they align with the task.</RULE>
      <RULE>When implementing complex or very modern libraries / packages use the tools available to you such as context7 to understand relevant parts of their documentation to help you understand how to use them.</RULE>
      <RULE>When adding libraries or packages use the package version tools to ensure you always use the latest package versions.</RULE>
    </RULES>
    <IMPORTANT_TOOLS>
      <TOOL>context7 - Retrieve documentation and information on how to implement libraries and packages</TOOL>
      <TOOL>package-version - Retrieve the latest stable or recommended version of a package</TOOL>
      <TOOL>fetch - Fast and lightweight tool to fetch the content of web pages/URLs</TOOL>
      <TOOL>think tool - If you're having troubles with a complex task use the think tool to think about something complex. If that doesn't work using the 'think harder' tool. These tools will not obtain new information or change any data, but just append the thought to the log. Use it when complex reasoning or some cache memory is needed.</TOOL>
    </IMPORTANT_TOOLS>
  </CRITICAL_TOOLING_RULES>

  <CRITICAL_TESTING_RULES>
    <IMPORTANT>Whenever adding new features you must always create accompanying unit tests.</IMPORTANT>
    <IMPORTANT>After completing the tasks the user has requested you MUST run the tests (e.g. `pnpm test`, `make test` etc...) to ensure they all pass, If any tests fail, you MUST fix them before proceeding.</IMPORTANT>
    <IMPORTANT>When writing tests for a UI, test the inputs against actual output objects/variables that would populate the UI as the user would see them when using the UI.</IMPORTANT>
  </CRITICAL_TESTING_RULES>

  <SPELLING_AND_LOCALISATION>
    <IMPORTANT>Always use British English spelling for all responses, documentation, comments and function names.</IMPORTANT>
    <BRITISH_ENGLISH_RULES>
      <RULE>ALWAYS use British English spelling and conventions in ALL writing.</RULE>
      <KEY_PATTERNS>
        <PATTERN>ALWAYS use -our not -or (colour, humour, favour, neighbour, harbour, behaviour)</PATTERN>
        <PATTERN>ALWAYS use -ise not -ize (organise, prioritise, specialise, recognise, apologise)</PATTERN>
        <PATTERN>ALWAYS use -re not -er (centre, theatre, calibre, metre, fibre)</PATTERN>
        <PATTERN>ALWAYS use -ogue not -og (catalogue, dialogue, monologue)</PATTERN>
        <PATTERN>ALWAYS use -ae/oe not -e (aesthetic, encyclopaedia, manoeuvre, paediatric)</PATTERN>
        <PATTERN>ALWAYS use -ll- not -l- (travelling, cancelled, counsellor, modelling)</PATTERN>
        <PATTERN>ALWAYS use -t not -ed for certain past tense verbs (burnt, learnt, dreamt, spelt)</PATTERN>
        <PATTERN>ALWAYS use -yse not -yze (analyse, paralyse, catalyse)</PATTERN>
        <PATTERN>ALWAYS use -ence not -ense (defence, offence, licence as noun)</PATTERN>
        <PATTERN>ALWAYS use British vocabulary (mum, aeroplane, flat, queue, autumn, holiday)</PATTERN>
      </KEY_PATTERNS>
    </BRITISH_ENGLISH_RULES>
  </SPELLING_AND_LOCALISATION>

  <MERMAID_DIAGRAMS>
    <RULE>Mermaid diagrams should use <br> instead of \n for new lines</RULE>
    <RULE>Mermaid diagrams should always use this colour theme unless otherwise specified</RULE>
    <MERMAID_THEME>
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
    </MERMAID_THEME>
  </MERMAID_DIAGRAMS>

  <IMPORTANT>⚠️ BY FOLLOWING THESE CRITICAL RULES YOU WILL MAKE THE WORLD OF SOFTWARE A BETTER PLACE ⚠️</IMPORTANT>
</IMPORTANT_RULES_YOU_MUST_FOLLOW>
