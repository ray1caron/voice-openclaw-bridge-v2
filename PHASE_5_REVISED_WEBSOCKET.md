# Phase 5: System Integration - REVISED (WebSocket Path)

**Date:** 2026-02-27 10:18 PST
**Status:** Pivot from HTTP to WebSocket architecture
**Key Insight:** OpenClaw uses WebSocket `/api/voice`, not HTTP REST API

---

## Architecture Correction

### ❌ Wrong Approach (HTTP REST)
Attempted to use: `POST /api/sessions/{key}/send`
Result: 405 Method Not Allowed
Reason: OpenClaw gateway doesn't expose HTTP REST API

### ✅ Correct Approach (WebSocket)
Use WebSocket client: `ws://127.0.0.1:18789/api/voice`
Status: Already built (53 tests), fully functional
Messages: JSON over WebSocket with defined protocol

---

## Existing Components ✅ (Sprint 1-4)

### 1. WebSocket Client
**File:** `src/bridge/websocket_client.py` (741 lines)
**Tests:** 53 passing ✅
**Protocol:**
```python
# Send to OpenClaw
{
  "type": "voice_input",
  "text": "your transcript here",
  "metadata": {...}
}

# Receive from OpenClaw
{
  "type": "final|thinking|tool_call|...",
  "content": "the response",
  "metadata": {
    "messageType": "FINAL",
    "speakable": "SPEAK",
    ...
  }
}
```

### 2. OpenClaw Middleware
**File:** `src/bridge/openclaw_middleware.py` (35 tests)
**Purpose:** Tags OpenClaw messages with metadata
**Tags:**
- `MessageType.FINAL` - Ready to speak
- `MessageType.THINKING` - Don't speak
- `MessageType.TOOL_CALL` - Don't speak
- `Speakability.SPEAK|SILENT|CONDITIONAL`

### 3. Response Filter
**File:** `src/bridge/response_filter.py` (39 tests)
**Purpose:** Decide which messages to speak to TTS
**Integrates with:** Middleware for metadata-based filtering

### 4. MiddlewareResponseFilter
**File:** `src/bridge/middleware_integration.py`
**Purpose:** Bridge between middleware and filter
**Logic:**
```python
if message has metadata:
    use metadata decision
else:
    use heuristics (patterns, keywords)
```

### 5. Audio Pipeline
**File:** `src/bridge/audio_pipeline.py` (65 tests)
**Capabilities:**
- Audio capture and playback
- VAD (voice activity detection)
- Barge-in/interrupt support
- Ring buffer for streaming

---

## Missing Components 🔜 (Phase 5)

### Day 1: STT Worker (Whisper)
**File:** `src/audio/stt_worker.py`
**Purpose:** Convert audio to text

```python
class STTWorker:
    """Speech-to-text worker using faster-whisper."""
    
    def __init__(self, model: str = "base"):
        self.model = faster_whisper.WhisperModel(
            model,
            device="cuda" if torch.cuda.is_available() else "cpu",
            compute_type="float16"
        )
    
    async def transcribe(self, audio: np.ndarray) -> str:
        """Transcribe audio to text."""
        segments, info = self.model.transcribe(audio)
        return " ".join(seg.text for seg in segments)
```

**Dependencies:** ✅ Already in pyproject.toml
- faster-whisper
- openai-whisper
- numpy

**Tests:**
```python
# tests/unit/test_stt_worker.py
async def test_transcribe_short_phrase():
    stt = STTWorker()
    audio = load_test_audio("hello.wav")
    text = await stt.transcribe(audio)
    assert "hello" in text.lower()
```

---

### Day 2: TTS Worker (Piper)
**File:** `src/audio/tts_worker.py`
**Purpose:** Convert text to audio (streaming)

```python
class TTSWorker:
    """Text-to-speech worker using Piper TTS."""
    
    def __init__(self, voice_model: str):
        self.model = PiperVoice.load(voice_model)
        self.synthesize = self.model.synthesize_streaming
    
    async def speak(self, text: str) -> AsyncGenerator[bytes, None]:
        """Stream TTS audio frames."""
        audio_stream = self.synthesize(text)
        for chunk in audio_stream:
            yield chunk
```

**Dependencies:** ✅ Already in pyproject.toml
- numpy
- onnxruntime (Piper backend)

**Tests:**
```python
# tests/unit/test_tts_worker.py
async def test_speak_short_text():
    tts = TTSWorker("en_US-lessac-medium")
    async for chunk in tts.speak("Hello"):
        assert len(chunk) > 0
```

---

### Day 3: Wake Word Detection
**File:** `src/audio/wake_word.py`
**Purpose:** Detect "Hey Hal" to start listening

