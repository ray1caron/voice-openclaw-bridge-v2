# Bug Tracker CLI User Guide

**Version:** 1.0
**Date:** 2026-02-28
**Location:** `src/bridge/bug_cli.py`
**Database:** `~/.voice-bridge/bugs.db`

---

## Overview

The Bug Tracker CLI provides command-line access to view, filter, and manage bugs captured by the automated bug tracking system. All bugs include full system context, stack traces, and environment data needed for debugging.

---

## Quick Start

```bash
# Set PYTHONPATH to access the module
cd /home/hal/.openclaw/workspace/voice-bridge-v2
export PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:$PYTHONPATH

# Run CLI commands
python3 -m bridge.bug_cli <command> [options]
```

---

## Available Commands

### 1. `list` - View Bugs

List bugs with optional filtering.

**Usage:**
```bash
python3 -m bridge.bug_cli list [options]
```

**Options:**
- `--status <STATUS>` - Filter by status (new, triaged, in_progress, fixed, closed, duplicate)
- `--severity <SEVERITY>` - Filter by severity (critical, high, medium, low, info)
- `--component <COMPONENT>` - Filter by component (audio, stt, tts, websocket, config, etc.)
- `--limit <N>` - Maximum number of bugs to show (default: 50)

**Examples:**

**List all bugs:**
```bash
python3 -m bridge.bug_cli list
```

**Expected Output:**
```
Bug Reports (43 found)
┏━━━━┳━━━━━━━━━━┳━━━━━━━━━━━┳━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━┓
┃ ID ┃ Severity ┃ Component ┃ Status┃ Title                             ┃ Time          ┃
┡━━━━╇━━━━━━━━━━╇━━━━━━━━━━━╇━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━┩
│ 1  │ [red]critical[/]    │ audio_pipeline │ new │ Critical audio crash      │ 2026-02-25T12…│
│ 2  │ [red]critical[/]    │ audio_pipeline │ new │ Critical audio crash      │ 2026-02-25T13…│
│ 3  │ [orange1]high[/]    │ websocket      │ new │ Connection dropped        │ 2026-02-25T14…│
...
└────┴──────────┴───────────┴───────┴───────────────────────────────────┴───────────────┘
```

**List only critical bugs:**
```bash
python3 -m bridge.bug_cli list --severity critical
```

**List bugs for specific component:**
```bash
python3 -m bridge.bug_cli list --component audio_pipeline
```

**List only fixed bugs:**
```bash
python3 -m bridge.bug_cli list --status fixed
```

**List last 5 bugs:**
```bash
python3 -m bridge.bug_cli list --limit 5
```

**Combine filters:**
```bash
python3 -m bridge.bug_cli list --severity critical --component audio_pipeline --limit 10
```

---

### 2. `show` - View Bug Details

Display complete bug information including stack trace, system state, and environment data.

**Usage:**
```bash
python3 -m bridge.bug_cli show <bug_id>
```

**Arguments:**
- `bug_id` - Numeric ID of the bug to display

**Example:**
```bash
python3 -m bridge.bug_cli show 1
```

**Expected Output:**
```
════════════════════════════════════════════════════════════════
Bug #1
════════════════════════════════════════════════════════════════
Critical audio crash

Severity: [red]critical[/]
Component: audio_pipeline
Status: new
Created: 2026-02-25T12:34:56.123456

Description:
Critical audio crash

Stack Trace:
Traceback (most recent call last):
  File "src/bridge/audio_pipeline.py", line 123, in process_audio
    self.audio_buffer.write(data)
  File "src/bridge/audio_buffer.py", line 45, in write
    raise AudioBufferOverflowError()
bridge.audio_buffer.AudioBufferOverflowError: Audio buffer overflow: 48000 samples queued

System State:
{
  "timestamp": "2026-02-25T12:34:56.123456",
  "python_version": "3.12.0",
  "platform": "Linux-6.5.0-14-generic-x86_64",
  "platform_version": "#20-Ubuntu SMP ...",
  "cpu_count": 8,
  "memory_available": 8589934592,
  "disk_free": 1793888014336,
  "audio_devices": [
    {"name": "HDA NVidia: LG HDR 4K (hw:0,3)", "channels": 0},
    {"name": "HDA NVidia: HDMI 1 (hw:0,7)", "channels": 0},
    {"name": "HDA NVidia: HDMI 2 (hw:0,8)", "channels": 0},
    {"name": "HDA Intel: PCH (hw:1,0)", "channels": 2},
    ...
  ],
  "config_hash": "a1b2c3d4e5f6...",
  "session_id": "abc123-def456-ghi789",
  "uptime_seconds": 12345.67
}

User Context: (if provided)
{"test_run": true, "timestamp": "2026-02-25T12:34:56.123456"}
════════════════════════════════════════════════════════════════
```

