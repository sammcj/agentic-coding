import type { ExtensionAPI, ExtensionCommandContext } from "@earendil-works/pi-coding-agent";
import {
	DynamicBorder,
	getMarkdownTheme,
	isEditToolResult,
	isToolCallEventType,
	isWriteToolResult,
} from "@earendil-works/pi-coding-agent";
import type { SelectItem } from "@earendil-works/pi-tui";
import { Container, Key, Markdown, SelectList, Text, matchesKey } from "@earendil-works/pi-tui";
import { readFile, writeFile, rm, mkdir } from "node:fs/promises";
import { dirname, relative, resolve } from "node:path";

// Custom session entry types
// New name: filechanges
const ENTRY_BASELINE = "filechanges:baseline";
const ENTRY_CLEAR = "filechanges:clear";
const ENTRY_UNTRACK = "filechanges:untrack";

type Baseline = {
	path: string; // normalized path relative to ctx.cwd where possible
	absPath: string;
	originalContent: string | null; // null => file did not exist (created)
	createdAt: number;
};

type TrackedFile = {
	path: string;
	absPath: string;
	displayPath: string;
	originalContent: string | null;
	currentContent: string;
	diff: string;
	added: number;
	removed: number;
	kind: "new" | "edited";
	updatedAt: number;
};

type PendingSnapshot = {
	path: string;
	absPath: string;
	before: string | null;
};

function stripAtPrefix(p: string): string {
	return p.startsWith("@") ? p.slice(1) : p;
}

function normalizeToolPath(cwd: string, raw: string): { absPath: string; relPath: string } {
	const cleaned = stripAtPrefix(raw);
	const absPath = resolve(cwd, cleaned);
	// Use relative path for storage/UI when possible. If it escapes cwd, keep the cleaned input.
	const rel = relative(cwd, absPath);
	const relPath = rel && !rel.startsWith("..") && rel !== "" ? rel : cleaned;
	return { absPath, relPath };
}

async function readTextOrNull(absPath: string): Promise<string | null> {
	try {
		return await readFile(absPath, "utf-8");
	} catch {
		return null;
	}
}

function countDiffLines(unifiedDiff: string): { added: number; removed: number } {
	let added = 0;
	let removed = 0;
	for (const line of unifiedDiff.split("\n")) {
		if (line.startsWith("+++ ") || line.startsWith("--- ") || line.startsWith("@@")) continue;
		if (line.startsWith("+")) added++;
		else if (line.startsWith("-")) removed++;
	}
	return { added, removed };
}

function formatAddedRemovedPlain(added: number, removed: number): string {
	return `(+${added}/-${removed})`;
}


function styleAddedRemovedForList(theme: any, text: string): string {
	// File rows use "+x/-y" as description; other rows use normal sentences.
	const m = text.match(/^\+(\d+)\/\-(\d+)$/);
	if (!m) return theme.fg("muted", text);
	const added = Number(m[1]);
	const removed = Number(m[2]);

	const plus = added === 0 ? theme.fg("text", `+${added}`) : theme.fg("success", `+${added}`);
	const minus = removed === 0 ? theme.fg("text", `-${removed}`) : theme.fg("error", `-${removed}`);
	return plus + theme.fg("text", "/") + minus;
}

function formatStatus(tracked: Map<string, TrackedFile>, theme?: any): string | undefined {
	if (tracked.size === 0) return undefined;
	let edited = 0;
	let created = 0;
	for (const t of tracked.values()) {
		if (t.kind === "new") created++;
		else edited++;
	}
	if (!theme) {
			return `Δ ${edited}  + ${created}`;
		}
	return theme.fg("muted", `Δ ${edited}  + ${created}`);
}

