# AsyncMock v2 Fix - Component Objects

**Version:** 0.2.0
**Date/Time:** 2026-02-27 13:22 PST

---

## Remaining Issue

After fixing the first round of AsyncMock issues, tests still show:
```
TypeError: object Mock can't be used in 'await' expression
```

**Root Cause:** Component objects themselves are `Mock()`, not `AsyncMock()`

---

## The Fix

**Change all Mock() component objects to AsyncMock():**

```python
# BEFORE:
orchestrator._wake_word = Mock()
orchestrator._audio = Mock()
orchestrator._stt = Mock()
orchestrator._tts = Mock()
orchestrator._websocket = Mock()
orchestrator._barge_in = Mock()

# AFTER:
orchestrator._wake_word = AsyncMock()
orchestrator._audio = AsyncMock()
orchestrator._stt = AsyncMock()
orchestrator._tts = AsyncMock()
orchestrator._websocket = AsyncMock()
orchestrator._barge_in = AsyncMock()
```

---

## Why This Works

When you do:
```python
orchestrator._component = Mock()
orchestrator._component.method = AsyncMock()
```

The `_component` is still a Mock object. If the orchestrator tries to await `_component` itself (not just its methods), it will fail.

By making the component objects AsyncMock:
```python
orchestrator._component = AsyncMock()
```

They're now coroutines themselves and can be awaited if needed.

---

**Status:** Fix script created and ready
**Next:** Run fix, commit, re-run tests
**Expected:** All tests pass