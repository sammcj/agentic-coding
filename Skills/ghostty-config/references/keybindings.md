# Ghostty Keybinding Actions Reference

Complete reference of keybinding actions available in Ghostty.

**Format:** `keybind = trigger=action` or `keybind = trigger=action:parameter`

---

## Meta Actions

| Action   | Description                                                              |
|----------|--------------------------------------------------------------------------|
| `ignore` | Prevents key processing by Ghostty and terminal (OS may still handle it) |
| `unbind` | Removes previously defined keybinding                                    |

```
keybind = ctrl+c=ignore          # Disable ctrl+c in Ghostty
keybind = ctrl+shift+c=unbind    # Remove default copy binding
```

---

## Terminal Output Actions

| Action       | Format                            | Description                             |
|--------------|-----------------------------------|-----------------------------------------|
| `csi`        | `csi:text`                        | Send CSI sequence without header        |
| `esc`        | `esc:text`                        | Send escape sequence                    |
| `text`       | `text:text`                       | Send string (Zig string literal syntax) |
| `cursor_key` | `cursor_key:app_text,normal_text` | Send data based on cursor key mode      |

```
keybind = ctrl+r=csi:0m                    # Reset text styling
keybind = ctrl+l=esc:c                     # Send ESC c (reset)
keybind = ctrl+shift+enter=text:\x1b[13;2u # Send modified enter
```

---

## Terminal Control Actions

| Action | Description |
|--------|-------------|
| `reset` | Restore terminal to initial state (like `reset` command) |
| `clear_screen` | Erase display and all scrollback history |

---

## Clipboard Actions

| Action                    | Description                            |
|---------------------------|----------------------------------------|
| `copy_to_clipboard`       | Copy selected text to system clipboard |
| `paste_from_clipboard`    | Insert system clipboard contents       |
| `paste_from_selection`    | Insert selection clipboard contents    |
| `copy_url_to_clipboard`   | Copy URL under cursor to clipboard     |
| `copy_title_to_clipboard` | Copy window title to clipboard         |

---

## Font Actions

| Action               | Format                      | Description                     |
|----------------------|-----------------------------|---------------------------------|
| `increase_font_size` | `increase_font_size:points` | Enlarge font (default: 1 point) |
| `decrease_font_size` | `decrease_font_size:points` | Reduce font (default: 1 point)  |
| `reset_font_size`    | -                           | Restore configured default      |
| `set_font_size`      | `set_font_size:points`      | Set exact font size             |

```
keybind = ctrl+plus=increase_font_size:2
keybind = ctrl+minus=decrease_font_size:2
keybind = ctrl+0=reset_font_size
keybind = ctrl+1=set_font_size:14
```

---

## Selection Actions

| Action             | Format                       | Description                |
|--------------------|------------------------------|----------------------------|
| `select_all`       | -                            | Highlight all visible text |
| `adjust_selection` | `adjust_selection:direction` | Modify existing selection  |

**Directions for `adjust_selection`:**
- `left`, `right`, `up`, `down`
- `page_up`, `page_down`
- `home`, `end`
- `beginning_of_line`, `end_of_line`

```
keybind = shift+left=adjust_selection:left
keybind = shift+end=adjust_selection:end
```

---

## Scrolling Actions

| Action                   | Format                            | Description                         |
|--------------------------|-----------------------------------|-------------------------------------|
| `scroll_to_top`          | -                                 | Move to scrollback beginning        |
| `scroll_to_bottom`       | -                                 | Move to scrollback end              |
| `scroll_to_selection`    | -                                 | Position viewport to show selection |
| `scroll_page_up`         | -                                 | Move up one page                    |
| `scroll_page_down`       | -                                 | Move down one page                  |
| `scroll_page_fractional` | `scroll_page_fractional:fraction` | Scroll by fraction (positive=down)  |
| `scroll_page_lines`      | `scroll_page_lines:count`         | Scroll by lines (positive=down)     |

```
keybind = shift+page_up=scroll_page_up
keybind = ctrl+up=scroll_page_lines:-3
keybind = ctrl+down=scroll_page_lines:3
keybind = ctrl+shift+up=scroll_page_fractional:-0.5
```

