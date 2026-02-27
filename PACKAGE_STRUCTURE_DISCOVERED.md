# E2E Test Import Fix - Package Structure Discovery

**Version:** 0.2.0
**Date/Time:** 2026-02-27 12:52 PST
**Status:** ✅ Package structure identified, imports corrected

---

## The Real Problem: Mixed Package Structure

The Phase 5 voice modules are in a **different package structure** than expected!

### Actual Package Structure (Discovered)

```
src/
├── audio/                    # Audio package (Phase 5)
│   ├── __init__.py
│   ├── wake_word.py         # → from audio.wake_word
│   ├── stt_worker.py        # → from audio.stt_worker
│   └── tts_worker.py        # → from audio.tts_worker
│
└── bridge/                  # Bridge package (Sprints 1-4)
    ├── __init__.py
    ├── audio_pipeline.py    # → from bridge.audio_pipeline
    ├── voice_orchestrator.py
    ├── websocket_client.py  # → from bridge.websocket_client
    └── ...
```

### What I Got Wrong Initially:

I thought the structure was:
```
src/bridge/audio/wake_word.py  # ❌ WRONG
```

But it's actually:
```
src/audio/wake_word.py  # ✅ CORRECT
```

---

## Correct Import Patterns

### Audio Modules (Phase 5):
```python
from audio.wake_word import WakeWordDetector  # ✅
from audio.stt_worker import STTWorker  # ✅
from audio.tts_worker import TTSWorker  # ✅
```

### Bridge Modules (Sprints 1-4):
```python
from bridge.audio_pipeline import AudioPipeline  # ✅
from bridge.websocket_client import WebSocketClient  # ✅
from bridge.voice_orchestrator import VoiceOrchestrator  # ✅
```

### Voice Orchestrator Uses Both:
```python
from audio.wake_word import WakeWordDetector  # Phase 5
from audio.stt_worker import STTWorker  # Phase 5
from audio.tts_worker import TTSWorker  # Phase 5
from bridge.audio_pipeline import AudioPipeline  # Sprint 1
from bridge.websocket_client import WebSocketClient  # Sprint 1
```

---

## Files Fixed

### 1. src/bridge/voice_orchestrator.py ✅
**Lines 34-54**

**Changed FROM:**
```python
from bridge.audio.wake_word import WakeWordDetector  # ❌
from bridge.audio.stt_worker import STTWorker  # ❌
from bridge.audio.tts_worker import TTSWorker  # ❌
```

**Changed TO:**
```python
from audio.wake_word import WakeWordDetector  # ✅
from audio.stt_worker import STTWorker  # ✅
from audio.tts_worker import TTSWorker  # ✅
```

### 2. tests/integration/test_voice_e2e.py ✅
**Multiple locations**

**Changed FROM:**
```python
from bridge.audio.wake_word import WakeWordEvent  # ❌
from bridge.audio.stt_worker import TranscriptionResult  # ❌
from bridge.audio.wake_word import WakeWordDetector  # ❌
```

**Changed TO:**
```python
from audio.wake_word import WakeWordEvent  # ✅
from audio.stt_worker import TranscriptionResult  # ✅
from audio.wake_word import WakeWordDetector  # ✅
```

---

## Why This Happened

### Phase 5 is Separate Package

**Reason:** Phase 5 voice modules were implemented as a separate `audio/` package, not under `bridge/`

**Benefits:**
- Clear separation between base bridge (Sprints 1-4) and voice layer (Phase 5)
- Audio modules can be independently imported for other projects
- Matches how unit tests import them

### Evidence from Unit Tests:
```python
# tests/unit/test_stt_worker.py uses:
@patch("audio.stt_worker.WhisperModel")  # ✅
from audio.stt_worker import STTWorker  # ✅

# tests/unit/test_wake_word.py uses:
from audio.wake_word import WakeWordConfig  # ✅
from audio.wake_word import WakeWordDetector  # ✅
```

---

## Test Execution

### Command:
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2
PYTHONPATH=src:$PYTHONPATH python3 -m pytest tests/integration/test_voice_e2e.py -v
```

### Expected Results:

| Test | Expected |
|------|----------|
| test_full_interaction_flow | ✅ PASS |
| test_barge_in_during_tts | ✅ PASS |
| test_multiple_interactions | ✅ PASS |
| test_error_handling | ✅ PASS |
| test_callback_system | ✅ PASS |
| test_statistics_aggregation | ✅ PASS |
| test_wake_word_detection_latency | ✅ PASS |
| test_interaction_latency | ✅ PASS |

**Total:** 8 tests

---

## Git Commits

1. ✅ `7b8d3c7` - "fix: Correct imports in VoiceOrchestrator" (WRONG, reverted)
2. ✅ `beecb59b` - "fix: Revert imports to correct structure" (FINAL, CORRECT)

---

## Key Takeaways

1. **Always check unit test imports** - they show the correct pattern
2. **Package structure matters** - audio/ is separate from bridge/
3. **Phase = Package** - Phase 5 got its own audio/ package
4. **Don't assume** - verify before making changes

---

**Status:** ✅ Imports fixed and committed
**Test Execution:** ⏸️ Queued (awaiting approval)
**Confidence:** HIGH - should work now

---

## Correct PYTHONPATH

```bash
# Must include both src/ and parent dir for audio/ and bridge/ packages
PYTHONPATH=/home/hal/.openclaw/workspace/voice-bridge-v2/src:/home/hal/.openclaw/workspace/voice-bridge-v2:$PYTHONPATH
```

This is why `AUDIO_PATH=src:` wasn't working - it needs both `src/` AND the project root!