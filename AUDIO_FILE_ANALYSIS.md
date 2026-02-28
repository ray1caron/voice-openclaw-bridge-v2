# E2E Test Audio Analysis

**File:** `tests/fixtures/audio/speech_like_2s.wav`

---

## Audio Properties

| Property | Value |
|----------|-------|
| **Samplerate** | 44,100 Hz (CD quality) |
| **Duration** | 3.75 seconds |
| **Channels** | 2 (stereo) |
| **Frames** | 165,464 samples |
| **File Size** | 647 KB |

---

## Analysis

**Quality:**
- High sample rate (44.1kHz vs standard 16kHz for voice)
- Stereo (vs mono for voice)
- 3.75 seconds duration (provides ample audio for testing)

**Format:**
- WAV format (uncompressed)
- Lossless audio quality
- Direct loading with soundfile

---

## Use in Test

The `test_barge_in_during_tts` test loads this file:

```python
audio, sr = sf.read("tests/fixtures/audio/speech_like_2s.wav")
duration_ms = (len(audio) / sr) * 1000
```

**Purpose:** Simulates real user speech input

---

**Audio file properties analyzed**