---

### 3. `stats` - Bug Statistics

Show summary statistics about the bug database.

**Usage:**
```bash
python3 -m bridge.bug_cli stats
```

**Expected Output:**
```
Bug Statistics
┏━━━━━━━━━━━━━━┳━━━━━━━┓
┃ Metric       ┃ Count ┃
┡━━━━━━━━━━━━━━╇━━━━━━━┩
│ Total Bugs   │ 43    │
│ New (unread) │ 43    │
│ Fixed        │ 0     │
│ Critical     │ 17    │
└──────────────┴───────┘
```

---

### 4. `export` - Export Bugs

Export bugs to a file for sharing or archival.

**Usage:**
```bash
python3 -m bridge.bug_cli export <output_file>
```

**Arguments:**
- `output_file` - Path to output file (use `.json` for JSON, `.md` for Markdown)

**Format Detection:**
- `.json` - Export as JSON array
- `.md` - Export as Markdown document
- Other extensions - Export as JSON (default)

**Examples:**

**Export to JSON:**
```bash
python3 -m bridge.bug_cli export /tmp/bugs.json
```

**Expected Output:**
```
2026-02-28 13:33:56 [info] bug_tracker_initialized db_path=/home/hal/.voice-bridge/bugs.db github_enabled=False
2026-02-28 13:33:56 [info] Exported json to /tmp/bugs.json
[green]Exported json to /tmp/bugs.json[/green]
```

**Export to Markdown:**
```bash
python3 -m bridge.bug_cli export /tmp/bugs.md
```

**Expected Output:**
```
2026-02-28 13:33:56 [info] bug_tracker_initialized db_path=/home/hal/.voice-bridge/bugs.db github_enabled=False
2026-02-28 13:33:56 [info] Exported markdown to /tmp/bugs.md
[green]Exported markdown to /tmp/bugs.md[/green]
```

---

### 5. `clear` - Delete Fixed Bugs

Remove bugs that have been marked as FIXED from the database.

**Usage:**
```bash
python3 -m bridge.bug_cli clear [--force]
```

**Options:**
- `--force` - Skip confirmation prompt

**Behavior:**
- Lists number of fixed bugs that will be deleted
- Prompts for confirmation (unless `--force` used)
- Deletes bugs with status='FIXED'

**Examples:**

**Delete fixed bugs with confirmation:**
```bash
python3 -m bridge.bug_cli clear
```

**Expected Output:**
```
Delete 0 fixed bugs? [y/N]: [yellow]No fixed bugs to clear.[/yellow]
Cancelled.
```

**Force delete without confirmation:**
```bash
python3 -m bridge.bug_cli clear --force
```

**Expected Output:**
```
Delete 5 fixed bugs? [y/N]: [green]Would delete 5 fixed bugs[/green]
```

**Note:** The `clear` command is a placeholder in the current implementation. The actual delete functionality needs to be implemented in `BugTracker`.

---

## Severity Levels

| Severity | Meaning | Use For |
|----------|---------|---------|
| **CRITICAL** | Crash, data loss, security | System crashes, data corruption, security vulnerabilities |
| **HIGH** | Feature broken, bad UX | Core features not working, major user impact |
| **MEDIUM** | Annoyance, workaround exists | Minor bugs, edge cases, workarounds available |
| **LOW** | Cosmetic, minor | Typos, UI issues, non-functional bugs |
| **INFO** | Telemetry | Informational messages, usage metrics |

---

## Status Values

| Status | Meaning | When to Set |
|--------|---------|-------------|
| **NEW** | Newly captured | Default status when bug is created |
| **TRIAGED** | Reviewed, prioritized | After manual review and prioritization |
| **IN_PROGRESS** | Being worked on | When development begins |
| **FIXED** | Fix deployed or ready | After fix is complete |
| **CLOSED** | No further action needed | After verification or if not a bug |
| **DUPLICATE** | Same as another bug | After identifying duplicate |

