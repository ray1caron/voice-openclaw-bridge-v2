# Automated Bug Tracking System

**Status:** MVP Feature Complete  
**Location:** `src/bridge/bug_tracker.py`  
**CLI:** `python -m bridge.bug_cli`

---

## Overview

The Voice-OpenClaw Bridge now includes an **automated bug tracking system** that:

1. **Captures errors automatically** when they occur
2. **Records full system context** - Python version, platform, audio devices, config state
3. **Stores locally** in SQLite database (privacy-first)
4. **Auto-files GitHub issues** (optional)
5. **Provides CLI tools** to view, filter, and export bugs

---

## Quick Start

### Basic Usage

```python
from bridge import capture_bug, BugSeverity

try:
    # Your code here
    risky_operation()
except Exception as e:
    # Capture the bug with full context
    bug_id = capture_bug(
        error=e,
        component="audio",
        severity=BugSeverity.HIGH,
        user_context="User was speaking during TTS playback"
    )
    print(f"Bug captured: #{bug_id}")
```

### Global Error Handler

```python
from bridge import install_global_handler, BugTracker

# Install handler to capture ALL uncaught exceptions
tracker = BugTracker.get_instance()
install_global_handler(tracker)

# Now any uncaught exception is automatically captured
# with full stack trace and system state
```

### CLI Commands

```bash
# List recent bugs
python -m bridge.bug_cli list

# Show specific bug
python -m bridge.bug_cli show 42

# List only critical bugs
python -m bridge.bug_cli list --severity critical

# Export to markdown
python -m bridge.bug_cli export bugs.md

# Show statistics
python -m bridge.bug_cli stats
```

---

## What Gets Captured

### Error Information
- Exception type and message
- Full stack trace
- Timestamp
- Component where error occurred
- Severity level (critical, high, medium, low, info)
- User-provided context

### System State
- Python version
- Platform (Linux/Mac/Windows)
- CPU count
- Available memory
- Free disk space
- Audio devices detected
- Config hash (detect config-related bugs)
- Session ID
- Application uptime

### Privacy
- **Local storage only** by default (SQLite)
- **No network calls** unless GitHub integration enabled
- **No user data** captured without explicit context
- Can run completely offline

---

## Integration Points

### In Audio Pipeline

```python
from bridge import AudioPipeline, capture_bug, BugSeverity

class MyAudioPipeline(AudioPipeline):
    def __init__(self):
        super().__init__()
        self._setup_error_handling()
    
    def _setup_error_handling(self):
        """Set up automatic error capture."""
        # Install global handler for uncaught errors
        from bridge import install_global_handler
        install_global_handler()
    
    def capture_device_error(self, device_id: str, error: Exception):
        """Capture audio device errors."""
        capture_bug(
            error=error,
            component="audio",
            severity=BugSeverity.HIGH,
            user_context=f"Device ID: {device_id}",
        )
```

### In WebSocket Client

```python
from bridge import OpenClawWebSocketClient, capture_bug

class BugTrackingWebSocketClient(OpenClawWebSocketClient):
    def __init__(self, config):
        super().__init__(config=config)
        self.tracker = BugTracker.get_instance()
    
    async def connect(self):
        try:
            return await super().connect()
        except Exception as e:
            self.tracker.capture_error(
                error=e,
                component="websocket",
                severity=BugSeverity.CRITICAL,
                user_context="Failed to connect to OpenClaw",
            )
            raise
```

### In Tool Chain Manager

```python
from bridge import ToolChainManager, capture_bug, BugSeverity

class BugTrackingToolChainManager(ToolChainManager):
    def on_tool_error(self, tool_name: str, error: Exception):
        """Capture tool execution errors."""
        capture_bug(
            error=error,
            component="tools",
            severity=BugSeverity.HIGH,
            user_context=f"Tool: {tool_name}",
        )
```

---

## Configuration

### Database Location

By default, bugs are stored in:
- `~/.voice-bridge/bugs.db`

You can customize:

```python
from bridge import BugTracker
from pathlib import Path

tracker = BugTracker(
    db_path=Path("/var/log/bridge/bugs.db"),
    github_token="ghp_...",  # Optional
)
```

### GitHub Integration

To auto-file GitHub issues:

```python
import os
from bridge import BugTracker

tracker = BugTracker(
    github_token=os.getenv("GITHUB_TOKEN"),
)

# Now capture_bug will auto-create GitHub issues
capture_bug(error, "audio", BugSeverity.CRITICAL, auto_file_github=True)
```

---

## CLI Reference

### `bug_cli list`

List bugs with filtering.

**Options:**
- `--status new|triaged|in_progress|fixed|closed`
- `--severity critical|high|medium|low|info`
- `--component audio|stt|tts|bridge|...`
- `--limit N` (default: 50)

**Examples:**
```bash
# List only critical audio bugs
python -m bridge.bug_cli list --severity critical --component audio

# List 100 most recent bugs
python -m bridge.bug_cli list --limit 100
```

### `bug_cli show ID`

Show detailed view of a specific bug.

```bash
python -m bridge.bug_cli show 42
```

Output includes:
- Full title and description
- Severity with color coding
- Stack trace
- System state (Python version, platform, etc.)
- Creation timestamp

### `bug_cli stats`

Show bug statistics.

```bash
python -m bridge.bug_cli stats
```

Output:
```
Bug Statistics
┏━━━━━━━━━━━━━━━━━┳━━━━━━━━┓
┃ Metric          ┃ Count  ┃
┡━━━━━━━━━━━━━━━━━╇━━━━━━━━┩
│ Total Bugs      │ 47     │
│ New (unread)    │ 12     │
│ Fixed           │ 28     │
│ Critical        │ 3      │
└─────────────────┴────────┘
```

### `bug_cli export`

