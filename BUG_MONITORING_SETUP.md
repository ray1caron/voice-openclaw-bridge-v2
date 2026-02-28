# Bug Database Monitoring - Setup

**Date:** 2026-02-28
**Time:** 2:12 PM PST
**Purpose:** Real-time monitoring of bug database for new bug reports

---

## Monitoring Script

**Location:** `scripts/monitor_bugs.py`

**Features:**
- ✅ Check current bug database statistics
- ✅ Identify NEW (unread) bugs
- ✅ Filter for recent bugs (last hour)
- ✅ Display bug details (ID, title, severity, component)
- ✅ Continuous monitoring mode
- ✅ One-time check mode

---

## Usage

**Check Once:**
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:$PYTHONPATH
python3 scripts/monitor_bugs.py --once
```

**Continuous Monitoring:**
```bash
# Check every 5 minutes (default)
python3 scripts/monitor_bugs.py

# Check every 1 minute
python3 scripts/monitor_bugs.py --interval 60

# Check every 10 minutes
python3 scripts/monitor_bugs.py --interval 600
```

---

## What Gets Monitored

**Database Statistics:**
- Total bugs in database
- New (unread) bugs
- Recent bugs (created in last hour)

**New Bug Alerts:**
- Bug ID
- Title
- Severity (CRITICAL, HIGH, MEDIUM, LOW, INFO)
- Component (audio, websocket, stt, tts, etc.)
- Creation time
- Age (minutes/hours since creation)
- Description snippet

---

## Monitoring Integration

**For Phase 6 Testing:**
- Run monitor in background during regression tests
- Catch any bugs generated during testing
- Alert immediately if new bugs appear

**For Production:**
- Run as daemon service
- Email/SMS notifications for CRITICAL bugs
- Dashboard integration

---

## Quick Reference

**Status Check:** `python3 scripts/monitor_bugs.py --once`
**Monitor Mode:** `python3 scripts/monitor_bugs.py`
**Exit Monitoring:** Ctrl+C

---

**Bug database monitoring configured - first check running now**