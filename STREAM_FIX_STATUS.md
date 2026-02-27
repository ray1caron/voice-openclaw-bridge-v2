# Quick Status - Stream Parameter Fix

**Issue:** mock_tts() functions missing 'stream' parameter

**Fix needed:** Add `stream=True` to all mock_tts function definitions

**Example:**
```python
# BEFORE:
async def mock_tts(text):
    yield np.random.uniform(-0.1, 0.1, 1600).astype(np.float32)

# AFTER:
async def mock_tts(text, stream=True):
    yield np.random.uniform(-0.1, 0.1, 1600).astype(np.float32)
```

**Status:** Fix script queued
**Waiting:** Approval to execute

Once approved and applied:
- Run tests to verify
- Fix any remaining coroutine issues
- All 7 tests should pass ✅

**Confidence:** HIGH - Clear path forward