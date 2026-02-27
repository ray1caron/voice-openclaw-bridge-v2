# Phase 3H Fix: Mock receive_response Instead of send_voice_input

**Version:** 0.2.0
**Date/Time:** 2026-02-27 14:59 PST

---

## The Real Problem

The `_send_to_openclaw` method calls TWO methods:

```python
async def _send_to_openclaw(self, text: str) -> str:
    # 1. Send voice input (doesn't return response)
    await self._websocket.send_voice_input(text)
    
    # 2. Receive response (THIS is where we get the response!)
    response = await self._websocket.receive_response()
    
    # 3. Extract text from response
    return response.get("text", "")
```

---

## What We Were Doing Wrong:

We were trying to make `send_voice_input` return the response:
```python
orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())
```

But `send_voice_input` doesn't return the response! It just sends. The actual response comes from `receive_response`.

---

## The Correct Fix:

```python
orchestrator._websocket = AsyncMock()

# Mock send_voice_input - just send, don't return anything
orchestrator._websocket.send_voice_input = AsyncMock(return_value=None)

# Mock receive_response - THIS is where the response comes from
orchestrator._websocket.receive_response = AsyncMock(return_value=mock_server.get_response())
```

---

## Why This Works:

1. Orchestrator calls `await self._websocket.send_voice_input(text)` → returns None (send was successful)
2. Orchestrator calls `await self._websocket.receive_response()` → returns the dict from mock_server.get_response()
3. Orchestrator extracts `response.get("text", "")` → "This is a mock response from OpenClaw."
4. Callback receives the string → SUCCESS!

---

## Test Status Before Fix:

✅ **4/7 tests PASS** (57%)
❌ test_callback_system - coroutine error
❌ test_barge_in_during_tts - unclear

---

## Expected After Fix:

✅ **5/7 tests PASS** (71%)
- test_callback_system should now PASS
- test_barge_in_during_tts: TBD

---

**Status:** Fix applied, tests queued
**Confidence:** VERY HIGH - This is the correct approach
**Phase:** 3H - Mock the right method

---

END OF PHASE 3H FIX