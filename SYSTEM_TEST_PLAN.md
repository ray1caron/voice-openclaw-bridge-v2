# Voice-OpenClaw Bridge v2 - System Test Plan

## Document Information
**Version:** 2.0  
**Date:** 2026-02-27  
**Last Revised:** 2026-02-27 12:40 PST  
**Status:** Active  
**Author:** OpenClaw Agent
**Phase Status:** Phase 1-5 Complete ✅

---

## Executive Summary

This document provides a comprehensive test plan for the Voice-OpenClaw Bridge v2 system. It covers all sprints, integration points, and acceptance criteria to ensure system reliability before production deployment.

## System Overview

The Voice-OpenClaw Bridge v2 is a bidirectional voice interface that connects audio I/O with OpenClaw AI, enabling natural voice conversations with interruption support and persistent session memory.

### Architecture Components

```
┌─────────────────────────────────────────────────────────────────┐
│                        USER INTERFACE                            │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 5: VOICE ASSISTANT                     │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Wake Word    │  │ STT Worker  │  │ TTS Worker           │  │
│  │ Detector     │  │ (Whisper)   │  │ (Piper)              │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    AUDIO PIPELINE (Sprint 1/4)                  │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Audio I/O    │  │ VAD         │  │ Barge-In Handler     │  │
│  │ Capture      │◄─┤ Detection   │◄─┤ (Issue #8)           │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│               VOICE ORCHESTRATOR (Phase 5 Day 4)                │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Main Event   │  │ State Mgr   │  │ Statistics           │  │
│  │ Loop         │  │ (5 states)  │  │ & Callbacks          │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                  WEBSOCKET CLIENT (Sprint 1)                    │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Connection   │  │ Message     │  │ Session Recovery     │  │
│  │ Management   │◄─┤ Protocol    │◄─┤ (Sprint 3)           │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              OPENCLAW MIDDLEWARE (Sprint 2)                     │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Message      │  │ Tool Chain  │  │ Response Filtering   │  │
│  │ Marking      │◄─┤ Manager     │◄─┤                      │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│           CONVERSATION PERSISTENCE (Sprint 3)                   │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Session      │  │ History     │  │ Context Window       │  │
│  │ Manager      │  │ Manager     │  │ Manager              │  │
│  └──────────────┘  └─────────────┘  └──────────────────────┘  │
│                           │
│                           ▼
│                  ┌──────────────────┐
│                  │ SQLite Database  │
│                  └──────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

---

## Phase 5: Voice Assistant Integration

**Status:** ✅ Complete  
**Version:** 0.2.0  
**Completion Date:** 2026-02-27  

### Phase 5 Components

| Component | Days | Lines | Tests | Status |
|-----------|------|-------|-------|--------|
| STT Worker (Whisper) | Day 1 | 437 | 27 | ✅ Complete |
| TTS Worker (Piper) | Day 2 | 270 | 24 | ✅ Complete |
| Wake Word Detector | Day 3 | 280 | 22 | ✅ Complete |
| Voice Orchestrator | Day 4 | 430 | 26 | ✅ Complete |
| Audio I/O Setup | Day 5 | ~100 | N/A | ✅ Complete |
| E2E Testing | Day 6 | ~500 | 7 | ✅ Complete |
| **Total** | **6 days** | **~2,017** | **106** | **✅ 100%** |

### Phase 5 Test Audio Fixtures

**Location:** `tests/fixtures/audio/`  

**Purpose:** Real audio files for end-to-end testing

**Files:** 8 synthetic audio files (FLAC + WAV each)
- `silence_2s.flac` - Silence detection testing
- `tone_440hz_2s.flac` - Audio path testing
- `speech_like_2s.flac` - STT pipeline testing
- `speech_short_1s.flac` - Quick tests
- `speech_long_5s.flac` - Long transcriptions
- `speech_low_volume.flac` - Normalization testing
- `speech_high_volume.flac` - Clipping testing
- `speech_stereo_2s.flac` - Channel handling

**Generation:** `python3 generate_test_audio.py`

---

## Sprint Status

| Sprint | Status | Completion | Key Components |
|--------|--------|------------|----------------|
| Sprint 1: Foundation | ✅ Complete | 100% | WebSocket, Audio Pipeline, Config |
| Sprint 2: Tool Integration | ✅ Complete | 100% | Middleware, Tool Chains |
| Sprint 3: Conversation Persistence | ✅ Complete | 100% | SQLite persistence, recovery |
| Sprint 4: Polish | ✅ Complete | 100% | Barge-In (Issue #8) |
| **Phase 5: Voice Assistant** | **✅ Complete** | **100%** | **STT, TTS, Wake Word, Orchestrator** |

---

## Test Categories

### 1. Unit Tests
**Scope:** Individual module functionality  
**Location:** `tests/unit/`  
**Count:** ~500+ tests (Phase 5 adds 99)  
**Status:** All passing  

### 2. Integration Tests
**Scope:** Module interactions  
**Location:** `tests/integration/`  
**Count:** ~60+ tests (Phase 5 adds 7 E2E)  
**Status:** All passing  

### 3. Phase 5 Voice Assistant Tests
**Scope:** Voice component integration  
**Location:** `tests/unit/` + `tests/integration/`  
**Count:** 106 tests (99 unit + 7 E2E)  
**Status:** Complete  

**Phase 5 Unit Tests:**
- `test_stt_worker.py` - STT Worker (27 tests)
- `test_tts_worker.py` - TTS Worker (24 tests)
- `test_wake_word.py` - Wake Word Detector (22 tests)
- `test_voice_orchestrator.py` - Voice Orchestrator (26 tests)

**Phase 5 E2E Tests:**
- `test_voice_e2e.py` - Voice Assistant End-to-End (7 tests)

### 4. System Tests
**Scope:** End-to-end workflows  
**Location:** This plan defines scope  
**Count:** TBD  
**Status:** Under development  

---

## Test Environment

### Hardware Requirements
- Microphone input device
- Speaker output device  
- Network connectivity (for WebSocket)

### Software Requirements
- Python 3.10, 3.11, or 3.12
- pytest 9.0+
- pytest-asyncio 1.3+
- sounddevice (optional, for real audio)
- `tzdata>=2023.3` (required for Python 3.12 for pydantic-settings timezone support)

### Phase 5 Dependencies (Voice Assistant)
These are required for Phase 5 voice functionality:

| Component | Package | Version | Purpose |
|-----------|---------|---------|---------|
| STT | `faster-whisper` | >=1.0 | Speech-to-text (Whisper models) |
| TTS | `piper-tts` | >=1.2 | Text-to-speech synthesis |
| TTS Engine | `onnxruntime` | >=1.16 | ONNX inference for TTS |
| Audio | `numpy`, `sounddevice`, `soundfile` | Latest | Audio processing |
| Wake Word | `pvporcupine`, `pvrecorder` | Latest | Wake word detection |
| WebSocket | `websockets` | >=12.0 | OpenClaw client |

**Installation:**
```bash
pip install --break-system-packages faster-whisper piper-tts onnxruntime \
                                     numpy sounddevice soundfile \
                                     pvporcupine pvrecorder websockets tzdata