```python
class WakeWordDetector:
    """Wake word detection using Porcupine."""
    
    def __init__(self, access_key: str):
        self.porcupine = pvporcupine.create(
            access_key=access_key,
            keyword_paths=[builtin_keyword("computer")]
        )
        self.recorder = pvrecorder.PvRecorder(
            device_index=-1,
            frame_length=self.porcupine.frame_length
        )
    
    async def listen(self) -> bool:
        """Wait for wake word detection."""
        while True:
            pcm = self.recorder.read()
            if self.porcupine.process(pcm) >= 0:
                return True  # Wake word detected
```

**Dependencies:** ✅ Already in pyproject.toml
- pvporcupine
- pvrecorder (x86_64 only)
- openwakeword (alternative, cross-platform)

**Tests:**
```python
# tests/unit/test_wake_word.py
async def test_wake_word_trigger():
    detector = WakeWordDetector("test-key")
    audio = load_wake_word_audio("hey_hal.wav")
    result = await detector.process_audio(audio)
    assert result is True
```

---

### Day 4: Main Orchestrator
**File:** `src/bridge/voice_orchestrator.py`
**Purpose:** Connect all components in state machine

```python
class VoiceOrchestrator:
    """Main voice assistant orchestrator."""
    
    def __init__(self):
        self.state = State.IDLE
        self.wake_word = WakeWordDetector()
        self.audio = AudioPipeline()
        self.stt = STTWorker()
        self.websocket = OpenClawWebSocketClient()
        self.filter = MiddlewareResponseFilter()
        self.tts = TTSWorker()
    
    async def run(self):
        """Main async loop."""
        while True:
            if self.state == State.IDLE:
                # Wait for wake word
                if await self.wake_word.listen():
                    self.state = State.LISTENING
            
            elif self.state == State.LISTENING:
                # Capture speech
                audio = await self.audio.capture_until_silence()
                transcript = await self.stt.transcribe(audio)
                
                if transcript:
                    self.state = State.PROCESSING
                    
                    # Send to OpenClaw
                    await self.websocket.send_voice_input(transcript)
            
            elif self.state == State.PROCESSING:
                # Wait for OpenClaw response (async)
                # Response comes via on_message callback
                pass
            
            elif self.state == State.SPEAKING:
                # TTS speaks response
                # Barge-in handled by audio_pipeline
                pass
```

**State Machine:**
```
IDLE → LISTENING (wake word)
LISTENING → PROCESSING (speech detected)
PROCESSING → SPEAKING (response ready)
SPEAKING → LISTENING (response done)
SPEAKING → INTERRUPTED (barge-in)
INTERRUPTED → PROCESSING (new input)
```

**Tests:**
```python
# tests/integration/test_voice_orchestrator.py
async def test_full_voice_loop():
    orchestrator = VoiceOrchestrator()
    await orchestrator.run_single_cycle()
    # Verify: capture → STT → WebSocket → Response → TTS
```

---

### Day 5: Audio I/O Integration
**Purpose:** Connect real microphone and speakers

**Tasks:**
1. Audio device discovery (audio_discovery.py exists)
2. Config selection of devices
3. Real-time audio capture with sounddevice
4. Real-time playback with sounddevice

**Existing:** `src/bridge/audio_discovery.py` (28 tests)

---

### Day 6: End-to-End Testing
**Tests to execute:**
- ST-001: Voice Pipeline End-to-End
- ST-002: Barge-In During Response
- ST-003: Wake Word Trigger

**Demo script:**
```bash
# Run full system
python3 -m src.bridge.voice_orchestrator

# Test:
# 1. "Hey Hal" (wake word)
# 2. "What time is it?"
# 3. Should hear response from TTS
```

---

## Flow Diagram (WebSocket Path)

```
┌─────────────────────────────────────────────────────────┐
│                   Wake Word Detector                   │
│              "Hey Hal" → trigger                        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────┐
│                Audio Capture                            │
│         Microphone → VAD → Audio Buffer                 │
└────────────────────┬────────────────────────────────────┘
                     │ speech detected
                     ↓
┌─────────────────────────────────────────────────────────┐
│                 STT Worker                              │
│              Audio → Text (Whisper)                     │
└────────────────────┬────────────────────────────────────┘
                     │ transcript
                     ↓
┌─────────────────────────────────────────────────────────┐
│           OpenClaw WebSocket Client                     │
│     ws://127.0.0.1:18789/api/voice                     │
│  Send: {"type":"voice_input","text":"..."}              │
└────────────────────┬────────────────────────────────────┘
                     │ response received
                     ↓
┌─────────────────────────────────────────────────────────┐
│              Middleware + Filter                        │
│    Tag → FINAL/THINKING → Decide: SPEAK/SILENT         │
└────────────────────┬────────────────────────────────────┘
                     │ speakable response
                     ↓
┌─────────────────────────────────────────────────────────┐
│                 TTS Worker                              │
│              Text → Audio (Piper)                       │
└────────────────────┬────────────────────────────────────┘
                     │ audio chunks
                     ↓
┌─────────────────────────────────────────────────────────┐
│               Audio Output                              │
│             Speakers (sounddevice)                      │
└─────────────────────────────────────────────────────────┘
```

