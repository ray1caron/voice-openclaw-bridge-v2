# Key Insight: AsyncMock vs Mock Usage

**Lesson Learned:** When to use AsyncMock vs Mock

---

## The Confusion:

In Phase 3D, I changed `send_voice_input` from `AsyncMock` to `Mock` because I saw it returning a dictionary, which is a synchronous value. But this caused new errors.

---

## The Rule:

### Use `AsyncMock` for:
- Async methods that return sync values
- Async methods that return async values
- Async generators

### Use `Mock` for:
- Sync methods
- Sync functions
- Regular objects

---

## Examples:

### ❌ WRONG:
```python
# send_voice_input is an async method:
async def send_voice_input(self, text: str) -> dict:
    # ... returns dict (sync value)
    return {"text": "response"}

# WRONG mock:
orchestrator._websocket.send_voice_input = Mock(return_value=mock_server.get_response())
# Error: dict can't be used in 'await' expression
```

### ✅ CORRECT:
```python
# CORRECT mock:
orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())
# Works correctly
```

---

## The Key Principle:

**Mock the **type** of the function/method, not the **type** of the return value.**

- `AsyncMock` for async functions (even if they return int, str, dict, etc.)
- `Mock` for sync functions

---

## Test Guidelines:

```python
# Async methods (even if returning sync types):
obj.async_method = AsyncMock(return_value=123)
obj.async_method = AsyncMock(return_value="string")
obj.async_method = AsyncMock(return_value={})
obj.async_method = AsyncMock(return_value=[])

# Sync methods:
obj.sync_method = Mock(return_value=async_func())  # Returns coroutine
# Or:
obj.sync_method = AsyncMock(return_value=async_func()) # Returns awaited value
```

---

This insight was learned through debugging Phase 3C-3E test failures.

**Date:** 2026-02-27
**Context:** Voice Bridge v2 E2E Testing