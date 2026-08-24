// Complements cc-safety-net rather than duplicating it.
// - cc-safety-net (preset `standard`) covers: git reset --hard, clean -fd, branch -D,
//   push --force/--delete, find -delete, secret reads. Parses command IR, so it also
//   sees through `bash -c` / `python -c` wrappers.
// - It ALLOWS anything project-scoped or under sudo. This guard covers that gap:
//   sudo, package removal, service state, --amend/rebase, truncate, `>` overwrites, ctx_purge.
// - Deletes and redirects proven to land inside the launch project skip the prompt. Proof is
//   argv-level and symlink-resolved; anything unprovable (substitution, `~`, `..`, cwd moves,
//   heredocs) still prompts. Toggle with `/safety deletes off`.
// - Everything outside that proof is still regex matching, so treat it as a prompt, not a boundary.
//   cc-safety-net is the enforcing layer; raise it to `strict` rather than hardening this file.
import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import { existsSync, mkdirSync, readFileSync, realpathSync, writeFileSync } from "node:fs";
import { basename, dirname, join, resolve, sep } from "node:path";
import { homedir } from "node:os";

type SafetyConfig = {
	enabled: boolean;
	/** Skip the delete prompt when every rm target resolves inside the project root. */
	allowProjectScopedDeletes: boolean;
};

/** Project root (where pi was started) plus the cwd the bash tool will run in. */
type DeleteScope = { root: string; cwd: string };

type Risk = {
	action: string;
	command?: string;
	reason?: string;
};

const CONFIG_PATH = join(homedir(), ".pi", "agent", "safety-guard.json");

const DEFAULT_CONFIG: SafetyConfig = { enabled: true, allowProjectScopedDeletes: true };

function loadConfig(): SafetyConfig {
	try {
		const parsed = JSON.parse(readFileSync(CONFIG_PATH, "utf8")) as Partial<SafetyConfig>;
		return { ...DEFAULT_CONFIG, ...parsed };
	} catch {
		return DEFAULT_CONFIG;
	}
}

function saveConfig(config: SafetyConfig) {
	mkdirSync(dirname(CONFIG_PATH), { recursive: true });
	writeFileSync(CONFIG_PATH, JSON.stringify(config, null, 2) + "\n", "utf8");
}

function formatRisk(risk: Risk): string {
	const lines = [`ACTION: ${risk.action}`];
	if (risk.command) lines.push(`COMMAND: \`${risk.command}\``);
	if (risk.reason) lines.push(`REASON: ${risk.reason}`);
	return lines.join("\n");
}

function shellWords(command: string): string[] {
	return command
		.split(/\s+/)
		.map((part) => part.trim())
		.filter(Boolean);
}

/** One simple command: its words, plus the files its redirects would truncate or append to. */
type Segment = { argv: string[]; writes: string[] };

/**
 * Splits a command into per-segment argv and redirect targets, or returns undefined when anything
 * defeats static analysis. Bailing is the safe outcome: callers fall back to prompting.
 *
 * Rejected outright: substitution (`$`, backticks), subshells, brace expansion, heredocs and `~`.
 * Their expansion is only known at run time, so a target cannot be proven in-project.
 */
