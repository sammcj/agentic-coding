# iDrive Backup Configuration Reference

## Directory Layout

```
~/Library/Application Support/IDriveforMac/
  appDefaultSettings.plist            # Settings + exclusion rules (XML plist)
  IDLoginDetails.plist                # Account info, quota, server
  IDriveSyncState.plist               # Per-user sync state bool
  backupSetSizeFlagFile.plist         # Size calculation flag
  localBackupSetSizeFlagFile.plist
  localExpressBackupSetSizeFlagFile.plist
  localDrivesPermissions.plist
  SyncFolderReference.plist
  webmanagement.plist
  WebsockPropagationDetails.plist     # Remote mgmt propagation timestamps
  WMKeepAlive
  install.txt                         # Contains "1"
  SessionLogsNew/
    Backup/                           # Plain text logs per session
    LOGXML/                           # Structured XML logs (parseable)
    Archive Cleanup/
    Delete/ | Rename/ | Restore/ | Sync/
  Utilities/
    CloudDetails.plist
  <username>/                         # Email address directory
    backupReferenceFile.plist         # Online backup paths (array)
    localBackupReferenceFile.plist    # Local backup paths
    localExpressBackupReferenceFile.plist
    tempLocalBackupReferenceFile.plist
    backupSetSizeFile.plist           # dict: path -> size string
    IDLoginDetails.plist              # Duplicate of top-level
    fileIndex.plist                   # Dedup index ID
    Sync.plist                        # Sync credentials + config
    NotificationDetails.plist         # Email/desktop notification settings
    CloudBasedAlertSetting.plist
    bandwidthRate                     # Plain text int
    lastBackupTime                    # Plain text timestamp
    destDrive                         # Plain text path
    expressDestDrive | localRestoreDestDrive | expressRestoreDestDrive
    RestorePath
    NewBackupsetOrder.plist           # dict: index -> path
    NewBackupsetSize.plist
    NewLocalBackupSetSizeFile.plist   # dict: path -> {fileCount, fileSize, fileStatus}
    NewLocalExpressBackupSetSizeFile.plist
    NewOnlineBackupSetSizeFile.plist
    ArchiveCleanupDBRecreate.plist
    enumerationVerifySelectionSettings.plist
    InProcessState.plist              # dict: {Notify: "1"} during ops
    userStatusForEnum.plist
    NetworkDriveBackupSet.plist
    NetworkDriveSize.plist
    desktopNotificationTimeStamp
    LastCreateTime.txt
    <username>                        # Plain text server info
    <username>e                       # Extended info
    CheckSum/                         # Empty when idle
    LDB_NEW/                          # Binary dedup databases (170-250 MB, root-owned)
    Operation/
      Backup/
        IBThrottle                    # Current throttle value (root-owned)
        intCancel                     # Cancel flag "1" (root-owned)
      evs_temp/info_tempchk/          # Checksum verification
      IntCheckSumLink/
      AccountServerDBDownload/
    Processfiles/interactive/
```

---

## appDefaultSettings.plist - Scalar Settings

The file is an XML plist with structure: `dict { username_email: dict { settings } }`.
There are exactly 27 top-level keys per user: 22 scalars + 5 exclusion map dicts.

| Plist Key                        | Type | Default | Notes                                     |
|----------------------------------|------|---------|-------------------------------------------|
| `AutoUpdate`                     | int  | 1       | 0/1 boolean                               |
| `AutomaticSync`                  | bool | true    |                                           |
| `BackupFailTextFieldValue`       | int  | 4       | Failure notification threshold            |
| `MonochromeMenuIcon`             | int  | 0       | 0/1 boolean                               |
| `NotifyFaiulreValue`             | int  | 10      | TYPO in key name is real                  |
| `NotifySpecialFailureState`      | bool | false   |                                           |
| `NotifySpecialFailureValue`      | int  | 0       |                                           |
| `PowerAfterScheduledJob `        | bool | false   | TRAILING SPACE in key                     |
| `ScheduleBackupFailAlert`        | bool | true    |                                           |
| `ShowHiddenFilesKey `            | bool | true    | TRAILING SPACE in key                     |
| `SleepWakeupModeKey`             | bool | false   | Wake for backup                           |
| `StartBackupTimer`               | bool | false   | Timer-based backup                        |
| `StartBackupTimerTextFieldValue` | int  | 0       | Timer interval                            |
| `UploadMultipleFileChunksKey`    | bool | true    | Multi-chunk uploads                       |
| `batteryButtonStatus`            | int  | 1       | 0/1 boolean                               |
| `batteryPercent`                 | int  | 50      | 0-100                                     |
| `blockProfile`                   | str  | ""      |                                           |
| `enableExcludeHiddenFilesKey`    | int  | 0       | 0/1 boolean, global hidden file exclusion |
| `launchOnStartup`                | int  | 1       | 0/1 boolean                               |
| `mNumberOfDays`                  | int  | 60      | Retention period                          |
| `mPercentageOfFiles`             | int  | 5       |                                           |
| `mTotalPercentageOfFiles`        | int  | 100     |                                           |

