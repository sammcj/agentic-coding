# Combined Detail Mode (Concise & Detailed)

When the user selects "Both (Concise & Detailed)", the analysis is performed at two levels of depth simultaneously using sub-agents, then merged into a single document.

## File naming

Both sub-agents write to the same output directory, using these filenames:

- Concise: `<source-title> - analysis-concise.md`
- Detailed: `<source-title> - analysis-detailed.md`

The combined output (produced by the script) uses the standard name: `<source-title> - analysis.md`

## Sub-agent orchestration

After completing source acquisition (Step 2), spawn two sub-agents in parallel using the `Agent` tool. Each agent receives:

1. The full source content (transcript or article text)
2. The output directory path
3. Their assigned detail level
4. The markdown template from Step 4 of SKILL.md

### Rules for both agents

Include these rules in both agent prompts:

- The `title` field in frontmatter must be the source title only. Do NOT append "Detailed Analysis", "Concise Analysis", or any detail-level suffix.
- Include ALL template sections: Summary (with Simplified Explanation and Key Takeaways), Key Insights, Notable Quotes, Structured Breakdown, Actionable Takeaways, Insights & Commentary, Additional Resources.
- Do NOT use **bold** to start list items or as a substitute for headings. Use `####` subheadings for structure within sections.
- Use Australian English spelling throughout.
- Do NOT run self-review, formatting, or PDF export. The main agent handles those.
- Both agents must include the full YAML frontmatter with identical source metadata. The combine step merges these into one copy.

### Concise agent instructions

```
You are one of two agents analysing the same source content. Your role is to produce
a CONCISE analysis: focus on the top-level takeaways, key quotes, and actionable items.
Keep sections brief. Aim for quick scanning. Do not pad with filler.

Write your analysis to: <output-dir>/<source-title> - analysis-concise.md

Use the standard markdown template from the skill. Include every section from the
template (Summary with Simplified Explanation and Key Takeaways, Key Insights, Notable
Quotes, Structured Breakdown, Actionable Takeaways, Insights & Commentary, Additional
Resources). Keep each section tight: 1-2 sentences per insight, 3-5 key takeaways,
shorter structured breakdown.
```

### Detailed agent instructions

```
You are one of two agents analysing the same source content. Your role is to produce
a DETAILED analysis: thorough coverage of all ideas, extensive supporting detail,
full breakdown of themes.

Write your analysis to: <output-dir>/<source-title> - analysis-detailed.md

Use the standard markdown template from the skill. Include every section from the
template (Summary with Simplified Explanation and Key Takeaways, Key Insights, Notable
Quotes, Structured Breakdown, Actionable Takeaways, Insights & Commentary, Additional
Resources). Expand each section fully: multiple supporting points per insight, extensive
structured breakdown, detailed actionable items with examples.
```

## Combining the files

Once both sub-agents complete, run the combine subcommand:

```bash
uv run ${CLAUDE_SKILL_DIR}/scripts/wisdom.py combine \
  "<output-dir>/<title> - analysis-concise.md" \
  "<output-dir>/<title> - analysis-detailed.md" \
  --cleanup
```

The script:
- Merges frontmatter (prefers the detailed file's values where they differ)
- Strips the preamble from each file (the H1 heading and source/date metadata lines, since the combined doc provides its own shared header)
- Bumps all remaining heading levels down by one (## becomes ###) so the two section wrappers ("Quick Take" and "Deep Dive") use ##
- Writes the combined file as `<title> - analysis.md`
- With `--cleanup`, deletes the two input files

It outputs `COMBINED_PATH: <path>` with the path to the merged file.

## After combining

Return to SKILL.md and continue with Step 5 (self-review) using the combined file. The self-review, formatting, PDF export, and sharing steps all operate on the single combined document.
