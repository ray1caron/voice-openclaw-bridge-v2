# Phase 1 Setup Guide - Fix Failing E2E Tests

**Objective:** Get 8/8 E2E tests passing (100% pass rate)
**Duration:** 4 hours
**Status:** Ready to start

---

## Current Status

**Last Test Run:** Unknown (need to run fresh)
**Passing:** 5/8 tests (62.5%)
**Failing:** 2 tests
  1. `test_barge_in_during_tts` - Assertion error: `assert 0 == 1`
  2. `test_error_handling` - Unclear failure mode

---

## GitHub Connection Status

**Repository:** https://github.com/ray1caron/voice-openclaw-bridge-v2
**Current Branch:**master**
**Unpushed Commits:** 35+
**Remote:** Configured with embedded token

---

## Phase 1 Steps

### Step 1.1: Diagnose `test_barge_in_during_tts` (1 hour)

**Command:**
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
python3 -m pytest tests/integration/test_voice_e2e.py::test_barge_in_during_tts -vvvs
```

**Diagnosis Checklist:**
- [ ] Identify which assertion is failing (line number)
- [ ] Check `interrupted_interactions` counter logic
- [ ] Verify BargeInHandler is properly counting interactions
- [ ] Confirm interrupt signal propagates to orchestrator
- [ ] Check if interrupt is being triggered at all

**Expected Root Causes (in order of likelihood):**
1. BargeInHandler not incrementing `interrupted_interactions`
2. Interrupt signal not reaching Voice Orchestrator
3. Test expectation incorrect
4. Race condition in async code

---

### Step 1.2: Fix `test_barge_in_during_tts` (1 hour)

**Potential Fixes:**

**If BargeInHandler not counting:**
```python
# In src/audio/barge_in.py, BargeInHandler class
# Ensure this method exists and is called:
async def on_interrupt(self) -> None:
    """Called when interruption detected."""
    self.interrupted_interactions += 1  # ADD THIS IF MISSING
    self.state = BargeInState.LISTENING
    # ... rest of interrupt logic
```

**If signal not propagating:**
```python
# In src/bridge/voice_orchestrator.py
# Ensure interrupt handler wiring:
self.barge_in_handler.set_interrupt_callback(
    lambda: self.handle_interrupt()  # ADD THIS IF MISSING
)
```

**If test expectation wrong:**
```python
# In tests/integration/test_voice_e2e.py
# Verify assert matches actual behavior:
assert orchestrator.stats.interrupted_interactions == 1  # MAY NEED ADJUSTMENT
```

**After Fix:**
```bash
# Verify fix with single test
python3 -m pytest tests/integration/test_voice_e2e.py::test_barge_in_during_tts -v

# If passes, run full E2E suite to ensure no regression
python3 -m pytest tests/integration/test_voice_e2e.py -v
```

---

### Step 1.3: Diagnose `test_error_handling` (1 hour)

**Command:**
```bash
# Run with verbose and show full output
python3 -m pytest tests/integration/test_voice_e2e.py::test_error_handling -vvvs
```

**Diagnosis Checklist:**
- [ ] Identify error type (connection, STT, TTS, timeout)
- [ ] Check error handler in Voice Orchestrator
- [ ] Verify error recovery logic exists
- [ ] Confirm test is triggering expected error scenario

---

### Step 1.4: Fix `test_error_handling` (1 hour)

**Potential Fixes:**

**If error handler not catching exceptions:**
```python
# In src/bridge/voice_orchestrator.py
try:
    result = await self.stt_worker.transcribe(audio_data)
except Exception as e:
    logger.error(f"STT failed: {e}")
    await self.error_callback(ErrorEvent(error=e, source="stt"))
    # Fallthrough to recovery logic
```

**If recovery not implemented:**
```python
# Add recovery logic that tests expect
async def handle_error(self, error: ErrorEvent) -> None:
    """Handle error and attempt recovery."""
    self.statistics.error_count += 1

    if error.source == "stt":
        # Fallback: ask user to repeat
        await self.response_callback("I didn't hear that. Please repeat.")
    elif error.source == "network":
        # Trigger reconnection
        await self._reconnect()
```

---

### Step 1.5: Verify All E2E Tests Pass (30 minutes)

**Command:**
```bash
# Run full E2E test suite 3 times to ensure stability
for i in {1..3}; do
    echo "Run $i:"
    python3 -m pytest tests/integration/test_voice_e2e.py -v
    echo "---"
done
```

**Expected Output:** All 8 tests pass, 3 times in a row

---

## Files to Review

Before starting, review these files:

1. **Test File:**
   - `/home/hal/.openclaw/workspace/voice-bridge-v2/tests/integration/test_voice_e2e.py`
   - Focus on `test_barge_in_during_tts` and `test_error_handling`

2. **Voice Orchestrator:**
   - `/home/hal/.openclaw/workspace/voice-bridge-v2/src/bridge/voice_orchestrator.py`
   - Check interrupt handling and error recovery

3. **Barge-In Handler:**
   - `/home/hal/.openclaw/workspace/voice-bridge-v2/src/audio/barge_in.py`
   - Verify `interrupted_interactions` counter

---

## Expected Deliverables

**Phase 1 Completion:**
- [ ] `test_barge_in_during_tts` fixed and passing
- [ ] `test_error_handling` fixed and passing
- [ ] 8/8 E2E tests passing (100%)
- [ ] Test suite run 3 times consecutively, all pass
- [ ] `RESULTS_E2E_PH1.md` created with detailed results
- [ ] Phase 1 complete timestamp recorded

**Phase 1 Deliverable:** E2E tests at 100% pass rate

---

## Quick Reference Commands

```bash
# Run single failing test with verbose output
python3 -m pytest tests/integration/test_voice_e2e.py::test_barge_in_during_tts -vvvs

# Run single failing test with error output
python3 -m pytest tests/integration/test_voice_e2e.py::test_error_handling -vvvs

# Run all E2E tests
python3 -m pytest tests/integration/test_voice_e2e.py -v

# Run with coverage
python3 -m pytest tests/integration/test_voice_e2e.py --cov=src

# Run and show output in real time
python3 -m pytest tests/integration/test_voice_e2e.py -v -s
```

---

## Next Phase Preview

After Phase 1 is complete, proceed to **Phase 2: Real Hardware Validation** (1 day)

---

**Document Version:** 1.0
**Created:** 2026-02-28 12:07 PM PST
**Status:** Ready for Execution