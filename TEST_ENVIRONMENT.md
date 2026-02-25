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

# Run E2E workflow tests (Issue #24)
python3 -m pytest tests/integration/test_e2e_workflow.py -v

# Run performance tests (Issue #24)
python3 -m pytest tests/integration/test_performance.py -v -m "performance"

# Run CI test suite (fast, excludes slow tests)
python3 -m pytest tests/ -v -m "not slow and not hardware"
```

## Environment Details

| Component | Version | Status |
|-----------|---------|--------|
| Python | 3.12.3 | ✓ Supported (>=3.10) |
| pytest | 9.0.2 | ✓ |
| pytest-asyncio | 1.3.0 | ✓ |
| pytest-cov | 4.0.0 | ✓ |
| pip | 24.0 | ✓ |

### CI Environment (GitHub Actions)

The CI pipeline runs on **Ubuntu Latest** with the following matrix:

| Python Version | Status | Use Case |
|----------------|--------|----------|
| 3.10 | ✓ Supported | Minimum supported |
| 3.11 | ✓ Supported | Current stable |
| 3.12 | ✓ Supported | Recommended |

**CI Pipeline Stages:**
1. **Lint** - Code formatting and static analysis (ruff, mypy, black)
2. **Unit Tests** - Fast unit tests on Python 3.10, 3.11, 3.12
3. **Integration Tests** - E2E and integration tests
4. **Performance Tests** - Latency and memory benchmarks (PRs + scheduled)
5. **Coverage** - Generate coverage reports
6. **Security** - Bandit security scan
7. **Build** - Package build verification

See `.github/workflows/ci.yml` for full configuration.

## Project Structure

```
voice-bridge-v2/
├── src/bridge/              # Source code
│   ├── websocket_client.py
│   ├── session_manager.py
│   ├── conversation_store.py
│   ├── context_window.py
│   ├── response_filter.py
│   ├── session_recovery.py
│   ├── audio_pipeline.py
│   └── ...
├── tests/
│   ├── unit/                # Unit tests (~404 passing)
│   │   ├── __init__.py
│   │   ├── conftest.py      # Fixtures & mocks
│   │   └── test_*.py
│   ├── integration/         # Integration tests (Issue #24)
│   │   ├── __init__.py
│   │   ├── test_session_integration.py      # Issue #20 (14 tests)
│   │   ├── test_websocket_integration.py
│   │   ├── test_response_filter_integration.py
│   │   ├── test_audio_integration.py
│   │   ├── test_config_integration.py
│   │   ├── test_session_recovery_integration.py
│   │   ├── test_e2e_workflow.py             # Issue #24 (NEW)
│   │   └── test_performance.py              # Issue #24 (NEW)
│   └── conftest.py          # Root fixtures
├── .github/workflows/       # CI/CD configuration
│   └── ci.yml               # GitHub Actions (Issue #24 - NEW)
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
markers = [
    "slow: marks tests as slow (deselect with '-m 'not slow'')",
    "integration: marks tests as integration tests",
    "hardware: marks tests that require hardware",
    "performance: marks performance/benchmark tests",  # #24
]
```

### CI/CD Configuration

The repository includes GitHub Actions CI at `.github/workflows/ci.yml`:

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` or `develop`
- Scheduled daily run at 3 AM UTC

**Jobs:**
- `lint` - Ruff, mypy, black checks
- `unit-tests` - Matrix across Python 3.10/3.11/3.12
- `integration-tests` - E2E and integration tests
- `performance-tests` - Latency and memory benchmarks
- `coverage` - Coverage report generation
- `security` - Bandit security scan
- `build` - Package build verification
- `summary` - Test results aggregation

### Test Markers

| Marker | Description | Skip Flag |
|--------|-------------|-----------|
| `slow` | Tests taking >5 seconds | `-m "not slow"` |
| `integration` | Integration/E2E tests | `-m "not integration"` |
| `performance` | Performance benchmarks | `-m "not performance"` |
| `hardware` | Tests requiring audio hardware | `-m "not hardware"` |

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

### Integration Tests (Issue #24 - New)

#### `test_e2e_workflow.py` - End-to-End Tests

Tests the complete voice bridge workflow:
- **Full Voice Pipeline** (`test_full_voice_to_voice_pipeline`) - Complete flow: Audio → STT → WebSocket → OpenClaw → Filter → TTS → Playback
- **Session Lifecycle** (`test_session_create_persist_restore_expire`) - Create → Persist → Restore → Expire
- **Context Window Integration** (`test_context_window_pruning_under_memory_pressure`) - Memory pressure handling
- **Concurrent Sessions** (`test_concurrent_session_handling`) - Multiple session handling
- **Error Recovery** (`test_network_failure_recovery`, `test_stt_failure_fallback`, `test_tts_failure_graceful_degradation`)

**Test Classes:**
- `TestFullVoicePipeline` - Complete E2E workflow tests
- `TestSessionLifecycleE2E` - Session lifecycle integration
- `TestContextWindowIntegration` - Context window integration
- `TestConcurrentSessionHandling` - Concurrent session tests
- `TestErrorRecovery` - Error recovery scenarios
- `TestE2EAcceptanceCriteria` - Issue #24 acceptance criteria
- `TestBargeInIntegration` - Barge-in/interruption tests
- `TestMessageOrdering` - Message sequencing tests

#### `test_performance.py` - Performance Benchmarks

Tests performance requirements:
- **Latency Benchmarks** - E2E < 2s target, filter < 50ms
- **Memory Usage** - Growth thresholds, stability tests
- **Concurrent Load** - Scalability tests

