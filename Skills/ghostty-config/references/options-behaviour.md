# Ghostty Options: Behaviour & Platform

Lookup catalogue for options controlling what Ghostty does: shell, clipboard, input, notifications, app lifecycle, and platform-specific settings. Fonts, colours, window geometry and the quick terminal live in `options-appearance.md`.

**Format:** `option-name` - Type - Default - Description. Valid values and platform notes where applicable.

## Contents

- Command & Shell
- Shell Integration: features, what it enables, manual setup
- Scrollback & Clipboard
- Links & Images
- Keybindings & Input Remapping
- Mouse & Input
- Bell
- Notifications
- Application
- macOS Platform: Window & Titlebar, Input, Security, Icon, Behaviour
- GTK/Linux Platform: Appearance, Custom Styling, Rendering, Linux System
- Terminal Behaviour
- Miscellaneous
- Duration Format Reference

---

## Command & Shell

| Option                          | Type                | Default             | Description                                                                              |
|---------------------------------|---------------------|---------------------|------------------------------------------------------------------------------------------|
| `command`                       | String              | SHELL env or passwd | Command to run. Prefixes: `direct:` (skip shell), `shell:` (force shell)                 |
| `initial-command`               | String              | null                | Command for first terminal only. CLI: `-e` flag                                          |
| `env`                           | String (repeatable) | null                | Format: `KEY=VALUE`. Reset: `env =`. Remove: `env = key=`                                |
| `input`                         | String (repeatable) | null                | Startup input. Format: `raw:string` or `path:filepath`                                   |
| `wait-after-command`            | Boolean             | `false`             | Keep terminal open after command exits                                                   |
| `abnormal-command-exit-runtime` | Duration            | null                | Threshold for "abnormal" exit detection (e.g., `2s`, `5000ms`)                           |
| `shell-integration`             | String              | `detect`            | Values: `none`, `detect`, `bash`, `fish`, `zsh`, `elvish`                                |
| `shell-integration-features`    | String              | null                | Features: `cursor`, `sudo`, `title`, `ssh-env`, `ssh-terminfo`. Prefix `no-` to disable |
| `term`                          | String              | null                | TERM environment variable value (e.g., `xterm-256color`, `xterm-ghostty`)                |

---

## Shell Integration

Auto-injected for **bash**, **zsh**, **fish**, **elvish**.

```
shell-integration = detect            # Default - auto-detect shell
shell-integration = none              # Disable auto-injection
shell-integration-features = cursor,sudo,title
shell-integration-features = no-cursor  # Disable one feature
```

| Feature        | Description                   |
|----------------|-------------------------------|
| `cursor`       | Blinking bar at prompt        |
| `sudo`         | Preserve terminfo with sudo   |
| `title`        | Set window title from shell   |
| `ssh-env`      | SSH environment compatibility |
| `ssh-terminfo` | Auto terminfo on remote hosts |

Enables: smart close (no confirm at prompt), new terminals inherit the previous working directory, prompt resizing via redraw, Ctrl/Cmd+triple-click selects command output, `jump_to_prompt`, Alt/Option+click cursor repositioning.

### Manual setup (when auto-injection fails)

Bash (top of `~/.bashrc`):

```bash
if [ -n "${GHOSTTY_RESOURCES_DIR}" ]; then
    builtin source "${GHOSTTY_RESOURCES_DIR}/shell-integration/bash/ghostty.bash"
fi
```

Zsh: `source ${GHOSTTY_RESOURCES_DIR}/shell-integration/zsh/ghostty-integration`

Fish: `source "$GHOSTTY_RESOURCES_DIR"/shell-integration/fish/vendor_conf.d/ghostty-shell-integration.fish`

macOS `/bin/bash` has no auto-injection: install Bash via Homebrew or source the script manually.

---

## Scrollback & Clipboard

