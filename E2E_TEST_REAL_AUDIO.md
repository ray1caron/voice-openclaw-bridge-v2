# E2E Test with Real Audio - Running

**Date:** 2026-02-28
**Time:** 2:44 PM PST
**Test:** `test_barge_in_during_tts`
**Audio File:** `tests/fixtures/audio/speech_like_2s.wav` (647KB)

---

## Test Details

**Test Name:** `test_barge_in_during_tts`
**Location:** `tests/integration/test_voice_e2e.py`
**Audio File:** `/home/hal/.openclaw/workspace/voice-bridge-v2/tests/fixtures/audio/speech_like_2s.wav`
**File Size:** 647KB
**Purpose:** Test barge-in interruption during TTS playback

---

## Test Scenario

**Flow:**
1. Wake word detected
2. Capture audio (using `speech_like_2s.wav`)
3. Transcribe speech
4. Send to OpenClaw
5. Get response
6. Start TTS synthesis
7. Simulate interruption at chunk 5
8. Verify interruption detected

---

## Command Running

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:$PYTHONPATH
python3 -m pytest \
    tests/integration/test_voice_e2e.py::TestVoiceAssistantE2E::test_barge_in_during_tts \
    -v \
    --tb=short
```

---

## Why This Test?

**Using Real Audio:**
- Actual speech waveform (647KB WAV)
- Real audio duration (~2 seconds)
- Tests with realistic data

**What It Validates:**
- Barge-in detection during active TTS
- Interruption handling
- Audio pipeline flow
- TTS interruption support

---

**E2E test running with real audio...**