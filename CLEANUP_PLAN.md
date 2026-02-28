# Workspace Cleanup Plan - Before Phase 7

**Date:** 2026-02-28
**Time:** 3:18 PM PST
**Purpose:** Clean old files before Phase 7 release

---

## Backup Status

✅ **BACKUP COMPLETE**
- Backup folder: /homes/hal/clawbot-backup/clawbot-backup-2026-02-28_15-17-25
- Files copied: 83

---

## Cleanup Strategy

### Files to DELETE (Old status/planning files)

These are intermediate Phase 6 files that are now consolidated:

```
AUDIO_FILE_ANALYSIS.md
BUG_MONITORING_ACTIVE.md
BUG_MONITORING_SETUP.md
CODE_FINDINGS_PRELIM.md
CODE_REVIEW_PLAN.md
CODE_REVIEW_STATUS.md
PHASE6_BUG_MONITORING.md
PHASE6_COMPLETE.md
PHASE6_DONE.md
PHASE6_INTEGRATION_TEST_RESULTS.md
PHASE6_MID_UPDATE.md
PHASE6_PROGRESS_REPORT.md
PHASE6_QUICK_NOTES.md
PHASE6_REGRESSION_COMPLETE.md
PHASE6_REGRESSION_ISSUES.md
PHASE6_STATUS.md
PHASE6_UNIT_TEST_RESULTS.md
SECURITY_PRELIMINARY.md
SECURITY_REVIEW_CORRECTED.md
SECURITY_REVIEW_PLAN.md
SECURITY_REVIEW_STATUS.md
TTS_IMPLEMENTATION_COMPLETE.md
E2E_TEST_REAL_AUDIO.md
TESTS_IN_PROGRESS.md
TESTS_RUNNING.md
```

### Files to KEEP (Final deliverables)

```
CODE_ISSUES_FOUND.md
CODE_REVIEW_SUMMARY.md
PERFORMANCE_METRICS.md
PERFORMANCE_REVIEW_SUMMARY.md
PERFORMANCE_STATUS.md
SECURITY_ISSUES_FOUND.md
SECURITY_REVIEW_SUMMARY.md
TODO_FIXME_INVENTORY.md
```

### Files to KEEP (Phase documentation)

```
PHASE6_SECURITY_COMPLETE.md
PHASE6_SECURITY_SUMMARY.md
PHASE6_PERFORMANCE_COMPLETE.md
PHASE6_PROGRESS_6.1-6.4.md
PHASE6_5_PLAN.md
PHASE6_5_STATUS.md
PHASE6_5_COMPLETE.md
PHASE6_COMPLETE_FINAL.md
```

### Files to KEEP (Core documentation - Already exist)

```
README.md (will update in Phase 7)
INSTALL.md (will update in Phase 7)
USER_GUIDE.md (will update in Phase 7)
BUG_TRACKER.md (BUG TRACKER USER GUIDE - WILL INCLUDE IN RELEASE)
```

---

## Cleanup Actions

### Step 1: Delete old status files (22 files)

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
rm -f AUDIO_FILE_ANALYSIS.md
rm -f BUG_MONITORING_ACTIVE.md
rm -f BUG_MONITORING_SETUP.md
rm -f CODE_FINDINGS_PRELIM.md
rm -f CODE_REVIEW_PLAN.md
rm -f CODE_REVIEW_STATUS.md
rm -f PHASE6_BUG_MONITORING.md
rm -f PHASE6_COMPLETE.md
rm -f PHASE6_DONE.md
rm -f PHASE6_INTEGRATION_TEST_RESULTS.md
rm -f PHASE6_MID_UPDATE.md
rm -f PHASE6_PROGRESS_REPORT.md
rm -f PHASE6_QUICK_NOTES.md
rm -f PHASE6_REGRESSION_COMPLETE.md
rm -f PHASE6_REGRESSION_ISSUES.md
rm -f PHASE6_STATUS.md
rm -f PHASE6_UNIT_TEST_RESULTS.md
rm -f SECURITY_PRELIMINARY.md
rm -f SECURITY_REVIEW_CORRECTED.md
rm -f SECURITY_REVIEW_PLAN.md
rm -f SECURITY_REVIEW_STATUS.md
rm -f TTS_IMPLEMENTATION_COMPLETE.md
rm -f E2E_TEST_REAL_AUDIO.md
rm -f TESTS_IN_PROGRESS.md
rm -f TESTS_RUNNING.md
```

### Step 2: Delete temporary test files

```bash
rm -f BUG_MONITORING_ACTIVE.md
rm -f CODE_STATS.md
```

### Step 3: Commit cleanup

```bash
git add -A
git commit -m "chore: Clean workspace before Phase 7 release

- Remove 24 intermediate Phase 6 status files
- Keep final deliverables only
- Clean workspace for release packaging"
```

---

## Bug Tracker User Guide

**File:** `BUG_TRACKER.md` (Already exists - WILL BE INCLUDED IN RELEASE)

**Content to Verify:**
- Installation guide
- CLI usage (python -m bridge.bug_cli)
- Database location
- Common operations
- GitHub integration (optional)

---

## After Cleanup

Before Phase 7 starts, workspace will be clean with only:
- ✅ Core source code
- ✅ Final test results
- ✅ Final Phase 6 documentation
- ✅ Core project documentation (README, INSTALL, USER_GUIDE)
- ✅ BUG_TRACKER.md (for release package)

---

**Cleanup ready to execute**