function tokenizeSegments(command: string): Segment[] | undefined {
	const segments: Segment[] = [];
	let argv: string[] = [];
	let writes: string[] = [];
	let token = "";
	let hasToken = false;
	/** Set once a redirect operator is seen, so the next word is its target rather than a word. */
	let pending: "write" | "read" | undefined;

	const endToken = () => {
		if (!hasToken) return;
		// `2>&1` and friends duplicate a descriptor rather than naming a file.
		if (pending === "write" && !token.startsWith("&")) writes.push(token);
		else if (!pending) argv.push(token);
		pending = undefined;
		token = "";
		hasToken = false;
	};
	const endSegment = () => {
		endToken();
		if (argv.length || writes.length) segments.push({ argv, writes });
		argv = [];
		writes = [];
	};

	for (let i = 0; i < command.length; i++) {
		const char = command[i];

		if (char === "\\") {
			const next = command[++i];
			if (next === undefined) return undefined;
			if (next !== "\n") {
				token += next;
				hasToken = true;
			}
			continue;
		}

		if (char === "'" || char === '"') {
			const close = command.indexOf(char, i + 1);
			if (close === -1) return undefined;
			const inner = command.slice(i + 1, close);
			// Double quotes still expand; a literal backslash inside them needs a real parser.
			if (char === '"' && /[$`\\]/.test(inner)) return undefined;
			token += inner;
			hasToken = true;
			i = close;
			continue;
		}

		if ("$`(){}".includes(char)) return undefined;

		// `&>` redirects all output, so check it before `&` is read as a segment break.
		if (char === ">" || (char === "&" && command[i + 1] === ">")) {
			if (char === "&") i++;
			// A leading descriptor number belongs to the operator, not to the preceding word.
			if (hasToken && /^\d+$/.test(token) && !pending) {
				token = "";
				hasToken = false;
			}
			endToken();
			if (command[i + 1] === ">" || command[i + 1] === "|") i++;
			pending = "write";
			continue;
		}

		if (char === "<") {
			// `<<` heredoc and `<<<` herestring carry inline content a word split cannot model.
			if (command[i + 1] === "<") return undefined;
			endToken();
			pending = "read";
			continue;
		}

		if (char === ";" || char === "\n" || char === "&" || char === "|") {
			// Collapse the two-character forms; a trailing bare `&` backgrounds, which is fine here.
			if (command[i + 1] === char) i++;
			endSegment();
			continue;
		}

		if (char === " " || char === "\t") {
			endToken();
			continue;
		}

		if (char === "~" && !hasToken) return undefined;

		token += char;
		hasToken = true;
	}

	// A redirect with no target is malformed; refuse to reason about it.
	if (pending && !hasToken) return undefined;
	endSegment();
	return segments;
}

/** Resolves symlinks as deep as the path currently exists, keeping the non-existent tail. */
function realpathDeepest(absolute: string): string {
	let current = absolute;
	const tail: string[] = [];
	for (;;) {
		try {
			return join(realpathSync(current), ...tail.reverse());
		} catch {
			const parent = dirname(current);
			if (parent === current) return absolute;
			tail.push(basename(current));
			current = parent;
		}
	}
}

function isStrictlyInside(root: string, path: string): boolean {
	return path !== root && path.startsWith(root.endsWith(sep) ? root : root + sep);
}

const PROTECTED_BASENAME = /^\.git$|^\.env($|\.)/;

/**
 * True when this rm operand can only ever remove something below the project root.
 *
 * Globs are resolved to the directory that holds their matches - `*` never crosses `/`, so
 * `./dist/*` cannot escape `./dist`. Symlinks are resolved before the containment test, which
 * is what stops `rm -rf ./link/` where `link` points outside the project.
 */
function operandWithinRoot(operand: string, scope: DeleteScope): boolean {
	if (!operand || operand.startsWith("~")) return false;

	const meta = operand.search(/[*?[\]]/);
	let literal = operand;
	if (meta >= 0) {
		const cut = operand.lastIndexOf("/", meta);
		literal = cut < 0 ? "." : operand.slice(0, cut);
	}

	if (/(^|\/)\.\.(\/|$)/.test(literal)) return false;

	const resolved = realpathDeepest(resolve(scope.cwd, literal));
	if (!isStrictlyInside(scope.root, resolved) && !(meta >= 0 && resolved === scope.root)) {
		return false;
	}
	// `rm -rf *` at the project root would wipe the checkout; that still deserves a prompt.
	if (meta >= 0 && resolved === scope.root) return false;
	if (PROTECTED_BASENAME.test(basename(resolved))) return false;

	return true;
}

const RM_SHORT_FLAGS = new Set(["r", "R", "f", "v", "d"]);
const RM_LONG_FLAGS = new Set(["--recursive", "--force", "--verbose", "--dir"]);
const RM_BINARIES = new Set(["rm", "/bin/rm", "/usr/bin/rm"]);

function isScopedRm(argv: string[], scope: DeleteScope): boolean {
	if (!RM_BINARIES.has(argv[0])) return false;

	const operands: string[] = [];
	let endOfFlags = false;
	for (const arg of argv.slice(1)) {
		if (endOfFlags || !arg.startsWith("-") || arg === "-") {
			operands.push(arg);
			continue;
		}
		if (arg === "--") {
			endOfFlags = true;
			continue;
		}
		if (arg.startsWith("--")) {
			if (!RM_LONG_FLAGS.has(arg)) return false;
			continue;
		}
		if (![...arg.slice(1)].every((flag) => RM_SHORT_FLAGS.has(flag))) return false;
	}

	return operands.length > 0 && operands.every((operand) => operandWithinRoot(operand, scope));
}

/**
 * Words that make a neighbouring segment untrustworthy: they either delete, or move the cwd out
 * from under the containment test - `cd .. && rm -rf project` is in-project by argv alone but is
 * not in practice. Matching is per-argument, so it also catches these nested inside a quoted
 * `bash -c '...'` payload.
 *
 * Interpreter names are deliberately absent. `rm -rf ./build && bun test` is the pattern this
 * allowance exists for, and a bare `bun test` in its own tool call never prompted anyway - chaining
 * it after a delete that is already proven in-project does not add risk. Inline code is different,
 * so INLINE_CODE_FLAG below covers `node -e` and friends, whose payload can delete via an API call
 * that no wordlist can see.
 */
const DELETE_ADJACENT =
	/\b(rm|rmdir|unlink|shred|truncate|dd|mkfs|find|xargs|sudo|doas|eval|exec|source|cd|pushd|popd|chroot|git)\b/i;

/** Flags that hand a segment an arbitrary code payload rather than a file to act on. */
const INLINE_CODE_FLAG = new Set(["-e", "-c", "-E", "--eval", "--command", "--exec"]);

/** Prefixes that can sit in front of the real binary without changing what it is. */
const COMMAND_WRAPPERS = new Set(["sudo", "doas", "env", "time", "nice", "command", "xargs", "builtin"]);

/**
 * True when the command invokes `rm` at all - including under a wrapper such as `sudo` or `xargs`.
 *
 * Segment-anchored so `cargo rm serde` and `npm rm pkg` do not trip it, with a loose text fallback
 * for the cases the tokeniser refuses (quoted `bash -c`, brace expansion), where prompting is right.
 */
function invokesRm(command: string, normalized: string): boolean {
	if (/(?:^|[;|&\n('"]|\b(?:sudo|doas|env|time|nice|command|xargs|builtin)\s)\s*rm\s+[-/.]/i.test(normalized)) {
		return true;
	}

	const segments = tokenizeSegments(command);
	if (!segments) return /\brm\b/i.test(normalized);

	return segments.some(({ argv }) => {
		for (const arg of argv) {
			if (RM_BINARIES.has(arg)) return true;
			if (arg.startsWith("-") || arg.includes("=")) continue;
			if (!COMMAND_WRAPPERS.has(arg)) return false;
		}
		return false;
	});
}

/**
 * True when the whole command's deleting is provably confined to the project. Every segment must
 * be either a project-scoped `rm` or plainly non-destructive, so `rm -rf ./build && npm run build`
 * passes while `rm -rf ./build && sudo rm -f /etc/hosts` does not.
 */
function deleteIsProjectScoped(command: string, scope: DeleteScope | undefined): boolean {
	if (!scope) return false;
	if (scope.cwd !== scope.root && !isStrictlyInside(scope.root, scope.cwd)) return false;

	const segments = tokenizeSegments(command);
	if (!segments?.length) return false;

	let sawRm = false;
	for (const { argv } of segments) {
		if (RM_BINARIES.has(argv[0])) {
			if (!isScopedRm(argv, scope)) return false;
			sawRm = true;
			continue;
		}
		if (argv.some((arg) => INLINE_CODE_FLAG.has(arg) || DELETE_ADJACENT.test(arg))) return false;
	}

	return sawRm;
}

/** File types worth a prompt when clobbered - source, config and lockfiles, not build chatter. */
const MEANINGFUL_FILE =
	/(\.env|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|\.json|\.ts|\.tsx|\.js|\.jsx|\.py|\.rs|\.go)$/i;

/** Matches the redirect shape the tokeniser cannot reach, so an unparseable command still prompts. */
const REDIRECT_FALLBACK =
	/>\s*[^&\s][^\n]*(\.env|package-lock\.json|pnpm-lock\.yaml|yarn\.lock|\.json|\.ts|\.tsx|\.js|\.jsx|\.py|\.rs|\.go)\b/i;

/**
 * True when a `>` or `>>` would clobber a meaningful file the project does not own.
 *
 * Redirects into the project are left alone for the same reason in-project deletes are: they are
 * the agent's normal working traffic and git already covers them. `2>&1`, `> /dev/null` and build
 * chatter never matched in the first place.
 */
function overwritesFileOutsideProject(command: string, normalized: string, scope: DeleteScope | undefined): boolean {
	const segments = tokenizeSegments(command);
	if (!segments) return REDIRECT_FALLBACK.test(normalized);

	const targets = segments.flatMap((segment) => segment.writes);
	return targets.some(
		(target) => MEANINGFUL_FILE.test(target) && !(scope && operandWithinRoot(target, scope)),
	);
}

export const __test = {
	tokenizeSegments,
	operandWithinRoot,
	deleteIsProjectScoped,
	overwritesFileOutsideProject,
	userExplicitlyRequestedRisk,
	classifyBash,
};

function classifyBash(command: string, scope?: DeleteScope): Risk | undefined {
	const normalized = command.replace(/\\\n/g, " ").replace(/\s+/g, " ").trim();
	const words = shellWords(normalized);

	if (/\bgit\s+push\b[\s\S]*(--force|-f|--force-with-lease)\b/i.test(normalized)) {
		return {
			action: "Force push git history",
			command,
			reason: "Force pushes can overwrite remote history for other collaborators.",
		};
	}

	if (/\bgit\s+commit\b[\s\S]*(--amend)\b/i.test(normalized)) {
		return {
			action: "Amend the latest git commit",
			command,
			reason: "Amending rewrites local commit history.",
		};
	}

	if (/\bgit\s+reset\b[\s\S]*(--hard)\b/i.test(normalized)) {
		return {
			action: "Hard reset git working tree",
			command,
			reason: "A hard reset discards uncommitted local changes.",
		};
	}

	if (/\bgit\s+(rebase|filter-branch)\b/i.test(normalized)) {
		return {
			action: "Rewrite git history",
			command,
			reason: "This git operation can rewrite commit history.",
		};
	}

	if (/\bgit\s+(branch|tag)\b[\s\S]*\s-d\b|\bgit\s+(branch|tag)\b[\s\S]*\s-D\b|\bgit\s+push\b[\s\S]*(:refs\/|--delete)\b/i.test(normalized)) {
		return {
			action: "Delete git branch or tag",
			command,
			reason: "Deleting refs can remove useful recovery points.",
		};
	}

	if (invokesRm(command, normalized) || /\bfind\b[\s\S]*\s-delete\b/i.test(normalized)) {
		if (deleteIsProjectScoped(command, scope)) return undefined;
		return {
			action: "Delete files or directories",
			command,
			reason: "The command removes data from the filesystem.",
		};
	}

	if (/\b(truncate|shred)\b/i.test(normalized) || overwritesFileOutsideProject(command, normalized, scope)) {
		return {
			action: "Overwrite or erase file contents",
			command,
			reason: "The command may replace existing file contents.",
		};
	}

	if (/\b(sudo\s+)?(apt|apt-get|dnf|yum|pacman|brew)\s+(remove|purge|uninstall|autoremove)\b/i.test(normalized)) {
		return {
			action: "Remove system packages",
			command,
			reason: "Package removal can change the host system outside the project.",
		};
	}

	if (/\b(sudo\s+)?(systemctl|service)\s+(stop|disable|restart)\b/i.test(normalized)) {
		return {
			action: "Change system service state",
			command,
			reason: "Service changes can disrupt running system processes.",
		};
	}

	if (words.includes("sudo")) {
		return {
			action: "Run a privileged system command",
			command,
			reason: "sudo commands can modify system-level state.",
		};
	}

	return undefined;
}

function classifyFileTool(toolName: string, input: Record<string, unknown>, inGitRepo: boolean): Risk | undefined {
	const path = typeof input.path === "string" ? input.path : undefined;
	if (!path) return undefined;

	if (/(^|\/)\.env($|\.)|(^|\/)\.git(\/|$)|(^|\/)node_modules(\/|$)/.test(path)) {
		return {
			action: `Modify protected path ${path}`,
			reason: "Protected paths often contain secrets, git internals, or dependency artifacts.",
		};
	}

	if (inGitRepo) return undefined;

	if (toolName === "write" && existsSync(path)) {
		return {
			action: `Overwrite existing file ${path}`,
			reason: "This file is not protected by a detected git recovery point.",
		};
	}

	if (toolName === "edit") {
		const edits = Array.isArray(input.edits) ? input.edits.length : 1;
		if (edits >= 3) {
			return {
				action: `Apply ${edits} edits to ${path}`,
				reason: "Large-scale edits outside a detected git repo are harder to recover.",
			};
		}
	}

	return undefined;
}

function lastUserText(ctx: ExtensionContext): string {
	const entries = ctx.sessionManager.getEntries();
	for (let i = entries.length - 1; i >= 0; i--) {
		const entry = entries[i] as any;
		const message = entry.type === "message" ? entry.message : undefined;
		if (message?.role !== "user") continue;
		const content = message.content;
		if (typeof content === "string") return content;
		if (Array.isArray(content)) {
			return content
				.map((part) => (part?.type === "text" && typeof part.text === "string" ? part.text : ""))
				.join("\n")
				.trim();
		}
	}
	return "";
}

/**
 * Only a verbatim quotation of the command counts as consent.
 *
 * This used to keyword-match the message instead: "delete the old build output" set a flag that
 * waved through every delete-shaped risk for the rest of the turn, `rm -rf ~` included - one
 * sentence silently disarmed the guard. Deletes inside the project no longer prompt at all, so the
 * loose form has nothing left to earn.
 */
function userExplicitlyRequestedRisk(userText: string, risk: Risk): boolean {
	if (!risk.command) return false;
	const collapse = (text: string) => text.toLowerCase().replace(/\s+/g, " ").trim();
	const command = collapse(risk.command);
	return command.length > 0 && collapse(userText).includes(command);
}

async function isInsideGitRepo(pi: ExtensionAPI): Promise<boolean> {
	try {
		const result = await pi.exec("git", ["rev-parse", "--is-inside-work-tree"]);
		return result.code === 0 && result.stdout.trim() === "true";
	} catch {
		return false;
	}
}

async function shouldAllowRisk(risk: Risk, ctx: ExtensionContext): Promise<boolean> {
	if (!ctx.hasUI) return false;

	const choice = await ctx.ui.select(`${formatRisk(risk)}\n\nAllow this action?`, [
		"Allow once",
		"Block",
	]);

	return choice === "Allow once";
}

export default function safetyGuard(pi: ExtensionAPI) {
	let config = loadConfig();
	// Pinned at load, so a later `cd` cannot widen the delete allowance beyond the launch project.
	const projectRoot = realpathDeepest(process.cwd());

	function deleteScope(ctx: ExtensionContext): DeleteScope | undefined {
		if (!config.allowProjectScopedDeletes) return undefined;
		return { root: projectRoot, cwd: realpathDeepest(ctx.cwd || projectRoot) };
	}

	function setEnabled(enabled: boolean) {
		config = { ...config, enabled };
		saveConfig(config);
	}

	function setScopedDeletes(allowProjectScopedDeletes: boolean) {
		config = { ...config, allowProjectScopedDeletes };
		saveConfig(config);
	}

	function safetyPrompt(): string {
		return `\n\nSafety Guard is enabled. Before performing a destructive action that the user did not explicitly request, ask for permission with ask_user_question and use this template in the option/description text:\nACTION: one-line short but understandable description\nCOMMAND (if applicable): \`command here\`\nREASON (if applicable): one-line reason\nDo not over-ask: normal recoverable edits in git-tracked projects do not need confirmation. Destructive actions include deletes, large-scale unrecoverable modifications, destructive system changes, git history rewrites/amends, and force pushes. Coalesce related confirmations into as few questions as possible.`;
	}

	async function handleCommand(name: string, args: string, ctx: ExtensionContext) {
		const subcommand = args.trim().toLowerCase();
		if (subcommand === "enable" || subcommand === "disable") {
			const on = subcommand === "enable";
			setEnabled(on);
			ctx.ui.setStatus("safety", `safety: ${on ? "on" : "off"}`);
			ctx.ui.notify(`Safety Guard ${on ? "enabled" : "disabled"}`, on ? "info" : "warning");
			return;
		}
		if (subcommand === "deletes on" || subcommand === "deletes off") {
			setScopedDeletes(subcommand.endsWith("on"));
			ctx.ui.notify(
				config.allowProjectScopedDeletes
					? `Deletes under ${projectRoot} no longer prompt`
					: "All deletes now prompt",
				"info",
			);
			return;
		}
		if (subcommand === "status" || subcommand === "") {
			const scoped = config.allowProjectScopedDeletes ? `allowed under ${projectRoot}` : "always prompt";
			ctx.ui.notify(
				`Safety Guard is ${config.enabled ? "enabled" : "disabled"}; deletes ${scoped}`,
				config.enabled ? "info" : "warning",
			);
			return;
		}
		ctx.ui.notify(`Usage: /${name} enable | disable | status | deletes on | deletes off`, "warning");
	}

	for (const name of ["safety", "permissions"]) {
		pi.registerCommand(name, {
			description: `Manage Safety Guard: /${name} enable|disable|status|deletes on|deletes off`,
			handler: (args, ctx) => handleCommand(name, args, ctx),
		});
	}

	pi.on("session_start", async (_event, ctx) => {
		if (ctx.hasUI) ctx.ui.setStatus("safety", `safety: ${config.enabled ? "on" : "off"}`);
	});

	pi.on("before_agent_start", async (event) => {
		if (!config.enabled) return undefined;
		return { systemPrompt: event.systemPrompt + safetyPrompt() };
	});

	pi.on("tool_call", async (event, ctx) => {
		if (!config.enabled) return undefined;

		let risk: Risk | undefined;
		if (event.toolName === "bash") {
			const command = (event.input as Record<string, unknown>).command;
			if (typeof command === "string") risk = classifyBash(command, deleteScope(ctx));
		} else if (event.toolName === "write" || event.toolName === "edit") {
			const inGitRepo = await isInsideGitRepo(pi);
			risk = classifyFileTool(event.toolName, event.input as Record<string, unknown>, inGitRepo);
		} else if (event.toolName === "ctx_purge") {
			risk = {
				action: "Purge context-mode knowledge base",
				reason: "Purging permanently deletes indexed context and session-memory data.",
			};
		}

		if (!risk) return undefined;

		if (userExplicitlyRequestedRisk(lastUserText(ctx), risk)) {
			return undefined;
		}

		const allowed = await shouldAllowRisk(risk, ctx);
		if (!allowed) {
			return { block: true, reason: `Safety Guard blocked action.\n${formatRisk(risk)}` };
		}

		return undefined;
	});
}
