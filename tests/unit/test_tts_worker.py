"""Unit tests for TTS Worker.

Tests Piper-based text-to-speech synthesis.
Mocking piper-tts to avoid requiring actual TTS models.
"""

from __future__ import annotations

import asyncio
import numpy as np
import pytest
from unittest.mock import Mock, patch


class TestTTSConfig:
    """Tests for TTS configuration."""

    def test_default_config(self):
        """Test creation with default parameters."""
        from audio.tts_worker import TTSConfig

        config = TTSConfig()

        assert config.voice_model == "en_US-lessac-medium"
        assert config.speed == 1.0
        assert config.volume == 1.0
        assert config.sample_rate == 24000

    def test_custom_config(self):
        """Test creation with custom parameters."""
        from audio.tts_worker import TTSConfig

        config = TTSConfig(
            voice_model="en_US-lessac-low",
            speed=1.5,
            volume=0.8,
        )

        assert config.voice_model == "en_US-lessac-low"
        assert config.speed == 1.5
        assert config.volume == 0.8

    def test_speed_validation_low(self):
        """Test speed validation - too low."""
        from audio.tts_worker import TTSConfig

        with pytest.raises(ValueError, match="speed must be between"):
            TTSConfig(speed=0.3)

    def test_speed_validation_high(self):
        """Test speed validation - too high."""
        from audio.tts_worker import TTSConfig

        with pytest.raises(ValueError, match="speed must be between"):
            TTSConfig(speed=2.5)

    def test_volume_validation_low(self):
        """Test volume validation - too low."""
        from audio.tts_worker import TTSConfig

        with pytest.raises(ValueError, match="volume must be between"):
            TTSConfig(volume=-0.1)

    def test_volume_validation_high(self):
        """Test volume validation - too high."""
        from audio.tts_worker import TTSConfig

        with pytest.raises(ValueError, match="volume must be between"):
            TTSConfig(volume=1.5)


