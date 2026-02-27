"""Unit tests for STT Worker.

Tests Whisper-based speech-to-text transcription.
Mocking model loading to avoid requiring actual Whisper model.
"""

from __future__ import annotations

import asyncio
import numpy as np
import pytest
from unittest.mock import Mock, patch, MagicMock

from audio.stt_worker import (
    STTWorker,
    TranscriptionResult,
    STTStats,
    ModelSize,
    ComputeType,
    DeviceType,
    transcribe_file,
    create_from_config,
)


class TestSTTWorkerInit:
    """Tests for STT worker initialization."""

    @patch("audio.stt_worker.WhisperModel")
    def test_init_with_defaults(self, mock_model):
        """Test initialization with default parameters."""
        # Mock model loading
        mock_instance = Mock()
        mock_model.return_value = mock_instance

        worker = STTWorker()

        assert worker.model_size == "base"
        assert worker.device == "auto"
        assert worker.compute_type == "int8"
        assert worker.language is None
        assert worker.stats.transcriptions_total == 0

    @patch("audio.stt_worker.WhisperModel")
    def test_init_with_custom_params(self, mock_model):
        """Test initialization with custom parameters."""
        mock_instance = Mock()
        mock_model.return_value = mock_instance

        worker = STTWorker(
            model_size="tiny",
            device="cuda",
            compute_type="float16",
            language="en",
        )

        assert worker.model_size == "tiny"
        assert worker.device == "cuda"
        assert worker.compute_type == "float16"
        assert worker.language == "en"

    @patch("audio.stt_worker.WhisperModel")
    def test_init_invalid_model_size(self, mock_model):
        """Test initialization with invalid model size."""
        with pytest.raises(ValueError, match="Invalid model_size"):
            STTWorker(model_size="invalid")

    def test_init_invalid_device(self):
        """Test initialization with invalid device."""
        with patch("audio.stt_worker.WhisperModel"):
            with pytest.raises(ValueError, match="Invalid device"):
                STTWorker(device="invalid")

    def test_init_invalid_compute_type(self):
        """Test initialization with invalid compute type."""
        with patch("audio.stt_worker.WhisperModel"):
            with pytest.raises(ValueError, match="Invalid compute_type"):
                STTWorker(compute_type="invalid")

    @patch("audio.stt_worker.WhisperModel")
    def test_import_error_no_faster_whisper(self, mock_model):
        """Test handling of missing faster-whisper."""
        mock_model.side_effect = ImportError("No module named 'faster_whisper'")

        with pytest.raises(ImportError, match="faster-whisper not installed"):
            STTWorker()

    @patch("audio.stt_worker.WhisperModel")
    def test_load_error(self, mock_model):
        """Test handling of model load error."""
        mock_model.side_effect = RuntimeError("Failed to load")

        with pytest.raises(RuntimeError, match="Failed to load Whisper model"):
            STTWorker()


class TestTranscriptionResult:
    """Tests for TranscriptionResult dataclass."""

    def test_result_creation(self):
        """Test creating a transcription result."""
        result = TranscriptionResult(
            text="Hello world",
            confidence=0.95,
            language="en",
            duration_ms=1000.0,
            segments_count=2,
            latency_ms=500.0,
        )

        assert result.text == "Hello world"
        assert result.confidence == 0.95
        assert result.language == "en"
        assert result.is_valid() is True

    def test_invalid_result(self):
        """Test result validation for empty text."""
        result = TranscriptionResult(
            text="",
            confidence=0.0,
            language="",
            duration_ms=0.0,
            segments_count=0,
            latency_ms=0.0,
        )

        assert result.is_valid() is False

    def test_whitespace_only_result(self):
        """Test result validation for whitespace-only text."""
        result = TranscriptionResult(
            text="   ",
            confidence=0.5,
            language="en",
            duration_ms=100.0,
            segments_count=1,
            latency_ms=100.0,
        )

        assert result.is_valid() is False

    def test_valid_result_with_special_chars(self):
        """Test result with special characters is considered valid."""
        result = TranscriptionResult(
            text="Hello, world! How are you?",
            confidence=0.9,
            language="en",
            duration_ms=2000.0,
            segments_count=3,
            latency_ms=800.0,
        )

        assert result.is_valid() is True


