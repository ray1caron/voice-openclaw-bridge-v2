# Proper Fix - No Shortcuts

**Version:** 0.2.0
**Date/Time:** 2026-02-27 14:46 PST

---

## The Problem:

Tests using `patch.object(orchestrator._component, 'method')` were failing because:

1. VoiceOrchestrator uses **lazy initialization** - all components start as `None`
2. `patch.object` requires a non-None object to patch

```python
# In VoiceOrchestrator.__init__:
self._wake_word: Optional[WakeWordDetector] = None  # Lazy init
self._audio: Optional[AudioPipeline] = None
self._stt: Optional[STTWorker] = None
self._websocket: Optional[WebSocketClient] = None
self._tts: Optional[TTSWorker] = None
self._barge_in: Optional[BargeInHandler] = None
```

---

## The Tests Fixed:

### test_full_interaction_flow (lines 90-114)
**BEFORE (WRONG):**
```python
with patch.object(orchestrator._wake_word, 'listen', new_callable=AsyncMock) as mock_listen:
    mock_listen.return_value = wake_event
    ... # More nested patch.object calls
```

**AFTER (CORRECT):**
```python
orchestrator._wake_word = AsyncMock()
orchestrator._wake_word.listen = AsyncMock(return_value=wake_event)

orchestrator._audio = AsyncMock()
orchestrator._audio.capture_audio = AsyncMock(return_value=(2000.0, mock_audio))
orchestrator._audio.play_audio = AsyncMock()

orchestrator._stt = AsyncMock()
orchestrator._stt.transcribe = AsyncMock(return_value=mock_transcription)

orchestrator._websocket = AsyncMock()
orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())

orchestrator._tts = AsyncMock()
async def mock_speak_gen(text, stream=True):
    yield mock_tts_audio
orchestrator._tts.speak = mock_speak_gen
```

### test_barge_in_during_tts (lines 165-183)
**BEFORE (WRONG):**
```python
with patch.object(orchestrator._wake_word, 'listen', new_callable=AsyncMock) as mock_listen:
    mock_listen.return_value = wake_event
    ... # More nested patch.object calls
```

**AFTER (CORRECT):**
```python
orchestrator._wake_word = AsyncMock()
orchestrator._wake_word.listen = AsyncMock(return_value=wake_event)

orchestrator._audio = AsyncMock()
orchestrator._audio.capture_audio = AsyncMock(return_value=(1000.0, mock_audio))
orchestrator._audio.play_audio = AsyncMock()

orchestrator._stt = AsyncMock()
orchestrator._stt.transcribe = AsyncMock(return_value=mock_transcription)

orchestrator._websocket = AsyncMock()
orchestrator._websocket.send_voice_input = AsyncMock(return_value=mock_server.get_response())

orchestrator._tts = AsyncMock()
orchestrator._tts.speak = interrupted_tts

orchestrator._barge_in = AsyncMock()
orchestrator._barge_in.check_interruption = Mock(side_effect=check_interruption_side_effect)
```

---

## Why This Works:

1. **Direct Assignment** creates the AsyncMock objects before they're needed
2. **No None Values** - components are initialized as AsyncMock objects
3. **Simpler Code** - no nested `with` statements
4. **Match Successful Tests** - same pattern used in test_callback_system, test_multiple_interactions

---

## Changes Made:

**File:** `tests/integration/test_voice_e2e.py`

**test_full_interaction_flow:**
- Removed: 25 lines of nested `with patch.object(...)` blocks
- Added: 20 lines of direct AsyncMock assignments
- Net: -5 lines, cleaner code

**test_barge_in_during_tts:**
- Removed: 19 lines of nested `with patch.object(...)` blocks
- Added: 13 lines of direct AsyncMock assignments
- Net: -6 lines, cleaner code

**Total:** 47 lines fixed, simplifying the code

---

## Expected Result:

Both tests should now PASS instead of FAILING with:
- ❌ `AttributeError: None does not have the attribute 'listen'`
- ✅ Both tests using proper direct AsyncMock assignment

---

**Status:** Fixes applied, tests queued
**Approach:** Proper, direct fix - no shortcuts or workarounds