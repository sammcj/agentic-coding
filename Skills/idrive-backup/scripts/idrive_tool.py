#!/usr/bin/env python3
"""iDrive Backup configuration tool for Claude Code.

Handles reading, querying, and safely modifying iDrive Backup configuration
on macOS. All operations use correct exclusion matching semantics including
Partial File Exclusion substring matching and symlink/firmlink resolution.

Requires only Python 3 stdlib (ships with macOS).
"""

import os
import plistlib
import shutil
import sys
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

IDRIVE_DIR = Path.home() / "Library" / "Application Support" / "IDriveforMac"
BACKUP_DIR = Path.home() / ".idrive-backup" / "backups"

# Plist keys for exclusion maps (exact names including quirks)
EXCLUSION_MAPS = {
    "Default": "Default Exclusion",
    "Partial File": "Partial File Exclusion",
    "User Profile": "User Profile Default Exclusion",
    "User Specified": "User specified Exclusion",  # lowercase 's' in "specified"
    "Propagated": "Propagated Files Exclusion",
}

EDITABLE_MAPS = {"User Specified"}

OPTYPE_NAMES = {"1": "Manual", "2": "Scheduled", "7": "CDP"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def die(msg):
    print(f"Error: {msg}", file=sys.stderr)
    sys.exit(1)


def load_settings():
    """Load appDefaultSettings.plist -> (data_dict, username, file_path)."""
    path = IDRIVE_DIR / "appDefaultSettings.plist"
    if not path.exists():
        die(f"{path} not found. Is iDrive installed?")
    with open(path, "rb") as f:
        data = plistlib.load(f)
    if not data:
        die("Empty settings file")
    username = next(iter(data))
    return data, username, path


def load_backup_ref(username):
    """Load backupReferenceFile.plist -> (list_of_paths, file_path)."""
    path = IDRIVE_DIR / username / "backupReferenceFile.plist"
    if not path.exists():
        return [], path
    with open(path, "rb") as f:
        data = plistlib.load(f)
    return list(data), path


def save_plist(data, path):
    """Write plist atomically: write to temp file, verify, rename over original.

    This prevents corruption if the process is interrupted mid-write.
    """
    path = Path(path)
    tmp = path.with_suffix(".plist.tmp")
    try:
        with open(tmp, "wb") as f:
            plistlib.dump(data, f, fmt=plistlib.FMT_XML)
        # Verify the written file is valid plist before replacing original
        with open(tmp, "rb") as f:
            plistlib.load(f)
        os.replace(tmp, path)
    except Exception:
        # Clean up temp file on any failure
        tmp.unlink(missing_ok=True)
        raise


def path_variants(p):
    """Return [original, symlink-resolved] for firmlink-aware comparison."""
    p = str(p).rstrip("/")
    if p.startswith("~/"):
        p = str(Path.home() / p[2:])
    elif p == "~":
        p = str(Path.home())
    variants = [p]
    try:
        resolved = os.path.realpath(p)
        if resolved != p:
            variants.append(resolved)
    except OSError:
        pass
    return variants


def is_child_path(child, parent):
    """True when child is strictly beneath parent in the directory tree."""
    return child.startswith(parent + "/")


def check_no_backup_in_progress():
    """Warn if iDrive appears to be running a backup right now."""
    try:
        _, username, _ = load_settings()
        cancel_file = IDRIVE_DIR / username / "Operation" / "Backup" / "intCancel"
        in_process = IDRIVE_DIR / username / "InProcessState.plist"
        if cancel_file.exists():
            with open(cancel_file) as f:
                if f.read().strip() == "0":
                    # intCancel=0 means a backup is active (not cancelled)
                    print("Warning: iDrive may have a backup in progress. "
                          "Modifying config during a backup is risky.", file=sys.stderr)
        if in_process.exists():
            with open(in_process, "rb") as f:
                state = plistlib.load(f)
            if state.get("Notify") == "1":
                pass  # Notify=1 is normal idle state
    except (SystemExit, OSError, plistlib.InvalidFileException):
        pass  # can't check, proceed anyway


def create_backup():
    """Copy both config files to ~/.idrive-backup/backups/ with timestamp.

    Returns True on success. Returns False if backups couldn't be created,
    in which case callers should abort the write operation.
    """
    try:
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"Error: cannot create backup directory {BACKUP_DIR} (permission denied). "
              "Aborting to avoid writing without a safety backup.", file=sys.stderr)
        return False

    ts = datetime.now().strftime("%Y-%m-%d-%H-%M")
    ok = True

    src = IDRIVE_DIR / "appDefaultSettings.plist"
    if src.exists():
        dst = BACKUP_DIR / f"appDefaultSettings_backup_{ts}.plist"
        try:
            shutil.copy2(src, dst)
            print(f"Backed up: {dst}")
        except (PermissionError, OSError) as e:
            print(f"Error: cannot write backup to {dst}: {e}", file=sys.stderr)
            ok = False

    try:
        _, username, _ = load_settings()
        ref = IDRIVE_DIR / username / "backupReferenceFile.plist"
        if ref.exists():
            dst = BACKUP_DIR / f"backupReferenceFile_backup_{ts}.plist"
            try:
                shutil.copy2(ref, dst)
                print(f"Backed up: {dst}")
            except (PermissionError, OSError) as e:
                print(f"Error: cannot write backup to {dst}: {e}", file=sys.stderr)
                ok = False
    except SystemExit:
        pass  # settings file missing, skip backup ref

    if not ok:
        print("Aborting: could not create safety backups.", file=sys.stderr)
    return ok