Type mixing: `AutoUpdate`, `batteryButtonStatus`, `enableExcludeHiddenFilesKey`, `launchOnStartup`, `MonochromeMenuIcon` use int 0/1 for booleans. The rest use native plist `<true/>`/`<false/>`.

---

## Exclusion Maps - Detailed

All five maps are `dict` where keys are paths/patterns and values are always `int(1)`.

### Default Exclusion (24 entries, read-only)

Core macOS system directories. All absolute paths:

```
/Desktop DB  /Desktop DF  /Network  /System  /Temporary Items
/TheVolumeSettingsFolder  /Trash  /Volumes  /automount  /bin
/cores  /dev  /etc  /home  /mach  /mach.sym  /mach_kernel
/mach_kernel.ctfsys  /net  /private  /sbin  /tmp  /usr  /var
```

### Partial File Exclusion (41 entries, read-only)

All entries are **relative patterns** (never absolute). Three sub-categories:

**Dot-prefix patterns** (23): directory names and extensions
`.HuggingFace` `.Huggingface` `.Trash` `.asdf` `.cache` `.cargo` `.conda`
`.git` `.huggingface` `.jar` `.lock` `.mono` `.npm` `.pnpm` `.previous`
`.pyc` `.rustup` `.swp` `.tmp` `.trash` `.uv` `.venv` `.yarn`

**Bare name patterns** (17): directory/file names
`Backups.backupdb` `IDrive Downloads` `IDrive-Sync` `IDriveLocal`
`IDriveforMac` `anaconda` `default.realm.note` `fp16.bin` `ggml` `gguf`
`mamaba` `miniconda` `node_modules` `onnx` `realm.note` `safetensors`
`site-packages`

**Path-containing pattern** (1): `pkg/mod`

**Matching algorithm**: For each pattern, two checks run:

1. `os.path.basename(path) == pattern` (exact filename match)
2. `pattern in path` (substring anywhere in the full path)

This means `.cache` matches `/foo/.cache/bar` AND `/foo/download_cache/bar`.

### User Profile Default Exclusion (7 entries, read-only)

Mix of system-level and user-specific absolute paths:

```
/Library/Caches
/Library/Logs
/Users/<user>/Library/Application Support/com.apple.LaunchServicesTemplateApp.dv
/Users/<user>/Library/Caches
/Users/<user>/Library/Cookies
/Users/<user>/Library/Logs
/Users/<user>/Library/Saved Application State
```

### User specified Exclusion (variable, editable)

All absolute paths. No tildes, no trailing slashes, no relative patterns. Can contain 100-2000+ entries. Typical distribution on a real system with ~1,800 entries:

- ~95% under `/Users/<user>` (mostly `Library/Containers/com.apple.*` auto-populated by iDrive)
- ~5% system-level (`/Library/*`, `/Applications`, etc.)

### Propagated Files Exclusion (usually 0 entries)

Pushed from web management console. Same format as other maps but managed remotely.

---

## Backup Reference Files

### backupReferenceFile.plist (online backup)

```xml
<plist version="1.0">
<array>
  <string>/Users</string>
</array>
</plist>
```

Can be as broad as `/Users` or as granular as individual subdirectories.

### localBackupReferenceFile.plist (local backup)

Same array format but typically more specific: `/Users/<user>/Desktop`, `/Users/<user>/Documents`, `/Users/<user>/Music`, `/Users/<user>/Pictures`.

### localExpressBackupReferenceFile.plist

Often identical to local backup reference.

---

## IDLoginDetails.plist

```xml
<dict>
  <key>Username</key><string>user@example.com</string>
  <key>IDriveQuota</key><string>5368709120000</string>    <!-- bytes as string -->
  <key>IDriveQuotaUsed</key><string>3369072386164</string> <!-- bytes as string -->
  <key>AccountDBSize</key><string>6312640512</string>
  <key>EncType</key><string>PRIVATE</string>  <!-- or DEFAULT -->
  <key>Plan</key><string>Personal</string>
  <key>PlanType</key><string>Regular</string>
  <key>AppVersion</key><string>4.0.0.71</string>
  <key>dedup</key><string>on</string>
  <key>dedup_enabled</key><true/>
  <key>serverName</key><string>evs2932.idrive.com</string>
  <key>serverIP</key><string>66.114.102.143</string>
  <key>UserAtServer</key><string>user@example.com@evs2932.idrive.com::ibackup</string>
  <!-- ... more server/auth fields -->
</dict>
```