**Performance Thresholds:**
```python
MAX_E2E_LATENCY_MS = 2000        # 2 seconds for full pipeline
MAX_FILTER_LATENCY_MS = 50        # 50ms for response filter
MAX_MEMORY_GROWTH_MB = 100        # 100MB max memory growth
MAX_CONCURRENT_SESSIONS = 20      # Max concurrent sessions
```

**Test Classes:**
- `TestLatencyBenchmarks` - End-to-end latency tests
- `TestMemoryBenchmarks` - Memory usage and stability
- `TestConcurrentLoad` - Load testing
- `TestStability` - Long-running stability
- `TestPerformanceReport` - Summary reporting

### Existing Integration Tests
- `test_session_integration.py` - Issue #20 (14 new tests) ✓
- `test_websocket_integration.py` - WebSocket connectivity
- `test_response_filter_integration.py` - Filter pipeline
- `test_audio_integration.py` - Audio end-to-end
- `test_config_integration.py` - Config loading
- `test_session_recovery_integration.py` - Session recovery

## CI Environment Setup

### Local CI Simulation

```bash
# Install CI dependencies
pip install pytest pytest-cov pytest-asyncio ruff mypy black bandit

# Run lint checks (from CI)
ruff check src/ tests/
ruff format --check src/ tests/
mypy src/ --ignore-missing-imports

# Run unit tests (from CI)
python3 -m pytest tests/unit -v -m "not slow and not hardware"

# Run integration tests (from CI)
python3 -m pytest tests/integration -v -m "integration and not slow and not performance"

# Run performance tests (from CI)
python3 -m pytest tests/integration/test_performance.py -v -m "performance"

# Generate coverage report (from CI)
python3 -m pytest tests/ -v --cov=src --cov-report=xml --cov-report=html

# Security scan (from CI)
bandit -r src/ -f json -o bandit-report.json
```

### CI System Dependencies

For Ubuntu/GitHub Actions:
```bash
sudo apt-get update
sudo apt-get install -y portaudio19-dev libsndfile1-dev
```

For local development on Ubuntu/Debian:
```bash
sudo apt-get install -y portaudio19-dev libsndfile1-dev
```

## Fixtures Available

### From `tests/unit/conftest.py`:
- `sample_audio_frame` - Zero-filled audio frame
- `high_energy_audio_frame` - Simulated speech frame
- `mock_sounddevice` - Auto-mocked sounddevice (prevents HW errors)
- `event_loop` - Async event loop

### From `tests/conftest.py`:
- `temp_config_dir` - Temporary configuration directory
- `temp_config_file` - Temporary config file path

### From `tests/integration/`:
- `temp_db_path` - Temporary database for isolation
- `test_config` - Mocked configuration fixture
- `cleanup_memory` - Memory cleanup fixture (performance tests)

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

# Run only E2E tests
python3 -m pytest tests/integration/test_e2e_workflow.py -v

# Run only performance tests
python3 -m pytest tests/integration/test_performance.py -v

# Run tests matching pattern
python3 -m pytest tests/ -k "test_session" -v

# Run with detailed output
python3 -m pytest tests/ -vv --tb=long

# Run specific test class
python3 -m pytest tests/integration/test_e2e_workflow.py::TestFullVoicePipeline -v

# Run with profiling (performance tests)
python3 -m pytest tests/integration/test_performance.py -v --profile

# Run with memory profiling
python3 -m pytest tests/integration/test_performance.py::TestMemoryBenchmarks -v
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

### CI Failures
1. **Lint failures** - Run `ruff check --fix` before committing
2. **Type check failures** - Add `# type: ignore` for complex cases or add type annotations
3. **Test timeouts** - Mark long tests with `@pytest.mark.slow`
4. **Integration test failures** - Ensure no real hardware is required (use mocks)

### Database Locked Errors
- Integration tests use temporary databases with `tmp_path` fixture
- Each test gets isolated database
- Cleaned up automatically after test

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

## Issue #24 Integration Test Summary

**Phase 4 Deliverables:**

| File | Description | Tests | Status |
|------|-------------|-------|--------|
| `test_e2e_workflow.py` | Full voice pipeline E2E | 25+ tests | ✓ New |
| `test_performance.py` | Latency, memory, load tests | 15+ tests | ✓ New |
| `.github/workflows/ci.yml` | CI/CD configuration | N/A | ✓ New |
| `TEST_ENVIRONMENT.md` | Updated documentation | N/A | ✓ Updated |

**Test Coverage:**
- ✅ Voice pipeline end-to-end
- ✅ Session lifecycle (create, persist, restore, expire)
- ✅ Context window pruning under memory pressure
- ✅ Concurrent session handling
- ✅ Error recovery (network, STT, TTS)
- ✅ Latency benchmarks (<2s target)
- ✅ Memory usage tests
- ✅ Concurrent session load tests

## Next Steps Checklist

Run before each development session:
- [x] `python3 -m pytest tests/ --tb=line -q` - Quick status check
- [x] Review new failures - fix before proceeding
- [ ] Run full test suite: `python3 -m pytest tests/ -v`
- [ ] Check integration tests: `python3 -m pytest tests/integration -v`
- [ ] Verify CI passes locally before pushing

## Test Metrics

**Latest Run (2026-02-25):**
- **Passed:** 429+ ✅ (all fixes applied)
- **Failed:** 0 ✅
- **Warnings:** 215
- **Total Time:** ~40 seconds

**Issue #24 Integration Tests:**
- **E2E Tests:** 25 new tests
- **Performance Tests:** 15 new tests
- **CI Pipeline:** 7 jobs configured
- **Target:** All passing (simulated components)