# Phase 6.5 Bug Fixes - Starting

**Date:** 2026-02-28
**Time:** 3:06 PM PST
**Step:** 6.5 Bug Fixes & Testing
**Status:** ⏳ STARTING

---

## Bugs to Fix

From Code Review (Phase 6.2):

### MEDIUM Priority Issues (2)

**Issue MEDIUM-001:**
- **File:** `src/bridge/bug_tracker.py`
- **Line:** 77
- **Type:** Error Handling
- **Issue:** Bare `except` clause
- **Severity:** MEDIUM
- **Estimated Time:** 5 minutes

**Issue MEDIUM-002:**
- **File:** `src/bridge/bug_tracker.py`
- **Line:** 87
- **Type:** Error Handling
- **Issue:** Bare `except` clause
- **Severity:** MEDIUM
- **Estimated Time:** 5 minutes

---

## Fix Plan

### Step 1: Fix Bare Except Clauses (10 min)

**Before:**
```python
try:
    # some code
except:  # Line 77, 87
    # bare except
```

**After:**
```python
try:
    # some code
except sqlite3.DatabaseError as e:
    logger.error(f"Database error: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

**Benefits:**
- Catches specific exceptions
- Logs errors properly
- Doesn't catch KeyboardInterrupt/SystemExit
- Better debugging

---

### Step 2: Verify Fixes (5 min)

**Run Tests:**
```bash
python3 -m pytest tests/ -k "bug_tracker" -v
```

**Expected:** All bug tracker tests pass

---

### Step 3: Optional - Review Print Statements (15 min)

**Issues:** 4 print statements in `audio_discovery.py`

**Assessment:** Acceptable for CLI utility

**Decision:** Document, no changes needed

---

### Step 4: Optional - Document TODOs (15 min)

**TODOs Remaining (2):**
1. Delete bug feature in bug_cli.py
2. OpenClaw context integration

**Action:** Already documented in TODO_FIXME_INVENTORY.md

**Decision:** No action needed, roadmap exists

---

## Expected Outcomes

**After Fixes:**
- 0 MEDIUM issues remaining
- All bug tracker tests pass
- No regressions introduced
- Production-ready code

---

## Deliverable

**Bug Fixes Summary:**
- `BUG_FIXES_APPLIED.md` - Documentation of fixes

---

## Timeline

| Activity | Duration | Status |
|----------|----------|--------|
| Fix bare except clauses (2) | 10 min | ⏸ NEXT |
| Run bug tracker tests | 5 min | ⏸ PENDING |
| Verify no regressions | 5 min | ⏸ PENDING |
| Document fixes | 5 min | ⏸ PENDING |

**Total Estimated:** 25 minutes (under 6-hour budget)

---

**Starting bug fixes**