---

## File Structure

```
src/audio/
├── stt_worker.py           # NEW - Whisper STT
├── tts_worker.py           # NEW - Piper TTS
├── wake_word.py            # NEW - Porcupine wake word
└── (existing: barge_in.py, interrupt_filter.py)

src/bridge/
├── voice_orchestrator.py   # NEW - Main orchestrator
├── state_machine.py        # NEW - State machine logic
└── (existing: websocket_client.py, middleware, filter, etc.)

tests/unit/
├── test_stt_worker.py      # NEW
├── test_tts_worker.py      # NEW
├── test_wake_word.py       # NEW
├── test_orchestrator.py    # NEW
└── (existing: test_websocket_client.py, etc.)

tests/integration/
├── test_e2e_voice.py       # NEW - End-to-end
└── (existing: test_websocket_integration.py, etc.)
```

---

## Dependencies Check

**All required in pyproject.toml ✅:**
- faster-whisper (STT)
- openai-whisper (STT)
- numpy (audio arrays)
- sounddevice (audio I/O)
- soundfile (audio files)
- pvporcupine (wake word - x86_64)
- pvrecorder (audio recording)
- openwakeword (wake word - cross-platform)
- onnxruntime (Piper backend)
- websockets (OpenClaw communication)

**Need to verify:**
- [ ] Whisper model downloaded: `/home/hal/.cache/huggingface/hub/...`
- [ ] Piper voice model: `voices/en_US-lessac-medium.onnx`
- [ ] Porcupine access key

---

## Advantages of WebSocket Path

### ✅ Already Built
- WebSocket client: 741 lines, 53 tests
- Middleware: 35 tests
- Response filter: 39 tests
- **Total: 127 tests passing**

### ✅ Designed for Real-Time
- Bidirectional streaming
- Low latency
- Interruption support built-in

### ✅ Metadata-Based Filtering
- Precise control over what to speak
- No heuristics needed when metadata present
- Better than HTTP polling

### ✅ Less Code to Write
- No HTTP client needed (400+ lines saved)
- Use existing WebSocket client
- Focus only on STT/TTS workers

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Whisper too slow | Medium | High latency | Use smaller model (tiny/base) |
| Piper not installed | Medium | TTS fails | Document install steps |
| No Porcupine key | Medium | No wake word | Alternative: openwakeword |
| Hardware audio issues | Low | Can't test | Use mock audio |
| WebSocket protocol changes | Low | Breaks | Already stable (53 tests) |

---

## Revised Timeline (Still 6 Days)

| Day | Focus | Deliverables | Status |
|-----|-------|--------------|--------|
| Day 0 | Discovery | ✅ Complete - WebSocket path confirmed | ✅ DONE |
| Day 1 | STT Worker | Whisper integration, tests | 📋 TODO |
| Day 2 | TTS Worker | Piper integration, streaming, tests | 📋 TODO |
| Day 3 | Wake Word | Porcupine + detection, tests | 📋 TODO |
| Day 4 | Orchestrator | State machine + wiring, tests | 📋 TODO |
| Day 5 | Audio I/O | Real device integration | 📋 TODO |
| Day 6 | E2E Testing | System tests + demo | 📋 TODO |

---

## Next Immediate Steps

### Today (Day 1): STT Worker
```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2

# Create STT worker
vim src/audio/stt_worker.py

# Create tests
vim tests/unit/test_stt_worker.py

# Run tests
pytest tests/unit/test_stt_worker.py -v
```

### Check Dependencies
```bash
# Verify Whisper model
python3 -faster_whisper  # Should work if installed

# Check Piper
python3 -c "import piper; print('Piper OK')"

# Check wake word support
python3 -c "import pvporcupine; print('Porcupine OK')"  # x86_64 only
```

---

## Success Criteria

Phase 5 is complete when:
1. ✅ STT worker transcribes audio → text
2. ✅ TTS worker converts text → audio
3. ✅ Wake word triggers listening
4. ✅ Orchestrator wires everything together
5. ✅ "Hey Hal, what time is it?" works end-to-end
6. ✅ Barge-in interrupts TTS <100ms
7. ✅ All tests passing (goal: +200 new tests)

---

**Revised:** 2026-02-27 10:18 PST
**Author:** Hal
**Status:** Ready to begin Day 1 (STT Worker)
**Approach:** WebSocket (not HTTP) ✅