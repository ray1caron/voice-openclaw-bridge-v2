# End-to-End Testing - Import Fixes and Test Execution

**Version:** 0.2.0
**Date/Time:** 2026-02-27 12:45 PST
**Purpose:** Fix import errors in E2E tests and run them

---

## Issue Identified ❌

E2E tests failed with import errors:

```
ModuleNotFoundError: No module named 'audio_pipeline'
ModuleNotFoundError: No module named 'audio' (for audio.wake_word, etc.)
```

**Root Cause:**
E2E tests using incorrect import paths:
```python
from audio.wake_word import WakeWordEvent  # ❌ Wrong
from audio.stt_worker import TranscriptionResult  # ❌ Wrong
from audio_pipeline  # ❌ Wrong
```

**Correct paths:**
```python
from bridge.audio.wake_word import WakeWordEvent  # ✅ Correct
from bridge.audio.stt_worker import TranscriptionResult  # ✅ Correct
from bridge.audio_pipeline  # ✅ Correct
```

---

## Fixes Applied ✅

### 1. Updated test_voice_e2e.py ✅
- Fixed imports to use `bridge.audio.` prefix
- Updated `audio_pipeline` to `bridge.audio_pipeline`
- 7 imports fixed total

### 2. Created run_e2e.py ✅
- Helper script that sets PYTHONPATH correctly
- Adds `src/` to Python path before running tests

### 3. Test Execution with PYTHONPATH ⏸️
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
PYTHONPATH=src:$PYTHONPATH python3 -m pytest tests/integration/test_voice_e2e.py -v
```

**Awaiting approval:** exec id ab3106f1

---

## Expected Test Results

With correct imports and PYTHONPATH, the 7 E2E tests should:

| Test | Expected Result |
|------|----------------|
| Full interaction flow | ✅ Pass |
| Barge-in interruption | ✅ Pass |
| Multiple interactions | ✅ Pass |
| Error handling | ✅ Pass |
| Callback system | ✅ Pass |
| Statistics aggregation | ✅ Pass |
| Performance benchmarks | ✅ Pass |

**Total:** 7 tests, all passing

---

## Why Imports Were Wrong

**Unit tests work because:**
```python
@patch("audio.stt_worker.WhisperModel")  # Mocks applied FIRST
def test_init(self, mock_model):
    from audio.stt_worker import STTWorker  # Then import with mock
```

**E2E tests fail because:**
```python
# Imports at MODULE LEVEL (before any mocks)
from audio.wake_word import WakeWordEvent  # ❌ Wrong path
from audio.stt_worker import TranscriptionResult  # ❌ Wrong
```

**Correct E2E approach:**
```python
# Import at module level with correct path
from bridge.audio.wake_word import WakeWordEvent  # ✅
from bridge.audio.stt_worker import TranscriptionResult  # ✅
```

Or:
```python
# Imports inside test functions
from bridge.audio.wake_word import WakeWordEvent  # ✅
```

---

## Current Status

- ✅ Import errors identified
- ✅ Imports fixed in test_voice_e2e.py
- ✅ Helper script created (run_e2e.py)
- ✅ TEST_ENV requirements updated in SYSTEM_TEST_PLAN.md
- ✅ Test audio fixtures created (8 files)
- ⏸️ Test execution queued with PYTHONPATH fix
- ⏸️ Git commit pending (after tests pass)

---

## Execution Plan

### Queued Actions:
1. ⏸️ Run tests with PYTHONPATH (awaiting approval: id ab3106f1)
2. ⏸️ Verify all 7 tests pass
3. ⏸ Commit test fixes
4. ⏸️ Push to GitHub
5. ⏸️ Update SYSTEM_TEST_PLAN.md with results

---

## Alternative: Run Tests Directly

If the queued command fails, run manually:

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2

# Method 1: PYTHONPATH
PYTHONPATH=src:$PYTHONPATH python3 -m pytest tests/integration/test_voice_e2e.py -v

# Method 2: Using helper script
python3 run_e2e.py

# Method 3: From src directory
cd src && python3 -m pytest ../tests/integration/test_voice_e2e.py -v
```

---

**Status:** ⏸️ Test execution queued with import fixes
**Next:** Await test results, commit fixes if tests pass
**Documentation:**
- SYSTEM_TEST_PLAN.md ✅ Updated
- TEST_AUDIO_FIXTURES_ADDED.md ✅ Created
- E2E_TESTING_SETUP_COMPLETE.md ✅ Created

**Ready for:** Test execution and verification