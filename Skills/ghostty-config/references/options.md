# Ghostty Configuration Options Reference

Complete reference of Ghostty configuration options organised by category.

**Format:** `option-name` - Type - Default - Description. Valid values and platform notes where applicable.

---

## Font Options

### Font Family

| Option                    | Type                | Default          | Description                        |
|---------------------------|---------------------|------------------|------------------------------------|
| `font-family`             | String (repeatable) | System dependent | Primary font with fallback support |
| `font-family-bold`        | String (repeatable) | Derived          | Bold variant                       |
| `font-family-italic`      | String (repeatable) | Derived          | Italic variant                     |
| `font-family-bold-italic` | String (repeatable) | Derived          | Bold-italic variant                |

Use `ghostty +list-fonts` to see available fonts.

### Font Style

| Option                   | Type           | Default | Description                                                       |
|--------------------------|----------------|---------|-------------------------------------------------------------------|
| `font-style`             | String/Boolean | null    | Named style (e.g., "Heavy") or `false` to disable                 |
| `font-style-bold`        | String/Boolean | null    | Bold style override                                               |
| `font-style-italic`      | String/Boolean | null    | Italic style override                                             |
| `font-style-bold-italic` | String/Boolean | null    | Bold-italic style override                                        |
| `font-synthetic-style`   | String         | `true`  | Values: `true`, `false`, `no-bold`, `no-italic`, `no-bold-italic` |

### Font Size & Features

| Option                  | Type                | Default          | Description                                               |
|-------------------------|---------------------|------------------|-----------------------------------------------------------|
| `font-size`             | Number              | System dependent | Font size in points (non-integer allowed, e.g., `13.5`)   |
| `font-feature`          | String (repeatable) | null             | OpenType features: `feat`, `+feat`, `-feat`, `feat=value` |
| `font-thicken`          | Boolean             | `false`          | Draw thicker strokes. **macOS only**                      |
| `font-thicken-strength` | Integer (0-255)     | null             | Thickening intensity. **macOS only**                      |
| `font-shaping-break`    | String              | `cursor`         | Where to break font shaping                               |

### Variable Fonts

| Option                       | Type                | Default | Description                             |
|------------------------------|---------------------|---------|-----------------------------------------|
| `font-variation`             | String (repeatable) | null    | Format: `axis=value` (e.g., `wght=600`) |
| `font-variation-bold`        | String (repeatable) | null    | Bold variant axes                       |
| `font-variation-italic`      | String (repeatable) | null    | Italic variant axes                     |
| `font-variation-bold-italic` | String (repeatable) | null    | Bold-italic variant axes                |

Common axes: `wght` (weight), `slnt` (slant), `ital`, `opsz`, `wdth`, `GRAD`

### Font Mapping

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `font-codepoint-map` | String (repeatable) | null | Format: `U+ABCD=fontname` or `U+ABCD-U+DEFG=fontname` |

### FreeType (Linux Only)

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `freetype-load-flags` | String | Per-flag defaults | Values: `hinting`, `force-autohint`, `monochrome`, `autohint`, prefix with `no-` |

---

## Colour & Display

### Basic Colours

| Option       | Type                | Default         | Description                                                 |
|--------------|---------------------|-----------------|-------------------------------------------------------------|
| `background` | Colour              | Theme dependent | Format: `#RRGGBB`, `RRGGBB`, or X11 colour name             |
| `foreground` | Colour              | Theme dependent | Format: `#RRGGBB`, `RRGGBB`, or X11 colour name             |
| `theme`      | String              | null            | Theme name or `light:theme1,dark:theme2` for mode switching |
| `palette`    | String (repeatable) | null            | Format: `N=COLOR` (N: 0-255)                                |

### Transparency & Images

| Option                      | Type             | Default            | Description                                                                                                                            |
|-----------------------------|------------------|--------------------|----------------------------------------------------------------------------------------------------------------------------------------|
| `background-opacity`        | Number (0.0-1.0) | 1.0                | Background transparency. macOS requires restart                                                                                        |
| `background-opacity-cells`  | Boolean          | `false`            | Apply opacity to cells with explicit backgrounds                                                                                       |
| `background-blur`           | Integer/Boolean  | `false`            | Blur intensity. `true`=20. **macOS, KDE Plasma only**                                                                                  |
| `background-image`          | Path             | null               | PNG or JPEG                                                                                                                            |
| `background-image-opacity`  | Number           | 1.0                | Image opacity                                                                                                                          |
| `background-image-position` | String           | `center`           | Values: `top-left`, `top-center`, `top-right`, `center-left`, `center`, `center-right`, `bottom-left`, `bottom-center`, `bottom-right` |
| `background-image-fit`      | String           | `contain`          | Values: `contain`, `cover`, `stretch`, `none`                                                                                          |
| `background-image-repeat`   | Boolean          | `false`            | Tile background image                                                                                                                  |
| `alpha-blending`            | String           | Platform dependent | Values: `native`, `linear`, `linear-corrected`                                                                                         |