class TestSTTStats:
    """Tests for STT statistics tracking."""

    def test_initial_stats(self):
        """Test initial statistics are zero."""
        stats = STTStats()

        assert stats.transcriptions_total == 0
        assert stats.transcriptions_success == 0
        assert stats.transcriptions_empty == 0
        assert stats.transcriptions_error == 0
        assert stats.total_duration_ms == 0.0
        assert stats.total_latency_ms == 0.0
        assert stats.average_latency_ms == 0.0

    def test_update_success(self):
        """Test updating stats with successful transcription."""
        stats = STTStats()
        result = TranscriptionResult(
            text="Hello",
            confidence=0.9,
            language="en",
            duration_ms=1000.0,
            segments_count=1,
            latency_ms=500.0,
        )

        stats.update_stats(result, 500.0)

        assert stats.transcriptions_total == 1
        assert stats.transcriptions_success == 1
        assert stats.transcriptions_empty == 0
        assert stats.transcriptions_error == 0
        assert stats.total_duration_ms == 1000.0
        assert stats.total_latency_ms == 500.0
        assert stats.average_latency_ms == 500.0

    def test_update_empty(self):
        """Test updating stats with empty transcription."""
        stats = STTStats()
        result = TranscriptionResult(
            text="",
            confidence=0.0,
            language="",
            duration_ms=0.0,
            segments_count=0,
            latency_ms=100.0,
        )

        stats.update_stats(result, 100.0)

        assert stats.transcriptions_total == 1
        assert stats.transcriptions_success == 0
        assert stats.transcriptions_empty == 1
        assert stats.transcriptions_error == 0

    def test_update_error(self):
        """Test updating stats with failed transcription."""
        stats = STTStats()

        stats.update_stats(None, 100.0)

        assert stats.transcriptions_total == 1
        assert stats.transcriptions_success == 0
        assert stats.transcriptions_empty == 0
        assert stats.transcriptions_error == 1

    def test_average_latency(self):
        """Test average latency calculation."""
        stats = STTStats()

        # First transcription
        stats.update_stats(
            TranscriptionResult("A", 0.9, "en", 100, 1, 100),
            100.0
        )

        # Second transcription
        stats.update_stats(
            TranscriptionResult("B", 0.9, "en", 100, 1, 200),
            200.0
        )

        assert stats.average_latency_ms == 150.0


class TestSTTWorkerTranscribe:
    """Tests for STT worker transcription."""

    @patch("audio.stt_worker.WhisperModel")
    @pytest.mark.asyncio
    async def test_transcribe_success(self, mock_model):
        """Test successful audio transcription."""
        # Mock model
        mock_instance = Mock()
        mock_segment = Mock(text="Hello world", no_speech_prob=0.05)
        mock_info = Mock(language="en")
        mock_model.return_value = mock_instance

        # Setup mock transcribe
        async def mock_transcribe_gen(*args, **kwargs):
            for _ in range(10):
                yield mock_segment, mock_info

        mock_instance.transcribe = mock_transcribe_gen

        # Create worker
        worker = STTWorker()

        # Create test audio (1 second at 16kHz)
        audio = np.random.randn(16000).astype(np.float32)

        # Transcribe
        result = await worker.transcribe(audio)

        assert result.is_valid()
        assert "world" in result.text.lower()
        assert result.language == "en"
        assert result.duration_ms == 1000.0

    @pytest.mark.asyncio
    async def test_transcribe_empty_audio(self, *mocks):
        """Test handling of empty audio."""
        with patch("audio.stt_worker.WhisperModel"):
            worker = STTWorker()

            # Empty audio
            audio = np.array([], dtype=np.float32)

            result = await worker.transcribe(audio)

            assert result.is_valid() is False
            assert result.text == ""
            assert worker.stats.transcriptions_empty == 1

    @pytest.mark.asyncio
    async def test_transcribe_invalid_type(self, *mocks):
        """Test handling of invalid audio type."""
        with patch("audio.stt_worker.WhisperModel"):
            worker = STTWorker()

            with pytest.raises(ValueError, match="must be numpy array"):
                await worker.transcribe("not an array")

    @pytest.mark.asyncio
    async def test_transcribe_multi_channel(self, *mocks):
        """Test handling of multi-channel audio (should fail)."""
        with patch("audio.stt_worker.WhisperModel"):
            worker = STTWorker()

            # Stereo audio (2 channels)
            audio = np.random.randn(16000, 2).astype(np.float32)

            with pytest.raises(ValueError, match="must be 1D"):
                await worker.transcribe(audio)

    @patch("audio.stt_worker.WhisperModel")
    def test_transcribe_sync(self, mock_model):
        """Test synchronous transcription method."""
        # Mock model
        mock_instance = Mock()
        mock_segment = Mock(text="Hello", no_speech_prob=0.1)
        mock_info = Mock(language="en")
        mock_model.return_value = mock_instance

        # Setup mock transcribe
        def mock_transcribe_gen(*args, **kwargs):
            yield mock_segment, mock_info

        mock_instance.transcribe = mock_transcribe_gen

        worker = STTWorker()
        audio = np.random.randn(16000).astype(np.float32)

        result = worker.transcribe_sync(audio)

        assert result.is_valid()
        assert "hello" in result.text.lower()