Quota values are strings containing byte counts. Convert to int for calculations.

---

## Session Logs

### LOGXML (structured, parseable)

Location: `SessionLogsNew/LOGXML/`

Naming: `MM-DD-YYYY.xml` (scheduled/manual), `MM-DD-YYYY_cdp.xml` (CDP).

```xml
<records>
  <record>
    <uname>user@example.com</uname>
    <status>Success</status>          <!-- Success | Failure | In Progress -->
    <duration>00:02:11</duration>
    <content><![CDATA[...!!!-separated fields...]]></content>
    <datetime>04-11-2026 11:49:20</datetime>
    <files>7240</files>
    <filesinsync>27</filesinsync>
    <optype>7</optype>                <!-- 1=Manual, 2=Scheduled, 7=CDP -->
    <size>1649206849</size>           <!-- bytes -->
    <backedupfiles>7240</backedupfiles>
    <mpc>hostname</mpc>
    <alert></alert>                   <!-- non-empty on warnings/errors -->
  </record>
</records>
```

A single XML file can contain multiple `<record>` elements. `In Progress` records may lack `<content>`.

The `<content>` CDATA uses `!!!` as line separator and URL-encodes special chars (`%40` for @, `%20` for space).

### Backup logs (plain text)

Location: `SessionLogsNew/Backup/`

Three files per session:

- `<timestamp>` - main log (large, 1-13 MB for CDP)
- `<timestamp>_info` - per-file detail log
- `<timestamp>.summary` - human-readable summary

**CDP log filenames have a leading space** (iDrive bug): ` 04-11-2026-00-00-00`. Scheduled logs don't.

Summary format:

```
Start Time: 04-11-2026 15:14:35
End Time: 04-11-2026 15:18:50

Files considered for backup: 5200
Files already present in your account: 73
Files backed up now: 5127 files (2.71 GB)
```

---

## NotificationDetails.plist

```xml
<dict>
  <key>emailEnableState</key><integer>1</integer>
  <key>emailEnableStateOfLocal</key><integer>0</integer>
  <key>emailEnableStateOfExpressDrive</key><integer>0</integer>
  <key>emailEnableStateOfNetworkDrive</key><integer>0</integer>
  <key>emailIDs</key><string>user@example.com</string>
  <key>notifyMe</key><integer>1</integer>
  <key>desktopNotfnState</key><integer>0</integer>
  <key>startMissedJobState</key><integer>1</integer>
  <key>backupType</key><integer>0</integer>
</dict>
```

---

## WebsockPropagationDetails.plist

Tracks when settings were last pushed from the web console. Dict keyed by username, values are epoch millisecond timestamps:

- `DefaultBackupSetDB`, `chk_asksave`, `chk_multiupld`, `chk_update`
- `ignore_accesserr`, `stop_schedule_backup`, `stop_schedule_backup_val`

---

## Operation Control Files

Under `<username>/Operation/Backup/`:

| File         | Owner | Content                                               |
| ------------ | ----- | ----------------------------------------------------- |
| `IBThrottle` | root  | Current bandwidth throttle value (plain text integer) |
| `intCancel`  | root  | Cancel flag, "1" means cancel requested               |

Read-only from user perspective (daemon writes these as root).

---

## Plain Text Config Files

| File               | Location | Content               | Example                       |
| ------------------ | -------- | --------------------- | ----------------------------- |
| `bandwidthRate`    | user dir | Bandwidth limit       | `42`                          |
| `lastBackupTime`   | user dir | Last backup timestamp | `04-11-2026 04:01:42`         |
| `destDrive`        | user dir | Destination drive     | `/System/Volumes/Data`        |
| `expressDestDrive` | user dir | Express destination   | `/System/Volumes/Data`        |
| `RestorePath`      | user dir | Restore path          | `/Users/samm/IDrive Restored` |
| `install.txt`      | top dir  | Installation flag     | `1`                           |

---

## Reading/Writing Plists

**Python** (preferred for complex operations):

```python
import plistlib
with open(path, 'rb') as f:
    data = plistlib.load(f)
# Modify data...
with open(path, 'wb') as f:
    plistlib.dump(data, f, fmt=plistlib.FMT_XML)
```

**plutil** (quick reads):

```bash
plutil -convert xml1 -o - file.plist   # dump to stdout
plutil -lint file.plist                 # validate
```

**defaults** (simple key reads):

```bash
defaults read ~/Library/Application\ Support/IDriveforMac/appDefaultSettings "user@example.com"
```

iDrive uses XML plist format. Always write back as XML (`plistlib.FMT_XML`).
