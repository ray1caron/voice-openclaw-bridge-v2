# Fix: Remaining Test Failures

**Version:** 0.2.0
**Date/Time:** 2026-02-27 15:17 PST

---

## Failing Tests:

### 1. test_barge_in_during_tts
**Error:** Uses old mock audio data

**Issue:**
```python
mock_audio = b"mock_audio_data"  # Line 116
orchestrator._audio.capture_audio = AsyncMock(return_value=(2000.0, mock_audio))
```

**Fix:** Replace with real audio file loading

### 2. test_statistics_aggregation
**Error:** Missing receive_response mock

**Issue:**
```python
orchestrator._websocket.send_voice_input = AsyncMock(side_effect=slow_interaction)
# Missing receive_response mock!
```

**Fix:** Add receive_response mock

---

## Common Pattern for All Tests:

```python
# For audio capture:
# Load real test audio
audio, sr = sf.read("tests/fixtures/audio/speech_like_2s.wav")
duration_ms = (len(audio) / sr) * 1000
orchestrator._audio.capture_audio = AsyncMock(return_value=(duration_ms, audio.astype(np.float32)))

# For websocket:
orchestrator._websocket.send_voice_input = AsyncMock(return_value=None)  # Send input
orchestrator._websocket.receive_response = AsyncMock(return_value=mock_server.get_response())  # Get response
```

---

## Next Steps:

1. Fix test_barge_in_during_tts - use real audio + mock receive_response
2. Fix test_statistics_aggregation - mock receive_response
3. Run tests again
4. Expect: 7/8 passing or better

---

**Status:** Preparing to apply fixes
**Current:** 5/8 passing (62.5%)
**Target:** 8/8 passing (100%)

---

END OF FIX PLAN