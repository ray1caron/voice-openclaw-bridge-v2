# Fix for AsyncMock return_value Issue

**Version:** 0.2.0
**Date/Time:** 2026-02-27 14:51 PST

---

## The Problem:

test_callback_system fails with:
```
AssertionError: assert <coroutine object AsyncMockMixin._execute_mock_call> == 'This is a mock response from OpenClaw.'
```

The callback `on_response(text)` is receiving a coroutine object instead of the string text.

## Root Cause:

When using `AsyncMock(return_value=mock_server.get_response())`:

```python
orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())
```

The AsyncMock wraps the return_value in a coroutine. When the method is called and awaited, the callback receives the coroutine object, not the actual dict/string.

## The Fix:

Change from `return_value` to `side_effect` with a lambda:

```python
orchestrator._websocket.send_voice_input = AsyncMock(side_effect=lambda text: mock_server.get_response())
```

The `side_effect` with a lambda ensures that when `send_voice_input` is called, it returns the result of the lambda function directly (a dict), bypassing the async wrapper.

## Why This Works:

- **return_value**: AsyncMock wraps the value in a coroutine
- **side_effect with lambda**: Returns the lambda's result directly

The lambda `lambda text: mock_server.get_response()` is a regular (non-async) function that returns the dict, so it doesn't get wrapped in a coroutine.

## Pattern Used in Successful Tests:

test_multiple_interactions (which is passing) uses:
```python
orchestrator._websocket.send_voice_input = AsyncMock(side_effect=get_mock_response)
```

Where `get_mock_response` is a regular function.
We're applying the same pattern to test_callback_system.

---

**Status:** Fix script queued
**Expected:** Fixes test_callback_system coroutine error
**Target:** 6/7 tests passing (86%)

---

END OF FIX EXPLANATION