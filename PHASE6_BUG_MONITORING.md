# Phase 6 Bug Monitoring Instructions

**During Phase 6 Quality Assurance testing:**

## Bug Database Monitoring

**Quick Check:**
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:$PYTHONPATH
python3 scripts/monitor_bugs.py --once
```

**Check After Each Test Suite:**
- After unit tests
- After integration tests
- After E2E tests
- After performance tests

**Look For:**
- Any NEW bugs created during testing
- CRITICAL severity bugs
- Bugs in components being tested

---

## What to Report

**If New Bugs Found:**
1. Count of new bugs
2. Severity levels
3. Components affected
4. Bug IDs and titles

**Example Alert Format:**
```
🚨 X new bugs detected during [test suite]
- CRITICAL: X bugs
- HIGH: X bugs
- Bug IDs: #1, #2, #3
```

---

**Monitor bug database throughout Phase 6 testing**