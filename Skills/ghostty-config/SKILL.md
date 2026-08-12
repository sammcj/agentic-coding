---
name: ghostty-config
description: Use when creating, editing or debugging Ghostty terminal configuration - config.ghostty files, config option names and their valid values, keybinds and key sequences, themes, fonts, shell integration, or `ghostty +` CLI actions. Covers macOS and Linux/GTK differences.
metadata:
  config_schema_last_updated: "2026-05-20" # Update when realigning the skill with the latest config schema JSON
---

# Ghostty Configuration

## Config File Locations

Config is optional; with no file Ghostty runs on its defaults. Since Ghostty 1.2.3 the file is named `config.ghostty`; extensionless `config` still loads for backwards compatibility.

- XDG (all platforms): `$XDG_CONFIG_HOME/ghostty/config.ghostty`, then `$XDG_CONFIG_HOME/ghostty/config`. `XDG_CONFIG_HOME` defaults to `~/.config`.
- macOS also: `~/Library/Application Support/com.mitchellh.ghostty/config.ghostty`, then `.../config`.

Every matching file loads, later files overriding earlier ones. Within a location `config.ghostty` loads before `config`. On macOS the macOS-path files load after the XDG ones, so macOS paths win on conflict.

## Syntax

```
# Comments start with #
background = 282c34
font-family = "JetBrains Mono"
keybind = ctrl+z=close_surface
font-family =                     # Empty value resets to default
```

- Keys are case-sensitive: use lowercase.
- Repeatable keys (`font-family`, `keybind`, `palette`, `env`, `link`) accumulate across lines.
- Every config key doubles as a CLI flag: `ghostty --background=282c34 --font-size=14`.

## Includes

```
config-file = themes/dark.conf
config-file = ?local.conf       # ? prefix = optional, no error if missing
```

`config-file` directives are processed at the end of the containing file, so keys written after one still lose to the included file's values. Put overrides in the included file, or include first and keep the parent free of conflicting keys.

## Applying Changes

- Reload: `ctrl+shift+,` (Linux), `cmd+shift+,` (macOS). Some options need a restart; some apply only to newly created terminals.
- Validate after every edit: `ghostty +validate-config`.

## CLI Actions

`ghostty +<action>`; add `--help` for per-action help.

| Command                                 | Purpose                                       |
|-----------------------------------------|-----------------------------------------------|
| `ghostty +validate-config`              | Check the config for errors                   |
| `ghostty +show-config`                  | Show the effective configuration              |
| `ghostty +show-config --default --docs` | Show defaults with documentation              |
| `ghostty +edit-config`                  | Open the config in the default editor         |
| `ghostty +list-fonts`                   | Available fixed-width fonts                   |
| `ghostty +list-themes`                  | Available colour themes                       |
| `ghostty +list-colors`                  | Available X11 colour names                    |
| `ghostty +list-keybinds`                | Current keybinds (`--default` for defaults)   |
| `ghostty +list-actions`                 | All keybind actions                           |
| `ghostty +show-face`                    | Font face information                         |
| `ghostty +ssh-cache`                    | Manage the SSH terminfo cache                 |
| `ghostty +new-window`                   | Open a new window (Linux only)                |

On macOS the `ghostty` binary is a helper tool: launch the terminal with `open -na Ghostty.app`, passing flags as `open -na Ghostty.app --args --font-size=14`. Use `ghostty -e <command>` to run a command in a new terminal.

## Keybind Syntax

Format: `keybind = [prefix:]trigger=action[:param]`

Modifiers: `shift`, `ctrl`/`control`, `alt`/`opt`/`option`, `super`/`cmd`/`command`.

```
keybind = ctrl+shift+t=new_tab
keybind = super+backquote=toggle_quick_terminal
keybind = ctrl+a>n=new_window          # Sequence: press ctrl+a, release, press n
keybind = clear                        # Remove ALL keybinds, including defaults
keybind = ctrl+a=unbind                # Remove one binding
keybind = ctrl+a=ignore                # Ghostty and the terminal both ignore the key
```

- Physical keys use W3C codes (`KeyA`, `key_a`, `Digit1`, `BracketLeft`) and outrank unicode codepoints. Prefer them for non-US layouts.
- Sequences wait indefinitely for the next key.

| Prefix         | Effect                                                                                |
|----------------|---------------------------------------------------------------------------------------|
| `global:`      | System-wide (macOS: needs Accessibility permission; Linux: needs an XDG Desktop Portal) |
| `all:`         | Applies to all terminal surfaces                                                      |
| `unconsumed:`  | Passes the input through as well                                                      |
| `performable:` | Consumes the input only if the action succeeds                                        |

Prefixes combine: `global:unconsumed:ctrl+a=reload_config`. Sequences work with `unconsumed:`/`performable:` but not with `global:` or `all:`.

Ghostty 1.3+ adds modal key tables and in-terminal search actions - see `references/keybindings.md`.

## Gotchas

- Confirm an option's platform before recommending it: the reference tables carry platform markers, and an option gated to another platform silently does nothing.
- `theme` accepts mode switching: `theme = light:catppuccin-latte,dark:catppuccin-mocha`.
- Disable ligatures with `font-feature = -calt` plus `font-feature = -liga`.
- Prefer a theme name from `ghostty +list-themes` over hand-written colours when the user asks for a known theme.

## References

Load one when the task needs it - each is a lookup catalogue, not background reading:

- Naming or checking an option for fonts, colours and themes, cursor appearance, selection or search-match colours, transparency, background images, shaders, cell metrics, scrollbar, window geometry/padding/decoration/startup state, tabs, splits or the quick terminal -> `references/options-appearance.md`
- Naming or checking an option for shell and command startup, shell integration, clipboard, scrollback, mouse (including cursor click-to-move), modifier remapping via `key-remap`, bell, notifications, links, app lifecycle, or the `macos-*`, `gtk-*`, `adw-*` and `linux-*` prefixed families -> `references/options-behaviour.md`
- Naming a keybind action, its `:param` form, key tables or search actions -> `references/keybindings.md`

Platform-gated options sit with their domain, not in a platform bucket: `font-thicken` (macOS) and `window-vsync` (macOS) are in the appearance file. Only the prefixed families above live in the platform sections.

The current schema (including tip releases) is at https://raw.githubusercontent.com/sammcj/vscode-ghostty-config-syntax/refs/heads/main/schema/ghostty-config-syntax.schema.json - large, so query it programmatically rather than reading it whole.
