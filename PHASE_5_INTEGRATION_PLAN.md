# Phase 5: System Integration

**Status:** Starting 2026-02-27
**Goal:** Wire voice components together into working end-to-end system
**Prerequisites:** Day 0 Spike (OpenClaw connectivity)

---

## Phase Overview

All 4 sprints are feature complete but not integrated:
- ✅ Sprint 1: WebSocket, Audio Pipeline, Config, Response Filter
- ✅ Sprint 2: Middleware, Tool Chain Manager, Multi-step handling
- ✅ Sprint 3: Session Persistence, History Manager, Context Windows
- ✅ Sprint 4: Barge-In, Interrupt Handling, System Tests

**Phase 5 connects the dots** to make it actually work.

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Wake Word Detection                      │
│                  (Porcupine "hey hal")                       │
└────────────────────┬────────────────────────────────────────┘
                     │ triggered
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Audio Pipeline                           │
│  ┌──────────┐    ┌──────┐    ┌──────────────┐              │
│  │ Capture  │───→│ VAD  │───→│ Audio Buffer │              │
│  └──────────┘    └──────┘    └──────────────┘              │
└────────────────────┬────────────────────────────────────────┘
                     │ speech detected
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  Speech-to-Text (STT)                       │
│                     (faster-whisper)                        │
└────────────────────┬────────────────────────────────────────┘
                     │ transcript
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                OpenClaw HTTP Client                         │
│           POST /api/sessions/main/send                       │
└────────────────────┬────────────────────────────────────────┘
                     │ response
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  Response Filter                            │
│        (filter tool calls, thinking, etc.)                  │
└────────────────────┬────────────────────────────────────────┘
                     │ speakable text
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                  Text-to-Speech (TTS)                       │
│                       (Piper TTS)                           │
└────────────────────┬────────────────────────────────────────┘
                     │ audio frames
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                    Audio Output                             │
│                   (sounddevice)                            │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration Tasks

### Day 0: Spike (BLOCKING GATE) ❓
- [ ] Run `spike_openclaw.py` to verify OpenClaw connectivity
- [ ] Document exact API shape in `docs/openclaw-api-notes.md`
- [ ] **Pass gate before proceeding**

### Day 1: OpenClaw HTTP Client
- [ ] Create `src/bridge/openclaw_client.py`
  - `OpenClawClient` class with `send_message()` method
  - Session management (list sessions, get session info)
  - Error handling and retries
- [ ] Write tests: `tests/unit/test_openclaw_client.py`
- [ ] Update config to include `openclaw.http` section

### Day 2: STT → OpenClaw Integration
- [ ] Connect Audio Pipeline → Whisper STT
- [ ] Connect STT output → OpenClawClient.send_message()
- [ ] Handle STT errors gracefully (empty transcript, timeout)
- [ ] Add metrics: STT latency, transcript accuracy

### Day 3: OpenClaw → TTS Integration
- [ ] Connect OpenClaw response → ResponseFilter
- [ ] Connect Response Filter → Piper TTS
- [ ] Connect TTS output → Audio Pipeline playback
- [ ] Add metrics: OpenClaw latency, TTS generation time

### Day 4: Wake Word & State Machine
- [ ] Integrate Porcupine wake word detection
- [ ] Connect wake word → Start recording
- [ ] Implement main state machine:
  - IDLE → LISTENING (wake word)
  - LISTENING → PROCESSING (speech end)
  - PROCESSING → SPEAKING (response ready)
  - SPEAKING → LISTENING (response done)
  - SPEAKING → INTERRUPTED (barge-in)
- [ ] Add barge-in support (already implemented in Sprint 4)

### Day 5: End-to-End Testing
- [ ] Execute ST-001: Voice Pipeline End-to-End
- [ ] Execute ST-002: Session Persistence Across Disconnect
- [ ] Execute ST-003: Barge-In During Response
- [ ] Verify performance benchmarks:
  - End-to-end latency < 2 seconds
  - Wake word response < 500ms
  - Interrupt latency < 100ms ✅ (already met)

### Day 6: Polish & Productionize
- [ ] Replace mock audio with real hardware I/O
- [ ] Test with real microphone and speakers
- [ ] Add graceful shutdown handling
- [ ] Update documentation (USER_GUIDE.md)
- [ ] Package installation script
- [ ] Demo: "Hey Hal, what time is it?" working end-to-end

---

## File Structure

```
src/bridge/
├── openclaw_client.py      # NEW - OpenClaw HTTP client
├── main.py                 # UPDATE - Main orchestrator
├── voice_pipeline.py       # NEW - Voice pipeline orchestration
└── state_machine.py        # NEW - Main state machine

src/audio/
├── stt_worker.py           # NEW - Speech-to-text worker
├── tts_worker.py           # NEW - Text-to-speech worker
└── wake_word.py            # NEW - Wake word detector

tests/
├── unit/
│   ├── test_openclaw_client.py  # NEW
│   ├── test_voice_pipeline.py   # NEW
│   └── test_state_machine.py    # NEW
└── integration/
    └── test_e2e_voice.py        # NEW - End-to-end voice test
```

---

## Dependencies Check

**Existing ✅:**
- httpx (HTTP client)
- faster-whisper (STT)
- piper-tts (TTS)
- sounddevice (audio I/O)
- webrtcvad (VAD)
- pvporcupine (wake word)

**Need to verify:**
- [ ] All dependencies installed in virtual environment
- [ ] Whisper model downloaded
- [ ] Piper voice model downloaded
- [ ] Porcupine access key configured

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| OpenClaw API changes | High | Document API shape in spike, version pinning |
| Hardware audio issues | Medium | Mock fallback, device discovery |
| Latency > 2s | Medium | Streaming TTS, parallel processing |
| Whisper accuracy | Medium | Configurable model size, retry |
| Session persistence | Low | Already implemented in Sprint 3 |

---

## Success Criteria

Phase 5 is complete when:
1. ✅ Day 0 spike passes (OpenClaw accessible)
2. ✅ All 6 days of tasks complete
3. ✅ ST-001, ST-002, ST-003 system tests pass
4. ✅ Real "Hey Hal" query works end-to-end
5. ✅ Barge-in interrupts working <100ms
6. ✅ Documentation updated (USER_GUIDE.md)
7. ✅ Installation script works

---

## Next Steps

1. **Immediate:** Run `python3 spike_openclaw.py`
2. **If pass:** Create `docs/openclaw-api-notes.md` and start Day 1
3. **If fail:** Debug OpenClaw gateway before proceeding

---

**Created:** 2026-02-27
**Owner:** Hal
**Status:** Day 0 spike pending approval