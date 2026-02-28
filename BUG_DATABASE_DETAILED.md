# Bug Database Detailed View - Phase 5

**Requirement:** Show bugs with environment, stack traces, and fix data

## Commands Executed

1. ✅ `bug_cli show 1` - Detailed view of bug #1 with full context
2. ✅ `bug_cli show 10` - Detailed view of bug #10 (for comparison)
3. ✅ `bug_cli export /tmp/bugs_output.json` - Export all bugs to JSON

## Expected Output

Each bug should include:

### Bug Information
- **ID**: Unique bug identifier
- **Severity**: CRITICAL, HIGH, MEDIUM, LOW, INFO
- **Component**: System component where error occurred
- **Status**: NEW, TRIAGED, IN_PROGRESS, FIXED, CLOSED, DUPLICATE
- **Title**: Brief description
- **Timestamp**: When the error occurred
- **Created At**: When bug was captured
- **Stack Trace**: Full Python stack trace
- **Description**: Error details

### System Snapshot (Environment Data)
- **Python Version**: Runtime Python version
- **Platform**: OS and architecture
- **CPU Count**: Number of CPUs
- **Memory Available**: Free memory in bytes
- **Disk Free**: Free disk space in bytes
- **Audio Devices**: List of audio devices with names and channels
- **Config Hash**: Hash of current configuration
- **Session ID**: Current session identifier
- **Uptime Seconds**: System uptime

### User Context
- Additional context provided when bug was captured
- Custom attributes
- Any relevant user data

### Fix Data (if available)
- GitHub Issue ID (if filed)
- Resolution notes
- Fix timestamp
- Status updates

**Awaiting detailed bug output...**