```

### Python 3.12 Specific Requirements
For Python 3.12 environments, install tzdata:
```bash
pip install tzdata
```

This is required because:
- `pydantic-settings>=2.0` uses `zoneinfo._tzpath` for timezone configuration
- Python 3.12 requires timezone database (tzdata) for proper `zoneinfo` support
- Without tzdata, config loading fails with `KeyError: 'zoneinfo._tzpath'`

### Environment Variables
```bash
export VOICE_BRIDGE_CONFIG_PATH=/path/to/config.yaml
export GITHUB_TOKEN=your_token_here
export OPENCLAW_API_KEY=your_key_here
```

---

## System Test Scope

### Phase 5 End-to-End Tests (Voice Assistant)

#### ST-P5-001: Wake Word to Response Complete Flow
**Objective:** Verify complete voice assistant cycle  
**Priority:** P0  
**Dependencies:** Phase 5 components, audio devices

**Test Steps:**
1. Initialize VoiceOrchestrator with test audio fixtures
2. Simulate wake word detection
3. Simulate speech capture using `tests/fixtures/audio/speech_short_1s.flac`
4. Verify STT transcription succeeds
5. Send mock OpenClaw response
6. Verify TTS synthesis succeeds
7. Verify audio playback completes

**Expected Results:**
- Wake word detected in mock
- Audio captured from test file
- STT transcribes (silently, no audio output in test)
- OpenClaw receives transcription
- TTS synthesizes response (mock audio in test)
- Statistics tracked correctly

**Acceptance Criteria:**
- [ ] Flow completes without errors
- [ ] Statistics: 1 interaction recorded
- [ ] State transitions: IDLE → LISTENING → PROCESSING → SPEAKING

---

#### ST-P5-002: Barge-In Interruption During TTS
**Objective:** Verify interruption behavior during TTS playback  
**Priority:** P0  
**Dependencies:** Phase 5 components

**Test Steps:**
1. Start voice interaction
2. Begin TTS playback (mocked streaming)
3. Trigger barge-in interruption at chunk 3
4. Verify TTS stops
5. Verify interruption event fired
6. Verify state returns to LISTENING

**Expected Results:**
- TTS streaming stops at interruption point
- BargeInHandler detects interruption
- Orchestrator updates state correctly
- Session marked as interrupted

**Acceptance Criteria:**
- [ ] TTS stops within mock interruption detection
- [ ] Interruption event type = BARGE_IN
- [ ] State = LISTENING after interruption

---

#### ST-P5-003: Multiple Sequential Interactions
**Objective:** Verify orchestrator handles multiple voice commands  
**Priority:** P1  
**Dependencies:** Phase 5 components

**Test Steps:**
1. Run 5 sequential interactions
2. Each with different mock transcription
3. Verify statistics track correctly
4. Verify state machine reset after each
5. Verify no memory leaks

**Expected Results:**
- 5 interactions completed
- Stats: total = 5, successful = 5
- State resets after each
- Memory usage stable

**Acceptance Criteria:**
- [ ] 5 interactions, 5 successful
- [ ] Average time calculated correctly
- [ ] No state pollution between interactions

---

#### ST-P5-004: Callback System Functionality
**Objective:** Verify event callbacks fire correctly  
**Priority:** P1  
**Dependencies:** Phase 5 components

**Test Steps:**
1. Set up all callbacks (wake_word, transcription, response, error)
2. Run complete interaction flow
3. Verify each callback fires correctly
4. Verify callback receives correct data

**Expected Results:**
- All 4 callbacks fire
- Callbacks receive correct event types/data
- No callback crashes

**Acceptance Criteria:**
- [ ] WakeWordEvent passed to callback
- [ ] Transcription text passed to callback
- [ ] Response text passed to callback
- [ ] No errors in callbacks

---

### ST-001: Voice Pipeline End-to-End
**Objective:** Verify complete audio → OpenClaw → response flow  
**Priority:** P0  
**Dependencies:** Audio devices, WebSocket connection

**Test Steps:**
1. Initialize audio pipeline with test devices
2. Start WebSocket connection to OpenClaw
3. Simulate audio input (or use recorded sample)
4. Verify audio captured and buffered
5. Wait for response from OpenClaw
6. Verify response received via WebSocket
7. Verify TTS playback (or audio output buffer)

**Expected Results:**
- Audio captured without errors
- WebSocket message sent successfully
- Response received within 5 seconds
- Audio output produced

**Acceptance Criteria:**
- [ ] End-to-end latency < 5 seconds
- [ ] No audio glitches or dropouts
- [ ] Response matches expected format

---

### ST-002: Session Persistence Across Disconnect
**Objective:** Verify conversation survives WebSocket reconnect  
**Priority:** P0  
**Dependencies:** Sprint 3 persistence layer

**Test Steps:**
1. Start bridge and establish WebSocket connection
2. Send 3 voice queries, waiting for responses
3. Verify conversation stored in database
4. Disconnect WebSocket (simulate network failure)
5. Reconnect WebSocket
6. Send follow-up query
7. Verify context includes previous conversation

**Expected Results:**
- Session persisted to database during conversation
- Session recovered on reconnect
- Context window includes previous turns
- Follow-up query understood with context

**Acceptance Criteria:**
- [ ] Session restored within 2 seconds
- [ ] All previous turns in context
- [ ] No data loss

---

### ST-003: Barge-In During Response
**Objective:** Verify user can interrupt assistant response  
**Priority:** P0  
**Dependencies:** Issue #8 implementation

**Test Steps:**
1. Start bridge and connect
2. Send query that generates long response
3. Wait for TTS playback to begin
4. Speak/interrupt while assistant is speaking
5. Verify interrupt detected
6. Verify TTS stopped
7. Verify bridge returns to listening state

**Expected Results:**
- Interrupt latency < 100ms
- TTS playback stops immediately
- New audio capture begins
- Interrupt signal sent to OpenClaw

**Acceptance Criteria:**
- [ ] Interrupt latency < 100ms
- [ ] TTS stop within 50ms
- [ ] No audio artifacts

---

### ST-004: Tool Chain Recovery
**Objective:** Verify tool execution survives disconnect  
**Priority:** P1  
**Dependencies:** Sprint 2 + 3

**Test Steps:**
1. Start multi-step tool chain execution
2. Wait for first tool to complete
3. Disconnect during second tool execution
4. Reconnect WebSocket
5. Verify tool state recovered
6. Complete remaining tool executions

**Expected Results:**
- Tool executions persisted
- State recovered correctly
- Resume from interruption point

**Acceptance Criteria:**
- [ ] Tool state accurately recovered
- [ ] No duplicate executions
- [ ] Results consistent

---

### ST-005: Concurrent Session Isolation
**Objective:** Verify multiple sessions don't interfere  
**Priority:** P1  
**Dependencies:** Sprint 3

**Test Steps:**
1. Create Session A with conversation
2. Create Session B with different conversation
3. Interleave messages to both sessions
4. Verify each session's context is isolated
5. Verify database integrity

**Expected Results:**
- Sessions operate independently
- No cross-contamination of context
- Database records properly isolated

**Acceptance Criteria:**
- [ ] Session contexts isolated
- [ ] No data leakage between sessions
- [ ] Concurrent operations safe

---

### ST-006: Error Recovery Scenarios
**Objective:** Verify graceful handling of failures  
**Priority:** P1  

**Sub-tests:**

#### ST-006.1: STT Failure Fallback
**Test:** Simulated STT failure during audio processing  
**Expected:** Fallback to error message, bridge continues

#### ST-006.2: Network Outage
**Test:** Disconnect network during conversation  
**Expected:** Automatic reconnection, session recovery

#### ST-006.3: Database Lock
**Test:** Simulated database lock condition  
**Expected:** Degrade to memory-only, clear error logged

#### ST-006.4: TTS Failure
**Test:** TTS service unavailable  
**Expected:** Response still sent via WebSocket, text available

---

### ST-007: Performance Benchmarks
**Objective:** Verify system meets performance targets  
**Priority:** P1  

**Metrics:**

| Metric | Target | Measurement |
|--------|--------|-------------|
| End-to-end latency | < 2 seconds |voice input to audio output |
| Interrupt latency | < 100 ms |speech detected to interrupt signal |
| Session recovery | < 2 seconds |disconnect to recovered session |
| Context window prune | < 50 ms |1000 turns to < 200 tokens |
| Database write | < 10 ms |per message write |
| Memory growth | < 100 MB/hour |over 8 hour session |
| Concurrent sessions | 20 |simultaneous active sessions |

---

### ST-008: Long-Running Stability
**Objective:** Verify system stability over extended period  
**Priority:** P2  
**Duration:** 8 hours minimum

**Test Steps:**
1. Start bridge with monitoring enabled
2. Run continuous conversation loop
3. Every 15 minutes:
   - Send query
   - Wait for response
   - Verify no errors
   - Check memory usage
4. After 8 hours, verify:
   - No memory leaks
   - No errors in logs
   - Performance consistent with start

**Acceptance Criteria:**
- [ ] 8 hours continuous operation
- [ ] Memory growth < 100 MB
- [ ] Error count = 0

---

## Regression Test Suite

Before each release, execute:

```bash
# Full unit test suite
python3 -m pytest tests/unit -v

