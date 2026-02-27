# Voice-OpenClaw Bridge v2 - System Test Plan

## Document Information
**Version:** 1.0  
**Date:** 2026-02-26  
**Last Revised:** 2026-02-26 09:13 PST  
**Status:** Active  
**Author:** OpenClaw Agent

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
│                    AUDIO PIPELINE (Sprint 1/4)                  │
│  ┌──────────────┐  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Audio I/O    │  │ VAD         │  │ Barge-In Handler     │  │
│  │ Capture      │◄─┤ Detection   │◄─┤ (Issue #8)           │  │
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

## Sprint Status

| Sprint | Status | Completion | Key Components |
|--------|--------|------------|----------------|
| Sprint 1: Foundation | ✅ Complete | 100% | WebSocket, Audio Pipeline, Config |
| Sprint 2: Tool Integration | ✅ Complete | 100% | Middleware, Tool Chains |
| Sprint 3: Conversation Persistence | ✅ Complete | 100% | SQLite persistence, recovery |
| Sprint 4: Polish | ✅ Complete | 100% | Barge-In (Issue #8) |

---

## Test Categories

### 1. Unit Tests
**Scope:** Individual module functionality  
**Location:** `tests/unit/`  
**Count:** ~430 tests  
**Status:** All passing  

### 2. Integration Tests
**Scope:** Module interactions  
**Location:** `tests/integration/`  
**Count:** ~50+ tests  
**Status:** All passing  

### 3. System Tests
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
