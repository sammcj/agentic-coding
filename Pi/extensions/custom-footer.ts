import type { AssistantMessage } from "@earendil-works/pi-ai";
import type { ExtensionAPI, ThemeColor } from "@earendil-works/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

type SubagentUsage = { input?: number; output?: number; cost?: number };

// A branch entry that is a completed `subagent` tool result carries per-agent
// usage under message.details.results[]. Returns [] for anything else
// (assistant messages, other tools, management/streaming entries with no results).
function subagentResults(entry: unknown): Array<{ usage?: SubagentUsage }> {
	const e = entry as {
		type?: string;
		message?: {
			role?: string;
			toolName?: string;
			details?: { results?: Array<{ usage?: SubagentUsage }> };
		};
	};
	if (e?.type !== "message") return [];
	const m = e.message;
	if (m?.role !== "toolResult" || m.toolName !== "subagent") return [];
	return m.details?.results ?? [];
}

// Output tokens produced by a single branch entry: the parent assistant stream
// plus any subagent tool-result output. Used to measure turn throughput.
function entryOutputTokens(entry: unknown): number {
	let out = 0;
	const e = entry as {
		type?: string;
		message?: { role?: string; usage?: { output?: number } };
	};
	if (e?.type === "message" && e.message?.role === "assistant") {
		out += e.message.usage?.output ?? 0;
	}
	for (const r of subagentResults(entry)) out += r.usage?.output ?? 0;
	return out;
}

// Compact token/number formatting: 1234 -> "1.2k", 1_200_000 -> "1.2M".
function fmt(n: number): string {
	if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
	if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
	return `${n}`;
}

// Thinking-level dot colours, keyed by level name.
const LEVEL_COLORS: Record<string, ThemeColor> = {
	off: "thinkingOff",
	minimal: "thinkingMinimal",
	low: "thinkingLow",
	medium: "thinkingMedium",
	high: "thinkingHigh",
	// pi's own level names are "xhigh" and "max"; "extra-high" matched neither, so both
	// top levels fell through to the default accent colour.
	xhigh: "thinkingXhigh",
	max: "thinkingMax",
};