| Option                           | Type                | Default          | Description                                                        |
|----------------------------------|---------------------|------------------|--------------------------------------------------------------------|
| `scrollback-limit`               | Integer (bytes)     | System dependent | Scrollback buffer size                                             |
| `clipboard-read`                 | String              | `ask`            | Values: `ask`, `allow`, `deny`                                     |
| `clipboard-write`                | String              | `allow`          | Values: `ask`, `allow`, `deny`                                     |
| `clipboard-trim-trailing-spaces` | Boolean             | `false`          | Trim whitespace from copied text                                   |
| `clipboard-paste-protection`     | Boolean             | `true`           | Confirm before pasting text with newlines                          |
| `clipboard-paste-bracketed-safe` | Boolean             | `true`           | Consider bracketed pastes safe                                     |
| `copy-on-select`                 | Boolean/String      | `true`           | Values: `true` (selection clipboard), `false`, `clipboard` (both)  |
| `clipboard-codepoint-map`        | String (repeatable) | null             | Map codepoints on copy. Format: `U+XXXX=U+YYYY` or `U+XXXX=text` |

---

## Links & Images

| Option                | Type                | Default | Description                                                      |
|-----------------------|---------------------|---------|------------------------------------------------------------------|
| `link-url`            | Boolean             | `true`  | Enable URL matching on hover                                     |
| `link-previews`       | String/Boolean      | `true`  | Values: `true`, `false`, `osc8`                                  |
| `link`                | String (repeatable) | null    | Custom regex link pattern. Format: `regex:PATTERN action:ACTION` |
| `image-storage-limit` | Integer (bytes)     | 320MB   | Kitty image protocol storage per screen                          |

---

## Keybindings & Input Remapping

| Option      | Type                | Default | Description                                                                                        |
|-------------|---------------------|---------|----------------------------------------------------------------------------------------------------|
| `keybind`   | String (repeatable) | null    | Key binding. Trigger and prefix syntax in SKILL.md; actions in `keybindings.md`             |
| `key-remap` | String (repeatable) | null    | Remap modifier keys. Format: `source=target` (e.g., `left_ctrl=left_alt`, `caps_lock=left_ctrl`)  |

---

## Mouse & Input

| Option                    | Type                | Default                | Description                                                                      |
|---------------------------|---------------------|------------------------|----------------------------------------------------------------------------------|
| `cursor-click-to-move`    | Boolean             | `false`                | Alt/Option+click repositions cursor at prompt                                    |
| `mouse-hide-while-typing` | Boolean             | `false`                | Hide mouse when typing                                                           |
| `mouse-shift-capture`     | String/Boolean      | `false`                | Values: `true`, `false`, `always`, `never`                                       |
| `mouse-scroll-multiplier` | Number (0.01-10000) | 3                      | Mouse wheel scroll distance                                                      |
| `mouse-reporting`         | Boolean             | null                   | Report mouse events to terminal apps. Toggle with `toggle_mouse_reporting` keybind |
| `scroll-to-bottom`        | String              | `keystroke, no-output` | Values: `keystroke`, `output`. Prefix `no-` to disable                           |
| `right-click-action`      | String              | `context-menu`         | Values: `context-menu`, `paste`, `copy`, `copy-or-paste`, `ignore`               |
| `click-repeat-interval`   | Integer (ms)        | Platform specific      | Multi-click detection interval                                                   |

---

## Bell

| Option              | Type                | Default | Description                                                                                        |
|---------------------|---------------------|---------|----------------------------------------------------------------------------------------------------|
| `bell-features`     | String (repeatable) | null    | Bell features. Values: `audio`, `system`, `attention`, `title`, `border`. Prefix `no-` to disable |
| `bell-audio-path`   | Path                | null    | Path to audio file for bell sound                                                                  |
| `bell-audio-volume` | Number (0.0-1.0)    | null    | Bell audio volume relative to system volume                                                        |

---

## Notifications

