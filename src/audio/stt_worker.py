"""Speech-to-Text Worker using Faster-Whisper.

Handles audio transcription with configurable model sizes and devices.
Supports both async and sync transcription for flexible integration.
Integrates with Voice Orchestrator for audio pipeline.

Dependencies:
- faster-whisper: CUDA-accelerated Whisper inference
- numpy: Audio array processing
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import Optional, Coroutine, Callable
from enum import Enum

import numpy as np
import structlog
from faster_whisper import WhisperModel

from bridge.config import STTConfig, get_config

logger = structlog.get_logger()


class ModelSize(Enum):
    """Available Whisper model sizes."""
    TINY = "tiny"
    BASE = "base"
    SMALL = "small"
    MEDIUM = "medium"
    LARGE = "large"
    LARGE_V2 = "large-v2"
    LARGE_V3 = "large-v3"


class ComputeType(Enum):
    """Whisper compute types."""
    INT8 = "int8"
    FLOAT16 = "float16"
    FLOAT32 = "float32"


class DeviceType(Enum):
    """Compute device types."""
    CPU = "cpu"
    CUDA = "cuda"
    AUTO = "auto"


@dataclass
class TranscriptionResult:
    """Result of transcription with metadata."""
    text: str
    confidence: float
    language: str
    duration_ms: float
    segments_count: int
    latency_ms: float

    def is_valid(self) -> bool:
        """Check if transcription is valid (non-empty)."""
        return bool(self.text and self.text.strip())


@dataclass
class STTStats:
    """STT worker statistics."""
    transcriptions_total: int = 0
    transcriptions_success: int = 0
    transcriptions_empty: int = 0
    transcriptions_error: int = 0
    total_duration_ms: float = 0.0
    total_latency_ms: float = 0.0
    average_latency_ms: float = 0.0

    def update_stats(
        self,
        result: Optional[TranscriptionResult],
        latency_ms: float,
    ):
        """Update statistics after a transcription."""
        self.transcriptions_total += 1
        self.total_latency_ms += latency_ms

        if result is None:
            self.transcriptions_error += 1
        elif result.is_valid():
            self.transcriptions_success += 1
            self.total_duration_ms += result.duration_ms
        else:
            self.transcriptions_empty += 1

        self.average_latency_ms = self.total_latency_ms / self.transcriptions_total


class STTWorker:
    """
    Speech-to-Text worker using Faster-Whisper.

    Features:
    - Configurable model size (tiny to large-v3)
    - Automatic device detection (CPU/CUDA)
    - Streaming transcription support
    - Language detection or forced language
    - Confidence scoring
    - Performance statistics
    - Async and sync transcription methods

    Example:
        >>> stt = STTWorker(model="base", device="cuda")
        >>> result = await stt.transcribe(audio_array)
        >>> print(result.text)  # "Hello world"
    """

    def __init__(
        self,
        model_size: str | ModelSize = ModelSize.BASE.value,
        device: str | DeviceType = DeviceType.AUTO.value,
        compute_type: str | ComputeType = ComputeType.INT8.value,
        language: Optional[str] = None,
        config: Optional[STTConfig] = None,
    ):
        """
        Initialize STT worker.

        Args:
            model_size: Whisper model size (tiny/base/small/medium/large)
            device: Compute device (cpu/cuda/auto)
            compute_type: Precision (int8/float16/float32)
            language: Force language (None for auto-detection)
            config: STT configuration (loads from default if None)

        Raises:
            ImportError: If faster-whisper not installed
            RuntimeError: If model loading fails
        """
        self.config = config or get_config().stt

        # Override config with explicit parameters
        self.model_size = model_size or self.config.model
        self.device = device or self.config.device
        self.compute_type = compute_type or self.config.compute_type
        self.language = language or self.config.language

        # Validate parameters
        self._validate_parameters()

        # Load model
        self._load_model()

        # Statistics
        self.stats = STTStats()

        logger.info(
            "stt_worker.initialized",
            model_size=self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            language=self.language or "auto-detect",
        )

    def _validate_parameters(self) -> None:
        """Validate initialization parameters."""
        # Validate model size
        valid_sizes = [m.value for m in ModelSize]
        if self.model_size not in valid_sizes:
            raise ValueError(
                f"Invalid model_size '{self.model_size}'. "
                f"Must be one of: {valid_sizes}"
            )

        # Validate device
        valid_devices = [d.value for d in DeviceType]
        if self.device not in valid_devices:
            raise ValueError(
                f"Invalid device '{self.device}'. "
                f"Must be one of: {valid_devices}"
            )

        # Validate compute type
        valid_types = [c.value for c in ComputeType]
        if self.compute_type not in valid_types:
            raise ValueError(
                f"Invalid compute_type '{self.compute_type}'. "
                f"Must be one of: {valid_types}"
            )

    def _load_model(self) -> None:
        """Load Whisper model."""
        try:
            start_time = time.perf_counter()

            # Determine device
            device_str = "cpu"
            if self.device == DeviceType.CUDA.value:
                device_str = "cuda"
            elif self.device == DeviceType.AUTO.value:
                # Try CUDA, fall back to CPU
                try:
                    import torch
                    device_str = "cuda" if torch.cuda.is_available() else "cpu"
                except ImportError:
                    device_str = "cpu"

            # Load model
            self.model = WhisperModel(
                self.model_size,
                device=device_str,
                compute_type=self.compute_type,
                download_root=None,  # Use default cache
            )

            load_time = (time.perf_counter() - start_time) * 1000

            logger.info(
                "stt_worker.model_loaded",
                model=self.model_size,
                device=device_str,
                load_time_ms=f"{load_time:.2f}",
            )

        except ImportError as e:
            logger.error("stt_worker.import_error", error=str(e))
            raise ImportError(
                "faster-whisper not installed. "
                "Install with: pip install faster-whisper"
            ) from e

        except Exception as e:
            logger.error("stt_worker.load_failed", error=str(e))
            raise RuntimeError(f"Failed to load Whisper model: {e}") from e

    async def transcribe(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> TranscriptionResult:
        """
        Transcribe audio to text (async wrapper).

        Args:
            audio: Audio array (float32, normalized -1.0 to 1.0)
            sample_rate: Sample rate (default 16000)
            beam_size: Beam search size (higher = slower but more accurate)
            vad_filter: Use VAD to filter silent segments

        Returns:
            TranscriptionResult with text and metadata

        Raises:
            ValueError: If audio shape is invalid
            RuntimeError: If transcription fails
        """
        return await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: self._transcribe_sync(
                audio, sample_rate, beam_size, vad_filter
            )
        )

    def transcribe_sync(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> TranscriptionResult:
        """
        Transcribe audio to text (sync version).

        Use this from synchronous contexts.
        """
        return self._transcribe_sync(audio, sample_rate, beam_size, vad_filter)

    def _transcribe_sync(
        self,
        audio: np.ndarray,
        sample_rate: int = 16000,
        beam_size: int = 5,
        vad_filter: bool = True,
    ) -> TranscriptionResult:
        """
        Internal sync transcription method.

        Args:
            audio: Audio array (float32, normalized)
            sample_rate: Sample rate
            beam_size: Beam search size
            vad_filter: VAD filtering

        Returns:
            TranscriptionResult
        """
        start_time = time.perf_counter()

        try:
            # Validate audio
            if not isinstance(audio, np.ndarray):
                raise ValueError(f"Audio must be numpy array, got {type(audio)}")

            if len(audio.shape) != 1:
                raise ValueError(f"Audio must be 1D, got shape {audio.shape}")

            if len(audio) == 0:
                logger.warning("stt_worker.empty_audio")
                result = TranscriptionResult(
                    text="",
                    confidence=0.0,
                    language="",
                    duration_ms=0.0,
                    segments_count=0,
                    latency_ms=0.0,
                )
                self.stats.update_stats(result, 0.0)
                return result

            # Resample if needed (Whisper expects 16000)
            if sample_rate != 16000:
                audio = self._resample(audio, sample_rate, 16000)
                sample_rate = 16000

            # Normalize audio
            audio = self._normalize_audio(audio)

            # Run transcription
            segments, info = self.model.transcribe(
                audio,
                beam_size=beam_size,
                vad_filter=vad_filter,
                language=self.language,
            )

            # Collect results
            texts = [segment.text for segment in segments]
            confidence_values = [segment.no_speech_prob for segment in segments]

            # Combine text
            text = " ".join(texts).strip()

            # Calculate confidence
            avg_confidence = 1.0 - np.mean(confidence_values) if confidence_values else 1.0

            # Calculate duration
            duration_ms = (len(audio) / sample_rate) * 1000

            # Calculate latency
            latency_ms = (time.perf_counter() - start_time) * 1000

            result = TranscriptionResult(
                text=text,
                confidence=float(avg_confidence),
                language=info.language,
                duration_ms=duration_ms,
                segments_count=len(segments),
                latency_ms=latency_ms,
            )

            # Update statistics
            self.stats.update_stats(result, latency_ms)

            logger.debug(
                "stt_worker.transcription_complete",
                text_length=len(text),
                confidence=f"{avg_confidence:.2f}",
                language=info.language,
                latency_ms=f"{latency_ms:.2f}",
            )

            return result

        except Exception as e:
            logger.error("stt_worker.transcription_error", error=str(e))
            self.stats.update_stats(None, 0.0)
            raise RuntimeError(f"Transcription failed: {e}") from e

    def _resample(self, audio: np.ndarray, orig_rate: int, target_rate: int) -> np.ndarray:
        """Resample audio to target sample rate."""
        # Simple linear interpolation (use libsamplerate for production)
        ratio = target_rate / orig_rate
        new_length = int(len(audio) * ratio)
        indices = np.linspace(0, len(audio) - 1, new_length)
        return np.interp(indices, np.arange(len(audio)), audio).astype(np.float32)

    def _normalize_audio(self, audio: np.ndarray) -> np.ndarray:
        """Normalize audio to [-1.0, 1.0]."""
        # Check if already normalized
        max_val = np.max(np.abs(audio))
        if max_val <= 1.0:
            return audio

        # Normalize
        return audio / max_val

    def get_stats(self) -> dict:
        """Get current statistics."""
        return {
            "transcriptions_total": self.stats.transcriptions_total,
            "transcriptions_success": self.stats.transcriptions_success,
            "transcriptions_empty": self.stats.transcriptions_empty,
            "transcriptions_error": self.stats.transcriptions_error,
            "total_duration_ms": self.stats.total_duration_ms,
            "total_latency_ms": self.stats.total_latency_ms,
            "average_latency_ms": self.stats.average_latency_ms,
        }

    def reset_stats(self) -> None:
        """Reset all statistics."""
        self.stats = STTStats()
        logger.info("stt_worker.stats_reset")


# Utility functions for common use cases

async def transcribe_file(
    file_path: str,
    model_size: str = "base",
    device: str = "auto",
) -> TranscriptionResult:
    """
    Transcribe an audio file.

    Args:
        file_path: Path to audio file (wav, mp3, etc.)
        model_size: Whisper model size
        device: Compute device

    Returns:
        TranscriptionResult

    Example:
        >>> result = await transcribe_file("recording.wav")
        >>> print(f"Transcribed: {result.text}")
    """
    import soundfile as sf

    # Load audio
    audio, sr = sf.read(file_path, dtype="float32")

    # Stereo to mono if needed
    if len(audio.shape) == 2:
        audio = np.mean(audio, axis=1)

    # Transcribe
    stt = STTWorker(model_size=model_size, device=device)
    return await stt.transcribe(audio, sample_rate=sr)


def create_from_config(config: Optional[STTConfig] = None) -> STTWorker:
    """
    Create STT worker from configuration.

    Args:
        config: STT configuration (uses default if None)

    Returns:
        Configured STTWorker instance
    """
    cfg = config or get_config().stt
    return STTWorker(
        model_size=cfg.model,
        device=cfg.device,
        compute_type=cfg.compute_type,
        language=cfg.language,
    )