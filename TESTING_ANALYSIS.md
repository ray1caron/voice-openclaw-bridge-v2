# Testing Approach Analysis

**Date:** 2026-02-27 10:32 PST
**Source:** TEST_ENVIRONMENT.md review

---

## Test Infrastructure Status

### Existing Setup ✅ (Mature)
- **pytest 9.0.2** - Latest version
- **pytest-asyncio 1.3.0** - Async test support
- **pytest-cov 4.0.0** - Coverage reporting
- **Python 3.12.3** - Latest Python
- **404 passing unit tests** - Already passing (Sprints 1-3)
- **GitHub Actions CI** - Full matrix across Python 3.10/3.11/3.12

### Test Structure
```
tests/
├── unit/               # ~404 tests passing
│   ├── conftest.py     # Fixtures & mocks (auto-mocks sounddevice)
│   └── test_*.py       # Individual test files
└── integration/        # E2E tests (Issue #24)
    └── test_*.py
```

---

## How Tests Are Written (Pattern from Existing Code)

### 1. Unit Test Pattern
```python
# From test_config.py, test_websocket_client.py, etc.
from __future__ import annotations
import pytest
from unittest.mock import Mock, AsyncMock

# Test class
class TestComponent:
    """Tests for Component functionality."""
    
    @pytest.mark.asyncio
    async def test_async_function(self):
        """Test async function."""
        # Arrange
        mock = Mock()
        # Act
        result = await function_under_test(mock)
        # Assert
        assert result is not None
    
    def test_sync_function(self):
        """Test sync function."""
        # Arrange/Act/Assert
        assert True
```

### 2. Mocking Pattern
```python
# From test_websocket_client.py
from unittest.mock import patch, AsyncMock

@patch("bridge.websocket_client.websockets")
def test_with_mock(self, mock_websockets):
    """Test with mocked dependency."""
    # Mock the external dependency
    mock_websockets.connect.return_value = AsyncMock()
    
    # Test the function
    result = client.connect()
    
    # Verify mock was called
    mock_websockets.connect.assert_called_once()
```

### 3. Fixture Pattern
```python
# From tests/unit/conftest.py
@pytest.fixture
def mock_sounddevice(monkeypatch):
    """Automatically mock sounddevice for all tests."""
    mock_sd = MagicMock()
    mock_sd.query_devices = Mock(return_value=mock_devices)
    monkeypatch.setattr(sys, 'modules',
                      {**sys.modules, 'sounddevice': mock_sd})
    yield mock_sd
```

---

## My Testing Approach (What I'm Doing)

### What I Built: `tests/unit/test_stt_worker.py`

**Pattern Used:** Same as existing tests
- ✅ Test classes for organization
- ✅ `@pytest.mark.asyncio` for async tests
- ✅ Mocking with `from unittest.mock import Mock, patch`
- ✅ Test marker: `pytestmark = [pytest.mark.unit, pytest.mark.stt]`

### Tests I Wrote (27 Total)

**Initialization Tests (6):**
```python
class TestSTTWorkerInit:
    def test_init_with_defaults(self, mock_model)
    def test_init_with_custom_params(self, mock_model)
    def test_init_invalid_model_size(self, mock_model)
    def test_init_invalid_device(self, *mocks)
    def test_init_invalid_compute_type(self, *mocks)
    def test_import_error_no_faster_whisper(self, mock_model)
```

**Transcription Tests (5):**
```python
class TestSTTWorkerTranscribe:
    @pytest.mark.asyncio
    async def test_transcribe_success(self, mock_model)
    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self, *mocks)
    @pytest.mark.asyncio
    async def test_transcribe_invalid_type(self, *mocks)
    @pytest.mark.asyncio
    async def test_transcribe_multi_channel(self, *mocks)
    def test_transcribe_sync(self, mock_model)
```

**Stats Tests (2):**
```python
class TestSTTStats:
    def test_initial_stats(self)
    def test_update_success(self)
    # ... more
```

**Total Pattern Matches:**
- ✅ Follows existing test structure
- ✅ Uses same mocking approach
- ✅ Same pytest markers
- ✅ Async test support

---

## Critical Difference: Dependencies

### Existing Tests (Passing)
```python
# test_websocket_client.py - Tests WebSocket client
from websockets.exceptions import ConnectionClosed  # ✅ Installed
# Passes because websockets IS installed
```

### My Tests (Failing)
```python
# test_stt_worker.py - Tests STT worker
from faster_whisper import WhisperModel  # ❌ NOT installed
# Fails because faster-whisper is NOT installed
```

---

## How Existing Tests Handle Missing Dependencies