---

## Common Workflows

### Workflow 1: Daily Bug Review

```bash
# Check for new critical bugs
python3 -m bridge.bug_cli list --severity critical --status new

# Review details of top 3 critical bugs
python3 -m bridge.bug_cli show 1
python3 -m bridge.bug_cli show 2
python3 -m bridge.bug_cli show 3

# Update statistics
python3 -m bridge.bug_cli stats
```

### Workflow 2: Investigate Component Issues

```bash
# All bugs in audio_pipeline component
python3 -m bridge.bug_cli list --component audio_pipeline

# Show the oldest bug
python3 -m bridge.bug_cli show 1

# Check if there are patterns (multiple similar bugs)
python3 -m bridge.bug_cli list --component audio_pipeline --severity critical | head -10
```

### Workflow 3: Prepare Bug Report for Team

```bash
# Export all critical bugs
python3 -m bridge.bug_cli list --severity critical > /tmp/critical_bugs.txt

# Export detailed JSON for analysis
python3 -m bridge.bug_cli export /tmp/bugs_detailed.json

# Export formatted Markdown for meeting
python3 -m bridge.bug_cli export /tmp/bugs_meeting.md
```

### Workflow 4: Track Progress

```bash
# Initial state
python3 -m bridge.bug_cli stats

# After fixes, mark bugs as FIXED
python3 -m bridge.bug_cli update-status 5 fixed
python3 -m bridge.bug_cli update-status 6 fixed

# Check progress
python3 -m bridge.bug_cli stats

# Clean up fixed bugs
python3 -m bridge.bug_cli clear
```

---

## Tips and Best Practices

1. **Check daily for critical bugs:**
   ```bash
   python3 -m bridge.bug_cli list --severity critical --status new --limit 10
   ```

2. **Review system state before fixing:**
   - Always check the `audio_devices` section in `show` output
   - Verify `config_hash` to ensure bug occurred with expected config
   - Check `python_version` and `platform` for environment-specific issues

3. **Export before major changes:**
   ```bash
   python3 -m bridge.bug_cli export /backup/bugs_backup_YYYYMMDD.json
   ```

4. **Use component-specific filters:**
   - `audio_pipeline` - Audio I/O and buffering issues
   - `stt` - Speech-to-Text transcription errors
   - `tts` - Text-to-Speech synthesis issues
   - `websocket` - OpenClaw connection problems
   - `config` - Configuration validation errors

5. **Track duplicate bugs:**
   ```bash
   # Find similar bugs
   python3 -m bridge.bug_cli list --component audio_pipeline --severity critical
   ```

6. **Database location:**
   - Default: `~/.voice-bridge/bugs.db`
   - SQL command-line: `sqlite3 ~/.voice-bridge/bugs.db`

---

## API Integration

The CLI can be integrated into automation scripts:

```bash
#!/bin/bash
# Check for critical bugs and alert if they exist
COUNT=$(python3 -m bridge.bug_cli list --severity critical --status new | grep -c "│")
if [ "$COUNT" -gt 0 ]; then
    echo "ALERT: $COUNT new critical bugs found!"
    # Send notification, create ticket, etc.
fi
```

---

## Troubleshooting

### "No bugs found"
- Database is empty or filters are too restrictive
- Try: `python3 -m bridge.bug_cli list` (no filters)

### "Bug #N not found"
- Bug ID doesn't exist in database
- Check: `python3 -m bridge.bug_cli list --limit 100`

### Import errors
- Ensure PYTHONPATH is set correctly
- Verify source directory structure exists:

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
export PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:$PYTHONPATH
```

### Database locked
- Only one process can write to SQLite at a time
- Close other applications using the database

---

## Related Documentation

- **Implementation:** `src/bridge/bug_tracker.py`
- **Test Script:** `tests/manual_test_bug_tracker.py`
- **System:** `src/bridge/bug_cli.py`
- **Overview:** `BUG_TRACKER.md`

---

## Support

For issues or questions:
1. Check the test script for usage examples
2. Review the implementation in `src/bridge/bug_tracker.py`
3. Export bugs for offline review and sharing

---

**Last Updated:** 2026-02-28
**Version:** 1.0