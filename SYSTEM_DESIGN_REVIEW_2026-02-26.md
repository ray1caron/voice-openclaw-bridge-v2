# Voice-OpenClaw Bridge v2 - System Design Review

**Review Date:** 2026-02-26 09:20 PST  
**Reviewer:** OpenClaw Agent  
**Status:** CRITICAL - Product Does Not Function

---

## Executive Summary

**The Problem:** We have built extensive infrastructure, but the Voice-OpenClaw Bridge v2 does **not function as a voice assistant**. 

**What We Built:**
- ✅ 509 passing tests across isolated modules
- ✅ Complete architectural infrastructure (WebSocket, Audio, Sessions, Barge-in)
- ✅ Database persistence layer
- ✅ Configuration system with hot-reload
- ✅ Bug tracking system
- ❌ **A working product**

**The Reality:**
The `bridge/main.py` initializes components and enters an infinite sleep loop. The actual voice pipeline—audio capture → STT → WebSocket → OpenClaw → response → TTS → audio playback—is **not implemented**.

**Root Cause:** Sprint-based development focused on components in isolation without sufficient integration testing of end-to-end flows.

---

## Critical Gaps Analysis

### 1. The Voice Pipeline Gap (CRITICAL)

**Current State:**
```python
# bridge/main.py
async def main():
    setup_logging()
    config = get_config()
    logger.info("Bridge initialized")
    
    while True:  # ← Does nothing useful
        await asyncio.sleep(1)
```

**Required Flow:**
```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Audio      │────>│   STT        │────>│   WebSocket  │
│   Capture    │     │   (Whisper)  │     │   Client     │
└──────────────┘     └──────────────┘     └──────┬───────┘
                                                  │
                                                  ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Audio      │<────│   TTS        │<────│   OpenClaw   │
│   Playback   │     │   (Piper)    │     │   Response   │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Status:** Components exist but are not wired together.

### 2. Hardware Integration Gap (CRITICAL)

**Current State:**
- Audio pipeline uses **mock VAD** because webrtcvad not installed
- No actual microphone capture in production code
- No speaker playback integration
- Tests mock sounddevice

**What's Missing:**
```python
# Required integration in main.py (does not exist):
async def voice_loop():
    while running:
        audio = await capture_audio_chunk()
        transcript = await stt_engine.transcribe(audio)
        await websocket.send({"type": "voice_input", "text": transcript})
        response = await wait_for_response()
        await tts_engine.speak(response)
```

### 3. Wake Word Integration Gap (CRITICAL)

**What Exists:**
- `voice-bridge-v2/` has `wakeword.py` from original project
- Porcupine wake word detection works standalone

**What's Missing:**
- Wake word **not connected** to voice pipeline
- No trigger to start listening for query
- No transition from idle → listening → processing → speaking

**Required:**
```python
async def main_control_loop():
    while True:
        await wake_word_detector.wait()  # "Computer"
        audio_pipeline.start_capture()     # Listen for query
        audio = await capture_until_silence()
        transcript = stt.transcribe(audio)
        response = await query_llm(transcript)
        await tts.speak(response)
```

### 4. WebSocket to Audio Bridge Gap (CRITICAL)

**Current State:**
- WebSocket client exists (Sprint 1)
- Audio pipeline exists (Sprint 1)
- They are **not connected**

**What's Missing:**
- WebSocket `voice_input` messages are never sent from captured audio
- WebSocket responses are never routed to TTS
- Response filtering identifies message types but doesn't control audio flow

### 5. Error Recovery in Main Loop (HIGH)

**Current State:**
- Error recovery exists in session persistence (Sprint 3)
- Bug tracking captures errors (Sprint 2)
- **No recovery** in the main voice loop

**What's Missing:**
- if STT fails → fallback to manual text input (or retry)
- if WebSocket disconnects → automatic reconnect
- if TTS fails → text-only response
- if audio capture fails → error message

---

## Sprint Retrospective: What Went Wrong

### Sprint 1: Foundation
**Delivered:**
- WebSocket client (connection management)
- Audio pipeline (buffering, VAD placeholder)
- Response filter (message categorization)
- Config system (loading, hot-reload)

**Missing:**
- ❌ Integration: WebSocket ← → Audio
- ❌ Real VAD (WebRTC)
- ❌ Hardware audio driver setup
- ❌ Wake word wiring

### Sprint 2: Tool Integration
**Delivered:**
- Middleware for message marking
- Tool chain manager
- Multi-step tool handling
- Bug tracking system

**Missing:**
- ❌ Tools themselves (no STT, TTS, LLM clients)
- ❌ Wiring to voice pipeline
- ❌ Error recovery hooks in main loop

### Sprint 3: Persistence
**Delivered:**
- SQLite database
- Session manager
- History persistence
- Context windows
- Session recovery

**Missing:**
- ❌ Session recovery only for WebSocket, not whole audio pipeline
- ❌ No persistence of "where we were" in voice conversation

### Sprint 4: Polish
**Delivered:**
- Barge-in/interruption (Issue #8)
- Extensive tests
- System test plan

**Missing:**
- ❌ Barge-in not actually connected to anything useful
- ❌ No end-to-end interruption demo
- ❌ Tests test code paths, not actual user experience

---

## The Fundamental Design Flaw

**Architecture Decision:** Sprint-based component isolation

**Better Architecture:** Functional slice integration

### What We Did (Component-First):
```
Sprint 1: WebSocket
Sprint 2: Middleware  
Sprint 3: Persistence
Sprint 4: Interruption

Result: Parts that don't connect
```

### What We Should Have Done (Flow-First):
```
Phase 1: Hello World Voice Pipeline
  - Minimal: capture → mock STT → echo → mock TTS → playback
  - Goal: Prove the loop works