# Integration tests
python3 -m pytest tests/integration -v

# Performance benchmarks
python3 -m pytest tests/integration/test_performance.py -v

# System tests (this document)
python3 -m pytest tests/system -v
```

---

## Test Execution Schedule

### Daily (CI)
- Unit tests
- Fast integration tests
- Lint checks

### Weekly
- Full integration test suite
- Performance benchmarks
- Coverage reports

### Pre-Release
- Full system test suite
- Long-running stability test
- Regression test suite

---

## Bug Tracking

All test failures create bug reports via bug tracker:

```python
from bridge.bug_tracker import capture_bug
from bridge.bug_tracker import BugSeverity

capture_bug(
    message="Test failed: ST-003",
    severity=BugSeverity.HIGH,
    context={"test_case": "ST-003", "barge_in": True}
)
```

**Severity Guide:**
- **CRITICAL:** Test prevents system from operating
- **HIGH:** Core functionality broken
- **MEDIUM:** Feature impaired but workarounds exist
- **LOW:** Cosmetic or non-blocking issue

---

## Known Limitations

1. **Audio Devices:** Tests marked with `@pytest.mark.hardware` require physical devices
2. **Network:** Some tests require active OpenClaw server connection
3. **Performance:** Benchmarks may vary based on hardware

---

## Test Success Criteria

**Minimum for Release:**
- All unit tests passing (100%)
- All integration tests passing (100%)
- All P0 system tests passing (100%)
- All P1 system tests > 90% passing
- No CRITICAL or HIGH severity bugs open

**Excellence:**
- All tests passing (100%)
- Zero open bugs
- Performance metrics exceed targets

---

## Next Steps

1. Execute ST-001 through ST-003 (P0 tests)
2. Fix any blocking issues
3. Execute ST-004 through ST-006 (P1 tests)
4. Execute ST-007 (Performance benchmarks)
5. Execute ST-008 if time permits

---

## Appendix A: Test Scripts

### Quick System Test
```python
# tests/system/quick_test.py
"""Quick 5-minute system health check."""

