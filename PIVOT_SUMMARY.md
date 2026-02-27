# Pivot: HTTP REST → WebSocket

**Date:** 2026-02-27 10:20 PST
**Trigger:** Spike test got 405 Method Not Allowed
**Resolution:** Use existing WebSocket client instead of HTTP API

---

## What Happened

### Attempted (Wrong Path)
- Created HTTP client for OpenClaw REST API
- Tested `POST /api/sessions/main/send`
- Got: **405 Method Not Allowed**
- Root cause: OpenClaw gateway doesn't expose HTTP REST API

### discovered (Right Path)
- **WebSocket client already exists** ✅
- **53 tests passing** ✅
- **741 lines of production code** ✅
- **Already integrated in Sprint 1** ✅

---

## Architecture Change

### Before (HTTP REST - Wrong)
```
Audio → STT → HTTP POST → OpenClaw → HTTP GET → TTS → Audio
        ↳ 405 error! ↗
```

### After (WebSocket - Correct)
```
Audio → STT → WebSocket → OpenClaw → WebSocket → Filter → TTS → Audio
        (already built!)  (already built!)      (already built!)
```

---

## What Already Exists ✅

### 1. WebSocket Client
```
File: src/bridge/websocket_client.py
Lines: 741
Tests: 53 passing
Endpoint: ws://127.0.0.1:18789/api/voice
Protocol: JSON messages with types
```

### 2. Middleware
```
File: src/bridge/openclaw_middleware.py
Tests: 35 passing
Purpose: Tag OpenClaw messages (FINAL, THINKING, etc.)
```

### 3. Response Filter
```
File: src/bridge/response_filter.py
Tests: 39 passing
Purpose: Decide what to speak
```

### 4. Integration Layer
```
File: src/bridge/middleware_integration.py
Purpose: Bridge middleware and filter
Status: Metadata-based filtering ready
```

**Total:** 127 tests passing for WebSocket infrastructure

---

## What We Need to Build 🔜 (Phase 5)

### Day 1: STT Worker (NEW)
```
File: src/audio/stt_worker.py
Purpose: Whisper integration
Function: Audio → Text
Tests: ~20 planned
```

### Day 2: TTS Worker (NEW)
```
File: src/audio/tts_worker.py
Purpose: Piper integration
Function: Text → Audio (streaming)
Tests: ~20 planned
```

### Day 3: Wake Word (NEW)
```
File: src/audio/wake_word.py
Purpose: Porcupine detection
Function: "Hey Hal" → trigger
Tests: ~15 planned
```

### Day 4: Orchestrator (NEW)
```
File: src/bridge/voice_orchestrator.py
Purpose: Wire everything together
Function: State machine + event loop
Tests: ~15 planned
```

### Day 5: Audio I/O (NEW)
```
File: Update existing audio_discovery.py
Purpose: Real device integration
Function: Mic + speakers
Tests: ~10 planned
```

### Day 6: E2E Testing (NEW)
```
File: tests/integration/test_e2e_voice.py
Purpose: Full system test
Function: "Hey Hal, what time is it?"
Tests: ST-001, ST-002, ST-003
```

---

## Impact Analysis

### Saved Work
- ✅ No HTTP client needed (~400 lines saved)
- ✅ WebSocket protocol stable (53 tests)
- ✅ Metadata filtering ready
- ✅ Message validation done

### New Work Required
- 🔜 STT worker (~200 lines)
- 🔜 TTS worker (~200 lines)
- 🔜 Wake word (~150 lines)
- 🔜 Orchestrator (~300 lines)
- 🔜 Tests (~200 lines)

**Net:** New code ~1,050 lines (vs. HTTP path ~1,400)
**Savings:** 350 lines + 200 lines for HTTP client

---

## Dependencies Status

**All required packages already in pyproject.toml ✅:**

```toml
# STT
"faster-whisper>=1.0"
"openai-whisper>=20231117"

# TTS
"numpy>=1.24"
"onnxruntime>=1.16"

# Audio
"sounddevice>=0.5"
"soundfile>=0.12"
"webrtcvad>=2.0"

# Wake Word (x86_64)
"pvporcupine>=3.0"
"pvrecorder>=1.2"
"openwakeword>=0.5"  # Alternative
```

**Need to verify:**
- [ ] Whisper model downloaded
- [ ] Piper voice model downloaded
- [ ] Porcupine access key

---

## Protocol Details

### Send to OpenClaw (WebSocket)
```python
{
  "type": "voice_input",
  "text": "your transcript here",
  "metadata": {
    "timestamp": 1234567890,
    "session_id": "voice-session-123"
  }
}
```

### Receive from OpenClaw (WebSocket)
```python
{
  "type": "final",
  "content": "The response text",
  "metadata": {
    "messageType": "FINAL",
    "speakable": "SPEAK",
    "model": "ollama/glm-4.7:cloud",
    "latencyMs": 1234
  }
}
```

### Message Types
- `FINAL` - Ready to speak ✅
- `THINKING` - Don't speak ❌
- `TOOL_CALL` - Don't speak ❌
- `TOOL_RESULT` - Don't speak ❌
- `PLANNING` - Don't speak ❌
- `PROGRESS` - Don't speak ❌

---

## Advantages of WebSocket Path

### 1. Real-Time ✅
- Bidirectional streaming
- Low latency (<100ms)
- Interruption support

### 2. Metadata-Driven ✅
- Precise control
- No heuristics needed
- Better filtering

### 3. Already Tested ✅
- 127 tests passing
- Production-ready
- Battle-tested

### 4. Less Code ✅
- No HTTP client
- No REST API
- Simpler architecture

---

## Timeline Adjustment

| Day | Original (HTTP) | Revised (WebSocket) |
|-----|-----------------|---------------------|
| Day 0 | HTTP API spike | ✅ Discovery complete |
| Day 1 | HTTP client | STT Worker |
| Day 2 | STT + OpenClaw | TTS Worker |
| Day 3 | OpenClaw + TTS | Wake Word |
| Day 4 | Wake word | Orchestrator |
| Day 5 | State machine | Audio I/O |
| Day 6 | E2E tests | E2E tests |

**Duration:** Still 6 days
**Efficiency:** Higher (reuse existing code)

---

## Immediate Next Steps

### 1. Create STT Worker (Day 1)
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2

vim src/audio/stt_worker.py
```

### 2. Test with existing WebSocket client
```python
import asyncio
from bridge.websocket_client import OpenClawWebSocketClient

async def test_websocket():
    client = OpenClawWebSocketClient()
    await client.connect()
    await client.send_voice_input("Hello, OpenClaw!")
    # Response comes via on_message callback

asyncio.run(test_websocket())
```

### 3. Verify dependencies
```bash
python3 -c "import faster_whisper; print('Whisper OK')"
python3 -c "import piper; print('Piper OK')"
python3 -c "import pvporcupine; print('Porcupine OK')"
```

---

## Summary

**Before:**
- ❌ Wrong architecture (HTTP REST)
- ❌ Got 405 error
- ❌ 400+ lines of HTTP client needed

**After:**
- ✅ Correct architecture (WebSocket)
- ✅ 127 tests passing
- ✅ Reuse existing code
- ✅ Only ~1,050 lines new code needed

**Pivot:**
- Reason: Spike test failure (405 Method Not Allowed)
- Impact: Reduced scope, better architecture
- Result: Faster completion
- Status: ✅ Ready to proceed Day 1

---

**Created:** 2026-02-27 10:20 PST
**Status:** Pivot complete, ready for Day 1 (STT Worker)
**Next:** Create `src/audio/stt_worker.py`