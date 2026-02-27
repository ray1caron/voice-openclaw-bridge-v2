# Phase 3E Fix - Test File Correction

## Problem:

test_barge_in_during_tts uses patch.object on orchestrator._wake_word, but _wake_word is None (lazy initialization).

## Solution:

Replace all patch.object usage on None-initialized components with direct assignment.

## Changes Needed in test_barge_in_during_tts:

BEFORE:
```python
with patch.object(orchestrator._wake_word, 'listen', new_callable=AsyncMock) as mock_listen:
    ...
```

AFTER:
```python
orchestrator._wake_word = AsyncMock()
orchestrator._wake_word.listen = AsyncMock(return_value=wake_event)
...
```

This is the same pattern used successfully in other tests like test_callback_system.