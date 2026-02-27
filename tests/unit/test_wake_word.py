"""Unit tests for Wake Word Detector.

Tests Porcupine-based wake word detection.
Mocking pvporcupine to avoid requiring actual access key.
"""

from __future__ import annotations

import asyncio
import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock


class TestWakeWordConfig:
    """Tests for wake word configuration."""

    def test_default_config(self):
        """Test creation with default parameters."""
        from audio.wake_word import WakeWordConfig

        config = WakeWordConfig()

        assert config.sensitivity == 0.85  # MEDIUM
        assert config.access_key is None
        assert config.device_index == -1
        assert config.frame_length == 512

    def test_custom_config(self):
        """Test creation with custom parameters."""
        from audio.wake_word import WakeWordConfig, SensitivityLevel

        config = WakeWordConfig(
            sensitivity=SensitivityLevel.HIGH.value,
            access_key="test-access-key-12345",
            device_index=0,
        )

        assert config.sensitivity == 0.88
        assert config.access_key == "test-access-key-12345"
        assert config.device_index == 0

    def test_sensitivity_validation_low(self):
        """Test sensitivity validation - too low."""
        from audio.wake_word import WakeWordConfig

        with pytest.raises(ValueError, match="sensitivity must be between"):
            WakeWordConfig(sensitivity=-0.1)

    def test_sensitivity_validation_high(self):
        """Test sensitivity validation - too high."""
        from audio.wake_word import WakeWordConfig

        with pytest.raises(ValueError, match="sensitivity must be between"):
            WakeWordConfig(sensitivity=1.5)

    def test_access_key_validation_too_short(self):
        """Test access key validation - too short."""
        from audio.wake_word import WakeWordConfig

        with pytest.raises(ValueError, match="access_key must be at least 10 characters"):
            WakeWordConfig(access_key="short")


class TestWakeWordDetectorInit:
    """Tests for wake word detector initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        from audio.wake_word import WakeWordDetector, BuiltInWakeWord

        detector = WakeWordDetector()

        assert detector.keyword == BuiltInWakeWord.COMPUTER.value
        assert detector.state.value == "idle"
        assert detector.detections_total == 0

    def test_init_with_enum(self):
        """Test initialization with BuiltInWakeWord enum."""
        from audio.wake_word import WakeWordDetector, BuiltInWakeWord

        detector = WakeWordDetector(keyword=BuiltInWakeWord.COMPUTER)

        assert detector.keyword == BuiltInWakeWord.COMPUTER.value

    def test_init_custom_keyword(self):
        """Test initialization with custom keyword."""
        from audio.wake_word import WakeWordDetector

        detector = WakeWordDetector(keyword="bumblebee")

        assert detector.keyword == "bumblebee"

    @patch("audio.wake_word.pvporcupine", side_effect=ImportError("pvporcupine not installed"))
    def test_import_error_no_porcupine(self, mock_pv):
        """Test handling of missing pvporcupine."""
        from audio.wake_word import WakeWordDetector

        # Patch to raise error
        original_load = WakeWordDetector._load_detector

        def init_with_error(self):
            original_load(self)

        WakeWordDetector._load_detector = init_with_error

        with pytest.raises(ImportError, match="pvporcupine not installed"):
            WakeWordDetector()

        # Restore
        WakeWordDetector._load_detector = original_load


class TestWakeWordDetectorListen:
    """Tests for wake word listening."""

    @pytest.mark.asyncio
    async def test_listen_with_timeout(self):
        """Test listening with timeout."""
        from audio.wake_word import WakeWordDetector

        detector = WakeWordDetector()

        # Short timeout
        event = await detector.listen(timeout=0.1)

        # Should return None (timeout before mock detection)
        assert event is None

    @pytest.mark.asyncio
    async def test_listen_detects_wake_word(self):
        """Test successful wake word detection (mock)."""
        from audio.wake_word import WakeWordDetector

        detector = WakeWordDetector()

        # Mock should detect after 1-3 seconds
        event = await detector.listen(timeout=5.0)

        assert event is not None
        assert event.keyword == "computer"
        assert event.confidence > 0.0
        assert event.timestamp > 0

    @pytest.mark.asyncio
    async def test_listen_with_callback(self):
        """Test callback on detection."""
        from audio.wake_word import WakeWordDetector

        detector = WakeWordDetector()

        callback_called = []
        def on_wake(event):
            callback_called.append(event)

        event = await detector.listen(callback=on_wake, timeout=5.0)

        assert len(callback_called) == 1
        assert callback_called[0].keyword == "computer"

    @pytest.mark.asyncio
    async def test_listen_state_changes(self):
        """Test state changes during listening."""
        from audio.wake_word import WakeWordDetector, WakeWordState

        detector = WakeWordDetector()

        assert detector.state == WakeWordState.IDLE

        # Should change to LISTENING
        async def listen_and_check():
            async for _ in detector.__class__._listen_mock(detector, None, 5.0):
                detector.state = WakeWordState.LISTENING

        event = await detector.listen(timeout=5.0)

        assert event is not None
        assert detector.state == WakeWordState.DETECTED


class TestWakeWordDetectorStats:
    """Tests for statistics tracking."""

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Test statistics are tracked correctly."""
        from audio.wake_word import WakeWordDetector

        detector = WakeWordDetector()

        # First detection
        await detector.listen(timeout=5.0)

        stats = detector.get_stats()
        assert stats["detections_total"] == 1
        assert stats["listening_time_ms"] > 0

        # Second detection
        await detector.listen(timeout=5.0)

        stats = detector.get_stats()
        assert stats["detections_total"] == 2

    def test_reset_stats(self):
        """Test resetting statistics."""
        from audio.wake_word import WakeWordDetector

        detector = WakeWordDetector()

        # Simulate some stats
        detector.detections_total = 10
        detector.listening_time_ms = 5000.0

        # Reset
        detector.reset_stats()

        stats = detector.get_stats()
        assert stats["detections_total"] == 0
        assert stats["listening_time_ms"] == 0.0