---

## Navigation Actions

| Action | Format | Description |
|--------|--------|-------------|
| `jump_to_prompt` | `jump_to_prompt:offset` | Navigate by shell prompts (requires shell integration) |

**Offset:** positive=forward, negative=backward

```
keybind = ctrl+shift+up=jump_to_prompt:-1     # Previous prompt
keybind = ctrl+shift+down=jump_to_prompt:1    # Next prompt
```

---

## File Export Actions

| Action | Format | Description |
|--------|--------|-------------|
| `write_scrollback_file` | `write_scrollback_file:action` | Export scrollback to temp file |
| `write_screen_file` | `write_screen_file:action` | Export visible screen to temp file |
| `write_selection_file` | `write_selection_file:action` | Export selection to temp file |

**Actions:** `copy` (path to clipboard), `paste` (path as terminal input), `open` (open in default app)

```
keybind = ctrl+shift+s=write_scrollback_file:open
keybind = ctrl+shift+e=write_selection_file:copy
```

---

## Window Actions

| Action | Description |
|--------|-------------|
| `new_window` | Open new terminal window |

---

## Tab Actions

| Action                 | Format            | Description                                   |
|------------------------|-------------------|-----------------------------------------------|
| `new_tab`              | -                 | Create new tab                                |
| `previous_tab`         | -                 | Switch to preceding tab                       |
| `next_tab`             | -                 | Switch to following tab                       |
| `last_tab`             | -                 | Jump to final tab                             |
| `goto_tab`             | `goto_tab:index`  | Navigate to tab by 1-based index              |
| `move_tab`             | `move_tab:offset` | Reposition tab (wraps cyclically)             |
| `toggle_tab_overview`  | -                 | Show/hide tab selector. **Linux only**        |
| `prompt_surface_title` | -                 | Open dialog to rename surface. **Linux only** |

```
keybind = ctrl+1=goto_tab:1
keybind = ctrl+9=last_tab
keybind = ctrl+shift+left=move_tab:-1
keybind = ctrl+shift+right=move_tab:1
```

---

## Split Actions

| Action              | Format                          | Description                       |
|---------------------|---------------------------------|-----------------------------------|
| `new_split`         | `new_split:direction`           | Create terminal division          |
| `goto_split`        | `goto_split:target`             | Focus adjacent split              |
| `toggle_split_zoom` | -                               | Expand/contract split to fill tab |
| `resize_split`      | `resize_split:direction,pixels` | Adjust split dimensions           |
| `equalize_splits`   | -                               | Distribute space equally          |

**Directions for `new_split`:** `right`, `down`, `left`, `up`, `auto` (larger axis)

**Targets for `goto_split`:** `right`, `down`, `left`, `up`, `previous`, `next`

```
keybind = ctrl+d=new_split:right
keybind = ctrl+shift+d=new_split:down
keybind = alt+left=goto_split:left
keybind = alt+right=goto_split:right
keybind = ctrl+alt+right=resize_split:right,50
keybind = ctrl+alt+left=resize_split:left,50
keybind = ctrl+shift+z=toggle_split_zoom
keybind = ctrl+shift+e=equalize_splits
```

---

## Window Management Actions

| Action                       | Description                | Platform   |
|------------------------------|----------------------------|------------|
| `reset_window_size`          | Restore default dimensions | macOS only |
| `toggle_maximize`            | Maximize/restore window    | Linux only |
| `toggle_fullscreen`          | Enter/exit fullscreen      | All        |
| `toggle_window_decorations`  | Show/hide titlebar         | Linux only |
| `toggle_window_float_on_top` | Keep window above others   | macOS only |

---

## Inspector & Development Actions

| Action                    | Format           | Description                  | Platform       |
|---------------------------|------------------|------------------------------|----------------|
| `inspector`               | `inspector:mode` | Control inspector visibility | All            |
| `show_gtk_inspector`      | -                | Activate GTK dev tools       | Linux only     |
| `show_on_screen_keyboard` | -                | Display virtual keyboard     | Linux/GTK only |