def fmt_bytes(n):
    """Human-readable byte size."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.2f} {unit}" if unit != "B" else f"{n} {unit}"
        n /= 1024
    return f"{n:.2f} PB"


# ---------------------------------------------------------------------------
# Exclusion matching
# ---------------------------------------------------------------------------

def check_partial_match(full_path, patterns):
    """Partial File Exclusion uses substring matching on the full path.

    When basename equals the pattern, that's the most specific match so we
    report only "filename match" (the substring check would also pass since
    the basename is part of the full path, but that's redundant).
    """
    hits = []
    basename = os.path.basename(full_path)
    for pat in patterns:
        if basename == pat:
            hits.append((pat, "filename match"))
        elif pat in full_path:
            hits.append((pat, "substring match"))
    return hits


def find_exclusion_matches(query_path):
    """Return all exclusion matches for a path across every map."""
    data, username, _ = load_settings()
    us = data[username]
    q_variants = path_variants(query_path)
    matches = []

    for label, plist_key in EXCLUSION_MAPS.items():
        exc = us.get(plist_key, {})

        if label == "Partial File":
            for qv in q_variants:
                for pat, how in check_partial_match(qv, exc.keys()):
                    matches.append({"category": label, "rule": pat, "match_type": how})
        else:
            for exc_key in exc:
                enorm = exc_key.rstrip("/")
                if not enorm:
                    continue
                e_variants = path_variants(enorm)
                for qv in q_variants:
                    for ev in e_variants:
                        if qv == ev:
                            matches.append({"category": label, "rule": exc_key, "match_type": "exact"})
                        elif is_child_path(qv, ev):
                            matches.append({"category": label, "rule": exc_key, "match_type": "parent"})

    # Hidden-file exclusion
    if us.get("enableExcludeHiddenFilesKey", 0) == 1:
        bn = os.path.basename(query_path.rstrip("/"))
        if bn.startswith("."):
            matches.append({"category": "Hidden Files", "rule": "enableExcludeHiddenFilesKey=1", "match_type": "hidden file"})

    # Deduplicate
    seen = set()
    unique = []
    for m in matches:
        key = (m["category"], m["rule"], m["match_type"])
        if key not in seen:
            seen.add(key)
            unique.append(m)
    return unique


def find_scope(query_path):
    """Return (in_scope: bool, matching_backup_path | None)."""
    _, username, _ = load_settings()
    bp_list, _ = load_backup_ref(username)
    q_variants = path_variants(query_path)

    for bp in bp_list:
        bp_clean = bp.rstrip("/")
        bp_v = path_variants(bp_clean)
        for qv in q_variants:
            for bv in bp_v:
                if qv == bv or is_child_path(qv, bv):
                    return True, bp
    return False, None


# ---------------------------------------------------------------------------
# Redundancy detection
# ---------------------------------------------------------------------------

def collect_all_exclusion_paths():
    """Gather (normalised, original_key, category) from all five maps."""
    data, username, _ = load_settings()
    us = data[username]
    entries = []
    for label, plist_key in EXCLUSION_MAPS.items():
        for key in us.get(plist_key, {}):
            norm = key.rstrip("/")
            if norm:
                entries.append((norm, key, label))
    return entries


def find_redundant_exclusions():
    entries = collect_all_exclusion_paths()
    redundant = []
    for norm, orig, cat in entries:
        for p_norm, _, p_cat in entries:
            if p_norm == norm:
                continue
            if is_child_path(norm, p_norm):
                redundant.append({
                    "path": norm,
                    "original_key": orig,
                    "category": cat,
                    "parent_path": p_norm,
                    "parent_category": p_cat,
                    "cleanable": cat == "User Specified",
                })
                break
    redundant.sort(key=lambda r: (r["path"], r["category"]))
    return redundant


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_check_exclusion(args):
    if not args:
        die("Usage: check-exclusion <path>")
    path = args[0]
    matches = find_exclusion_matches(path)
    in_scope, scope_path = find_scope(path)

    print(f"Path: {path}")
    scope_msg = f"Yes (under {scope_path})" if in_scope and scope_path else "No"
    print(f"In backup scope: {scope_msg}")
    print()

    if matches:
        print(f"EXCLUDED by {len(matches)} rule(s):")
        for m in matches:
            print(f"  [{m['category']}] {m['rule']} ({m['match_type']})")
        verdict = "in scope but EXCLUDED" if in_scope else "outside backup scope and also excluded"
        print(f"\nVerdict: NOT backed up ({verdict}).")
    elif in_scope:
        print("Not matched by any exclusion rule.")
        print("\nVerdict: This path WILL be backed up.")
    else:
        print("Not matched by any exclusion rule, but NOT in backup scope.")
        print("\nVerdict: NOT backed up (not under any backup path).")


def cmd_check_scope(args):
    if not args:
        die("Usage: check-scope <path>")
    ok, bp = find_scope(args[0])
    msg = f"Yes (under {bp})" if ok and bp else "No"
    print(f"In scope: {msg}")


def cmd_list_exclusions(args):
    category = None
    if len(args) >= 2 and args[0] == "--category":
        category = args[1]

    data, username, _ = load_settings()
    us = data[username]

    for label, plist_key in EXCLUSION_MAPS.items():
        if category and label.lower() != category.lower():
            continue
        exc = us.get(plist_key, {})
        tag = "editable" if label in EDITABLE_MAPS else "read-only"
        print(f"=== {label} ({len(exc)} entries, {tag}) ===")
        for p in sorted(exc.keys()):
            print(f"  {p}")
        print()


def _prepare_write():
    """Common pre-write checks: backup-in-progress warning + safety backup.

    Calls sys.exit(1) if backups can't be created.
    """
    check_no_backup_in_progress()
    if not create_backup():
        sys.exit(1)


def cmd_add_exclusion(args):
    if not args:
        die("Usage: add-exclusion <absolute-path>")
    path = args[0]
    if not path.startswith("/"):
        die("Path must be absolute (start with /)")
    if path.endswith("/"):
        path = path.rstrip("/")

    _prepare_write()
    data, username, settings_path = load_settings()
    us = data[username]
    exc = us.get("User specified Exclusion", {})

    if path in exc:
        print(f"Already excluded: {path}")
        return

    exc[path] = 1
    us["User specified Exclusion"] = exc
    data[username] = us
    save_plist(data, settings_path)
    print(f"Added exclusion: {path}")


def cmd_remove_exclusion(args):
    if not args:
        die("Usage: remove-exclusion <path>")
    path = args[0]

    _prepare_write()
    data, username, settings_path = load_settings()
    us = data[username]
    exc = us.get("User specified Exclusion", {})

    if path not in exc:
        print(f"Not found in User specified Exclusion: {path}")
        return

    del exc[path]
    us["User specified Exclusion"] = exc
    data[username] = us
    save_plist(data, settings_path)
    print(f"Removed exclusion: {path}")


def cmd_show_settings(args):  # noqa: ARG001
    del args  # no arguments for this command
    data, username, _ = load_settings()
    us = data[username]
    print(f"Username: {username}\n")
    for key in sorted(us.keys()):
        val = us[key]
        if isinstance(val, dict):
            print(f"  {key}: ({len(val)} entries)")
        else:
            print(f"  {key}: {val!r}")


def cmd_set_setting(args):
    if len(args) < 2:
        die("Usage: set-setting <key> <value>")
    key, raw = args[0], args[1]

    _prepare_write()
    data, username, settings_path = load_settings()
    us = data[username]

    # Handle keys with trailing spaces (ShowHiddenFilesKey , PowerAfterScheduledJob )
    # If the exact key isn't found, check for a variant with trailing space.
    existing = us.get(key)
    if existing is None and key + " " in us:
        actual_key = key + " "
        print(f"Note: using actual plist key '{actual_key}' (has trailing space).", file=sys.stderr)
        key = actual_key
        existing = us.get(key)
    value: object
    if existing is None:
        print(f"Warning: '{key}' not in current settings, adding as string.", file=sys.stderr)
        value = raw
    elif isinstance(existing, bool):
        value = raw.lower() in ("true", "1", "yes", "on", "enabled")
    elif isinstance(existing, int):
        value = int(raw)
    elif isinstance(existing, str):
        value = raw
    else:
        die(f"Cannot modify key '{key}' (type {type(existing).__name__})")
        return  # unreachable, but satisfies type checker

    us[key] = value
    data[username] = us
    save_plist(data, settings_path)
    print(f"Set {key} = {value!r}")


def cmd_account_status(args):  # noqa: ARG001
    del args  # no arguments for this command
    login = IDRIVE_DIR / "IDLoginDetails.plist"
    if not login.exists():
        die("IDLoginDetails.plist not found")
    with open(login, "rb") as f:
        d = plistlib.load(f)

    quota = int(d.get("IDriveQuota", "0"))
    used = int(d.get("IDriveQuotaUsed", "0"))
    free = quota - used
    pct = (used / quota * 100) if quota > 0 else 0

    print(f"Username:   {d.get('Username', '?')}")
    print(f"Plan:       {d.get('Plan', '?')} ({d.get('PlanType', '')})")
    print(f"Encryption: {d.get('EncType', '?')}")
    print(f"Dedup:      {d.get('dedup', '?')}")
    print(f"Version:    {d.get('AppVersion', '?')}")
    print(f"Server:     {d.get('serverName', '?')}")
    print()
    print(f"Quota:  {fmt_bytes(quota)}")
    print(f"Used:   {fmt_bytes(used)} ({pct:.1f}%)")
    print(f"Free:   {fmt_bytes(free)}")


def cmd_last_backup(args):  # noqa: ARG001
    del args  # no arguments for this command
    log_dir = IDRIVE_DIR / "SessionLogsNew" / "LOGXML"
    if not log_dir.exists():
        die("No LOGXML directory found")

    xml_files = sorted(log_dir.glob("*.xml"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not xml_files:
        print("No log files found.")
        return

    for xf in xml_files[:5]:
        print(f"--- {xf.name} ---")
        try:
            tree = ET.parse(xf)
            for rec in tree.getroot().findall("record"):
                status = rec.findtext("status", "?")
                dt = rec.findtext("datetime", "")
                dur = rec.findtext("duration", "")
                files = rec.findtext("backedupfiles", "0")
                size = int(rec.findtext("size", "0"))
                ot = rec.findtext("optype", "")
                alert = rec.findtext("alert", "")

                print(f"  Status:   {status}")
                print(f"  Type:     {OPTYPE_NAMES.get(ot, f'Type {ot}')}")
                print(f"  Time:     {dt}")
                print(f"  Duration: {dur}")
                print(f"  Files:    {files}")
                print(f"  Size:     {fmt_bytes(size)}")
                if alert:
                    print(f"  Alert:    {alert}")
                print()
        except ET.ParseError as e:
            print(f"  XML parse error: {e}\n")


def cmd_find_redundant(args):  # noqa: ARG001
    del args
    redundant = find_redundant_exclusions()
    if not redundant:
        print("No redundant exclusions found.")
        return
    cleanable = sum(1 for r in redundant if r["cleanable"])
    print(f"Found {len(redundant)} redundant exclusion(s), {cleanable} cleanable:\n")
    for r in redundant:
        tag = " [cleanable]" if r["cleanable"] else ""
        print(f"  {r['path']} [{r['category']}]{tag}")
        print(f"    covered by: {r['parent_path']} [{r['parent_category']}]")


def cmd_clean_redundant(args):  # noqa: ARG001
    del args
    _prepare_write()
    data, username, settings_path = load_settings()
    us = data[username]
    exc = us.get("User specified Exclusion", {})

    entries = collect_all_exclusion_paths()
    removed = []
    for norm, orig, cat in entries:
        if cat != "User Specified":
            continue
        for p_norm, _, p_cat in entries:
            if p_norm == norm:
                continue
            if is_child_path(norm, p_norm) and orig in exc:
                del exc[orig]
                removed.append((orig, p_norm, p_cat))
                break

    if removed:
        us["User specified Exclusion"] = exc
        data[username] = us
        save_plist(data, settings_path)
        print(f"Removed {len(removed)} redundant exclusion(s):")
        for orig, parent, p_cat in removed:
            print(f"  {orig} (covered by {parent} [{p_cat}])")
    else:
        print("No cleanable redundant exclusions found.")


def cmd_list_backup_paths(args):  # noqa: ARG001
    del args
    _, username, _ = load_settings()
    paths, _ = load_backup_ref(username)
    print(f"Backup paths ({len(paths)}):")
    for p in sorted(paths):
        print(f"  {p}")


def cmd_add_backup_path(args):
    if not args:
        die("Usage: add-backup-path <absolute-path>")
    path = args[0].rstrip("/")
    if not path.startswith("/"):
        die("Path must be absolute")
    if not os.path.isdir(path):
        die(f"Directory does not exist: {path}")

    _prepare_write()
    _, username, _ = load_settings()
    paths, ref_path = load_backup_ref(username)

    if path in paths:
        print(f"Already in backup paths: {path}")
        return

    paths.append(path)
    save_plist(paths, ref_path)
    print(f"Added backup path: {path}")


def cmd_remove_backup_path(args):
    if not args:
        die("Usage: remove-backup-path <path>")
    path = args[0]

    _prepare_write()
    _, username, _ = load_settings()
    paths, ref_path = load_backup_ref(username)

    if path not in paths:
        print(f"Not in backup paths: {path}")
        return

    paths.remove(path)
    save_plist(paths, ref_path)
    print(f"Removed backup path: {path}")


def cmd_backup_config(args):  # noqa: ARG001
    del args
    create_backup()


# ---------------------------------------------------------------------------
# CLI dispatch
# ---------------------------------------------------------------------------

COMMANDS = {
    "check-exclusion": cmd_check_exclusion,
    "check-scope": cmd_check_scope,
    "list-exclusions": cmd_list_exclusions,
    "add-exclusion": cmd_add_exclusion,
    "remove-exclusion": cmd_remove_exclusion,
    "show-settings": cmd_show_settings,
    "set-setting": cmd_set_setting,
    "account-status": cmd_account_status,
    "last-backup": cmd_last_backup,
    "find-redundant": cmd_find_redundant,
    "clean-redundant": cmd_clean_redundant,
    "list-backup-paths": cmd_list_backup_paths,
    "add-backup-path": cmd_add_backup_path,
    "remove-backup-path": cmd_remove_backup_path,
    "backup-config": cmd_backup_config,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in COMMANDS:
        print("iDrive Backup Configuration Tool\n")
        print("Commands:")
        for name in COMMANDS:
            print(f"  {name}")
        sys.exit(0 if len(sys.argv) >= 2 and sys.argv[1] in ("--help", "-h") else 1)

    COMMANDS[sys.argv[1]](sys.argv[2:])


if __name__ == "__main__":
    main()
