# Sam's Agentic Coding Rules, Templates and Examples

- [Sam's Agentic Coding Rules, Templates and Examples](#sams-agentic-coding-rules-templates-and-examples)
  - [Coding Agent Rules, Agents, Templates and Skills](#coding-agent-rules-agents-templates-and-skills)
    - [Client Tooling - Not All Created Equal](#client-tooling---not-all-created-equal)
  - [Patterns / Workflows](#patterns--workflows)
  - [MCP Servers](#mcp-servers)
  - [Tips For Agentic Coding](#tips-for-agentic-coding)
    - [Writing Rules](#writing-rules)
    - [Getting High Quality Outcomes](#getting-high-quality-outcomes)
    - [Context Window \& Token Usage](#context-window--token-usage)
    - [Agent Rules](#agent-rules)
  - [Links](#links)
  - [Notes](#notes)
  - [License](#license)

A collection of coding rules, templates, MCP servers and examples for working with Agentic Coding tools (Cline, Claude Code etc...)

## Coding Agent Rules, Agents, Templates and Skills

_Note: My rules starting with an `_` indicate that I only toggle these on for specific scenarios and they are disabled by default._

- **Claude Code**
  - [Agent Rules](./Claude/CLAUDE.md)
  - [Agents / Sub-Agents](./Claude/agents/)
  - [Skills](./Claude/skills/)
  - [Commands](./Claude/commands/)
- **Cline**
  - [Agent Rules](./Cline/Rules/)
  - [Workflows (Prompt Templates)](./Cline/Workflows/)
  - [Cline Docs on Rules](https://docs.cline.bot/features/cline-rules)

![Rules Toggled In Cline](clinerules.png)

### Client Tooling - Not All Created Equal

**I recommend Claude Code or Cline as the best agentic coding tools.**

I find they both _far_ outperform the many other tools I've tried (Copilot Agent, Cursor, Windsurf, Kiro, Augment Code, Gemini CLI, Codex etc...).

Both Claude Code and Cline are equally good in different ways. Claude Code provides the best value for money if you can pair it with the Claude Max 5 subscription ($100 USD / month).

> _You may also find other rules for other tools that I've tried but did not find as effective such as Github Copilot Agent, Charm, Gemini CLI and [Amazon Kiro](./Kiro/kiro-specific-rules.md) - be mindful they might not be as well maintained as the Claude Code and Cline rules. I have a table where I keep track of coding agent tools here:_ https://smcleod.net/agentic-coding-tools/

## Patterns / Workflows

- See my blog post on my Setup -> Plan -> Act -> Review & Iterate workflow at: [smcleod.net](https://smcleod.net)

## MCP Servers

- [MCP DevTools](https://github.com/sammcj/mcp-devtools): This has become the only MCP server I _always_ have enabled. I wrote it to provide the most common tooling I use with Agentic Coding.
  - [Example MCP DevTools client config](https://github.com/sammcj/agentic-coding/blob/main/MCP/mcp-config-mvp.json)

- Always have tools available to the agent that allow it to:
  - Search the web.
  - Efficiently retrieve web page content as markdown.
  - Lookup package documentation.
  - Perform math calculations.
- Be mindful of how many tokens each MCP server adds to your context window (`/context` in Claude Code), some tools abuse their descriptions and pollute the context window - for example Github's official MCP server alone uses ¼ of the entire context window of Claude Sonnet 4.

---

## Tips For Agentic Coding

### Writing Rules

- **Using pseudo-XML for your rules can help LLM adherence**
  - LLMs are trained on a lot of structured data (such as XML), see [this blog post](https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/use-xml-tags) for more information.
  - On _many_ occasions I have been given feedback that after simply changing rules XML like structure - the LLM closer adheres to them.
- **Only enable the rules you actually want to use**
  - Think about the signal to noise ratio of your rules (and context in general), _how much information could you be told at once and remember?_
  - If you have a lot of rules that are not relevant to the current task, then you're just adding noise and misleading the prediction engine, while increasing the token count.
  - Do not blindly import and enable all my (or anyone else's) rules!
- **Be clear, concise and specific in your rules. Avoid ambiguity**
- **Use emphasis** (e.g. `**bold**`, `*italic*`, `__underline__`) to highlight important parts of your rules.
- As well as global rules, **consider adding project specific rules** such as `.clinerules`, `CLAUDE.md` or similar that relate to repository specific behaviour (e.g. "To build the application, you must run `make build` etc.)
  - I have an _example_ of what these might look like in [Cline/Rules/adhoc/_repo-specific-rules.md](./Cline/Rules/adhoc/_repo-specific-rules.md).
- **Rules are often transferable between agentic coding tools**
  - While I write a lot of my rules in Cline, for 95% of them there's no reason they can't be used with other Agentic Coding tools such as Claude Code etc. without modification.
- **Get AI to help you write or improve rules**

If you spend a long time on a difficult problem with a coding agent and you finally crack it - get it to:
1. Summarise the fix
2. Why previous attempts did not work
3. What led them down the wrong paths initially
4. Get them to write a concise, clear rule (prompt) that could be used in the future (or added to your global rules if it's a common issue) to prevent the issue from happening again or at least aid with debugging.

Example:
> You fixed it! That's taken a long time to fix. Can you please respond with details on:
  > 1. What the fix was
  > 2. Why it wasn't picked up earlier
  > 3. What information could I have provided to AI coding agents in the future - not just for this project but also other projects in general?
> With those in mind I would like you also like you to create a 1 to 3 sentence prompt I can provide to future AI coding agents that would help them avoid having similar issues in the future.

---

### Getting High Quality Outcomes

- Treat an agent like you would someone who just joined your team, don't assume they know anything about your codebase or intended outcomes. Unless the task is very simple and self explanatory - a single sentence is probably not going to be enough for a prompt. GIGO.
- Manage the context window usage effectively (see other notes here on this).
- Start with a plan - break down large or complex tasks into a checklist of items to complete, have the agent follow and mark off items has it completes them.
- Make use of tools (MCP servers), they extend and enhance LLMs with access to up to date information, new capabilities and integrations.
- Always have tools available to the agent that allow it to search the web, lookup package documentation, efficiently retrieve web page content as markdown.
- Spend the time to craft global and project scoped agent rules (guidelines).

---

### Context Window & Token Usage

- Understand that LLMs are stateless, this means that every time you send a message the entire context is sent back for re-processing.
- Don't fall into the trap of thinking the solution is just around the corner when you've dug yourself into a hole troubleshooting, get the agent to document the problem, what it's tried to fix it so far and possible next things to try, then start a fresh session and provide the document.
- Ideally try to keep the models context window usage under 75%, the higher the usage the slower and dumber the model becomes along with increased cost.
- When you want to refresh the conversation ask the agent to document where it is up to and what's left to do (if you don't already have a dev plan with a checklist of tasks) and provide the document when starting a fresh session.
- Use checkpoints to roll back to previous points in the conversation or code changes when you've gone down the wrong path or want to explore a different approach.
- Ensure you enable prompt caching, some agentic coding tools will do this automatically, others like Cline with some providers require you to enable it in settings. Prompt caching can reduce the cost of agentic coding by 75-90%.
- Practice good code hygiene, keep files from getting too long as if the agent has to read or write the entire file it will be slower, costly and more at risk of errors, a good rule of thumb is a maximum of 700 lines.
- Only use multimodal operations (images / screenshots as used by browser tools etc..) to a minimum - only when truly needed or where cost is not an issue as they use a lot of tokens.
- Add files and directories you never want the agent to read to the agent's ignore file (e.g. `.clineignore` or claude.json's access rules).
- Don't pipe data into LLMs and be wary of code with hardcoded data (XML, SVGs, i18n translations) inline. LLMs are designed to perform predictions (e.g. writing text / code and answering questions) effectively, they're not designed to parse large amounts of data at low cost - that's what software is for.
- Don't waste time with low end models for planning or coding, the higher error rates, lower quality code and the rework they often incur does not pay off (at least with current generation models).
- Whenever you find the agent performing actions that seem to consume a disproportionate amount of tokens - ask yourself if there is an agent rule that might need to be added, or if there's a MCP tool that could perform this kind of task more efficiently.
- Avoid using Claude Opus - it's 5x the price for 1.5x the smarts.

#### Subscription vs Consumption Based Providers

- A Claude Max 5 subscription will cost you $100 USD / month and get you over $2000+ equivalent worth of raw LLM API token usage.
- Be wary of subscription based AI coding tools like Cursor or Windsurf - they often provide you reduced versions of models with smaller context windows, artificially slowed response times and fallback to lower end models. Read the fine print especially if it seems too cheap to be true.
- All subscription based agentic coding tools serve their models from the US. This is fine for most things, but occasionally you might work with a client that requires all inference to be performed within Australia.
- Some consumption based offerings like Github Copilot have very low rate limits if you use the service with anything other than their client. With Github Copilot's SDK you can use your entire months paid limits of Claude Sonnet access in just two days.

---

### Agent Rules

- Create both global (all projects) and project scoped agent rules to guide the agent as to how it should behave, what it's values are, if there are any specific build, lint or test commands it should be aware of, where to find additional information etc...
- Writing your rules in XML style tags (`<Golang_Rules`>...`</Golang_Rules>`) can significantly improve adherence.

---

## Links

- [Blog - smcleod.net](https://smcleod.net)
- [GitHub - sammcj](https://github.com/sammcj)
- [Cline](https://cline.bot): IMO The best agentic coding tool.

## Notes

- If you see 'tmux-cli' in any rules, you need to install it - [pchalasani/claude-code-tools](https://github.com/pchalasani/claude-code-tools)

## License

- This repository is licensed under the [Apache 2.0 License](./LICENSE).
