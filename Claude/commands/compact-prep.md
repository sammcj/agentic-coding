---
description: Ask the agent to prepare for conversation compaction by updating any relevant state and providing guidance for the compaction agent and to kick off the session there after
argument-hint: "[optional additional instructions]"
---

# This is an automated message to state that the context window usage is getting high and the user is going to run a compaction

As such, could you please:

1. (Only if applicable) Update any state that tracks the work currently in progress / the state of the tasks being worked on, e.g. A development plan if operating from one, the CLAUDE.md ( Only if that is where the user has asked you to track in flight work and it does not only contain rules), etc... to ensure it's up to date without any now outdated or invalid information, if it has next steps that they are correct, and if you're mid troubleshooting a complex problem - where you've got to and what you've tried so far (but keep it concise).

2. Give me a concise prompt that I can provide to the compaction agent that will be compacting our conversation to ensure the signal to noise ratio is kept high and focused. The agent will already be aware of it's task to compact the conversation so only needs additional guidance on specific things that may not be obvious but are important to keep (e.g. the WHY not just the WHAT).

3. Give me a concise prompt that I can provide to continue our work after compaction is complete. Keep in mind that the new agent / session will have access to the same files and will have the same CLAUDE.md agent rules in context.

Note: You must not quote, indent or format the prompts in any way that might impact me copying and pasting them without cleaning them up.

---

`$ARGUMENTS`
