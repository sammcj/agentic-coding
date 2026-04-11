---
name: idrive-backup
description: Use this skill whenever the user wants you to manage, discuss or diagnose iDrive Backup configuration on macOS
allowed-tools: Read Edit Write Bash Glob Grep
---

# iDrive Backup for macOS

iDrive stores all configuration at `~/Library/Application Support/IDriveforMac/`. The username is the iDrive account email (e.g. `user@example.com`), detected from the top-level key in `appDefaultSettings.plist`.

## The Tool

This skill bundles `scripts/idrive_tool.py` which handles all iDrive operations with correct matching semantics, symlink resolution, and safety backups. Run it with:

```bash
python3 <skill-path>/scripts/idrive_tool.py <command> [args...]
```

### Commands

| Command                               | Description                                                                                         |
| ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `check-exclusion <path>`              | Check if a path is excluded and by which rules. Reports backup scope too                            |
| `check-scope <path>`                  | Check if a path falls under any backup reference path                                               |
| `list-exclusions [--category <name>]` | List exclusion entries. Categories: Default, Partial File, User Profile, User Specified, Propagated |
| `add-exclusion <path>`                | Add absolute path to User Specified exclusions (auto-backups config first)                          |
| `remove-exclusion <path>`             | Remove path from User Specified exclusions                                                          |
| `show-settings`                       | Display all scalar settings with current values                                                     |
| `set-setting <key> <value>`           | Modify a setting (auto-detects type from existing value)                                            |
| `account-status`                      | Show quota, usage, encryption type, plan, app version                                               |
| `last-backup`                         | Parse recent LOGXML files and show backup status/results                                            |
| `find-redundant`                      | Find exclusion paths made redundant by a parent path in any map                                     |
| `clean-redundant`                     | Remove redundant entries from User Specified exclusions                                             |
| `list-backup-paths`                   | List all online backup reference paths                                                              |
| `add-backup-path <path>`              | Add a directory to backup reference                                                                 |
| `remove-backup-path <path>`           | Remove a directory from backup reference                                                            |
| `backup-config`                       | Create timestamped backup copies of config files                                                    |

## Safety Rules

1. **Back up before modifying.** The tool does this automatically. Manual changes must copy both `appDefaultSettings.plist` and `<username>/backupReferenceFile.plist` to `~/.idrive-backup/backups/` with timestamps first.
2. **Only modify User Specified exclusions.** The other four maps (Default, Partial File, User Profile, Propagated) are system-managed and will be overwritten by iDrive.
3. **Preserve plist key quirks exactly.** Two keys have trailing spaces: `ShowHiddenFilesKey ` and `PowerAfterScheduledJob `. One has a typo: `NotifyFaiulreValue`. The editable exclusion map key is `User specified Exclusion` (lowercase 's'). Getting any of these wrong creates orphaned keys.
4. **Never modify** `IDLoginDetails.plist`, `Sync.plist`, `LDB_NEW/*.ib` databases, or anything under `Operation/` (root-owned daemon files).
5. **Exclusion values are always int(1).** Presence in the map means excluded. Never write a 0 value; delete the key instead.
6. **All User Specified paths must be absolute.** No tildes, no trailing slashes, no relative paths.

## Five Exclusion Maps

| Map            | Plist Key                        | Count     | Matching                                     | Editable         |
| -------------- | -------------------------------- | --------- | -------------------------------------------- | ---------------- |
| Default        | `Default Exclusion`              | ~24       | Exact/parent path                            | No               |
| Partial File   | `Partial File Exclusion`         | ~41       | **Substring** of full path OR exact filename | No               |
| User Profile   | `User Profile Default Exclusion` | ~7        | Exact/parent path                            | No               |
| User Specified | `User specified Exclusion`       | 100-2000+ | Exact/parent path                            | **Yes**          |
| Propagated     | `Propagated Files Exclusion`     | Usually 0 | Exact/parent path                            | No (web console) |

**Partial File Exclusion is substring-based.** This is the trickiest map. A pattern like `.cache` matches both `/Users/foo/.cache` and `/path/to/download_cache`. Patterns are relative names (never absolute paths), including dotfile dirs (`.git`, `.venv`), filename patterns (`fp16.bin`, `safetensors`), and one with a separator (`pkg/mod`).

## Key Gotchas

1. **Mixed boolean types.** Some settings use `<true/>`/`<false/>`, others use `<integer>0</integer>`/`<integer>1</integer>` for the same concept. The tool handles this; if modifying manually, match the existing type.
2. **Symlinks/firmlinks.** `~/Desktop` may resolve to `~/Library/Mobile Documents/com~apple~CloudDocs/Desktop` when iCloud Desktop is enabled. Always resolve with `os.path.realpath()` before comparing paths.
3. **CDP log filenames have a leading space.** iDrive bug: Continuous Data Protection logs in `SessionLogsNew/Backup/` are named ` MM-DD-YYYY-00-00-00` (note leading space). Account for this when globbing or reading.
4. **Some files are root-owned.** `Operation/Backup/IBThrottle`, `LDB_NEW/*.ib`, and some plists are written by the iDrive daemon as root. Reading is fine; writing requires elevated privileges you shouldn't use.
5. **The appDefaultSettings.plist can be large.** User Specified Exclusion alone can have 1,800+ entries (mostly auto-populated `~/Library/Containers/com.apple.*` paths). The plist file can exceed 170 KB.

## Detailed Reference

For detailed file format information, all 22+ scalar settings with types and descriptions, secondary file formats (logs, size files, sync config), or the complete directory layout, read `references/idrive-config.md`.