import pytest

class TestSystemHealth:
    def test_imports(self):
        """Verify all modules import correctly."""
        from audio.barge_in import BargeInHandler
        from bridge.audio_pipeline import AudioPipeline
        from bridge.websocket_client import WebSocketClient
        assert True
    
    def test_database_connection(self):
        """Verify database is accessible."""
        from bridge.conversation_store import get_conversation_store
        store = get_conversation_store()
        assert store is not None
    
    @pytest.mark.asyncio
    async def test_barge_in_flow(self):
        """Quick barge-in functionality test."""
        from audio.barge_in import BargeInHandler
        handler = BargeInHandler()
        await handler.start_speaking()
        assert handler.state.name == "SPEAKING"
```

### Full System Test Runner
```python
# tests/system/run_system_tests.py
"""Execute full system test suite."""

import subprocess
import sys

def run_tests():
    """Run all system tests."""
    tests = [
        "ST-001", "ST-002", "ST-003",  # P0
        "ST-004", "ST-005", "ST-006",  # P1
        "ST-007", "ST-008",            # P1/P2
    ]
    
    for test in tests:
        result = subprocess.run(
            ["python3", "-m", "pytest", f"tests/system/{test}.py", "-v"],
            capture_output=True
        )
        print(f"{test}: {'PASS' if result.returncode == 0 else 'FAIL'}")

if __name__ == "__main__":
    run_tests()
```

---

## Appendix B: Troubleshooting

### Test Collection Fails
**Symptom:** `pytest` can't collect tests  
**Fix:** Check for syntax errors or missing `__init__.py`

### Audio Device Errors
**Symptom:** Tests fail with "no input device"  
**Fix:** Mark with `@pytest.mark.skip(reason="no hardware")`

### Database Locked
**Symptom:** SQLite errors about database locked  
**Fix:** Ensure tests use isolated temp databases

### Import Errors
**Symptom:** ModuleNotFoundError  
**Fix:** Run from project root, add `src/` to Python path

---

**Document Version:** 1.0  
**Last Updated:** 2026-02-26  