### Pattern 1: Mark as Skip/Slow
```python
# In pyproject.toml markers:
"hardware: marks tests that require hardware"

# In test file:
@pytest.mark.hardware
def test_with_real_mic(self):
    """Test that requires real hardware."""
    # Only runs with: pytest -m hardware
    pass
```

### Pattern 2: Mock the Dependency
```python
from unittest.mock import patch, MagicMock

@patch("audio.stt_worker.WhisperModel")
def test_with_mock(self, mock_model):
    """Test with mocked WhisperModel."""
    # This is what I did!
    mock_instance = Mock()
    mock_model.return_value = mock_instance
    pass
```

### Pattern 3: Conditional Import
```python
try:
    import faster_whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

@pytest.mark.skipif(not WHISPER_AVAILABLE, reason="faster-whisper not installed")
def test_with_real_model(self):
    """Test with real Whisper model."""
    pass
```

---

## My Problem: Import Before Mock

### What I Did (Wrong Pattern):
```python
# tests/unit/test_stt_worker.py
from audio.stt_worker import STTWorker  # ← Imports HERE
# ↑ This imports stt_worker.py
# ↑ stt_worker.py does: from faster_whisper import WhisperModel
# ↑ faster-whisper NOT installed
# ↑ CRASH at import time!

class TestSTTWorkerInit:
    @patch("audio.stt_worker.WhisperModel")  # ← Mock applied LATER
    def test_init_with_defaults(self, mock_model):
        # Too late! Already crashed above!
        pass
```

### What I Should Do (Correct Pattern):

#### Option 1: Don't Import at Module Level
```python
# tests/unit/test_stt_worker.py
import pytest
from unittest.mock import patch

# DON'T import STTWorker at module level!

class TestSTTWorkerInit:
    @patch("audio.stt_worker.WhisperModel")
    def test_init_with_defaults(self, mock_model):
        # Import INSIDE test function (after mock applied)
        from audio.stt_worker import STTWorker
        worker = STTWorker()
        pass
```

#### Option 2: Use pytest Lazy Import
```python
# tests/unit/test_stt_worker.py
import pytest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

pytest.importorskip("faster_whisper")  # ← Skip entire file if not installed

from audio.stt_worker import STTWorker  # ← Now safe to import
```

#### Option 3: Mock at Import Time (Advanced)
```python
# tests/unit/conftest.py
import sys
from unittest.mock import MagicMock

# Mock faster_whisper BEFORE any tests import
sys.modules["faster_whisper"] = MagicMock()
```

---

## What Needs to Change

### Immediate Fix
Rewrite `tests/unit/test_stt_worker.py` to:

1. **Remove module-level imports:**
```python
# Don't do this:
from audio.stt_worker import STTWorker  # ← DELETE THIS LINE
```

2. **Import inside each test:**
```python
# Do this instead:
@patch("audio.stt_worker.WhisperModel")
def test_init_with_defaults(self, mock_model):
    from audio.stt_worker import STTWorker  # ← Import HERE
    worker = STTWorker()
    assert worker is not None
```

OR

3. **Add skip marker:**
```python
import pytest

pytest.importorskip("faster_whisper")  # Skip if not installed

# Now safe to import
from audio.stt_worker import STTWorker
```

---

## Testing Strategy Summary

### What the Project Expects:
- ✅ Unit tests with pytest
- ✅ Mock external dependencies
- ✅ Separate unit vs integration tests
- ✅ CI runs tests automatically
- ✅ Mark slow/hardware tests

### What I Did:
- ✅ Followed test structure
- ✅ Used pytest markers
- ✅ Wrote 27 unit tests
- ❌ Imported module at wrong time (before mock applied)

### What I Need to Fix:
- ⏸️ Reorder imports (inside tests, not at module level)
- ⏸️ Add skip marker for missing dependency
- ⏸️ Re-run tests
- ⏸️ Verify all pass

---

## Decision: Which Fix Approach?

### Approach 1: Import Inside Tests
**Pros:**
- Works with existing test structure
- No changes to conftest.py needed
- Tests run only when dependencies available

**Cons:**
- Verbose (import in every test)
- Less clean code

**Recommendation:** ✅ **Use this for now**

### Approach 2: pytest.importorskip()
**Pros:**
- Clean, idiomatic pytest pattern
- One line at top of file
- Clear skip message

**Cons:**
- Entire test file skipped if dependency missing
- Can't test mock behavior without dependency

**Recommendation:** ✅ **Better long-term**

### Approach 3: Global Mock in conftest.py
**Pros:**
- Most powerful control
- Can test everything with mocks

**Cons:**
- Changes shared fixture
- Affects all tests
- More complex

**Recommendation:** ⚠️ **Use only if needed**

---

**Generated:** 2026-02-27 10:32 PST
**Status:** Ready to fix test imports
**Next:** Rewrite test_stt_worker.py with correct import pattern