### Cursor

| Option               | Type             | Default | Description                                                  |
|----------------------|------------------|---------|--------------------------------------------------------------|
| `cursor-color`       | Colour           | null    | Cursor colour. Special: `cell-foreground`, `cell-background` |
| `cursor-text`        | Colour           | null    | Text under cursor colour                                     |
| `cursor-opacity`     | Number (0.0-1.0) | 1.0     | Cursor transparency                                          |
| `cursor-style`       | String           | null    | Values: `block`, `bar`, `underline`, `block_hollow`          |
| `cursor-style-blink` | Boolean/null     | null    | Whether cursor blinks (null respects DEC Mode 12)            |

### Selection

| Option                      | Type    | Default | Description                 |
|-----------------------------|---------|---------|-----------------------------|
| `selection-foreground`      | Colour  | null    | Selected text foreground    |
| `selection-background`      | Colour  | null    | Selected text background    |
| `selection-clear-on-typing` | Boolean | `true`  | Clear selection when typing |
| `selection-clear-on-copy`   | Boolean | `false` | Clear selection after copy  |

### Contrast & Splits

| Option                    | Type              | Default          | Description                         |
|---------------------------|-------------------|------------------|-------------------------------------|
| `minimum-contrast`        | Number (1-21)     | null             | WCAG contrast ratio                 |
| `split-divider-color`     | Colour            | null             | Split pane divider colour |
| `unfocused-split-opacity` | Number (0.15-1.0) | System dependent | Unfocused split opacity             |
| `unfocused-split-fill`    | Colour            | Background       | Unfocused split overlay colour      |

---

## Cell Adjustments

All accept Integer or Percentage (e.g., `20%`, `-15%`).

| Option                           | Default             | Description                            |
|----------------------------------|---------------------|----------------------------------------|
| `adjust-cell-width`              | 0                   | Cell width adjustment                  |
| `adjust-cell-height`             | 0                   | Cell height (font centred vertically) |
| `adjust-font-baseline`           | 0                   | Baseline position (positive=UP)        |
| `adjust-underline-position`      | 0                   | Underline position (positive=DOWN)     |
| `adjust-underline-thickness`     | 0                   | Underline thickness                    |
| `adjust-strikethrough-position`  | 0                   | Strikethrough position                 |
| `adjust-strikethrough-thickness` | 0                   | Strikethrough thickness                |
| `adjust-overline-position`       | 0                   | Overline position                      |
| `adjust-overline-thickness`      | 0                   | Overline thickness                     |
| `adjust-cursor-thickness`        | 0                   | Bar/hollow cursor thickness            |
| `adjust-cursor-height`           | 0                   | Cursor height                          |
| `adjust-box-thickness`           | 0                   | Box drawing character thickness        |
| `adjust-icon-height`             | 1.2x capital height | Nerd font icon height.                |

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `grapheme-width-method` | String | `unicode` | Values: `legacy`, `unicode` |

---

## Command & Shell

| Option                          | Type                | Default             | Description                                                                             |
|---------------------------------|---------------------|---------------------|-----------------------------------------------------------------------------------------|
| `command`                       | String              | SHELL env or passwd | Command to run. Prefixes: `direct:` (skip shell), `shell:` (force shell)                |
| `initial-command`               | String              | null                | Command for first terminal only. CLI: `-e` flag                                         |
| `env`                           | String (repeatable) | null                | Format: `KEY=VALUE`. Reset: `env =`. Remove: `env = key=`                               |
| `input`                         | String (repeatable) | null                | Startup input. Format: `raw:string` or `path:filepath`                                  |
| `wait-after-command`            | Boolean             | `false`             | Keep terminal open after command exits                                                  |
| `abnormal-command-exit-runtime` | Integer (ms)        | null                | Threshold for "abnormal" exit detection                                                 |
| `shell-integration`             | String              | `detect`            | Values: `none`, `detect`, `bash`, `fish`, `zsh`, `elvish`                               |
| `shell-integration-features`    | String              | null                | Features: `cursor`, `sudo`, `title`, `ssh-env`, `ssh-terminfo`. Prefix `no-` to disable |

---

## Scrollback & Clipboard

