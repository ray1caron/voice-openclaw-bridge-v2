# Test Plan - Sprint 1: Configuration System

**Issue:** #10 - Configuration System  
**Status:** In Progress  
**Date:** 2026-02-21  
**Branch:** sprint1-config-system

## Overview

This test plan validates the Configuration System implementation for Voice-OpenClaw Bridge v2. The system must support YAML configuration, environment variables, .env files, hot-reload, and strict validation.

## Test Strategy

### 1. Unit Tests (pytest)
**Location:** `tests/unit/test_config.py`

| Test Case | Status | Notes |
|-----------|--------|-------|
| Config validation with valid data | ⬜ | |
| Config validation with invalid data (strict mode) | ⬜ | |
| Default values are applied correctly | ⬜ | |
| Environment variable override | ⬜ | |
| .env file loading | ⬜ | |
| YAML config file loading | ⬜ | |
| Nested config access (config.audio.input_device) | ⬜ | |
| Config save and reload roundtrip | ⬜ | |

### 2. Integration Tests
**Location:** `tests/integration/test_config_integration.py`

| Test Case | Status | Notes |
|-----------|--------|-------|
| Full config load from file system | ⬜ | |
| Config directory creation | ⬜ | |
| Hot-reload file watching | ⬜ | |
| Config change detection | ⬜ | |
| Reload callback invocation | ⬜ | |

### 3. Audio Discovery Tests
**Location:** `tests/unit/test_audio_discovery.py`

| Test Case | Status | Notes |
|-----------|--------|-------|
| Device discovery returns valid devices | ⬜ | |
| Input/output device classification | ⬜ | |
| Default device detection | ⬜ | |
| Device recommendation heuristics | ⬜ | |
| Report generation | ⬜ | |

### 4. Manual Validation

#### Setup Script
| Step | Status | Notes |
|------|--------|-------|
| Run `python scripts/setup.py` on fresh system | ⬜ | |
| Verify config directory created: `~/.voice-bridge/` | ⬜ | |
| Verify config file created: `~/.voice-bridge/config.yaml` | ⬜ | |
| Verify .env template created: `~/.voice-bridge/.env` | ⬜ | |
| Verify audio discovery report displayed | ⬜ | |
| Verify recommended devices selected | ⬜ | |

#### Config Validation
| Step | Status | Notes |
|------|--------|-------|
| Edit config.yaml with invalid value → should fail on load | ⬜ | |
| Edit config.yaml with valid value → hot-reload triggers | ⬜ | |
| Set env var → overrides config file value | ⬜ | |
| Create .env file → loads on startup | ⬜ | |

## Test Execution Plan

### Phase 1: Unit Tests (Current)
1. ✅ Create test directory structure
2. ⬜ Write config unit tests
3. ⬜ Write audio discovery unit tests
4. ⬜ Run tests: `pytest tests/unit -v`

### Phase 2: Integration Tests (Next)
1. ⬜ Write integration tests
2. ⬜ Test file I/O operations
3. ⬜ Test hot-reload with actual file changes
4. ⬜ Run tests: `pytest tests/integration -v`

### Phase 3: Manual Validation (Final)
1. ⬜ Clean test environment (remove ~/.voice-bridge/)
2. ⬜ Run setup script
3. ⬜ Verify all artifacts created correctly
4. ⬜ Test hot-reload manually
5. ⬜ Document any issues

## Success Criteria

- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Manual validation successful
- [ ] Config loads in <100ms
- [ ] Hot-reload triggers within 500ms of file change
- [ ] No errors on first-time setup

## Dependencies

Required packages (already in pyproject.toml):
- pytest >=7.0
- pytest-asyncio >=0.21
- pytest-cov >=4.0
- pytest-mock >=3.10

## GitHub Updates

As tests are completed, I will:
1. Post progress comment on Issue #10
2. Commit test files with message: `test(#10): add unit tests for config validation`
3. Update this test plan with checkmarks
4. Create sub-issues if blockers found

---

**Last Updated:** 2026-02-21 12:18 PST  
**Next Action:** Commit test plan to GitHub, then begin Phase 1 unit tests
