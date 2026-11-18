# Running a skill on other agents

1. Run the validator in full (without `--report-only`). Its PORTABILITY section lists what Codex and GitHub Copilot drop or pass through unchanged in this skill.
2. For install location, skill-list limits, or another agent (`opencode`, `hermes`, `openclaw`), run SkillEvaluator's harness check:

   ```bash
   uvx --from 'skillevaluator>=1.0.1' skillevaluator harness-check <skill-dir> --harness codex,copilot-cli
   ```

   - Fix `not loaded` findings first, then `degraded`.
   - A `*-ROOT` finding says only that the skill is not installed in that agent's folder. Ignore it until it is.
   - Run this subcommand only. SkillEvaluator's `quality-check`, `tier1` and `validate` score against another template (semver versions, fixed section headings) and contradict this primer.

## Behaviours no check detects

- `allowed-tools` pre-approves tools and never restricts them. Codex ignores it.
- Codex ignores `disable-model-invocation`, so the agent can still load the skill.
- GitHub Copilot shows a double quote in a description as `&quot;`. Use single quotes when the exact text matters.