function buildWidgetLines(tracked: Map<string, TrackedFile>, theme?: any): string[] | undefined {
	if (tracked.size === 0) return undefined;
	const items = [...tracked.values()].sort((a, b) => b.updatedAt - a.updatedAt);
	const max = 8;
	const lines: string[] = [];

	// Separator between chat history and this widget (widget renders above the editor).
	//const sep = "─".repeat(60);
	//lines.push(theme ? theme.fg("borderMuted", sep) : sep);

	for (const t of items.slice(0, max)) {
		const tag = t.kind === "new" ? "+" : "Δ";

		if (!theme) {
			lines.push(`${tag} ${t.displayPath} ${formatAddedRemovedPlain(t.added, t.removed)}`);
			continue;
		}

		const prefix = theme.fg("muted", `${tag} `) + theme.fg("muted", `${t.displayPath} `);
		let counts: string;
		const plus = t.added === 0 ? theme.fg("text", `+${t.added}`) : theme.fg("success", `+${t.added}`);
		const minus = t.removed === 0 ? theme.fg("text", `-${t.removed}`) : theme.fg("error", `-${t.removed}`);
		counts = theme.fg("text", "(") + plus + theme.fg("text", "/") + minus + theme.fg("text", ")");

		lines.push(prefix + counts);
	}
	if (items.length > max) {
		lines.push(theme ? theme.fg("dim", `…and ${items.length - max} more`) : `…and ${items.length - max} more`);
	}
	return lines;
}

function diffLines(original: string[], current: string[]): Array<{ type: "same" | "add" | "remove"; line: string }> {
	const rows = original.length;
	const cols = current.length;
	const dp: number[][] = Array.from({ length: rows + 1 }, () => Array(cols + 1).fill(0));
	for (let i = rows - 1; i >= 0; i--) {
		for (let j = cols - 1; j >= 0; j--) {
			dp[i][j] = original[i] === current[j] ? dp[i + 1][j + 1] + 1 : Math.max(dp[i + 1][j], dp[i][j + 1]);
		}
	}

	const out: Array<{ type: "same" | "add" | "remove"; line: string }> = [];
	let i = 0;
	let j = 0;
	while (i < rows && j < cols) {
		if (original[i] === current[j]) {
			out.push({ type: "same", line: original[i] });
			i++;
			j++;
		} else if (dp[i + 1][j] >= dp[i][j + 1]) {
			out.push({ type: "remove", line: original[i++] });
		} else {
			out.push({ type: "add", line: current[j++] });
		}
	}
	while (i < rows) out.push({ type: "remove", line: original[i++] });
	while (j < cols) out.push({ type: "add", line: current[j++] });
	return out;
}

function splitLines(text: string): string[] {
	if (text.length === 0) return [];
	return text.replace(/\n$/, "").split("\n");
}

function patchFromBaseline(displayPath: string, original: string | null, current: string): string {
	const before = splitLines(original ?? "");
	const after = splitLines(current);
	const diff = diffLines(before, after);
	const lines = [`--- ${displayPath}`, `+++ ${displayPath}`, "@@"];
	for (const part of diff) {
		if (part.type === "add") lines.push(`+${part.line}`);
		else if (part.type === "remove") lines.push(`-${part.line}`);
		else lines.push(` ${part.line}`);
	}
	return `${lines.join("\n")}\n`;
}

async function ensureParentDir(absPath: string): Promise<void> {
	await mkdir(dirname(absPath), { recursive: true });
}

