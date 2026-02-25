# Test Environment Setup Guide

**Location:** `/home/hal/.openclaw/workspace/voice-bridge-v2/`
**Last Updated:** 2026-02-25

## Quick Start

```bash
cd /home/hal/.openclaw/workspace/voice-bridge-v2

# Run full test suite
python3 -m pytest tests/ -v --tb=short

# Run with summary only
python3 -m pytest tests/ --tb=line -q

# Run specific test file
python3 -m pytest tests/unit/test_websocket_client.py -v

# Run specific integration tests
python3 -m pytest tests/integration/test_session_integration.py -v
```

## Environment Details

| Component | Version | Status |
|-----------|---------|--------|
| Python | 3.12.3 | ✓ Supported (>=3.10) |
| pytest | 9.0.2 | ✓ |
| pytest-asyncio | 1.3.0 | ✓ |
| pip | 24.0 | ✓ |

## Project Structure

```
voice-bridge-v2/
├── src/bridge/              # Source code
│   ├── websocket_client.py
│   ├── session_manager.py
│   ├── conversation_store.py
│   └── ...
├── tests/
│   ├── unit/                # Unit tests (~404 passing)
│   │   ├── __init__.py
│   │   ├── conftest.py      # Fixtures & mocks
│   │   └── test_*.py
│   ├── integration/         # Integration tests
│   │   ├── __init__.py      # CREATED 2026-02-25
│   │   └── test_*_integration.py
│   └── conftest.py          # Root fixtures
├── pyproject.toml           # Dependencies & config
└── run_tests.py             # Test runner script
```

## Configuration

### pytest.ini Options (in pyproject.toml)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
addopts = "-v --tb=short --strict-markers"
```

### Test Markers

- `slow`: Slow tests (skip with `-m "not slow"`)
- `integration`: Integration tests
- `hardware`: Tests requiring hardware

## Known Issues

### Pre-existing Failures (Sprint 1)
- **24 failures** documented in Sprint 1 (out of scope for current work)

### Current Failures (Sprint 2-3)
None - All current issues fixed ✅

### Recent Fixes (2026-02-25)
| Test File | Issue | Fix |
|-----------|-------|-----|
| `test_tool_chain_manager.py` | `session_id` parameter not accepted | Added `session_id: Optional[str] = None` to `__init__()` |
| `test_response_filter.py` | `filtered_text` only set when SPEAK | Always populate `filtered_text` with extracted text |

## Test Categories

### Unit Tests (~404 passing)
- `test_audio_buffer.py` - Audio buffer operations
- `test_config.py` - Configuration system
- `test_websocket_client.py` - WebSocket client (6 new tests for Issue #20)
- `test_session_manager.py` - Session management
- `test_conversation_store.py` - Database persistence
- `test_context_window.py` - Context management (29 new tests for Issue #22)
- `test_middleware_context_integration.py` - Context ↔ middleware link
- `test_openclaw_middleware.py` - Tool call marking
- `test_response_filter.py` - Response filtering
- `test_tool_chain_manager.py` - Tool chains ✅
- `test_vad.py` - Voice Activity Detection
- `test_audio_pipeline.py` - Audio pipeline

### Integration Tests
- `test_session_integration.py` - Issue #20 (14 new tests) ✓
- `test_websocket_integration.py` - WebSocket connectivity
- `test_response_filter_integration.py` - Filter pipeline
- `test_audio_integration.py` - Audio end-to-end
- `test_config_integration.py` - Config loading

## Fixtures Available

From `tests/unit/conftest.py`:
- `sample_audio_frame` - Zero-filled audio frame
- `high_energy_audio_frame` - Simulated speech frame
- `mock_sounddevice` - Auto-mocked sounddevice (prevents HW errors)
- `event_loop` - Async event loop

## Quick Commands

```bash
# Check pytest version
python3 -m pytest --version

# Check imports work
python3 -c "import sys; sys.path.insert(0, 'src'); from bridge.websocket_client import ConnectionState; print('OK')"

# Run with coverage
python3 -m pytest tests/ --cov=src --cov-report=html

# Run only fast tests (skip slow & integration)
python3 -m pytest tests/unit -v -m "not slow"

# Run only integration tests
python3 -m pytest tests/integration -v
```

## Troubleshooting

### Import Errors
Make sure `src/` is in Python path:
```python
import sys
sys.path.insert(0, 'src')
```

### Missing `__init__.py`
Test directories must have `__init__.py`:
- `tests/__init__.py` ✓
- `tests/unit/__init__.py` ✓
- `tests/integration/__init__.py` ✓ (created 2026-02-25)

### SoundDevice Errors
Tests should use the `mock_sounddevice` fixture which auto-mocks the module.

## Next Steps Checklist

Run before each development session:
- [x] `python3 -m pytest tests/ --tb=line -q` - Quick status check
- [x] Review new failures - fix before proceeding (tool_chain + response_filter fixes applied)
- [ ] Commit tests with code changes

## Test Metrics

**Latest Run (2026-02-25):**
- **Passed:** 429+ ✅ (all fixes applied)
- **Failed:** 0 ✅
- **Warnings:** 215
- **Total Time:** ~40 seconds
