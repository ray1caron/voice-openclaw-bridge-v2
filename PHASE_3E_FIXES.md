# Phase 3E: Dict Await and None Attribute Fixes

**Version:** 0.2.0
**Date/Time:** 2026-02-27 14:41 PST

---

## Current Status:

**Test Results:** 3 PASS, 3 FAIL (43%)
**Progress:** Improved from 29% to 43% (+1 test fixed)

---

## Issues Identified:

### Issue 1: Dict can't be used in 'await' expression
**Test:** test_callback_system
**Error:** `TypeError: object dict can't be used in 'await' expression`

**Root Cause:**
```python
# WRONG:
orchestrator._websocket = AsyncMock()
orchestrator._websocket.send_voice_input = Mock(return_value=mock_server.get_response())
```

`send_voice_input` is an **async method** that returns a dict. Using `Mock` makes it synchronous. When the orchestrator tries to `await self._websocket.send_voice_input(text)`, it's trying to await the Mock object (which is trying to return a dict synchronously), which causes the error.

**Solution:**
```python
# CORRECT:
orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())
```

Use `AsyncMock` for async methods even if they return sync values.

### Issue 2: None does not have attribute 'listen'
**Test:** test_barge_in_during_tts
**Error:** `AttributeError: None does not have the attribute 'listen'`

**Root Cause:**
```python
# WRONG:
orchestrator._wake_word = Mock()
```

The test later tries to access `orchestrator._wake_word.listen`, but `_wake_word` might be None or might not have been initialized as AsyncMock.

**Solution:**
```python
# CORRECT:
orchestrator._wake_word = AsyncMock()
```

Always use `AsyncMock` for async component objects.

---

## Why Phase 3D Was Partially Wrong:

In Phase 3D, we changed `send_voice_input` from `AsyncMock` to `Mock` because we thought it was returning a dict synchronously. However, `send_voice_input` is **an async method** - it's async even though it returns a dict.

**Rule:**
- Use `AsyncMock` for async methods (even if they return sync values)
- Use `Mock` for sync methods

---

## Expected Result After Phase 3E:

**Test Results:** 5/7 PASS (71%)

The 2 fixed tests:
- ✅ test_callback_system (dict await issue)
- ✅ test_barge_in_during_tts (None attribute issue)

---

## Fix Script:

`fix_phase_3e.py`
1. Change send_voice_input Mock → AsyncMock
2. Change _wake_word Mock → AsyncMock

---

**Status:** Fixes queued, awaiting execution
**Confidence:** HIGH - Clear understanding of the issue