export default function (pi: ExtensionAPI) {
	pi.on("session_start", async (_event, ctx) => {
		// Seed from the session's real level rather than a literal. Nothing fires
		// thinking_level_select at startup, so a hardcoded start value displayed that level
		// on every launch no matter what the model or settings actually resolved to.
		let thinkingLevel: string = ctx.thinkingLevel ?? "off";

		pi.on("thinking_level_select", async (event) => {
			thinkingLevel = event.level;
		});

		// Tokens/sec measured across the model generation time only, not the
		// full agent loop. Confirmation prompts, tool execution, and other
		// non-generation time is tracked and excluded from the elapsed time.
		let lastSpeed: number | null = null;
		let windowStart: number | null = null;
		let windowStartIndex = 0;
		// Cumulative tool execution time during the current agent loop.
		// Measured as the union of all tool call intervals, so concurrent
		// tool calls don't double-count overlapping wall-clock time.
		// Subtracted from elapsed time so t/s reflects model decode rate.
		let toolWaitMs = 0;
		// Number of currently-inflight tool calls.
		let activeToolCalls = 0;
		// When the first tool in a batch started (only valid when activeToolCalls > 0).
		let toolBatchStart = 0;
		// Set by the footer factory so events can repaint the footer.
		let triggerRender: (() => void) | null = null;

		// Cumulative token/cost totals. Recomputed when a message finalises
		// (message_end / agent_end), not on every repaint — bounds the O(branch)
		// scan to actual content changes. NOTE: footerData.onBranchChange is the
		// git branch, not the message branch, so it can't drive this.
		let totals = { input: 0, output: 0, cost: 0 };
		const recomputeTotals = () => {
			let input = 0,
				output = 0,
				cost = 0;
			for (const e of ctx.sessionManager.getBranch()) {
				if (e.type === "message" && e.message.role === "assistant") {
					const m = e.message as AssistantMessage;
					input += m.usage.input;
					output += m.usage.output;
					cost += m.usage.cost.total;
				}
				// Subagent usage from slash-command results
				if (
					e.type === "custom_message" &&
					e.customType === "subagent-slash-result"
				) {
					const details = e.details as {
						result?: {
							details?: { results?: Array<{ usage?: SubagentUsage }> };
						};
					};
					for (const r of details?.result?.details?.results ?? []) {
						input += r.usage?.input ?? 0;
						output += r.usage?.output ?? 0;
						cost += r.usage?.cost ?? 0;
					}
				}
				// Subagent usage from `subagent` tool results
				for (const r of subagentResults(e)) {
					input += r.usage?.input ?? 0;
					output += r.usage?.output ?? 0;
					cost += r.usage?.cost ?? 0;
				}
			}
			totals = { input, output, cost };
		};
		recomputeTotals();

		// Track tool execution time as union of active intervals.
		// When at least one tool is running, the clock ticks for tool wait.
		// Concurrent tools share the same wall-clock → no double-counting.
		// Sub-agents are excluded: they do model inference, not tool I/O.
		pi.on("tool_call", async (event) => {
			if (event.toolName === "subagent") return;
			if (activeToolCalls === 0) toolBatchStart = Date.now();
			activeToolCalls++;
		});

		pi.on("tool_result", async (event) => {
			if (event.toolName === "subagent") return;
			activeToolCalls--;
			if (activeToolCalls === 0 && toolBatchStart !== 0) {
				toolWaitMs += Date.now() - toolBatchStart;
			}
		});

		pi.on("agent_start", async () => {
			windowStart = Date.now();
			windowStartIndex = ctx.sessionManager.getBranch().length;
			toolWaitMs = 0;
			activeToolCalls = 0;
			toolBatchStart = 0;
		});

		pi.on("agent_end", async () => {
			if (windowStart !== null) {
				const branch = ctx.sessionManager.getBranch();
				let output = 0;
				for (let i = windowStartIndex; i < branch.length; i++) {
					output += entryOutputTokens(branch[i]);
				}
				// Account for any inflight tool calls that never received a
				// tool_result (should be rare, but safety first).
				const now = Date.now();
				if (activeToolCalls > 0 && toolBatchStart !== 0) {
					toolWaitMs += now - toolBatchStart;
				}

				const wallElapsed = (now - windowStart) / 1000;
				// Subtract tool execution time (confirmations, bash, file I/O, etc.)
				// so the t/s reflects model generation speed only.
				const elapsed = wallElapsed - toolWaitMs / 1000;
				// Skip if elapsed is unreasonably small (e.g. restored from session).
				// Aggregate throughput: concurrent subagents push this above any single
				// decode rate, which is the intended reading. Async/detached runs return
				// after agent_end and are not counted.
				if (elapsed > 0.5 && output > 0) {
					lastSpeed = Math.round(output / elapsed);
				}
				windowStart = null;
			}
			// Catch-all: by loop end every message (incl. subagent tool results) is
			// in the branch, so totals are guaranteed fresh here.
			recomputeTotals();
			triggerRender?.();
		});

		// Refresh cumulative totals as each message finalises (assistant turn,
		// tool result, or custom message all emit message_end), then repaint.
		pi.on("message_end", async () => {
			recomputeTotals();
			triggerRender?.();
		});

		ctx.ui.setFooter((tui, theme, footerData) => {
			// onBranchChange = git branch change; repaint so the git segment updates.
			const unsub = footerData.onBranchChange(() => tui.requestRender());
			triggerRender = () => tui.requestRender();

			return {
				dispose: () => {
					triggerRender = null;
					unsub();
				},
				invalidate() {},
				render(width: number): string[] {
					const { input, output, cost } = totals;

					// Separator
					const sep = " " + theme.fg("dim", "│") + " ";

					// Session context usage — model's context window.
					// percent is null right after compaction (tokens unknown); hide it then.
					const contextUsage = ctx.getContextUsage();
					const ctxWindow =
						contextUsage?.contextWindow ?? ctx.model?.contextWindow ?? 0;
					let contextPct = "";
					if (contextUsage?.percent != null && ctxWindow > 0) {
						const pct = contextUsage.percent;
						const color = pct > 80 ? "error" : pct > 50 ? "warning" : "success";
						contextPct =
							theme.fg(color, `${pct.toFixed(1)}%`) +
							theme.fg("dim", "/" + fmt(ctxWindow));
					}

					const branch = footerData.getGitBranch();

					// Colored stat labels — using valid theme token names only
					const arrowUp =
						theme.fg("success", "↑") + theme.fg("text", fmt(input));
					const arrowDown =
						theme.fg("error", "↓") + theme.fg("text", fmt(output));
					const costStr = theme.fg("warning", "$" + cost.toFixed(3));
					const speedStr =
						lastSpeed !== null
							? theme.fg("mdLink", fmt(lastSpeed) + " t/s")
							: "";

					const levelColor = LEVEL_COLORS[thinkingLevel] || "accent";
					const levelDot = theme.fg(levelColor, "●");
					const modelStr = theme.fg("accent", ctx.model?.id || "no-model");
					const levelStr = theme.fg("muted", thinkingLevel);

					// Git branch — use success color
					const gitStr = branch ? theme.fg("toolDiffAdded", " " + branch) : "";

					// Statuses published by other extensions via ctx.ui.setStatus(). The built-in
					// footer renders these; replacing the footer silently swallowed them, so any
					// extension using setStatus had no visible effect. Rendered generically so
					// this does not need to know which extensions exist.
					const statuses = [...footerData.getExtensionStatuses().values()]
						.map((s) => s.trim())
						.filter(Boolean)
						.map((s) =>
							// A warning word is the convention for "look at this now". Plurals and
							// -ed/-ing forms count; word boundaries keep "mission" and "terrorist"
							// from reading as "miss" and "error".
							/\b(miss(ed|es)?|warn(ing)?s?|stale|errors?)\b/i.test(s)
								? theme.fg("warning", s)
								: theme.fg("muted", s),
						);

					// ===== LEFT: stats with │ separators between each =====
					const leftParts = [
						arrowUp,
						arrowDown,
						costStr,
						contextPct,
						speedStr,
						...statuses,
					].filter(Boolean);

					const left = leftParts.join(sep);

					// ===== RIGHT: model info =====
					const rightParts = [
						modelStr,
						levelDot + " " + levelStr,
						gitStr,
					].filter(Boolean);

					const right = rightParts.join(" " + theme.fg("dim", "•") + " ");
					const midSep = right ? " " + theme.fg("dim", "│") + " " : "";

					// Pad left side so right side is right-aligned
					const leftContent = left + midSep;
					const padNeeded = Math.max(
						1,
						width - visibleWidth(leftContent) - visibleWidth(right),
					);
					const pad = " ".repeat(padNeeded);

					return [truncateToWidth(leftContent + pad + right, width)];
				},
			};
		});
	});
}
