# GitHub Phase 1 Development Checklist

**Repository:** https://github.com/ray1caron/voice-openclaw-bridge-v2
**Current Branch:**master**
**Phase:** 1 - Fix Failing E2E Tests
**Target Date:** 2026-02-28 (Today)
**Status:** SETUP COMPLETE ✅

---

## Pre-Flight Checklist

### GitHub Connection
- [x] Repository configured (`ray1caron/voice-openclaw-bridge-v2`)
- [x] Remote URL with token embedded
- [ ] Verify git status (pending approval)
- [ ] Check unpushed commits (pending approval)
- [ ] Verify current branch (pending approval)

### Development Environment
- [x] Phase 1 Setup Guide created (`PHASE1_SETUP.md`)
- [x] Results template created (`RESULTS_E2E_PH1.md`)
- [x] Diagnostic script created (`scripts/diagnose_e2e.sh`)
- [ ] Make diagnostic script executable (pending)

---

## Phase 1 Tasks

### Task 1.1: Run Diagnostic Script
**Status:** ❌ NOT STARTED

**Commands:**
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
chmod +x scripts/diagnose_e2e.sh
./scripts/diagnose_e2e.sh
```

**Acceptance:**
- [ ] Diagnostic script runs without errors
- [ ] All 3 diagnostic files generated
- [ ] Results reviewed and logged

**Output Files:**
- `/tmp/phase1_diagnostics/barge_in_diagnostic_<timestamp>.txt`
- `/tmp/phase1_diagnostics/error_handling_diagnostic_<timestamp>.txt`
- `/tmp/phase1_diagnostics/e2e_baseline_<timestamp>.txt`

---

### Task 1.2: Analyze `test_barge_in_during_tts` Failure
**Status:** ❌ NOT STARTED

**Diagnosis:**
- [ ] Identify failing assertion line number
- [ ] Check `interrupted_interactions` variable
- [ ] Verify BargeInHandler implementation
- [ ] Confirm signal propagation path
- [ ] Document root cause in `RESULTS_E2E_PH1.md`

**Test File Location:**
`tests/integration/test_voice_e2e.py::test_barge_in_during_tts`

**Key Code to Review:**
- `src/audio/barge_in.py` - BargeInHandler class
- `src/bridge/voice_orchestrator.py` - Interrupt handling
- Test assertion at end of test function

---

### Task 1.3: Fix `test_barge_in_during_tts`
**Status:** ❌ NOT STARTED

**Action Items:**
- [ ] Apply fix based on diagnosis
- [ ] Test fix with single test
- [ ] Run full E2E suite to check regression
- [ ] Document fix in comments
- [ ] Update `RESULTS_E2E_PH1.md`

**Files to Modify:**
- [ ] `src/audio/barge_in.py` (if missing counter)
- [ ] `src/bridge/voice_orchestrator.py` (if signal not propagating)
- [ ] `tests/integration/test_voice_e2e.py` (if expectation wrong, last resort)

---

### Task 1.4: Analyze `test_error_handling` Failure
**Status:** ❌ NOT STARTED

**Diagnosis:**
- [ ] Identify error type from verbose output
- [ ] Check error handler implementation
- [ ] Verify error recovery logic
- [ ] Confirm test triggers error scenario
- [ ] Document root cause in `RESULTS_E2E_PH1.md`

**Test File Location:**
`tests/integration/test_voice_e2e.py::test_error_handling`

**Key Code to Review:**
- `src/bridge/voice_orchestrator.py` - Error handling
- Exception handling blocks
- on_error callback

---

### Task 1.5: Fix `test_error_handling`
**Status:** ❌ NOT STARTED

**Action Items:**
- [ ] Apply fix based on diagnosis
- [ ] Test fix with single test
- [ ] Run full E2E suite to check regression
- [ ] Document fix in comments
- [ ] Update `RESULTS_E2E_PH1.md`

**Files to Modify:**
- [ ] `src/bridge/voice_orchestrator.py` (error handling)
- [ ] `tests/integration/test_voice_e2e.py` (if test expectation wrong, last resort)

---

### Task 1.6: Verify All E2E Tests Pass
**Status:** ❌ NOT STARTED

**Commands:**
```bash
# Run 3 times consecutively
for i in {1..3}; do
    echo "Run $i:"
    python3 -m pytest tests/integration/test_voice_e2e.py -v
    echo "---"
done
```

**Acceptance Criteria:**
- [ ] Run 1: 8/8 tests passing
- [ ] Run 2: 8/8 tests passing
- [ ] Run 3: 8/8 tests passing
- [ ] No flaky behavior
- [ ] Duration reasonable (< 60s per run)

---

### Task 1.7: Complete Documentation
**Status:** ❌ NOT STARTED

**Documentation Updates:**
- [ ] Update `RESULTS_E2E_PH1.md` with final results
- [ ] Document all changes made
- [ ] Add comments to code for fixes
- [ ] Record completion timestamp

---

### Task 1.8: Commit Phase 1 Changes
**Status:** ❌ NOT STARTED

**Git Workflow:**
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2

# Check status
git status

# Add changes
git add -A

# Commit
git commit -m "phase-1: Fix E2E test failures

- Fixed test_barge_in_during_tts assertion
- Fixed test_error_handling error recovery
- All 8 E2E tests now passing (100%)
- Verified with 3 consecutive runs

Closes #ISSUE_NUMBER (if applicable)"
```

**Items to Commit:**
- [ ] Modified source files
- [ ] Updated test results
- [ ] Phase 1 documentation

---

## Post-Phase 1 Actions

### Before Proceeding to Phase 2
- [ ] Review changes with `git diff`
- [ ] Confirm commit message is accurate
- [ ] Update memory/YYYY-MM-DD.md with Phase 1 summary
- [ ] Create status update for user

### Not Required (Will Come Later)
- [ ] Push to GitHub (wait until Phase 3)
- [ ] Create release tag (wait until Phase 6)
- [ ] Update CHANGELOG.md (wait until Phase 6)

---

## Quick Reference

### Test Commands
```bash
# Single test with max verbosity
python3 -m pytest tests/integration/test_voice_e2e.py::test_barge_in_during_tts -vvvs

# Run all E2E tests
python3 -m pytest tests/integration/test_voice_e2e.py -v

# Run with coverage
python3 -m pytest tests/integration/test_voice_e2e.py --cov=src

# Run stability test (3 times)
for i in {1..3}; do python3 -m pytest tests/integration/test_voice_e2e.py -v; done
```

### File Locations
- Test file: `tests/integration/test_voice_e2e.py`
- Voice Orchestrator: `src/bridge/voice_orchestrator.py`
- Barge-In Handler: `src/audio/barge_in.py`
- Setup guide: `PHASE1_SETUP.md`
- Results template: `RESULTS_E2E_PH1.md`
- Diagnostic script: `scripts/diagnose_e2e.sh`

---

## Progress Summary

**Tasks Completed:** 0/8 (0%)
**Active Tasks:** None
**Blocked Issues:** None
**Estimated Time Remaining:** 4 hours

---

**Last Updated:** 2026-02-28 12:07 PM PST
**Next Review:** After Task 1.1 (Diagnostic Script)
**Phase 1 Target:** Complete by end of day 2026-02-28