| Option                           | Type            | Default          | Description                                                       |
|----------------------------------|-----------------|------------------|-------------------------------------------------------------------|
| `scrollback-limit`               | Integer (bytes) | System dependent | Scrollback buffer size                                            |
| `clipboard-read`                 | String          | `ask`            | Values: `ask`, `allow`, `deny`                                    |
| `clipboard-write`                | String          | `allow`          | Values: `ask`, `allow`, `deny`                                    |
| `clipboard-trim-trailing-spaces` | Boolean         | `false`          | Trim whitespace from copied text                                  |
| `clipboard-paste-protection`     | Boolean         | `true`           | Confirm before pasting text with newlines                         |
| `clipboard-paste-bracketed-safe` | Boolean         | `true`           | Consider bracketed pastes safe                                    |
| `copy-on-select`                 | Boolean/String  | `true`           | Values: `true` (selection clipboard), `false`, `clipboard` (both) |

---

## Links & Images

| Option                | Type            | Default | Description                             |
|-----------------------|-----------------|---------|-----------------------------------------|
| `link-url`            | Boolean         | `true`  | Enable URL matching on hover            |
| `link-previews`       | String/Boolean  | `true`  | Values: `true`, `false`, `osc8`       |
| `image-storage-limit` | Integer (bytes) | 320MB   | Kitty image protocol storage per screen |

---

## Mouse & Input

| Option                    | Type                | Default                | Description                                                        |
|---------------------------|---------------------|------------------------|--------------------------------------------------------------------|
| `cursor-click-to-move`    | Boolean             | `false`                | Alt/Option+click repositions cursor at prompt                      |
| `mouse-hide-while-typing` | Boolean             | `false`                | Hide mouse when typing                                             |
| `mouse-shift-capture`     | String/Boolean      | `false`                | Values: `true`, `false`, `always`, `never`                         |
| `mouse-scroll-multiplier` | Number (0.01-10000) | 3                      | Mouse wheel scroll distance                                      |
| `scroll-to-bottom`        | String              | `keystroke, no-output` | Values: `keystroke`, `output`. Prefix `no-` to disable             |
| `right-click-action`      | String              | `context-menu`         | Values: `context-menu`, `paste`, `copy`, `copy-or-paste`, `ignore` |
| `click-repeat-interval`   | Integer (ms)        | Platform specific      | Multi-click detection interval                                     |

---

## Window

### Size & Position

| Option              | Type             | Default | Description                                        |
|---------------------|------------------|---------|----------------------------------------------------|
| `window-width`      | Integer (cells)  | null    | Initial width (min 10). Both width/height required |
| `window-height`     | Integer (cells)  | null    | Initial height (min 4). Both width/height required |
| `window-position-x` | Integer (pixels) | null    | Initial X position. **macOS only**                 |
| `window-position-y` | Integer (pixels) | null    | Initial Y position. **macOS only**                 |

### Padding

| Option                   | Type    | Default      | Description                                              |
|--------------------------|---------|--------------|----------------------------------------------------------|
| `window-padding-x`       | Integer | 0            | Horizontal padding. Format: single value or `left,right` |
| `window-padding-y`       | Integer | 0            | Vertical padding. Format: single value or `top,bottom`   |
| `window-padding-balance` | Boolean | `false`      | Balance extra padding from cell alignment                |
| `window-padding-color`   | String  | `background` | Values: `background`, `extend`, `extend-always`          |

### Appearance

| Option                       | Type           | Default        | Description                                                          |
|------------------------------|----------------|----------------|----------------------------------------------------------------------|
| `window-decoration`          | String/Boolean | `auto`         | Values: `none`, `auto`, `client` (1.1.0+), `server` (1.1.0+)         |
| `window-theme`               | String         | `auto`         | Values: `auto`, `system`, `light`, `dark`, `ghostty`                 |
| `window-colorspace`          | String         | `srgb`         | Values: `srgb`, `display-p3`. **macOS only**                         |
| `window-vsync`               | Boolean        | `true`         | Sync with screen refresh. **macOS only**                             |
| `window-title-font-family`   | String         | System default | Title font. **GTK only**. (1.1.0+)                                   |
| `window-subtitle`            | String/Boolean | null           | Values: `false`, `working-directory`. **GTK only**. (1.1.0+)         |
| `window-titlebar-background` | Colour         | null           | Titlebar background. **GTK only**, requires `window-theme = ghostty` |
| `window-titlebar-foreground` | Colour         | null           | Titlebar foreground. **GTK only**, requires `window-theme = ghostty` |

### Behaviour

| Option                             | Type    | Default                 | Description                                          |
|------------------------------------|---------|-------------------------|------------------------------------------------------|
| `window-inherit-working-directory` | Boolean | `true`                  | New windows inherit working directory                |
| `window-inherit-font-size`         | Boolean | `false`                 | New windows inherit font size                        |
| `window-save-state`                | String  | `default`               | Values: `default`, `never`, `always`. **macOS only** |
| `window-step-resize`               | Boolean | `false`                 | Resize in cell increments. **macOS only**            |
| `maximize`                         | Boolean | `false`                 | Start maximized. (1.1.0+)                            |
| `fullscreen`                       | Boolean | `false`                 | Start fullscreen                                     |
| `title`                            | String  | null                    | Force window title                                   |
| `class`                            | String  | `com.mitchellh.ghostty` | Application class (WM_CLASS). **GTK only**           |
| `x11-instance-name`                | String  | `ghostty`               | WM_CLASS instance. **X11 only**                      |
| `working-directory`                | String  | `inherit`               | Values: absolute path, `home`, `inherit`             |
| `focus-follows-mouse`              | Boolean | `false`                 | Mouse movement selects splits                        |

