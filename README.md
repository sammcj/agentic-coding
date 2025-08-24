# Sam's Agentic Coding Rules, Templates and Examples

- [Sam's Agentic Coding Rules, Templates and Examples](#sams-agentic-coding-rules-templates-and-examples)
  - [MCP Servers](#mcp-servers)
  - [Patterns / Workflows](#patterns--workflows)
  - [Coding Agent Rules](#coding-agent-rules)
    - [Tips For Writing Rules](#tips-for-writing-rules)
  - [Sub-Agent Definitions](#sub-agent-definitions)
  - [Links](#links)
  - [Notes](#notes)
  - [License](#license)

A collection of coding rules, templates, MCP servers and examples for working with Agentic Coding tools (Cline, Claude Code etc...)

## MCP Servers

- [MCP DevTools](https://github.com/sammcj/mcp-devtools): This has become the only MCP server I _always_ have enabled. I wrote it to provide the most common tooling I use with Agentic Coding.
  - [Example MCP DevTools client config](https://github.com/sammcj/agentic-coding/blob/main/MCP/mcp-config-mvp.json)

## Patterns / Workflows

- See my blog post on my Setup -> Plan -> Act -> Review & Iterate workflow at: [smcleod.net](https://smcleod.net)

## Coding Agent Rules

_Note: My rules starting with an `_` indicate that I only toggle these on for specific scenarios and they are disabled by default._

- [Agent Rules](./Cline/Rules/)
- [Workflows (Prompt Templates)](./Cline/Workflows/)
- [Amazon Kiro Specific Rules](./Kiro/kiro-specific-rules.md) (Mainly as Kiro seems to over-complicate and over-engineer everything).
- [Cline Docs on Rules](https://docs.cline.bot/features/cline-rules)

![Rules Toggled In Cline](clinerules.png)

### Tips For Writing Rules

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
> YOU FIXED IT! Finally! That's taken a VERY long time to fix. Can you please respond with details on:
  > 1. What the fix was
  > 2. Why it wasn't picked up earlier
  > 3. What information could I have provided to AI coding agents in the future - not just for this project but also other projects in general?
> With those in mind I would like you also like you to create a 1 to 3 sentence prompt I can provide to future AI coding agents that would help them avoid having similar issues in the future.

---

## Sub-Agent Definitions

Claude Code recently introduced the concept of [sub-agents](https://docs.anthropic.com/en/docs/claude-code/sub-agents), which are essentially agents that can be called by other agents to handle specific tasks or workflows.

- [Sub-Agent Definitions](./SubAgents/)

---

## Links

- [Blog - smcleod.net](https://smcleod.net)
- [GitHub - sammcj](https://github.com/sammcj)
- [Cline](https://cline.bot): IMO The best agentic coding tool.

## Notes

- If you see 'tmux-cli' in any rules, you need to install it - [pchalasani/claude-code-tools](https://github.com/pchalasani/claude-code-tools)

## License

- This repository is licensed under the [Apache 2.0 License](./LICENSE).