class TestSTTWorkerStats:
    """Tests for statistics tracking."""

    @patch("audio.stt_worker.WhisperModel")
    @pytest.mark.asyncio
    async def test_stats_tracking(self, mock_model):
        """Test statistics are tracked correctly."""
        # Mock model
        mock_instance = Mock()
        mock_segment = Mock(text="Test", no_speech_prob=0.05)
        mock_info = Mock(language="en")
        mock_model.return_value = mock_instance

        # Setup mock transcribe
        async def mock_transcribe_gen(*args, **kwargs):
            yield mock_segment, mock_info

        mock_instance.transcribe = mock_transcribe_gen

        worker = STTWorker()
        audio = np.random.randn(16000).astype(np.float32)

        # First transcription
        await worker.transcribe(audio)

        stats = worker.get_stats()
        assert stats["transcriptions_total"] == 1
        assert stats["transcriptions_success"] == 1

        # Second transcription
        await worker.transcribe(audio)

        stats = worker.get_stats()
        assert stats["transcriptions_total"] == 2
        assert stats["transcriptions_success"] == 2

    @patch("audio.stt_worker.WhisperModel")
    def test_reset_stats(self, mock_model):
        """Test resetting statistics."""
        mock_instance = Mock()
        mock_model.return_value = mock_instance
        mock_instance.transcribe = Mock(return_value=([], Mock(language="en")))

        worker = STTWorker()

        # Simulate some stats
        worker.stats.transcriptions_total = 10
        worker.stats.transcriptions_success = 8

        # Reset
        worker.reset_stats()

        stats = worker.get_stats()
        assert stats["transcriptions_total"] == 0
        assert stats["transcriptions_success"] == 0


class TestAudioPreprocessing:
    """Tests for audio preprocessing methods."""

    @patch("audio.stt_worker.WhisperModel")
    def test_normalize_audio(self, mock_model):
        """Test audio normalization."""
        mock_instance = Mock()
        mock_model.return_value = mock_instance

        worker = STTWorker()

        # Create audio with values > 1.0
        audio = np.array([2.0, -3.0, 1.5], dtype=np.float32)
        normalized = worker._normalize_audio(audio)

        # Should be normalized to [-1.0, 1.0]
        assert np.max(np.abs(normalized)) <= 1.0
        assert np.isclose(normalized[0], 2.0 / 3.0)

    @patch("audio.stt_worker.WhisperModel")
    def test_normalize_already_normalized(self, mock_model):
        """Test that already normalized audio is unchanged."""
        mock_instance = Mock()
        mock_model.return_value = mock_instance

        worker = STTWorker()

        # Already normalized audio
        audio = np.array([0.5, -0.5, 1.0], dtype=np.float32)
        normalized = worker._normalize_audio(audio)

        assert np.array_equal(normalized, audio)

    @patch("audio.stt_worker.WhisperModel")
    def test_resample_audio(self, mock_model):
        """Test audio resampling."""
        mock_instance = Mock()
        mock_model.return_value = mock_instance

        worker = STTWorker()

        # 8kHz audio, resample to 16kHz
        audio = np.sin(np.linspace(0, 2 * np.pi, 8000)).astype(np.float32)
        resampled = worker._resample(audio, 8000, 16000)

        # Should be roughly 2x the length
        assert len(resampled) == 16000


class TestUtilityFunctions:
    """Tests for utility functions."""

    @patch("audio.stt_worker.sf.read")
    @patch("audio.stt_worker.STTWorker")
    @pytest.mark.asyncio
    async def test_transcribe_file(self, mock_worker, mock_read):
        """Test transcribing an audio file."""
        # Setup mocks
        mock_read.return_value = (
            np.random.randn(16000).astype(np.float32),
            16000,
        )

        mock_instance = Mock()
        mock_result = TranscriptionResult(
            text="File content",
            confidence=0.9,
            language="en",
            duration_ms=1000,
            segments_count=1,
            latency_ms=500
        )
        mock_instance.transcribe = Mock(
            return_value=asyncio.Future()
        )
        mock_instance.transcribe.return_value.set_result(mock_result)
        mock_worker.return_value = mock_instance

        # Transcribe file
        result = await transcribe_file("test.wav")

        assert result.text == "File content"
        assert mock_read.called

    @patch("audio.stt_worker.get_config")
    @patch("audio.stt_worker.WhisperModel")
    def test_create_from_config(self, mock_model, mock_get_config):
        """Test creating STT worker from config."""
        # Mock config
        mock_config = Mock()
        mock_config.model = "tiny"
        mock_config.device = "cuda"
        mock_config.compute_type = "float16"
        mock_config.language = "en"
        mock_get_config.return_value.stt = mock_config

        # Create worker
        worker = create_from_config()

        assert worker.model_size == "tiny"
        assert worker.device == "cuda"
        assert worker.compute_type == "float16"
        assert worker.language == "en"


class TestConfigurationIntegration:
    """Tests for configuration system integration."""

    @patch("audio.stt_worker.get_config")
    @patch("audio.stt_worker.WhisperModel")
    def test_uses_config_defaults(self, mock_model, mock_get_config):
        """Test that STT worker uses config defaults."""
        # Mock config
        mock_config = Mock()
        mock_config.model = "medium"
        mock_config.device = "cuda"
        mock_config.compute_type = "float16"
        mock_config.language = None
        mock_get_config.return_value.stt = mock_config

        mock_instance = Mock()
        mock_model.return_value = mock_instance

        # Create worker (should use config)
        worker = STTWorker()

        assert worker.model_size == "medium"
        assert worker.device == "cuda"
        assert worker.compute_type == "float16"
        assert worker.language is None


# Test markers for pytest
pytestmark = [
    pytest.mark.unit,
    pytest.mark.stt,
]