| Option                            | Type     | Default | Description                                                                   |
|-----------------------------------|----------|---------|-------------------------------------------------------------------------------|
| `desktop-notifications`           | Boolean  | null    | Whether to enable desktop notifications                                       |
| `app-notifications`               | String   | null    | App notifications to enable (e.g., `clipboard-copy`, `no-clipboard-copy`)     |
| `notify-on-command-finish`        | String   | null    | Values: `never`, `unfocused`, `always`. Requires shell integration or OSC 133 |
| `notify-on-command-finish-action` | String   | null    | How to notify. Comma-separated. Values: `bell`, `notify`. Prefix `no-` to disable |
| `notify-on-command-finish-after`  | Duration | null    | Minimum command runtime before notification (e.g., `5s`, `30s`)               |

---

## Application

| Option                                | Type           | Default            | Description                                            |
|---------------------------------------|----------------|--------------------|--------------------------------------------------------|
| `confirm-close-surface`               | String/Boolean | `true`             | Values: `true`, `false`, `always`                      |
| `quit-after-last-window-closed`       | Boolean        | Platform dependent | Exit when last window closes                           |
| `quit-after-last-window-closed-delay` | Duration       | unset              | Delay before quitting. Min: 1s. **Linux only**         |
| `initial-window`                      | Boolean        | `true`             | Create window on launch                                |
| `undo-timeout`                        | Duration       | 5s                 | Undo availability duration. 0 disables. **macOS only** |
| `auto-update`                         | String         | null               | Values: `off`, `check`, `download`                     |
| `auto-update-channel`                 | String         | null               | Values: `stable`, `tip`                                |

---

## macOS Platform

### Window & Titlebar

| Option                        | Type    | Default | Description                                                     |
|-------------------------------|---------|---------|---------------------------------------------------------------- |
| `macos-titlebar-style`        | String  | `auto`  | Values: `auto`, `hidden`, `tabs`                                |
| `macos-titlebar-proxy-icon`   | String  | null    | Values: `visible`, `hidden`                                     |
| `macos-window-buttons`        | String  | null    | Traffic light buttons visibility. Values: `visible`, `hidden`   |
| `macos-window-shadow`         | Boolean | null    | Whether to show window shadow                                   |
| `macos-non-native-fullscreen` | String  | null    | Values: `true`, `false`, `visible-menu`, `padded-notch`         |
| `macos-hidden`                | String  | null    | Hide app from dock and app switcher. Values: `never`, `always`  |

### Input

| Option                | Type   | Default | Description                                                              |
|-----------------------|--------|---------|--------------------------------------------------------------------------|
| `macos-option-as-alt` | String | null    | Treat option key as alt. Values: `true`, `false`, `left`, `right`        |
| `macos-shortcuts`     | String | null    | Allow macOS Shortcuts to control Ghostty. Values: `ask`, `allow`, `deny` |

### Security

| Option                          | Type    | Default | Description                  |
|---------------------------------|---------|---------|------------------------------|
| `macos-auto-secure-input`       | Boolean | null    | Auto-enable secure input     |
| `macos-secure-input-indication` | Boolean | null    | Show secure input indication |

### Icon

| Option                    | Type   | Default | Description                                                                                                                      |
|---------------------------|--------|---------|----------------------------------------------------------------------------------------------------------------------------------|
| `macos-icon`              | String | null    | Values: `official`, `blueprint`, `chalkboard`, `microchip`, `glass`, `holographic`, `paper`, `retro`, `xray`, `custom`, `custom-style` |
| `macos-icon-frame`        | String | null    | Frame material. Values: `aluminum`, `beige`, `plastic`, `chrome`                                                                 |
| `macos-icon-ghost-color`  | Colour | null    | Ghost colour for custom icon                                                                                                     |
| `macos-icon-screen-color` | Colour | null    | Screen colour for custom icon                                                                                                    |
| `macos-custom-icon`       | Path   | null    | Path to custom app icon (PNG, JPEG, or ICNS)                                                                                     |

### Behaviour

| Option                     | Type   | Default | Description                                                   |
|----------------------------|--------|---------|---------------------------------------------------------------|
| `macos-dock-drop-behavior` | String | null    | Dock file/folder drop action. Values: `new-tab`, `new-window` |

