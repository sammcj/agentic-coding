# Additional Important Rules

<USER_RULES description="CRITICAL ADDITION RULES YOU _MUST_ FOLLOW">
   <RULE>CRITICAL: You see elegance in simplicity. Favour a less is more approach. Do not over complicate things. DO NOT INTRODUCE UNNECESSARY COMPLEXITY.</RULE>
   <RULE>CRITICAL: When running interactive commands (e.g. npm run dev, make run etc...) prefix commands with the timeout so you don't end up sitting there waiting for their exit code and output forever.</RULE>
   <RULE>IMPORTANT: When creating tests, don't over complicate them. Keep tests concise and simple. We don't want to end up with more tests than we have code.</RULE>
   <RULE>IMPORTANT: When creating specs - do not add additional tasks beyond what is truly required and specified by the user, for example if the user says they want basic unit tests - do not write specs for a large number of testing requirements - stick to what they've asked for unless you think it's not possible - in which case you must ask for clarification<RULE>
   <RULE>IMPORTANT: When implementing a complex new package or library, use the tools available to you to lookup it's documentation if you are unsure how to properly use it.</RULE>
   <RULE>IMPORTANT: Always leave adding tests until last, unless the user specifically states otherwise.</RULE>
   <RULE>IMPORTANT: Always use British / Australian English spelling, we are NOT American, we are Australian.</RULE>
   <RULE>When dealing with Python virtual environments, use uv and store the venv in .venv</RULE>
   <RULE>When creating a new nodeJS application, use pnpm instead of npm</RULE>
   <RULE>When working with environment variables, use dotenv and store the .env file in the root of the project along with a .env.example with complete, up to date examples</RULE>
   <RULE>When developing web applications make good use of browser real estate, we don't want one of those applications that squashes all the content into a small piece of the browsers available resolution.</RULE>
   <RULE>Never perform git add or git commit commands</RULE>
</USER_RULES>
