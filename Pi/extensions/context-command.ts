/**
 * /context — compact context usage report.
 *
 * Shows startup context (system prompt, tools, context files, skills) and, once a
 * conversation exists, message/tool-call consumers. Counts are estimates except
 * when the active provider has reported aggregate usage via ctx.getContextUsage().
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Box, matchesKey, Text, truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

type AnyRecord = Record<string, any>;

type Item = {
	label: string;
	tokens: number;
	detail?: string;
	kind?: string;
};

type ContextReport = {
	model: string;
	limit: number;
	total: number;
	free: number;
	mode: "startup" | "conversation";
	categories: Item[];
	startup: {
		system: Item[];
		tools: Item[];
		memory: Item[];
		skills: Record<string, Item[]>;
	};
	conversation: {
		entries: number;
		byRole: Item[];
		toolCalls: Item[];
		largest: Item[];
	};
};

const TOKEN_DIVISOR = 4;
const MAX_LIST = 6;

function estimateTokens(value: unknown): number {
	if (value == null) return 0;
	const text = typeof value === "string" ? value : JSON.stringify(value);
	return Math.max(0, Math.ceil(text.length / TOKEN_DIVISOR));
}

function fmt(n: number): string {
	if (n < 20 && n > 0) return "<20";
	if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}m`;
	if (n >= 10_000) return `${Math.round(n / 1000)}k`;
	if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
	return String(Math.round(n));
}

function pct(tokens: number, limit: number): string {
	if (!limit) return "0%";
	const p = (tokens / limit) * 100;
	return p < 0.1 && tokens > 0 ? "<0.1%" : `${p.toFixed(1)}%`;
}

function compactPath(file: string): string {
	const home = process.env.HOME;
	return home && file.startsWith(home) ? file.replace(home, "~") : file;
}

function firstLine(value: unknown): string {
	const text = typeof value === "string" ? value : JSON.stringify(value ?? "");
	return text.replace(/\s+/g, " ").trim();
}

function contentText(content: unknown): string {
	if (typeof content === "string") return content;
	if (!Array.isArray(content)) return firstLine(content);
	const parts: string[] = [];
	for (const block of content) {
		if (!block || typeof block !== "object") continue;
		if (block.type === "text" && typeof block.text === "string") parts.push(block.text);
		else if (block.type === "thinking" && typeof block.thinking === "string") parts.push(block.thinking);
		else if (block.type === "toolCall") parts.push(`${block.name ?? "tool"} ${JSON.stringify(block.arguments ?? {})}`);
		else if (block.type === "image") parts.push("[image]");
	}
	return parts.join("\n");
}

function messageTokens(message: AnyRecord): number {
	if (message.role === "toolResult") {
		return estimateTokens(`${message.toolName ?? "toolResult"}\n${contentText(message.content)}`);
	}
	return estimateTokens(contentText(message.content ?? message));
}

function messageRole(entry: AnyRecord): string | undefined {
	return entry?.message?.role;
}

function selectedToolNames(options: AnyRecord, pi: ExtensionAPI): Set<string> {
	const selected = Array.isArray(options.selectedTools) ? options.selectedTools : [];
	if (selected.length === 0) return new Set(pi.getActiveTools().map((t: any) => typeof t === "string" ? t : t.name));
	return new Set(selected.map((t: any) => typeof t === "string" ? t : t.name).filter(Boolean));
}

function subtractKnown(systemPrompt: string, known: string[]): number {
	let remaining = systemPrompt;
	for (const part of known.filter(Boolean).sort((a, b) => b.length - a.length)) {
		remaining = remaining.replace(part, "");
	}
	return estimateTokens(remaining);
}

function pushCount(map: Map<string, number>, key: string, tokens: number) {
	map.set(key, (map.get(key) ?? 0) + tokens);
}

function topItems(items: Item[], max = MAX_LIST): Item[] {
	return [...items].sort((a, b) => b.tokens - a.tokens || a.label.localeCompare(b.label)).slice(0, max);
}

function buildReport(pi: ExtensionAPI, ctx: any): ContextReport {
	const options = ctx.getSystemPromptOptions?.() ?? {};
	const usage = ctx.getContextUsage?.();
	const limit = usage?.limit ?? ctx.model?.contextWindow ?? 128_000;
	const model = ctx.model?.id ?? "unknown model";
	const systemPrompt = ctx.getSystemPrompt?.() ?? "";

	const skills = Array.isArray(options.skills) ? options.skills : [];
	const skillItems: Item[] = skills.map((skill: AnyRecord) => ({
		label: skill.name ?? "unknown",
		tokens: estimateTokens(`${skill.name ?? ""}\n${skill.description ?? ""}`),
		detail: compactPath(skill.filePath ?? skill.sourceInfo?.path ?? ""),
		kind: skill.sourceInfo?.scope ?? "skills",
	}));
	const skillsByScope: Record<string, Item[]> = {};
	for (const item of skillItems) {
		const scope = item.kind ?? "skills";
		(skillsByScope[scope] ??= []).push(item);
	}

	const contextFiles = Array.isArray(options.contextFiles) ? options.contextFiles : [];
	const memoryItems: Item[] = contextFiles.map((file: AnyRecord) => ({
		label: compactPath(file.path ?? file.filePath ?? "context file"),
		tokens: estimateTokens(file.content ?? file.text ?? ""),
	}));

	const selected = selectedToolNames(options, pi);
	const allTools = pi.getAllTools();
	const toolItems: Item[] = allTools
		.filter((tool: AnyRecord) => selected.size === 0 || selected.has(tool.name))
		.map((tool: AnyRecord) => ({
			label: tool.name,
			// Match the prompt-facing footprint, not the full JSON schema object. Full
			// schemas badly overestimate startup usage compared with Pi's footer.
			tokens: estimateTokens([
				tool.name,
				tool.description,
				...(Array.isArray(tool.promptGuidelines) ? tool.promptGuidelines : []),
			].filter(Boolean).join("\n")),
			detail: tool.sourceInfo?.source ?? "tool",
		}));

	const knownPromptParts = [
		...skills.map((s: AnyRecord) => `${s.name ?? ""}\n${s.description ?? ""}`),
		...skills.map((s: AnyRecord) => s.description ?? ""),
		...contextFiles.map((f: AnyRecord) => f.content ?? f.text ?? ""),
		...(Array.isArray(options.promptGuidelines) ? options.promptGuidelines : []),
		options.customPrompt,
		options.appendSystemPrompt,
	].filter((v): v is string => typeof v === "string" && v.length > 0);

	const promptGuidelinesTokens = estimateTokens(Array.isArray(options.promptGuidelines) ? options.promptGuidelines.join("\n") : "");
	const customPromptTokens = estimateTokens([options.customPrompt, options.appendSystemPrompt].filter(Boolean).join("\n"));
	const systemBaseTokens = Math.max(estimateTokens(systemPrompt) ? 1 : 0, subtractKnown(systemPrompt, knownPromptParts));
	const systemItems = [
		{ label: "Pi system prompt", tokens: systemBaseTokens },
		{ label: "Prompt guidelines", tokens: promptGuidelinesTokens },
		{ label: "Custom/append prompt", tokens: customPromptTokens },
	].filter((item) => item.tokens > 0);

	const branch = ctx.sessionManager.getBranch?.() ?? [];
	const roleTokens = new Map<string, number>();
	const toolCallTokens = new Map<string, number>();
	const largest: Item[] = [];
	let messageEntries = 0;
	let conversationTokens = 0;

	for (const entry of branch) {
		if (entry.type !== "message") continue;
		messageEntries++;
		const role = messageRole(entry) ?? "message";
		const message = entry.message ?? {};
		const tokens = messageTokens(message);
		conversationTokens += tokens;
		pushCount(roleTokens, role, tokens);

		if (role === "assistant" && Array.isArray(message.content)) {
			for (const block of message.content) {
				if (block?.type === "toolCall" && block.name) {
					pushCount(toolCallTokens, block.name, estimateTokens(block.arguments ?? {}) + estimateTokens(block.name));
				}
			}
		}
		if (role === "toolResult" && message.toolName) {
			pushCount(toolCallTokens, `${message.toolName} result`, tokens);
		}

		largest.push({
			label: `${role}${entry.id ? ` ${entry.id}` : ""}`,
			tokens,
			detail: firstLine(contentText(message.content)).slice(0, 80),
		});
	}

	const startupSystem = systemItems.reduce((sum, item) => sum + item.tokens, 0);
	const startupTools = toolItems.reduce((sum, item) => sum + item.tokens, 0);
	const startupMemory = memoryItems.reduce((sum, item) => sum + item.tokens, 0);
	const startupSkills = skillItems.reduce((sum, item) => sum + item.tokens, 0);
	const startupTokens = startupSystem + startupTools + startupMemory + startupSkills;
	const measuredTotal = usage?.tokens ?? 0;
	const total = Math.max(measuredTotal, startupTokens + conversationTokens);
	const accounted = startupTokens + conversationTokens;
	const other = Math.max(0, total - accounted);
	const free = Math.max(0, limit - total);

	const categories = [
		{ label: "System prompt", tokens: startupSystem },
		{ label: "System tools", tokens: startupTools, detail: `${toolItems.length} active` },
		{ label: "Memory files", tokens: startupMemory, detail: `${memoryItems.length} files` },
		{ label: "Skills", tokens: startupSkills, detail: `${skillItems.length} loaded` },
		{ label: "Messages", tokens: conversationTokens, detail: `${messageEntries} entries` },
		{ label: "Provider/other", tokens: other },
		{ label: "Free space", tokens: free },
	];

	return {
		model,
		limit,
		total,
		free,
		mode: messageEntries === 0 ? "startup" : "conversation",
		categories,
		startup: {
			system: systemItems,
			tools: topItems(toolItems),
			memory: topItems(memoryItems),
			skills: Object.fromEntries(Object.entries(skillsByScope).map(([scope, items]) => [scope, topItems(items)])),
		},
		conversation: {
			entries: messageEntries,
			byRole: [...roleTokens.entries()].map(([label, tokens]) => ({ label, tokens })).sort((a, b) => b.tokens - a.tokens),
			toolCalls: [...toolCallTokens.entries()].map(([label, tokens]) => ({ label, tokens })).sort((a, b) => b.tokens - a.tokens).slice(0, MAX_LIST),
			largest: topItems(largest, 10),
		},
	};
}

function plainReport(report: ContextReport): string {
	const lines: string[] = [];
	lines.push(`Context Usage — ${report.model}`);
	lines.push(`${fmt(report.total)}/${fmt(report.limit)} tokens (${pct(report.total, report.limit)}) · free ${fmt(report.free)}`);
	lines.push("");
	lines.push("Breakdown");
	for (const item of report.categories) lines.push(`  ${item.label}: ${fmt(item.tokens)} (${pct(item.tokens, report.limit)})${item.detail ? ` · ${item.detail}` : ""}`);
	lines.push("");
	lines.push("Startup context");
	for (const item of report.startup.system) lines.push(`  ${item.label}: ${fmt(item.tokens)}`);
	for (const item of report.startup.tools) lines.push(`  tool ${item.label}: ${fmt(item.tokens)}`);
	for (const item of report.startup.memory) lines.push(`  memory ${item.label}: ${fmt(item.tokens)}`);
	for (const [scope, items] of Object.entries(report.startup.skills)) {
		lines.push(`  skills ${scope}`);
		for (const item of items) lines.push(`    ${item.label}: ${fmt(item.tokens)}`);
	}
	if (report.mode === "conversation") {
		lines.push("");
		lines.push("Conversation");
		for (const item of report.conversation.byRole) lines.push(`  ${item.label}: ${fmt(item.tokens)}`);
		if (report.conversation.toolCalls.length) lines.push("  Tool calls/results");
		for (const item of report.conversation.toolCalls) lines.push(`    ${item.label}: ${fmt(item.tokens)}`);
		lines.push("  Largest entries");
		for (const item of report.conversation.largest) lines.push(`    ${item.label}: ${fmt(item.tokens)} · ${item.detail ?? ""}`);
	}
	return lines.join("\n");
}

function renderReport(report: ContextReport, theme: any, width: number): string[] {
	const barWidth = Math.max(12, Math.min(28, Math.floor(width / 4)));
	const usedCells = Math.max(0, Math.min(barWidth, Math.round((report.total / report.limit) * barWidth)));
	const bar = `${"█".repeat(usedCells)}${"░".repeat(barWidth - usedCells)}`;
	const lines: string[] = [];
	const add = (line = "") => lines.push(line);
	const item = (prefix: string, row: Item) => {
		const amount = `${fmt(row.tokens)} (${pct(row.tokens, report.limit)})`;
		add(`${theme.fg("dim", prefix)} ${theme.fg("text", row.label)} ${theme.fg("dim", "·")} ${theme.fg("accent", amount)}${row.detail ? ` ${theme.fg("dim", "· " + row.detail)}` : ""}`);
	};

	add(`${theme.fg("accent", theme.bold("Context Usage"))} ${theme.fg("dim", "·")} ${theme.fg("text", report.model)}`);
	add(`${theme.fg(report.total / report.limit > 0.8 ? "error" : report.total / report.limit > 0.5 ? "warning" : "success", bar)} ${theme.fg("text", `${fmt(report.total)}/${fmt(report.limit)}`)} ${theme.fg("dim", `(${pct(report.total, report.limit)}) · free ${fmt(report.free)}`)}`);
	add("");
	add(theme.fg("dim", "Estimated usage by category"));
	for (const row of report.categories) item("├", row);
	add("");
	add(`${theme.fg("accent", "Startup context")} ${theme.fg("dim", report.mode === "startup" ? "before first message" : "base payload")}`);
	for (const row of report.startup.system) item("├", row);
	if (report.startup.memory.length) {
		add(theme.fg("dim", "├ Memory files"));
		for (const row of report.startup.memory) item("│ ├", row);
	}
	if (report.startup.tools.length) {
		add(theme.fg("dim", `├ System tools · top ${report.startup.tools.length}`));
		for (const row of report.startup.tools) item("│ ├", row);
	}
	for (const [scope, rows] of Object.entries(report.startup.skills)) {
		add(theme.fg("dim", `├ Skills · ${scope}`));
		for (const row of rows) item("│ ├", row);
	}
	if (report.mode === "conversation") {
		add("");
		add(`${theme.fg("accent", "Conversation")} ${theme.fg("dim", `${report.conversation.entries} entries`)}`);
		for (const row of report.conversation.byRole) item("├", row);
		if (report.conversation.toolCalls.length) {
			add(theme.fg("dim", "├ Tool calls/results"));
			for (const row of report.conversation.toolCalls) item("│ ├", row);
		}
		if (report.conversation.largest.length) {
			add(theme.fg("dim", "├ Largest message entries"));
			for (const row of report.conversation.largest) item("│ ├", row);
		}
	}

	return lines.map((line) => visibleWidth(line) > width ? truncateToWidth(line, width) : line);
}

async function showContextOverlay(report: ContextReport, ctx: any) {
	// overlay:false replaces the main viewport so the report fills the
	// screen, is scrollable (Ctrl+N/P), and disappears on Esc without
	// adding anything to the model context.
	await ctx.ui.custom((_tui: any, theme: any, _kb: any, done: (value?: unknown) => void) => ({
		render(width: number): string[] {
			const box = new Box(1, 1, (s) => theme.bg("customMessageBg", s));
			const body = [
				...renderReport(report, theme, Math.max(20, width - 2)),
				"",
				theme.fg("dim", "Esc/Enter to close · not added to model context"),
			].join("\n");
			box.addChild(new Text(body, 0, 0));
			return box.render(width);
		},
		invalidate() {},
		handleInput(data: string) {
			if (matchesKey(data, "enter") || matchesKey(data, "escape")) done(undefined);
		},
	}));
}

export default function (pi: ExtensionAPI) {
	pi.registerCommand("context", {
		description: "Show what is consuming the context window",
		handler: async (_args, ctx) => {
			const report = buildReport(pi, ctx);
			if (ctx.mode === "print" || !ctx.hasUI) {
				console.log(plainReport(report));
				return;
			}
			await showContextOverlay(report, ctx);
		},
	});
}