**Modes for `inspector`:** `toggle`, `show`, `hide`

```
keybind = ctrl+shift+i=inspector:toggle
```

---

## Configuration Actions

| Action          | Description                            |
|-----------------|----------------------------------------|
| `open_config`   | Launch config file in default editor   |
| `reload_config` | Reread and apply configuration changes |

```
keybind = ctrl+comma=open_config
keybind = ctrl+shift+comma=reload_config
```

---

## Closing Actions

| Action              | Description                                     |
|---------------------|-------------------------------------------------|
| `close_surface`     | Close current window, tab, or split             |
| `close_tab`         | Close current tab and all its splits            |
| `close_window`      | Close active window and all contents            |
| `close_all_windows` | **Deprecated** - Use `all:close_window` instead |

```
keybind = ctrl+w=close_surface
keybind = ctrl+shift+w=close_tab
```

---

## Application Actions

| Action                   | Description                   | Platform   |
|--------------------------|-------------------------------|------------|
| `toggle_secure_input`    | Prevent keyboard monitoring   | macOS only |
| `toggle_command_palette` | Display action browser        | Linux only |
| `toggle_quick_terminal`  | Show/hide drop-down terminal  | All        |
| `toggle_visibility`      | Show/hide all windows         | macOS only |
| `check_for_updates`      | Initiate update verification  | macOS only |
| `undo`                   | Revert last reversible action | macOS only |
| `redo`                   | Reapply last undone action    | macOS only |
| `quit`                   | Terminate Ghostty application | All        |

**Reversible actions for undo/redo:** new/close window, tab, split

```
keybind = global:super+backquote=toggle_quick_terminal
keybind = super+h=toggle_visibility
keybind = super+q=quit
```

---

## Testing Actions

| Action | Format | Description |
|--------|--------|-------------|
| `crash` | `crash:thread` | Intentionally crash for testing. **DATA LOSS WARNING** |

**Threads:** `main`, `io`, `render`

---

## Default Keybindings

View all default keybindings:
```bash
ghostty +list-keybinds --default
```

### Common Defaults (Platform Dependent)

| macOS         | Linux          | Action                 |
|---------------|----------------|------------------------|
| `cmd+c`       | `ctrl+shift+c` | `copy_to_clipboard`    |
| `cmd+v`       | `ctrl+shift+v` | `paste_from_clipboard` |
| `cmd+t`       | `ctrl+shift+t` | `new_tab`              |
| `cmd+w`       | `ctrl+shift+w` | `close_surface`        |
| `cmd+n`       | `ctrl+shift+n` | `new_window`           |
| `cmd+d`       | `ctrl+shift+d` | `new_split:right`      |
| `cmd+plus`    | `ctrl+plus`    | `increase_font_size`   |
| `cmd+minus`   | `ctrl+minus`   | `decrease_font_size`   |
| `cmd+0`       | `ctrl+0`       | `reset_font_size`      |
| `cmd+,`       | -              | `open_config`          |
| `cmd+shift+,` | `ctrl+shift+,` | `reload_config`        |

---

## Keybinding Tips

### Remove All Default Bindings
```
keybind = clear
```

### Vim-style Navigation
```
keybind = ctrl+h=goto_split:left
keybind = ctrl+j=goto_split:down
keybind = ctrl+k=goto_split:up
keybind = ctrl+l=goto_split:right
```

### tmux-style Leader Key
```
keybind = ctrl+a>c=new_tab
keybind = ctrl+a>n=next_tab
keybind = ctrl+a>p=previous_tab
keybind = ctrl+a>|=new_split:right
keybind = ctrl+a>-=new_split:down
keybind = ctrl+a>z=toggle_split_zoom
keybind = ctrl+a>x=close_surface
```

### Global Quick Terminal
```
keybind = global:super+backquote=toggle_quick_terminal
```
**macOS:** Requires Accessibility permissions
**Linux:** Requires XDG Desktop Portal (KDE 5.27+, GNOME 48+)