export default function (pi: ExtensionAPI) {
	// In-memory state (reconstructed on session_start from custom entries)
	const baselines = new Map<string, Baseline>(); // key: relPath
	const tracked = new Map<string, TrackedFile>(); // key: relPath

	// Per-tool-call snapshot, only committed on successful tool_result
	const pendingByToolCallId = new Map<string, PendingSnapshot>();

	function updateUi(ctx: any) {
		if (!ctx?.hasUI) return;

		ctx.ui.setStatus("filechanges", formatStatus(tracked, ctx.ui.theme));
		ctx.ui.setWidget("filechanges", buildWidgetLines(tracked, ctx.ui.theme));
	}

	async function recomputeTrackedFile(ctx: any, relPath: string) {
		const baseline = baselines.get(relPath);
		if (!baseline) return;

		const current = await readTextOrNull(baseline.absPath);
		if (baseline.originalContent === null) {
			// file was created
			if (current === null) {
				tracked.delete(relPath);
				return;
			}
			const displayPath = baseline.path;
			const diff = patchFromBaseline(displayPath, null, current);
			const { added, removed } = countDiffLines(diff);
			tracked.set(relPath, {
				path: baseline.path,
				absPath: baseline.absPath,
				displayPath,
				originalContent: null,
				currentContent: current,
				diff,
				added,
				removed,
				kind: "new",
				updatedAt: Date.now(),
			});
			return;
		}

		// file existed before
		if (current === null) {
			// Deleted outside of tracked tools (or manually). Still track as edited; diff will show removal.
			const displayPath = baseline.path;
			const diff = patchFromBaseline(displayPath, baseline.originalContent, "");
			const { added, removed } = countDiffLines(diff);
			tracked.set(relPath, {
				path: baseline.path,
				absPath: baseline.absPath,
				displayPath,
				originalContent: baseline.originalContent,
				currentContent: "",
				diff,
				added,
				removed,
				kind: "edited",
				updatedAt: Date.now(),
			});
			return;
		}

		if (current === baseline.originalContent) {
			// back to original; untrack
			tracked.delete(relPath);
			return;
		}

		const displayPath = baseline.path;
		const diff = patchFromBaseline(displayPath, baseline.originalContent, current);
		const { added, removed } = countDiffLines(diff);
		tracked.set(relPath, {
			path: baseline.path,
			absPath: baseline.absPath,
			displayPath,
			originalContent: baseline.originalContent,
			currentContent: current,
			diff,
			added,
			removed,
			kind: "edited",
			updatedAt: Date.now(),
		});
	}

	async function clearLog(ctx: ExtensionCommandContext, reason: "accept" | "decline") {
		baselines.clear();
		tracked.clear();
		pendingByToolCallId.clear();
		pi.appendEntry(ENTRY_CLEAR, { timestamp: Date.now(), reason });
		updateUi(ctx);
	}

	async function declineAll(ctx: ExtensionCommandContext) {
		await ctx.waitForIdle();

		if (tracked.size === 0) {
			if (ctx.hasUI) ctx.ui.notify("filechanges: nothing to decline.", "info");
			return;
		}

		const force = (ctx as any).args?.includes("force") ?? false;
		if (ctx.hasUI && !force) {
			const ok = await ctx.ui.confirm(
				"Decline pi changes?",
				"This will revert ALL currently logged pi changes (overwrite files / delete created files)."
			);
			if (!ok) return;
		} else if (!ctx.hasUI && !force) {
			throw new Error("Decline requires confirmation. Run: /filechanges-decline force");
		}

		const items = [...tracked.values()].sort((a, b) => b.updatedAt - a.updatedAt);
		let reverted = 0;
		const errors: string[] = [];

		for (const item of items) {
			try {
				if (item.originalContent === null) {
					// created file
					await rm(item.absPath, { force: true });
				} else {
					await ensureParentDir(item.absPath);
					await writeFile(item.absPath, item.originalContent, "utf-8");
				}
				reverted++;
			} catch (e: any) {
				errors.push(`${item.displayPath}: ${e?.message ?? String(e)}`);
			}
		}

		await clearLog(ctx, "decline");

		if (ctx.hasUI) {
			if (errors.length === 0) {
				ctx.ui.notify(`filechanges: declined changes for ${reverted} file(s).`, "info");
			} else {
				ctx.ui.notify(
					`filechanges: declined with ${errors.length} error(s). Run /filechanges to inspect; see console for details.`,
					"warning"
				);
				console.warn("[filechanges] decline errors:\n" + errors.join("\n"));
			}
		}
	}

	async function acceptAll(ctx: ExtensionCommandContext) {
		await ctx.waitForIdle();

		if (tracked.size === 0) {
			if (ctx.hasUI) ctx.ui.notify("filechanges: nothing to accept.", "info");
			return;
		}

		const force = (ctx as any).args?.includes("force") ?? false;
		if (ctx.hasUI && !force) {
			const ok = await ctx.ui.confirm(
				"Accept pi changes?",
				"This will keep current files as-is and clear the modification log."
			);
			if (!ok) return;
		} else if (!ctx.hasUI && !force) {
			throw new Error("Accept requires confirmation. Run: /filechanges-accept force");
		}

		const count = tracked.size;
		await clearLog(ctx, "accept");
		if (ctx.hasUI) ctx.ui.notify(`filechanges: accepted changes for ${count} file(s).`, "info");
	}

	function parseCommandArgs(args: string | undefined): string[] {
		if (!args) return [];
		return args
			.split(/\s+/g)
			.map((s) => s.trim())
			.filter(Boolean);
	}

	// Commands
	pi.registerCommand("filechanges", {
		description: "Show files changed by pi and inspect diffs",
		handler: async (_args, ctx) => {
			// Provide args to helpers (a bit hacky but keeps code compact)
			(ctx as any).args = parseCommandArgs(_args);

			await ctx.waitForIdle();
			updateUi(ctx);

			if (!ctx.hasUI) {
				const items = [...tracked.values()].sort((a, b) => b.updatedAt - a.updatedAt);
				if (items.length === 0) {
					console.log("filechanges: no pi-made modifications recorded.");
					return;
				}
				// Non-interactive: just print a summary to stdout
				const lines = buildWidgetLines(tracked) ?? [];
				console.log(lines.join("\n"));
				return;
			}

			// Interactive loop: ESC in diff view returns to the modification log.
			while (true) {
				await ctx.waitForIdle();
				updateUi(ctx);

				const items = [...tracked.values()].sort((a, b) => b.updatedAt - a.updatedAt);
				if (items.length === 0) {
					ctx.ui.notify("filechanges: no pi-made modifications recorded.", "info");
					return;
				}

				const selectItems: SelectItem[] = [
					{ value: "__accept__", label: "Accept changes (clear log)", description: "Keep current files" },
					{ value: "__decline__", label: "Undo changes (revert)", description: "Restore original contents" },
					{ value: "__sep__", label: "────────", description: "" },
					...items.map((t) => ({
						value: t.path,
						label: `${t.kind === "new" ? "+" : "Δ"} ${t.displayPath}`,
						description: `+${t.added}/-${t.removed}`,
					})),
				];

				const picked = await ctx.ui.custom<string | null>((tui, theme, _kb, done) => {
					const container = new Container();
					container.addChild(new DynamicBorder((s: string) => theme.fg("accent", s)));
					container.addChild(new Text(theme.fg("accent", theme.bold("File changes")), 1, 0));

					const list = new SelectList(selectItems, Math.min(14, selectItems.length), {
						selectedPrefix: (t) => theme.fg("accent", t),
						selectedText: (t) => theme.fg("accent", t),
						description: (t) => styleAddedRemovedForList(theme, t),
						scrollInfo: (t) => theme.fg("dim", t),
						noMatch: (t) => theme.fg("warning", t),
					});

					list.onSelect = (item) => {
						if (item.value === "__sep__") return;
						done(item.value);
					};
					list.onCancel = () => done(null);
					container.addChild(list);

					container.addChild(
						new Text(theme.fg("dim", "↑↓ navigate • enter select • esc close"), 1, 0)
					);
					container.addChild(new DynamicBorder((s: string) => theme.fg("accent", s)));

					return {
						render: (w) => container.render(w),
						invalidate: () => container.invalidate(),
						handleInput: (data) => {
							list.handleInput(data);
							tui.requestRender();
						},
					};
				}, { overlay: true });

				if (!picked) return;
				if (picked === "__accept__") {
					await acceptAll(ctx);
					return;
				}
				if (picked === "__decline__") {
					await declineAll(ctx);
					return;
				}

				const t = tracked.get(picked);
				if (!t) {
					ctx.ui.notify("filechanges: entry not found (maybe log was cleared).", "warning");
					continue;
				}

				const md = "```diff\n" + (t.diff.trimEnd() || "(no diff)") + "\n```";
				await ctx.ui.custom<void>((tui, theme, _kb, done) => {
					const container = new Container();
					container.addChild(new DynamicBorder((s: string) => theme.fg("accent", s)));
					container.addChild(new Text(theme.fg("accent", theme.bold(t.displayPath)), 1, 0));
					container.addChild(new Markdown(md, 1, 0, getMarkdownTheme()));
					container.addChild(new Text(theme.fg("dim", "esc to go back"), 1, 0));
					container.addChild(new DynamicBorder((s: string) => theme.fg("accent", s)));

					return {
						render: (w) => container.render(w),
						invalidate: () => container.invalidate(),
						handleInput: (data) => {
							if (matchesKey(data, Key.escape) || matchesKey(data, Key.ctrl("c"))) done();
							else tui.requestRender();
						},
					};
				}, { overlay: true });

				// After closing diff, loop back to the modification log.
			}
		},
	});

	pi.registerCommand("filechanges-accept", {
		description: "Accept pi-made changes (keeps files, clears log)",
		handler: async (args, ctx) => {
			(ctx as any).args = parseCommandArgs(args);
			await acceptAll(ctx);
		},
	});

	pi.registerCommand("filechanges-decline", {
		description: "Decline pi-made changes (reverts files, clears log)",
		handler: async (args, ctx) => {
			(ctx as any).args = parseCommandArgs(args);
			await declineAll(ctx);
		},
	});

	async function rebuildFromSession(ctx: any): Promise<void> {
		baselines.clear();
		tracked.clear();
		pendingByToolCallId.clear();

		// Replay custom entries on current branch
		for (const entry of ctx.sessionManager.getBranch()) {
			if (entry.type !== "custom") continue;

			if (entry.customType === ENTRY_CLEAR) {
				baselines.clear();
				tracked.clear();
				continue;
			}

			if (entry.customType === ENTRY_BASELINE) {
				const data = entry.data as any;
				if (!data?.path) continue;
				const { absPath, relPath } = normalizeToolPath(ctx.cwd, data.path);
				baselines.set(relPath, {
					path: relPath,
					absPath,
					originalContent: typeof data.originalContent === "string" ? data.originalContent : null,
					createdAt: typeof data.timestamp === "number" ? data.timestamp : Date.now(),
				});
				continue;
			}

			if (entry.customType === ENTRY_UNTRACK) {
				const data = entry.data as any;
				if (!data?.path) continue;
				const { relPath } = normalizeToolPath(ctx.cwd, data.path);
				baselines.delete(relPath);
				tracked.delete(relPath);
				continue;
			}
		}

		// Compute current diffs
		for (const relPath of baselines.keys()) {
			await recomputeTrackedFile(ctx, relPath);
		}

		updateUi(ctx);
	}

	// Rebuild state on any session/branch navigation. session_start carries a reason of
	// "startup" | "reload" | "new" | "resume" | "fork", so switching and forking arrive
	// here too - there are no separate session_switch / session_fork events.
	pi.on("session_start", async (_event, ctx) => {
		await rebuildFromSession(ctx);
	});

	pi.on("session_tree", async (_event, ctx) => {
		await rebuildFromSession(ctx);
	});

	// Capture before snapshots for edit/write
	pi.on("tool_call", async (event, ctx) => {
		if (isToolCallEventType("edit", event) || isToolCallEventType("write", event)) {
			const { absPath, relPath } = normalizeToolPath(ctx.cwd, event.input.path);
			const before = await readTextOrNull(absPath);
			pendingByToolCallId.set(event.toolCallId, { path: relPath, absPath, before });
		}
	});

	// Commit on successful results
	pi.on("tool_result", async (event, ctx) => {
		if (event.isError) {
			pendingByToolCallId.delete(event.toolCallId);
			return;
		}

		if (!isEditToolResult(event) && !isWriteToolResult(event)) return;

		const pending = pendingByToolCallId.get(event.toolCallId);
		pendingByToolCallId.delete(event.toolCallId);
		if (!pending) return;

		// If no baseline exists yet for this file, create one now from the successful call's snapshot.
		if (!baselines.has(pending.path)) {
			baselines.set(pending.path, {
				path: pending.path,
				absPath: pending.absPath,
				originalContent: pending.before,
				createdAt: Date.now(),
			});
			pi.appendEntry(ENTRY_BASELINE, {
				path: pending.path,
				originalContent: pending.before,
				timestamp: Date.now(),
			});
		}

		// Recompute cumulative diff against baseline
		await recomputeTrackedFile(ctx, pending.path);

		// If file is back to baseline, untrack + persist
		const baseline = baselines.get(pending.path);
		const current = await readTextOrNull(pending.absPath);
		if (baseline) {
			const backToOriginal =
				(baseline.originalContent !== null && current === baseline.originalContent) ||
				(baseline.originalContent === null && current === null);

			if (backToOriginal) {
				baselines.delete(pending.path);
				tracked.delete(pending.path);
				pi.appendEntry(ENTRY_UNTRACK, { path: pending.path, timestamp: Date.now() });
			}
		}

		updateUi(ctx);
	});
}