Export bugs to file.

```bash
# Export to JSON
python -m bridge.bug_cli export bugs.json

# Export to Markdown (great for reports)
python -m bridge.bug_cli export bugs.md
```

---

## Severity Levels

| Level | Use Case | Auto-File GitHub | Notification |
|-------|----------|------------------| ------------|
| **CRITICAL** | Crash, data loss, security breach | ✅ Yes | ✅ Alert |
| **HIGH** | Feature broken, bad UX | ⚠️ Optional | ⚠️ Log |
| **MEDIUM** | Annoyance, workaround exists | ❌ No | ⚠️ Log |
| **LOW** | Cosmetic, minor | ❌ No | ❌ Silent |
| **INFO** | Telemetry only | ❌ No | ❌ Silent |

---

## Workflow

### Development Phase

1. **Run with global handler** to capture all errors
2. **Review bugs via CLI** after each session
3. **Fix bugs** in order: CRITICAL → HIGH → MEDIUM
4. **Mark fixed** in bug tracker

### Production Phase

1. **Auto-capture** all errors silently
2. **Weekly review** of bug database
3. **Weekly export** to markdown for team review
4. **Critical bugs** auto-file GitHub issues
5. **Trend analysis** to find common failure patterns

---

## Database Schema

```sql
CREATE TABLE bugs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    severity TEXT NOT NULL,
    component TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    stack_trace TEXT,
    system_state TEXT NOT NULL,  -- JSON
    user_context TEXT,
    status TEXT NOT NULL DEFAULT 'new',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    github_issue INTEGER
);

-- Indexes for fast queries
CREATE INDEX idx_severity ON bugs(severity);
CREATE INDEX idx_status ON bugs(status);
CREATE INDEX idx_component ON bugs(component);
```

---

## Advanced Usage

### Custom Bug Tracker

```python
from bridge.bug_tracker import BugTracker, BugStatus

class CustomBugTracker(BugTracker):
    def on_bug_captured(self, bug_id: int):
        """Called when bug is captured."""
        # Send to external system
        bug = self.get_bug(bug_id)
        send_to_datadog(bug)
        
    def update_status(self, bug_id: int, status: BugStatus):
        """Update bug status with logging."""
        super().update_status(bug_id, status)
        logger.info(f"Bug #{bug_id} status → {status.value}")
```

### Bulk Operations

```python
# Get all critical audio bugs
critical_audio = tracker.list_bugs(
    severity=BugSeverity.CRITICAL,
    component="audio"
)

# Export for team review
tracker.export_to_file(Path("review.md"), format="markdown")

# Mark all as triaged
for bug in critical_audio:
    tracker.update_status(bug.id, BugStatus.TRIAGED)
```

---

## Troubleshooting

### No bugs showing up

Check:
1. Is `capture_bug()` being called?
2. Check database path: `~/.voice-bridge/bugs.db`
3. Verify permissions: `ls -la ~/.voice-bridge/`

### GitHub issues not creating

Check:
1. GitHub token has `repo` scope
2. Repository exists and is accessible
3. Token not expired: `echo $GITHUB_TOKEN`

### Global handler not capturing

Ensure `install_global_handler()` is called early:

```python
def main():
    # Install FIRST
    install_global_handler()
    
    # Then run app
    run_app()
```

---

## Future Enhancements

- [ ] Web dashboard for viewing bugs
- [ ] Automatic error classification with ML
- [ ] Integration with Sentry/Errorception
- [ ] Email notifications for critical bugs
- [ ] Weekly bug report generation
- [ ] Duplicate bug detection

---

## API Reference

### BugTracker

```python
t = BugTracker(db_path=None, github_token=None)

t.capture_error(error, component, severity, user_context=None)
t.get_bug(bug_id) -> Optional[BugReport]
t.list_bugs(status=None, severity=None, component=None, limit=100)
t.update_status(bug_id, status)
t.export_to_file(path, format="json")
t.get_stats() -> dict
```

### Severity Enum

```python
class BugSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"
```

### Status Enum

```python
class BugStatus(Enum):
    NEW = "new"
    TRIAGED = "triaged"
    IN_PROGRESS = "in_progress"
    FIXED = "fixed"
    CLOSED = "closed"
    DUPLICATE = "duplicate"
```

---

## Examples

### Capture STT Error

```python
from bridge import STTEngine, capture_bug, BugSeverity

class STTEngineWithBugTracking(STTEngine):
    def transcribe(self, audio):
        try:
            return super().transcribe(audio)
        except Exception as e:
            capture_bug(
                error=e,
                component="stt",
                severity=BugSeverity.HIGH,
                user_context=f"Audio length: {len(audio)} samples",
            )
            raise
```

### Capture Config Error

```python
from bridge import AppConfig, capture_bug, BugSeverity

try:
    config = AppConfig.load()
except ValidationError as e:
    capture_bug(
        error=e,
        component="config",
        severity=BugSeverity.HIGH,
        user_context="Config validation failed on load",
    )
    raise
```

### Capture Timeout Error

```python
from bridge import capture_bug, BugSeverity

try:
    result = await asyncio.wait_for(operation(), timeout=5.0)
except asyncio.TimeoutError as e:
    capture_bug(
        error=e,
        component="async",
        severity=BugSeverity.MEDIUM,
        user_context=f"Operation timed out after 5s",
    )
    raise
```

---

## Conclusion

The Bug Tracker provides:

- ✅ **Zero-config** - Works out of the box
- ✅ **Privacy-first** - Local SQLite storage
- ✅ **Full context** - Captures everything needed to debug
- ✅ **GitHub integration** - Optional auto-filing
- ✅ **CLI tooling** - Easy viewing and management

**Start using it today** to never lose track of another bug!

---

*Last Updated: 2026-02-22*