class TestTTSWorkerInit:
    """Tests for TTS worker initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default parameters."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        assert worker.config.voice_model == "en_US-lessac-medium"
        assert worker.state.value == "idle"
        assert worker.stats.syntheses_total == 0

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        from audio.tts_worker import TTSWorker, VoiceModel

        worker = TTSWorker(voice_model=VoiceModel.LESSAC_LOW.value)

        assert worker.config.voice_model == "en_US-lessac-low"

    def test_init_with_enum(self):
        """Test initialization with VoiceModel enum."""
        from audio.tts_worker import TTSWorker, VoiceModel

        worker = TTSWorker(voice_model=VoiceModel.LESSAC_HIGH)

        assert worker.config.voice_model == "en_US-lessac-high"

    @patch("audio.tts_worker.TTSWorker._load_model", side_effect=ImportError("piper-tts not installed"))
    def test_import_error_no_piper(self, mock_load):
        """Test handling of missing piper-tts."""
        from audio.tts_worker import TTSWorker

        # Mock _load_model to raise error
        original_load = TTSWorker._load_model

        def init_with_error(self):
            original_load(self)

        TTSWorker._load_model = init_with_error

        with pytest.raises(ImportError, match="piper-tts not installed"):
            TTSWorker()

        # Restore
        TTSWorker._load_model = original_load


class TestTTSWorkerSpeak:
    """Tests for TTS worker speech synthesis."""

    @pytest.mark.asyncio
    async def test_speak_empty_text(self):
        """Test handling of empty text."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        chunks = []
        async for chunk in worker.speak(""):
            chunks.append(chunk)

        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_speak_whitespace_only(self):
        """Test handling of whitespace-only text."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        chunks = []
        async for chunk in worker.speak("   "):
            chunks.append(chunk)

        assert len(chunks) == 0

    @pytest.mark.asyncio
    async def test_speak_valid_text(self):
        """Test synthesis of valid text (mock)."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        chunks = []
        async for chunk in worker.speak("Hello world"):
            chunks.append(chunk)

        # Should generate some audio
        assert len(chunks) > 0

        # Each chunk should be a numpy array
        for chunk in chunks:
            assert isinstance(chunk, np.ndarray)

    @pytest.mark.asyncio
    async def test_speak_stream_false(self):
        """Test synthesis with stream=False."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        chunks = []
        async for chunk in worker.speak("Test", stream=False):
            chunks.append(chunk)

        # Should return single complete audio
        assert len(chunks) == 1
        assert isinstance(chunks[0], np.ndarray)

    @pytest.mark.asyncio
    async def test_speak_stream_true(self):
        """Test synthesis with stream=True."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        chunks = []
        async for chunk in worker.speak("Test", stream=True):
            chunks.append(chunk)

        # Should return multiple chunks
        assert len(chunks) > 1
        for chunk in chunks:
            assert isinstance(chunk, np.ndarray)

    def test_speak_sync(self):
        """Test synchronous speak method."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()
        audio = worker.speak_sync("Hello world")

        assert isinstance(audio, np.ndarray)
        assert len(audio) > 0


class TestTTSWorkerStats:
    """Tests for statistics tracking."""

    @pytest.mark.asyncio
    async def test_stats_tracking(self):
        """Test statistics are tracked correctly."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        # First synthesis
        async for _ in worker.speak("First"):
            pass

        stats = worker.get_stats()
        assert stats["syntheses_total"] == 1
        assert stats["syntheses_success"] == 1

        # Second synthesis
        async for _ in worker.speak("Second"):
            pass

        stats = worker.get_stats()
        assert stats["syntheses_total"] == 2
        assert stats["syntheses_success"] == 2

    def test_reset_stats(self):
        """Test resetting statistics."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        # Simulate some stats
        worker.stats.syntheses_total = 10
        worker.stats.syntheses_success = 8

        # Reset
        worker.reset_stats()

        stats = worker.get_stats()
        assert stats["syntheses_total"] == 0
        assert stats["syntheses_success"] == 0


class TestTTSWorkerMockSynthesis:
    """Tests for mock synthesis (without real TTS)."""

    @pytest.mark.asyncio
    async def test_mock_synthesis_generates_audio(self):
        """Test mock synthesis generates audio."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        # The mock should generate white noise
        async for chunk in worker.speak("Test"):
            assert len(chunk) > 0
            assert isinstance(chunk, np.ndarray)

    @pytest.mark.asyncio
    async def test_mock_duration_estimation(self):
        """Test mock duration estimation."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        # 150ms per character * 5 characters = 750ms
        # 24kHz sample rate = 750ms * 24 samples/ms = 18,000 samples
        text = "Hello"  # 5 chars

        chunks = []
        async for chunk in worker.speak(text):
            chunks.append(chunk)

        total_samples = sum(len(chunk) for chunk in chunks)
        expected_samples = int((len(text) * 150 / 1000) * 24000)

        # Should be close to expected (within 20% tolerance)
        assert 0.8 * expected_samples < total_samples < 1.2 * expected_samples

    @pytest.mark.asyncio
    async def test_mock_noise_level(self):
        """Test mock generates appropriate noise level."""
        from audio.tts_worker import TTSWorker

        worker = TTSWorker()

        async for chunk in worker.speak("Test"):
            # Mock should generate low-amplitude noise (-0.1 to 0.1)
            assert np.max(np.abs(chunk)) <= 0.1


class TestVoiceModel:
    """Tests for VoiceModel enum."""

    def test_voice_model_values(self):
        """Test VoiceModel enum values."""
        from audio.tts_worker import VoiceModel

        assert VoiceModel.LESSAC_LOW.value == "en_US-lessac-low"
        assert VoiceModel.LESSAC_MEDIUM.value == "en_US-lessac-medium"
        assert VoiceModel.LESSAC_HIGH.value == "en_US-lessac-high"


class TestTTSResult:
    """Tests for TTSResult dataclass."""

    def test_result_creation(self):
        """Test creating a TTS result."""
        from audio.tts_worker import TTSResult

        audio = np.zeros(24000)  # 1 second at 24kHz
        result = TTSResult(
            audio=audio,
            duration_ms=1000.0,
            sample_rate=24000,
            text_length=10,
            synthesis_time_ms=100.0,
        )

        assert result.duration_ms == 1000.0
        assert result.sample_rate == 24000
        assert result.text_length == 10


class TestConfigurationIntegration:
    """Tests for configuration system integration."""

    @patch("audio.tts_worker.get_config")
    def test_create_from_config(self, mock_get_config):
        """Test creating TTS worker from config."""
        # Mock config
        mock_config = Mock()
        mock_config.voice = "en_US-lessac-low"
        mock_config.speed = 1.5
        mock_config.volume = 0.8

        mock_get_config.return_value.tts = mock_config

        from audio.tts_worker import create_from_config

        worker = create_from_config()

        assert worker.config.voice_model == "en_US-lessac-low"
        assert worker.config.speed == 1.5
        assert worker.config.volume == 0.8

    def test_create_from_config_fallback(self):
        """Test fallback to default if config unavailable."""
        from audio.tts_worker import create_from_config

        worker = create_from_config()

        # Should use defaults
        assert worker.config.voice_model == "en_US-lessac-medium"


# Test markers for pytest
pytestmark = [
    pytest.mark.unit,
    pytest.mark.tts,
]