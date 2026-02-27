# FIX: Use Real Audio Files in E2E Tests

**Version:** 0.2.0
**Date/Time:** 2026-02-27 15:10 PST

---

## The Problem:

E2E tests are using mocked audio data (b"mock_audio") instead of the actual audio files that were created:
```python
# WRONG (current approach):
orchestrator._audio.capture_audio = AsyncMock(return_value=(1000.0, b"mock_audio"))
```

This doesn't test the real audio pipeline with actual STT processing.

---

## The Fix:

Use `speech_like_2s.wav` for all tests:
```python
# CORRECT (real audio):
import soundfile as sf

@staticmethod
def load_test_audio():
    """Load the test audio file."""
    audio, sr = sf.read("tests/fixtures/audio/speech_like_2s.wav")
    return (len(audio) / sr), audio.astype(np.float32)

# Then in tests:
duration_ms, audio_data = load_test_audio()
orchestrator._audio.capture_audio = AsyncMock(return_value=(duration_ms * 1000, audio_data))
```

---

## Implementation:

1. Generate test audio files if not present
2. Load speech_like_2s.wav for all capture_audio mocks
3. Use actual audio data throughout tests
4. This will test real audio processing pipeline

---

**Status:** Updating test file now
**Audio Files:** speech_like_2s.wav to be used for all tests

---

END OF FIX PLAN