/**
 * Pi Welcome Header — themed startup chrome.
 *
 * Replaces Pi's built-in header so the logo, version, model, cwd, and usual
 * help text appear before Pi's native loaded resources listing.
 */

import path from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { VERSION } from "@earendil-works/pi-coding-agent";
import { truncateToWidth, visibleWidth } from "@earendil-works/pi-tui";

const LOGO = [
	"  ██████   ██",
	"  ██   ██  ██",
	"  ██████   ██",
	"  ██       ██",
];

function compactCwd(cwd: string): string {
	const home = process.env.HOME;
	if (home && cwd.startsWith(home)) return cwd.replace(home, "~");
	return cwd;
}

function projectName(cwd: string): string {
	return path.basename(cwd) || "session";
}

export default function (pi: ExtensionAPI) {
	pi.on("session_start", (_event, ctx) => {
		if (ctx.mode !== "tui") return;

		const dir = compactCwd(ctx.cwd ?? process.cwd());
		const user = process.env.USER || "user";
		const model = ctx.model?.id ?? "no model";

		ctx.ui.setHeader((_tui, theme) => ({
			render(width: number): string[] {
				const lines = [
					...LOGO.map((line) => line.replace(/█/g, theme.fg("accent", "█"))),
					"",
					`${theme.fg("accent", theme.bold("pi coding agent"))} ${theme.fg("dim", "·")} ${theme.fg("text", user)} ${theme.fg("dim", "·")} ${theme.fg("dim", projectName(dir))}`,
					`${theme.fg("dim", "version:")} ${theme.fg("text", `v${VERSION}`)}`,
					`${theme.fg("dim", "model:")} ${theme.fg("text", model)}`,
					`${theme.fg("dim", "dir:  ")} ${theme.fg("text", dir)}`,
					"",
					`${theme.fg("muted", "escape interrupt · ctrl+c/ctrl+d clear/exit · / commands · ! bash · ctrl+o more")}`,
					`${theme.fg("dim", "Press ctrl+o to show full startup help and loaded resources.")}`,
					"",
					`${theme.fg("dim", "Pi can explain its own features and look up its docs. Ask it how to use or extend Pi.")}`,
				];
				return lines.map((line) => visibleWidth(line) > width ? truncateToWidth(line, width) : line);
			},
			invalidate() {},
		}));
	});

	pi.on("session_shutdown", (_event, ctx) => {
		if (ctx.hasUI) ctx.ui.setHeader(undefined);
	});
}