### Tabs

| Option                    | Type   | Default   | Description                                      |
|---------------------------|--------|-----------|--------------------------------------------------|
| `window-new-tab-position` | String | `current` | Values: `current`, `end`                         |
| `window-show-tab-bar`     | String | `auto`    | Values: `always`), `auto`, `never`. **GTK only** |

---

## Resize Overlay

| Option                    | Type     | Default       | Description                                                                                             |
|---------------------------|----------|---------------|---------------------------------------------------------------------------------------------------------|
| `resize-overlay`          | String   | `after-first` | Values: `always`, `never`, `after-first`                                                                |
| `resize-overlay-position` | String   | `center`      | Values: `center`, `top-left`, `top-center`, `top-right`, `bottom-left`, `bottom-center`, `bottom-right` |
| `resize-overlay-duration` | Duration | 750ms         | Format: `1h30m`, `45s`, `100ms`                                                                         |

---

## Quick Terminal

| Option                                  | Type             | Default            | Description                                                            |
|-----------------------------------------|------------------|--------------------|------------------------------------------------------------------------|
| `quick-terminal-position`               | String           | null               | Values: `top`, `bottom`, `left`, `right`, `center`                     |
| `quick-terminal-size`                   | String           | null               | Format: `50%` or `500px`, or `size1,size2`                             |
| `quick-terminal-screen`                 | String           | `main`             | Values: `main`, `mouse`, `macos-menu-bar`. **macOS only**              |
| `quick-terminal-animation-duration`     | Number (seconds) | System dependent   | Animation duration. **macOS only**                                     |
| `quick-terminal-autohide`               | Boolean          | Platform dependent | Auto-hide on focus loss                                                |
| `quick-terminal-space-behavior`         | String           | `move`             | Values: `move`, `remain`. **macOS only**.                              |
| `quick-terminal-keyboard-interactivity` | String           | `on-demand`        | Values: `none`, `on-demand`, `exclusive`. **Linux Wayland only**       |
| `gtk-quick-terminal-layer`              | String           | `top`              | Values: `overlay`, `top`, `bottom`, `background`. **GTK Wayland only** |
| `gtk-quick-terminal-namespace`          | String           | null               | Window namespace. **GTK Wayland only**                                 |

---

## Application

| Option                                | Type           | Default            | Description                                            |
|---------------------------------------|----------------|--------------------|--------------------------------------------------------|
| `confirm-close-surface`               | String/Boolean | `true`             | Values: `true`, `false`, `always`                      |
| `quit-after-last-window-closed`       | Boolean        | Platform dependent | Exit when last window closes                           |
| `quit-after-last-window-closed-delay` | Duration       | unset              | Delay before quitting. Min: 1s. **Linux only**         |
| `initial-window`                      | Boolean        | `true`             | Create window on launch                                |
| `undo-timeout`                        | Duration       | 5s                 | Undo availability duration. 0 disables. **macOS only** |

---

## Miscellaneous

| Option                  | Type                | Default | Description                                           |
|-------------------------|---------------------|---------|-------------------------------------------------------|
| `config-file`           | String (repeatable) | null    | Additional config files. Prefix `?` for optional      |
| `config-default-files`  | Boolean             | `true`  | Load default config paths. **CLI only**               |
| `title-report`          | Boolean             | `false` | Enable title reporting (CSI 21 t). Security risk.     |
| `macos-titlebar-style`  | String              | `auto`  | Values: `auto`, `hidden`, `tabs`. **macOS only**      |
| `gtk-single-instance`   | Boolean             | `true`  | Single application instance. **GTK only**             |
| `command-palette-entry` | String (repeatable) | null    | Format: `title:text,action:action[,description:text]` |

---

## Colour Format Reference

All colour options accept:
- `#RRGGBB` - Hex with hash
- `RRGGBB` - Hex without hash
- X11 colour names (e.g., `red`, `steelblue`, `coral`)
- Special values for cursor/selection: `cell-foreground`, `cell-background`)

## Duration Format Reference

Duration options accept combinations of:
- `y` (years), `d` (days), `h` (hours), `m` (minutes)
- `s` (seconds), `ms` (milliseconds), `us`/`µs` (microseconds), `ns` (nanoseconds)

Examples: `1h30m`, `45s`, `100ms`, `750ms`