Phase 2: Add Real Services
  - Replace mock STT with Whisper
  - Replace mock TTS with Piper
  - Add real WebSocket to OpenClaw

Phase 3: Add Persistence
  - Save conversations
  - Recover sessions

Phase 4: Add Polish
  - Interruption
  - Wake word
  - Performance tuning
```

---

## Path to a Functional Product

### Option A: Complete Rewrite (6-8 weeks)
**Approach:** Start fresh with working example

**Steps:**
1. Create minimal `voice_loop.py` that captures audio and prints transcript
2. Add STT (Whisper) integration
3. Add WebSocket send/receive
4. Add TTS (Piper) and playback
5. Wire into main event loop
6. Add configuration for audio devices
7. Test end-to-end
8. Incrementally add back: persistence, interruption, etc.

**Pros:** Clean slate, known working foundation
**Cons:** Lose existing test coverage, time intensive

### Option B: Surgical Integration (2-3 weeks)
**Approach:** Wire existing modules together

**Steps:**
1. **Week 1: Core Loop**
   - Create `src/bridge/voice_orchestrator.py`
   - Wire AudioPipeline → WebSocketClient (bidirectional)
   - Integrate STT (Whisper) and TTS (Piper)
   - Simple control flow: wake word → listen → process → speak → idle

2. **Week 2: Hardware Integration**
   - Install webrtcvad, sounddevice
   - Configure audio devices
   - Test with real microphone/speakers
   - Fix latency issues

3. **Week 3: Polish & Recovery**
   - Add error handling
   - Connect session persistence
   - Enable barge-in
   - Performance tuning

**Pros:** Reuses existing code, keeps tests
**Cons:** May inherit architectural debt

### Recommendation: Option B

**Reasoning:**
- The infrastructure IS good (509 tests prove that)
- The design is sound (modular, well-documented)
- What's missing is **integration**, not components
- Complete rewrite would waste 3+ months of work

---

## Immediate Action Plan

### Critical Path to MVP (2 weeks)

**Week 1: Make It Speak**

**Day 1-2: Core Orchestrator**
```python
# src/bridge/voice_orchestrator.py
class VoiceOrchestrator:
    """Wires together all components for voice loop."""
    
    def __init__(self):
        self.audio = AudioPipeline()
        self.websocket = WebSocketClient()
        self.stt = WhisperSTT()  # NEW
        self.tts = PiperTTS()    # NEW
        self.sessions = SessionManager()
    
    async def run_voice_loop(self):
        """Main voice interaction loop."""
        while True:
            # 1. Wait for wake word OR user input
            if await self.wait_for_wake_or_input():
                # 2. Capture audio until silence
                audio = await self.audio.capture_until_silence()
                # 3. Transcribe
                text = await self.stt.transcribe(audio)
                # 4. Send to OpenClaw
                await self.websocket.send_voice(text)
                # 5. Receive response
                response = await self.websocket.receive()
                # 6. Speak response
                await self.tts.speak(response)
```

**Day 3-4: Whisper Integration**
- Add faster-whisper dependency
- Create `src/bridge/stt_whisper.py`
- Test with sample audio file
- Verify latency < 1s on RTX 5070

**Day 5: Piper Integration**
- Add piper-tts dependency
- Create `src/bridge/tts_piper.py`
- Test voice generation
- Verify timing

**Weekend**: End-to-end test with hardcoded query

**Week 2: Make It Production-Ready**

**Day 6-7: Wake Word**
- Move `wakeword.py` into `src/bridge/`
- Create `WakeWordDetector` class
- Wire to voice orchestrator
- Test: "Computer" → listening → response

**Day 8-9: Hardware Audio**
- Install portaudio, webrtcvad
- Configure audio devices in config.yaml
- Test with real microphone
- Fix latency/buffer issues

**Day 10: Error Recovery**
- Add try/catch around voice loop
- Implement fallback strategies
- Add logging at each step
- Test failure scenarios

**Deliverable:** Working voice assistant

---

## Technical Debt to Address

### High Priority
1. **audio_pipeline.py** - Replace mock VAD with webrtcvad
2. **websocket_client.py** - Add send_voice() convenience method
3. **config.py** - Add audio device auto-discovery
4. **barge_in_integration.py** - Currently unused, needs wiring

### Medium Priority
5. **session_recovery.py** - Only recovers WebSocket, not audio state
6. **bug_tracker.py** - Good to have, but focus on preventing bugs first
7. **response_filter.py** - Filtering works, but doesn't control audio flow

### Low Priority
8. **context_window.py** - Optimization for later
9. **tool_chain_manager.py** - Advanced feature for v2

---

## Success Criteria

**MVP is successful when:**

1. **Basic Function**
   - Say "computer"
   - Ask "What time is it?"
   - Hear correct answer spoken within 3 seconds

2. **Robustness**
   - Handles network hiccup → reconnects automatically
   - Handles no audio → clear error message
   - Handles STT failure → asks to repeat

3. **Performance**
   - Wake word → response: < 3 seconds
   - Whisper inference: < 1 second (GPU)
   - No audio dropouts or stuttering

---

## Conclusion

**What We Have:** Excellent infrastructure, no product  
**What's Needed:** Integration of existing components  
**Time to MVP:** 2 weeks with focused effort  
**Recommended Path:** Option B - Surgical Integration

**Next Step:** Create voice_orchestrator.py and wire the existing pipeline.

**Blocker:** Webrtcvad installation and audio device configuration.

**Risk:** If audio hardware issues can't be resolved quickly, product will remain non-functional.

---

**Document Author:** OpenClaw Agent  
**Review Status:** Complete  
**Action Required:** Decision on Option A vs Option B