---

## GTK/Linux Platform

### GTK Appearance

| Option                             | Type    | Default | Description                                                       |
|------------------------------------|---------|---------|-------------------------------------------------------------------|
| `gtk-adwaita`                      | Boolean | null    | Whether to use Adwaita theme                                      |
| `gtk-titlebar`                     | Boolean | null    | Whether to show titlebar                                          |
| `gtk-titlebar-style`               | String  | null    | Values: `native`, `tabs` (merges tab bar into titlebar)           |
| `gtk-titlebar-hide-when-maximized` | Boolean | null    | Hide titlebar when maximised                                      |
| `gtk-toolbar-style`                | String  | null    | Toolbar bar appearance. Values: `flat`, `raised`, `raised-border` |
| `gtk-tabs-location`               | String  | null    | Tab bar location. Values: `top`, `bottom`                         |
| `gtk-wide-tabs`                    | Boolean | null    | Whether to use wide tabs                                          |
| `gtk-single-instance`              | Boolean | `true`  | Single application instance                                       |
| `adw-toolbar-style`                | String  | null    | Adwaita toolbar style. Values: `flat`, `raised`, `raised-border`  |
| `language`                         | String  | null    | Override GUI language (e.g., `de_DE.UTF-8`). Cannot be reloaded at runtime |

### GTK Custom Styling

| Option           | Type | Default | Description             |
|------------------|------|---------|-------------------------|
| `gtk-custom-css` | Path | null    | Path to custom CSS file |

### GTK Rendering

| Option             | Type    | Default | Description                        |
|--------------------|---------|---------|------------------------------------|
| `gtk-gsk-renderer` | String  | null    | GSK renderer (e.g., `gl`, `cairo`) |
| `gtk-opengl-debug` | Boolean | null    | Enable OpenGL debugging            |

### Linux System

| Option                         | Type    | Default | Description                                                      |
|--------------------------------|---------|---------|------------------------------------------------------------------|
| `linux-cgroup`                 | String  | null    | Linux cgroup configuration (e.g., `v2`, `v1`)                    |
| `linux-cgroup-hard-fail`       | Boolean | null    | Hard fail on cgroup errors                                       |
| `linux-cgroup-memory-limit`    | Number  | null    | Cgroup memory limit in bytes                                     |
| `linux-cgroup-processes-limit` | Number  | null    | Cgroup process limit                                             |
| `async-backend`                | String  | null    | Low-level async IO backend. Values: `auto`, `epoll`, `io_uring` |

---

## Terminal Behaviour

| Option                    | Type    | Default | Description                                               |
|---------------------------|---------|---------|-----------------------------------------------------------|
| `enquiry-response`        | String  | null    | Response to ENQ character                                 |
| `osc-color-report-format` | String  | null    | OSC colour report format. Values: `8-bit`, `16-bit`       |
| `vt-kam-allowed`          | Boolean | null    | Whether VT KAM (keyboard action mode) sequence is allowed |

---

## Miscellaneous

| Option                  | Type                | Default | Description                                           |
|-------------------------|---------------------|---------|-------------------------------------------------------|
| `config-file`           | String (repeatable) | null    | Additional config files. Prefix `?` for optional      |
| `config-default-files`  | Boolean             | `true`  | Load default config paths. **CLI only**               |
| `title-report`          | Boolean             | `false` | Enable title reporting (CSI 21 t). Security risk      |
| `command-palette-entry` | String (repeatable) | null    | Format: `title:text,action:action[,description:text]` |

---

## Duration Format Reference

Colour value formats: see `options-appearance.md`.

Duration options accept combinations of:
- `y` (years), `d` (days), `h` (hours), `m` (minutes)
- `s` (seconds), `ms` (milliseconds), `us`/`µs` (microseconds), `ns` (nanoseconds)

Examples: `1h30m`, `45s`, `100ms`, `750ms`