class TestWakeWordDetectorProcessFrame:
    """Tests for processing audio frames."""

    def test_process_frame_no_detector(self):
        """Test frame processing without real detector."""
        from audio.wake_word import WakeWordDetector

        detector = WakeWordDetector()

        # Mock audio frame
        frame = np.random.randint(-32768, 32767, 512, dtype=np.int16)

        result = detector.process_audio_frame(frame)

        # Should return None (no real detector)
        assert result is None


class TestWakeWordEvent:
    """Tests for WakeWordEvent dataclass."""

    def test_event_creation(self):
        """Test creating a wake word event."""
        from audio.wake_word import WakeWordEvent

        event = WakeWordEvent(
            keyword="computer",
            confidence=0.95,
            timestamp=1234567890.0,
            frame_index=100,
        )

        assert event.keyword == "computer"
        assert event.confidence == 0.95
        assert event.timestamp == 1234567890.0
        assert event.frame_index == 100


class TestBuiltInWakeWord:
    """Tests for BuiltInWakeWord enum."""

    def test_builtin_keywords(self):
        """Test built-in keyword enum values."""
        from audio.wake_word import BuiltInWakeWord

        assert BuiltInWakeWord.PORCUPINE.value == "porcupine"
        assert BuiltInWakeWord.COMPUTER.value == "computer"
        assert BuiltInWakeWord.BUMBLEBEE.value == "bumblebee"
        assert BuiltInWakeWord.ALEXA.value == "alexa"
        assert BuiltInWakeWord.NEON.value == "neon"


class TestSensitivityLevel:
    """Tests for SensitivityLevel enum."""

    def test_sensitivity_levels(self):
        """Test sensitivity level values."""
        from audio.wake_word import SensitivityLevel

        assert SensitivityLevel.VERY_HIGH.value == 0.93
        assert SensitivityLevel.HIGH.value == 0.88
        assert SensitivityLevel.MEDIUM.value == 0.85
        assert SensitivityLevel.LOW.value == 0.80
        assert SensitivityLevel.VERY_LOW.value == 0.75


class TestWakeWordState:
    """Tests for WakeWordState enum."""

    def test_state_values(self):
        """Test wake word state enum values."""
        from audio.wake_word import WakeWordState

        assert WakeWordState.IDLE.value == "idle"
        assert WakeWordState.LISTENING.value == "listening"
        assert WakeWordState.DETECTED.value == "detected"
        assert WakeWordState.ERROR.value == "error"


class TestConfigurationIntegration:
    """Tests for configuration system integration."""

    @patch("audio.wake_word.get_config")
    def test_create_from_config(self, mock_get_config):
        """Test creating detector from config."""
        # Mock config
        mock_config = Mock()
        mock_config.keyword_paths = ["path/to/model"]
        mock_config.sensitivity = 0.90
        mock_config.access_key = "test-key-12345"
        mock_config.device_index = 1

        mock_get_config.return_value.wake_word = mock_config

        from audio.wake_word import create_from_config

        detector = create_from_config()

        assert detector.config.sensitivity == 0.90
        assert detector.config.access_key == "test-key-12345"
        assert detector.config.device_index == 1

    def test_create_from_config_fallback(self):
        """Test fallback to default if config unavailable."""
        from audio.wake_word import create_from_config

        detector = create_from_config()

        # Should use defaults
        assert detector.config.sensitivity == 0.85


# Test markers for pytest
pytestmark = [
    pytest.mark.unit,
    pytest.mark.wake_word,
]