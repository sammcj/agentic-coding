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
| `scroll_to_row`          | `scroll_to_row:row`               | Scroll to absolute row (0 = first)  |
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

## Search Actions

Available since Ghostty 1.3. Search has its own GUI in the terminal surface.

| Action             | Format                      | Description                                          |
|--------------------|-----------------------------|------------------------------------------------------|
| `start_search`     | -                           | Open the search UI without setting a query           |
| `search`           | `search:text`               | Search for the given text (empty cancels)            |
| `search_selection` | -                           | Search for the current selection                     |
| `navigate_search`  | `navigate_search:direction` | Move between results: `previous` or `next`           |
| `end_search`       | -                           | End the current search and hide the search GUI       |

```
keybind = ctrl+shift+f=start_search
keybind = ctrl+f=search_selection
keybind = ctrl+g=navigate_search:next
keybind = ctrl+shift+g=navigate_search:previous
keybind = escape=end_search
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

| Action        | Format                | Description                                  |
|---------------|-----------------------|----------------------------------------------|
| `new_window`  | -                     | Open new terminal window                     |
| `goto_window` | `goto_window:target`  | Focus the `previous` or `next` window        |

```
keybind = super+shift+bracket_left=goto_window:previous
keybind = super+shift+bracket_right=goto_window:next
```

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

```
keybind = ctrl+1=goto_tab:1
keybind = ctrl+9=last_tab
keybind = ctrl+shift+left=move_tab:-1
keybind = ctrl+shift+right=move_tab:1
```

---

## Title Actions

| Action                 | Format                    | Description                                       |
|------------------------|---------------------------|---------------------------------------------------|
| `set_surface_title`    | `set_surface_title:title` | Set the focused surface's title (empty resets it) |
| `set_tab_title`        | `set_tab_title:title`     | Set the current tab's title (empty clears it)     |
| `prompt_surface_title` | -                         | Open a dialog to rename the focused surface       |
| `prompt_tab_title`     | -                         | Open a dialog to rename the current tab           |

A tab title set via `set_tab_title` or `prompt_tab_title` overrides any title the terminal application sets, and persists across focus changes.

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

| Action                      | Description                                      | Platform   |
|-----------------------------|--------------------------------------------------|------------|
| `toggle_secure_input`       | Prevent keyboard monitoring                      | macOS only |
| `toggle_command_palette`    | Display action browser                           | All        |
| `toggle_quick_terminal`     | Show/hide drop-down terminal                     | All        |
| `toggle_mouse_reporting`    | Toggle mouse reporting (see `mouse-reporting`)   | All        |
| `toggle_readonly`           | Toggle read-only mode (no input sent to the PTY) | All        |
| `toggle_background_opacity` | Toggle transparent/opaque (no-op if opacity >=1) | macOS only |
| `toggle_visibility`         | Show/hide all windows                            | macOS only |
| `check_for_updates`         | Initiate update verification                     | macOS only |
| `undo`                      | Revert last reversible action                    | macOS only |
| `redo`                      | Reapply last undone action                       | macOS only |
| `quit`                      | Terminate Ghostty application                    | All        |

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

## Key Table & Sequence Actions

Available since Ghostty 1.3. Named key tables let a trigger switch into a different set of bindings (a modal layer), similar to Vim modes or tmux prefix tables. The named tables themselves are defined in the `keybind` configuration; these actions activate and deactivate them.

| Action                      | Format                         | Description                                              |
|-----------------------------|--------------------------------|----------------------------------------------------------|
| `activate_key_table`        | `activate_key_table:name`      | Activate a named table; stays active until deactivated   |
| `activate_key_table_once`   | `activate_key_table_once:name` | Activate a named table until its first valid binding runs|
| `deactivate_key_table`      | -                              | Deactivate the current table; the previous one returns   |
| `deactivate_all_key_tables` | -                              | Deactivate every active table                            |
| `end_key_sequence`          | -                              | End the active key sequence, flushing prior keys to the terminal |

```
# Enter a modal "resize" table, then deactivate it with escape
keybind = ctrl+a>r=activate_key_table:resize
# Flush ctrl+w to the program instead of waiting for the next key in a sequence
keybind = ctrl+w>escape=end_key_sequence
```

If a named table does not exist, the activate actions have no effect and report `performable` as false.

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
